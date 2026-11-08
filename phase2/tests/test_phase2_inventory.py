"""Checkpoint-1 inventory: completeness, exact-duplicate handling, classification, traceability.

Synthetic-record tests always run. Real-data tests run when the local inputs are present
(some are untracked research files) and skip otherwise - they never fall back to fabricated data.
"""

from __future__ import annotations

import json

import pytest

from phase2 import paths
from phase2.build import build
from phase2.classify import applicability_class, classify, find_conflicts
from phase2.coverage import assign_question_ids, compute_coverage
from phase2.dedupe import dedupe_exact
from phase2.loaders import Record, load_daily, load_expansion, load_production


def rec(**kw) -> Record:
    base = dict(dataset=paths.DS_PRODUCTION, claim_id="CLM-001", source_id="SRC-001",
                source_url="https://example.org/a", claim_text="Claim A.", excerpt="Excerpt A.",
                locator="Section 1", publication_date="2024", uc_applicability=["ulcerative_colitis"],
                evidence_status="prototype_eligible")
    base.update(kw)
    return Record(**base)


# ---------------------------------------------------------------- classification
def test_usable_requires_everything():
    assert classify(rec(), {})[0] == "usable"


@pytest.mark.parametrize("kw,expected", [
    ({"uc_applicability": ["crohns_disease"]}, "crohns_only"),
    ({"excerpt": None}, "unverifiable"),
    ({"locator": None}, "unverifiable"),
    ({"source_url": None}, "unverifiable"),
    ({"source_resolved": False}, "unverifiable"),
    ({"verification_status": "unverified"}, "unverifiable"),
    ({"uc_applicability": []}, "incomplete"),
    ({"evidence_status": "still_needs_evidence"}, "incomplete"),
    ({"publication_date": None}, "incomplete"),
    ({"declared_conflict_note": "Conflicts with SRC-004 on dose."}, "conflicting"),
])
def test_status_rules(kw, expected):
    assert classify(rec(**kw), {})[0] == expected


def test_declared_consistency_is_not_a_conflict():
    r = rec(declared_conflict_note="Consistent in direction with STRIDE-II.")
    assert classify(r, {})[0] == "usable"


def test_precedence_crohns_over_unverifiable_but_reasons_kept():
    status, reasons = classify(rec(uc_applicability=["crohns_disease"], excerpt=None), {})
    assert status == "crohns_only"
    assert any(x.startswith("unverifiable") for x in reasons)


def test_ibd_general_is_usable_but_not_uc_specific():
    assert applicability_class(["ibd_general"]) == "ibd_general"
    assert classify(rec(uc_applicability=["ibd_general"]), {})[0] == "usable"
    assert applicability_class(["ulcerative_colitis", "crohns_disease"]) == "uc_specific"


def test_cross_dataset_applicability_disagreement_is_conflicting_missing_is_not():
    a = rec(uc_applicability=["crohns_disease"])
    b = rec(dataset=paths.DS_BASELINE, uc_applicability=["ulcerative_colitis"])
    c = rec(dataset=paths.DS_EXPANSION, claim_id="CLM-002")
    d = rec(dataset=paths.DS_BASELINE, claim_id="CLM-002", uc_applicability=[])
    conflicts = find_conflicts([a, b, c, d])
    assert "prototype-v1:CLM-001" in conflicts and "baseline-register:CLM-001" in conflicts
    assert not any(k.endswith("CLM-002") for k in conflicts)      # empty != disagreement


# ---------------------------------------------------------------- exact dedupe
def test_exact_duplicates_collapse_across_and_within_datasets():
    rows = [rec(), rec(dataset=paths.DS_BASELINE), rec(dataset=paths.DS_BASELINE)]
    out = dedupe_exact(rows)
    assert (out.before, out.after) == (3, 1)
    assert out.kept[0].dataset == paths.DS_PRODUCTION            # production wins retention
    assert len(out.merged["prototype-v1:CLM-001"]) == 2


def test_dedupe_keeps_incomplete_and_conflicting_variants():
    rows = [rec(), rec(dataset=paths.DS_BASELINE, uc_applicability=[]),
            rec(dataset=paths.DS_BASELINE, claim_text="Claim A, reworded.")]
    assert dedupe_exact(rows).after == 3


def test_same_text_different_claim_id_is_not_a_duplicate():
    assert dedupe_exact([rec(), rec(claim_id="CLM-002")]).after == 2


def test_dedupe_does_not_mutate_inputs_count():
    rows = [rec(), rec()]
    dedupe_exact(rows)
    assert len(rows) == 2


# ---------------------------------------------------------------- coverage
def _questions():
    return [
        {"question_id": "L1-1", "level": 1, "parent_question_id": None, "question": "p", "urgency_clinical_risk": None, "prior_tree_coverage": None},
        {"question_id": "L3-1", "level": 3, "parent_question_id": "L1-1", "question": "a", "urgency_clinical_risk": None, "prior_tree_coverage": None},
        {"question_id": "L3-2", "level": 3, "parent_question_id": "L1-1", "question": "b", "urgency_clinical_risk": None, "prior_tree_coverage": None},
    ]


def _row(qids, status="usable", app="uc_specific", prod=True, cid="CLM-1"):
    return {"claim_id": cid, "mapped_question_ids": qids, "status": status,
            "applicability_class": app, "in_production": prod}


def test_leaf_covered_partial_not_covered_and_rollup():
    rows = [_row(["L3-1"]), _row(["L3-2"], app="ibd_general", cid="CLM-2")]
    cov = compute_coverage(_questions(), rows)
    s = {q: v["scopes"]["all_possessed"]["status"] for q, v in cov["questions"].items()}
    assert s == {"L1-1": "partial", "L3-1": "covered", "L3-2": "partial"}


def test_crohns_only_never_counts_toward_coverage():
    cov = compute_coverage(_questions(), [_row(["L3-1"], app="crohns_only", status="crohns_only")])
    q = cov["questions"]["L3-1"]["scopes"]["all_possessed"]
    assert q["status"] == "not_covered" and q["direct_claims"] == [] and q["crohns_only_not_counted"] == ["CLM-1"]


def test_non_production_evidence_does_not_count_as_production_servable():
    cov = compute_coverage(_questions(), [_row(["L3-1"], prod=False)])
    q = cov["questions"]["L3-1"]["scopes"]
    assert q["all_possessed"]["status"] == "covered" and q["production_servable"]["status"] == "not_covered"


def test_unmapped_topic_stays_unmapped():
    r = rec(topic="core_condition_knowledge")
    assign_question_ids([r])
    assert r.mapped_question_ids == [] and r.mapping_basis == "unmapped"


# ---------------------------------------------------------------- real data
needs_prod = pytest.mark.skipif(not paths.PRODUCTION_JSON.exists(), reason="production JSON missing")
needs_exp = pytest.mark.skipif(not paths.EXPANSION_CLAIMS.exists(), reason="expansion package not present")
needs_tree = pytest.mark.skipif(not paths.QUESTION_TREE.exists(), reason="question tree not present")


@pytest.fixture(scope="module")
def result():
    if not (paths.PRODUCTION_JSON.exists() and paths.QUESTION_TREE.exists()):
        pytest.skip("inputs missing")
    return build()


@needs_prod
def test_production_inventory_is_complete():
    recs, summ = load_production()
    assert len(recs) == 49 and summ.source_rows == 20
    assert {r.claim_id for r in recs} == {c["claimId"] for c in json.loads(paths.PRODUCTION_JSON.read_text())["claims"]}


@needs_exp
def test_candidates_discovered_not_assumed():
    recs, _ = load_expansion()
    raw = json.loads(paths.EXPANSION_CLAIMS.read_text())["claims"]
    assert len(recs) == len(raw)                                  # whatever is on disk, no more, no less
    assert [r.claim_id for r in recs] == [c["claimId"] for c in raw]


@pytest.mark.skipif(not paths.DAILY_ARTIFACT_DIR.exists(), reason="daily artifacts not present")
def test_daily_discovery_runs_are_inventoried_but_hold_no_claims():
    recs, summ = load_daily()
    n = len(list(paths.DAILY_ARTIFACT_DIR.glob("redacted-run-*.json")))
    assert recs == [] and f"{n} redacted run report(s)" in summ.notes[0]


def test_every_loaded_record_is_in_manifest_or_merged(result):
    kept = {c["record_id"] for c in result["claims"]}
    merged = sum(len(v["collapsed"]) for v in result["dedupe_log"])
    assert result["counts"]["before_dedupe"] == result["counts"]["after_dedupe"] + merged
    assert len(kept) == result["counts"]["after_dedupe"]


def test_all_production_claims_survive_dedupe_in_production_dataset(result):
    prod = {c["claim_id"] for c in result["claims"] if c["originating_dataset"] == paths.DS_PRODUCTION}
    assert len(prod) == 49


def test_status_counts_sum_to_total_and_use_only_known_statuses(result):
    assert sum(result["counts"]["by_status"].values()) == result["counts"]["after_dedupe"]
    assert {c["status"] for c in result["claims"]} <= {"usable", "incomplete", "conflicting", "crohns_only", "unverifiable"}


def test_manifest_traceability_fields_present(result):
    required = {"claim_id", "source_id", "supporting_excerpt", "locator", "publication_date", "uc_applicability",
                "evidence_status", "originating_dataset", "content_hash", "status", "status_reasons"}
    for c in result["claims"]:
        assert required <= set(c)
        assert c["status"] != "usable" or (c["source_id"] and c["supporting_excerpt"] and c["locator"] and c["source_url"])
        assert c["status"] == "usable" or c["status_reasons"]


def test_known_clm083_baseline_conflict_is_flagged_and_prototype_stays_crohns_only(result):
    by = {c["record_id"]: c for c in result["claims"]}
    assert by["baseline-register:CLM-083"]["status"] == "conflicting"
    assert by["prototype-v1:CLM-083"]["status"] == "crohns_only"


def test_production_uc_eligible_set_is_unchanged(result):
    uc = sorted(c["claim_id"] for c in result["claims"]
                if c["originating_dataset"] == paths.DS_PRODUCTION and c["applicability_class"] == "uc_specific")
    assert uc == ["CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"]


@needs_tree
def test_coverage_covers_exactly_39_questions_with_valid_statuses(result):
    qs = result["coverage"]["questions"]
    assert len(qs) == 39
    for scope in ("production_servable", "all_possessed"):
        t = result["coverage"]["scopes"][scope]["all_39"]
        assert t["covered"] + t["partial"] + t["not_covered"] == 39
    assert all(v["scopes"][s]["status"] in ("covered", "partial", "not_covered")
               for v in qs.values() for s in v["scopes"])


def test_candidate_pending_review_is_never_production_servable(result):
    for c in result["claims"]:
        if c["originating_dataset"] == paths.DS_EXPANSION:
            assert c["in_production"] is False


def test_no_candidate_claim_ids_collide_with_production(result):
    prod = {c["claim_id"] for c in result["claims"] if c["originating_dataset"] == paths.DS_PRODUCTION}
    cand = {c["claim_id"] for c in result["claims"] if c["originating_dataset"] == paths.DS_EXPANSION}
    assert not prod & cand
