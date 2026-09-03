"""Evidence-backend selector.

The app retrieves evidence from the fixed JSON file (``evidence_loader.load_evidence_package``).
A Supabase-backed path exists in ``supabase_evidence_source`` but is **dormant**: it is
only reachable when BOTH

    EVIDENCE_BACKEND=supabase
    EVIDENCE_SUPABASE_ENABLED=1

are set in the environment. Neither is set by default or in ``.env.example``. The
migration gate (see ``db/PLAN-v1.0.0.md``) must pass before anyone sets them.

Nothing here runs a query - it only decides which loader the caller should use, and
refuses the DB path unless it has been explicitly, deliberately enabled.
"""

from __future__ import annotations

import os

FILE_BACKEND = "file"
SUPABASE_BACKEND = "supabase"


class SupabaseBackendNotEnabled(RuntimeError):
    """Raised when EVIDENCE_BACKEND=supabase without EVIDENCE_SUPABASE_ENABLED=1."""


def get_evidence_backend() -> str:
    """Return the active backend name. Defaults to ``"file"``.

    Raises :class:`SupabaseBackendNotEnabled` if ``supabase`` is requested but the
    explicit enable flag is not set - the DB path never activates by accident.
    """
    backend = (os.environ.get("EVIDENCE_BACKEND") or FILE_BACKEND).strip().lower()
    if backend == FILE_BACKEND:
        return FILE_BACKEND
    if backend == SUPABASE_BACKEND:
        if os.environ.get("EVIDENCE_SUPABASE_ENABLED", "").strip() != "1":
            raise SupabaseBackendNotEnabled(
                "EVIDENCE_BACKEND=supabase requires EVIDENCE_SUPABASE_ENABLED=1. "
                "Supabase-backed retrieval stays disabled until the migration gate passes."
            )
        return SUPABASE_BACKEND
    raise ValueError(f"unknown EVIDENCE_BACKEND {backend!r} (expected 'file' or 'supabase')")


def load_active_evidence_package():
    """Load the evidence package via whichever backend is active.

    Default path is unchanged from before this module existed.
    """
    if get_evidence_backend() == FILE_BACKEND:
        from agent_core.evidence_loader import load_evidence_package

        return load_evidence_package()

    # supabase path - imported lazily; only reached when explicitly enabled.
    from agent_core.supabase_evidence_source import load_evidence_package_from_db

    return load_evidence_package_from_db()
