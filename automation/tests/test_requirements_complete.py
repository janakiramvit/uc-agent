"""Every third-party package imported anywhere under automation/ must be pinned in
automation/requirements.txt — an environment built from that file alone must be able to run
everything here (runtime, tools/, tests/)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from uc_evidence_discovery import config

# stdlib modules used across the codebase (kept short and explicit rather than relying on
# sys.stdlib_module_names, which is 3.10+ only and still misses some private helpers we touch).
_STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()
_STDLIB |= {
    "__future__", "argparse", "dataclasses", "datetime", "hashlib", "json", "os", "re",
    "secrets", "socket", "subprocess", "sys", "time", "typing", "urllib", "ast", "random",
}

_MODULE_TO_REQUIREMENT = {
    "requests": "requests",
    "jsonschema": "jsonschema",
    "openpyxl": "openpyxl",
    "yaml": "PyYAML",
    "pytest": "pytest",
}


def _top_level_imports(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text("utf-8"), filename=str(py_file))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


def _first_party_packages() -> set[str]:
    return {"uc_evidence_discovery", "tools", "tests", "automation"}


def test_every_third_party_import_is_pinned():
    requirements_text = (config.AUTOMATION_DIR / "requirements.txt").read_text("utf-8")
    pinned = {line.split("==")[0] for line in requirements_text.splitlines()
              if line and not line.startswith("#")}

    first_party = _first_party_packages()
    missing: set[tuple[str, str]] = set()
    for py_file in config.AUTOMATION_DIR.rglob("*.py"):
        if ".venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        for name in _top_level_imports(py_file):
            if name in _STDLIB or name in first_party or name in ("conftest",):
                continue
            requirement = _MODULE_TO_REQUIREMENT.get(name, name)
            if requirement not in pinned:
                missing.add((str(py_file.relative_to(config.AUTOMATION_DIR)), name))
    assert missing == set(), f"unpinned third-party imports: {sorted(missing)}"


def test_requirements_file_pins_every_dependency_exactly():
    text = (config.AUTOMATION_DIR / "requirements.txt").read_text("utf-8")
    lines = [l for l in text.splitlines() if l and not l.startswith("#")]
    assert lines, "requirements.txt should not be empty"
    for line in lines:
        assert "==" in line, f"{line!r} is not exactly pinned"
