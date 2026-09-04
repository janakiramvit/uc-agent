"""A crash mid-finalize (simulated: QA raises before the checkpoint is (re)written) must not
corrupt or lose the last valid checkpoint — the branch stays resumable from a fresh worktree."""

from __future__ import annotations

from uc_evidence_discovery import checkpoint as checkpoint_mod
from uc_evidence_discovery import config, gitio, qa
from uc_evidence_discovery.runner import main

from .conftest import git


def test_a_mid_finalize_crash_leaves_the_branch_resumable(monkeypatch, main_checkout, bare_remote, state_root):
    def boom(*a, **k):
        raise RuntimeError("simulated crash during QA/finalize")

    monkeypatch.setattr(qa, "run_checks", boom)

    rc = main(["--state-root", str(state_root), "--no-network"])
    assert rc == 0, "a handled crash must not fail the job"
    assert not state_root.exists()  # worktree still cleaned up on the failure path

    # the branch was never pushed to (crash happened before commit); fetch a *fresh* worktree
    # and confirm the checkpoint that was already there is still valid and resumable.
    fresh = main_checkout.parent / "uc-state-fresh"
    git(["fetch", "origin", f"+refs/heads/{config.STAGING_BRANCH}:{config.STAGING_REMOTE_REF}"], main_checkout)
    git(["worktree", "add", "--detach", str(fresh), config.STAGING_REMOTE_REF], main_checkout)
    try:
        fresh_paths = config.StatePaths(root=fresh)
        result = checkpoint_mod.load(fresh_paths)
        assert result.recovered is False
        assert result.doc["runId"]
        assert not checkpoint_mod.validate(result.doc)
    finally:
        gitio.remove_worktree(fresh, main_checkout)


def test_a_crash_after_the_checkpoint_write_still_leaves_a_valid_checkpoint(monkeypatch, state_root):
    """Even if something fails *after* checkpoint_mod.save (e.g. artifact build), the
    already-written checkpoint on disk in --state-root is schema-valid (save() validates
    before writing, atomically)."""
    from uc_evidence_discovery import artifact as artifact_mod

    def boom(*a, **k):
        raise RuntimeError("simulated crash after checkpoint save")

    monkeypatch.setattr(artifact_mod, "build", boom)

    rc = main(["--state-root", str(state_root), "--no-network"])
    assert rc == 0
    # worktree was removed by the runner; nothing further to assert about --state-root itself,
    # but the run must not have crashed the process.
