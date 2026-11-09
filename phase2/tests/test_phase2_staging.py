"""Staging reconciliation / load: SQL wiring against a fake connection, pure reconciliation logic, and
(DATABASE_URL-gated) live checks that canonical stays empty and nothing is duplicated or approved."""

from __future__ import annotations

import json
import sys

import pytest

from phase2 import paths, staging
from phase2.build import build
from phase2.loaders import Record, load_all

pytestmark = pytest.mark.skipif(not (paths.PRODUCTION_JSON.exists() and paths.EXPANSION_CLAIMS.exists()),
                                reason="inputs missing")


class _Res:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    """Records every statement; `existing` simulates rows staging already holds."""

    def __init__(self, existing_keys=None, quarantined=None, claim_fields=None):
        self.calls: list[tuple[str, tuple]] = []
        self.existing_keys = existing_keys or {}
        self.quarantined = quarantined or []
        self.claim_fields = claim_fields or {}

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if sql.startswith("SELECT natural_key FROM staging."):
            table = sql.split("staging.")[1].split()[0]
            return _Res([(k,) for k in self.existing_keys.get((table, params[1]), [])])
        if sql.startswith("SELECT dataset_code, natural_key, fields FROM staging.claim_raw"):
            return _Res([(d, k, f) for (d, k), f in self.claim_fields.items()])
        if sql.startswith("SELECT dataset_code, natural_key FROM quarantine.record"):
            return _Res(self.quarantined)
        return _Res()

    def writes(self):
        return [c for c in self.calls if c[0].lstrip().startswith(("INSERT", "DELETE", "UPDATE"))]


@pytest.fixture(scope="module")
def inv():
    records, summaries = load_all()
    return build(records=list(records), summaries=summaries), records


def test_plan_mode_issues_no_writes(inv):
    result, records = inv
    conn = FakeConn()
    staging.load(conn, "b1", result, records, apply=False)
    assert conn.writes() == []


def test_apply_writes_only_to_staging_and_quarantine_never_canonical(inv):
    result, records = inv
    conn = FakeConn()
    staging.load(conn, "b1", result, records, apply=True)
    assert conn.writes()
    for sql, _ in conn.writes():
        assert "canonical." not in sql
        assert any(t in sql for t in ("staging.source_raw", "staging.claim_raw", "staging.claim_qa_raw",
                                      "quarantine.record"))


def test_never_writes_prototype_or_baseline_rows(inv):
    result, records = inv
    conn = FakeConn()
    staging.load(conn, "b1", result, records, apply=True)
    for sql, params in conn.writes():
        if "staging.claim_raw" in sql or "staging.source_raw" in sql:
            assert params[1] == paths.DS_EXPANSION        # dataset_code of every source/claim row written
        if "staging.claim_qa_raw" in sql:
            assert params[1] == staging.ANNOTATION_DATASET


def test_nothing_is_marked_approved_or_valid_without_flags(inv):
    result, records = inv
    conn = FakeConn()
    staging.load(conn, "b1", result, records, apply=True)
    for sql, params in conn.writes():
        if "staging.claim_raw" in sql:
            assert params[6] in ("valid_with_flags", "quarantine")      # never plain 'valid' / approved
            assert "pending_owner_review" in params[8]
        if "staging.claim_qa_raw" in sql:
            assert json.loads(params[3])["approved"] is False


def test_rerun_reports_already_present_and_still_idempotent(inv):
    result, records = inv
    claim_ids = [r["claim_id"] for r in result["claims"] if r["originating_dataset"] == paths.DS_EXPANSION]
    ann = [r["record_id"] for r in staging.nonproduction_rows(result)]
    conn = FakeConn(existing_keys={("claim_raw", paths.DS_EXPANSION): claim_ids,
                                   ("source_raw", paths.DS_EXPANSION): ["SRC-028", "SRC-033", "SRC-034"],
                                   ("claim_qa_raw", staging.ANNOTATION_DATASET): ann})
    s = staging.load(conn, "b1", result, records, apply=False)
    assert s["expansion_claims"]["to_insert"] == [] and len(s["expansion_claims"]["already_present"]) == len(claim_ids)
    assert s["annotations"]["to_insert"] == 0
    c2 = FakeConn()
    staging.load(c2, "b1", result, records, apply=True)
    assert all("ON CONFLICT (batch_id, dataset_code, natural_key) DO UPDATE" in sql
               for sql, _ in c2.writes() if sql.startswith("INSERT INTO staging."))


def test_quarantine_covers_every_non_usable_nonproduction_record_and_skips_already_quarantined(inv):
    result, records = inv
    conn = FakeConn(quarantined=[("baseline-register", "CLM-083")])
    s = staging.load(conn, "b1", result, records, apply=True)
    non_usable = [r for r in staging.nonproduction_rows(result) if r["status"] in staging.NON_USABLE]
    assert s["quarantine"]["non_usable_nonproduction"] == len(non_usable)
    assert "baseline-register:CLM-083" in s["quarantine"]["already_quarantined_by_other_step"]
    inserted = [p for sql, p in conn.writes() if sql.startswith("INSERT INTO quarantine.record")]
    assert len(inserted) == len(non_usable) - 1
    assert all(p[6] == staging.QUARANTINE_STEP for p in inserted)
    # only this module's own earlier rows are deleted before re-insert
    deletes = [(sql, p) for sql, p in conn.writes() if sql.startswith("DELETE")]
    assert deletes and all("source_step=%s" in sql and p[1] == staging.QUARANTINE_STEP for sql, p in deletes)


def test_usable_candidates_are_never_quarantined(inv):
    result, records = inv
    conn = FakeConn()
    staging.load(conn, "b1", result, records, apply=True)
    usable = {r["claim_id"] for r in staging.nonproduction_rows(result) if r["status"] == "usable"}
    quarantined = {p[3] for sql, p in conn.writes() if sql.startswith("INSERT INTO quarantine.record")}
    assert not usable & quarantined


# ------------------------------------------------------------------ pure reconciliation
def _rec(**kw):
    base = dict(dataset=paths.DS_BASELINE, claim_id="CLM-1", source_id="SRC-1", claim_text="T", excerpt="E",
                locator="L", source_url="U", uc_applicability=["ibd_general"])
    base.update(kw)
    return Record(**base)


def test_compare_reports_missing_and_mismatched_without_proposing_inserts():
    existing = {(paths.DS_BASELINE, "CLM-1"): {"claim_text": "DIFFERENT", "supporting_excerpt": "E",
                                               "precise_locator": "L", "authoritative_url": "U",
                                               "condition_applicability": ["ibd_general"]}}
    out = staging.compare_to_staging([_rec(), _rec(claim_id="CLM-2")], existing)
    b = out[paths.DS_BASELINE]
    assert b["present_in_staging"] == 1 and b["missing_from_staging"] == ["CLM-2"]
    assert b["content_mismatches"] == [{"claim_id": "CLM-1", "fields": ["claim_text"]}]


def test_expansion_staging_fields_use_adapter_names(inv):
    result, _ = inv
    row = next(r for r in result["claims"] if r["originating_dataset"] == paths.DS_EXPANSION)
    raw = {c["claimId"]: c for c in json.loads(paths.EXPANSION_CLAIMS.read_text())["claims"]}[row["claim_id"]]
    f = staging.staging_claim_fields(row, raw)
    assert {"claim_ref", "source_ref", "claim_text", "supporting_excerpt", "precise_locator",
            "authoritative_url", "condition_applicability"} <= set(f)
    assert f["claim_text"] == raw["normalizedClaim"]


# ------------------------------------------------------------------ owner review
def test_owner_review_lists_every_usable_uc_applicable_nonproduction_record_and_approves_nothing(inv):
    from phase2.review import render, review_candidates

    result, _ = inv
    uc, general = review_candidates(result)
    expected = [r for r in result["claims"] if r["originating_dataset"] != paths.DS_PRODUCTION
                and r["status"] == "usable" and r["applicability_class"] == "uc_specific"]
    assert [r["record_id"] for r in uc] == [r["record_id"] for r in expected] and uc
    text = render(result)
    for r in uc + general:
        assert r["claim_text"] in text and r["supporting_excerpt"] in text and r["locator"] in text
    assert "[x]" not in text.lower() and text.count("Owner decision") == len(uc) + len(general)


# ------------------------------------------------------------------ live dev DB (gated)
@pytest.fixture()
def live():
    sys.path.insert(0, str(paths.REPO / "db"))
    from pipeline.config import load_env

    s = load_env()
    if not s.has_db:
        pytest.skip("needs DATABASE_URL (dev)")
    from pipeline.db import connect

    c = connect(s)
    try:
        yield c
    finally:
        c.rollback()
        c.close()


def test_live_canonical_still_only_prototype_v1_and_empty_of_phase2(live):
    n = dict(live.execute("SELECT d.code, (SELECT count(*) FROM canonical.claim c WHERE c.dataset_id=d.dataset_id) "
                          "FROM canonical.dataset d").fetchall())
    assert n.get("prototype-v1") == 49 and n.get("baseline-register", 0) == 0
    assert paths.DS_EXPANSION not in n
    (cnt,) = live.execute("SELECT count(*) FROM canonical.claim").fetchone()
    assert cnt == 49


def test_live_no_duplicate_prototype_or_baseline_rows(live):
    dups = live.execute("SELECT dataset_code, natural_key, count(*) FROM staging.claim_raw "
                        "GROUP BY batch_id, dataset_code, natural_key HAVING count(*) > 1").fetchall()
    assert dups == []
    got = dict(live.execute("SELECT dataset_code, count(*) FROM staging.claim_raw "
                            "WHERE dataset_code IN ('prototype-v1','baseline-register') GROUP BY 1").fetchall())
    assert got == {"prototype-v1": 49, "baseline-register": 61}


def test_live_phase2_rows_are_pending_review_never_approved(live):
    rows = live.execute("SELECT validation_status, fields->>'review_status' FROM staging.claim_raw "
                        "WHERE dataset_code=%s", (paths.DS_EXPANSION,)).fetchall()
    if not rows:
        pytest.skip("phase-2 load not applied yet")
    assert {s for s, _ in rows} <= {"valid_with_flags", "quarantine"}
    assert all(r == "pending_clinical_review" for _, r in rows)
    (appr,) = live.execute("SELECT count(*) FROM staging.claim_qa_raw WHERE dataset_code=%s "
                           "AND (fields->>'approved')::boolean", (staging.ANNOTATION_DATASET,)).fetchone()
    assert appr == 0
