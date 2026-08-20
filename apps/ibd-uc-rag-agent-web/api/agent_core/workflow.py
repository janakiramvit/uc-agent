"""
LangGraph workflow for the UC RAG prototype.

Implements the 8-state query workflow as an explicit LangGraph
``StateGraph``:

  1. receive_query
  2. classify_topic
  3. retrieve_uc_claims
  4. check_source_and_applicability
  5. check_safety_boundaries
  6. compose_answer
  7. attach_citations
  8. fallback_if_unsupported

Retrieval and answer composition are fully deterministic and require no
model/API call by default. An optional LLM call is gated behind the
``ENABLE_MODEL_CALLS`` environment variable (default false / off) and is
never invoked by the deterministic path used in this prototype.
"""

from __future__ import annotations

import os
from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agent_core.evidence_loader import EvidencePackage, is_crohns_only, is_uc_eligible
from agent_core.retrieval import RetrievedClaim, UCEvidenceRetriever
from agent_core.safety_rules import (
    UNSUPPORTED_TOPIC_MESSAGE,
    SYMPTOM_INFLAMMATION_CAVEAT,
    check_safety_boundaries,
    is_known_unsupported_topic,
    mentions_symptoms_or_inflammation,
)


class WorkflowState(TypedDict, total=False):
    # inputs
    query: str
    topic_filter: Optional[str]
    disease_filter: str

    # working state
    visited_nodes: list[str]
    classified_topic: Optional[str]
    known_unsupported: bool
    candidate_claims: list[RetrievedClaim]
    verified_claims: list[RetrievedClaim]
    safety_triggered: bool
    safety_message: str

    # outputs
    answer: str
    citations: list[dict[str, Any]]
    status: str  # "answered" | "unsupported" | "refused"
    show_symptom_caveat: bool


def _record(state: WorkflowState, node_name: str) -> None:
    state.setdefault("visited_nodes", [])
    state["visited_nodes"].append(node_name)


def make_receive_query(state: WorkflowState) -> WorkflowState:
    _record(state, "receive_query")
    state["query"] = (state.get("query") or "").strip()
    state.setdefault("topic_filter", None)
    state.setdefault("disease_filter", "ulcerative_colitis")
    return state


def make_classify_topic_node(topic_vocabulary: list[str]):
    def classify_topic(state: WorkflowState) -> WorkflowState:
        _record(state, "classify_topic")
        query = state.get("query", "")
        explicit = state.get("topic_filter")

        classified = explicit
        if not classified:
            lower = query.lower()
            for topic in topic_vocabulary:
                keyword = topic.replace("_", " ")
                if keyword and keyword in lower:
                    classified = topic
                    break
        state["classified_topic"] = classified
        state["known_unsupported"] = is_known_unsupported_topic(query)
        return state

    return classify_topic


def make_retrieve_uc_claims_node(retriever: UCEvidenceRetriever):
    def retrieve_uc_claims(state: WorkflowState) -> WorkflowState:
        _record(state, "retrieve_uc_claims")
        if state.get("known_unsupported"):
            state["candidate_claims"] = []
            return state
        results = retriever.retrieve(
            query=state.get("query", ""),
            topic_filter=state.get("classified_topic"),
            disease_filter=state.get("disease_filter", "ulcerative_colitis"),
        )
        state["candidate_claims"] = results
        return state

    return retrieve_uc_claims


def check_source_and_applicability(state: WorkflowState) -> WorkflowState:
    """Defense-in-depth re-verification: independently re-checks that each
    candidate is UC-eligible, not Crohn's-only, and not in the excluded set
    -- even though retrieve_uc_claims already filtered. A bug in the
    retriever layer must not silently leak non-UC evidence.
    """
    _record(state, "check_source_and_applicability")
    verified = []
    for claim in state.get("candidate_claims", []):
        metadata = {
            "conditionApplicability": claim.condition_applicability,
            "claimId": claim.claim_id,
        }
        if not is_uc_eligible(metadata):
            continue
        if is_crohns_only(metadata):
            continue
        verified.append(claim)
    state["verified_claims"] = verified
    return state


def check_safety_boundaries_node(state: WorkflowState) -> WorkflowState:
    _record(state, "check_safety_boundaries")
    result = check_safety_boundaries(state.get("query", ""))
    state["safety_triggered"] = result.triggered
    state["safety_message"] = result.message
    return state


def compose_answer(state: WorkflowState) -> WorkflowState:
    """Deterministic, template-based composition from surviving claims'
    plainLanguageExplanation fields. No LLM call by default. Never
    fabricates content beyond what is present in the claim fields.

    Optional model-assisted composition can be enabled by setting
    ENABLE_MODEL_CALLS=true and MODEL_PROVIDER in the environment; that
    path is not exercised here and requires an explicit opt-in.
    """
    _record(state, "compose_answer")
    verified = state.get("verified_claims", [])

    if os.getenv("ENABLE_MODEL_CALLS", "false").lower() == "true":
        # Optional path -- intentionally not implemented in this local
        # prototype build. Left as an explicit, clearly-gated no-op so
        # that no paid/model call is ever made without deliberate,
        # separate implementation work and explicit opt-in.
        pass

    explanations = []
    for i, claim in enumerate(verified, start=1):
        explanations.append(f"[{i}] {claim.claim_text}")

    if explanations:
        answer = (
            "Based on the reviewed ulcerative colitis evidence set:\n\n"
            + "\n\n".join(explanations)
        )
    else:
        answer = UNSUPPORTED_TOPIC_MESSAGE

    state["answer"] = answer
    state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
    return state


def attach_citations(state: WorkflowState) -> WorkflowState:
    _record(state, "attach_citations")
    citations = []
    for i, claim in enumerate(state.get("verified_claims", []), start=1):
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
    state["citations"] = citations
    state["status"] = "answered" if citations else "unsupported"
    return state


def fallback_if_unsupported(state: WorkflowState) -> WorkflowState:
    _record(state, "fallback_if_unsupported")
    state["answer"] = UNSUPPORTED_TOPIC_MESSAGE
    state["citations"] = []
    state["status"] = "unsupported"
    state["show_symptom_caveat"] = False
    return state


def refuse(state: WorkflowState) -> WorkflowState:
    _record(state, "refuse")
    state["answer"] = state.get("safety_message") or "This request cannot be fulfilled by this prototype."
    state["citations"] = []
    state["status"] = "refused"
    state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
    return state


# --- routing functions -------------------------------------------------


def route_after_safety(state: WorkflowState) -> str:
    if state.get("safety_triggered"):
        return "refuse"
    return "compose_answer"


def route_after_citations(state: WorkflowState) -> str:
    if state.get("status") == "unsupported" or not state.get("verified_claims"):
        return "fallback_if_unsupported"
    return END


def build_workflow(package: EvidencePackage, retriever: UCEvidenceRetriever):
    """Build and compile the LangGraph StateGraph for the UC query workflow."""
    topic_vocabulary = sorted({c["topic"] for c in package.uc_eligible_claims if c.get("topic")})
    # Also include the full known vocabulary across all claims so
    # classify_topic can recognize e.g. "biologics" style topics that have
    # zero UC-eligible claims (handled via known_unsupported keywords too).

    graph = StateGraph(WorkflowState)

    graph.add_node("receive_query", make_receive_query)
    graph.add_node("classify_topic", make_classify_topic_node(topic_vocabulary))
    graph.add_node("retrieve_uc_claims", make_retrieve_uc_claims_node(retriever))
    graph.add_node("check_source_and_applicability", check_source_and_applicability)
    graph.add_node("check_safety_boundaries", check_safety_boundaries_node)
    graph.add_node("compose_answer", compose_answer)
    graph.add_node("attach_citations", attach_citations)
    graph.add_node("fallback_if_unsupported", fallback_if_unsupported)
    graph.add_node("refuse", refuse)

    graph.set_entry_point("receive_query")
    graph.add_edge("receive_query", "classify_topic")
    graph.add_edge("classify_topic", "retrieve_uc_claims")
    graph.add_edge("retrieve_uc_claims", "check_source_and_applicability")
    graph.add_edge("check_source_and_applicability", "check_safety_boundaries")
    graph.add_conditional_edges(
        "check_safety_boundaries",
        route_after_safety,
        {"refuse": "refuse", "compose_answer": "compose_answer"},
    )
    graph.add_edge("compose_answer", "attach_citations")
    graph.add_conditional_edges(
        "attach_citations",
        route_after_citations,
        {"fallback_if_unsupported": "fallback_if_unsupported", END: END},
    )
    graph.add_edge("fallback_if_unsupported", END)
    graph.add_edge("refuse", END)

    return graph.compile()


def run_query(
    compiled_graph,
    query: str,
    topic_filter: str | None = None,
    disease_filter: str = "ulcerative_colitis",
) -> WorkflowState:
    initial_state: WorkflowState = {
        "query": query,
        "topic_filter": topic_filter,
        "disease_filter": disease_filter,
        "visited_nodes": [],
    }
    result = compiled_graph.invoke(initial_state)
    return result
