"""Citation grounding: the LLM synthesizer must never be able to invent a
citation, because citations are constructed independently from the
verified evidence (never parsed out of model free text); and the
citation_verifier node must independently catch it if one ever slipped
through some future code path."""

from unittest.mock import patch

from agent_core.graph_v2 import make_llm_evidence_synthesizer_node
from agent_core.llm_synthesizer import LLMResult
from agent_core.subagents import make_citation_verifier_node


def test_synthesizer_citations_always_come_from_verified_claims(package, retriever):
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    assert verified, "fixture expects fibre to retrieve at least one UC-eligible claim"

    node = make_llm_evidence_synthesizer_node()
    state = {
        "query": "Is fibre good for UC?",
        "verified_claims": verified,
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
    }
    with patch(
        "agent_core.graph_v2.synthesize_with_llm",
        return_value=LLMResult(text="Grounded answer citing [1].", provider="test", model="test-model"),
    ):
        result = node(state)

    real_ids = {c.claim_id for c in verified}
    cited_ids = {c["claimId"] for c in result["draft_citations"]}
    assert cited_ids == real_ids
    assert result["llm_error"] is None


def test_citation_verifier_catches_fabricated_citation(package):
    verifier = make_citation_verifier_node(package)
    state = {
        "visited_nodes": [],
        "trace": [],
        "draft_citations": [
            {
                "claimId": "CLM-999-FAKE",
                "sourceUrl": "https://example.invalid/fabricated",
                "supportingExcerpt": "Fabricated excerpt.",
                "exactLocator": "p.0",
            }
        ],
    }
    result = verifier(state)
    assert result["citation_verifier_result"]["passed"] is False
    assert result["citation_verifier_result"]["mismatches"][0]["reason"] == "unknown_claim_id"


def test_citation_verifier_passes_real_untouched_citation(package):
    real_claim = package.all_claims[0]
    verifier = make_citation_verifier_node(package)
    state = {
        "visited_nodes": [],
        "trace": [],
        "draft_citations": [
            {
                "claimId": real_claim["claimId"],
                "sourceUrl": real_claim["sourceUrl"],
                "supportingExcerpt": real_claim["supportingExcerpt"],
                "exactLocator": real_claim["exactLocator"],
            }
        ],
    }
    result = verifier(state)
    assert result["citation_verifier_result"]["passed"] is True


def test_citation_verifier_catches_tampered_excerpt(package):
    real_claim = package.all_claims[0]
    verifier = make_citation_verifier_node(package)
    state = {
        "visited_nodes": [],
        "trace": [],
        "draft_citations": [
            {
                "claimId": real_claim["claimId"],
                "sourceUrl": real_claim["sourceUrl"],
                "supportingExcerpt": "This excerpt was silently altered from the original.",
                "exactLocator": real_claim["exactLocator"],
            }
        ],
    }
    result = verifier(state)
    assert result["citation_verifier_result"]["passed"] is False
    assert result["citation_verifier_result"]["mismatches"][0]["reason"] == "excerpt_mismatch"
