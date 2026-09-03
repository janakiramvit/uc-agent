"""Pure validation over staging records (no DB).

Turns raw :class:`StagingRecord` fields into *validated* canonical field dicts and a
per-record :class:`Outcome`:

    valid              - promotable as-is
    valid_with_flags   - promotable; carries non-fatal notes (e.g. an evidence-strength
                         value left NULL pending human classification, verbatim kept)
    quarantine         - NOT promotable; explicit reasons; goes to quarantine.record

Fatal (-> quarantine): bad ID pattern, missing claim text / excerpt / locator on a
non-excluded claim, an unmapped ``condition`` / ``disease_context`` token, a claim whose
``source_ref`` does not resolve within its own dataset.

Non-fatal (-> flag, value left NULL, ``*_raw`` preserved): unmapped evidence-strength /
outcome / source-type / status value; empty applicability on a known metadata-incomplete
claim; a populated human-review field.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pipeline.adapters.base import CLINICAL_FIELDS, StagingRecord
from pipeline.enums import crosswalk

CLAIM_ID_RE = re.compile(r"^CLM-\d{1,4}([A-Za-z]\d?)?$")
SOURCE_ID_RE = re.compile(r"^SRC-\d{1,4}$")

# canonical field -> (enum dimension, is_multi)
_CLAIM_ENUMS = {
    "condition_applicability": ("condition", True),
    "disease_context": ("disease_context", True),
    "outcome_type": ("outcome_type", False),
    "evidence_level": ("evidence_level", False),
    "confidence": ("confidence", False),
    "review_status": ("review_status", False),
    "evidence_status": ("evidence_status", False),
    "prototype_eligibility_status": ("prototype_eligibility_status", False),
}
_SOURCE_ENUMS = {
    "condition_applicability": ("condition", True),
    "disease_context": ("disease_context", True),
    "source_type": ("source_type", False),
    "review_status": ("review_status", False),
}
# claim fields that must be non-empty for a non-excluded claim
_CLAIM_REQUIRED_TEXT = ("claim_text", "supporting_excerpt", "precise_locator")


@dataclass
class Outcome:
    natural_key: str
    target: str
    dataset: str
    status: str = "valid"          # valid | valid_with_flags | quarantine
    errors: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    canonical: dict[str, Any] = field(default_factory=dict)   # validated field values
    provenance: dict[str, Any] = field(default_factory=dict)

    def fail(self, reason: str) -> None:
        self.errors.append(reason)
        self.status = "quarantine"

    def flag(self, note: str) -> None:
        if note not in self.flags:
            self.flags.append(note)
        if self.status == "valid":
            self.status = "valid_with_flags"


@dataclass
class ValidationReport:
    dataset: str
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def by_status(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for o in self.outcomes:
            out[o.status] = out.get(o.status, 0) + 1
        return out

    def target_counts(self) -> dict[str, dict[str, int]]:
        res: dict[str, dict[str, int]] = {}
        for o in self.outcomes:
            res.setdefault(o.target, {})
            res[o.target][o.status] = res[o.target].get(o.status, 0) + 1
        return res

    @property
    def quarantined(self) -> list[Outcome]:
        return [o for o in self.outcomes if o.status == "quarantine"]

    @property
    def promotable(self) -> list[Outcome]:
        return [o for o in self.outcomes if o.status != "quarantine"]


def _resolve_enum(o: Outcome, field_name: str, dim: str, is_multi: bool,
                  input_format: str, value: Any, *, fatal_if_unmapped: bool = False) -> None:
    """Populate ``o.canonical[field_name]`` (+ ``_raw``) from a crosswalk.

    ``fatal_if_unmapped`` is set only for retrieval-safety-critical fields (a claim's
    ``condition_applicability``). Elsewhere an unmapped value is non-fatal: the canonical
    field is left NULL, the verbatim value stays in ``<field>_raw``, and the record is
    flagged ``pending_human_classification`` - never partially normalized.
    """
    raw_tokens = value if isinstance(value, list) else ([value] if value else [])
    o.canonical[f"{field_name}_raw"] = value
    resolved: list[str] = []
    unmapped: list[str] = []
    for tok in raw_tokens:
        cw = crosswalk(dim, input_format, tok)
        if cw.mapped:
            resolved.append(cw.canonical_value)  # type: ignore[arg-type]
        elif tok:
            unmapped.append(tok)

    if unmapped and fatal_if_unmapped:
        o.fail(f"{field_name}: unmapped {dim} value(s) {unmapped!r}")
        o.canonical[field_name] = None
        return
    if unmapped:
        for tok in unmapped:
            o.flag(f"pending_human_classification:{field_name}={tok!r}")
        # do not partially populate an applicability/strength field
        o.canonical[field_name] = None
        return
    if is_multi:
        o.canonical[field_name] = sorted(set(resolved)) if resolved else None
    else:
        o.canonical[field_name] = resolved[0] if resolved else None


def _validate_source(o: Outcome, rec: StagingRecord, input_format: str) -> None:
    if not SOURCE_ID_RE.match(o.natural_key):
        o.fail(f"source_ref {o.natural_key!r} does not match {SOURCE_ID_RE.pattern}")
    for k, v in rec.fields.items():
        if k in _SOURCE_ENUMS:
            dim, multi = _SOURCE_ENUMS[k]
            _resolve_enum(o, k, dim, multi, input_format, v)
        else:
            o.canonical[k] = v
    o.canonical["source_ref"] = o.natural_key


def _validate_claim(o: Outcome, rec: StagingRecord, input_format: str,
                    excluded_ids: set[str]) -> None:
    if not CLAIM_ID_RE.match(o.natural_key):
        o.fail(f"claim_ref {o.natural_key!r} does not match {CLAIM_ID_RE.pattern}")
    is_excluded = o.natural_key in excluded_ids
    for k, v in rec.fields.items():
        if k in _CLAIM_ENUMS:
            dim, multi = _CLAIM_ENUMS[k]
            # A claim we cannot classify by CONDITION is unsafe to serve (the UC
            # substring filter depends on it) -> fatal. Everything else is "pending".
            fatal = k == "condition_applicability" and not is_excluded
            _resolve_enum(o, k, dim, multi, input_format, v, fatal_if_unmapped=fatal)
        else:
            o.canonical[k] = v
    o.canonical["claim_ref"] = o.natural_key

    if not is_excluded:
        for f in _CLAIM_REQUIRED_TEXT:
            if not (rec.fields.get(f) or "").strip():
                o.fail(f"required claim field {f!r} is empty on a non-excluded claim")
        if not (o.canonical.get("condition_applicability")):
            o.flag("applicability_missing_or_pending:condition_applicability")
        if not (o.canonical.get("disease_context")):
            o.flag("applicability_missing_or_pending:disease_context")

    # clinical-invention guard: every clinical field is either input-derived or None
    for f in CLINICAL_FIELDS:
        if f in o.canonical and o.canonical[f] == "":
            o.canonical[f] = None


def validate_dataset(records: list[StagingRecord], *, dataset: str,
                     input_format: str) -> ValidationReport:
    report = ValidationReport(dataset=dataset)
    excluded_ids = {
        r.natural_key for r in records if r.target == "excluded_raw"
    }
    source_refs = {
        r.natural_key for r in records if r.target == "source_raw"
    }

    for rec in records:
        o = Outcome(natural_key=rec.natural_key, target=rec.target, dataset=dataset,
                    provenance=dict(rec.provenance))
        if rec.target == "source_raw":
            _validate_source(o, rec, input_format)
        elif rec.target == "claim_raw":
            _validate_claim(o, rec, input_format, excluded_ids)
            sref = rec.fields.get("source_ref")
            if sref and sref not in source_refs:
                o.fail(f"source_ref {sref!r} does not resolve within dataset {dataset!r}")
        elif rec.target == "excluded_raw":
            o.canonical = {"claim_ref": rec.natural_key, **rec.fields}
        elif rec.target in ("claim_qa_raw", "reconcile_raw"):
            o.canonical = dict(rec.fields)
        report.outcomes.append(o)

    return report
