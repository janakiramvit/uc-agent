"""Deterministic SRC-/CLM- identifier allocation.

Next ids are computed from the *union* of every registry that could contain one — never from
the prompt's hard-coded ``SRC-035`` / ``CLM-128``. If the live registries are ahead of the
prompt, the registries win.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from . import config

_SRC_RE = re.compile(r"\bSRC-(\d{3,})\b")
_CLM_RE = re.compile(r"\bCLM-(\d{3,})\b")


def _nums(text: str, rx: re.Pattern) -> set[int]:
    return {int(m.group(1)) for m in rx.finditer(text)}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def scan_existing(paths: config.StatePaths, checkpoint: dict) -> tuple[set[int], set[int]]:
    """Return ``(source_numbers, claim_numbers)`` seen anywhere."""
    blobs = [
        _read(paths.sources_path),
        _read(paths.claims_path),
        json.dumps(checkpoint, ensure_ascii=False),
    ]
    src: set[int] = set()
    clm: set[int] = set()
    for blob in blobs:
        src |= _nums(blob, _SRC_RE)
        clm |= _nums(blob, _CLM_RE)
    return src, clm


class Allocator:
    """Hands out fresh, collision-checked ids for a single run."""

    def __init__(self, used_src: Iterable[int], used_clm: Iterable[int]) -> None:
        self._src = set(used_src) | {config.SOURCE_ID_FLOOR}
        self._clm = set(used_clm) | {config.CLAIM_ID_FLOOR}
        self._next_src = max(self._src) + 1
        self._next_clm = max(self._clm) + 1

    @classmethod
    def from_state(cls, paths: config.StatePaths, checkpoint: dict) -> "Allocator":
        s, c = scan_existing(paths, checkpoint)
        return cls(s, c)

    @property
    def peek_source_id(self) -> str:
        return f"SRC-{self._next_src:03d}"

    @property
    def peek_claim_id(self) -> str:
        return f"CLM-{self._next_clm:03d}"

    def source_id(self) -> str:
        while self._next_src in self._src:
            self._next_src += 1
        val = self._next_src
        self._src.add(val)
        self._next_src += 1
        return f"SRC-{val:03d}"

    def claim_id(self) -> str:
        while self._next_clm in self._clm:
            self._next_clm += 1
        val = self._next_clm
        self._clm.add(val)
        self._next_clm += 1
        return f"CLM-{val:03d}"
