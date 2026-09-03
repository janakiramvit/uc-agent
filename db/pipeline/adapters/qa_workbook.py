"""Adapter: ``ibd-evidence-review-final-remediation-qa.xlsx`` -> staging QA OVERLAY only.

Hard rule: this workbook never produces ``source_raw`` or ``claim_raw`` records. Its
per-claim QA-observed metadata (outcome type, study type, confidence, ...) is kept inside
``claim_qa_raw.findings`` and is **never merged into** ``canonical.claim``.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import AdapterResult, StagingRecord, iter_table

ADAPTER = "qa_workbook"
DATASET = "baseline-register"

# sheet -> (qa_dimension, claim-id header, outcome header, [extra headers kept in findings])
_CLAIM_QA_SHEETS = {
    "Corrected Claim QA": (
        "corrected_claim", "Claim ID", "QA classification",
        ["Source ID", "Condition applicability", "Disease context", "Outcome type",
         "Study type", "Confidence", "Finding", "Required action",
         "Reviewer decision", "Reviewer notes"],
    ),
    "Source and Locator QA": (
        "source_and_locator", "Claim ID", "QA outcome",
        ["Source ID", "Evidence status", "Source exists", "Source active",
         "Excerpt status", "Locator status", "Exact locator",
         "Condition applicability", "Disease context", "Outcome type", "Study type",
         "Confidence", "Limitations", "Metadata finding", "QA note",
         "Reviewer fields blank"],
    ),
    "Safety Boundary QA": (
        "safety_boundary", "Claim ID", "QA outcome",
        ["Source ID", "Diagnosis/flare", "Causation", "Medication", "Individual diet",
         "Guaranteed outcome", "Symptoms vs inflammation", "Condition scope", "QA note"],
    ),
    "CLM-092 Exclusion QA": (
        "exclusion", "Claim ID", "Classification",
        ["Evidence status", "Final-QA eligibility", "Approved-export eligibility",
         "Visible in unresolved sheet", "Missing evidence",
         "Duplicate supported occurrence", "Reviewer decision", "Reviewer notes"],
    ),
}

_RECONCILE_SHEETS = (
    "Active Claim Reconciliation", "Workbook Integrity",
    "Report Reconciliation", "QA Summary",
)


def load(path: str | Path) -> AdapterResult:
    path = Path(path)
    res = AdapterResult(adapter=ADAPTER, input_key="qa_workbook")

    for sheet, (dimension, id_hdr, outcome_hdr, extras) in _CLAIM_QA_SHEETS.items():
        for xlrow, row in iter_table(path, sheet):
            claim_ref = row.get(id_hdr)
            if not claim_ref:
                continue
            findings = {k: row.get(k) for k in extras}
            rec = StagingRecord(
                target="claim_qa_raw", dataset=DATASET,
                natural_key=f"{claim_ref}:{dimension}",
                fields={
                    "claim_ref": claim_ref,
                    "qa_dimension": dimension,
                    "qa_outcome": row.get(outcome_hdr),
                    "qa_note": row.get("QA note") or row.get("Finding"),
                    "findings": findings,
                },
                raw=dict(row),
            )
            rec.with_provenance(src_file=str(path), src_sheet=sheet, src_row=xlrow,
                                adapter=ADAPTER)
            res.records.append(rec)

    for sheet in _RECONCILE_SHEETS:
        for xlrow, row in iter_table(path, sheet):
            key = (row.get("Metric") or row.get("Integrity check")
                   or row.get("Check") or f"r{xlrow}")
            rec = StagingRecord(
                target="reconcile_raw", dataset=DATASET,
                natural_key=f"qa:{sheet}:{key}",
                fields={"sheet": sheet, "key": key, "values": dict(row)},
                raw=dict(row),
            )
            rec.with_provenance(src_file=str(path), src_sheet=sheet, src_row=xlrow,
                                adapter=ADAPTER)
            res.records.append(rec)

    return res
