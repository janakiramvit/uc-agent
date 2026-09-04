"""Typed control-flow exceptions for the runner."""

from __future__ import annotations


class RunnerError(Exception):
    """Base class for all runner-raised errors."""


class SafeStop(RunnerError):
    """Raised when the runner must stop *before* doing research but has left a recoverable
    state behind (e.g. both checkpoint files invalid, staging worktree missing, another run
    holds the lock). Exit code 0 with a partial/safe status; never a crash."""


class LockHeld(SafeStop):
    """Another run holds a valid (non-stale, or stale-but-still-active) lock."""


class UntrustedStateRoot(RunnerError):
    """``--state-root`` failed validation: not a worktree of the staging branch, is on
    ``sys.path``, or overlaps the trusted-code tree."""
