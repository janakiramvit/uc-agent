"""Safety critic: combined verdict = deterministic AND llm. Proves an
LLM saying "this is fine" can NEVER override a deterministic safety
failure -- the core "invalid/lenient model output cannot bypass
safeguards" guarantee for this node."""

from unittest.mock import patch

from agent_core.llm_safety_critic import SafetyCriticOutput, make_llm_safety_critic_node


def test_llm_cannot_override_a_deterministic_failure():
    """The draft contains diagnosis language (deterministic regex catches
    it), but the mocked LLM claims passed=True. The combined result must
    still fail -- this is the load-bearing assertion for this file."""
    node = make_llm_safety_critic_node()
    unsafe_draft = "You have ulcerative colitis based on this evidence."
    lenient_llm = SafetyCriticOutput(passed=True, concerns=[])
    with patch(
        "agent_core.llm_safety_critic.call_structured",
        return_value=(lenient_llm, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"draft_answer": unsafe_draft, "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["safety_critic_result"]["passed"] is False
    assert result["safety_critic_result"]["deterministic_passed"] is False
    assert result["safety_critic_result"]["llm_passed"] is True  # recorded, but did not win


def test_llm_can_fail_a_deterministically_passing_draft():
    """The LLM can only make things STRICTER: a draft that passes the
    regex check can still be failed by the model's own judgment."""
    node = make_llm_safety_critic_node()
    safe_looking_draft = "[1] The evidence reports an association between fibre and UC outcomes."
    strict_llm = SafetyCriticOutput(passed=False, concerns=["subtle overreach the regex missed"])
    with patch(
        "agent_core.llm_safety_critic.call_structured",
        return_value=(strict_llm, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"draft_answer": safe_looking_draft, "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["safety_critic_result"]["passed"] is False
    assert result["safety_critic_result"]["deterministic_passed"] is True


def test_both_pass_when_draft_is_genuinely_safe():
    node = make_llm_safety_critic_node()
    safe_draft = "[1] The evidence reports an association between fibre and UC outcomes."
    good_llm = SafetyCriticOutput(passed=True, concerns=[])
    with patch(
        "agent_core.llm_safety_critic.call_structured",
        return_value=(good_llm, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"draft_answer": safe_draft, "visited_nodes": [], "trace": []}
        result = node(state)
    assert result["safety_critic_result"]["passed"] is True


def test_falls_back_to_deterministic_alone_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_safety_critic_node()

    unsafe_draft = "You should stop taking your medication now."
    state = {"draft_answer": unsafe_draft, "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["safety_critic_result"]["mode"] == "deterministic_fallback"
    assert result["safety_critic_result"]["passed"] is False  # deterministic alone still catches it

    safe_draft = "[1] The evidence reports an association between fibre and UC outcomes."
    state2 = {"draft_answer": safe_draft, "visited_nodes": [], "trace": []}
    result2 = node(state2)
    assert result2["safety_critic_result"]["passed"] is True
