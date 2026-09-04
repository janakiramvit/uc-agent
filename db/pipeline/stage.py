"""DB I/O for the staging schema. Everything here is a thin persistence layer over the
PURE logic in ``pipeline.adapters`` / ``pipeline.validate`` / ``pipeline.reconcile`` -
no business logic lives here. Requires a connection from ``pipeline.db.connect()``
(already dev-target-gated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pipeline.adapters.base import AdapterResult, StagingRecord
from pipeline.config import PROMPT_VERSION
from pipeline.reconcile import ReconResult
from pipeline.validate import Outcome, ValidationReport

_TABLES = ("source_raw", "claim_raw", "claim_qa_raw", "excluded_raw", "reconcile_raw")


def new_batch(conn, note: str = "pipeline.ingest run") -> str:
    (batch_id,) = conn.execute(
        "INSERT INTO staging.ingest_batch (prompt_version, note) VALUES (%s, %s) "
        "RETURNING batch_id",
        (PROMPT_VERSION, note),
    ).fetchone()
    return str(batch_id)


def latest_batch(conn) -> str:
    row = conn.execute(
        "SELECT batch_id FROM staging.ingest_batch ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        raise RuntimeError("no staging.ingest_batch rows - run --step stage first")
    return str(row[0])


def stage_records(conn, batch_id: str, records: list[StagingRecord]) -> dict[str, int]:
    """Insert raw adapter output into staging.*_raw. validation_status stays 'pending'."""
    counts: dict[str, int] = {}
    for r in records:
        if r.target not in _TABLES:
            raise ValueError(f"unknown staging target {r.target!r}")
        conn.execute(
            f"INSERT INTO staging.{r.target} "
            "(batch_id, dataset_code, natural_key, fields, provenance, raw) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (batch_id, dataset_code, natural_key) DO UPDATE SET "
            "fields = EXCLUDED.fields, provenance = EXCLUDED.provenance, raw = EXCLUDED.raw",
            (batch_id, r.dataset, r.natural_key, json.dumps(r.fields, default=str),
             json.dumps(r.provenance, default=str), json.dumps(r.raw, default=str)),
        )
        counts[r.target] = counts.get(r.target, 0) + 1
    return counts


def persist_validation(conn, batch_id: str, dataset: str, report: ValidationReport) -> dict:
    """Write validation_status/errors/flags/canonical back onto the staged rows, and
    quarantine every 'quarantine' outcome. Returns a summary dict."""
    summary = {"updated": 0, "quarantined": 0}
    for o in report.outcomes:
        conn.execute(
            f"UPDATE staging.{o.target} SET validation_status=%s, validation_errors=%s, "
            "validation_flags=%s, canonical=%s "
            "WHERE batch_id=%s AND dataset_code=%s AND natural_key=%s",
            (o.status, json.dumps(o.errors), json.dumps(o.flags),
             json.dumps(o.canonical, default=str), batch_id, dataset, o.natural_key),
        )
        summary["updated"] += 1
        if o.status == "quarantine":
            quarantine(conn, batch_id, dataset, o.target.replace("_raw", ""),
                      o.natural_key, o.canonical, o.errors, source_step="validate")
            summary["quarantined"] += 1
    return summary


def persist_reconciliation(conn, batch_id: str, res: ReconResult) -> dict:
    """Write every reconciliation row to staging.reconciliation_result and quarantine
    every material-mismatch entity (source_step='reconcile'). Never normalizes."""
    for r in res.rows:
        conn.execute(
            "INSERT INTO staging.reconciliation_result "
            "(batch_id, comparison, left_label, right_label, entity_type, entity_ref, "
            " field, status, material, left_value, right_value) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (batch_id, r.comparison, r.left, r.right, r.entity_type, r.entity_ref,
             r.field, r.status, r.material,
             (str(r.left_value)[:4000] if r.left_value is not None else None),
             (str(r.right_value)[:4000] if r.right_value is not None else None)),
        )
    seen: set[tuple[str, str, str]] = set()
    for q in res.quarantine_recommendations:
        key = (q.dataset, q.entity_type, q.entity_ref)
        if key in seen:
            continue
        seen.add(key)
        quarantine(conn, batch_id, q.dataset, q.entity_type, q.entity_ref,
                  {"reasons": q.reasons}, q.reasons, source_step="reconcile")
    return {"rows": len(res.rows), "material_mismatches": len(res.material_mismatches()),
            "quarantine_entities": len(seen)}


def quarantine(conn, batch_id: str, dataset_code: str, entity_type: str, natural_key: str,
               raw: dict, reasons: list[str], *, source_step: str) -> None:
    conn.execute(
        "INSERT INTO quarantine.record "
        "(batch_id, dataset_code, entity_type, natural_key, raw, reasons, source_step) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (batch_id, dataset_code, entity_type, natural_key,
         json.dumps(raw, default=str), list(reasons) or ["unspecified"], source_step),
    )


@dataclass
class StagingCounts:
    by_target: dict[str, dict[str, int]]     # dataset_code -> target -> count
    total: int


def read_counts(conn, batch_id: str) -> StagingCounts:
    by_target: dict[str, dict[str, int]] = {}
    total = 0
    for t in _TABLES:
        rows = conn.execute(
            f"SELECT dataset_code, count(*) FROM staging.{t} "
            "WHERE batch_id=%s GROUP BY dataset_code", (batch_id,),
        ).fetchall()
        for ds, n in rows:
            by_target.setdefault(ds, {})[t] = n
            total += n
    return StagingCounts(by_target=by_target, total=total)


def read_validation_summary(conn, batch_id: str) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for t in _TABLES:
        rows = conn.execute(
            f"SELECT validation_status, count(*) FROM staging.{t} "
            "WHERE batch_id=%s GROUP BY validation_status", (batch_id,),
        ).fetchall()
        for status, n in rows:
            out.setdefault(t, {})[status or "pending"] = n
    return out


def read_quarantine_summary(conn, batch_id: str) -> list[tuple]:
    return conn.execute(
        "SELECT source_step, dataset_code, entity_type, count(*), "
        "       array_agg(DISTINCT natural_key ORDER BY natural_key) "
        "FROM quarantine.record WHERE batch_id=%s "
        "GROUP BY source_step, dataset_code, entity_type "
        "ORDER BY source_step, dataset_code, entity_type", (batch_id,),
    ).fetchall()
