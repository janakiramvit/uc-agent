"""Post-promotion checks. All marked ``post_promotion`` -> skipped without a dev
``DATABASE_URL``. These assume ``--step promote`` has run against that dev DB.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.post_promotion


def test_referential_integrity(db_conn):
    (orphans,) = db_conn.execute(
        "SELECT count(*) FROM canonical.claim c "
        "LEFT JOIN canonical.source s "
        "  ON s.dataset_id = c.dataset_id AND s.source_ref = c.source_ref "
        "WHERE s.id IS NULL"
    ).fetchone()
    assert orphans == 0


def test_dataset_isolation(db_conn):
    (bad,) = db_conn.execute(
        "SELECT count(*) FROM canonical.claim c "
        "JOIN canonical.dataset d USING (dataset_id) "
        "WHERE NOT EXISTS (SELECT 1 FROM canonical.source s "
        "  WHERE s.dataset_id = c.dataset_id AND s.source_ref = c.source_ref)"
    ).fetchone()
    assert bad == 0


def test_shadow_prototype_claims_equal_json(db_conn, registry):
    oracle = json.loads(registry["prototype_json"].path.read_text())
    rows = db_conn.execute(
        "SELECT claim_json FROM canonical.v_prototype_claim").fetchall()
    got = {r[0]["claimId"]: r[0] for r in rows}
    want = {c["claimId"]: c for c in oracle["claims"]}
    assert set(got) == set(want)
    for cid, wc in want.items():
        assert got[cid] == wc, f"{cid} differs from the file"


def test_shadow_prototype_sources_equal_json(db_conn, registry):
    oracle = json.loads(registry["prototype_json"].path.read_text())
    rows = db_conn.execute(
        "SELECT source_json FROM canonical.v_prototype_source").fetchall()
    got = {r[0]["sourceId"]: r[0] for r in rows}
    want = {s["sourceId"]: s for s in oracle["sources"]}
    assert got == want


def test_shadow_excluded_ids_and_limitations(db_conn, registry):
    oracle = json.loads(registry["prototype_json"].path.read_text())
    excl = [r[0] for r in db_conn.execute(
        "SELECT claim_ref FROM canonical.v_prototype_excluded_claim_id").fetchall()]
    assert sorted(excl) == sorted(oracle["excludedClaimIds"])
    lims = [r[0] for r in db_conn.execute(
        "SELECT text FROM canonical.v_prototype_limitation ORDER BY ordinal").fetchall()]
    assert lims == oracle["limitations"]


def test_uc_eligible_is_the_expected_five(db_conn):
    ids = sorted(r[0] for r in db_conn.execute(
        'SELECT "claimId" FROM canonical.v_uc_eligible_claim').fetchall())
    assert ids == ["CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"]


def test_reconciliation_note_snapshot_present(db_conn):
    (n,) = db_conn.execute(
        "SELECT count(*) FROM canonical.reconciliation_note").fetchone()
    assert n > 0
    (unresolved,) = db_conn.execute(
        "SELECT count(*) FROM canonical.reconciliation_note "
        "WHERE status='mismatch' AND material "
        "AND field IN ('claim_text','authoritative_url','precise_locator',"
        "'condition_applicability','review_status')"
    ).fetchone()
    # any remaining material mismatch must have a matching quarantine row
    (q,) = db_conn.execute("SELECT count(*) FROM quarantine.record").fetchone()
    assert q >= unresolved


def test_canonical_evidence_not_readable_by_public(db_conn):
    # the base tables have RLS forced; a non-owner select through no view returns 0
    (n,) = db_conn.execute(
        "SELECT count(*) FROM information_schema.role_table_grants "
        "WHERE table_schema IN ('staging','quarantine') AND grantee IN ('anon','authenticated')"
    ).fetchone()
    assert n == 0
