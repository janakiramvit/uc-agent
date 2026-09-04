"""Field-by-field reconciliation (pure, no DB).

Three comparisons:

  A. prototype-v1 workbook  vs  ibd-prototype-evidence.json  (same origin -> FULL parity)
  B. baseline-register workbook  vs  candidate-claims.json    (pre-remediation reference:
       only IDs / citation URL / condition applicability / review status must be stable;
       claim text & strength fields are expected to differ - reported, not material)
  C. baseline-register  vs  prototype-v1  for SHARED claim/source IDs  (both "current",
       intentionally versioned datasets - not required to be byte-identical)

Per (entity, field): match | mismatch | workbook_only | json_only | null_preserved.
A **material** mismatch (IDs, claim text, citation, locator, applicability, limitations,
licensing, review status - in a comparison where that field is in scope) produces a
quarantine recommendation for the affected record(s).

**Nothing is normalized and no original value is ever overwritten here.** A narrow,
principled, fully-tested set of comparison-C classifiers (see `_classify_c_row`) may
mark a mismatch `classification="expected_versioned_difference"` (drops `material` to
False - both original values are still recorded verbatim in `left_value`/`right_value`
and the row still reports `status="mismatch"`) or `classification=
"requires_clinical_applicability_review"` (stays material - flags WHY, doesn't release
it). Every classifier is a generic rule grounded in the datasets' own documented fields
(e.g. "prototype's URL equals the register's own canonical_url"), never an entity-ID
allowlist - so it only fires when the same provenance-backed condition holds, for any
entity, present or future.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from pipeline.validate import Outcome

# Fields compared value-by-value. IDs are NOT here - ID-set stability is a separate check.
COMPARABLE_FIELDS = (
    "claim_text", "supporting_excerpt", "precise_locator",
    "authoritative_url", "condition_applicability", "disease_context", "topic",
    "outcome_type", "evidence_level", "confidence", "limitations",
    "applicability_limitations", "review_status", "evidence_status",
    "prototype_eligibility_status", "title", "pub_year", "source_type",
)
# For comparisons against a same-origin JSON twin we expect VERBATIM parity, so enum
# fields are compared using the workbook's preserved ``<field>_raw`` value.
_RAW_PREFERRED_FIELDS = frozenset({
    "evidence_level", "confidence", "outcome_type", "source_type",
    "condition_applicability", "disease_context", "review_status",
})
MATERIAL_FIELDS = frozenset({
    "claim_ref", "source_ref", "claim_text", "supporting_excerpt", "precise_locator",
    "authoritative_url", "condition_applicability", "disease_context", "limitations",
    "applicability_limitations", "review_status", "access_licensing_note",
})
MULTI_FIELDS = frozenset({"condition_applicability", "disease_context"})

_WS = re.compile(r"\s+")


def _norm_scalar(v: Any) -> str | None:
    if v is None or v == "":
        return None
    return _WS.sub(" ", str(v).strip())


def _norm_multi(v: Any) -> tuple[str, ...] | None:
    if v is None or v == "":
        return None
    items = v if isinstance(v, list) else re.split(r"[;|]", str(v))
    toks = tuple(sorted({_WS.sub(" ", t.strip().lower()) for t in items if t and t.strip()}))
    return toks or None


# The ECCO-style locator label documented in the register's own "Precise locator" /
# "Exact authoritative passage" columns (e.g. "Statement 1:", "Statement 21.1:",
# "Practice Point 2B:"). Isolating ONLY this leading label is the sole normalization
# rule 4 of the remediation checkpoint authorizes for excerpt comparison - nothing else
# (no trailing evidence-grade/consensus annotations, no other wording) is stripped.
_STATEMENT_LABEL_RE = re.compile(
    r"^\s*(Statement|Practice\s+Point)\s+[0-9]+(?:\.[0-9]+)?[A-Za-z]?\s*[:.]\s*",
    re.IGNORECASE,
)


def strip_statement_label(text: str | None) -> str | None:
    if text is None:
        return None
    return _STATEMENT_LABEL_RE.sub("", text).strip()


def compare_values(field_name: str, wb: Any, ref: Any) -> str:
    is_multi = field_name in MULTI_FIELDS
    a = _norm_multi(wb) if is_multi else _norm_scalar(wb)
    b = _norm_multi(ref) if is_multi else _norm_scalar(ref)
    if a is None and b is None:
        return "null_preserved"
    if a is not None and b is None:
        return "workbook_only"
    if a is None and b is not None:
        return "json_only"
    return "match" if a == b else "mismatch"


@dataclass
class ReconRow:
    comparison: str            # "A" | "B" | "C"
    left: str                  # left source label
    right: str                 # right source label
    entity_type: str           # "claim" | "source"
    entity_ref: str
    field: str
    status: str
    material: bool
    left_value: Any = None
    right_value: Any = None
    # Set only by a classifier (see _classify_c_row). Both original values above are
    # ALWAYS preserved untouched regardless of classification.
    classification: str | None = None      # e.g. "expected_versioned_difference",
    #                                         "requires_clinical_applicability_review"
    detail: str | None = None              # human-readable reason for the classification


@dataclass
class QuarantineRec:
    dataset: str
    entity_type: str
    entity_ref: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class ReconResult:
    rows: list[ReconRow] = field(default_factory=list)
    id_stability: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    quarantine_recommendations: list[QuarantineRec] = field(default_factory=list)

    def status_tally(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for r in self.rows:
            out.setdefault(r.field, {})
            out[r.field][r.status] = out[r.field].get(r.status, 0) + 1
        return out

    def material_mismatches(self) -> list[ReconRow]:
        return [r for r in self.rows if r.status == "mismatch" and r.material]


# --------------------------------------------------------------------------- helpers


def _canon_by_ref(outcomes: list[Outcome], target: str) -> dict[str, dict]:
    return {o.natural_key: o.canonical for o in outcomes if o.target == target}


def _ref_by_key(refs: list, dataset: str, entity_type: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for rec in refs:
        f = rec.fields if hasattr(rec, "fields") else rec
        if f.get("kind") != "reference":
            continue
        if rec.dataset != dataset or f.get("entity_type") != entity_type:
            continue
        out[f["entity_ref"]] = f["values"]
    return out


def _pick(row: dict, fname: str, prefer_raw: bool) -> Any:
    if prefer_raw and fname in _RAW_PREFERRED_FIELDS and f"{fname}_raw" in row:
        return row[f"{fname}_raw"]
    return row.get(fname)


def _compare_maps(result: ReconResult, *, comparison: str, left: str, right: str,
                  entity_type: str, left_map: dict[str, dict], right_map: dict[str, dict],
                  fields_in_scope: set[str], material_scope: set[str],
                  quarantine_datasets: list[str], keep_values: bool,
                  prefer_raw: bool = False,
                  classify: Callable[[ReconRow], None] | None = None) -> None:
    left_ids, right_ids = set(left_map), set(right_map)
    result.id_stability.setdefault(f"{comparison}:{entity_type}", {
        "both": sorted(left_ids & right_ids),
        f"{left}_only": sorted(left_ids - right_ids),
        f"{right}_only": sorted(right_ids - left_ids),
    })
    # ID-set drift is itself a material finding.
    for ref in sorted(left_ids ^ right_ids):
        side = left if ref in left_ids else right
        result.rows.append(ReconRow(comparison, left, right, entity_type, ref,
                                    "__id_set__", "workbook_only" if side == left
                                    else "json_only", material=True))

    for ref in sorted(left_ids & right_ids):
        lrow, rrow = left_map[ref], right_map[ref]
        per_ref_material: list[ReconRow] = []
        for fname in fields_in_scope:
            lv = _pick(lrow, fname, prefer_raw)
            rv = _pick(rrow, fname, prefer_raw)
            if lv is None and rv is None and fname not in lrow and fname not in rrow:
                continue
            status = compare_values(fname, lv, rv)
            material = fname in material_scope
            row = ReconRow(
                comparison, left, right, entity_type, ref, fname, status, material,
                left_value=(lv if keep_values else None),
                right_value=(rv if keep_values else None),
            )
            if classify is not None:
                classify(row)          # may flip row.material and set classification/detail
            result.rows.append(row)
            if row.status == "mismatch" and row.material:
                per_ref_material.append(row)
        if per_ref_material:
            for ds in quarantine_datasets:
                result.quarantine_recommendations.append(QuarantineRec(
                    dataset=ds, entity_type=entity_type, entity_ref=ref,
                    reasons=[
                        (f"{r.classification}: {r.field} ({left} vs {right}) - {r.detail}"
                         if r.classification else
                         f"material reconciliation mismatch on {r.field} ({left} vs {right})")
                        for r in per_ref_material
                    ],
                ))


def reconcile(datasets: dict[str, list[Outcome]], references: list, *,
              keep_values: bool = True) -> ReconResult:
    res = ReconResult()
    proto = datasets.get("prototype-v1", [])
    base = datasets.get("baseline-register", [])

    # --- A: prototype-v1 workbook vs prototype_json oracle -----------------
    if proto:
        for et, tgt in (("claim", "claim_raw"), ("source", "source_raw")):
            _compare_maps(
                res, comparison="A", left="prototype_workbook", right="prototype_json",
                entity_type=et,
                left_map=_canon_by_ref(proto, tgt),
                right_map=_ref_by_key(references, "prototype-v1", et),
                fields_in_scope=set(COMPARABLE_FIELDS),
                material_scope=set(MATERIAL_FIELDS),
                quarantine_datasets=["prototype-v1"], keep_values=keep_values,
                prefer_raw=True,
            )

    # --- B: baseline-register workbook vs candidate_claims.json ----------
    if base:
        stability_only = {"claim_ref", "source_ref", "authoritative_url",
                          "condition_applicability", "review_status"}
        _compare_maps(
            res, comparison="B", left="register_workbook", right="candidate_claims_json",
            entity_type="claim",
            left_map=_canon_by_ref(base, "claim_raw"),
            right_map=_ref_by_key(references, "baseline-register", "claim"),
            fields_in_scope=set(COMPARABLE_FIELDS),
            material_scope=stability_only,           # text/strength differences expected
            quarantine_datasets=["baseline-register"], keep_values=keep_values,
            prefer_raw=True,
        )

    # --- C: baseline-register vs prototype-v1 for SHARED ids (two intentionally
    #        versioned datasets - NOT required to be byte-identical; see _classify_c_row) --
    if base and proto:
        base_sources = _canon_by_ref(base, "source_raw")
        base_claims = _canon_by_ref(base, "claim_raw")
        classifier = _make_c_classifier(base_sources=base_sources, base_claims=base_claims)
        for et, tgt in (("claim", "claim_raw"), ("source", "source_raw")):
            _compare_maps(
                res, comparison="C", left="baseline-register", right="prototype-v1",
                entity_type=et,
                left_map=_canon_by_ref(base, tgt),
                right_map=_canon_by_ref(proto, tgt),
                fields_in_scope={"claim_text", "supporting_excerpt", "precise_locator",
                                 "authoritative_url", "condition_applicability",
                                 "disease_context", "limitations",
                                 "applicability_limitations", "title", "pub_year"},
                material_scope={"claim_text", "supporting_excerpt", "precise_locator",
                                "authoritative_url", "condition_applicability",
                                "limitations", "applicability_limitations"},
                quarantine_datasets=["baseline-register", "prototype-v1"],
                keep_values=keep_values,
                classify=classifier,
            )
    return res


def _make_c_classifier(*, base_sources: dict[str, dict], base_claims: dict[str, dict]
                       ) -> Callable[[ReconRow], None]:
    """Comparison-C classifiers. Each rule is generic (grounded in a documented field
    already present in the data), never an entity-ID allowlist. Mutates `row` in place;
    `left_value`/`right_value` (the original, untouched values) are never modified."""

    def _register_canonical_url_for(row: ReconRow) -> str | None:
        if row.entity_type == "source":
            src = base_sources.get(row.entity_ref)
        else:
            claim = base_claims.get(row.entity_ref)
            src = base_sources.get(claim.get("source_ref")) if claim else None
        return (src or {}).get("canonical_url")

    def classify(row: ReconRow) -> None:
        if row.status != "mismatch":
            return

        if row.field == "authoritative_url":
            reg_canonical_url = _register_canonical_url_for(row)
            if (reg_canonical_url and _norm_scalar(reg_canonical_url) ==
                    _norm_scalar(row.right_value)):
                row.material = False
                row.classification = "expected_versioned_difference"
                row.detail = (
                    "prototype-v1's authoritative_url equals baseline-register's own "
                    "source.canonical_url for this source (an authoritative full-text "
                    "URL vs the same source's documented canonical citation URL - both "
                    "belong to the identical, documented source, neither is chosen over "
                    "the other; each dataset's original URL is preserved as recorded)."
                )
            return

        if row.field == "supporting_excerpt":
            l_stripped = strip_statement_label(_norm_scalar(row.left_value))
            r_stripped = strip_statement_label(_norm_scalar(row.right_value))
            if l_stripped is not None and l_stripped == r_stripped:
                row.material = False
                row.classification = "expected_versioned_difference"
                row.detail = (
                    "identical substantive text once the documented leading "
                    "'Statement N:' / 'Practice Point N:' locator label is isolated - "
                    "both original excerpts are preserved byte-for-byte."
                )
            return

        if row.field == "condition_applicability":
            left_set = set(row.left_value or [])
            right_set = set(row.right_value or [])
            if right_set and left_set and right_set < left_set:
                # material stays True: this is NOT released, only explained. The
                # broader baseline-register scope needs a clinician's decision before
                # it can promote with UC applicability; never inferred/upgraded here.
                row.classification = "requires_clinical_applicability_review"
                row.detail = (
                    "baseline-register's condition_applicability "
                    f"{sorted(left_set)!r} is a strict superset of prototype-v1's "
                    f"narrower, corrected scope {sorted(right_set)!r} (see the "
                    "prototype's own correction sheet). Kept quarantined for human "
                    "clinical review - not auto-narrowed or auto-upgraded."
                )
            return

    return classify


# --------------------------------------------------------------------------- reports

_COMPARISON_LABEL = {
    "A": "prototype-v1 workbook  vs  ibd-prototype-evidence.json (same origin - full parity)",
    "B": "baseline-register workbook  vs  candidate-claims.json (pre-remediation reference)",
    "C": "baseline-register  vs  prototype-v1  (shared IDs - both current)",
}


def write_full_report(res: ReconResult, path) -> None:
    """Local-only (gitignored): includes truncated field values."""
    from pathlib import Path

    from pipeline.adapters.base import now_iso

    lines = ["# Schema reconciliation report (FULL - local only, not committed)", "",
             f"_Generated {now_iso()} by `pipeline.reconcile`. Contains workbook-derived "
             "evidence text - do not share or commit._", ""]
    for cmp_id, label in _COMPARISON_LABEL.items():
        crows = [r for r in res.rows if r.comparison == cmp_id]
        if not crows:
            continue
        lines.append(f"## Comparison {cmp_id}: {label}")
        lines.append("")
        st = {}
        for r in crows:
            st[r.status] = st.get(r.status, 0) + 1
        lines.append(f"Rows: {len(crows)} - " + ", ".join(f"{k}={v}" for k, v in sorted(st.items())))
        lines.append("")
        idk = res.id_stability.get(f"{cmp_id}:claim") or {}
        for k, v in idk.items():
            if k != "both" and v:
                lines.append(f"- claim IDs {k}: {v}")
        idk = res.id_stability.get(f"{cmp_id}:source") or {}
        for k, v in idk.items():
            if k != "both" and v:
                lines.append(f"- source IDs {k}: {v}")
        mm = [r for r in crows if r.status == "mismatch"]
        if mm:
            lines.append("")
            lines.append("| entity | field | material | classification | workbook/left | json/right |")
            lines.append("|---|---|---|---|---|---|")
            for r in mm:
                lv = str(r.left_value)[:140].replace("|", "\\|").replace("\n", " ")
                rv = str(r.right_value)[:140].replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {r.entity_type} {r.entity_ref} | {r.field} | "
                             f"{'YES' if r.material else 'no'} | {r.classification or ''} "
                             f"| {lv} | {rv} |")
                if r.detail:
                    lines.append(f"|  |  |  | _{r.detail}_ |  |  |")
        lines.append("")
    lines.append("## Quarantine recommendations (material mismatches)")
    lines.append("")
    if not res.quarantine_recommendations:
        lines.append("_None._")
    for q in res.quarantine_recommendations:
        lines.append(f"- `{q.dataset}` {q.entity_type} **{q.entity_ref}** - {'; '.join(q.reasons)}")
    Path(path).write_text("\n".join(lines) + "\n")


def write_summary(res: ReconResult, path) -> None:
    """Committable, redacted: counts only, NO field values, NO secrets."""
    from pathlib import Path

    from pipeline.adapters.base import now_iso

    lines = ["# Reconciliation SUMMARY (redacted - safe to commit)", "",
             f"_Generated {now_iso()} by `pipeline.reconcile`. Counts only; no evidence "
             "text, no connection strings._", ""]
    for cmp_id, label in _COMPARISON_LABEL.items():
        crows = [r for r in res.rows if r.comparison == cmp_id]
        if not crows:
            continue
        st: dict[str, int] = {}
        for r in crows:
            st[r.status] = st.get(r.status, 0) + 1
        mat = sum(1 for r in crows if r.status == "mismatch" and r.material)
        lines.append(f"## Comparison {cmp_id}")
        lines.append(f"- {label}")
        lines.append(f"- rows: {len(crows)}; " + ", ".join(f"{k}={v}" for k, v in sorted(st.items())))
        lines.append(f"- **material mismatches: {mat}**")
        for et in ("claim", "source"):
            idk = res.id_stability.get(f"{cmp_id}:{et}")
            if idk:
                only = {k: len(v) for k, v in idk.items() if k != "both" and v}
                lines.append(f"- {et} ID sets: both={len(idk['both'])}"
                             + (f", {only}" if only else ""))
        lines.append("")
    lines.append("## Per-field status tally (all comparisons)")
    lines.append("")
    lines.append("| field | match | mismatch | material-mismatch | workbook_only | json_only | null_preserved |")
    lines.append("|---|--:|--:|--:|--:|--:|--:|")
    tally = res.status_tally()
    for fname in sorted(tally):
        t = tally[fname]
        matm = sum(1 for r in res.rows if r.field == fname and r.status == "mismatch" and r.material)
        lines.append(f"| {fname} | {t.get('match',0)} | {t.get('mismatch',0)} | {matm} "
                     f"| {t.get('workbook_only',0)} | {t.get('json_only',0)} | {t.get('null_preserved',0)} |")
    lines.append("")
    qby_ds: dict[str, int] = {}
    for q in res.quarantine_recommendations:
        qby_ds[q.dataset] = qby_ds.get(q.dataset, 0) + 1
    lines.append("## Quarantine recommendations")
    lines.append(f"- total: {len(res.quarantine_recommendations)} across "
                 f"{len({(q.dataset, q.entity_ref) for q in res.quarantine_recommendations})} entities")
    for ds, n in sorted(qby_ds.items()):
        lines.append(f"- `{ds}`: {n}")
    lines.append("")
    lines.append("Entity refs with a material mismatch (IDs only, no values):")
    refs = sorted({f"{q.dataset}:{q.entity_type}:{q.entity_ref}"
                   for q in res.quarantine_recommendations})
    for r in refs:
        lines.append(f"- {r}")

    classified = [r for r in res.rows if r.classification]
    if classified:
        lines.append("")
        lines.append("## Classifications (IDs + category only, no values)")
        for label in ("expected_versioned_difference", "requires_clinical_applicability_review"):
            rows = sorted({(r.entity_type, r.entity_ref, r.field)
                          for r in classified if r.classification == label})
            if not rows:
                continue
            lines.append(f"- **{label}** ({len(rows)}): " +
                         ", ".join(f"{et}:{ref}.{f}" for et, ref, f in rows))
    Path(path).write_text("\n".join(lines) + "\n")

