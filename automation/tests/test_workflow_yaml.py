"""Static checks on the workflow YAML (no GitHub, no network)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from uc_evidence_discovery import config

WORKFLOW = config.REPO_ROOT / ".github" / "workflows" / "uc-daily-evidence-discovery.yml"


def _load() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_file_exists_and_parses():
    assert WORKFLOW.is_file()
    doc = _load()
    assert doc["name"]


def test_schedule_and_manual_trigger_present():
    doc = _load()
    on = doc.get("on") or doc.get(True)  # PyYAML may parse bare `on:` as boolean True
    assert "schedule" in on
    assert on["schedule"] == [{"cron": "0 14 * * *"}]
    assert "workflow_dispatch" in on


def test_hard_timeout_is_ten_minutes():
    doc = _load()
    job = doc["jobs"]["discover"]
    assert job["timeout-minutes"] == 10


def test_concurrency_queues_not_cancels():
    doc = _load()
    conc = doc["concurrency"]
    assert conc["group"] == "uc-daily-evidence-discovery"
    assert conc["cancel-in-progress"] is False


def test_permissions_are_minimal():
    doc = _load()
    perms = doc["permissions"]
    assert perms == {"contents": "write", "actions": "read"}


def test_python_3_13():
    doc = _load()
    steps = doc["jobs"]["discover"]["steps"]
    setup = next(s for s in steps if "setup-python" in s.get("uses", ""))
    assert setup["with"]["python-version"] == "3.13"


def test_third_party_actions_are_sha_pinned():
    doc = _load()
    steps = doc["jobs"]["discover"]["steps"]
    used = [s["uses"] for s in steps if "uses" in s]
    assert used, "workflow should use at least one action"
    for u in used:
        name, ref = u.split("@", 1)
        assert re.fullmatch(r"[0-9a-f]{40}", ref), f"{name} is not pinned to a 40-char commit SHA: {ref}"


def test_run_url_is_constructed_not_assumed_builtin():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_RUN_URL" in text
    assert "github.server_url" in text and "github.repository" in text and "github.run_id" in text
    # must not merely reference a bare ${{ github.run_url }} (no such context exists)
    assert "github.run_url" not in text.lower().replace("github_run_url", "")


def test_worktree_step_targets_staging_branch_not_a_checkout_switch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git worktree add" in text
    assert "automation/uc-evidence-staging" in text
    assert re.search(r"git\s+checkout\s+automation/uc-evidence-staging", text) is None
    assert re.search(r"git\s+switch\s+automation/uc-evidence-staging", text) is None


def test_python_step_passes_state_root():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--state-root" in text


def test_artifact_step_uploads_only_redacted_paths():
    doc = _load()
    steps = doc["jobs"]["discover"]["steps"]
    upload = next(s for s in steps if "upload-artifact" in s.get("uses", ""))
    path_spec = upload["with"]["path"]
    for line in path_spec.strip().splitlines():
        line = line.strip()
        assert line.startswith("automation/artifact/redacted-run-"), line
    assert upload["with"]["if-no-files-found"] == "error"


def test_no_step_pushes_to_main():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "refs/heads/main" not in text
    assert re.search(r"push\s+origin\s+(HEAD:)?main\b", text) is None


def test_worktree_removal_has_safety_net_step():
    doc = _load()
    steps = doc["jobs"]["discover"]["steps"]
    cleanup = [s for s in steps if "worktree remove" in s.get("run", "")]
    assert cleanup, "expected a worktree-removal step"
    assert cleanup[0].get("if") == "always()"
    assert "git worktree remove --force" in cleanup[0]["run"]
    assert "git worktree prune" in cleanup[0]["run"]
