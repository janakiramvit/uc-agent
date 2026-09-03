"""The Supabase evidence backend is dormant by default and cannot activate by accident."""

import pytest

from agent_core.evidence_backend import (
    FILE_BACKEND,
    SUPABASE_BACKEND,
    SupabaseBackendNotEnabled,
    get_evidence_backend,
    load_active_evidence_package,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("EVIDENCE_BACKEND", raising=False)
    monkeypatch.delenv("EVIDENCE_SUPABASE_ENABLED", raising=False)


def test_default_backend_is_file():
    assert get_evidence_backend() == FILE_BACKEND


def test_supabase_without_enable_flag_raises(monkeypatch):
    monkeypatch.setenv("EVIDENCE_BACKEND", "supabase")
    with pytest.raises(SupabaseBackendNotEnabled):
        get_evidence_backend()


def test_supabase_with_enable_flag_selects_supabase(monkeypatch):
    monkeypatch.setenv("EVIDENCE_BACKEND", "supabase")
    monkeypatch.setenv("EVIDENCE_SUPABASE_ENABLED", "1")
    assert get_evidence_backend() == SUPABASE_BACKEND


def test_unknown_backend_rejected(monkeypatch):
    monkeypatch.setenv("EVIDENCE_BACKEND", "sqlite")
    with pytest.raises(ValueError):
        get_evidence_backend()


def test_file_path_still_loads_the_49_claim_package():
    pkg = load_active_evidence_package()
    assert len(pkg.all_claims) == 49
    assert {c["claimId"] for c in pkg.uc_eligible_claims} == {
        "CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}
