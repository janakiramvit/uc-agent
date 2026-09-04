"""pipeline.stage SQL wiring, checked against a fake connection (no live DB needed).

Catches column-count / table-name / ON CONFLICT-target mistakes without requiring a
real Postgres. The actual SQL semantics are exercised for real once connected to the
dev Supabase project (post_promotion-style tests would cover that, gated on DATABASE_URL).
"""

from __future__ import annotations

from pipeline import stage
from pipeline.adapters.base import StagingRecord
from pipeline.reconcile import QuarantineRec, ReconResult, ReconRow
from pipeline.validate import Outcome, ValidationReport


class _Result:
    def __init__(self, row=None, rows=None):
        self._row, self._rows = row, rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeConn:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if "RETURNING batch_id" in sql:
            return _Result(row=("11111111-1111-1111-1111-111111111111",))
        if "SELECT batch_id FROM staging.ingest_batch" in sql:
            return _Result(row=("22222222-2222-2222-2222-222222222222",))
        return _Result()


def test_new_batch_inserts_and_returns_id():
    conn = FakeConn()
    bid = stage.new_batch(conn, note="test")
    assert bid == "11111111-1111-1111-1111-111111111111"
    assert "INSERT INTO staging.ingest_batch" in conn.calls[0][0]


def test_stage_records_one_insert_per_record_correct_table():
    conn = FakeConn()
    recs = [
        StagingRecord(target="source_raw", dataset="d", natural_key="SRC-1", fields={}),
        StagingRecord(target="claim_raw", dataset="d", natural_key="CLM-1", fields={}),
        StagingRecord(target="claim_qa_raw", dataset="d", natural_key="CLM-1:x", fields={}),
        StagingRecord(target="excluded_raw", dataset="d", natural_key="CLM-2", fields={}),
        StagingRecord(target="reconcile_raw", dataset="d", natural_key="r1", fields={}),
    ]
    counts = stage.stage_records(conn, "batch", recs)
    assert counts == {t: 1 for t in
                      ("source_raw", "claim_raw", "claim_qa_raw", "excluded_raw", "reconcile_raw")}
    tables_hit = {c[0].split()[2] for c in conn.calls}   # "INSERT INTO staging.<table>"
    assert tables_hit == {f"staging.{t}" for t in
                          ("source_raw", "claim_raw", "claim_qa_raw", "excluded_raw", "reconcile_raw")}
    for sql, params in conn.calls:
        assert "ON CONFLICT (batch_id, dataset_code, natural_key)" in sql
        assert params[0] == "batch" and params[1] == "d"


def test_stage_records_rejects_unknown_target():
    conn = FakeConn()
    bad = StagingRecord(target="bogus_raw", dataset="d", natural_key="x", fields={})
    try:
        stage.stage_records(conn, "batch", [bad])
        assert False, "should have raised"
    except ValueError:
        pass


def test_persist_validation_updates_and_quarantines():
    conn = FakeConn()
    ok = Outcome(natural_key="CLM-1", target="claim_raw", dataset="d", status="valid")
    bad = Outcome(natural_key="CLM-2", target="claim_raw", dataset="d", status="quarantine",
                 errors=["bad id"])
    report = ValidationReport(dataset="d", outcomes=[ok, bad])
    summary = stage.persist_validation(conn, "batch", "d", report)
    assert summary == {"updated": 2, "quarantined": 1}
    updates = [c for c in conn.calls if c[0].startswith("UPDATE staging.claim_raw")]
    assert len(updates) == 2
    quarantines = [c for c in conn.calls if c[0].startswith("INSERT INTO quarantine.record")]
    assert len(quarantines) == 1
    assert quarantines[0][1][2] == "claim"          # entity_type derived from target
    assert quarantines[0][1][6] == "validate"        # source_step


def test_persist_reconciliation_inserts_rows_and_dedupes_quarantine():
    conn = FakeConn()
    res = ReconResult(
        rows=[ReconRow("C", "l", "r", "claim", "CLM-1", "claim_text", "mismatch", True)],
        quarantine_recommendations=[
            QuarantineRec(dataset="d1", entity_type="claim", entity_ref="CLM-1",
                          reasons=["mismatch on claim_text"]),
            QuarantineRec(dataset="d1", entity_type="claim", entity_ref="CLM-1",
                          reasons=["duplicate should be deduped"]),
        ],
    )
    summary = stage.persist_reconciliation(conn, "batch", res)
    assert summary["rows"] == 1
    inserts_recon = [c for c in conn.calls
                     if c[0].startswith("INSERT INTO staging.reconciliation_result")]
    assert len(inserts_recon) == 1
    quarantines = [c for c in conn.calls if c[0].startswith("INSERT INTO quarantine.record")]
    assert len(quarantines) == 1                      # deduped
    assert quarantines[0][1][6] == "reconcile"
