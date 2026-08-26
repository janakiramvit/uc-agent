"""Model-powered planner: structured decisions, DYNAMIC tool selection
(the model's chosen tool_calls are actually executed via the real
deterministic tools, not just recorded as a label), compound-query
decomposition, hallucinated-topic rejection, and safe fallback."""

from unittest.mock import patch

from agent_core.llm_planner import PlannedToolCall, PlannerOutput, make_llm_planner_node
from agent_core.tools import MCPToolContext

TOPIC_VOCAB = ["fibre", "alcohol", "fruit_vegetables", "core_condition_knowledge"]


def test_planner_falls_back_deterministically_when_unconfigured(package, retriever, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["plan"]["mode"] == "deterministic_fallback"
    assert result["plan"]["identified_topics"] == ["fibre"]


def test_planner_dynamic_tool_selection_actually_executes_real_tool(package, retriever):
    """The model 'chose' to call search_uc_claims -- prove that choice is
    dispatched to the REAL deterministic tool (not decorative): the
    returned tool_results must contain genuine UC-eligible claims."""
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    mocked_output = PlannerOutput(
        identified_topics=["fibre"],
        tool_calls=[PlannedToolCall(tool="search_uc_claims", query="fibre", topic="fibre")],
        reasoning="test",
    )
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["plan"]["mode"] == "llm"
    tool_results = result["plan"]["tool_results"]
    assert len(tool_results) == 1
    assert tool_results[0]["tool"] == "search_uc_claims"
    claim_ids = {c["claimId"] for c in tool_results[0]["result"]["claims"]}
    assert claim_ids == {"CLM-014", "CLM-094"}
    assert result["plan"]["planner_sourced_claim_ids"] == ["CLM-014", "CLM-094"]


def test_planner_dynamic_tool_selection_can_choose_a_different_tool(package, retriever):
    """Proves selection is genuinely dynamic, not hardcoded to one tool:
    the model choosing check_claim_applicability instead must dispatch to
    THAT function, not search_uc_claims."""
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    mocked_output = PlannerOutput(
        identified_topics=[],
        tool_calls=[PlannedToolCall(tool="check_claim_applicability", claim_id="CLM-014")],
        reasoning="test",
    )
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "Is CLM-014 relevant?", "visited_nodes": [], "trace": []}
        result = node(state)

    tool_results = result["plan"]["tool_results"]
    assert tool_results[0]["tool"] == "check_claim_applicability"
    assert tool_results[0]["result"]["status"] == "uc_eligible"


def test_compound_query_decomposition_via_llm(package, retriever):
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    mocked_output = PlannerOutput(identified_topics=["fibre", "alcohol"], tool_calls=[], reasoning="two topics")
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "What about fibre and alcohol?", "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["plan"]["identified_topics"] == ["fibre", "alcohol"]
    assert "retrieve_evidence_per_subtopic" in result["plan"]["steps"]


def test_hallucinated_topic_is_rejected_not_trusted(package, retriever):
    """The model naming a topic that doesn't exist in the real vocabulary
    must never leak into identified_topics -- that would let an LLM
    invent a routing category applicability filtering doesn't know about."""
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    mocked_output = PlannerOutput(identified_topics=["fibre", "biologics_NOT_REAL"], tool_calls=[], reasoning="")
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "fibre and biologics", "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["plan"]["identified_topics"] == ["fibre"]


def test_tool_calls_are_capped(package, retriever):
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    too_many = [PlannedToolCall(tool="list_supported_topics") for _ in range(10)]
    mocked_output = PlannerOutput(identified_topics=[], tool_calls=too_many, reasoning="")
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "anything", "visited_nodes": [], "trace": []}
        result = node(state)

    assert len(result["plan"]["tool_calls"]) <= 4
    assert len(result["plan"]["tool_results"]) <= 4


def test_a_failed_tool_call_does_not_crash_planning(package, retriever):
    ctx = MCPToolContext(package=package, retriever=retriever)
    node = make_llm_planner_node(TOPIC_VOCAB, ctx)
    mocked_output = PlannerOutput(
        identified_topics=[],
        tool_calls=[PlannedToolCall(tool="get_claim", claim_id=None)],
        reasoning="",
    )
    with patch(
        "agent_core.llm_planner.call_structured",
        return_value=(mocked_output, "ok", "anthropic", "claude-haiku-4-5"),
    ):
        state = {"query": "anything", "visited_nodes": [], "trace": []}
        result = node(state)
    # get_claim(ctx, "") should return found=False, not raise.
    assert result["plan"]["tool_results"][0]["result"]["found"] is False
