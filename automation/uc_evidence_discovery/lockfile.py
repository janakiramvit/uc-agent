"""Advisory run lock, stored at ``<state-root>/state/run.lock`` and **never committed**.

A stale lock (older than :data:`STALE_AFTER_SECONDS`) may be reclaimed *only* after confirming
via the GitHub Actions API that its workflow run is no longer active. If activity cannot be
determined, the lock is treated as held.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .errors import LockHeld

STALE_AFTER_SECONDS = 20 * 60


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _iso(dt: _dt.datetime) -> str:
    return dt.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class LockInfo:
    runId: str
    workflowRunUrl: str
    triggeringCommit: str
    createdAt: str
    expiryAt: str
    host: str
    status: str = "held"

    @classmethod
    def new(cls, *, run_id: str, run_url: str, commit: str, ttl_seconds: int = STALE_AFTER_SECONDS) -> "LockInfo":
        now = _utcnow()
        return cls(
            runId=run_id,
            workflowRunUrl=run_url,
            triggeringCommit=commit,
            createdAt=_iso(now),
            expiryAt=_iso(now + _dt.timedelta(seconds=ttl_seconds)),
            host=socket.gethostname(),
        )

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2) + "\n"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def acquire(
    path: Path,
    info: LockInfo,
    *,
    is_run_active: Callable[[str], Optional[bool]] = lambda _run_id: None,
    stale_after_seconds: int = STALE_AFTER_SECONDS,
    now: Optional[_dt.datetime] = None,
) -> None:
    """Write ``info`` to ``path`` or raise :class:`LockHeld`.

    ``is_run_active`` maps a run id (parsed from the existing lock) to ``True`` (still
    running), ``False`` (finished), or ``None`` (unknown). ``None`` ⇒ do not reclaim.
    """
    now = now or _utcnow()
    existing = read(path)
    if existing:
        created = existing.get("createdAt")
        age = None
        if created:
            try:
                age = (now - _parse_iso(created)).total_seconds()
            except ValueError:
                age = None
        is_stale = age is not None and age >= stale_after_seconds
        if not is_stale:
            raise LockHeld(
                f"run.lock held by run {existing.get('runId')} "
                f"(age {int(age) if age is not None else 'unknown'}s); not stale"
            )
        # stale — only reclaim if the corresponding workflow run is definitely not active
        other_run = existing.get("runId", "")
        active = is_run_active(other_run)
        if active is not False:
            raise LockHeld(
                f"stale run.lock for run {other_run!r} but its workflow run is "
                f"{'still active' if active else 'of unknown status'}; not reclaiming"
            )
    _atomic_write(path, info.to_json())


def release(path: Path, run_id: str, *, now: Optional[_dt.datetime] = None) -> None:
    """Mark the lock released if we own it. Safe to call multiple times / after errors."""
    existing = read(path)
    if not existing or existing.get("runId") != run_id:
        return
    existing["status"] = "released"
    existing["releasedAt"] = _iso(now or _utcnow())
    try:
        _atomic_write(path, json.dumps(existing, indent=2) + "\n")
    except OSError:
        pass
