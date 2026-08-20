"""Unsupported-topic queries must short-circuit to the fixed fallback
BEFORE ever reaching the LLM synthesizer -- no API key should be needed
to correctly refuse to answer what the evidence doesn't cover."""

import pytest

from agent_core.graph_v2 import run_graph_v2
from agent_core.safety_rules import UNSUPPORTED_TOPIC_MESSAGE

UNSUPPORTED_QUERIES = [
    "What does ESR tell me about my UC?",
    "What does CRP tell me about my UC?",
    "What does fecal calprotectin tell me about my UC?",
    "What does biologics evidence say about UC?",
    "What do JAK inhibitors do for UC?",
    "Does mucosal healing matter in UC?",
]


@pytest.mark.parametrize("query", UNSUPPORTED_QUERIES)
def test_unsupported_topic_returns_fixed_fallback_without_llm(graph, query):
    result = run_graph_v2(graph, query)
    assert result["status"] == "unsupported"
    assert result["answer"] == UNSUPPORTED_TOPIC_MESSAGE
    assert result["citations"] == []
    # The LLM synthesizer must never have run for a known-gap query.
    assert "evidence_synthesizer" not in result["visited_nodes"]


def test_unsupported_query_never_reaches_llm_unavailable_status(graph):
    """Distinguishes 'we don't have evidence for this' (unsupported) from
    'we have evidence but no LLM key' (llm_unavailable) -- these must not
    collapse into the same status."""
    result = run_graph_v2(graph, "What does ESR tell me about my UC?")
    assert result["status"] != "llm_unavailable"
