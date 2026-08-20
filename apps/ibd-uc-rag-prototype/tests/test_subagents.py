"""Tests for the extended LangGraph subagent workflow (app/subagents.py).

Covers: subagent routing/node order, Safety Critic rejection, Citation
Verifier rejection, QA-agent structured failure reporting, and the
retry-once-then-stop behavior.
"""

from __future__ import annotations

import pytest

from app.qa_checks import run_all_qa_checks
from app.subagents import (
    build_extended_workflow,
    classify_intent,
    route_after_citation_verifier,
    route_after_safety_critic,
    run_extended_query,
    safety_critic_review,
)


@pytest.fixture(scope="module")
def extended_graph(package, retriever):
    return build_extended_workflow(package, retriever)


# --- routing / node sequence ---------------------------------------------------------


def test_normal_query_visits_all_subagents_in_order(extended_graph):
    result = run_extended_query(extended_graph, "What does the evidence say about fibre in ulcerative colitis?")
    assert result["visited_nodes"] == [
        "receive_query",
        "query_classifier",
        "evidence_retriever",
        "source_applicability_checker",
        "gap_detector",
        "check_safety_boundaries",
        "evidence_synthesizer",
        "safety_critic",
        "citation_verifier",
        "qa_agent",
        "attach_citations_final",
    ]
    assert result["status"] == "answered"
    assert result["qa_report"]["overall_pass"] is True


def test_unsupported_topic_short_circuits_to_gap_detector_fallback(extended_graph):
    result = run_extended_query(extended_graph, "What does ESR tell me about my UC?")
    assert result["visited_nodes"] == [
        "receive_query",
        "query_classifier",
        "evidence_retriever",
        "source_applicability_checker",
        "gap_detector",
        "fallback_if_unsupported",
    ]
    assert result["status"] == "unsupported"
    assert "evidence_synthesizer" not in result["visited_nodes"]


def test_unsafe_query_short_circuits_to_refuse_before_synthesis(extended_graph):
    result = run_extended_query(extended_graph, "Do I have UC?")
    assert result["visited_nodes"] == [
        "receive_query",
        "query_classifier",
        "evidence_retriever",
        "source_applicability_checker",
        "gap_detector",
        "check_safety_boundaries",
        "refuse",
    ]
    assert result["status"] == "refused"
    assert "evidence_synthesizer" not in result["visited_nodes"]


# --- Query Classifier intent detection ---------------------------------------------------------


@pytest.mark.parametrize(
    "query,expected_intent",
    [
        ("Do I have UC?", "diagnosis_seeking"),
        ("Will I have a flare next week?", "flare_prediction_seeking"),
        ("Should I stop taking my medication?", "medication_change_seeking"),
        ("Give me a diet plan", "diet_plan_seeking"),
        ("Does my pain mean I am inflamed?", "symptom_inflammation_question"),
        ("What does the evidence say about fibre?", "question"),
    ],
)
def test_classify_intent(query, expected_intent):
    assert classify_intent(query) == expected_intent


# --- Safety Critic (inspects OUTPUT, not the query) ---------------------------------------------------------


def test_safety_critic_accepts_safe_draft():
    result = safety_critic_review("Based on the reviewed evidence, fibre intake was associated with symptom scores.")
    assert result["passed"] is True
    assert result["failures"] == []


@pytest.mark.parametrize(
    "bad_draft,expected_failure",
    [
        ("You have ulcerative colitis based on this evidence.", "diagnosis_language"),
        ("You will flare within the next two weeks.", "flare_prediction"),
        ("You should stop taking your medication now.", "medication_change_language"),
        ("Here is your personal diet plan for this week.", "individualized_diet_prescription"),
        ("This food causes ulcerative colitis flares.", "causal_overstatement"),
        ("Symptoms prove active inflammation is present.", "symptom_inflammation_confusion"),
    ],
)
def test_safety_critic_rejects_bad_draft(bad_draft, expected_failure):
    result = safety_critic_review(bad_draft)
    assert result["passed"] is False
    assert expected_failure in result["failures"]


def test_safety_critic_never_shown_to_user_via_full_graph(extended_graph):
    """Feed the graph a query whose real evidence is safe, but force the
    synthesizer to emit a hand-crafted bad draft (test-only hook) on every
    attempt, and assert the unsafe text is never returned as the answer."""
    state = {
        "query": "What does the evidence say about fibre in ulcerative colitis?",
        "topic_filter": None,
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
        "_test_force_bad_draft_attempts": [1, 2],
    }
    result = extended_graph.invoke(state)
    assert result["status"] == "refused"
    assert "you have ulcerative colitis" not in result["answer"].lower()
    assert "stop taking your medication" not in result["answer"].lower()


# --- Citation Verifier ---------------------------------------------------------


def test_citation_verifier_catches_fabricated_citation(extended_graph):
    state = {
        "query": "What does the evidence say about fibre in ulcerative colitis?",
        "topic_filter": None,
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
        "_test_inject_fake_citation": True,
        "_test_inject_fake_citation_attempts": [1, 2],  # fabricate on every attempt
    }
    result = extended_graph.invoke(state)
    assert result["status"] == "refused"
    assert result["citations"] == []
    # The final answer must never surface the fabricated claim.
    assert "CLM-999-FAKE" not in str(result["answer"])


# --- QA Agent structured failure reporting ---------------------------------------------------------


def test_qa_agent_flags_missing_excerpt(package):
    bad_citations = [
        {
            "claimId": "CLM-014",
            "sourceUrl": "https://example.com",
            "supportingExcerpt": "",  # injected failure: excerpt presence
            "exactLocator": "p.1",
            "limitations": "some limitation",
            "applicabilityLimitations": "some applicability limitation",
        }
    ]
    report = run_all_qa_checks(package, "Based on the reviewed ulcerative colitis evidence set:\n\n[1] ok", bad_citations, ["esr"])
    assert report["overall_pass"] is False
    assert report["checks"]["excerpt_presence"]["passed"] is False


def test_qa_agent_flags_missing_locator(package):
    bad_citations = [
        {
            "claimId": "CLM-014",
            "sourceUrl": "https://example.com",
            "supportingExcerpt": "some excerpt",
            "exactLocator": "",  # injected failure: locator presence
            "limitations": "some limitation",
            "applicabilityLimitations": "some applicability limitation",
        }
    ]
    report = run_all_qa_checks(package, "answer", bad_citations, ["esr"])
    assert report["checks"]["exact_locator_presence"]["passed"] is False
    assert report["overall_pass"] is False


def test_qa_agent_flags_diagnosis_in_answer(package):
    report = run_all_qa_checks(package, "You have ulcerative colitis based on this evidence.", [], ["esr"])
    assert report["checks"]["no_diagnosis_in_answer"]["passed"] is False
    assert report["overall_pass"] is False


def test_qa_agent_flags_medication_change_in_answer(package):
    report = run_all_qa_checks(package, "You should stop taking your medication immediately.", [], ["esr"])
    assert report["checks"]["no_medication_change_in_answer"]["passed"] is False


def test_qa_agent_flags_causation_upgrade(package):
    citations = [{"claimId": "CLM-014", "claimText": "Fibre intake was associated with improved symptom scores."}]
    report = run_all_qa_checks(package, "Fibre intake causes improved symptom scores.", citations, ["esr"])
    assert report["checks"]["no_causation_upgrade"]["passed"] is False


def test_qa_agent_flags_esr_missing_from_gaps(package):
    report = run_all_qa_checks(package, "answer", [], gap_terms=["crp"])  # esr missing on purpose
    assert report["checks"]["esr_remains_unsupported"]["passed"] is False


def test_qa_agent_passes_clean_report(package):
    report = run_all_qa_checks(package, "This topic is not currently covered by the reviewed UC evidence set.", [], ["esr", "crp"])
    assert report["overall_pass"] is True
    assert all(c["passed"] for c in report["checks"].values())


# --- retry / stop behavior ---------------------------------------------------------


def test_route_after_safety_critic_retries_once_then_stops():
    failing = {"safety_critic_result": {"passed": False}}
    assert route_after_safety_critic({**failing, "synthesis_attempts": 1}) == "evidence_synthesizer"
    assert route_after_safety_critic({**failing, "synthesis_attempts": 2}) == "refuse"

    passing = {"safety_critic_result": {"passed": True}, "synthesis_attempts": 1}
    assert route_after_safety_critic(passing) == "citation_verifier"


def test_route_after_citation_verifier_retries_once_then_stops():
    failing = {"citation_verifier_result": {"passed": False}}
    assert route_after_citation_verifier({**failing, "synthesis_attempts": 1}) == "evidence_synthesizer"
    assert route_after_citation_verifier({**failing, "synthesis_attempts": 2}) == "refuse"

    passing = {"citation_verifier_result": {"passed": True}, "synthesis_attempts": 1}
    assert route_after_citation_verifier(passing) == "qa_agent"


def test_retry_then_succeed_exercises_synthesizer_twice(extended_graph):
    state = {
        "query": "What does the evidence say about fibre in ulcerative colitis?",
        "topic_filter": None,
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
        "_test_force_bad_draft_attempts": [1],  # bad only on the first attempt
    }
    result = extended_graph.invoke(state)
    assert result["status"] == "answered"
    assert result["synthesis_attempts"] == 2
    assert result["visited_nodes"].count("evidence_synthesizer") == 2


def test_repeated_failure_stops_and_does_not_loop_forever(extended_graph):
    state = {
        "query": "What does the evidence say about fibre in ulcerative colitis?",
        "topic_filter": None,
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
        "synthesis_attempts": 0,
        "_test_force_bad_draft_attempts": [1, 2],  # bad on every attempt
    }
    result = extended_graph.invoke(state)
    assert result["status"] == "refused"
    assert result["synthesis_attempts"] == 2  # capped, not unbounded
    assert result["visited_nodes"].count("evidence_synthesizer") == 2


# --- no paid model calls in the extended graph either ---------------------------------------------------------


def test_no_model_call_in_extended_graph(extended_graph, monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("No model/network call should be made by the subagent graph")

    monkeypatch.setattr("requests.post", fail_if_called, raising=False)
    monkeypatch.setattr("requests.get", fail_if_called, raising=False)

    result = run_extended_query(extended_graph, "What does the evidence say about alcohol in ulcerative colitis?")
    assert result["status"] == "answered"
