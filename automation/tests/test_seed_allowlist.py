from __future__ import annotations

from uc_evidence_discovery import config, gitio


def test_commit_allowlist_excludes_caches_locks_and_raw_reddit_file():
    allow = config.StatePaths.COMMIT_ALLOWLIST
    deny = config.StatePaths.COMMIT_DENYLIST_SUBPATHS
    for rel in allow:
        assert not rel.startswith("knowledge/uc-evidence-expansion/retrieval-cache/")
        assert not rel.startswith("knowledge/uc-evidence-expansion/source-files/")
        assert "run.lock" not in rel
        assert "uc_39_question_tree" not in rel
        assert ".venv" not in rel and ".env" not in rel

    assert "knowledge/uc-evidence-expansion/state/run.lock" in deny
    assert "knowledge/uc-evidence-expansion/retrieval-cache/" in deny
    assert "knowledge/uc-evidence-expansion/source-files/" in deny
    assert "uc_39_question_tree.json" in deny
    assert ".uc_reddit_work/" in deny


def test_only_a_fixed_trio_is_force_added():
    force = config.StatePaths.COMMIT_FORCE_PATHS
    assert force == {
        "knowledge/uc-evidence-expansion/state/checkpoint.json",
        "knowledge/uc-evidence-expansion/state/checkpoint.json.known-good",
        "knowledge/uc-evidence-expansion/journal/run-journal.ndjson",
    }
    assert force <= set(config.StatePaths.COMMIT_ALLOWLIST)


def test_stage_paths_ignores_files_outside_the_allowlist_even_if_present(state_root, state_paths):
    # plant an out-of-band file that is NOT on the allowlist
    rogue = state_paths.evidence_dir / "retrieval-cache" / "should-not-be-staged.json"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text("{}", encoding="utf-8")
    lock = state_paths.lock_path
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("{}", encoding="utf-8")

    staged = gitio.stage_paths(state_paths)
    assert not any("retrieval-cache" in s for s in staged)
    assert not gitio.has_staged_changes(state_paths)  # nothing tracked changed


def test_stage_paths_only_touches_allowlisted_relative_paths(state_paths):
    staged = gitio.stage_paths(state_paths)
    for rel in staged:
        assert rel in config.StatePaths.COMMIT_ALLOWLIST
