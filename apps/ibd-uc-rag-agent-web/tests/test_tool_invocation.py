"""Tool invocation behavior: the six read-only evidence tools that back
the tool-augmented RAG layer (search, get-claim, get-source,
list-topics, check-applicability, evidence-gaps)."""

import pytest

from agent_core.tools import (
    MCPToolContext,
    check_claim_applicability,
    compute_evidence_gaps,
    get_claim,
    get_evidence_gaps,
    get_source,
    list_supported_topics,
    search_uc_claims,
)

UC_ELIGIBLE_IDS = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}


@pytest.fixture
def ctx(package, retriever):
    return MCPToolContext(package=package, retriever=retriever)


def test_search_uc_claims_only_returns_uc_eligible(ctx):
    result = search_uc_claims(ctx, "fibre")
    assert result["count"] > 0
    for claim in result["claims"]:
        assert claim["claimId"] in UC_ELIGIBLE_IDS


def test_get_claim_returns_uc_eligible_claim(ctx):
    result = get_claim(ctx, "CLM-014")
    assert result["found"] is True
    assert result["claim"]["claimId"] == "CLM-014"


def test_get_claim_refuses_crohns_only_claim(ctx, package):
    crohns_only_ids = [
        c["claimId"]
        for c in package.all_claims
        if c.get("conditionApplicability") == "crohns_disease" and c["claimId"] not in package.excluded_claim_ids
    ]
    assert crohns_only_ids, "fixture expects at least one Crohn's-only claim in the package"
    result = get_claim(ctx, crohns_only_ids[0])
    assert result["found"] is False
    assert result["reason"] == "crohns_only_not_uc_eligible"


def test_get_claim_unknown_id(ctx):
    result = get_claim(ctx, "CLM-DOES-NOT-EXIST")
    assert result["found"] is False
    assert result["reason"] == "unknown_claim_id"


def test_get_source_known_and_unknown(ctx, package):
    known_source_id = next(iter(package.sources_by_id))
    found = get_source(ctx, known_source_id)
    assert found["found"] is True

    missing = get_source(ctx, "SRC-DOES-NOT-EXIST")
    assert missing["found"] is False


def test_list_supported_topics_reflects_5_claim_reality(ctx):
    result = list_supported_topics(ctx)
    assert result["count"] <= 5
    assert set(result["topics"]).issubset({"fibre", "alcohol", "fruit_vegetables", "core_condition_knowledge"})


def test_check_claim_applicability_statuses(ctx):
    assert check_claim_applicability(ctx, "CLM-014")["status"] == "uc_eligible"
    assert check_claim_applicability(ctx, "CLM-NOPE")["status"] == "unknown"


def test_compute_evidence_gaps_includes_known_absent_categories(package):
    gaps = compute_evidence_gaps(package)
    assert "esr" in gaps["known_absent_categories"] or any("esr" in g for g in gaps["known_absent_categories"])
    assert set(gaps["all_gap_terms"]) >= set(gaps["known_absent_categories"])


def test_get_evidence_gaps_tool_wraps_compute(ctx, package):
    via_tool = get_evidence_gaps(ctx)
    via_direct = compute_evidence_gaps(package)
    assert via_tool == via_direct
