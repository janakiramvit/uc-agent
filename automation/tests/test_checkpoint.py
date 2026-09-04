from __future__ import annotations

import json

import pytest

from uc_evidence_discovery import checkpoint as checkpoint_mod
from uc_evidence_discovery import config

from .conftest import MINIMAL_CHECKPOINT


def test_valid_primary_loads_directly(state_paths):
    res = checkpoint_mod.load(state_paths)
    assert res.source == "primary"
    assert not res.recovered
    assert res.doc["runId"] == MINIMAL_CHECKPOINT["runId"]


def test_invalid_primary_recovers_from_known_good(state_paths):
    state_paths.checkpoint_path.write_text("{ this is not json", encoding="utf-8")
    res = checkpoint_mod.load(state_paths)
    assert res.source == "known_good"
    assert res.recovered is True
    assert res.doc["runId"] == MINIMAL_CHECKPOINT["runId"]


def test_both_invalid_raises_safe_stop_before_research(state_paths):
    state_paths.checkpoint_path.write_text("not json", encoding="utf-8")
    state_paths.known_good_path.write_text("also not json", encoding="utf-8")
    with pytest.raises(checkpoint_mod.SafeStop):
        checkpoint_mod.load(state_paths)


def test_schema_invalid_document_also_triggers_recovery(state_paths):
    broken = dict(MINIMAL_CHECKPOINT)
    broken.pop("stopReason")  # required field missing
    state_paths.checkpoint_path.write_text(json.dumps(broken), encoding="utf-8")
    res = checkpoint_mod.load(state_paths)
    assert res.recovered


def test_atomic_write_then_revalidate_updates_known_good(state_paths):
    doc = dict(MINIMAL_CHECKPOINT)
    doc["stopReason"] = "advanced by test"
    doc["counters"] = dict(doc["counters"], recordsScreened=99)
    checkpoint_mod.save(state_paths, doc)

    on_disk = json.loads(state_paths.checkpoint_path.read_text("utf-8"))
    assert on_disk["counters"]["recordsScreened"] == 99
    known_good = json.loads(state_paths.known_good_path.read_text("utf-8"))
    assert known_good["counters"]["recordsScreened"] == 99
    assert not checkpoint_mod.validate(on_disk)


def test_save_refuses_to_write_an_invalid_document(state_paths):
    before = state_paths.checkpoint_path.read_text("utf-8")
    bad = dict(MINIMAL_CHECKPOINT)
    del bad["runStatus"]
    with pytest.raises(checkpoint_mod.SafeStop):
        checkpoint_mod.save(state_paths, bad)
    assert state_paths.checkpoint_path.read_text("utf-8") == before  # nothing written


def test_no_temp_files_left_behind(state_paths):
    doc = dict(MINIMAL_CHECKPOINT)
    doc["stopReason"] = "x"
    checkpoint_mod.save(state_paths, doc)
    leftovers = list(state_paths.state_dir.glob("*.tmp.*"))
    assert leftovers == []


def test_prompt_context_cannot_override_a_newer_checkpoint(state_paths):
    """The checkpoint says T-UCX-03/S-UCX-03-a/cursor 0 (matches the prompt) — advance it, and
    confirm a load reports the difference rather than letting any prompt-supplied value win."""
    doc = dict(MINIMAL_CHECKPOINT)
    doc["nextRecommendedOperation"] = dict(
        doc["nextRecommendedOperation"],
        topicId="T-UCX-04", searchId="S-UCX-04-a", cursor=7,
        firstNewSourceId="SRC-050", firstNewClaimId="CLM-200",
    )
    state_paths.checkpoint_path.write_text(json.dumps(doc), encoding="utf-8")
    res = checkpoint_mod.load(state_paths)
    assert res.doc["nextRecommendedOperation"]["topicId"] == "T-UCX-04"
    assert res.prompt_difference is not None
    assert res.prompt_difference["promptExpected"] == config.PROMPT_EXPECTATIONS
    assert res.prompt_difference["checkpointHas"]["topicId"] == "T-UCX-04"
    assert res.prompt_difference["resolution"].startswith("checkpoint is authoritative")


def test_matching_checkpoint_reports_no_difference(state_paths):
    res = checkpoint_mod.load(state_paths)
    assert res.prompt_difference is None  # MINIMAL_CHECKPOINT already matches PROMPT_EXPECTATIONS


@pytest.mark.parametrize("schema_path", [config.SCHEMA_V1_0_0, config.SCHEMA_V1_1_0])
def test_current_real_checkpoint_files_validate_against_both_schemas(schema_path):
    """Backward-compat evidence for the v1.0.0 -> v1.1.0 migration. Skipped where the real,
    git-ignored local checkpoint files are not present on this machine/CI checkout."""
    real_state = config.REPO_ROOT / config.EVIDENCE_SUBPATH / "state"
    primary = real_state / "checkpoint.json"
    known_good = real_state / config.KNOWN_GOOD_FILENAME
    if not (primary.exists() and known_good.exists()):
        pytest.skip("real checkpoint.json / checkpoint.json.known-good not present locally")
    for p in (primary, known_good):
        doc = json.loads(p.read_text("utf-8"))
        errors = checkpoint_mod.validate(doc, schema_path=schema_path)
        assert errors == [], f"{p} failed against {schema_path.name}: {errors}"


def test_only_one_known_good_filename_exists_in_the_repo():
    real_state = config.REPO_ROOT / config.EVIDENCE_SUBPATH / "state"
    assert config.KNOWN_GOOD_FILENAME == "checkpoint.json.known-good"
    assert not (real_state / "checkpoint.known-good.json").exists()
