"""Model-powered query classifier and reformulator: safe fallback, and
proof that known_unsupported/classified_topic stay deterministic
regardless of LLM availability (they gate downstream applicability/gap
routing and must never depend on a model call succeeding)."""

from unittest.mock import patch

from agent_core.llm_query_understanding import (
    ClassifierOutput,
    ReformulationOutput,
    make_llm_query_classifier_node,
    make_llm_query_reformulator_node,
)

TOPIC_VOCAB = ["fibre", "alcohol", "fruit_vegetables", "core_condition_knowledge"]


def test_classifier_sets_known_unsupported_deterministically_even_without_llm(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_query_classifier_node(TOPIC_VOCAB)
    state = {"query": "What does ESR tell me about my UC?", "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["known_unsupported"] is True
    assert result["classifier_info"]["mode"] == "deterministic_fallback"


def test_classifier_falls_back_to_deterministic_intent(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_query_classifier_node(TOPIC_VOCAB)
    state = {"query": "Do I have UC?", "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["query_intent"] == "diagnosis_seeking"


def test_classifier_llm_success_sets_intent_and_topic():
    node = make_llm_query_classifier_node(TOPIC_VOCAB)
    mocked = ClassifierOutput(intent="question", primary_topic="fibre", rationale="")
    with patch("agent_core.llm_query_understanding.call_structured", return_value=(mocked, "ok", "anthropic", "claude-haiku-4-5")):
        state = {"query": "Is fibre good?", "visited_nodes": [], "trace": []}
        result = node(state)
    assert result["query_intent"] == "question"
    assert result["classified_topic"] == "fibre"
    assert result["classifier_info"]["mode"] == "llm"


def test_classifier_llm_hallucinated_topic_is_rejected():
    node = make_llm_query_classifier_node(TOPIC_VOCAB)
    mocked = ClassifierOutput(intent="question", primary_topic="not_a_real_topic", rationale="")
    with patch("agent_core.llm_query_understanding.call_structured", return_value=(mocked, "ok", "anthropic", "claude-haiku-4-5")):
        state = {"query": "Is fibre good?", "visited_nodes": [], "trace": []}
        result = node(state)
    # Falls back to the deterministic keyword match instead of trusting the invented topic.
    assert result["classified_topic"] == "fibre"


def test_reformulator_falls_back_to_original_query_unchanged(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_query_reformulator_node()
    state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["reformulated_query"] == "Is fibre good for UC?"
    assert result["reformulation_info"]["mode"] == "deterministic_fallback"


def test_reformulator_llm_success_widens_query():
    node = make_llm_query_reformulator_node()
    mocked = ReformulationOutput(reformulated_query="Is fibre or fiber good for UC?", added_terms=["fiber"], rationale="")
    with patch("agent_core.llm_query_understanding.call_structured", return_value=(mocked, "ok", "anthropic", "claude-haiku-4-5")):
        state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
        result = node(state)
    assert result["reformulated_query"] == "Is fibre or fiber good for UC?"
    assert result["reformulation_info"]["mode"] == "llm"


def test_reformulator_empty_llm_output_falls_back_safely():
    node = make_llm_query_reformulator_node()
    mocked = ReformulationOutput(reformulated_query="   ", added_terms=[], rationale="")
    with patch("agent_core.llm_query_understanding.call_structured", return_value=(mocked, "ok", "anthropic", "claude-haiku-4-5")):
        state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
        result = node(state)
    assert result["reformulated_query"] == "Is fibre good for UC?"
