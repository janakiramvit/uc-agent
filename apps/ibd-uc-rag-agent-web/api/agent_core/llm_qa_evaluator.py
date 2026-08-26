"""Model-powered QA evaluator: a holistic final read layered on top of
the deterministic ``run_all_qa_checks`` (agent_core.qa_checks), which
remains the base pass/fail signal (unique claim IDs, source existence,
locator/excerpt presence, limitation preservation, no diagnosis/flare/
medication-change/diet-prescription/causation-upgrade language, correct
unsupported-topic fallback, etc.).

This node is INFORMATIONAL, matching the existing (pre-LLM) QA agent's
role in the graph: its verdict is recorded in the QA report for the
developer/trace panel but does not introduce a new gate on top of the
safety-critic/citation-verifier retry loop that already governs whether
an answer reaches the user. Fails safe to the deterministic report alone
when unavailable.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.model_router import call_structured
from agent_core.qa_checks import run_all_qa_checks as deterministic_run_all_qa_checks
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens


class QAEvaluatorOutput(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the final QA evaluator for a UC (ulcerative colitis) evidence answer. You \
are given the answer, its citations, and the results of automated structural checks (which already \
passed). Do a holistic read for anything those checks might miss: overclaiming beyond the cited \
evidence, tone that reads as medical advice rather than reviewed evidence, or a citation number in \
the text with no matching citation entry. List concrete issues only; passed=true if none."""


def _format_input(answer: str, citations: list[dict], deterministic_report: dict) -> str:
    citation_lines = [f"[{c.get('number')}] claimId={c.get('claimId')}" for c in citations]
    return (
        f"Answer:\n{answer}\n\nCitations:\n" + "\n".join(citation_lines) +
        f"\n\nAutomated checks overall_pass={deterministic_report.get('overall_pass')}"
    )


def make_llm_qa_evaluator_node(package):
    def llm_qa_evaluator_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("qa_agent")

        answer = state.get("draft_answer", "")
        citations = state.get("draft_citations", [])
        deterministic_report = deterministic_run_all_qa_checks(package, answer, citations, state.get("gap_terms", []))

        user_prompt = _format_input(answer, citations, deterministic_report)
        estimated = estimate_tokens(SYSTEM_PROMPT, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured("critic", QAEvaluatorOutput, SYSTEM_PROMPT, user_prompt)

        llm_section = (
            {"mode": "llm", "status": status, "provider": provider, "model": model, "passed": result.passed, "issues": result.issues}
            if result is not None
            else {"mode": "deterministic_fallback", "status": status}
        )

        qa_report = {**deterministic_report, "llm_evaluation": llm_section}
        state["qa_report"] = qa_report
        state.setdefault("trace", [])
        state["trace"].append({"node": "qa_agent", "output": qa_report})
        return state

    return llm_qa_evaluator_node
