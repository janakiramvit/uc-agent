"""Citation reviewer: an additive semantic check that only ever runs
after the deterministic citation_verifier already passed. Its role is to
be able to fail an answer the deterministic check missed (semantic
mismatch), never to rescue one the deterministic check would have caught
(it isn't even invoked in that case, by graph routing)."""

from unittest.mock import patch

from agent_core.llm_citation_reviewer import CitationReview, CitationReviewBatch, make_llm_citation_reviewer_node


def _draft_citation():
    return {
        "number": 1,
        "claimId": "CLM-014",
        "sourceTitle": "t",
        "sourceUrl": "u",
        "claimText": "Fibre intake was associated with improved outcomes.",
        "supportingExcerpt": "Fibre intake was associated with improved outcomes.",
        "exactLocator": "l",
    }


def test_flags_semantic_mismatch():
    node = make_llm_citation_reviewer_node()
    mocked = CitationReviewBatch(
        reviews=[CitationReview(claim_id="CLM-014", semantically_supported=False, concern="excerpt doesn't back the sentence")]
    )
    with patch("agent_core.llm_citation_reviewer.call_structured", return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5")):
        state = {
            "draft_answer": "[1] Fibre cures UC entirely.",
            "draft_citations": [_draft_citation()],
            "visited_nodes": [],
            "trace": [],
        }
        result = node(state)
    assert result["citation_review_result"]["passed"] is False


def test_passes_when_semantically_supported():
    node = make_llm_citation_reviewer_node()
    mocked = CitationReviewBatch(reviews=[CitationReview(claim_id="CLM-014", semantically_supported=True, concern="")])
    with patch("agent_core.llm_citation_reviewer.call_structured", return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5")):
        state = {
            "draft_answer": "[1] Fibre intake was associated with improved outcomes.",
            "draft_citations": [_draft_citation()],
            "visited_nodes": [],
            "trace": [],
        }
        result = node(state)
    assert result["citation_review_result"]["passed"] is True


def test_no_citations_is_a_trivial_pass():
    node = make_llm_citation_reviewer_node()
    state = {"draft_answer": "no evidence available", "draft_citations": [], "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["citation_review_result"]["passed"] is True
    assert result["citation_review_result"]["mode"] == "skipped"


def test_falls_back_to_pass_when_unconfigured_since_deterministic_already_passed(monkeypatch):
    """This node only runs after citation_verifier passed -- unavailability
    here must not block an already-verified answer."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_citation_reviewer_node()
    state = {
        "draft_answer": "[1] Fibre intake was associated with improved outcomes.",
        "draft_citations": [_draft_citation()],
        "visited_nodes": [],
        "trace": [],
    }
    result = node(state)
    assert result["citation_review_result"]["passed"] is True
    assert result["citation_review_result"]["mode"] == "deterministic_fallback"
