from __future__ import annotations

from uc_evidence_discovery.runner import main

from .conftest import MINIMAL_CHECKPOINT


def test_dry_run_resumes_from_the_saved_topic_search_and_cursor(state_root, state_paths):
    rc = main(["--state-root", str(state_root), "--dry-run", "--no-network"])
    assert rc == 0
    import json

    saved = json.loads(state_paths.checkpoint_path.read_text("utf-8"))
    # research_skipped (no_network) leaves pendingSearches untouched -> same resume point
    assert saved["pendingSearches"] == MINIMAL_CHECKPOINT["pendingSearches"]
    assert saved["nextRecommendedOperation"]["topicId"] == "T-UCX-03"
    assert saved["nextRecommendedOperation"]["searchId"] == "S-UCX-03-a"
    assert saved["nextRecommendedOperation"]["cursor"] == 0


def test_pending_identifiers_are_not_rescreened(state_root, state_paths):
    """Identifiers already in processedSourceIdentifiers must be treated as known before any
    new screening — verified at the dedup-index layer used by the runner."""
    from uc_evidence_discovery.checkpoint import load
    from uc_evidence_discovery.dedup import CandidateKey, ProcessedIndex

    cp = load(state_paths).doc
    index = ProcessedIndex.from_checkpoint(cp)
    dup = index.duplicate_reason(CandidateKey(doi="10.1053/j.gastro.2022.12.007"))
    assert dup is not None and "duplicate_doi" in dup
