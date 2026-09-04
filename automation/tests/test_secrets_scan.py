from __future__ import annotations

import json
import re

from uc_evidence_discovery import config, qa
from uc_evidence_discovery.runner import main

from .conftest import MINIMAL_CHECKPOINT

_SECRET_PATTERNS = (
    r"(?i)ghp_[A-Za-z0-9]{20,}", r"(?i)gho_[A-Za-z0-9]{20,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"(?i)postgres(?:ql)?://\S+",
    r"(?i)aws_secret", r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}",
)


def _scan(text: str) -> list[str]:
    hits = []
    for pat in _SECRET_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return hits


def test_automation_source_tree_has_no_hardcoded_secret():
    # artifact.py and qa.py legitimately embed these patterns *as detection data* (the
    # forbidden-substring / secret-regex definitions themselves); everywhere else is banned.
    pattern_definition_files = {
        config.PKG_DIR / "artifact.py",
        config.PKG_DIR / "qa.py",
        config.AUTOMATION_DIR / "tests" / "test_secrets_scan.py",
    }
    for py_file in config.AUTOMATION_DIR.rglob("*.py"):
        if ".venv" in py_file.parts or "__pycache__" in py_file.parts or py_file in pattern_definition_files:
            continue
        hits = _scan(py_file.read_text("utf-8", errors="ignore"))
        assert hits == [], f"{py_file}: {hits}"


def test_qa_module_flags_secret_patterns_in_generated_outputs(state_paths):
    state_paths.sources_path.write_text(json.dumps({"sources": [
        {"sourceId": "SRC-1", "title": "leaky", "doi": "10.1/x",
         "connectionString": "postgres://user:pass@host/db"}
    ]}), encoding="utf-8")
    state_paths.claims_path.write_text(json.dumps({"claims": []}), encoding="utf-8")
    state_paths.manifest_path.write_text(json.dumps({"targetIndex": "NONE"}), encoding="utf-8")
    state_paths.licensing_path.write_text(json.dumps({"entries": []}), encoding="utf-8")
    state_paths.coverage_map_path.write_text(json.dumps({}), encoding="utf-8")
    state_paths.run_report_path.write_text("no secrets here", encoding="utf-8")

    summary = qa.run_checks(
        state_paths, run_id="uc-exp-000000000001", checkpoint_doc=MINIMAL_CHECKPOINT,
        counters={"elapsedResearchSeconds": 1, "queriesConsumed": 0, "recordsScreened": 0,
                  "sourcesAccepted": 0, "pdfsDownloaded": 0, "claimsExtracted": 0},
    )
    secret_check = next(c for c in summary["checks"] if c["id"] == "QA-13")
    assert secret_check["result"] == "FAIL"


def test_journal_and_checkpoint_written_by_a_dry_run_contain_no_secret(state_root, state_paths):
    rc = main(["--state-root", str(state_root), "--dry-run", "--no-network"])
    assert rc == 0
    journal_text = state_paths.journal_path.read_text("utf-8")
    checkpoint_text = state_paths.checkpoint_path.read_text("utf-8")
    assert _scan(journal_text) == []
    assert _scan(checkpoint_text) == []
