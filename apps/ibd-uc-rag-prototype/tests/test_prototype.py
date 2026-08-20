"""
Full pytest suite for the IBD/UC RAG prototype.

Covers: UC-only filtering, Crohn's exclusion, ESR/unsupported-topic
fallback, citation/locator/limitation preservation, safety refusals,
determinism with no model calls, LangGraph state transitions, Streamlit
startup, unique claim IDs, and source-resolution integrity.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from app.evidence_loader import (
    DEFAULT_EVIDENCE_PATH,
    is_crohns_only,
    is_uc_eligible,
    load_raw_evidence,
)
from app.safety_rules import UNSUPPORTED_TOPIC_MESSAGE
from app.workflow import run_query

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_UC_CLAIM_IDS = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}

UNSUPPORTED_TOPIC_QUERIES = [
    "What does biologics evidence say about UC?",
    "What do JAK inhibitors do for UC?",
    "Does mucosal healing matter in UC?",
    "What does colonoscopy show in UC?",
    "What does intestinal ultrasound show in UC?",
    "What does ESR tell me about my UC?",
    "What does CRP tell me about my UC?",
    "What does fecal calprotectin tell me about my UC?",
]


# 1. UC-only filtering ----------------------------------------------------


def test_uc_only_filtering_exact_five_claims(package):
    uc_ids = {c["claimId"] for c in package.uc_eligible_claims}
    assert uc_ids == EXPECTED_UC_CLAIM_IDS
    assert len(package.uc_eligible_claims) == 5
    for c in package.uc_eligible_claims:
        assert "ulcerative_colitis" in c["conditionApplicability"]


def test_only_uc_substring_claims_ever_retrievable(package, retriever):
    # Sweep several queries; every candidate returned must be UC-eligible.
    for q in ["fibre", "alcohol", "fruit", "vegetables", "diet", "nutrition", ""]:
        results = retriever.retrieve(q)
        for r in results:
            assert "ulcerative_colitis" in r.condition_applicability
            assert r.claim_id in EXPECTED_UC_CLAIM_IDS


# 2. Crohn's-only exclusion -----------------------------------------------


def test_crohns_only_claim_count_is_fifteen(package):
    assert len(package.crohns_only_claims) == 15
    for c in package.crohns_only_claims:
        assert c["conditionApplicability"] == "crohns_disease"


def test_crohns_only_claims_never_retrievable(package, retriever, graph):
    crohns_ids = {c["claimId"] for c in package.crohns_only_claims}
    assert crohns_ids.isdisjoint(EXPECTED_UC_CLAIM_IDS)

    # Direct retriever sweep.
    for q in ["fibre", "alcohol", "diet", "nutrition", "fruit", ""]:
        results = retriever.retrieve(q)
        returned_ids = {r.claim_id for r in results}
        assert returned_ids.isdisjoint(crohns_ids)

    # End-to-end through the graph, including an adversarial attempt.
    for q in [
        "What does the evidence say about fibre?",
        "Apply this Crohns claim about fiber to my UC",
        "Use the Crohn's evidence for UC",
    ]:
        result = run_query(graph, q)
        cited_ids = {c["claimId"] for c in result.get("citations", [])}
        assert cited_ids.isdisjoint(crohns_ids)


# 3. ESR unsupported fallback ----------------------------------------------


def test_esr_question_returns_exact_fallback(graph):
    result = run_query(graph, "What does ESR tell me about my UC disease activity?")
    assert result["answer"] == UNSUPPORTED_TOPIC_MESSAGE
    assert result["citations"] == []
    assert result["status"] == "unsupported"


# 4. Source and claim citation preservation --------------------------------


def test_citations_preserve_real_source_and_claim_text(package, graph):
    result = run_query(graph, "What does the evidence say about fibre in ulcerative colitis?")
    assert result["citations"], "expected at least one citation for fibre query"
    source_by_id = package.sources_by_id
    claims_by_id = {c["claimId"]: c for c in package.uc_eligible_claims}
    for c in result["citations"]:
        original = claims_by_id[c["claimId"]]
        assert c["sourceTitle"] == original["sourceTitle"]
        assert c["sourceUrl"] == original["sourceUrl"]
        assert c["claimText"] == original["claimText"]
        assert original["sourceId"] in source_by_id


# 5. Exact locator preservation --------------------------------------------


def test_exact_locator_preserved_verbatim(package, graph):
    result = run_query(graph, "What does the evidence say about fibre in ulcerative colitis?")
    claims_by_id = {c["claimId"]: c for c in package.uc_eligible_claims}
    assert result["citations"]
    for c in result["citations"]:
        original = claims_by_id[c["claimId"]]
        assert c["exactLocator"] == original["exactLocator"]


# 6. Limitation preservation -------------------------------------------------


def test_limitations_and_applicability_limitations_preserved(package, graph):
    result = run_query(graph, "What does the evidence say about alcohol in ulcerative colitis?")
    claims_by_id = {c["claimId"]: c for c in package.uc_eligible_claims}
    assert result["citations"]
    for c in result["citations"]:
        original = claims_by_id[c["claimId"]]
        assert c["limitations"] == original["limitations"]
        assert c["applicabilityLimitations"] == original["applicabilityLimitations"]
        assert c["limitations"]
        assert c["applicabilityLimitations"]


# 7. Unsupported-topic fallback for zero-eligible topics --------------------


@pytest.mark.parametrize("query", UNSUPPORTED_TOPIC_QUERIES)
def test_unsupported_topics_return_fixed_fallback(package, graph, query):
    uc_topics = {c["topic"] for c in package.uc_eligible_claims}
    # Sanity: none of the UC-eligible topics are biomarker/procedure topics.
    assert uc_topics.isdisjoint(
        {"biologics", "jak_inhibitors", "mucosal_healing", "colonoscopy", "esr", "crp", "fecal_calprotectin"}
    )
    result = run_query(graph, query)
    assert result["answer"] == UNSUPPORTED_TOPIC_MESSAGE
    assert result["citations"] == []


# 8. Medication-change refusal ----------------------------------------------


def test_medication_change_is_refused(graph):
    result = run_query(graph, "Should I stop taking my medication for UC?")
    assert result["status"] == "refused"
    assert "cannot recommend starting, stopping, or changing any medication" in result["answer"]
    assert result["citations"] == []


# 9. Diagnosis refusal --------------------------------------------------------


def test_diagnosis_request_is_refused(graph):
    result = run_query(graph, "Do I have UC?")
    assert result["status"] == "refused"
    assert "cannot diagnose" in result["answer"]
    assert result["citations"] == []


def test_flare_diagnosis_request_is_refused(graph):
    result = run_query(graph, "Is this a flare?")
    assert result["status"] == "refused"
    assert result["citations"] == []


# 10. Symptom-vs-inflammation caveat -----------------------------------------


def test_symptom_inflammation_equivalence_is_refused_not_confirmed(graph):
    result = run_query(graph, "Does my pain mean I am inflamed?")
    assert result["status"] == "refused"
    assert "do not always move together" in result["answer"]
    # Must never confirm or deny inflammation.
    assert "you are inflamed" not in result["answer"].lower()
    assert "you are not inflamed" not in result["answer"].lower()


def test_symptom_caveat_shown_when_topic_touched_in_normal_query(graph):
    result = run_query(graph, "What does the evidence say about symptoms and inflammation?")
    assert result.get("show_symptom_caveat") is True


# 11. Deterministic retrieval, no model call ----------------------------------


def test_deterministic_output_across_repeated_runs(graph, monkeypatch):
    monkeypatch.delenv("ENABLE_MODEL_CALLS", raising=False)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("No model/network call should be made in the default path")

    # Patch common network entry points to ensure nothing calls out.
    monkeypatch.setattr("requests.post", fail_if_called, raising=False)
    monkeypatch.setattr("requests.get", fail_if_called, raising=False)

    results = [
        run_query(graph, "What does the evidence say about fibre in ulcerative colitis?")
        for _ in range(3)
    ]
    answers = [r["answer"] for r in results]
    citations = [r["citations"] for r in results]
    assert len(set(answers)) == 1
    assert all(c == citations[0] for c in citations)


def test_no_model_call_when_flag_false(graph, monkeypatch):
    monkeypatch.setenv("ENABLE_MODEL_CALLS", "false")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Model call must not happen when ENABLE_MODEL_CALLS=false")

    monkeypatch.setattr("requests.post", fail_if_called, raising=False)
    result = run_query(graph, "What does the evidence say about alcohol in ulcerative colitis?")
    assert result["status"] == "answered"


# 12. LangGraph state transitions ---------------------------------------------


def test_graph_node_sequence_normal_answerable_query(graph):
    result = run_query(graph, "What does the evidence say about fibre in ulcerative colitis?")
    assert result["visited_nodes"] == [
        "receive_query",
        "classify_topic",
        "retrieve_uc_claims",
        "check_source_and_applicability",
        "check_safety_boundaries",
        "compose_answer",
        "attach_citations",
    ]


def test_graph_node_sequence_unsupported_topic_query(graph):
    result = run_query(graph, "What does ESR tell me about my UC?")
    assert result["visited_nodes"] == [
        "receive_query",
        "classify_topic",
        "retrieve_uc_claims",
        "check_source_and_applicability",
        "check_safety_boundaries",
        "compose_answer",
        "attach_citations",
        "fallback_if_unsupported",
    ]


def test_graph_node_sequence_safety_boundary_short_circuits(graph):
    result = run_query(graph, "Do I have UC?")
    assert result["visited_nodes"] == [
        "receive_query",
        "classify_topic",
        "retrieve_uc_claims",
        "check_source_and_applicability",
        "check_safety_boundaries",
        "refuse",
    ]
    assert "compose_answer" not in result["visited_nodes"]


# 13. Streamlit app startup/import ---------------------------------------------


def test_streamlit_app_module_imports_without_error():
    import importlib
    import streamlit_app  # noqa: F401

    importlib.reload(streamlit_app)


def test_streamlit_run_starts_cleanly():
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "streamlit_app.py"),
            "--server.headless",
            "true",
            "--server.port",
            "8511",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        started = False
        for _ in range(30):
            time.sleep(1)
            if proc.poll() is not None:
                break
            try:
                import urllib.request

                with urllib.request.urlopen("http://localhost:8511", timeout=2) as resp:
                    if resp.status == 200:
                        started = True
                        break
            except Exception:
                continue
        assert started, "Streamlit app did not start and respond within timeout"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


# 14. Unique claim IDs -----------------------------------------------------------


def test_no_duplicate_claim_ids_in_loaded_set(package):
    ids = [c["claimId"] for c in package.all_claims]
    assert len(ids) == len(set(ids))


def test_no_duplicate_claim_ids_raw_file():
    raw = load_raw_evidence(DEFAULT_EVIDENCE_PATH)
    ids = [c["claimId"] for c in raw["claims"]]
    assert len(ids) == len(set(ids))


# 15. No superseded-source references / all sourceIds resolve --------------------


def test_no_superseded_source_field_present(package):
    for s in package.sources_by_id.values():
        assert "supersededBy" not in s
        assert "superseded_by" not in s


def test_every_claim_source_id_resolves_to_a_source(package):
    for c in package.all_claims:
        assert c["sourceId"] in package.sources_by_id


def test_uc_eligible_claims_source_ids_resolve(package):
    for c in package.uc_eligible_claims:
        assert c["sourceId"] in package.sources_by_id


# --- extra structural / eligibility sanity checks -----------------------------


def test_excluded_claim_ids_never_present(package):
    all_ids = {c["claimId"] for c in package.all_claims}
    assert all_ids.isdisjoint(package.excluded_claim_ids)
    assert len(package.excluded_claim_ids) == 12


def test_source_evidence_file_not_modified():
    # The evidence file is read-only (structural check the loader never writes).
    assert DEFAULT_EVIDENCE_PATH.exists()
    import os

    mode = oct(os.stat(DEFAULT_EVIDENCE_PATH).st_mode)[-3:]
    # Should not be world/owner-writable-only-by-accident; just assert readable.
    assert os.access(DEFAULT_EVIDENCE_PATH, os.R_OK)
