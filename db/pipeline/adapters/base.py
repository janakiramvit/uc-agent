"""Shared adapter primitives: the staging record, the safe-default guard, xlsx helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

ADAPTER_CONTRACT_VERSION = "1.0.0"

# Canonical column names whose value must come from the input verbatim or stay None.
# Attempting to substitute a default for any of these is a bug -> raises.
CLINICAL_FIELDS: frozenset[str] = frozenset({
    # claim text / citation / locator (preserve verbatim)
    "claim_text", "original_claim_text", "supporting_excerpt",
    "exact_authoritative_passage", "precise_locator", "authoritative_url",
    "citation_url", "exact_locator",
    # applicability
    "condition_applicability", "disease_context", "applicability_limitations",
    "regional_applicability", "region_applicability_note",
    # evidence strength
    "evidence_level", "confidence", "study_type",
    # limitations / licensing
    "limitations", "evidence_limitations", "access_licensing_note",
    # review / status
    "review_status", "evidence_status", "final_qa_eligibility",
    "approved_export_eligibility", "verification_status",
    "prototype_eligibility_status",
    # classification
    "topic", "outcome_type",
})

# The ONLY fields an adapter/loader may fill with a computed default. All technical.
SAFE_DEFAULTS: dict[str, Any] = {
    "load_batch_id": None,          # set by the ingest orchestrator
    "adapter": None,
    "adapter_version": ADAPTER_CONTRACT_VERSION,
    "ingested_at": None,           # set at write time
}


class ClinicalFieldDefaultError(RuntimeError):
    """Raised if code tries to default a clinical/applicability/evidence-strength/
    licensing/review field. These stay None when the input does not carry them."""


def apply_safe_default(field_name: str, value: Any) -> Any:
    """Return ``value`` unchanged if present; otherwise the documented safe default.

    Raises for any field in :data:`CLINICAL_FIELDS`.
    """
    if value not in (None, ""):
        return value
    if field_name in CLINICAL_FIELDS:
        raise ClinicalFieldDefaultError(
            f"refusing to default clinical field {field_name!r}; leave it None"
        )
    if field_name in SAFE_DEFAULTS:
        return SAFE_DEFAULTS[field_name]
    return None


@dataclass
class StagingRecord:
    """One row destined for a ``staging.*`` table (before validation)."""

    target: str                      # "source_raw" | "claim_raw" | "claim_qa_raw" |
    #                                  "excluded_raw" | "reconcile_raw"
    dataset: str                     # dataset code, e.g. "baseline-register"
    natural_key: str                 # stable business key within (dataset, target)
    fields: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def with_provenance(self, *, src_file: str, src_sheet: str | None, src_row: int,
                        adapter: str) -> "StagingRecord":
        self.provenance = {
            "src_file": Path(src_file).name,   # name only - never the full local path
            "src_sheet": src_sheet,
            "src_row": src_row,
            "adapter": adapter,
            "adapter_version": ADAPTER_CONTRACT_VERSION,
        }
        return self


@dataclass
class AdapterResult:
    adapter: str
    input_key: str
    version: str = ADAPTER_CONTRACT_VERSION
    records: list[StagingRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.records:
            out[r.target] = out.get(r.target, 0) + 1
        return out


# --------------------------------------------------------------------------- xlsx


def _norm(cell: Any) -> Any:
    if isinstance(cell, str):
        s = cell.strip()
        return s or None
    return cell


def iter_table(path: Path, sheet: str, *, header_row_idx: int = 3
               ) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield ``(excel_row_number, {header: value})`` for each non-empty data row.

    The three v1.0.0 workbooks all use: r0 title, r1 subtitle, r2 blank, r3 header.
    ``excel_row_number`` is 1-based (header is ``header_row_idx + 1``).
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[sheet]
        rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()
    if len(rows) <= header_row_idx:
        return
    header = [(_norm(c) or f"col{i}") for i, c in enumerate(rows[header_row_idx])]
    for offset, row in enumerate(rows[header_row_idx + 1:], start=header_row_idx + 2):
        values = [_norm(c) for c in row]
        if all(v is None for v in values):
            continue
        record = {}
        for i, h in enumerate(header):
            record[h] = values[i] if i < len(values) else None
        yield offset, record


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
