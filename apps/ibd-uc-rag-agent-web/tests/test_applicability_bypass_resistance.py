"""Applicability filtering cannot be bypassed by an LLM-influenced input,
even a hostile/hallucinating one. This tests the actual attack surface:
fusion.py resolves vector- or planner-sourced claim IDs directly against
``package.all_claims`` (which still includes Crohn's-only claims, only
excluded-claim-ID claims are pre-filtered) -- so a Crohn's-only claim ID
injected via a manipulated vector match or planner tool call CAN enter
``candidate_claims`` through fusion. The deterministic
``source_applicability_checker`` that runs immediately after fusion must
still strip it back out before it ever reaches ``verified_claims`` /
citations / synthesis. This is defense in depth, and this test proves
the depth actually holds."""

from agent_core.fusion import fuse_candidates
from agent_core.subagents import make_source_applicability_checker_node


def _first_crohns_only_claim_id(package):
    return next(
        c["claimId"]
        for c in package.all_claims
        if c.get("conditionApplicability") == "crohns_disease"
    )


def test_crohns_only_claim_injected_via_vector_match_is_stripped_by_applicability_checker(package, retriever):
    crohns_id = _first_crohns_only_claim_id(package)
    bm25_claims = retriever.retrieve(query="fibre", topic_filter="fibre")

    # Simulate a hostile/hallucinated vector match surfacing a Crohn's-only claim.
    fused_claims, report = fuse_candidates(
        package,
        bm25_claims,
        vector_matches=[{"claimId": crohns_id, "score": 0.99}],
        vector_used=True,
    )
    # Fusion alone (by design) resolves any real claim ID -- confirm the
    # attack surface is real before proving the downstream gate closes it.
    assert crohns_id in [c.claim_id for c in fused_claims]

    checker = make_source_applicability_checker_node(package)
    state = {"candidate_claims": fused_claims, "visited_nodes": [], "trace": []}
    result = checker(state)

    verified_ids = {c.claim_id for c in result["verified_claims"]}
    assert crohns_id not in verified_ids, "Crohn's-only claim must never survive applicability checking"


def test_crohns_only_claim_injected_via_planner_tool_call_is_stripped(package, retriever):
    crohns_id = _first_crohns_only_claim_id(package)
    bm25_claims = retriever.retrieve(query="fibre", topic_filter="fibre")

    fused_claims, report = fuse_candidates(
        package,
        bm25_claims,
        vector_matches=[],
        vector_used=False,
        planner_ids=[crohns_id],
    )
    assert crohns_id in [c.claim_id for c in fused_claims]

    checker = make_source_applicability_checker_node(package)
    state = {"candidate_claims": fused_claims, "visited_nodes": [], "trace": []}
    result = checker(state)

    verified_ids = {c.claim_id for c in result["verified_claims"]}
    assert crohns_id not in verified_ids


def test_excluded_claim_id_is_not_even_resolvable_by_fusion(package, retriever):
    excluded_id = next(iter(package.excluded_claim_ids))
    bm25_claims = retriever.retrieve(query="fibre", topic_filter="fibre")

    fused_claims, report = fuse_candidates(
        package, bm25_claims, vector_matches=[{"claimId": excluded_id, "score": 0.99}], vector_used=True
    )
    assert excluded_id not in [c.claim_id for c in fused_claims]


def test_full_graph_never_cites_crohns_only_claim_even_with_manipulated_vector_output(graph, package):
    """End-to-end: patch vector_retrieve to inject a Crohn's-only claim ID
    for a real query, and confirm it never reaches the final citations."""
    from unittest.mock import patch

    from agent_core.llm_synthesizer import LLMResult
    from agent_core.vector_retrieval import VectorMatch

    crohns_id = _first_crohns_only_claim_id(package)

    def fake_vector_retrieve(pkg, query, top_k=5):
        return [VectorMatch(claim_id=crohns_id, score=0.99)]

    good_llm = LLMResult(text="[1] Grounded synthesis.", provider="test", model="test-model")

    with patch("agent_core.vector_retrieval.vector_retrieve", side_effect=fake_vector_retrieve), \
         patch("agent_core.graph_v2.synthesize_with_llm", return_value=good_llm):
        result = graph.invoke(
            {
                "query": "Is fibre good for ulcerative colitis?",
                "disease_filter": "ulcerative_colitis",
                "visited_nodes": [],
                "trace": [],
                "synthesis_attempts": 0,
            }
        )

    cited_ids = {c["claimId"] for c in result.get("citations", [])}
    assert crohns_id not in cited_ids
