"""Production agent graph (v2): a genuine model-powered RAG agent, not a
deterministic retrieval pipeline with one bolted-on LLM call.

Full node sequence:
  receive_query -> planner (LLM, dynamic tool selection)
  -> query_classifier (LLM, intent -- informational, never overrides the
     hard safety gate below) -> query_reformulator (LLM, recall-widening
     only, never narrowing)
  -> evidence_retriever (BM25, planner- and reformulator-routed)
  -> vector_retriever (embeddings, when configured)
  -> fusion_reranker (Reciprocal Rank Fusion over BM25 + vector + the
     planner's own tool-call results -- three genuine ranked signals)
  -> source_applicability_checker (deterministic, non-bypassable)
  -> evidence_analyst (LLM, summarizes/rates ALREADY-verified claims only)
  -> conflict_detector (deterministic structural signal)
  -> conflict_resolver (LLM, classifies true-contradiction vs. which
     dimension differs -- NEVER drops either claim)
  -> gap_detector -> check_safety_boundaries (deterministic, hard,
     non-bypassable query-level refusal gate)
  -> evidence_synthesizer (LLM, the ONLY node whose text becomes the
     final answer; citations built independently, never parsed from
     model text)
  -> safety_critic (LLM verdict AND-ed with the deterministic regex
     verdict -- LLM can only make this stricter, never looser)
  -> citation_verifier (deterministic, non-bypassable existence/integrity
     check against the real evidence package)
  -> citation_reviewer (LLM, semantic-support check -- only runs after
     the deterministic check already passed)
  -> qa_agent (LLM verdict alongside the deterministic QA checks)
  -> attach_citations_final
  (bounded retry: safety_critic / citation_verifier / citation_reviewer
  failure routes back to evidence_synthesizer once, then hard-refuses;
  fallback_if_unsupported / refuse / llm_unavailable are terminal)

Every LLM-powered node fails safe: no configured provider, a timeout, a
provider error, or output that doesn't match its schema all degrade to a
deterministic fallback (documented per-node) rather than blocking or
crashing the graph, and the failure reason is recorded in the trace.

Deterministic tools remain non-bypassable by construction, not just by
convention: BM25 (agent_core.retrieval), vector retrieval + RRF fusion
(agent_core.vector_retrieval / agent_core.fusion), UC-applicability
filtering (agent_core.evidence_loader.is_uc_eligible/is_crohns_only, run
inside source_applicability_checker), citation existence/integrity
(agent_core.subagents.citation_verifier_node), the query-level safety
gate (agent_core.safety_rules.check_safety_boundaries), and request/token
limits (agent_core.rate_limit) all run in plain Python that no LLM output
can skip, relax, or redirect -- an LLM node can only ADD an opinion on
top of what these have already decided.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agent_core.conflict_detector import make_conflict_detector_node
from agent_core.evidence_loader import EvidencePackage
from agent_core.fusion import make_fusion_reranker_node
from agent_core.llm_citation_reviewer import make_llm_citation_reviewer_node
from agent_core.llm_conflict_resolver import make_llm_conflict_resolver_node
from agent_core.llm_evidence_analyst import make_llm_evidence_analyst_node
from agent_core.llm_planner import make_llm_planner_node
from agent_core.llm_qa_evaluator import make_llm_qa_evaluator_node
from agent_core.llm_query_understanding import (
    make_llm_query_classifier_node,
    make_llm_query_reformulator_node,
)
from agent_core.llm_safety_critic import make_llm_safety_critic_node
from agent_core.llm_synthesizer import LLMNotConfiguredError, synthesize_with_llm
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens
from agent_core.retrieval import RetrievedClaim, UCEvidenceRetriever
from agent_core.safety_rules import mentions_symptoms_or_inflammation
from agent_core.subagents import (
    MAX_SYNTHESIS_ATTEMPTS,
    make_check_safety_boundaries_node,
    make_citation_verifier_node,
    make_gap_detector_node,
    make_source_applicability_checker_node,
    route_after_gap_detector,
    route_after_query_safety,
)
from agent_core.tools import MCPToolContext
from agent_core.vector_retrieval import make_vector_retriever_node
from agent_core.workflow import fallback_if_unsupported, make_receive_query


def make_planned_evidence_retriever_node(retriever: UCEvidenceRetriever):
    """BM25 retrieval routed by BOTH the planner's identified sub-topics
    (one call per sub-topic when there's more than one) AND the
    reformulator's recall-widening query (an ADDITIONAL pass, unioned in
    -- never a replacement, so reformulation can only grow the candidate
    pool, never shrink it)."""

    def planned_evidence_retriever_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("evidence_retriever")

        if state.get("known_unsupported"):
            state["candidate_claims"] = []
            state.setdefault("trace", [])
            state["trace"].append({"node": "evidence_retriever", "output": {"skipped": "known_unsupported"}})
            return state

        query = state.get("query", "")
        reformulated_query = state.get("reformulated_query") or query
        disease_filter = state.get("disease_filter", "ulcerative_colitis")
        topics = (state.get("plan") or {}).get("identified_topics") or []

        merged: dict[str, RetrievedClaim] = {}
        per_topic_counts: dict[str, int] = {}

        if len(topics) > 1:
            for topic in topics:
                results = retriever.retrieve(query=query, topic_filter=topic, disease_filter=disease_filter)
                per_topic_counts[topic] = len(results)
                for claim in results:
                    merged.setdefault(claim.claim_id, claim)
            mode = "per_subtopic"
        else:
            for claim in retriever.retrieve(
                query=query, topic_filter=state.get("classified_topic"), disease_filter=disease_filter
            ):
                merged.setdefault(claim.claim_id, claim)
            mode = "single_query"

        reformulation_added = 0
        if reformulated_query.strip().lower() != query.strip().lower():
            for claim in retriever.retrieve(query=reformulated_query, topic_filter=None, disease_filter=disease_filter):
                if claim.claim_id not in merged:
                    merged[claim.claim_id] = claim
                    reformulation_added += 1

        candidate_claims = list(merged.values())
        state["candidate_claims"] = candidate_claims
        state.setdefault("trace", [])
        state["trace"].append(
            {
                "node": "evidence_retriever",
                "output": {
                    "mode": mode,
                    "topics": topics,
                    "counts_by_topic": per_topic_counts,
                    "reformulation_added_count": reformulation_added,
                    "candidate_claim_ids": [c.claim_id for c in candidate_claims],
                },
            }
        )
        return state

    return planned_evidence_retriever_node


class GraphV2State(TypedDict, total=False):
    query: str
    topic_filter: Optional[str]
    disease_filter: str

    visited_nodes: list[str]
    trace: list[dict[str, Any]]
    plan: dict[str, Any]
    classifier_info: dict[str, Any]
    reformulation_info: dict[str, Any]
    reformulated_query: str
    classified_topic: Optional[str]
    query_intent: str
    known_unsupported: bool
    candidate_claims: list[RetrievedClaim]
    verified_claims: list[RetrievedClaim]
    vector_retrieval_status: str
    vector_matches: list[dict[str, Any]]
    fusion_report: dict[str, Any]
    evidence_analysis: dict[str, Any]
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
    citation_review_result: dict[str, Any]
    stop_reason: Optional[str]
    qa_report: dict[str, Any]
    _token_budget_used: int

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
    """The one node whose real model call produces the final answer text.
    Citations are constructed independently from the verified evidence
    (never parsed out of the model's free text), so a hallucinated
    citation is structurally impossible here."""

    def evidence_synthesizer_node(state: dict) -> dict:
        _record(state, "evidence_synthesizer")
        attempts = state.get("synthesis_attempts", 0) + 1
        state["synthesis_attempts"] = attempts

        verified = state.get("verified_claims", [])
        evidence_text = " ".join(c.claim_text for c in verified)
        estimated = estimate_tokens(state.get("query", ""), evidence_text)

        if not check_and_consume_token_budget(state, estimated):
            state["draft_answer"] = ""
            state["llm_error"] = "token_budget_exceeded: request's cumulative model token budget was exhausted"
        else:
            try:
                result = synthesize_with_llm(state.get("query", ""), verified)
                state["draft_answer"] = result.text
                state["llm_provider"] = result.provider
                state["llm_model"] = result.model
                state["llm_error"] = None
            except LLMNotConfiguredError as exc:
                state["draft_answer"] = ""
                state["llm_error"] = f"not_configured: {exc}"
            except Exception as exc:  # noqa: BLE001 - any provider/timeout failure must surface, not crash the graph
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


def route_after_safety_critic(state: dict) -> str:
    if state.get("safety_critic_result", {}).get("passed"):
        return "citation_verifier"
    if state.get("synthesis_attempts", 0) < MAX_SYNTHESIS_ATTEMPTS:
        return "evidence_synthesizer"
    return "refuse"


def route_after_citation_verifier(state: dict) -> str:
    if state.get("citation_verifier_result", {}).get("passed"):
        return "citation_reviewer"
    if state.get("synthesis_attempts", 0) < MAX_SYNTHESIS_ATTEMPTS:
        return "evidence_synthesizer"
    return "refuse"


def route_after_citation_reviewer(state: dict) -> str:
    if state.get("citation_review_result", {}).get("passed", True):
        return "qa_agent"
    if state.get("synthesis_attempts", 0) < MAX_SYNTHESIS_ATTEMPTS:
        return "evidence_synthesizer"
    return "refuse"


def llm_unavailable_response(state: dict) -> dict:
    _record(state, "llm_unavailable")
    state["answer"] = (
        "This deployment does not have a working LLM provider configured for synthesis, so it cannot "
        "generate a grounded answer for this query. Set SYNTHESIS_PROVIDER/SYNTHESIS_MODEL and the "
        f"matching API key as environment variables and retry. Detail: {state.get('llm_error')}"
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
        elif state.get("citation_review_result") and not state["citation_review_result"].get("passed", True):
            stop_reason = "citation_reviewer_failed_after_retry"
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
    elif stop_reason == "citation_reviewer_failed_after_retry":
        message = (
            "This prototype detected a citation that did not semantically support the answer text near "
            "it, even after a repair attempt, so it is refusing rather than showing a mismatched citation."
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
    tool_ctx = MCPToolContext(package=package, retriever=retriever)

    graph = StateGraph(GraphV2State)

    graph.add_node("receive_query", make_receive_query)
    graph.add_node("planner", make_llm_planner_node(topic_vocabulary, tool_ctx))
    graph.add_node("query_classifier", make_llm_query_classifier_node(topic_vocabulary))
    graph.add_node("query_reformulator", make_llm_query_reformulator_node())
    graph.add_node("evidence_retriever", make_planned_evidence_retriever_node(retriever))
    graph.add_node("vector_retriever", make_vector_retriever_node(package))
    graph.add_node("fusion_reranker", make_fusion_reranker_node(package))
    graph.add_node("source_applicability_checker", make_source_applicability_checker_node(package))
    graph.add_node("evidence_analyst", make_llm_evidence_analyst_node())
    graph.add_node("conflict_detector", make_conflict_detector_node())
    graph.add_node("conflict_resolver", make_llm_conflict_resolver_node(package))
    graph.add_node("gap_detector", make_gap_detector_node(package))
    graph.add_node("check_safety_boundaries", make_check_safety_boundaries_node())
    graph.add_node("evidence_synthesizer", make_llm_evidence_synthesizer_node())
    graph.add_node("safety_critic", make_llm_safety_critic_node())
    graph.add_node("citation_verifier", make_citation_verifier_node(package))
    graph.add_node("citation_reviewer", make_llm_citation_reviewer_node())
    graph.add_node("qa_agent", make_llm_qa_evaluator_node(package))
    graph.add_node("attach_citations_final", attach_citations_final_v2)
    graph.add_node("fallback_if_unsupported", fallback_if_unsupported_v2)
    graph.add_node("refuse", refuse_v2)
    graph.add_node("llm_unavailable", llm_unavailable_response)

    graph.set_entry_point("receive_query")
    graph.add_edge("receive_query", "check_safety_boundaries")
    # The deterministic, hard, non-bypassable query-level safety gate runs
    # FIRST -- before the planner or any other LLM-powered node -- so a
    # diagnosis/flare/medication-change/individualized-diet request is
    # refused without ever spending a single model call on retrieval,
    # planning, evidence analysis, or conflict resolution. Reuses
    # subagents.route_after_query_safety unchanged; its "evidence_synthesizer"
    # return value is remapped here to "planner", the real next step once
    # the gate has passed.
    graph.add_conditional_edges(
        "check_safety_boundaries",
        route_after_query_safety,
        {"refuse": "refuse", "evidence_synthesizer": "planner"},
    )
    graph.add_edge("planner", "query_classifier")
    graph.add_edge("query_classifier", "query_reformulator")
    graph.add_edge("query_reformulator", "evidence_retriever")
    graph.add_edge("evidence_retriever", "vector_retriever")
    graph.add_edge("vector_retriever", "fusion_reranker")
    graph.add_edge("fusion_reranker", "source_applicability_checker")
    graph.add_edge("source_applicability_checker", "evidence_analyst")
    graph.add_edge("evidence_analyst", "conflict_detector")
    graph.add_edge("conflict_detector", "conflict_resolver")
    graph.add_edge("conflict_resolver", "gap_detector")
    # route_after_gap_detector (subagents.py, unchanged) returns
    # "check_safety_boundaries" for the "evidence can proceed" case, a
    # holdover key name from the original workflow; remapped here to
    # "evidence_synthesizer" directly since the safety gate already ran
    # above -- re-running it here would be redundant, not safer.
    graph.add_conditional_edges(
        "gap_detector",
        route_after_gap_detector,
        {"fallback_if_unsupported": "fallback_if_unsupported", "check_safety_boundaries": "evidence_synthesizer"},
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
        {"citation_reviewer": "citation_reviewer", "evidence_synthesizer": "evidence_synthesizer", "refuse": "refuse"},
    )
    graph.add_conditional_edges(
        "citation_reviewer",
        route_after_citation_reviewer,
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
