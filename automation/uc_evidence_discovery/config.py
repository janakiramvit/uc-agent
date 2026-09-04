"""Static configuration: trusted-code paths, daily limits, timing budget, API allowlist.

Everything here is read from the ``main`` checkout. The only mutable-state location is the
``--state-root`` directory, whose layout is described by :class:`StatePaths`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# --- Trusted-code roots (always under the main checkout) -------------------------------------
PKG_DIR = Path(__file__).resolve().parent                 # .../automation/uc_evidence_discovery
AUTOMATION_DIR = PKG_DIR.parent                           # .../automation
REPO_ROOT = AUTOMATION_DIR.parent                         # repo root (main checkout)

EVIDENCE_SUBPATH = Path("knowledge/uc-evidence-expansion")
SCHEMA_V1_0_0 = REPO_ROOT / EVIDENCE_SUBPATH / "state" / "checkpoint.schema.json"
SCHEMA_V1_1_0 = REPO_ROOT / EVIDENCE_SUBPATH / "state" / "checkpoint.schema-v1.1.0.json"

# Redacted artifact is written under the main checkout, never under --state-root.
ARTIFACT_DIR = AUTOMATION_DIR / "artifact"

# --- Branch / commit identity --------------------------------------------------------------
STAGING_BRANCH = "automation/uc-evidence-staging"
STAGING_REMOTE_REF = f"refs/remotes/origin/{STAGING_BRANCH}"
COMMIT_MESSAGE_TEMPLATE = "chore(evidence): daily UC discovery {date}"
# Non-personal identity for staging commits. No credentials ever placed in a remote URL.
BOT_NAME = "uc-evidence-bot"
BOT_EMAIL = "uc-evidence-bot@users.noreply.github.com"

# --- Checkpoint schema versions ----------------------------------------------------------
SCHEMA_VERSION_1_0_0 = "uc-evidence-expansion-1.0.0"
SCHEMA_VERSION_1_1_0 = "uc-evidence-expansion-1.1.0"
KNOWN_GOOD_FILENAME = "checkpoint.json.known-good"   # the single, real on-disk known-good file

# --- Timing budget (seconds) -----------------------------------------------------------------
# GitHub hard timeout is 10 min (600 s). Research must not start work after the soft deadline.
# The runner must finish all finalization by FINALIZE_DEADLINE, leaving the last window for the
# separate actions/upload-artifact step + GitHub runner cleanup.
SOFT_DEADLINE_SECONDS = 450
FINALIZE_DEADLINE_SECONDS = 540
UPLOAD_CLEANUP_RESERVE_SECONDS = 60
HARD_TIMEOUT_SECONDS = 600

# --- Hard daily limits ---------------------------------------------------------------------
MAX_QUERIES = 10
MAX_SCREENED = 30
MAX_ACCEPTED = 5
MAX_CLAIMS = 20
MAX_RETRIES_PER_SERVICE = 2
BACKOFF_BASE_SECONDS = 1.5
MAX_RESPONSE_BYTES = 5_000_000
PER_HOST_MIN_INTERVAL_SECONDS = 1.0
STOP_AFTER_CONSECUTIVE_EMPTY_SEARCHES = 2

# --- Network allowlist -------------------------------------------------------------------
# Only authoritative public endpoints. No Reddit, no login/paywall/SERP hosts, no paid model
# or research APIs, no OpenAI / Anthropic.
API_HOST_ALLOWLIST = frozenset(
    {
        "www.ebi.ac.uk",            # Europe PMC REST
        "eutils.ncbi.nlm.nih.gov",  # NCBI E-utilities
        "clinicaltrials.gov",       # ClinicalTrials.gov API v2
        "api.github.com",           # stale-lock liveness check only (actions: read)
    }
)
DENY_HOST_SUBSTRINGS = ("reddit.", "redd.it", "openai.", "anthropic.", "api.anthropic.")

USER_AGENT = (
    "uc-agent-evidence-discovery/1.0 (+https://github.com/janakiramvit/uc-agent; "
    "deterministic non-LLM research staging bot)"
)

# --- ID reservations (documented in knowledge/uc-evidence-expansion/README.md) --------------
SOURCE_ID_FLOOR = 32     # SRC-001..SRC-032 reserved by prior packages
CLAIM_ID_FLOOR = 114     # CLM-001..CLM-114 reserved by prior packages

# Prompt v1.0.0 historical expectations. Used only to *report a difference*; the validated
# checkpoint is the sole source of truth and always wins.
PROMPT_EXPECTATIONS = {
    "topicId": "T-UCX-03",
    "searchId": "S-UCX-03-a",
    "cursor": 0,
    "firstNewSourceId": "SRC-035",
    "firstNewClaimId": "CLM-128",
}

# --- Research priority topics (deterministic keyword rules; no LLM) -------------------------
RESEARCH_PRIORITY_KEYWORDS = (
    "acute severe ulcerative colitis", "fulminant colitis", "truelove", "witts",
    "hospitalis", "hospitaliz", "fecal calprotectin", "faecal calprotectin",
    "c-reactive protein", "mucosal healing", "endoscopic remission", "histologic remission",
    "treat to target", "treat-to-target", "intestinal ultrasound", "biologic",
    "vedolizumab", "ustekinumab", "infliximab", "adalimumab", "golimumab", "tofacitinib",
    "upadacitinib", "filgotinib", "jak inhibitor", "ozanimod", "etrasimod",
    "maintenance of remission", "loss of response", "therapeutic drug monitoring",
    "colectomy", "pouchitis", "ileal pouch", "pregnancy", "colorectal cancer surveillance",
    "dysplasia surveillance", "extraintestinal manifestation",
)


@dataclass(frozen=True)
class StatePaths:
    """Filesystem layout *inside* an ``automation/uc-evidence-staging`` worktree.

    ``primary_checkout`` is the main checkout that *this specific worktree* is linked to (as
    resolved by ``gitio.resolve_state_root`` from the worktree's own git metadata) — worktree
    add/remove must run from there, not necessarily from ``config.REPO_ROOT`` (which is only
    guaranteed correct for the trusted-code location, not for an arbitrary worktree under test).
    """

    root: Path
    primary_checkout: Path | None = None

    @property
    def evidence_dir(self) -> Path:
        return self.root / EVIDENCE_SUBPATH

    @property
    def state_dir(self) -> Path:
        return self.evidence_dir / "state"

    @property
    def checkpoint_path(self) -> Path:
        return self.state_dir / "checkpoint.json"

    @property
    def known_good_path(self) -> Path:
        return self.state_dir / KNOWN_GOOD_FILENAME

    @property
    def lock_path(self) -> Path:
        return self.state_dir / "run.lock"

    @property
    def journal_path(self) -> Path:
        return self.evidence_dir / "journal" / "run-journal.ndjson"

    @property
    def retrieval_cache_dir(self) -> Path:
        return self.evidence_dir / "retrieval-cache"

    @property
    def topic_map_path(self) -> Path:
        return self.evidence_dir / "topic-priority-map.json"

    @property
    def sources_path(self) -> Path:
        return self.evidence_dir / "sources.json"

    @property
    def claims_path(self) -> Path:
        return self.evidence_dir / "candidate-claims.json"

    @property
    def coverage_map_path(self) -> Path:
        return self.evidence_dir / "question-coverage-map.json"

    @property
    def manifest_path(self) -> Path:
        return self.evidence_dir / "ingestion-manifest.json"

    @property
    def licensing_path(self) -> Path:
        return self.evidence_dir / "licensing-access-register.json"

    @property
    def qa_results_path(self) -> Path:
        return self.evidence_dir / "qa-results.json"

    @property
    def run_report_path(self) -> Path:
        return self.evidence_dir / "RUN-REPORT.md"

    @property
    def qa_report_path(self) -> Path:
        return self.evidence_dir / "QA-REPORT.md"

    @property
    def evidence_gaps_path(self) -> Path:
        return self.evidence_dir / "EVIDENCE-GAPS.md"

    @property
    def reviewer_workbook_path(self) -> Path:
        return self.evidence_dir / "reviewer-workbook.xlsx"

    # Explicit commit allowlist (relative to the worktree root). Nothing else is ever staged.
    COMMIT_ALLOWLIST = (
        "knowledge/uc-evidence-expansion/sources.json",
        "knowledge/uc-evidence-expansion/candidate-claims.json",
        "knowledge/uc-evidence-expansion/question-coverage-map.json",
        "knowledge/uc-evidence-expansion/ingestion-manifest.json",
        "knowledge/uc-evidence-expansion/licensing-access-register.json",
        "knowledge/uc-evidence-expansion/qa-results.json",
        "knowledge/uc-evidence-expansion/EVIDENCE-GAPS.md",
        "knowledge/uc-evidence-expansion/QA-REPORT.md",
        "knowledge/uc-evidence-expansion/RUN-REPORT.md",
        "knowledge/uc-evidence-expansion/reviewer-workbook.xlsx",
        "knowledge/uc-evidence-expansion/topic-priority-map.json",
        "knowledge/uc-evidence-expansion/state/checkpoint.json",
        "knowledge/uc-evidence-expansion/state/checkpoint.json.known-good",
        "knowledge/uc-evidence-expansion/journal/run-journal.ndjson",
    )
    # These are force-added because the repo .gitignore ignores them; still only ever inside a
    # staging worktree, never on main.
    COMMIT_FORCE_PATHS = frozenset(
        {
            "knowledge/uc-evidence-expansion/state/checkpoint.json",
            "knowledge/uc-evidence-expansion/state/checkpoint.json.known-good",
            "knowledge/uc-evidence-expansion/journal/run-journal.ndjson",
        }
    )
    # Never staged / committed under any circumstances.
    COMMIT_DENYLIST_SUBPATHS = (
        "knowledge/uc-evidence-expansion/state/run.lock",
        "knowledge/uc-evidence-expansion/retrieval-cache/",
        "knowledge/uc-evidence-expansion/source-files/",
        "uc_39_question_tree.json",
        ".uc_reddit_work/",
        "UC-REDDIT-DEMAND-REPORT.md",
        ".venv/",
        ".env",
    )


def assert_not_on_sys_path(path: Path) -> None:
    """Guard: the state root must never be importable."""
    resolved = str(path.resolve())
    for entry in sys.path:
        try:
            if entry and Path(entry).resolve() == Path(resolved):
                raise AssertionError(f"--state-root {resolved} is on sys.path; refusing to run")
        except (OSError, RuntimeError):
            continue


def assert_outside_trusted_tree(path: Path) -> None:
    resolved = path.resolve()
    if resolved == REPO_ROOT or AUTOMATION_DIR in resolved.parents or resolved == AUTOMATION_DIR:
        raise AssertionError(
            f"--state-root {resolved} overlaps the trusted-code tree ({AUTOMATION_DIR})"
        )
