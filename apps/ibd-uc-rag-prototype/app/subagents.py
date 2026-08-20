"""Bounded LangGraph subagents (nodes), each with a narrow single
responsibility, that extend the original 8-node workflow in
``app/workflow.py``.

    1. Query Classifier            -> query_classifier_node
    2. Evidence Retriever          -> evidence_retriever_node (wraps retrieve_uc_claims)
    3. Source Applicability Checker-> source_applicability_checker_node (extends
                                       check_source_and_applicability with a
                                       source-level status check)
    4. Evidence Synthesizer        -> evidence_synthesizer_node
    5. Safety Critic               -> safety_critic_node (inspects the OUTPUT)
    6. Citation Verifier           -> citation_verifier_node
    7. Gap Detector                -> gap_detector_node (reuses
                                       mcp_server.tools.compute_evidence_gaps)
    8. QA Agent                    -> qa_agent_node (runs app/qa_checks.py)

``build_extended_workflow`` wires these into a new, separate compiled
graph (``app/workflow.py::build_workflow`` and its exact 8-node
behaviour are left untouched so the existing 35 tests keep passing).
The extended graph can retry the Evidence Synthesizer once when the
Safety Critic or Citation Verifier rejects a draft, and hard-stops to a
refusal if the retry also fails (never loops forever).
"""

from __future__ import annotations

import re
from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.evidence_loader import EvidencePackage
from app.qa_checks import run_all_qa_checks
from app.retrieval import RetrievedClaim, UCEvidenceRetriever
from app.safety_rules import (
    REFUSAL_MESSAGES,
    UNSUPPORTED_TOPIC_MESSAGE,
    SafetyBoundary,
    check_safety_boundaries,
    mentions_symptoms_or_inflammation,
)
from app.workflow import (
    check_source_and_applicability,
    fallback_if_unsupported,
    make_classify_topic_node,
    make_receive_query,
    make_retrieve_uc_claims_node,
)

MAX_SYNTHESIS_ATTEMPTS = 2  # 1 initial attempt + 1 retry, then hard-stop.


class ExtendedWorkflowState(TypedDict, total=False):
    # inputs
    query: str
    topic_filter: Optional[str]
    disease_filter: str

    # working state
    visited_nodes: list[str]
    trace: list[dict[str, Any]]
    classified_topic: Optional[str]
    query_intent: str
    known_unsupported: bool
    candidate_claims: list[RetrievedClaim]
    verified_claims: list[RetrievedClaim]
    gap_terms: list[str]
    safety_triggered: bool
    safety_message: str
    draft_answer: str
    draft_citations: list[dict[str, Any]]
    synthesis_attempts: int
    safety_critic_result: dict[str, Any]
    citation_verifier_result: dict[str, Any]
    stop_reason: Optional[str]
    qa_report: dict[str, Any]

    # outputs
    answer: str
    citations: list[dict[str, Any]]
    status: str  # "answered" | "unsupported" | "refused"
    show_symptom_caveat: bool

    # test-only hooks (never used in production; see evidence_synthesizer_node)
    _test_force_bad_draft_attempts: list[int]
    _test_inject_fake_citation: bool
    _test_inject_fake_citation_attempts: list[int]


def _record(state: dict, node_name: str) -> None:
    state.setdefault("visited_nodes", [])
    state["visited_nodes"].append(node_name)


def _trace(state: dict, node_name: str, output: Any) -> None:
    state.setdefault("trace", [])
    state["trace"].append({"node": node_name, "output": output})


# --- 1. Query Classifier -------------------------------------------------

_INTENT_BY_BOUNDARY = {
    SafetyBoundary.DIAGNOSIS_REQUEST: "diagnosis_seeking",
    SafetyBoundary.FLARE_PREDICTION: "flare_prediction_seeking",
    SafetyBoundary.MEDICATION_CHANGE: "medication_change_seeking",
    SafetyBoundary.INDIVIDUALIZED_DIET_PLAN: "diet_plan_seeking",
    SafetyBoundary.SYMPTOM_INFLAMMATION_EQUIVALENCE: "symptom_inflammation_question",
    SafetyBoundary.CROHNS_TO_UC_MISAPPLICATION: "crohns_misapplication",
    SafetyBoundary.NONE: "question",
}


def classify_intent(query: str) -> str:
    """Identify the query's intent (question vs. diagnosis-seeking vs.
    medication-change-seeking, etc.) by reusing the single source of
    truth for these patterns (``app.safety_rules.check_safety_boundaries``)
    rather than duplicating the regex patterns here.
    """
    result = check_safety_boundaries(query)
    return _INTENT_BY_BOUNDARY.get(result.boundary, "question")


def make_query_classifier_node(topic_vocabulary: list[str]):
    """Query Classifier subagent: identifies UC topic AND intent."""
    _classify_topic = make_classify_topic_node(topic_vocabulary)

    def query_classifier_node(state: dict) -> dict:
        state = _classify_topic(state)
        state["visited_nodes"].pop()  # remove the inner node's own record
        _record(state, "query_classifier")
        state["query_intent"] = classify_intent(state.get("query", ""))
        _trace(
            state,
            "query_classifier",
            {"classified_topic": state.get("classified_topic"), "query_intent": state["query_intent"]},
        )
        return state

    return query_classifier_node


# --- 2. Evidence Retriever -------------------------------------------------


def make_evidence_retriever_node(retriever: UCEvidenceRetriever):
    """Evidence Retriever subagent: retrieves only UC-applicable claims
    (thin, explicit wrapper around the existing retrieve_uc_claims node)."""
    _retrieve = make_retrieve_uc_claims_node(retriever)

    def evidence_retriever_node(state: dict) -> dict:
        state = _retrieve(state)
        state["visited_nodes"].pop()
        _record(state, "evidence_retriever")
        _trace(
            state,
            "evidence_retriever",
            {"candidate_claim_ids": [c.claim_id for c in state.get("candidate_claims", [])]},
        )
        return state

    return evidence_retriever_node


# --- 3. Source Applicability Checker -------------------------------------------------


def make_source_applicability_checker_node(package: EvidencePackage):
    """Extends check_source_and_applicability with a source-level status
    check (source exists, and -- if the data model ever adds it -- is not
    superseded). Defense in depth, same intent as the original node."""

    def source_applicability_checker_node(state: dict) -> dict:
        state = check_source_and_applicability(state)
        state["visited_nodes"].pop()
        _record(state, "source_applicability_checker")

        verified = []
        for claim in state.get("verified_claims", []):
            original = next((c for c in package.all_claims if c["claimId"] == claim.claim_id), None)
            if original is None:
                continue
            source = package.sources_by_id.get(original["sourceId"])
            if source is None:
                continue
            if source.get("supersededBy") or source.get("superseded_by") or source.get("status") == "superseded":
                continue
            verified.append(claim)
        state["verified_claims"] = verified
        _trace(
            state,
            "source_applicability_checker",
            {"verified_claim_ids": [c.claim_id for c in verified]},
        )
        return state

    return source_applicability_checker_node


# --- 4. Gap Detector -------------------------------------------------


def make_gap_detector_node(package: EvidencePackage):
    """Identifies when the topic has no UC-eligible claims (including
    ESR) and routes to the fallback message. Reuses
    ``mcp_server.tools.compute_evidence_gaps`` -- single source of truth
    with the MCP server's ``get_evidence_gaps`` tool."""
    from mcp_server.tools import compute_evidence_gaps

    gaps = compute_evidence_gaps(package)
    gap_terms = gaps["all_gap_terms"]

    def gap_detector_node(state: dict) -> dict:
        _record(state, "gap_detector")
        state["gap_terms"] = gap_terms
        query = (state.get("query") or "").lower()
        topic = state.get("classified_topic")
        topic_has_no_uc_claims = bool(topic) and topic not in {
            c.get("topic") for c in package.uc_eligible_claims
        }
        keyword_gap_hit = any(term in query for term in gaps["known_absent_categories"])
        no_candidates = not state.get("verified_claims")
        is_gap = state.get("known_unsupported", False) or topic_has_no_uc_claims or keyword_gap_hit or no_candidates
        state["is_evidence_gap"] = is_gap
        _trace(state, "gap_detector", {"is_evidence_gap": is_gap, "gap_terms_checked": len(gap_terms)})
        return state

    return gap_detector_node


def route_after_gap_detector(state: dict) -> str:
    if state.get("is_evidence_gap") or not state.get("verified_claims"):
        return "fallback_if_unsupported"
    return "check_safety_boundaries"


# --- query-level safety boundary (reused, wrapped for tracing) -------------------------------------------------


def make_check_safety_boundaries_node():
    def check_safety_boundaries_node(state: dict) -> dict:
        _record(state, "check_safety_boundaries")
        result = check_safety_boundaries(state.get("query", ""))
        state["safety_triggered"] = result.triggered
        state["safety_message"] = result.message
        _trace(state, "check_safety_boundaries", {"triggered": result.triggered, "boundary": result.boundary.value})
        return state

    return check_safety_boundaries_node


def route_after_query_safety(state: dict) -> str:
    if state.get("safety_triggered"):
        return "refuse"
    return "evidence_synthesizer"


# --- 5. Evidence Synthesizer -------------------------------------------------

_TEST_BAD_DRAFT_TEXT = "TEST-ONLY-INJECTED-BAD-DRAFT: you have ulcerative colitis and should stop taking your medication."


def _draft_from_claims(verified: list, strict: bool) -> str:
    """Template-based composition using ONLY plainLanguageExplanation
    (or, in strict retry mode, the more literal supportingExcerpt) --
    never claimText paraphrase invention beyond the source fields."""
    parts = []
    for i, claim in enumerate(verified, start=1):
        text = claim.supporting_excerpt if strict else (claim.claim_text or claim.supporting_excerpt)
        parts.append(f"[{i}] {text}")
    if not parts:
        return UNSUPPORTED_TOPIC_MESSAGE
    return "Based on the reviewed ulcerative colitis evidence set:\n\n" + "\n\n".join(parts)


def make_evidence_synthesizer_node():
    def evidence_synthesizer_node(state: dict) -> dict:
        _record(state, "evidence_synthesizer")
        attempts = state.get("synthesis_attempts", 0) + 1
        state["synthesis_attempts"] = attempts
        strict = attempts >= 2

        verified = state.get("verified_claims", [])

        # Test-only hook: allows tests to deterministically exercise the
        # retry/stop path without depending on the (safe, deterministic)
        # real evidence ever producing unsafe text. Never triggered in
        # production -- the key is absent from every real request.
        forced_bad_attempts = set(state.get("_test_force_bad_draft_attempts", []))
        if attempts in forced_bad_attempts:
            draft = _TEST_BAD_DRAFT_TEXT
        else:
            draft = _draft_from_claims(verified, strict=strict)

        state["draft_answer"] = draft
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
        fake_citation_attempts = set(state.get("_test_inject_fake_citation_attempts", [1]))
        if state.get("_test_inject_fake_citation") and attempts in fake_citation_attempts:
            citations.append(
                {
                    "number": len(citations) + 1,
                    "claimId": "CLM-999-FAKE",
                    "sourceTitle": "Fabricated Source",
                    "sourceUrl": "https://example.invalid/fabricated",
                    "claimText": "Fabricated claim text never present in the evidence package.",
                    "supportingExcerpt": "Fabricated excerpt.",
                    "exactLocator": "p.0",
                    "evidenceLevel": "unknown",
                    "confidence": "unknown",
                    "limitations": "n/a",
                    "applicabilityLimitations": "n/a",
                }
            )
        state["draft_citations"] = citations
        state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
        _trace(
            state,
            "evidence_synthesizer",
            {"attempt": attempts, "strict": strict, "draft_answer": draft, "citation_count": len(citations)},
        )
        return state

    return evidence_synthesizer_node


# --- 6. Safety Critic -------------------------------------------------

_CRITIC_DIAGNOSIS = [r"\byou have (uc|ulcerative colitis)\b", r"\byou are diagnosed\b"]
_CRITIC_FLARE = [r"\byou will flare\b", r"\byou('re| are) (going|about) to flare\b"]
_CRITIC_MEDICATION = [r"\bshould (start|stop|take|increase|decrease)\b.*(medication|dose|drug)\b", r"\bstop taking\b"]
_CRITIC_DIET = [r"\byour (personal|individualized|specific) diet plan\b", r"\byou must eat\b"]
_CRITIC_CAUSAL = ["causes", "cause of", "proven to cause", "results in", "leads to"]
_CRITIC_SYMPTOM_INFLAMMATION = [
    r"\bno symptoms means no inflammation\b",
    r"\bsymptoms prove (active )?inflammation\b",
    r"\bsymptoms confirm inflammation\b",
]


def _regex_any(text: str, patterns: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(re.search(p, lowered) for p in patterns)


def safety_critic_review(draft_answer: str) -> dict[str, Any]:
    """Reviews the DRAFTED ANSWER (not the query) for: diagnosis language,
    flare prediction, medication-change language, personalized diet
    prescription, causal overstatement, and symptom/inflammation
    confusion. Distinct, separately-testable from the pre-query
    ``app.safety_rules.check_safety_boundaries``."""
    failures = []
    if _regex_any(draft_answer, _CRITIC_DIAGNOSIS):
        failures.append("diagnosis_language")
    if _regex_any(draft_answer, _CRITIC_FLARE):
        failures.append("flare_prediction")
    if _regex_any(draft_answer, _CRITIC_MEDICATION):
        failures.append("medication_change_language")
    if _regex_any(draft_answer, _CRITIC_DIET):
        failures.append("individualized_diet_prescription")
    if any(w in (draft_answer or "").lower() for w in _CRITIC_CAUSAL):
        failures.append("causal_overstatement")
    if _regex_any(draft_answer, _CRITIC_SYMPTOM_INFLAMMATION):
        failures.append("symptom_inflammation_confusion")
    return {"passed": not failures, "failures": failures}


def make_safety_critic_node():
    def safety_critic_node(state: dict) -> dict:
        _record(state, "safety_critic")
        result = safety_critic_review(state.get("draft_answer", ""))
        state["safety_critic_result"] = result
        _trace(state, "safety_critic", result)
        return state

    return safety_critic_node


def route_after_safety_critic(state: dict) -> str:
    if state.get("safety_critic_result", {}).get("passed"):
        return "citation_verifier"
    if state.get("synthesis_attempts", 0) < MAX_SYNTHESIS_ATTEMPTS:
        return "evidence_synthesizer"
    return "refuse"


# --- 7. Citation Verifier -------------------------------------------------


def make_citation_verifier_node(package: EvidencePackage):
    claims_by_id = {c["claimId"]: c for c in package.all_claims}

    def citation_verifier_node(state: dict) -> dict:
        _record(state, "citation_verifier")
        mismatches = []
        for c in state.get("draft_citations", []):
            original = claims_by_id.get(c.get("claimId"))
            if original is None:
                mismatches.append({"claimId": c.get("claimId"), "reason": "unknown_claim_id"})
                continue
            if c.get("sourceUrl") != original.get("sourceUrl"):
                mismatches.append({"claimId": c.get("claimId"), "reason": "sourceUrl_mismatch"})
                continue
            if c.get("supportingExcerpt") != original.get("supportingExcerpt"):
                mismatches.append({"claimId": c.get("claimId"), "reason": "excerpt_mismatch"})
                continue
            if c.get("exactLocator") != original.get("exactLocator"):
                mismatches.append({"claimId": c.get("claimId"), "reason": "locator_mismatch"})
                continue
        result = {"passed": not mismatches, "mismatches": mismatches}
        state["citation_verifier_result"] = result
        _trace(state, "citation_verifier", result)
        return state

    return citation_verifier_node


def route_after_citation_verifier(state: dict) -> str:
    if state.get("citation_verifier_result", {}).get("passed"):
        return "qa_agent"
    if state.get("synthesis_attempts", 0) < MAX_SYNTHESIS_ATTEMPTS:
        return "evidence_synthesizer"
    return "refuse"


# --- 8. QA Agent -------------------------------------------------


def make_qa_agent_node(package: EvidencePackage):
    def qa_agent_node(state: dict) -> dict:
        _record(state, "qa_agent")
        answer = state.get("draft_answer", "")
        citations = state.get("draft_citations", [])
        report = run_all_qa_checks(package, answer, citations, state.get("gap_terms", []))
        state["qa_report"] = report
        _trace(state, "qa_agent", report)
        return state

    return qa_agent_node


def attach_citations_final(state: dict) -> dict:
    _record(state, "attach_citations_final")
    state["answer"] = state.get("draft_answer", "")
    state["citations"] = state.get("draft_citations", [])
    state["status"] = "answered" if state["citations"] else "unsupported"
    _trace(state, "attach_citations_final", {"status": state["status"], "citation_count": len(state["citations"])})
    return state


def refuse_extended(state: dict) -> dict:
    _record(state, "refuse")
    stop_reason = state.get("stop_reason")
    if stop_reason is None:
        # Determine the reason from the surviving state rather than relying
        # on a routing-function-side mutation (LangGraph does not guarantee
        # in-place mutations performed inside conditional-edge routing
        # functions are merged back into graph state).
        if state.get("safety_critic_result") and not state["safety_critic_result"].get("passed", True):
            stop_reason = "safety_critic_failed_after_retry"
        elif state.get("citation_verifier_result") and not state["citation_verifier_result"].get("passed", True):
            stop_reason = "citation_verifier_failed_after_retry"
    if stop_reason == "safety_critic_failed_after_retry":
        message = (
            "This prototype could not safely compose an answer to that request after a "
            "repair attempt, so it is refusing rather than returning unreviewed or unsafe "
            "text. Please rephrase, or consult your care team for anything diagnostic, "
            "medication-related, or individualized."
        )
    elif stop_reason == "citation_verifier_failed_after_retry":
        message = (
            "This prototype detected a citation that did not match the underlying reviewed "
            "evidence and could not repair it, so it is refusing rather than showing an "
            "unverifiable citation."
        )
    else:
        message = state.get("safety_message") or "This request cannot be fulfilled by this prototype."
    state["answer"] = message
    state["citations"] = []
    state["status"] = "refused"
    state["show_symptom_caveat"] = mentions_symptoms_or_inflammation(state.get("query", ""))
    _trace(state, "refuse", {"stop_reason": stop_reason, "message": message})
    return state


def fallback_if_unsupported_extended(state: dict) -> dict:
    state = fallback_if_unsupported(state)
    state["visited_nodes"].pop()
    _record(state, "fallback_if_unsupported")
    _trace(state, "fallback_if_unsupported", {"answer": state["answer"]})
    return state


# --- graph assembly -------------------------------------------------


def build_extended_workflow(package: EvidencePackage, retriever: UCEvidenceRetriever):
    """Build and compile the extended LangGraph StateGraph with the eight
    bounded subagents and the retry/repair loop. Separate from (and does
    not modify) ``app.workflow.build_workflow``."""
    topic_vocabulary = sorted({c["topic"] for c in package.uc_eligible_claims if c.get("topic")})

    graph = StateGraph(ExtendedWorkflowState)

    graph.add_node("receive_query", make_receive_query)
    graph.add_node("query_classifier", make_query_classifier_node(topic_vocabulary))
    graph.add_node("evidence_retriever", make_evidence_retriever_node(retriever))
    graph.add_node("source_applicability_checker", make_source_applicability_checker_node(package))
    graph.add_node("gap_detector", make_gap_detector_node(package))
    graph.add_node("check_safety_boundaries", make_check_safety_boundaries_node())
    graph.add_node("evidence_synthesizer", make_evidence_synthesizer_node())
    graph.add_node("safety_critic", make_safety_critic_node())
    graph.add_node("citation_verifier", make_citation_verifier_node(package))
    graph.add_node("qa_agent", make_qa_agent_node(package))
    graph.add_node("attach_citations_final", attach_citations_final)
    graph.add_node("fallback_if_unsupported", fallback_if_unsupported_extended)
    graph.add_node("refuse", refuse_extended)

    graph.set_entry_point("receive_query")
    graph.add_edge("receive_query", "query_classifier")
    graph.add_edge("query_classifier", "evidence_retriever")
    graph.add_edge("evidence_retriever", "source_applicability_checker")
    graph.add_edge("source_applicability_checker", "gap_detector")
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
        "safety_critic",
        route_after_safety_critic,
        {
            "citation_verifier": "citation_verifier",
            "evidence_synthesizer": "evidence_synthesizer",
            "refuse": "refuse",
        },
    )
    graph.add_edge("evidence_synthesizer", "safety_critic")
    graph.add_conditional_edges(
        "citation_verifier",
        route_after_citation_verifier,
        {"qa_agent": "qa_agent", "evidence_synthesizer": "evidence_synthesizer", "refuse": "refuse"},
    )
    graph.add_edge("qa_agent", "attach_citations_final")
    graph.add_edge("attach_citations_final", END)
    graph.add_edge("fallback_if_unsupported", END)
    graph.add_edge("refuse", END)

    return graph.compile()


def run_extended_query(
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
