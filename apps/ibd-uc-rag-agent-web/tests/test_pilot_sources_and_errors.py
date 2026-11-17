"""Pilot release: source counts by kind (never a single 'papers' number), per-answer unique sources, dataset switch, and no
database details in browser-visible errors."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from agent_core import supabase_evidence_source as sup
from agent_core.evidence_loader import EvidencePackage, load_evidence_package, source_kind


def _pkg(sources, claims):
    return EvidencePackage(version="v", created_at="", intended_use="", sources_by_id={s["sourceId"]: s for s in sources},
                           all_claims=claims, excluded_claim_ids=set(), uc_eligible_claims=[c for c in claims if "ulcerative_colitis" in c["conditionApplicability"]],
                           crohns_only_claims=[], limitations=[])


S = [{"sourceId": "S1", "sourceType": "guideline"}, {"sourceId": "S2", "sourceType": "randomized controlled trial"},
     {"sourceId": "S3", "sourceType": "official patient information"}, {"sourceId": "S4", "sourceType": "clinical trial registry record"},
     {"sourceId": "S5", "sourceType": "guideline"}]
C = [{"claimId": "A", "sourceId": "S1", "conditionApplicability": "ulcerative_colitis"},
     {"claimId": "B", "sourceId": "S1", "conditionApplicability": "ulcerative_colitis"},
     {"claimId": "C", "sourceId": "S2", "conditionApplicability": "ulcerative_colitis"},
     {"claimId": "D", "sourceId": "S3", "conditionApplicability": "ulcerative_colitis; ibd_general"},
     {"claimId": "E", "sourceId": "S5", "conditionApplicability": "crohns_disease"}]


@pytest.mark.parametrize("t,k", [("guideline", "guideline"), ("consensus statement", "guideline"), ("randomized controlled trial", "study"),
                                 ("systematic review", "study"), ("official patient information", "patient_information"),
                                 ("clinical trial registry record", "trial_record"), ("ongoing clinical trial (registry record)", "trial_record")])
def test_source_kind(t, k):
    assert source_kind({"sourceType": t}) == k


def test_reviewed_sources_count_only_sources_that_can_actually_be_cited_and_split_by_kind():
    p = _pkg(S, C)
    c = p.source_counts()
    assert c == {"total": 3, "studies": 1, "guidelines": 1, "trialRecords": 0, "patientInformation": 1}   # S4/S5 support no UC claim


def test_answer_counts_each_source_once_even_when_several_claims_come_from_it():
    p = _pkg(S, C)
    ids = p.sources_for_claims(["A", "B", "C"])
    assert ids == {"S1", "S2"} and p.source_counts(ids)["total"] == 2


def test_provenance_exposes_dataset_and_reviewed_sources_but_no_connection_details():
    prov = _pkg(S, C).provenance()
    assert prov["dataset"] == "prototype-v1" and prov["reviewedSources"]["total"] == 3
    blob = str(prov).lower()
    assert "postgres" not in blob and "supabase" not in blob.replace("backend", "") and "password" not in blob


def test_json_package_reviewed_sources_are_split_and_total_matches_citable_sources():
    p = load_evidence_package()
    c = p.source_counts()
    assert c["total"] == len(p.citable_sources()) == c["studies"] + c["guidelines"] + c["trialRecords"] + c["patientInformation"]


def test_dataset_switch_defaults_to_prototype_and_rejects_unknown(monkeypatch):
    monkeypatch.delenv("EVIDENCE_DATASET", raising=False)
    assert sup.active_dataset() == "prototype-v1"
    monkeypatch.setenv("EVIDENCE_DATASET", "pilot")
    assert sup.active_dataset() == "pilot"
    monkeypatch.setenv("EVIDENCE_DATASET", "evil; drop table")
    with pytest.raises(ValueError):
        sup.active_dataset()


def test_loader_reads_the_views_of_the_selected_dataset(monkeypatch):
    seen = []

    class Conn:
        def execute(self, sql, params=()):
            seen.append(sql)
            class R:
                def fetchall(s): return []
                def fetchone(s): return ("prototype-v1", {})
            return R()

        def close(self): pass

    monkeypatch.setenv("EVIDENCE_DATASET", "pilot")
    sup.load_evidence_package_from_db(Conn())
    assert any("v_pilot_claim" in q for q in seen) and not any("v_prototype_claim" in q for q in seen)


def test_internal_errors_never_leak_database_details_to_the_browser(monkeypatch, capsys):
    import chat
    sent = {}

    class H(chat.handler):
        def __init__(self): pass
        def _send_json(self, status, obj): sent["s"], sent["o"] = status, obj

    def boom():
        raise RuntimeError('connection to server at "15.1.2.3", port 5432 failed: FATAL: tenant/user evidence_app.abcdefgh not found')

    monkeypatch.setattr(chat, "_pipeline", boom)
    h = H()
    body = b'{"query": "diet in UC?"}'
    h.headers = {"Content-Length": str(len(body))}
    import io
    h.rfile = io.BytesIO(body)
    h.client_address = ("1.2.3.4", 1)
    h.do_POST()
    blob = str(sent["o"])
    assert sent["s"] == 500 and "15.1.2.3" not in blob and "evidence_app" not in blob and "trace" not in sent["o"]
    assert "evidence_app" in capsys.readouterr().err        # logged server-side only


# ------------------------------------------------------------------ pilot: coverage gate and no-coverage answers
from agent_core.safety_rules import answer_declares_no_coverage, is_known_unsupported_topic


@pytest.mark.parametrize("q", ["What do fecal calprotectin results mean in UC?", "Does CRP matter in ulcerative colitis?",
                               "Should I have a colonoscopy or an endoscopy?"])
def test_biomarker_and_endoscopy_questions_are_no_longer_short_circuited_as_unsupported(q):
    assert not is_known_unsupported_topic(q)


@pytest.mark.parametrize("q", ["What does ESR tell me?", "Does vedolizumab work?", "What about intestinal ultrasound?", "Does mucosal healing matter?"])
def test_genuinely_uncovered_topics_stay_unsupported(q):
    assert is_known_unsupported_topic(q)


@pytest.mark.parametrize("answer", [
    "Based on the provided evidence entries, there is **no information available** about how fatigue should be evaluated.\n\nThe entries discuss biomarkers.",
    "Based on the verified evidence provided, the entries do not directly describe which symptom changes commonly make people suspect a UC flare.",
    "I cannot answer this question from the evidence provided.",
])
def test_an_answer_that_says_the_evidence_does_not_cover_the_question_is_detected(answer):
    assert answer_declares_no_coverage(answer)


@pytest.mark.parametrize("answer", [
    "AGA suggests that a biomarker test may help monitoring [1]. Your clinician decides which tests are right for you.\n\nThe guideline does not specify how often to test.",
    "The AGA guideline concludes that non-invasive tests can inform monitoring [1].",
])
def test_a_real_answer_with_a_later_caveat_is_not_treated_as_a_coverage_gap(answer):
    assert not answer_declares_no_coverage(answer)


def test_no_coverage_answer_becomes_unsupported_with_no_citations():
    import chat
    out = chat.handler._to_response({"status": "answered", "answer": "There is no information in the evidence about fatigue.",
                                     "citations": [{"claimId": "CLM-115"}, {"claimId": "CLM-116"}]})
    assert out["status"] == "unsupported" and out["citations"] == []
    assert "not currently covered" in out["answer"]
