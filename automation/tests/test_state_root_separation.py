"""Proves the code/state separation invariants: the runner always executes trusted code from
the ``main`` checkout, ``--state-root`` is a pure data directory that is never imported from
and never lands on ``sys.path``, and the worktree is always cleaned up.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from uc_evidence_discovery import checkpoint as checkpoint_mod
from uc_evidence_discovery import config, gitio
from uc_evidence_discovery.errors import UntrustedStateRoot
from uc_evidence_discovery.runner import main

from .conftest import MINIMAL_CHECKPOINT, git


def test_trusted_modules_load_from_main_checkout_not_state_root(state_root):
    import uc_evidence_discovery

    real_file = Path(uc_evidence_discovery.__file__).resolve()
    assert real_file.is_relative_to(config.PKG_DIR)
    assert not real_file.is_relative_to(state_root)


def test_state_root_never_added_to_sys_path(state_root):
    before = set(sys.path)
    paths = gitio.resolve_state_root(str(state_root))
    assert str(paths.root) not in sys.path
    assert set(sys.path) == before


def test_hostile_state_root_python_is_never_imported(tmp_path, state_root):
    # plant a poisoned package + sitecustomize inside the state root
    (state_root / "config.py").write_text("SOFT_DEADLINE_SECONDS = 999999\nPOISONED = True\n")
    (state_root / "sitecustomize.py").write_text(
        f"open(r'{tmp_path}/poisoned.marker', 'w').write('x')\n"
    )
    pkg = state_root / "uc_evidence_discovery"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("POISONED = True\n")

    rc = main(["--state-root", str(state_root), "--validate-checkpoint"])
    assert rc == 0

    import uc_evidence_discovery as real_pkg
    from uc_evidence_discovery import config as real_config

    assert not hasattr(real_pkg, "POISONED")
    assert real_config.SOFT_DEADLINE_SECONDS == 450
    assert not (tmp_path / "poisoned.marker").exists()
    assert not any(str(state_root) in str(p) for p in sys.path)


def test_state_io_resolves_only_inside_state_root(state_root):
    paths = gitio.resolve_state_root(str(state_root))
    loaded = checkpoint_mod.load(paths)
    assert loaded.doc["runId"] == MINIMAL_CHECKPOINT["runId"]
    assert paths.checkpoint_path.is_relative_to(state_root)
    assert paths.journal_path.is_relative_to(state_root)
    assert paths.lock_path.is_relative_to(state_root)
    # the schema used to validate comes from the trusted main checkout, not state-root
    assert config.SCHEMA_V1_1_0.is_relative_to(config.REPO_ROOT)
    assert not config.SCHEMA_V1_1_0.is_relative_to(state_root)


def test_refuses_a_worktree_on_the_wrong_branch(main_checkout, tmp_path):
    target = tmp_path / "not-staging"
    git(["worktree", "add", "--detach", str(target), "main"], main_checkout)
    with pytest.raises(UntrustedStateRoot):
        gitio.resolve_state_root(str(target))


def test_refuses_a_plain_directory_that_is_not_a_worktree(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(UntrustedStateRoot):
        gitio.resolve_state_root(str(plain))


def test_dry_run_intentionally_keeps_the_worktree_for_inspection(state_root):
    rc = main(["--state-root", str(state_root), "--dry-run", "--no-network"])
    assert rc == 0
    assert state_root.exists()


def test_worktree_removed_after_a_real_run(main_checkout, state_root):
    rc = main(["--state-root", str(state_root), "--no-network"])  # not dry-run: real cleanup
    assert rc == 0
    listing = git(["worktree", "list"], main_checkout).stdout
    assert str(state_root) not in listing
    assert not state_root.exists()


def test_worktree_removed_after_handled_failure(main_checkout, state_root):
    # corrupt both checkpoint copies so checkpoint.load() raises SafeStop deep inside main();
    # main() must still remove the worktree in its finally block.
    cp_path = config.StatePaths(root=state_root).checkpoint_path
    kg_path = config.StatePaths(root=state_root).known_good_path
    cp_path.write_text("{not json", encoding="utf-8")
    kg_path.write_text("{not json", encoding="utf-8")

    rc = main(["--state-root", str(state_root), "--no-network"])
    assert rc == 0  # safe stop, not a crash
    listing = git(["worktree", "list"], main_checkout).stdout
    assert str(state_root) not in listing
