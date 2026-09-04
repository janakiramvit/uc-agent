"""Append-only NDJSON run journal at ``<state-root>/journal/run-journal.ndjson``.

Same record shape as the existing file: ``{"ts", "runId", "event", "detail"}``.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


def _ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Journal:
    def __init__(self, path: Path, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: str, detail: str) -> None:
        line = json.dumps(
            {"ts": _ts(), "runId": self.run_id, "event": event, "detail": detail},
            ensure_ascii=False,
        )
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
