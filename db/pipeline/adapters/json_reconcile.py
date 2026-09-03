"""Adapter: the ``knowledge/ibd-research-review/*.json`` references -> staging.reconcile_raw.

Read-only. Never emits ``source_raw`` / ``claim_raw`` / ``excluded_raw``. Builds the
reference side of the field-by-field reconciliation:

  * ``prototype_json``          -> per-claim / per-source oracle values for dataset prototype-v1
  * ``candidate_claims_json``   -> per-claim reference values for dataset baseline-register
  * ``prototype_exclusions``    -> excluded-id reference for prototype-v1
  * ``*summary`` / ``run-summary`` -> count metrics
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.adapters.base import AdapterResult, StagingRecord

ADAPTER = "json_reconcile"

# canonical field name -> key(s) that may hold it in a JSON claim object
_CLAIM_FIELD_KEYS = {
    "claim_text": ("claimText", "claim"),
    "supporting_excerpt": ("supportingExcerpt",),
    "precise_locator": ("exactLocator", "pageNumber"),
    "authoritative_url": ("sourceUrl",),
    "condition_applicability": ("conditionApplicability",),
    "disease_context": ("diseaseContext",),
    "topic": ("topic",),
    "outcome_type": ("outcomeType",),
    "evidence_level": ("evidenceLevel",),
    "confidence": ("confidence",),
    "limitations": ("limitations",),
    "applicability_limitations": ("applicabilityLimitations",),
    "review_status": ("reviewStatus",),
    "prototype_eligibility_status": ("prototypeEligibilityStatus",),
    "source_ref": ("sourceId",),
}
_SOURCE_FIELD_KEYS = {
    "title": ("sourceTitle",),
    "authoritative_url": ("sourceUrl",),
    "pub_year": ("publicationYear",),
    "source_type": ("sourceType",),
    "condition_applicability": ("conditionApplicability",),
    "disease_context": ("diseaseContext",),
    "evidence_limitations": ("evidenceLimitations",),
    "region_applicability_note": ("canadaUsApplicability",),
    "regional_assessment": ("regionalAssessment",),
    "review_status": ("reviewStatus",),
}


def _first(obj: dict, keys: tuple[str, ...]):
    for k in keys:
        if k in obj and obj[k] not in (None, ""):
            return obj[k]
    return None


def _project(obj: dict, keymap: dict) -> dict:
    return {canon: _first(obj, keys) for canon, keys in keymap.items()}


def _rec(dataset: str, entity_type: str, entity_ref: str, source_key: str,
         values: dict, path: Path) -> StagingRecord:
    r = StagingRecord(
        target="reconcile_raw", dataset=dataset,
        natural_key=f"json:{source_key}:{entity_type}:{entity_ref}",
        fields={"kind": "reference", "reference": source_key,
                "entity_type": entity_type, "entity_ref": entity_ref, "values": values},
        raw={},
    )
    r.with_provenance(src_file=str(path), src_sheet=None, src_row=0, adapter=ADAPTER)
    return r


def load(paths: dict[str, Path]) -> AdapterResult:
    """``paths`` maps input-registry keys -> Path (only the reconcile/oracle ones)."""
    res = AdapterResult(adapter=ADAPTER, input_key="json_reconcile")

    # --- prototype oracle ---------------------------------------------------
    p = paths.get("prototype_json")
    if p and p.is_file():
        data = json.loads(p.read_text())
        res.records.append(_rec("prototype-v1", "package", "prototype_json", "prototype_json",
                                {"version": data.get("version"),
                                 "createdAt": data.get("createdAt"),
                                 "intendedUse": data.get("intendedUse"),
                                 "claimCount": len(data.get("claims", [])),
                                 "sourceCount": len(data.get("sources", [])),
                                 "excludedClaimIds": data.get("excludedClaimIds", []),
                                 "limitations": data.get("limitations", [])}, p))
        for c in data.get("claims", []):
            res.records.append(_rec("prototype-v1", "claim", c["claimId"], "prototype_json",
                                    _project(c, _CLAIM_FIELD_KEYS), p))
        for s in data.get("sources", []):
            res.records.append(_rec("prototype-v1", "source", s["sourceId"], "prototype_json",
                                    _project(s, _SOURCE_FIELD_KEYS), p))

    # --- baseline candidate claims ---------------------------------------
    p = paths.get("candidate_claims_json")
    if p and p.is_file():
        for c in json.loads(p.read_text()):
            res.records.append(_rec("baseline-register", "claim", c["claimId"],
                                    "candidate_claims_json",
                                    _project(c, _CLAIM_FIELD_KEYS), p))

    # --- prototype exclusions ------------------------------------------
    p = paths.get("prototype_exclusions_json")
    if p and p.is_file():
        data = json.loads(p.read_text())
        res.records.append(_rec("prototype-v1", "exclusion_set", "prototype_exclusions",
                                "prototype_exclusions_json",
                                {"excludedClaimIds": data.get("excludedClaimIds", []),
                                 "triage": data.get("triage", [])}, p))

    # --- summaries / run summary -> count metrics ---------------------
    for key, dataset in (("prototype_summary_json", "prototype-v1"),
                         ("run_summary_json", "baseline-register"),
                         ("removed_replaced_json", "baseline-register")):
        p = paths.get(key)
        if p and p.is_file():
            data = json.loads(p.read_text())
            res.records.append(_rec(dataset, "metrics", key, key,
                                    data if isinstance(data, dict) else {"items": data}, p))

    return res
