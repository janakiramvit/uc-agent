"""After promotion to dev canonical (skipped until promoted): parity with the approved preview, RLS/reader-role security,
retirements, and rollback readiness. All read-only - no destructive test is run against the populated database."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from release import pilot_db

REPO = pilot_db.REPO
sys.path.insert(0, str(REPO / "db"))
sys.path.insert(0, str(REPO / "apps" / "ibd-uc-rag-agent-web" / "api"))


@pytest.fixture()
def live():
    from pipeline.config import load_env
    s = load_env()
    if not s.has_db:
        pytest.skip("needs DATABASE_URL (dev)")
    from pipeline.db import connect
    c = connect(s)
    try:
        if not c.execute("SELECT 1 FROM canonical.dataset WHERE code='pilot-additions'").fetchall():
            pytest.skip("pilot not promoted yet")
        yield c
    finally:
        c.rollback()
        c.close()


def _reader_dsn():
    env = REPO / "db" / ".env.reader"
    if not env.exists():
        pytest.skip("no reader login file")
    for line in env.read_text().splitlines():
        if line.startswith("EVIDENCE_SUPABASE_DB_URL="):
            return line.split("=", 1)[1].strip()
    pytest.skip("reader DSN missing")


def test_promoted_rows_equal_the_approved_preview_exactly(live):
    pv = json.loads((REPO / "release" / "output" / "promotion-preview.json").read_text())
    got = {r[0]: r for r in live.execute(
        "SELECT claim_ref, claim_text, supporting_excerpt, review_status_raw, review_status, condition_applicability_raw "
        "FROM canonical.claim c JOIN canonical.dataset d USING (dataset_id) WHERE d.code='pilot-additions'").fetchall()}
    assert sorted(got) == sorted(c["claim_ref"] for c in pv["claims"])
    for c in pv["claims"]:
        r = got[c["claim_ref"]]
        assert (r[1], r[2], r[3], r[4], r[5]) == (c["claim_text"], c["supporting_excerpt"], "owner_reviewed_for_pilot", None,
                                                  c["condition_applicability_raw"])


def test_nothing_in_canonical_is_marked_clinician_approved(live):
    (n,) = live.execute("SELECT count(*) FROM canonical.claim WHERE review_status = 'approved' OR review_status_raw ILIKE '%clinician%'").fetchone()
    assert n == 0


def test_deferred_candidate_and_retired_claims_are_excluded_from_the_pilot_package(live):
    ex = {r[0] for r in live.execute("SELECT claim_ref FROM canonical.v_pilot_excluded_claim_id").fetchall()}
    assert {"CLM-014", "CLM-093", "CLM-094", "CLM-081", "CLM-095", "CLM-126", "CLM-702"} <= ex
    assert "CLM-703" not in {r[0] for r in live.execute("SELECT claim_ref FROM canonical.claim").fetchall()}
    for ref in ("CLM-126", "CLM-702", "CLM-703", "CLM-244"):
        assert not live.execute("SELECT 1 FROM canonical.claim WHERE claim_ref=%s", (ref,)).fetchall()


def test_prototype_v1_is_byte_untouched_and_preserves_the_retired_claims(live):
    (n,) = live.execute("SELECT count(*) FROM canonical.v_prototype_claim").fetchone()
    assert n == 49
    got = {r[0] for r in live.execute("SELECT \"claimId\" FROM canonical.v_prototype_claim").fetchall()}
    assert {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"} <= got


def test_forced_rls_still_on_for_every_base_table(live):
    rows = live.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN "
                        "('canonical','staging','quarantine') AND c.relkind='r' AND NOT c.relforcerowsecurity").fetchall()
    assert rows == []


def test_reader_role_reads_pilot_views_but_not_staging_quarantine_or_base_tables_and_cannot_write():
    import psycopg
    conn = psycopg.connect(_reader_dsn(), connect_timeout=15, autocommit=True)
    try:
        (n,) = conn.execute("SELECT count(*) FROM canonical.v_pilot_claim").fetchone()
        assert n == 59
        for table in ("canonical.claim", "canonical.source", "canonical.excluded_claim", "staging.claim_raw", "staging.claim_qa_raw",
                      "quarantine.record", "canonical.dataset"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
        for stmt in ("INSERT INTO canonical.excluded_claim (dataset_id, claim_ref) VALUES (1, 'X')",
                     "DELETE FROM canonical.v_pilot_claim", "UPDATE canonical.v_pilot_claim SET \"claimId\"='x'"):
            with pytest.raises(Exception):
                conn.execute(stmt)
    finally:
        conn.close()


def test_app_loader_pilot_package_matches_expectations_and_never_falls_back_to_json(monkeypatch):
    pytest.importorskip("langchain_core")      # needs the app's environment (run under the app venv)
    from agent_core.supabase_evidence_source import load_evidence_package_from_db
    monkeypatch.setenv("EVIDENCE_SUPABASE_DB_URL", _reader_dsn())
    monkeypatch.setenv("EVIDENCE_DATASET", "pilot")
    p = load_evidence_package_from_db()
    assert p.backend == "supabase" and p.dataset == "pilot"
    ids = sorted(c["claimId"] for c in p.uc_eligible_claims)
    assert ids == ["CLM-115", "CLM-116", "CLM-117", "CLM-118", "CLM-119", "CLM-120", "CLM-121", "CLM-701", "CLM-705", "CLM-706"]
    assert not {"CLM-014", "CLM-093", "CLM-094", "CLM-081", "CLM-095"} & {c["claimId"] for c in p.all_claims}
    assert p.source_counts()["trialRecords"] == 0


def test_rollback_readiness_switching_the_dataset_restores_the_previous_live_set_without_any_write(monkeypatch):
    pytest.importorskip("langchain_core")      # needs the app's environment (run under the app venv)
    from agent_core.supabase_evidence_source import load_evidence_package_from_db
    monkeypatch.setenv("EVIDENCE_SUPABASE_DB_URL", _reader_dsn())
    monkeypatch.setenv("EVIDENCE_DATASET", "prototype-v1")
    p = load_evidence_package_from_db()
    assert sorted(c["claimId"] for c in p.uc_eligible_claims) == ["CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"]


def test_file_backend_rollback_still_loads_the_original_package(monkeypatch):
    pytest.importorskip("langchain_core")      # needs the app's environment (run under the app venv)
    from agent_core.evidence_loader import load_evidence_package
    p = load_evidence_package()
    assert p.backend == "file" and len(p.all_claims) == 49
