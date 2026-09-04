"""Two-tier timing budget.

* soft deadline  – no new query and no new record screened after this point;
* finalize deadline – all QA / checkpoint / journal / artifact / commit / push / lock-release
  and worktree removal must be done by here, leaving the final window for the separate
  actions/upload-artifact step and GitHub runner cleanup inside the 10-minute hard timeout.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from . import config


@dataclass
class Deadline:
    soft_seconds: float = config.SOFT_DEADLINE_SECONDS
    finalize_seconds: float = config.FINALIZE_DEADLINE_SECONDS
    _start: float = field(default_factory=time.monotonic)

    def elapsed(self) -> float:
        return time.monotonic() - self._start

    def soft_expired(self) -> bool:
        return self.elapsed() >= self.soft_seconds

    def finalize_expired(self) -> bool:
        return self.elapsed() >= self.finalize_seconds

    def remaining_soft(self) -> float:
        return max(0.0, self.soft_seconds - self.elapsed())

    def remaining_finalize(self) -> float:
        return max(0.0, self.finalize_seconds - self.elapsed())

    def may_start_new_work(self) -> bool:
        """True only while it is safe to begin another query or screen another record."""
        return not self.soft_expired()
