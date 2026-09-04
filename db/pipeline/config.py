"""Versions, filesystem paths, and the input-file registry.

No secrets live here. ``DATABASE_URL`` / ``PROD_HOST_DENYLIST`` are read from
``db/.env`` (gitignored) at runtime by :func:`load_env`, never hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROMPT_VERSION = "1.0.0"
CANONICAL_SCHEMA_VERSION = "1.0.0"

# db/ package root, repo root
DB_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = DB_DIR.parent

# Where generated (gitignored) artifacts go.
SCHEMA_INFERRED_DIR = DB_DIR / "schema" / "inferred"
REPORTS_DIR = DB_DIR / "reports"
MIGRATIONS_DIR = DB_DIR / "supabase" / "migrations"

KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "ibd-research-review"
# Optional byte-identical mirror kept outside the repo (see MIGRATION_REPORT.md). Used
# only as a fallback if the in-repo copy is missing. Set IBD_RESEARCH_REVIEW_MIRROR to
# point at it; no machine-specific path is hard-coded here.
EXTERNAL_MIRROR = Path(os.environ.get("IBD_RESEARCH_REVIEW_MIRROR", KNOWLEDGE_DIR))

APP_DIR = REPO_ROOT / "apps" / "ibd-uc-rag-agent-web"
APP_EVIDENCE_JSON = APP_DIR / "api" / "data" / "ibd-prototype-evidence.json"

DATASET_BASELINE = "baseline-register"
DATASET_PROTOTYPE = "prototype-v1"


def _first_existing(*candidates: Path) -> Path:
    for c in candidates:
        if c.is_file():
            return c
    # Return the first candidate so callers can raise a clear FileNotFoundError.
    return candidates[0]


@dataclass(frozen=True)
class InputFile:
    key: str
    role: str  # "load" | "qa_overlay" | "reconcile" | "oracle"
    dataset: str | None
    path: Path
    note: str = ""


def input_registry() -> dict[str, InputFile]:
    """The canonical list of inputs for Prompt v1.0.0.

    ``load``       -> parsed into staging.* (source/claim/excluded)
    ``qa_overlay`` -> parsed into staging.claim_qa_raw / staging.reconcile_raw only
    ``reconcile``  -> read-only comparison reference; never written to staging/canonical
    ``oracle``     -> shadow-test fixture (post-promotion)
    """
    reg = _first_existing(
        KNOWLEDGE_DIR / "ibd-evidence-review-final-remediation.xlsx",
        EXTERNAL_MIRROR / "ibd-evidence-review-final-remediation.xlsx",
    )
    qa = _first_existing(
        KNOWLEDGE_DIR / "ibd-evidence-review-final-remediation-qa.xlsx",
        EXTERNAL_MIRROR / "ibd-evidence-review-final-remediation-qa.xlsx",
    )
    items = [
        InputFile("register_workbook", "load", DATASET_BASELINE, reg,
                  "authoritative baseline source/claim register"),
        InputFile("qa_workbook", "qa_overlay", DATASET_BASELINE, qa,
                  "QA/reconciliation overlay ONLY - never populates source/claim"),
        InputFile("prototype_workbook", "load", DATASET_PROTOTYPE,
                  KNOWLEDGE_DIR / "ibd-prototype-evidence-review.xlsx",
                  "existing 49/20 prototype cut - reproduce + shadow-test only"),
        InputFile("prototype_json", "oracle", DATASET_PROTOTYPE,
                  KNOWLEDGE_DIR / "ibd-prototype-evidence.json",
                  "shadow-test oracle (byte-identical to the app's api/data copy)"),
        InputFile("candidate_claims_json", "reconcile", DATASET_BASELINE,
                  KNOWLEDGE_DIR / "extracted-claims" / "candidate-claims.json",
                  "pre-filter extraction output (models.py list-typed schema)"),
        InputFile("prototype_exclusions_json", "reconcile", DATASET_PROTOTYPE,
                  KNOWLEDGE_DIR / "prototype-evidence-exclusions.json", ""),
        InputFile("prototype_summary_json", "reconcile", DATASET_PROTOTYPE,
                  KNOWLEDGE_DIR / "prototype-evidence-summary.json", ""),
        InputFile("removed_replaced_json", "reconcile", DATASET_BASELINE,
                  KNOWLEDGE_DIR / "archive" / "removed-claims" / "removed-and-replaced-claims.json", ""),
        InputFile("run_summary_json", "reconcile", DATASET_BASELINE,
                  KNOWLEDGE_DIR / "run-summary-final-remediation-qa.json", ""),
    ]
    return {i.key: i for i in items}


# Deferred - Phase 2. Never opened by the v1.0.0 pipeline.
PHASE_2_DIR = REPO_ROOT / "knowledge" / "uc-evidence-expansion"


@dataclass
class Settings:
    database_url: str | None = None
    prod_host_denylist: tuple[str, ...] = ()
    db_environment: str = ""           # must be "development" to connect
    expected_dev_host: str = ""        # must exactly match the parsed DATABASE_URL host
    canonical_schema: str = "canonical"
    staging_schema: str = "staging"
    quarantine_schema: str = "quarantine"
    _loaded_from: str = field(default="", repr=False)

    @property
    def has_db(self) -> bool:
        return bool(self.database_url)

    @property
    def is_declared_development(self) -> bool:
        return self.db_environment.strip().lower() in {"development", "dev"}


def load_env(dotenv_path: Path | None = None) -> Settings:
    """Load settings from ``db/.env`` (or the process env). Never logs the value."""
    path = dotenv_path or (DB_DIR / ".env")
    data: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip().strip('"').strip("'")
    getenv = lambda k: os.environ.get(k) or data.get(k) or None  # noqa: E731
    denylist = tuple(
        h.strip() for h in (getenv("PROD_HOST_DENYLIST") or "").split(",") if h.strip()
    )
    return Settings(
        database_url=getenv("DATABASE_URL"),
        prod_host_denylist=denylist,
        db_environment=getenv("DB_ENVIRONMENT") or "",
        expected_dev_host=(getenv("EXPECTED_DEV_HOST") or "").strip().lower(),
        canonical_schema=getenv("CANONICAL_SCHEMA") or "canonical",
        staging_schema=getenv("STAGING_SCHEMA") or "staging",
        quarantine_schema=getenv("QUARANTINE_SCHEMA") or "quarantine",
        _loaded_from=str(path) if path.is_file() else "process-env",
    )


def redact_dsn(dsn: str | None) -> str:
    """Return a safe-to-log identifier for a connection string.

    Never includes the URL, username, password, or complete host - only a one-way,
    non-reversible fingerprint of the host (for correlating log lines / confirming
    "same target as last time"), plus the literal db name.
    """
    if not dsn:
        return "<unset>"
    try:
        import hashlib
        from urllib.parse import urlsplit

        parts = urlsplit(dsn)
        host = parts.hostname or ""
        db = (parts.path or "").lstrip("/") or "?"
        fp = hashlib.sha256(host.encode()).hexdigest()[:8] if host else "????????"
        return f"postgres://<redacted>@<host-fingerprint:{fp}>/{db}"
    except Exception:
        return "<unparseable-dsn>"
