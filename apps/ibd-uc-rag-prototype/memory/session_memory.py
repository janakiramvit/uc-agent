"""Session-scoped, in-memory-only store.

Holds: the current question, the IDs of claims retrieved for it, the
conversation turns (question+answer pairs) for this session only, and
the safety warnings already shown this session. Never written to disk.

In a running Streamlit app this is backed directly by
``st.session_state`` (see ``get_streamlit_session_memory`` below) so it
is naturally scoped to one browser session and disappears when that
session ends. In tests / non-Streamlit contexts it can be backed by a
plain dict, which makes two independently-constructed ``SessionMemory``
instances provably isolated from each other.
"""

from __future__ import annotations

from typing import Any, MutableMapping

from memory.guard import validate_before_store

_DEFAULTS = {
    "current_question": None,
    "retrieved_claim_ids": [],
    "turns": [],
    "safety_warnings_shown": [],
}


class SessionMemory:
    """In-memory-only session store. Never persisted to disk."""

    def __init__(self, backing: MutableMapping[str, Any] | None = None):
        # ``backing`` is typically ``st.session_state`` (dict-like) in the
        # real app, or a plain dict in tests -- either way this class
        # never opens a file or database connection.
        self._store: MutableMapping[str, Any] = backing if backing is not None else {}
        for key, default in _DEFAULTS.items():
            if key not in self._store:
                self._store[key] = default() if callable(default) else (list(default) if isinstance(default, list) else default)

    # --- current question -------------------------------------------------

    @property
    def current_question(self) -> str | None:
        return self._store.get("current_question")

    def set_current_question(self, question: str | None) -> None:
        if question is not None:
            validate_before_store(question)
        self._store["current_question"] = question

    # --- retrieved claim ids -------------------------------------------------

    @property
    def retrieved_claim_ids(self) -> list[str]:
        return list(self._store.get("retrieved_claim_ids", []))

    def set_retrieved_claim_ids(self, claim_ids: list[str]) -> None:
        claim_ids = list(claim_ids)
        validate_before_store(claim_ids)
        self._store["retrieved_claim_ids"] = claim_ids

    # --- conversation turns -------------------------------------------------

    @property
    def turns(self) -> list[dict[str, str]]:
        return list(self._store.get("turns", []))

    def add_turn(self, question: str, answer: str) -> None:
        validate_before_store(question)
        validate_before_store(answer)
        self._store.setdefault("turns", [])
        self._store["turns"].append({"question": question, "answer": answer})

    # --- safety warnings already shown -------------------------------------------------

    @property
    def safety_warnings_shown(self) -> list[str]:
        return list(self._store.get("safety_warnings_shown", []))

    def add_safety_warning(self, message: str) -> None:
        if not message:
            return
        validate_before_store(message)
        self._store.setdefault("safety_warnings_shown", [])
        if message not in self._store["safety_warnings_shown"]:
            self._store["safety_warnings_shown"].append(message)

    # --- clear -------------------------------------------------

    def clear(self) -> None:
        """Reset all fields in place (so any external reference such as
        ``st.session_state`` keeps working after clearing)."""
        self._store["current_question"] = None
        self._store["retrieved_claim_ids"] = []
        self._store["turns"] = []
        self._store["safety_warnings_shown"] = []

    def as_dict(self) -> dict[str, Any]:
        return {
            "current_question": self.current_question,
            "retrieved_claim_ids": self.retrieved_claim_ids,
            "turns": self.turns,
            "safety_warnings_shown": self.safety_warnings_shown,
        }


def get_streamlit_session_memory() -> SessionMemory:
    """Return the ``SessionMemory`` bound to the current Streamlit
    session, creating it on first use. Requires an active Streamlit
    script run context; only call this from ``streamlit_app.py``."""
    import streamlit as st

    if "_session_memory" not in st.session_state:
        st.session_state["_session_memory"] = SessionMemory(backing=st.session_state)
    return st.session_state["_session_memory"]
