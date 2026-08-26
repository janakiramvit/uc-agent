"""QA evaluator: deterministic checks (agent_core.qa_checks) remain the
base signal; the LLM's holistic verdict is layered on top as additional
recorded detail, never replacing the deterministic report."""

from unittest.mock import patch

from agent_core.llm_qa_evaluator import QAEvaluatorOutput, make_llm_qa_evaluator_node


def test_deterministic_report_always_present_alongside_llm(package):
    node = make_llm_qa_evaluator_node(package)
    mocked = QAEvaluatorOutput(passed=True, issues=[])
    with patch("agent_core.llm_qa_evaluator.call_structured", return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5")):
        state = {"draft_answer": "no citations here", "draft_citations": [], "gap_terms": [], "visited_nodes": [], "trace": []}
        result = node(state)
    assert "overall_pass" in result["qa_report"]  # deterministic checks present
    assert result["qa_report"]["llm_evaluation"]["passed"] is True


def test_llm_can_flag_additional_issues(package):
    node = make_llm_qa_evaluator_node(package)
    mocked = QAEvaluatorOutput(passed=False, issues=["tone reads as prescriptive"])
    with patch("agent_core.llm_qa_evaluator.call_structured", return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5")):
        state = {"draft_answer": "you should do this", "draft_citations": [], "gap_terms": [], "visited_nodes": [], "trace": []}
        result = node(state)
    assert result["qa_report"]["llm_evaluation"]["issues"] == ["tone reads as prescriptive"]


def test_falls_back_to_deterministic_only_when_unconfigured(package, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_llm_qa_evaluator_node(package)
    state = {"draft_answer": "no citations here", "draft_citations": [], "gap_terms": [], "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["qa_report"]["llm_evaluation"]["mode"] == "deterministic_fallback"
    assert "overall_pass" in result["qa_report"]
