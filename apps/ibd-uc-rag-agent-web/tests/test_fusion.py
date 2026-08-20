"""Fusion/reranking correctness, and proof that vector retrieval -- when
it does run -- genuinely participates in the fused candidate set that
flows into applicability checking, conflict detection, and synthesis
(not just a side-channel that gets computed and discarded)."""

from unittest.mock import patch

from agent_core.fusion import fuse_candidates, reciprocal_rank_fusion
from agent_core.graph_v2 import run_graph_v2
from agent_core.llm_synthesizer import LLMResult
from agent_core.retrieval import RetrievedClaim
from agent_core.vector_retrieval import VectorMatch


def test_rrf_single_list_preserves_order():
    fused = reciprocal_rank_fusion([["a", "b", "c"]])
    assert fused == ["a", "b", "c"]


def test_rrf_boosts_items_ranked_high_in_both_lists():
    bm25 = ["a", "b", "c"]
    vector = ["b", "a", "c"]
    fused = reciprocal_rank_fusion([bm25, vector])
    # 'a' and 'b' both rank in the top two of both lists; 'c' is last in both.
    assert fused[-1] == "c"
    assert set(fused[:2]) == {"a", "b"}


def test_rrf_surfaces_vector_only_item_not_in_bm25_list():
    bm25 = ["a", "b"]
    vector = ["z", "a"]
    fused = reciprocal_rank_fusion([bm25, vector])
    assert "z" in fused


def _claim(claim_id, topic="fibre"):
    return RetrievedClaim(
        claim_id=claim_id,
        source_title="t",
        source_url="u",
        claim_text="c",
        supporting_excerpt="e",
        exact_locator="l",
        evidence_level="guideline",
        confidence="moderate",
        limitations="",
        applicability_limitations="",
        topic=topic,
        outcome_type="o",
        condition_applicability="ulcerative_colitis",
        disease_context="d",
    )


def test_fuse_candidates_passthrough_when_vector_not_used(package):
    bm25_claims = [_claim("CLM-014"), _claim("CLM-094")]
    fused, report = fuse_candidates(package, bm25_claims, vector_matches=[], vector_used=False)
    assert [c.claim_id for c in fused] == ["CLM-014", "CLM-094"]
    assert report.vector_used is False
    assert report.vector_ids == []


def test_fuse_candidates_resolves_vector_only_claim_from_package(package):
    """CLM-095 (alcohol) is real and UC-eligible but not in the BM25
    result for this synthetic example -- fusion must still resolve it
    from the package so it can be verified/cited downstream."""
    bm25_claims = [_claim("CLM-014")]
    vector_matches = [{"claimId": "CLM-095", "score": 0.9}, {"claimId": "CLM-014", "score": 0.5}]
    fused, report = fuse_candidates(package, bm25_claims, vector_matches, vector_used=True)
    fused_ids = [c.claim_id for c in fused]
    assert "CLM-095" in fused_ids
    assert report.vector_used is True
    assert report.vector_ids == ["CLM-095", "CLM-014"]


def test_full_graph_vector_only_hit_reaches_final_citations(graph, package):
    """End-to-end proof that vector retrieval is wired into the answer
    workflow, not decorative. The query classifies to the 'fibre' topic,
    which makes BM25 structurally topic-filter its candidates to
    CLM-014/CLM-094 only (alcohol's CLM-095 is excluded before BM25 even
    ranks anything). Mocking the embeddings call to surface CLM-095
    anyway proves fusion genuinely adds a claim BM25 could not have
    returned, and that it survives applicability checking through to the
    final citations returned to the user -- not merely computed and
    discarded."""

    def fake_vector_retrieve(pkg, query, top_k=5):
        return [VectorMatch(claim_id="CLM-095", score=0.95)]

    good_llm = LLMResult(text="[1] Grounded synthesis citing the retrieved evidence.", provider="test", model="test-model")

    with patch("agent_core.vector_retrieval.vector_retrieve", side_effect=fake_vector_retrieve), \
         patch("agent_core.graph_v2.synthesize_with_llm", return_value=good_llm):
        result = run_graph_v2(graph, "Is fibre good for ulcerative colitis?")

    assert result["fusion_report"]["bm25_ids"] == ["CLM-014", "CLM-094"]
    assert result["vector_retrieval_status"] == "ok"
    assert result["fusion_report"]["vector_used"] is True
    assert "CLM-095" in result["fusion_report"]["fused_ids"]
    cited_ids = {c["claimId"] for c in result["citations"]}
    assert "CLM-095" in cited_ids, "a vector-only hit must survive through to the final citations, not be discarded"
