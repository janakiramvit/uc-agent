from __future__ import annotations

from uc_evidence_discovery.extract import extract_candidates, verify_verbatim


def _allocator():
    n = {"i": 0}

    def alloc():
        n["i"] += 1
        return f"CLM-{n['i']:03d}"
    return alloc


def test_excerpts_are_verbatim_substrings_with_locator_and_blank_review_fields():
    rec = {
        "title": "Acute severe ulcerative colitis rescue therapy",
        "raw_ext_id": "12345", "journal": "Gut", "pubYear": "2024",
        "abstractText": (
            "This guideline addresses acute severe ulcerative colitis and Truelove Witts "
            "criteria for hospitalisation. Intravenous corticosteroids are first-line therapy "
            "in acute severe ulcerative colitis. Ciclosporin rescue therapy or colectomy is "
            "considered for steroid non-response."
        ),
    }
    claims = extract_candidates(
        rec, source_id="SRC-999", applicability="ulcerative_colitis", topic_id="T-UCX-03",
        mapped_question_ids=["L3-1.1.2"], allocate_claim_id=_allocator(), remaining_global=20,
        topic_keywords=("acute severe", "truelove", "witts", "colectomy"),
    )
    assert claims
    for c in claims:
        assert c["exactSupportingExcerpt"] in rec["abstractText"]
        assert c["normalizedClaim"] == c["exactSupportingExcerpt"]
        assert verify_verbatim(c, rec["abstractText"]) is None
        assert c["exactLocator"]
        assert c["verificationBasis"] == "abstract_only"
        assert c["conditionApplicability"] == "ulcerative_colitis"
        assert c["reviewStatus"] == "pending_clinical_review"
        assert c["isMechanicallyExtractedCandidate"] is True
        assert c["humanReviewStatus"] == "" and c["clinicalReviewStatus"] == "" and c["reviewerDecision"] == ""
        assert c["mappedPatientQuestionIds"] == ["L3-1.1.2"]


def test_excerpt_never_upgraded_beyond_source_applicability():
    rec = {
        "title": "IBD consensus", "raw_ext_id": "1", "journal": "Gut", "pubYear": "2021",
        "abstractText": "This IBD consensus on treat to target applies to ulcerative colitis and Crohn's disease. "
                        "Treat to target strategies include mucosal healing as a goal.",
    }
    claims = extract_candidates(
        rec, source_id="SRC-1", applicability="ibd_general", topic_id="T-UCX-02",
        mapped_question_ids=[], allocate_claim_id=_allocator(), remaining_global=20,
        topic_keywords=("treat to target",),
    )
    assert claims
    assert all(c["conditionApplicability"] == "ibd_general" for c in claims)


def test_respects_remaining_global_cap():
    rec = {
        "title": "t", "raw_ext_id": "1", "journal": "Gut", "pubYear": "2021",
        "abstractText": (
            "Acute severe ulcerative colitis first statement about truelove witts criteria here. "
            "Acute severe ulcerative colitis second statement about colectomy thresholds here too. "
            "Acute severe ulcerative colitis third statement about ciclosporin rescue therapy here. "
            "Acute severe ulcerative colitis fourth statement about hospitalisation pathways here."
        ),
    }
    claims = extract_candidates(
        rec, source_id="SRC-1", applicability="ulcerative_colitis", topic_id="T-UCX-03",
        mapped_question_ids=[], allocate_claim_id=_allocator(), remaining_global=2,
        topic_keywords=("acute severe", "truelove", "colectomy", "ciclosporin", "hospitalis"),
    )
    assert len(claims) <= 2


def test_no_abstract_yields_no_candidates():
    claims = extract_candidates(
        {"title": "x", "abstractText": ""}, source_id="SRC-1", applicability="unknown",
        topic_id="T-UCX-03", mapped_question_ids=[], allocate_claim_id=_allocator(), remaining_global=20,
    )
    assert claims == []


def test_verify_verbatim_rejects_paraphrase():
    claim = {"exactSupportingExcerpt": "this sentence was not in the source"}
    assert verify_verbatim(claim, "a totally different abstract body") is not None
