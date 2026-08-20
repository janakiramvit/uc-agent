"""Persisted, non-clinical user preference store.

Holds exactly three things: preferred answer length (short/standard/
detailed), preferred language tag (stored only -- no translation is
implemented), and whether citations should be expanded by default.

Persists across a session restart via a local JSON file under this
project's own ``memory_store/`` directory (never the evidence
``data/`` directory, and never the read-only source evidence file).

Like ``SessionMemory``, every write path here runs through
``validate_before_store`` first, so this store can never end up holding
a diagnosis, flare prediction, medication recommendation, or other
blocked clinical content -- even though its schema is already narrow
enough (three constrained fields) that such content has nowhere to go.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memory.guard import validate_before_store

ALLOWED_ANSWER_LENGTHS = ("short", "standard", "detailed")

DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "memory_store" / "user_preferences.json"

_DEFAULTS: dict[str, Any] = {
    "answer_length": "standard",
    "language": "en",
    "citations_expanded_default": False,
}


class UserPreferenceMemory:
    def __init__(self, path: str | Path = DEFAULT_STORE_PATH):
        self.path = Path(path)
        self._data: dict[str, Any] = dict(_DEFAULTS)
        self._load_from_disk()

    # --- persistence -------------------------------------------------

    def _load_from_disk(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as f:
                on_disk = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(on_disk, dict):
            return
        for key in _DEFAULTS:
            if key in on_disk:
                try:
                    validate_before_store(on_disk[key])
                except Exception:
                    continue  # never load blocked content from disk either
                self._data[key] = on_disk[key]

    def _save(self) -> None:
        validate_before_store(self._data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    # --- fields -------------------------------------------------

    @property
    def answer_length(self) -> str:
        return self._data["answer_length"]

    def set_answer_length(self, value: str) -> None:
        if value not in ALLOWED_ANSWER_LENGTHS:
            raise ValueError(f"answer_length must be one of {ALLOWED_ANSWER_LENGTHS}, got {value!r}")
        validate_before_store(value)
        self._data["answer_length"] = value
        self._save()

    @property
    def language(self) -> str:
        return self._data["language"]

    def set_language(self, tag: str) -> None:
        # Stores the language tag only -- no translation is implemented.
        validate_before_store(tag)
        self._data["language"] = tag
        self._save()

    @property
    def citations_expanded_default(self) -> bool:
        return bool(self._data["citations_expanded_default"])

    def set_citations_expanded_default(self, flag: bool) -> None:
        self._data["citations_expanded_default"] = bool(flag)
        self._save()

    # --- clear -------------------------------------------------

    def clear(self) -> None:
        self._data = dict(_DEFAULTS)
        self._save()

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)
