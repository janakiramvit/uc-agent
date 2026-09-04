from __future__ import annotations

from uc_evidence_discovery.dedup import ProcessedIndex
from uc_evidence_discovery.screening import applicability_label, screen


def test_uc_only_stays_ulcerative_colitis():
    rec = {"title": "Ulcerative colitis maintenance of remission trial",
           "abstractText": "Patients with ulcerative colitis were followed for maintenance of remission."}
    assert applicability_label(rec) == "ulcerative_colitis"


def test_crohns_only_never_upgraded_to_uc():
    rec = {"title": "Crohn's disease fistulizing outcomes", "abstractText": "Crohn's disease patients with perianal fistula."}
    assert applicability_label(rec) == "crohns_only"

    idx = ProcessedIndex()
    d = screen(
        {**rec, "doi": "10.1/crohns", "journal": "Gut",
         "abstractText": rec["abstractText"] + " acute severe colectomy rescue therapy " * 5},
        index=idx, topic_id="T-UCX-03",
    )
    assert d.applicability == "crohns_only"
    assert d.status == "rejected"
    assert "crohns_only" in d.reason


def test_both_terms_present_stays_ibd_general_not_relabelled_uc():
    rec = {"title": "IBD cohort with UC and Crohn's disease",
           "abstractText": "This cohort included both ulcerative colitis and Crohn's disease patients."}
    assert applicability_label(rec) == "ibd_general"


def test_ibd_general_screen_result_keeps_label_and_flags_for_review():
    idx = ProcessedIndex()
    rec = {
        "title": "IBD treat to target consensus with ulcerative colitis and Crohn's disease",
        "doi": "10.1/ibdgen", "journal": "Gut",
        "abstractText": (
            "This IBD consensus covers ulcerative colitis and Crohn's disease treat to target "
            "recommendations, mucosal healing, and biologic step-up. " * 3
        ),
    }
    d = screen(rec, index=idx, topic_id="T-UCX-03", topic_keywords=("treat to target",))
    assert d.applicability == "ibd_general"
    if d.status == "accepted":
        assert d.requires_human_review is True
        assert "ibd_general_label_retained_not_upgraded_to_uc" in d.reason


def test_ambiguous_no_uc_or_crohns_terms_is_unknown_and_flagged():
    rec = {"title": "Unrelated cardiology", "abstractText": "z" * 50}
    assert applicability_label(rec) == "unknown"


def test_inflammatory_bowel_disease_without_uc_or_crohn_word_is_ibd_general():
    rec = {"title": "IBD biomarker panel", "abstractText": "Inflammatory bowel disease biomarker validation study."}
    assert applicability_label(rec) == "ibd_general"
