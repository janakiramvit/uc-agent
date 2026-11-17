"""Live dev-DB reconciliation after `release.pilot_db stage` (skipped without DATABASE_URL). Read-only."""

from __future__ import annotations

import sys

import pytest

from release import pilot_db

sys.path.insert(0, str(pilot_db.REPO / "db"))


@pytest.fixture()
def live():
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


def _staged(live):
    (n,) = live.execute("SELECT count(*) FROM staging.claim_raw WHERE dataset_code=%s", (pilot_db.STAGING_DATASET,)).fetchone()
    return n


def test_staged_counts_match_the_frozen_inventory(live):
    if _staged(live) == 0:
        pytest.skip("release not staged yet")
    assert _staged(live) == 64
    (s,) = live.execute("SELECT count(*) FROM staging.source_raw WHERE dataset_code=%s", (pilot_db.STAGING_DATASET,)).fetchone()
    assert s == 74
    (a,) = live.execute("SELECT count(*) FROM staging.claim_qa_raw WHERE dataset_code=%s", (pilot_db.ANNOTATION_DATASET,)).fetchone()
    assert a == 128


def test_prototype_and_baseline_staging_rows_were_not_duplicated_or_changed(live):
    got = dict(live.execute("SELECT dataset_code, count(*) FROM staging.claim_raw WHERE dataset_code IN "
                            "('prototype-v1','baseline-register') GROUP BY 1").fetchall())
    assert got == {"prototype-v1": 49, "baseline-register": 61}
    assert live.execute("SELECT 1 FROM staging.claim_raw GROUP BY batch_id, dataset_code, natural_key HAVING count(*)>1").fetchall() == []


def test_nothing_is_owner_reviewed_approved_or_promoted_at_staging(live):
    (appr,) = live.execute("SELECT count(*) FROM staging.claim_qa_raw WHERE dataset_code=%s AND (fields->>'approved')::boolean",
                           (pilot_db.ANNOTATION_DATASET,)).fetchone()
    assert appr == 0                                    # nothing is ever marked approved
    (rev,) = live.execute("SELECT count(*) FROM staging.claim_qa_raw WHERE dataset_code=%s AND (fields->>'owner_reviewed')::boolean "
                          "AND fields->>'review_status_raw'='owner_reviewed_for_pilot'", (pilot_db.ANNOTATION_DATASET,)).fetchone()
    assert rev in (0, 15)                               # the 15 owner decisions, recorded only as owner_reviewed_for_pilot
    ds = dict(live.execute("SELECT code, status FROM canonical.dataset").fetchall())
    assert ds == {"prototype-v1": "promoted", "baseline-register": "staged"} or "pilot-additions" in ds
    (n,) = live.execute("SELECT count(*) FROM canonical.claim c JOIN canonical.dataset d USING (dataset_id) WHERE d.code='prototype-v1'").fetchone()
    assert n == 49


def test_hard_excluded_categories_are_quarantined_and_proposals_are_not(live):
    rows = live.execute("SELECT natural_key, validation_status, validation_flags FROM staging.claim_raw WHERE dataset_code=%s",
                        (pilot_db.STAGING_DATASET,)).fetchall()
    if not rows:
        pytest.skip("release not staged yet")
    status = {k: s for k, s, _ in rows}
    for cid in ("CLM-115", "CLM-126", "CLM-701", "CLM-702"):
        assert status[cid] == "valid_with_flags"
    assert status["CLM-122"] == "quarantine" and status["CLM-205"] != "quarantine"
    q = {k for (k,) in live.execute("SELECT natural_key FROM quarantine.record WHERE source_step=%s", (pilot_db.QUARANTINE_STEP,)).fetchall()}
    assert "CLM-115" not in q and "CLM-122" in q


def test_pilot_views_exist_return_prototype_rows_and_the_reader_role_can_read_only_views(live):
    (n,) = live.execute("SELECT count(*) FROM canonical.v_pilot_claim").fetchone()
    assert n >= 49
    assert live.execute("SELECT 1 FROM information_schema.role_table_grants WHERE grantee='evidence_reader' AND table_schema='canonical' "
                        "AND table_name IN ('claim','source','dataset')").fetchall() == []
