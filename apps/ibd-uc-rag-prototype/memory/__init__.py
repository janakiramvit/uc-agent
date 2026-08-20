"""Memory layers for the UC RAG prototype.

Two clearly separate stores:

  - ``SessionMemory``  -- in-memory only, scoped to one Streamlit
    session (backed by ``st.session_state``), never written to disk.
  - ``UserPreferenceMemory`` -- small, non-clinical preferences that may
    persist across a session restart via a local JSON file under
    ``memory_store/`` (never the evidence ``data/`` directory).

Both stores share a hard, code-enforced guard (``guard.py``) that
refuses to store diagnosis language, flare predictions, medication-
change recommendations, unsupported medical conclusions, or unreviewed
evidence treated as approved fact. See ``clear_all_memory`` to wipe both
stores at once (wired to the Streamlit "Clear my data" control).
"""

from memory.guard import ClinicalContentRejected, validate_before_store
from memory.preference_memory import UserPreferenceMemory
from memory.session_memory import SessionMemory


def clear_all_memory(session_memory: SessionMemory | None, preference_memory: UserPreferenceMemory) -> None:
    """Clear both the session-only store and the persisted preference store."""
    if session_memory is not None:
        session_memory.clear()
    preference_memory.clear()


__all__ = [
    "SessionMemory",
    "UserPreferenceMemory",
    "clear_all_memory",
    "validate_before_store",
    "ClinicalContentRejected",
]
