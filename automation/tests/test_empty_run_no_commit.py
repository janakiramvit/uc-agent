from __future__ import annotations

from uc_evidence_discovery import config, gitio, lockfile
from uc_evidence_discovery.runner import main

from .conftest import git


def test_stage_paths_and_commit_are_a_noop_when_nothing_changed(state_root):
    paths = config.StatePaths(root=state_root)
    gitio.stage_paths(paths)  # existing, unmodified files: nothing new to stage
    assert gitio.has_staged_changes(paths) is False
    assert gitio.commit(paths) is None


def test_a_run_that_cannot_acquire_the_lock_pushes_no_commit(main_checkout, bare_remote, state_root):
    """A run that never acquires the lock must return before staging/committing anything, so
    the remote staging branch is untouched (the runner also removes its own worktree on this
    path, so we check the *remote*, not the now-gone local worktree)."""
    paths = config.StatePaths(root=state_root)
    lockfile.acquire(
        paths.lock_path,
        lockfile.LockInfo.new(run_id="uc-exp-holdholdhold", run_url="https://x/runs/9", commit="abc"),
    )
    before = git(["rev-parse", f"refs/heads/{config.STAGING_BRANCH}"], bare_remote).stdout.strip()

    rc = main(["--state-root", str(state_root), "--no-network"])
    assert rc == 0  # safe stop, not a crash
    assert not state_root.exists(), "the runner removes its worktree even on a safe stop"

    after = git(["rev-parse", f"refs/heads/{config.STAGING_BRANCH}"], bare_remote).stdout.strip()
    assert after == before, "a run that never acquired the lock must push no commit"


def test_lock_file_itself_is_never_staged_or_committed(state_root):
    paths = config.StatePaths(root=state_root)
    lockfile.acquire(paths.lock_path, lockfile.LockInfo.new(
        run_id="uc-exp-aaaaaaaaaaaa", run_url="", commit=""))
    staged = gitio.stage_paths(paths)
    assert "knowledge/uc-evidence-expansion/state/run.lock" not in staged
    assert gitio.has_staged_changes(paths) is False
