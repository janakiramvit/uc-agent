from __future__ import annotations

import json

import pytest

from uc_evidence_discovery import config, provider_state
from uc_evidence_discovery.errors import SafeStop


@pytest.fixture()
def paths(tmp_path):
    return config.StatePaths(root=tmp_path)


def test_no_files_means_a_clean_first_run_state_with_the_discovery_floor(paths):
    st = provider_state.load(paths)
    assert st["providers"] == {} and st["discoveryStartDate"] == config.EARLIEST_DISCOVERY_DATE


def test_save_validates_writes_atomically_and_keeps_a_known_good_copy(paths):
    st = provider_state.empty_state()
    provider_state.provider(st, "europepmc")["lastSuccessfulCutoff"] = "2026-11-10"
    provider_state.save(paths, st)
    assert paths.provider_state_path.exists() and paths.provider_state_known_good_path.exists()
    assert provider_state.load(paths)["providers"]["europepmc"]["lastSuccessfulCutoff"] == "2026-11-10"
    assert not list(paths.state_dir.glob("*.tmp.*"))


def test_corrupt_primary_recovers_from_known_good(paths):
    st = provider_state.empty_state()
    provider_state.provider(st, "pubmed")["lastSuccessfulCutoff"] = "2026-11-11"
    provider_state.save(paths, st)
    paths.provider_state_path.write_text("{not json", encoding="utf-8")
    assert provider_state.load(paths)["providers"]["pubmed"]["lastSuccessfulCutoff"] == "2026-11-11"


def test_present_but_invalid_state_is_a_safe_stop_never_a_silent_reset(paths):
    paths.state_dir.mkdir(parents=True)
    paths.provider_state_path.write_text(json.dumps({"schemaVersion": "wrong", "providers": {}}), encoding="utf-8")
    with pytest.raises(SafeStop):
        provider_state.load(paths)            # resetting would re-open a backfill window


def test_invalid_document_is_refused_on_save(paths):
    st = provider_state.empty_state()
    st["providers"]["x"] = {"lastSuccessfulCutoff": 5}
    with pytest.raises(SafeStop):
        provider_state.save(paths, st)
    assert not paths.provider_state_path.exists()


def test_state_is_bounded(paths):
    st = provider_state.empty_state()
    p = provider_state.provider(st, "europepmc")
    p["rejectedKeys"] = [f"k{i}" for i in range(provider_state.MAX_REJECTED_KEYS + 50)]
    st["runHistory"] = [{"date": "2026-11-10", "runId": f"r{i}"} for i in range(provider_state.MAX_HISTORY + 10)]
    provider_state.save(paths, st)
    again = provider_state.load(paths)
    assert len(again["providers"]["europepmc"]["rejectedKeys"]) == provider_state.MAX_REJECTED_KEYS
    assert len(again["runHistory"]) == provider_state.MAX_HISTORY
