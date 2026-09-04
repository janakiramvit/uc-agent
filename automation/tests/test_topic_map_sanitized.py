"""The sanitizer is allowlist-by-construction: it reads a fixed set of input fields and drops
everything else *without inspecting it*. It must still emit a clean derivative from a raw node
that carries Reddit URLs / handles / narrative text in the fields it does not read, and it must
abort only when a *permitted output* value is itself polluted or violates the strict schema.
"""

from __future__ import annotations

import json

import pytest

from tools import build_topic_priority_map as sanitizer  # noqa: E402


def _raw_source(**overrides) -> dict:
    node = {
        "question_id": "L3-1.1.2",
        "level": 3,
        "parent_question_id": "L2-1.1",
        "normalized_question": "When are UC symptoms severe enough to need urgent care?",
        "topic": "Acute severe ulcerative colitis",
        "subtopic": "Red flags",
        "user_goal": "Recognize when to seek urgent care",
        "recurrence_band": "High",
        "approximate_example_count": 120,
        "aggregate_engagement_band": "High proxy",
        "supporting_public_urls": [
            "https://www.reddit.com/r/UlcerativeColitis/comments/abc123/my_flare_story/",
            "https://reddit.com/user/some_redditor/posts",
        ],
        "paraphrased_demand_rationale": "Many threads describe u/some_redditor's personal flare narrative.",
        "urgency_clinical_risk": "High",
        "expected_answer_format": "Red-flag checklist",
        "suggested_next_questions": ["..."],
        "current_evidence_package_coverage": "none",
        "likely_evidence_gap": "Full narrative about the poster's ER visit at reddit.com/r/IBD/x",
        "confidence": "medium",
        "sampling_limitations": "n/a",
        "privacy_licensing_notes": "public only",
        "human_review_status": "",
        "human_review_notes": "",
        "approval": "",
        "username": "some_redditor",
        "profile_url": "https://reddit.com/user/some_redditor",
        "contact_details": "",
        "exact_location": "",
        "identifiable_personal_health_narrative": "",
    }
    node.update(overrides)
    return node


def test_reddit_bearing_source_still_produces_a_clean_derivative_by_dropping_fields():
    node = _raw_source()
    rec = sanitizer.sanitize_node(node)

    # only the permitted fields made it into the output
    assert set(rec.keys()) == {
        "nodeId", "parentId", "normalizedQuestion", "topicId",
        "priorityBand", "recurrenceBand", "evidenceCoverage",
    }
    assert rec["nodeId"] == "L3-1.1.2"
    assert rec["parentId"] == "L2-1.1"
    assert rec["normalizedQuestion"].startswith("When are UC symptoms")
    assert rec["topicId"] == "Acute severe ulcerative colitis"
    assert rec["priorityBand"] == "High"
    assert rec["recurrenceBand"] == "High"
    assert rec["evidenceCoverage"] == "none"

    # none of the discarded Reddit-bearing text leaked into the output
    blob = json.dumps(rec).lower()
    assert "reddit" not in blob
    assert "some_redditor" not in blob
    assert "http" not in blob

    errors = sanitizer.validate_output_record(rec)
    assert errors == []


def test_build_end_to_end_on_a_reddit_bearing_source_file(tmp_path):
    src = tmp_path / "uc_39_question_tree.json"
    src.write_text(json.dumps({"nodes": [_raw_source(), _raw_source(question_id="L1-1", parent_question_id="")]}))
    doc = sanitizer.build(src)
    assert len(doc["nodes"]) == 2
    blob = json.dumps(doc).lower()
    assert "reddit" not in blob and "redditor" not in blob and "http" not in blob


def test_abort_is_triggered_only_by_polluted_output_not_by_discarded_input_fields():
    # a source whose PERMITTED fields are clean, but discarded fields are drenched in Reddit
    # content, must sanitize successfully (no abort).
    clean = _raw_source(
        supporting_public_urls=["https://reddit.com/r/x/y"] * 50,
        paraphrased_demand_rationale="https://reddit.com/u/whoever " * 20,
    )
    rec = sanitizer.sanitize_node(clean)
    assert sanitizer.validate_output_record(rec) == []

    # now pollute a PERMITTED field itself -> must fail validation
    polluted = _raw_source(topic="See https://reddit.com/r/UlcerativeColitis for details")
    rec2 = sanitizer.sanitize_node(polluted)
    errors = sanitizer.validate_output_record(rec2)
    assert errors, "a polluted permitted OUTPUT field must fail validation"


def test_build_raises_when_any_output_record_is_polluted(tmp_path):
    src = tmp_path / "uc_39_question_tree.json"
    src.write_text(json.dumps({"nodes": [_raw_source(topic="visit u/some_redditor for more")]}))
    with pytest.raises(ValueError):
        sanitizer.build(src)


def test_missing_source_file_is_not_an_error(tmp_path):
    rc = sanitizer.main(["--source", str(tmp_path / "absent.json"), "--check"])
    assert rc == 0
