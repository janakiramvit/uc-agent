from __future__ import annotations

import json

from uc_evidence_discovery import artifact, config
from uc_evidence_discovery.apis.http import host_allowed


def test_reddit_hosts_are_never_allowed():
    for host in ("reddit.com", "www.reddit.com", "old.reddit.com", "redd.it"):
        assert host_allowed(f"https://{host}/r/UlcerativeColitis") is False


def test_allowlisted_hosts_contain_no_reddit_entry():
    for host in config.API_HOST_ALLOWLIST:
        assert "reddit" not in host and "redd.it" not in host


def test_deny_substrings_cover_reddit_variants():
    assert any("reddit" in d for d in config.DENY_HOST_SUBSTRINGS)


def test_topic_map_is_the_only_reddit_derived_input_the_runner_reads():
    """screening.py / runner.py must not reference the raw question-tree filename."""
    from uc_evidence_discovery import runner, screening

    text = open(runner.__file__).read() + open(screening.__file__).read()
    assert "uc_39_question_tree" not in text


def test_redacted_artifact_never_contains_a_reddit_url(tmp_path):
    path = artifact.build(
        run_id="uc-exp-000000000001", run_url="https://x/runs/1",
        started_at="t0", finished_at="t1", source_data_cutoff="t0", status="partial",
        counters={"elapsedResearchSeconds": 1, "queriesConsumed": 1, "recordsScreened": 1,
                  "sourcesAccepted": 0, "claimsExtracted": 0, "pdfsDownloaded": 0},
        disposition_reason_categories={}, accepted_sources=[],
        query_labels=["acute severe ulcerative colitis"], qa_summary={"total": 0, "passed": 0, "failed": 0},
        checkpoint_valid=True, next_topic_id="T-UCX-03", error_categories=[], out_dir=tmp_path,
    )
    blob = path.read_text("utf-8").lower()
    assert "reddit" not in blob and "redd.it" not in blob
