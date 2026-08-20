"""Production agent graph (v2): the full stateful LangGraph pipeline
requested for the Next.js/Vercel rebuild.

Node sequence:
  receive_query -> planner -> query_classifier -> evidence_retriever (BM25)
  -> vector_retriever (embeddings, if configured) -> source_applicability_checker
  -> conflict_detector -> gap_detector -> check_safety_boundaries
  -> evidence_synthesizer (REAL LLM call) -> safety_critic -> citation_verifier
  -> qa_agent -> attach_citations_final
  (with refuse / fallback_if_unsupported / llm_unavailable exit paths, and a
  bounded retry loop back to evidence_synthesizer on safety-critic or
  citation-verifier failure, identical in shape to the deterministic
  prototype's retry policy)

This module composes ONLY: it reuses the unmodified, already-tested nodes
from ``agent_core.workflow`` / ``agent_core.subagents`` for everything
that does not require a model call (retrieval, applicability filtering,
gap detection, safety-boundary checks on the query, safety-critic review
of the draft, citation verification, QA checks), and adds exactly four
new nodes: planner, vector_retriever, conflict_detector, and an
LLM-backed evidence_synthesizer that replaces the deterministic template
synthesizer used by the prototype.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agent_core.conflict_detector import make_conflict_detector_node
from agent_core.evidence_loader import EvidencePackage
from agent_core.llm_synthesizer import LLMNotConfiguredError, synthesize_with_llm
from agent_core.planner import make_planner_node
from agent_core.qa_checks import run_all_qa_checks
from agent_core.retrieval import RetrievedClaim, UCEvidenceRetriever
from agent_core.safety_rules import mentions_symptoms_or_inflammation
from agent_core.subagents import (
    MAX_SYNTHESIS_ATTEMPTS,
    make_check_safety_boundaries_node,
    make_citation_verifier_node,
    make_evidence_retriever_node,
    make_gap_detector_node,
    make_qa_agent_node,
    make_query_classifier_node,
    make_safety_critic_node,
    make_source_applicability_checker_node,
    route_after_citation_verifier,
    route_after_gap_detector,
    route_after_query_safety,
    route_after_safety_critic,
)
from agent_core.vector_retrieval import make_vector_retriever_node
from agent_core.workflow import fallback_if_unsupported, make_receive_query


class GraphV2State(TypedDict, total=False):
    query: str
    topic_filter: Optional[str]
    disease_filter: str

    visited_nodes: list[str]
    trace: list[dict[str, Any]]
    plan: dict[str, Any]
    classified_topic: Optional[str]
    query_intent: str
    known_unsupported: bool
    candidate_claims: list[RetrievedClaim]
    verified_claims: list[RetrievedClaim]
    vector_retrieval_status: str
    vector_matches: list[dict[str, Any]]
    conflict_report: dict[str, Any]
    gap_terms: list[str]
    is_evidence_gap: bool
    safety_triggered: bool
    safety_message: str
    draft_answer: str
    draft_citations: list[dict[str, Any]]
    synthesis_attempts: int
    llm_provider: Optional[str]
    llm_model: Optional[str]
    llm_error: Optional[str]
    safety_critic_result: dict[str, Any]
    citation_verifier_result: dict[str, Any]
    stop_reason: Optional[str]
    qa_report: dict[str, Any]

    answer: str
    citations: list[dict[str, Any]]
    status: str  # "answered" | "unsupported" | "refused" | "llm_unavailable" | "error"
    show_symptom_caveat: bool


def _record(state: dict, node_name: str) -> None:
    state.setdefault("visited_nodes", [])
    state["visited_nodes"].append(node_name)


def _trace(state: dict, node_name: str, output: Any) -> None:
    state.setdefault("trace", [])
    state["trace"].append({"node": node_name, "output": output})


def make_llm_evidence_synthesizer_node():
    """Real-LLM-backed replacement for the prototype's deterministic
    template synthesizer. Citations are constructed independently from
    the verified evidence (never parsed out of the model's free text), so
    a hallucinated citation is structurally impossible here -- the model
    can only fail by writing prose that later fails the safety-critic or
    by summarizing the evidence poorly, both of which are checked
    downstream."""

    def evidence_synthesizer_node(state: dict) -> dict:
        _record(state, "evidence_synthesizer")
        attempts = state.get("synthesis_attempts", 0) + 1
        state["synthesis_attempts"] = attempts

        verified = state.get("verified_claims", [])

        try:
            result = synthesize_with_llm(state.get("query", ""), verified)
            state["draft_answer"] = result.text
            state["llm_provider"] = result.provider
            state["llm_model"] = result.model
            state["llm_error"] = None
        except LLMNotConfiguredError as exc:
            state["draft_answer"] = ""
            state["llm_error"] = f"not_configured: {exc}"
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any provider/timeout failure must surface, not crash the graph
            state["draft_answer"] = ""
            state["llm_error"] = f"provider_error: {exc}"

        citations = []
        for i, claim in enumerate(verified, start=1):
            citations.append(
                {
                    "number": i,
                    "claimId": claim.claim_id,
                    "sourceTitle": claim.source_title,
                    "sourceUrl": claim.source_url,
                    "claimText": claim.claim_text,
                    "supportingExcerpt": claim.supporting_excerpt,
                    "exactLocator": claim.exact_locator,
                    "evidenceLevel": claim.evidence_level,
                    "confidence": claim.confidence,
                    "limitations": claim.limitations,
                    "applicabilityLimitations": claim.applicability_limitations,
                }
            )
        state["draft_citations"] = citations
        state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
        _trace(
            state,
            "evidence_synthesizer",
            {
                "attempt": attempts,
                "llm_error": state.get("llm_error"),
                "provider": state.get("llm_provider"),
                "citation_count": len(citations),
            },
        )
        return state

    return evidence_synthesizer_node


def route_after_synthesis(state: dict) -> str:
    if state.get("llm_error"):
        return "llm_unavailable"
    return "safety_critic"


def llm_unavailable_response(state: dict) -> dict:
    _record(state, "llm_unavailable")
    state["answer"] = (
        "This deployment does not have a working LLM provider configured, so it cannot generate a "
        "grounded synthesis for this query. Set ANTHROPIC_API_KEY or OPENAI_API_KEY as an environment "
        f"variable and retry. Detail: {state.get('llm_error')}"
    )
    state["citations"] = []
    state["status"] = "llm_unavailable"
    state["show_symptom_caveat"] = False
    _trace(state, "llm_unavailable", {"llm_error": state.get("llm_error")})
    return state


def refuse_v2(state: dict) -> dict:
    _record(state, "refuse")
    stop_reason = state.get("stop_reason")
    if stop_reason is None:
        if state.get("safety_critic_result") and not state["safety_critic_result"].get("passed", True):
            stop_reason = "safety_critic_failed_after_retry"
        elif state.get("citation_verifier_result") and not state["citation_verifier_result"].get("passed", True):
            stop_reason = "citation_verifier_failed_after_retry"
    if stop_reason == "safety_critic_failed_after_retry":
        message = (
            "This prototype could not safely compose an answer to that request after a repair attempt, "
            "so it is refusing rather than returning unreviewed or unsafe text. Please rephrase, or "
            "consult your care team for anything diagnostic, medication-related, or individualized."
        )
    elif stop_reason == "citation_verifier_failed_after_retry":
        message = (
            "This prototype detected a citation that did not match the underlying reviewed evidence and "
            "could not repair it, so it is refusing rather than showing an unverifiable citation."
        )
    else:
        message = state.get("safety_message") or "This request cannot be fulfilled by this prototype."
    state["answer"] = message
    state["citations"] = []
    state["status"] = "refused"
    state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
    _trace(state, "refuse", {"stop_reason": stop_reason, "message": message})
    return state


def fallback_if_unsupported_v2(state: dict) -> dict:
    state = fallback_if_unsupported(state)
    state["visited_nodes"].pop()
    _record(state, "fallback_if_unsupported")
    _trace(state, "fallback_if_unsupported", {"answer": state["answer"]})
    return state


def attach_citations_final_v2(state: dict) -> dict:
    _record(state, "attach_citations_final")
    state["answer"] = state.get("draft_answer", "")
    state["citations"] = state.get("draft_citations", [])
    state["status"] = "answered" if state["citations"] else "unsupported"
    _trace(state, "attach_citations_final", {"status": state["status"], "citation_count": len(state["citations"])})
    return state


def build_graph_v2(package: EvidencePackage, retriever: UCEvidenceRetriever):
    topic_vocabulary = sorted({c["topic"] for c in package.uc_eligible_claims if c.get("topic")})

    graph = StateGraph(GraphV2State)

    graph.add_node("receive_query", make_receive_query)
    graph.add_node("planner", make_planner_node(topic_vocabulary))
    graph.add_node("query_classifier", make_query_classifier_node(topic_vocabulary))
    graph.add_node("evidence_retriever", make_evidence_retriever_node(retriever))
    graph.add_node("vector_retriever", make_vector_retriever_node(package))
    graph.add_node("source_applicability_checker", make_source_applicability_checker_node(package))
    graph.add_node("conflict_detector", make_conflict_detector_node())
    graph.add_node("gap_detector", make_gap_detector_node(package))
    graph.add_node("check_safety_boundaries", make_check_safety_boundaries_node())
    graph.add_node("evidence_synthesizer", make_llm_evidence_synthesizer_node())
    graph.add_node("safety_critic", make_safety_critic_node())
    graph.add_node("citation_verifier", make_citation_verifier_node(package))
    graph.add_node("qa_agent", make_qa_agent_node(package))
    graph.add_node("attach_citations_final", attach_citations_final_v2)
    graph.add_node("fallback_if_unsupported", fallback_if_unsupported_v2)
    graph.add_node("refuse", refuse_v2)
    graph.add_node("llm_unavailable", llm_unavailable_response)

    graph.set_entry_point("receive_query")
    graph.add_edge("receive_query", "planner")
    graph.add_edge("planner", "query_classifier")
    graph.add_edge("query_classifier", "evidence_retriever")
    graph.add_edge("evidence_retriever", "vector_retriever")
    graph.add_edge("vector_retriever", "source_applicability_checker")
    graph.add_edge("source_applicability_checker", "conflict_detector")
    graph.add_edge("conflict_detector", "gap_detector")
    graph.add_conditional_edges(
        "gap_detector",
        route_after_gap_detector,
        {"fallback_if_unsupported": "fallback_if_unsupported", "check_safety_boundaries": "check_safety_boundaries"},
    )
    graph.add_conditional_edges(
        "check_safety_boundaries",
        route_after_query_safety,
        {"refuse": "refuse", "evidence_synthesizer": "evidence_synthesizer"},
    )
    graph.add_conditional_edges(
        "evidence_synthesizer",
        route_after_synthesis,
        {"safety_critic": "safety_critic", "llm_unavailable": "llm_unavailable"},
    )
    graph.add_conditional_edges(
        "safety_critic",
        route_after_safety_critic,
        {
            "citation_verifier": "citation_verifier",
            "evidence_synthesizer": "evidence_synthesizer",
            "refuse": "refuse",
        },
    )
    graph.add_conditional_edges(
        "citation_verifier",
        route_after_citation_verifier,
        {"qa_agent": "qa_agent", "evidence_synthesizer": "evidence_synthesizer", "refuse": "refuse"},
    )
    graph.add_edge("qa_agent", "attach_citations_final")
    graph.add_edge("attach_citations_final", END)
    graph.add_edge("fallback_if_unsupported", END)
    graph.add_edge("refuse", END)
    graph.add_edge("llm_unavailable", END)

    return graph.compile()


def run_graph_v2(
    compiled_graph,
    query: str,
    topic_filter: str | None = None,
    disease_filter: str = "ulcerative_colitis",
) -> dict:
    initial_state: dict = {
        "query": query,
        "topic_filter": topic_filter,
        "disease_filter": disease_filter,
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
    }
    return compiled_graph.invoke(initial_state)
