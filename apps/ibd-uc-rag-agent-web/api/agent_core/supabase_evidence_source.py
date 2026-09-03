"""Dormant Supabase-backed evidence source.

Builds the same :class:`agent_core.evidence_loader.EvidencePackage` the file loader
produces, but from the ``canonical.v_prototype_*`` views over a **server-side**
connection (role ``evidence_reader``; ``EVIDENCE_SUPABASE_DB_URL``). Never runs in the
browser. Not imported unless ``EVIDENCE_BACKEND=supabase`` AND
``EVIDENCE_SUPABASE_ENABLED=1`` (see ``evidence_backend.py``).

Requires ``psycopg`` (not in the app's base requirements). Kept import-light so the
module can be inspected without the dependency installed.
"""

from __future__ import annotations

import os

from agent_core.evidence_loader import EvidencePackage

_UC = "ulcerative_colitis"


def _connect():
    dsn = os.environ.get("EVIDENCE_SUPABASE_DB_URL")
    if not dsn:
        raise RuntimeError(
            "EVIDENCE_SUPABASE_DB_URL is not set (server-side only; never NEXT_PUBLIC_*)."
        )
    import psycopg  # local import - optional dependency

    return psycopg.connect(dsn, autocommit=True)


def load_evidence_package_from_db(conn=None) -> EvidencePackage:
    own = conn is None
    conn = conn or _connect()
    try:
        claims = [r[0] for r in conn.execute(
            "SELECT claim_json FROM canonical.v_prototype_claim").fetchall()]
        sources = [r[0] for r in conn.execute(
            "SELECT source_json FROM canonical.v_prototype_source").fetchall()]
        excluded = [r[0] for r in conn.execute(
            "SELECT claim_ref FROM canonical.v_prototype_excluded_claim_id").fetchall()]
        limitations = [r[0] for r in conn.execute(
            "SELECT text FROM canonical.v_prototype_limitation ORDER BY ordinal").fetchall()]
        meta = conn.execute(
            "SELECT version, package_meta FROM canonical.v_dataset WHERE code='prototype-v1'"
        ).fetchone() or ("prototype-v1", {})
    finally:
        if own:
            conn.close()

    version, pkg_meta = meta
    sources_by_id = {s["sourceId"]: s for s in sources}
    excluded_set = set(excluded)
    all_claims = [c for c in claims if c.get("claimId") not in excluded_set]
    uc_eligible = [c for c in all_claims if _UC in (c.get("conditionApplicability") or "")]
    crohns_only = [c for c in all_claims
                   if (c.get("conditionApplicability") or "").strip() == "crohns_disease"]

    return EvidencePackage(
        version=version or "prototype-v1",
        created_at=(pkg_meta or {}).get("created_at", ""),
        intended_use=(pkg_meta or {}).get("intended_use", ""),
        sources_by_id=sources_by_id,
        all_claims=all_claims,
        excluded_claim_ids=excluded_set,
        uc_eligible_claims=uc_eligible,
        crohns_only_claims=crohns_only,
        limitations=limitations,
    )
