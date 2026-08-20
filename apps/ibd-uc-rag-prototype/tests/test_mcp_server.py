"""Tests for the local, read-only MCP server (mcp_server/).

Covers: tool schemas (input/output shape), retrieval correctness (only
the 5-claim UC-eligible set is ever returned), the hard boundary that
Crohn's-only/excluded claim IDs are refused even when asked for
directly, and get_evidence_gaps' dynamic diff.
"""

from __future__ import annotations

import asyncio

import pytest

from mcp_server.tools import (
    MCPToolContext,
    check_claim_applicability,
    get_claim,
    get_evidence_gaps,
    get_source,
    list_supported_topics,
    search_uc_claims,
)

EXPECTED_UC_CLAIM_IDS = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}


@pytest.fixture
def ctx(package, retriever):
    return MCPToolContext(package=package, retriever=retriever)


# --- schema/shape ---------------------------------------------------------


def test_search_uc_claims_shape(ctx):
    result = search_uc_claims(ctx, "fibre")
    assert set(result.keys()) == {"query", "topic", "count", "claims"}
    assert isinstance(result["claims"], list)
    for c in result["claims"]:
        assert {"claimId", "sourceId", "sourceUrl", "supportingExcerpt", "exactLocator", "evidenceLevel", "limitations", "applicabilityLimitations"}.issubset(c.keys())


def test_get_claim_shape(ctx):
    result = get_claim(ctx, "CLM-014")
    assert set(result.keys()) == {"found", "claimId", "reason", "claim"}
    assert result["found"] is True
    assert result["claim"]["claimId"] == "CLM-014"


def test_get_source_shape(ctx, package):
    any_source_id = next(iter(package.sources_by_id))
    result = get_source(ctx, any_source_id)
    assert set(result.keys()) == {"found", "sourceId", "source"}
    assert result["found"] is True


def test_list_supported_topics_shape(ctx):
    result = list_supported_topics(ctx)
    assert set(result.keys()) == {"topics", "count"}
    assert result["count"] == len(result["topics"])


def test_check_claim_applicability_shape(ctx):
    result = check_claim_applicability(ctx, "CLM-014")
    assert set(result.keys()) == {"claimId", "status", "reason"}


def test_get_evidence_gaps_shape(ctx):
    result = get_evidence_gaps(ctx)
    assert set(result.keys()) == {"data_driven_gap_topics", "known_absent_categories", "all_gap_terms"}


# --- retrieval correctness ---------------------------------------------------------


def test_search_uc_claims_only_returns_uc_eligible(ctx):
    for q in ["fibre", "alcohol", "diet", "fruit", "vegetables", ""]:
        result = search_uc_claims(ctx, q)
        for c in result["claims"]:
            assert c["claimId"] in EXPECTED_UC_CLAIM_IDS
            assert "ulcerative_colitis" in c["conditionApplicability"]


def test_get_claim_refuses_crohns_only(ctx, package):
    crohns_id = package.crohns_only_claims[0]["claimId"]
    result = get_claim(ctx, crohns_id)
    assert result["found"] is False
    assert result["reason"] == "crohns_only_not_uc_eligible"
    assert result["claim"] is None


def test_get_claim_refuses_excluded_id(ctx, package):
    excluded_id = next(iter(package.excluded_claim_ids))
    result = get_claim(ctx, excluded_id)
    assert result["found"] is False
    assert result["reason"] == "excluded_claim"
    assert result["claim"] is None


def test_get_claim_refuses_unknown_id(ctx):
    result = get_claim(ctx, "CLM-DOES-NOT-EXIST")
    assert result["found"] is False
    assert result["reason"] == "unknown_claim_id"


def test_get_claim_accepts_all_five_uc_eligible_ids(ctx):
    for claim_id in EXPECTED_UC_CLAIM_IDS:
        result = get_claim(ctx, claim_id)
        assert result["found"] is True
        assert result["claim"]["claimId"] == claim_id


def test_check_claim_applicability_all_statuses(ctx, package):
    uc_result = check_claim_applicability(ctx, next(iter(EXPECTED_UC_CLAIM_IDS)))
    assert uc_result["status"] == "uc_eligible"

    crohns_id = package.crohns_only_claims[0]["claimId"]
    crohns_result = check_claim_applicability(ctx, crohns_id)
    assert crohns_result["status"] == "crohns_only"

    excluded_id = next(iter(package.excluded_claim_ids))
    excluded_result = check_claim_applicability(ctx, excluded_id)
    assert excluded_result["status"] == "excluded"

    unknown_result = check_claim_applicability(ctx, "CLM-NOPE")
    assert unknown_result["status"] == "unknown"


def test_list_supported_topics_reflects_five_claim_reality(ctx, package):
    result = list_supported_topics(ctx)
    expected_topics = {c["topic"] for c in package.uc_eligible_claims}
    assert set(result["topics"]) == expected_topics
    assert len(expected_topics) < 14  # much smaller than the full 49-claim topic list


def test_get_evidence_gaps_includes_esr_and_is_dynamic(ctx, package):
    result = get_evidence_gaps(ctx)
    assert "esr" in result["known_absent_categories"]
    assert "esr" in result["all_gap_terms"]
    uc_topics = {c["topic"] for c in package.uc_eligible_claims}
    for t in result["data_driven_gap_topics"]:
        assert t not in uc_topics  # every reported gap topic truly has zero UC-eligible claims


def test_get_source_unknown_id(ctx):
    result = get_source(ctx, "SRC-DOES-NOT-EXIST")
    assert result["found"] is False
    assert result["source"] is None


# --- claim data preservation ---------------------------------------------------------


def test_search_result_preserves_fields_verbatim(ctx, package):
    result = search_uc_claims(ctx, "fibre")
    claims_by_id = {c["claimId"]: c for c in package.uc_eligible_claims}
    assert result["claims"]
    for c in result["claims"]:
        original = claims_by_id[c["claimId"]]
        assert c["sourceUrl"] == original["sourceUrl"]
        assert c["supportingExcerpt"] == original["supportingExcerpt"]
        assert c["exactLocator"] == original["exactLocator"]
        assert c["limitations"] == original["limitations"]
        assert c["applicabilityLimitations"] == original["applicabilityLimitations"]


# --- server wiring (exactly 6 tools, no others) ---------------------------------------------------------


def test_mcp_server_exposes_exactly_six_tools():
    from mcp_server.server import mcp

    async def _list():
        return await mcp.list_tools()

    tools = asyncio.run(_list())
    names = {t.name for t in tools}
    assert names == {
        "search_uc_claims",
        "get_claim",
        "get_source",
        "list_supported_topics",
        "check_claim_applicability",
        "get_evidence_gaps",
    }


def test_mcp_server_smoke_call_each_tool():
    """Manual smoke test of each of the six tools via the underlying
    context object (the SDK doesn't offer a trivial synchronous local
    client, so we invoke the pure tool functions directly, which is what
    server.py's @mcp.tool()-decorated wrappers call unmodified)."""
    from app.evidence_loader import load_evidence_package
    from app.retrieval import build_retriever

    package = load_evidence_package()
    ctx = MCPToolContext(package=package, retriever=build_retriever(package))

    assert search_uc_claims(ctx, "fibre")["count"] >= 1
    assert get_claim(ctx, "CLM-014")["found"] is True
    any_source_id = next(iter(package.sources_by_id))
    assert get_source(ctx, any_source_id)["found"] is True
    assert list_supported_topics(ctx)["count"] >= 1
    assert check_claim_applicability(ctx, "CLM-014")["status"] == "uc_eligible"
    assert "esr" in get_evidence_gaps(ctx)["all_gap_terms"]
