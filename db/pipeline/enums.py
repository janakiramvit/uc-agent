"""Canonical enumeration vocabulary + per-input crosswalk - single source of truth.

The canonical vocab starts from ``knowledge/ibd-research-review/scripts/models.py``
(the authoring schema's ``Literal`` sets). Every *observed* input value that is not
already canonical gets an **explicit, human-reviewable** crosswalk row here, each with
a ``note`` explaining the mapping. This is documented reconciliation, not silent
inference.

Rules:
  * A value with no canonical form and no crosswalk row is **unmapped** -> the record is
    quarantined (never coerced).
  * ``evidence_level`` / ``confidence`` (evidence-strength) mappings are conservative:
    a free-text label is mapped only where the correspondence is unambiguous; anything
    doubtful is left to quarantine for human classification.
  * ``topic`` and ``study_type`` are open free-text, NOT controlled here.

``emit_seed_rows()`` produces the rows that ``0004_seed_metadata.sql`` must contain;
``tests/test_enums.py`` asserts the SQL file and this module agree.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Canonical vocabulary (dimension -> ordered list of allowed values)
# ---------------------------------------------------------------------------
CANONICAL_ENUMS: dict[str, list[str]] = {
    "condition": [
        "ulcerative_colitis", "crohns_disease", "ibd_general",
        "general_population", "unclear",
    ],
    "disease_context": [
        "active_disease", "remission", "post_surgery",
        "stricture_or_obstruction_risk", "perioperative",
        "general_or_unspecified", "not_applicable", "unclear",
    ],
    "outcome_type": [
        "symptoms", "inflammation", "biomarkers", "disease_activity",
        "remission_induction", "remission_maintenance", "relapse_risk",
        "hospitalisation", "surgery", "nutritional_status", "quality_of_life",
        "adverse_effects", "adherence", "general_patient_education",
        "obstruction_risk", "perioperative_nutrition_management",
        "evidence_uncertainty", "unclear",
    ],
    "evidence_level": [
        "formal_guideline", "consensus_statement", "systematic_review",
        "meta_analysis", "randomized_trial", "controlled_trial",
        "observational", "official_patient_information",
        "expert_explanation", "other",
    ],
    "confidence": ["high", "moderate", "low"],
    "source_type": [
        "guideline", "systematic_review", "meta_analysis", "randomized_trial",
        "controlled_trial", "observational", "patient_information",
        "expert_content", "other",
    ],
    "review_status": [
        "pending_human_review", "approved", "rejected",
    ],
    "evidence_status": [
        "ready_for_human_review", "still_needs_evidence",
    ],
    "prototype_eligibility_status": [
        "prototype_eligible", "prototype_eligible_with_limitation", "excluded",
    ],
}

# ---------------------------------------------------------------------------
# Crosswalk rows: (dimension, input_format, input_value, canonical_value|None, note)
# canonical_value == input_value rows are implied for every CANONICAL_ENUMS entry
# and need not be listed. A row with canonical_value=None means "known but
# deliberately NOT auto-mapped -> quarantine for human classification".
# ---------------------------------------------------------------------------
INPUT_FORMATS = (
    "register_workbook", "qa_workbook", "prototype_workbook",
    "prototype_json", "candidate_claims_json", "models_py",
)

# Dimensions where an unmapped value is a HARD failure (structural / retrieval-safety):
# a claim we cannot classify by condition or disease context must not enter canonical.
QUARANTINE_ON_UNMAPPED: frozenset[str] = frozenset({"condition", "disease_context"})

# Dimensions where an unmapped value is NOT fatal: keep the row, store the verbatim
# value in ``<field>_raw``, leave the canonical ``<field>`` NULL, and flag the record
# ``pending_human_classification`` in reconciliation_result / claim_qa. This is the
# "evidence-strength values stay null/unknown/pending, not inferred" rule.
PENDING_ON_UNMAPPED: frozenset[str] = frozenset({
    "evidence_level", "confidence", "outcome_type", "source_type",
    "review_status", "evidence_status", "prototype_eligibility_status",
})

# Format-only normalizations (hyphen/space -> underscore, obvious synonyms). Applied to
# BOTH the prototype workbook and its JSON twin. Every row is human-reviewable here and
# is echoed into db/schema/enumerations.md.
_EL = "evidence_level"
_evidence_level_norm = {
    "meta-analysis": ("meta_analysis", "hyphen->underscore, same term"),
    "systematic review": ("systematic_review", "space->underscore, same term"),
    "observational study": ("observational", "same study design, canonical drops 'study'"),
    "randomized controlled trial": ("randomized_trial", "RCT == canonical randomized_trial"),
    "official patient information": ("official_patient_information", "space->underscore"),
    "consensus statement": ("consensus_statement", "space->underscore"),
    "clinical guideline": ("formal_guideline", "synonym; source_type for these rows is 'guideline'"),
    # deliberately NOT mapped -> pending human classification, raw preserved:
    "guideline/consensus": (None, "ambiguous: formal_guideline vs consensus_statement"),
    "review": (None, "ambiguous: narrative vs systematic review"),
    "EL5": (None, "ECCO evidence level 5 (expert opinion); expert_explanation vs other"),
}
_source_type_norm = {
    "guideline": ("guideline", "identity"),
    "expert": ("expert_content", "synonym"),
    "study": (None, "ambiguous: RCT / observational / other"),
    "review": (None, "ambiguous: systematic_review vs narrative"),
}

_CROSSWALK: list[tuple[str, str, str, str | None, str]] = [
    # --- outcome_type: prototype/QA free-text label vs canonical ---
    ("outcome_type", "prototype_workbook", "nutrition_status", "nutritional_status",
     "prototype label 'nutrition_status' == canonical 'nutritional_status'"),
    ("outcome_type", "qa_workbook", "nutrition_status", "nutritional_status",
     "QA sheet label 'nutrition_status' == canonical 'nutritional_status'"),
    # --- condition: spacing normalization ---
    ("condition", "register_workbook", "general population", "general_population",
     "spacing normalization only"),
]
for _fmt in ("prototype_workbook", "prototype_json"):
    for _raw, (_canon, _note) in _evidence_level_norm.items():
        _CROSSWALK.append((_EL, _fmt, _raw, _canon, _note))
# source_type free-text vocab is shared by the register and prototype workbooks + JSON
for _fmt in ("register_workbook", "prototype_workbook", "prototype_json",
             "candidate_claims_json"):
    for _raw, (_canon, _note) in _source_type_norm.items():
        _CROSSWALK.append(("source_type", _fmt, _raw, _canon, _note))

# models.py identity rows (so the crosswalk table records the authoring vocabulary too)
for _dim, _vals in CANONICAL_ENUMS.items():
    for _v in _vals:
        _CROSSWALK.append((_dim, "models_py", _v, _v, "authoring vocabulary (models.py)"))


@dataclass(frozen=True)
class CrosswalkResult:
    input_value: str
    canonical_value: str | None
    matched: bool          # True if an exact-canonical hit or an explicit crosswalk row
    mapped: bool           # True if it resolves to a non-None canonical value
    note: str = ""


def _index() -> dict[tuple[str, str, str], tuple[str | None, str]]:
    idx: dict[tuple[str, str, str], tuple[str | None, str]] = {}
    for dim, fmt, raw, canon, note in _CROSSWALK:
        idx[(dim, fmt, raw)] = (canon, note)
    return idx


_IDX = _index()


def crosswalk(dimension: str, input_format: str, value: str | None) -> CrosswalkResult:
    """Resolve one raw enum token."""
    if value is None or value == "":
        return CrosswalkResult(value or "", None, matched=True, mapped=False,
                               note="empty -> null (allowed for nullable dimensions)")
    v = value.strip()
    if dimension in CANONICAL_ENUMS and v in CANONICAL_ENUMS[dimension]:
        return CrosswalkResult(v, v, matched=True, mapped=True, note="exact canonical")
    hit = _IDX.get((dimension, input_format, v))
    if hit is not None:
        canon, note = hit
        return CrosswalkResult(v, canon, matched=True, mapped=canon is not None, note=note)
    return CrosswalkResult(v, None, matched=False, mapped=False,
                           note="no canonical form and no crosswalk row -> unmapped")


def split_multi(raw: str | None) -> list[str]:
    """'a; b; c' (or 'a | b', 'a, b') -> ['a','b','c']; '' -> []."""
    if not raw:
        return []
    text = str(raw)
    for sep in (";", "|"):
        text = text.replace(sep, ";")
    parts = [p.strip() for p in text.split(";")]
    return [p for p in parts if p]


def emit_seed_rows() -> list[dict]:
    """Rows for 0004_seed_metadata.sql (enum_value + enum_crosswalk)."""
    values = [
        {"table": "enum_value", "dimension": d, "value": v, "ordinal": i}
        for d, vs in CANONICAL_ENUMS.items()
        for i, v in enumerate(vs)
    ]
    xwalk = [
        {"table": "enum_crosswalk", "dimension": d, "input_format": f,
         "input_value": raw, "canonical_value": canon, "note": note}
        for d, f, raw, canon, note in _CROSSWALK
        if f != "models_py"  # identity rows are implied; keep the seed compact
    ]
    return values + xwalk
