"""Shared fixtures.

``automation/`` (and only ``automation/``) is put on ``sys.path`` so tests import the real
package the same way the ``main`` checkout does. The sandbox fixtures build a throwaway git
repo with a ``main`` branch (trusted code) and an ``automation/uc-evidence-staging`` branch
(mutable state), then attach the staging branch as a real ``git worktree`` — exactly the shape
the production workflow uses.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

AUTOMATION_DIR = Path(__file__).resolve().parent.parent
if str(AUTOMATION_DIR) not in sys.path:
    sys.path.insert(0, str(AUTOMATION_DIR))

from uc_evidence_discovery import config  # noqa: E402


def git(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), check=check, capture_output=True, text=True)


MINIMAL_CHECKPOINT: dict = {
    "schemaVersion": config.SCHEMA_VERSION_1_1_0,
    "runId": "uc-exp-aaaaaaaaaaaa",
    "runStartTime": "2026-09-01T00:00:00Z",
    "runFinishTime": "2026-09-01T00:10:00Z",
    "lastCheckpointTime": "2026-09-01T00:10:00Z",
    "runStatus": "partially_completed",
    "currentTopicId": "T-UCX-03",
    "currentSearchStrategyId": "S-UCX-03-a",
    "currentSearchQuery": "acute severe ulcerative colitis Truelove Witts criteria",
    "currentApiCursor": 0,
    "lastProcessedRecord": None,
    "latestPublicationTimestampEncountered": "2023-03-01T00:00:00Z",
    "completedSearches": [],
    "pendingSearches": [
        {"searchId": "S-UCX-03-a", "topicId": "T-UCX-03",
         "service": "europepmc", "query": "acute severe ulcerative colitis", "cursor": 0},
    ],
    "processedSourceIdentifiers": {
        "doi": ["10.1053/j.gastro.2022.12.007"],
        "pubmedId": ["36822736"],
        "canonicalUrl": ["https://doi.org/10.1053/j.gastro.2022.12.007"],
        "checksum": [],
        "normalizedTitle": ["aga clinical practice guideline"],
    },
    "acceptedRecords": [],
    "rejectedRecords": [],
    "deferredRecords": [],
    "failedItems": [],
    "retryCounts": {},
    "counters": {
        "elapsedResearchSeconds": 249.0,
        "queriesConsumed": 5,
        "recordsScreened": 30,
        "sourcesAccepted": 3,
        "pdfsDownloaded": 0,
        "claimsExtracted": 13,
    },
    "stopReason": "sandbox fixture checkpoint",
    "nextRecommendedOperation": {
        "description": "Continue topic T-UCX-03 from cursor 0.",
        "topicId": "T-UCX-03",
        "searchId": "S-UCX-03-a",
        "cursor": 0,
        "firstNewSourceId": "SRC-035",
        "firstNewClaimId": "CLM-128",
    },
}


def _seed_evidence_dir(root: Path, checkpoint: dict) -> None:
    evidence = root / config.EVIDENCE_SUBPATH
    (evidence / "state").mkdir(parents=True, exist_ok=True)
    (evidence / "journal").mkdir(parents=True, exist_ok=True)
    (evidence / "state" / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
    (evidence / "state" / config.KNOWN_GOOD_FILENAME).write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
    (evidence / "sources.json").write_text(
        json.dumps({"schemaVersion": config.SCHEMA_VERSION_1_1_0, "sources": []}, indent=2), encoding="utf-8")
    (evidence / "candidate-claims.json").write_text(
        json.dumps({"schemaVersion": config.SCHEMA_VERSION_1_1_0, "claims": []}, indent=2), encoding="utf-8")
    (evidence / "topic-priority-map.json").write_text(
        json.dumps({"schemaVersion": "uc-evidence-expansion-topic-priority-map-1.0.0", "nodes": []}, indent=2),
        encoding="utf-8",
    )


@pytest.fixture()
def bare_remote(tmp_path) -> Path:
    """A bare 'origin' with a main branch and a seeded automation/uc-evidence-staging branch."""
    origin_src = tmp_path / "origin_src"
    origin_src.mkdir()
    git(["init", "-b", "main"], origin_src)
    git(["config", "user.email", "test@example.com"], origin_src)
    git(["config", "user.name", "Test"], origin_src)
    (origin_src / "README.md").write_text("sandbox main\n")
    git(["add", "README.md"], origin_src)
    git(["commit", "-m", "init main"], origin_src)

    git(["checkout", "-b", config.STAGING_BRANCH], origin_src)
    _seed_evidence_dir(origin_src, MINIMAL_CHECKPOINT)
    git(["add", "-A"], origin_src)
    git(["commit", "-m", "seed staging"], origin_src)
    git(["checkout", "main"], origin_src)

    bare = tmp_path / "origin.git"
    git(["clone", "--bare", str(origin_src), str(bare)], tmp_path)
    return bare


@pytest.fixture()
def main_checkout(tmp_path, bare_remote) -> Path:
    repo = tmp_path / "main_checkout"
    git(["clone", str(bare_remote), str(repo)], tmp_path)
    git(["config", "user.email", "test@example.com"], repo)
    git(["config", "user.name", "Test"], repo)
    git(["checkout", "main"], repo)
    return repo


@pytest.fixture()
def state_root(tmp_path, main_checkout) -> Path:
    """A real linked git worktree of automation/uc-evidence-staging, attached to main_checkout."""
    git(["fetch", "origin",
        f"+refs/heads/{config.STAGING_BRANCH}:{config.STAGING_REMOTE_REF}"], main_checkout)
    target = tmp_path / "uc-state"
    git(["worktree", "add", "--detach", str(target), config.STAGING_REMOTE_REF], main_checkout)
    return target


@pytest.fixture()
def state_paths(state_root):
    return config.StatePaths(root=state_root)
