"""End-to-end runner with fake providers in a real sandbox git worktree: outputs, state, alerts, exit codes."""

from __future__ import annotations

import functools
import json

import pytest

from tests.test_discover import FakeProvider, make_record
from uc_evidence_discovery import artifact as artifact_mod
from uc_evidence_discovery import checkpoint as checkpoint_mod
from uc_evidence_discovery import config, discover, provider_state
from uc_evidence_discovery.providers.base import EvidenceType, ProviderUnavailable
from uc_evidence_discovery.runner import main


@pytest.fixture(autouse=True)
def _sandbox(monkeypatch, tmp_path):
    monkeypatch.setenv("UC_DISCOVERY_TODAY", "2026-11-10")
    monkeypatch.setattr(artifact_mod, "build", functools.partial(artifact_mod.build, out_dir=tmp_path / "artifact"))
    yield


def _providers(extra_error=False):
    trial = make_record(3, "clinicaltrials", doi="", pmid="", nctId="NCT07000003", evidenceType="ongoing_trial",
                        journal="ClinicalTrials.gov registry", canonicalUrl="https://clinicaltrials.gov/study/NCT07000003",
                        title="Treat to target ulcerative colitis trial")
    return [FakeProvider("europepmc", [make_record(1, "europepmc")]),
            FakeProvider("pubmed", error=ProviderUnavailable("pubmed: HTTP 503")) if extra_error
            else FakeProvider("pubmed", [make_record(1, "pubmed"), make_record(2, "pubmed")]),
            FakeProvider("clinicaltrials", [trial], evidence_type=EvidenceType.ONGOING_TRIAL)]


def _run(monkeypatch, state_root, providers, *extra):
    monkeypatch.setattr(discover, "build_providers", lambda: providers)
    return main(["--state-root", str(state_root), "--no-push", *extra])


def test_run_writes_funnel_daily_report_state_and_staged_sources(monkeypatch, state_root, capsys):
    rc = _run(monkeypatch, state_root, _providers())
    assert rc == 0
    paths = config.StatePaths(root=state_root)
    funnel = json.loads(paths.provider_funnel_path.read_text())
    assert set(funnel["providers"]) == {"europepmc", "pubmed", "clinicaltrials"}
    assert funnel["totals"]["accepted"] == 3 - 0 and funnel["providers"]["pubmed"]["duplicates"] == 1   # 1 cross-provider dup
    report = paths.daily_report_path.read_text()
    assert "Provider health" in report and "Europe PMC".lower() in report.lower() or "EUROPEPMC" in report
    assert all(name.upper() in report or name in report for name in ("europepmc", "pubmed", "clinicaltrials"))
    state = provider_state.load(paths)
    assert all(state["providers"][n]["lastSuccessfulCutoff"] == "2026-11-10" for n in ("europepmc", "pubmed", "clinicaltrials"))
    sources = json.loads(paths.sources_path.read_text())["sources"]
    assert {s["evidenceType"] for s in sources} == {"published_study", "ongoing_trial"}
    claims = json.loads(paths.claims_path.read_text())["claims"]
    trial_ids = {s["sourceId"] for s in sources if s["evidenceType"] == "ongoing_trial"}
    assert claims and not any(c["sourceId"] in trial_ids for c in claims)
    assert not checkpoint_mod.validate(json.loads(paths.checkpoint_path.read_text()))
    qa = json.loads(paths.qa_results_path.read_text())
    assert qa["summary"]["failed"] == 0, [c for c in qa["checks"] if c["result"] == "FAIL"]


def test_provider_failure_makes_the_job_fail_visibly_but_still_stages_the_other_providers(monkeypatch, state_root, capsys):
    rc = _run(monkeypatch, state_root, _providers(extra_error=True))
    out = capsys.readouterr()
    assert rc == 1                                                       # not silent
    assert "::error title=UC discovery PROVIDER_FAILURE (pubmed)" in out.out
    paths = config.StatePaths(root=state_root)
    assert json.loads(paths.provider_funnel_path.read_text())["providers"]["pubmed"]["status"] == "failed"
    assert len(json.loads(paths.sources_path.read_text())["sources"]) == 2          # europepmc + trial still staged
    assert provider_state.load(paths)["providers"]["pubmed"]["lastSuccessfulCutoff"] is None


def test_redacted_artifact_carries_provider_health_counts_but_no_text(monkeypatch, state_root, tmp_path):
    _run(monkeypatch, state_root, _providers())
    (art,) = (tmp_path / "artifact").glob("redacted-run-*.json")
    doc = json.loads(art.read_text())
    assert set(doc["providerHealth"]) == {"europepmc", "pubmed", "clinicaltrials"}
    assert doc["providerHealth"]["europepmc"]["accepted"] == 1
    blob = json.dumps(doc).lower()
    assert "fecal calprotectin" not in blob and "randomised" not in blob


def test_never_promotes_or_approves_and_targets_the_staging_branch_only(monkeypatch, state_root):
    _run(monkeypatch, state_root, _providers())
    paths = config.StatePaths(root=state_root)
    manifest = json.loads(paths.manifest_path.read_text())
    assert manifest["productionPromotion"] == "blocked_by_design" and manifest["targetIndex"].startswith("NONE")
    for s in json.loads(paths.sources_path.read_text())["sources"]:
        assert not s["humanReviewStatus"] and not s["clinicalReviewStatus"]
    assert config.STAGING_BRANCH == "automation/uc-evidence-staging"
