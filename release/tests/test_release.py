"""Pilot release: inventory integrity, curation rules, review pack, staging/promotion SQL wiring (no database needed)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from release import inventory as inv
from release import pilot_db, review

REPO = inv.REPO
FROZEN = inv.FROZEN


@pytest.fixture(scope="module")
def built():
    b = pilot_db.build_all()
    return b


def test_cutoff_is_frozen_and_inputs_match_their_recorded_hashes():
    import hashlib
    cut = json.loads((FROZEN / "EVIDENCE-CUTOFF.json").read_text())
    assert cut["evidenceCutoffDate"] == "2026-11-17" and cut["stagingCommit"] == "9c7cd28"
    for rel, sha in cut["files"].items():
        assert hashlib.sha256((REPO / rel).read_bytes()).hexdigest() == sha, rel
    assert cut["counts"] == {"stagingSources": 73, "stagingClaims": 61}


def test_inventory_counts_and_exact_dedupe(built):
    r = built["inventory"]
    assert (r["sources_before"], r["sources_after"]) == (119, 99)
    assert (r["claims_before"], r["claims_after"]) == (171, 125)
    assert len(r["claim_decisions"]) == 46 and len(r["source_decisions"]) == 20
    assert r["source_id_collisions"] == []
    assert {c["claimId"] for c in r["claim_id_collisions"]} == {"CLM-081", "CLM-083", "CLM-085"}


def test_every_merged_source_shares_a_strong_identifier_or_exact_title_and_url(built):
    for d in built["inventory"]["source_decisions"]:
        assert set(d["matchedOn"]) & {"pmid", "doi", "url", "title"}


def test_every_staged_claim_has_exactly_one_curated_decision(built):
    staged = {c["claimId"] for c in json.loads((FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    cur = built["curation"]
    proposed_staged = {k for k in cur["proposed"] if not k.startswith("CLM-7")}
    assert proposed_staged | set(cur["deferred"]) == staged
    assert not proposed_staged & set(cur["deferred"])


def test_only_clearly_supported_uc_human_evidence_is_proposed(built):
    prop = [r for r in built["claim_rows"] if r["recommendation"] == "proposed_include"]
    assert prop and len(prop) == 10
    for r in prop:
        assert r["category"] in ("uc_specific_human", "ibd_general_with_uc_subgroup")
        assert r["evidenceType"] in ("clinical_guideline", "published_study")
        assert r["excerpt"] and r["locator"] and r["citationUrl"].startswith("https://") and r["limitations"] and r["strength"]
        assert r["patient"] and r["questions"]
    srcs = {s["gid"]: s for s in built["source_rows"]}
    for r in prop:
        assert srcs[r["sourceGroup"]]["category"] == "published_or_guideline"        # never trial / animal / case-report sources


def test_no_deferred_category_can_leak_into_proposals(built):
    bad = {"crohns_only", "animal_preclinical", "case_report", "trial_record", "conflicting", "ibd_general_unclear",
           "incomplete_or_unverifiable", "duplicate"}
    for r in built["claim_rows"]:
        if r["recommendation"] == "proposed_include":
            assert r["category"] not in bad


def test_trial_records_never_carry_claims(built):
    trial_sources = {s["keeper"] for s in built["source_rows"] if s["category"] == "trial_record"}
    for r in built["claim_rows"]:
        if r["origin"] == "staging":
            assert f"staging:{r['sourceId']}" not in trial_sources


def test_excerpt_of_every_staged_proposal_is_the_frozen_verbatim_excerpt_and_verified_in_the_public_abstract(built):
    raw = {c["claimId"]: c for c in json.loads((FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    summ = json.loads((REPO / "release" / "output" / "release-summary.json").read_text())
    for r in built["claim_rows"]:
        if r["recommendation"] == "proposed_include":
            if not r.get("authored"):
                assert r["excerpt"] == raw[r["claimId"]]["exactSupportingExcerpt"]
            assert summ["excerptVerification"][r["claimId"]]["verbatimInPublicAbstract"] is True


def test_authored_claim_ids_are_reserved_unique_and_never_reuse_an_existing_id(built):
    used = {c.claim_id for c in built["inventory"]["all_claims"]}
    for a in built["curation"]["authored_claims"]:
        n = int(a["claimId"].split("-")[1])
        assert 700 <= n <= 799 and a["claimId"] not in used


def test_patient_text_does_not_add_numbers_or_names_absent_from_the_excerpt(built):
    """Cheap overstatement guard: every number in a patient-facing claim must occur in the excerpt or the study description."""
    for r in built["claim_rows"]:
        if r["recommendation"] == "proposed_include":
            nums = set(re.findall(r"\d+(?:\.\d+)?", r["patient"]))
            allowed = set(re.findall(r"\d+(?:\.\d+)?", r["excerpt"] + " " + r["limitations"] + " " + r.get("population", "")
                                     + " " + r.get("studyDesignDetail", "")))
            assert nums <= allowed | {"8", "56", "2025"}, (r["claimId"], nums - allowed)


# ------------------------------------------------------------------ promotion preview
def _dec(*ids):
    return {"proposed": {i: "approve" for i in ids}}


def test_preview_contains_only_approved_claims_and_their_sources(built):
    pv = pilot_db.promotion_preview(built, _dec("CLM-115", "CLM-701"))
    assert [c["claim_ref"] for c in pv["claims"]] == ["CLM-115", "CLM-701"]
    assert {s["source_ref"] for s in pv["sources"]} == {"SRC-028", "SRC-141"}
    assert "CLM-115" not in pv["excludedClaimRefs"] and "CLM-244" in pv["excludedClaimRefs"]


def test_preview_refuses_to_approve_anything_that_was_not_proposed(built):
    with pytest.raises(ValueError):
        pilot_db.promotion_preview(built, _dec("CLM-244"))
    with pytest.raises(ValueError):
        pilot_db.promotion_preview(built, {"proposed": {"CLM-115": "yes"}})


def test_preview_rows_are_owner_reviewed_never_clinician_approved(built):
    pv = pilot_db.promotion_preview(built, _dec(*[k for k in built["curation"]["proposed"]]))
    for c in pv["claims"]:
        assert c["review_status_raw"] == "owner_reviewed_for_pilot" and c["review_status"] is None
        assert "approved" not in json.dumps({k: v for k, v in c.items() if k.startswith("review")}).lower()
        assert c["prototype_eligibility_status_raw"] == "prototype_eligible_with_limitation"
    assert "NOT clinician-approved" in pv["packageMeta"]["intended_use"]


def test_clm126_gets_a_uc_applicability_so_the_app_can_serve_its_explicit_uc_statement(built):
    pv = pilot_db.promotion_preview(built, _dec("CLM-126"))
    assert "ulcerative_colitis" in pv["claims"][0]["condition_applicability_raw"]


# ------------------------------------------------------------------ SQL wiring with a fake connection
class _R:
    def __init__(self, rows=None): self._r = rows or []
    def fetchall(self): return self._r
    def fetchone(self): return self._r[0] if self._r else None


class FakeConn:
    def __init__(self, dataset_exists=0):
        self.calls, self.dataset_exists = [], dataset_exists

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if sql.lstrip().startswith("SELECT batch_id FROM staging.ingest_batch"):
            return _R([("b1",)])
        if "SELECT dataset_code, natural_key FROM quarantine.record" in sql:
            return _R([("baseline-register", "CLM-083")])
        if "SELECT count(*) FROM canonical.dataset" in sql:
            return _R([(self.dataset_exists,)])
        if "RETURNING dataset_id" in sql:
            return _R([(42,)])
        return _R()

    def writes(self):
        return [c for c in self.calls if c[0].lstrip().startswith(("INSERT", "DELETE", "UPDATE"))]


def test_stage_apply_writes_only_staging_and_quarantine(built):
    conn = FakeConn()
    s = pilot_db.stage(conn, built, apply=True)
    assert conn.writes() and s["claimsUpserted"] == 63 and s["sourcesUpserted"] == 73
    for sql, _ in conn.writes():
        assert "canonical." not in sql and any(t in sql for t in ("staging.", "quarantine.record"))


def test_stage_plan_issues_no_writes(built):
    conn = FakeConn()
    pilot_db.stage(conn, built, apply=False)
    assert conn.writes() == []


def test_stage_quarantines_only_hard_excluded_categories_and_skips_already_quarantined(built):
    conn = FakeConn()
    pilot_db.stage(conn, built, apply=True)
    q = [p for sql, p in conn.writes() if sql.startswith("INSERT INTO quarantine.record")]
    assert q and all(p[6] == pilot_db.QUARANTINE_STEP for p in q)
    assert ("baseline-register", "CLM-083") not in {(p[1], p[3]) for p in q}
    cats = {json.loads(p[4])["category"] for p in q}
    assert cats <= set(pilot_db.HARD_EXCLUDE)


def test_stage_never_marks_anything_owner_reviewed_or_approved(built):
    conn = FakeConn()
    pilot_db.stage(conn, built, apply=True)
    for sql, p in conn.writes():
        if "staging.claim_qa_raw" in sql:
            f = json.loads(p[3])
            assert f["owner_reviewed"] is False and f["approved"] is False


def test_promote_requires_confirmation_and_refuses_a_second_promotion(built):
    pv = pilot_db.promotion_preview(built, _dec("CLM-115"))
    with pytest.raises(RuntimeError):
        pilot_db.promote(FakeConn(), pv, confirm=False)
    with pytest.raises(RuntimeError):
        pilot_db.promote(FakeConn(dataset_exists=1), pv, confirm=True)


def test_promote_writes_only_the_pilot_dataset_never_prototype_v1(built):
    pv = pilot_db.promotion_preview(built, _dec("CLM-115", "CLM-116"))
    conn = FakeConn()
    out = pilot_db.promote(conn, pv, confirm=True)
    assert out["claims"] == 2
    joined = " ".join(sql for sql, _ in conn.writes())
    assert "prototype-v1" not in joined
    assert not any(("UPDATE" in sql or "DELETE" in sql) and "canonical." in sql for sql, _ in conn.writes())
    ds = next(p for sql, p in conn.calls if "RETURNING dataset_id" in sql)
    assert ds[0] == "pilot-additions"
