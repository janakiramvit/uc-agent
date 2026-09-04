from __future__ import annotations

from uc_evidence_discovery.dedup import ProcessedIndex
from uc_evidence_discovery.screening import DISPOSITIONS, screen


def test_dispositions_are_mutually_exclusive_and_reasoned():
    idx = ProcessedIndex()
    records = [
        {"title": "Acute severe ulcerative colitis and Truelove Witts criteria", "doi": "10.1/a",
         "journal": "Gut", "abstractText": "x" * 130 + " acute severe ulcerative colitis truelove witts"},
        {"title": "Random unrelated cardiology study", "doi": "10.1/b", "journal": "Heart",
         "abstractText": "y" * 200},
        {"title": "Crohn's disease fistula outcomes", "doi": "10.1/c", "journal": "Gut",
         "abstractText": "acute severe crohn's disease colectomy " * 6},
        {"title": "No abstract guideline", "doi": "10.1/d", "journal": "Gut", "abstractText": ""},
    ]
    results = [screen(r, index=idx, topic_id="T-UCX-03") for r in records]
    for d in results:
        assert d.status in DISPOSITIONS
        assert d.reason

    assert results[0].status == "accepted"
    assert results[1].status == "rejected"
    assert results[2].status == "rejected" and "crohns_only" in results[2].reason
    assert results[3].status in ("deferred", "rejected")


def test_duplicate_takes_precedence_and_counts_separately_from_accepted():
    idx = ProcessedIndex(doi={"10.1/dup"})
    d = screen({"title": "Acute severe ulcerative colitis", "doi": "10.1/dup", "journal": "Gut",
               "abstractText": "acute severe ulcerative colitis truelove witts " * 5},
              index=idx, topic_id="T-UCX-03")
    assert d.status == "duplicate"
    assert d.reason.startswith("duplicate_doi")


def test_deferred_reason_present_and_distinct_from_rejected():
    idx = ProcessedIndex()
    d = screen({"title": "Acute severe ulcerative colitis", "doi": "10.1/e", "journal": "Gut",
               "abstractText": "too short"},
              index=idx, topic_id="T-UCX-03")
    assert d.status == "deferred"
    assert d.reason
