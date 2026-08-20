from agent_core.conflict_detector import detect_conflicts, make_conflict_detector_node
from agent_core.retrieval import RetrievedClaim


def _claim(claim_id, topic, confidence, evidence_level):
    return RetrievedClaim(
        claim_id=claim_id,
        source_title="t",
        source_url="u",
        claim_text="c",
        supporting_excerpt="e",
        exact_locator="l",
        evidence_level=evidence_level,
        confidence=confidence,
        limitations="",
        applicability_limitations="",
        topic=topic,
        outcome_type="o",
        condition_applicability="ulcerative_colitis",
        disease_context="d",
    )


def test_no_conflict_for_single_claim_topic():
    report = detect_conflicts([_claim("CLM-1", "fibre", "moderate", "guideline")])
    assert report.has_conflicts is False


def test_conflict_when_confidence_differs_within_topic():
    claims = [
        _claim("CLM-1", "fibre", "moderate", "guideline"),
        _claim("CLM-2", "fibre", "high", "guideline"),
    ]
    report = detect_conflicts(claims)
    assert report.has_conflicts is True
    assert report.conflicts[0]["topic"] == "fibre"
    assert set(report.conflicts[0]["claimIds"]) == {"CLM-1", "CLM-2"}


def test_no_conflict_when_same_topic_same_ratings():
    claims = [
        _claim("CLM-1", "alcohol", "moderate", "guideline"),
        _claim("CLM-2", "alcohol", "moderate", "guideline"),
    ]
    report = detect_conflicts(claims)
    assert report.has_conflicts is False


def test_real_fibre_claims_flagged_as_conflicting(retriever):
    """CLM-014 (moderate/systematic review) and CLM-094 (high/official
    patient information) are real, differently-rated evidence entries on
    the same fibre topic -- the detector should surface that, not hide it."""
    results = retriever.retrieve(query="fibre", topic_filter="fibre")
    report = detect_conflicts(results)
    assert report.has_conflicts is True


def test_conflict_detector_node_records_trace():
    node = make_conflict_detector_node()
    claims = [
        _claim("CLM-1", "fibre", "moderate", "guideline"),
        _claim("CLM-2", "fibre", "high", "guideline"),
    ]
    state = {"verified_claims": claims, "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["conflict_report"]["has_conflicts"] is True
    assert "conflict_detector" in result["visited_nodes"]
