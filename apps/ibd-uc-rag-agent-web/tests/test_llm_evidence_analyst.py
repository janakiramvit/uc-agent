"""Evidence analyst: consumes prior graph state (verified_claims), and a
hallucinated claim ID in its structured output must never survive into
the recorded analysis -- proof that invalid model output cannot smuggle
evidence that was never actually retrieved."""

from unittest.mock import patch

from agent_core.llm_evidence_analyst import ClaimRelevance, EvidenceAnalysisOutput, make_llm_evidence_analyst_node


def test_falls_back_deterministically_when_unconfigured(monkeypatch, retriever):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    node = make_llm_evidence_analyst_node()
    state = {"query": "Is fibre good?", "verified_claims": verified, "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["evidence_analysis"]["mode"] == "deterministic_fallback"
    assert result["evidence_analysis"]["sufficiency"] == "sufficient"


def test_insufficient_when_no_verified_claims_and_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_evidence_analyst_node()
    state = {"query": "anything", "verified_claims": [], "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["evidence_analysis"]["sufficiency"] == "insufficient"


def test_prior_state_consumption_only_analyzes_what_was_actually_retrieved(retriever):
    """The node must be handed the real verified_claims from prior graph
    state (not re-retrieve on its own) -- confirmed by mocking the model
    call and asserting the prompt it received contains exactly those
    claim IDs and no others."""
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    node = make_llm_evidence_analyst_node()
    mocked = EvidenceAnalysisOutput(sufficiency="sufficient", key_points=["a point"], per_claim=[])

    captured_prompts = {}

    def fake_call_structured(category, schema, system_prompt, user_prompt, **kwargs):
        captured_prompts["user_prompt"] = user_prompt
        return mocked, "ok", "anthropic", "claude-sonnet-4-5"

    with patch("agent_core.llm_evidence_analyst.call_structured", side_effect=fake_call_structured):
        state = {"query": "Is fibre good?", "verified_claims": verified, "visited_nodes": [], "trace": []}
        node(state)

    for c in verified:
        assert c.claim_id in captured_prompts["user_prompt"]


def test_hallucinated_claim_id_is_dropped_and_flagged(retriever):
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    real_id = verified[0].claim_id
    node = make_llm_evidence_analyst_node()
    mocked = EvidenceAnalysisOutput(
        sufficiency="sufficient",
        key_points=[],
        per_claim=[
            ClaimRelevance(claim_id=real_id, relevance="high", note="real"),
            ClaimRelevance(claim_id="CLM-999-FAKE", relevance="high", note="hallucinated"),
        ],
    )
    with patch(
        "agent_core.llm_evidence_analyst.call_structured",
        return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"query": "Is fibre good?", "verified_claims": verified, "visited_nodes": [], "trace": []}
        result = node(state)

    kept_ids = {c["claim_id"] for c in result["evidence_analysis"]["per_claim"]}
    assert kept_ids == {real_id}
    assert result["evidence_analysis"]["dropped_hallucinated_claim_ids"] == ["CLM-999-FAKE"]
