"""Adapter: ``ibd-evidence-review-final-remediation.xlsx`` -> staging (dataset baseline-register).

This workbook is the **authoritative baseline source/claim register**. It carries no
per-claim ``evidence_level`` / ``outcome_type`` / ``confidence`` / ``study_type`` /
``plain_language_explanation`` / ``applicability_limitations`` columns - those stay None
for baseline-register claims (the QA overlay's QA-observed values go to ``claim_qa``,
never here).
"""

from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import AdapterResult, StagingRecord, iter_table
from pipeline.enums import split_multi

ADAPTER = "register_workbook"
DATASET = "baseline-register"

# Excel column header -> canonical field name. Headers not listed are kept in ``raw`` only.
_SOURCE_MAP = {
    "Source ID": "source_ref",
    "Source status": "status",
    "Source title": "title",
    "Source type": "source_type",
    "Authors": "authors",
    "Journal": "journal",
    "Year": "pub_year",
    "Authoritative source URL": "authoritative_url",
    "Canonical URL": "canonical_url",
    "PMID": "pmid",
    "PMCID": "pmcid",
    "DOI": "doi",
    "Full-text verification": "full_text_verification",
    "Condition applicability": "condition_applicability",
    "Disease context": "disease_context",
    "Main relevant finding": "main_relevant_finding",
    "Evidence/reliability limitations": "evidence_limitations",
    "Access/licensing note": "access_licensing_note",
    "Canada/US applicability": "region_applicability_note",
    "Regional assessment": "regional_assessment",
    "Review status": "review_status",
}
_SOURCE_MULTI = {"condition_applicability", "disease_context"}
_SOURCE_HUMAN_REVIEW = ("User decision", "User notes")

_CLAIM_MAP = {
    "Claim ID": "claim_ref",
    "Source ID": "source_ref",
    "Split from": "split_from_ref",
    "Source title": "source_title",
    "Topic": "topic",
    "Condition applicability": "condition_applicability",
    "Disease context": "disease_context",
    "Original claim": "original_claim_text",
    "QA proposed claim": "qa_proposed_claim_text",
    "Final remediated claim": "claim_text",
    "Preserved supporting excerpt": "supporting_excerpt",
    "Exact authoritative passage": "exact_authoritative_passage",
    "Precise locator": "precise_locator",
    "Authoritative source URL": "authoritative_url",
    "Evidence status": "evidence_status",
    "Final-QA eligibility": "final_qa_eligibility",
    "Future approved-export eligibility": "approved_export_eligibility",
    "Verification status": "verification_status",
    "Final remediation note": "remediation_note",
    "Limitations": "limitations",
    "Review status": "review_status",
}
_CLAIM_MULTI = {"condition_applicability", "disease_context"}
_CLAIM_HUMAN_REVIEW = ("User decision", "User-edited claim", "Reviewer notes")


def _map_row(row: dict, colmap: dict, multi: set) -> dict:
    out: dict = {}
    for header, target in colmap.items():
        val = row.get(header)
        out[target] = split_multi(val) if target in multi else val
    return out


def load(path: str | Path) -> AdapterResult:
    path = Path(path)
    res = AdapterResult(adapter=ADAPTER, input_key="register_workbook")

    # --- Sources sheet -----------------------------------------------------
    for xlrow, row in iter_table(path, "Sources"):
        ref = row.get("Source ID")
        if not ref:
            res.warnings.append(f"Sources r{xlrow}: blank Source ID, skipped")
            continue
        fields = _map_row(row, _SOURCE_MAP, _SOURCE_MULTI)
        human = {k: row.get(k) for k in _SOURCE_HUMAN_REVIEW}
        if any(v for v in human.values()):
            res.warnings.append(f"Sources {ref}: human-review field populated {human!r}")
        rec = StagingRecord(target="source_raw", dataset=DATASET, natural_key=ref,
                            fields=fields, raw=dict(row))
        rec.with_provenance(src_file=str(path), src_sheet="Sources", src_row=xlrow,
                            adapter=ADAPTER)
        res.records.append(rec)

    # --- Claims sheet ----------------------------------------------------
    for xlrow, row in iter_table(path, "Claims"):
        ref = row.get("Claim ID")
        if not ref:
            res.warnings.append(f"Claims r{xlrow}: blank Claim ID, skipped")
            continue
        fields = _map_row(row, _CLAIM_MAP, _CLAIM_MULTI)
        human = {k: row.get(k) for k in _CLAIM_HUMAN_REVIEW}
        if any(v for v in human.values()):
            res.warnings.append(f"Claims {ref}: human-review field populated {human!r}")
        rec = StagingRecord(target="claim_raw", dataset=DATASET, natural_key=ref,
                            fields=fields, raw=dict(row))
        rec.with_provenance(src_file=str(path), src_sheet="Claims", src_row=xlrow,
                            adapter=ADAPTER)
        res.records.append(rec)

    # --- Audit sheets -> excluded_raw / reconcile_raw --------------------
    for xlrow, row in iter_table(path, "Removed or Replaced Claims"):
        ref = row.get("Original claim ID")
        if not ref:
            continue
        rec = StagingRecord(
            target="excluded_raw", dataset=DATASET, natural_key=ref,
            fields={
                "result": row.get("Accounting category"),
                "reason": row.get("Removal/replacement reason"),
                "replacement_refs": row.get("Replacement/final claim IDs"),
                "replacement_source": row.get("Replacement source"),
                "origin_sheet": "Removed or Replaced Claims",
            },
            raw=dict(row),
        )
        rec.with_provenance(src_file=str(path), src_sheet="Removed or Replaced Claims",
                            src_row=xlrow, adapter=ADAPTER)
        res.records.append(rec)

    for xlrow, row in iter_table(path, "Unresolved Claims"):
        ref = row.get("Claim ID")
        if not ref:
            continue
        rec = StagingRecord(
            target="excluded_raw", dataset=DATASET, natural_key=ref,
            fields={
                "result": row.get("Final-QA eligibility") or "unresolved",
                "reason": row.get("Evidence still missing"),
                "evidence_status": row.get("Evidence status"),
                "origin_sheet": "Unresolved Claims",
            },
            raw=dict(row),
        )
        rec.with_provenance(src_file=str(path), src_sheet="Unresolved Claims",
                            src_row=xlrow, adapter=ADAPTER)
        res.records.append(rec)

    for sheet in ("Locator Corrections", "CLM-097 Remediation",
                  "Validation Summary", "Final Remediation Summary"):
        for xlrow, row in iter_table(path, sheet):
            key = (row.get("Claim ID") or row.get("Assertion ID")
                   or row.get("Check ID") or row.get("Metric") or f"r{xlrow}")
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
