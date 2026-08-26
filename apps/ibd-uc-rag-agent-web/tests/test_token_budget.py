"""Per-request token budget: deterministic, enforced in code BEFORE every
model call, and a model-powered node must actually skip its call (fail
safe) once the budget is exhausted -- not merely report a number."""

from unittest.mock import patch

from agent_core.rate_limit import DEFAULT_MAX_TOKENS_PER_REQUEST, check_and_consume_token_budget, estimate_tokens, remaining_token_budget


def test_estimate_tokens_is_conservative_and_positive():
    assert estimate_tokens("") >= 1
    assert estimate_tokens("a" * 400) >= 100


def test_budget_consumed_across_calls_within_one_state():
    state = {}
    assert check_and_consume_token_budget(state, 1000) is True
    assert check_and_consume_token_budget(state, 1000) is True
    assert state["_token_budget_used"] == 2000


def test_budget_exhaustion_blocks_further_consumption():
    state = {"_token_budget_used": DEFAULT_MAX_TOKENS_PER_REQUEST - 100}
    assert check_and_consume_token_budget(state, 50) is True
    assert check_and_consume_token_budget(state, 100) is False  # would exceed the cap
    assert state["_token_budget_used"] == DEFAULT_MAX_TOKENS_PER_REQUEST - 50  # rejected call did not consume


def test_remaining_budget_reporting():
    state = {"_token_budget_used": 3000}
    assert remaining_token_budget(state) == DEFAULT_MAX_TOKENS_PER_REQUEST - 3000


def test_budget_is_per_request_state_not_global():
    state_a = {}
    state_b = {}
    check_and_consume_token_budget(state_a, DEFAULT_MAX_TOKENS_PER_REQUEST)
    # A fresh state (new request) must not inherit state_a's exhaustion.
    assert check_and_consume_token_budget(state_b, 100) is True


def test_exhausted_budget_prevents_the_model_from_ever_being_called(retriever):
    """The load-bearing guarantee: once budget is exhausted, a
    model-powered node must not even attempt the call -- proven by
    patching call_structured to raise if invoked."""
    from agent_core.llm_evidence_analyst import make_llm_evidence_analyst_node

    node = make_llm_evidence_analyst_node()
    verified = retriever.retrieve(query="fibre", topic_filter="fibre")
    state = {
        "query": "Is fibre good?",
        "verified_claims": verified,
        "visited_nodes": [],
        "trace": [],
        "_token_budget_used": DEFAULT_MAX_TOKENS_PER_REQUEST,  # already exhausted
    }
    with patch("agent_core.llm_evidence_analyst.call_structured", side_effect=AssertionError("must not be called")):
        result = node(state)

    assert result["evidence_analysis"]["status"] == "token_budget_exceeded"
    assert result["evidence_analysis"]["mode"] == "deterministic_fallback"
