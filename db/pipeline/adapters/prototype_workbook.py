"""Adapter: ``ibd-prototype-evidence-review.xlsx`` -> staging (dataset prototype-v1).

Loaded solely to reproduce + shadow-test the existing 49-claim / 20-source prototype cut.
``Included With Limitations`` is a filtered duplicate of rows already in ``Included Claims``
(the 7 ``prototype_eligible_with_limitation`` claims) -> kept as a reconcile cross-check,
not re-loaded.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import AdapterResult, StagingRecord, iter_table
from pipeline.enums import split_multi

ADAPTER = "prototype_workbook"
DATASET = "prototype-v1"

_SOURCE_MAP = {
    "sourceId": "source_ref",
    "sourceTitle": "title",
    "sourceUrl": "authoritative_url",
    "publicationYear": "pub_year",
    "sourceType": "source_type",
    "conditionApplicability": "condition_applicability",
    "diseaseContext": "disease_context",
    "evidenceLimitations": "evidence_limitations",
    "canadaUsApplicability": "region_applicability_note",
    "regionalAssessment": "regional_assessment",
    "reviewStatus": "review_status",
}
_CLAIM_MAP = {
    "claimId": "claim_ref",
    "sourceId": "source_ref",
    "sourceTitle": "source_title",
    "sourceUrl": "authoritative_url",
    "conditionApplicability": "condition_applicability",
    "diseaseContext": "disease_context",
    "topic": "topic",
    "outcomeType": "outcome_type",
    "claimText": "claim_text",
    "plainLanguageExplanation": "plain_language_explanation",
    "supportingExcerpt": "supporting_excerpt",
    "exactLocator": "precise_locator",
    "evidenceLevel": "evidence_level",
    "limitations": "limitations",
    "applicabilityLimitations": "applicability_limitations",
    "confidence": "confidence",
    "prototypeEligibilityStatus": "prototype_eligibility_status",
}
_MULTI = {"condition_applicability", "disease_context"}
_SOURCE_HUMAN_REVIEW = ("userDecision", "userNotes")
_CLAIM_HUMAN_REVIEW = ("userDecision", "reviewerNotes")


def _map_row(row: dict, colmap: dict) -> dict:
    return {
        target: (split_multi(row.get(header)) if target in _MULTI else row.get(header))
        for header, target in colmap.items()
    }


def load(path: str | Path) -> AdapterResult:
    path = Path(path)
    res = AdapterResult(adapter=ADAPTER, input_key="prototype_workbook")

    for xlrow, row in iter_table(path, "Included Sources"):
        ref = row.get("sourceId")
        if not ref:
            continue
        if any(row.get(k) for k in _SOURCE_HUMAN_REVIEW):
            res.warnings.append(f"Included Sources {ref}: human-review field populated")
        rec = StagingRecord(target="source_raw", dataset=DATASET, natural_key=ref,
                            fields=_map_row(row, _SOURCE_MAP), raw=dict(row))
        rec.with_provenance(src_file=str(path), src_sheet="Included Sources",
                            src_row=xlrow, adapter=ADAPTER)
        res.records.append(rec)

    for xlrow, row in iter_table(path, "Included Claims"):
        ref = row.get("claimId")
        if not ref:
            continue
        if any(row.get(k) for k in _CLAIM_HUMAN_REVIEW):
            res.warnings.append(f"Included Claims {ref}: human-review field populated")
        rec = StagingRecord(target="claim_raw", dataset=DATASET, natural_key=ref,
                            fields=_map_row(row, _CLAIM_MAP), raw=dict(row))
        rec.with_provenance(src_file=str(path), src_sheet="Included Claims",
                            src_row=xlrow, adapter=ADAPTER)
        res.records.append(rec)

    for xlrow, row in iter_table(path, "Excluded Claims"):
        ref = row.get("claimId")
        if not ref:
            continue
        rec = StagingRecord(
            target="excluded_raw", dataset=DATASET, natural_key=ref,
            fields={"result": row.get("result"), "reason": row.get("reason"),
                    "origin_sheet": "Excluded Claims"},
            raw=dict(row),
        )
        rec.with_provenance(src_file=str(path), src_sheet="Excluded Claims",
                            src_row=xlrow, adapter=ADAPTER)
        res.records.append(rec)

    for sheet in ("Included With Limitations", "CLM-083 Correction",
                  "CLM-096-100 Metadata", "Prototype Coverage", "Prototype Summary"):
        for xlrow, row in iter_table(path, sheet):
            key = (row.get("claimId") or row.get("area") or row.get("metric")
                   or f"r{xlrow}")
            rec = StagingRecord(
                target="reconcile_raw", dataset=DATASET,
                natural_key=f"{sheet}:{key}",
                fields={"sheet": sheet, "key": key, "values": dict(row)},
                raw=dict(row),
            )
            rec.with_provenance(src_file=str(path), src_sheet=sheet, src_row=xlrow,
                                adapter=ADAPTER)
            res.records.append(rec)

    return res
