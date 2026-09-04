from __future__ import annotations

import json

import pytest

from uc_evidence_discovery import artifact


def _build(tmp_path, **overrides):
    kwargs = dict(
        run_id="uc-exp-000000000001", run_url="https://x/runs/1",
        started_at="2026-09-04T00:00:00Z", finished_at="2026-09-04T00:08:00Z",
        source_data_cutoff="2026-09-01T00:00:00Z", status="partial",
        counters={"elapsedResearchSeconds": 300, "queriesConsumed": 4, "recordsScreened": 20,
                  "sourcesAccepted": 2, "claimsExtracted": 6, "pdfsDownloaded": 0},
        disposition_reason_categories={"not_relevant": 3, "duplicate_doi": 1},
        accepted_sources=[{"sourceId": "SRC-100", "title": "A guideline title", "doi": "10.1/x",
                           "pubmedId": "1", "pmcId": "", "clinicalTrialsId": "",
                           "canonicalUrl": "https://doi.org/10.1/x", "ucApplicability": "ulcerative_colitis"}],
        query_labels=["acute severe ulcerative colitis truelove witts"],
        qa_summary={"total": 15, "passed": 15, "failed": 0},
        checkpoint_valid=True, next_topic_id="T-UCX-03", error_categories=[],
        out_dir=tmp_path,
    )
    kwargs.update(overrides)
    return artifact.build(**kwargs)


def test_artifact_contains_only_allowlisted_fields(tmp_path):
    path = _build(tmp_path)
    doc = json.loads(path.read_text("utf-8"))
    allowed_top = {
        "artifactSchema", "runId", "workflowRunUrl", "startedAt", "finishedAt",
        "sourceDataCutoff", "status", "counters", "dispositionReasonCategories",
        "queryLabels", "acceptedSources", "qa", "checkpointValidation", "nextTopicId",
        "errorCategories", "note",
    }
    assert set(doc.keys()) == allowed_top
    src = doc["acceptedSources"][0]
    assert set(src.keys()) == {
        "sourceId", "title", "doi", "pubmedId", "pmcId", "clinicalTrialsId",
        "canonicalUrl", "ucApplicability", "reviewStatus",
    }


def test_artifact_excludes_abstracts_and_excerpts_and_raw_responses(tmp_path):
    path = _build(tmp_path)
    blob = path.read_text("utf-8").lower()
    for forbidden in ("abstracttext", "exactsupportingexcerpt", "normalizedclaim", "rawresponse"):
        assert forbidden not in blob


def test_query_labels_are_coarsened_not_verbatim(tmp_path):
    path = _build(tmp_path, query_labels=["EXT_ID:36822736 AND SRC:MED complex[filter]"])
    doc = json.loads(path.read_text("utf-8"))
    assert "EXT_ID:36822736" not in doc["queryLabels"][0]


def test_build_refuses_to_write_if_a_secret_like_token_sneaks_in(tmp_path):
    with pytest.raises(AssertionError):
        _build(tmp_path, run_url="https://x/runs/1?token=ghp_" + "a" * 30)


def test_markdown_companion_is_also_written(tmp_path):
    json_path = _build(tmp_path)
    md_path = json_path.with_suffix(".md")
    assert md_path.exists()
    text = md_path.read_text("utf-8").lower()
    assert "abstracttext" not in text
