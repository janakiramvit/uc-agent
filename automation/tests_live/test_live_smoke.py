"""Controlled LIVE smoke test, one per provider. Deselected by default (they use the network and the polite 1 s/host rate limit):

    cd automation && python -m pytest tests_live -m live -o addopts= -v

Each test makes a small, bounded number of requests through the real guarded client (robots.txt honoured, no PDFs) and records
nothing. Wide windows are used so that a healthy provider is expected to return something; a day with genuinely no new
records must not fail the smoke test."""

from __future__ import annotations

import datetime as dt

import pytest

from uc_evidence_discovery.apis import europepmc as epmc_api
from uc_evidence_discovery.apis.http import Http
from uc_evidence_discovery.providers import guidelines as gl
from uc_evidence_discovery.providers.base import Window
from uc_evidence_discovery.providers.clinicaltrials import ClinicalTrialsProvider
from uc_evidence_discovery.providers.europepmc import EuropePmcProvider
from uc_evidence_discovery.providers.pubmed import PubMedProvider
from uc_evidence_discovery.providers.robots import RobotsPolicy

pytestmark = pytest.mark.live

TODAY = dt.date.today()
MONTH = Window(TODAY - dt.timedelta(days=30), TODAY)
TWO_YEARS = Window(TODAY - dt.timedelta(days=730), TODAY)


@pytest.fixture(scope="module")
def http():
    return Http(enabled=True)


def test_europepmc_old_syntax_returns_zero_and_corrected_syntax_returns_records(http):
    old = epmc_api.search(http, '"ulcerative colitis" AND (2021:2026[pub_year])', page_size=1)
    assert old["hitCount"] == 0                                           # the documented root cause
    out = EuropePmcProvider().search_window(http, MONTH, max_pages=1)
    assert out.hit_count > 0 and out.records
    assert all(r["evidenceType"] in ("published_study", "clinical_guideline") for r in out.records)


def test_pubmed_corrected_query_returns_records_with_abstracts(http):
    out = PubMedProvider().search_window(http, Window(TODAY - dt.timedelta(days=7), TODAY), max_pages=1)
    assert out.hit_count > 0 and out.records
    assert any(len(r["abstractText"]) > 100 for r in out.records)


def test_clinicaltrials_returns_trials_labelled_as_trials(http):
    out = ClinicalTrialsProvider().search_window(http, MONTH, max_pages=1)
    assert out.hit_count > 0 and out.records
    assert all(r["evidenceType"] in ("ongoing_trial", "completed_trial_record") and r["nctId"].startswith("NCT")
               for r in out.records)


def _provider(name):
    return next(p for p in gl.build_guideline_providers() if p.name == name)


def test_aga_site_is_refused_by_robots_and_the_pubmed_index_still_finds_guidelines(http):
    out = _provider("aga").search_window(http, TWO_YEARS, max_pages=1)
    assert out.access_limits and "gastro.org" in out.access_limits[0]          # legitimate access limitation, reported
    assert out.records and all(r["evidenceType"] == "clinical_guideline" for r in out.records)


def test_acg_listing_contains_the_public_ulcerative_colitis_guideline(http):
    acg = _provider("acg")
    items = acg._site(acg, http, RobotsPolicy(http), TWO_YEARS, type("O", (), {"searches": 0, "notes": []})())
    uc = [i for i in items if "Ulcerative Colitis" in i["title"]]
    assert uc and uc[0]["doi"].startswith("10.14309/ajg.")


def test_ecco_site_blocks_automated_clients_and_is_reported_as_an_access_limitation(http):
    out = _provider("ecco").search_window(http, TWO_YEARS, max_pages=1)
    assert out.access_limits and "ecco-ibd.eu" in out.access_limits[0]


def test_nice_ng130_is_readable_and_parsed(http):
    nice = _provider("nice")
    items = nice._site(nice, http, RobotsPolicy(http), TWO_YEARS, type("O", (), {"searches": 0, "notes": []})())
    assert any(i["title"] == "Ulcerative colitis: management" for i in items)


def test_bsg_sitemap_lists_the_ibd_in_adults_guideline(http):
    bsg = _provider("bsg")
    items = bsg._site(bsg, http, RobotsPolicy(http), TWO_YEARS, type("O", (), {"searches": 0, "notes": []})())
    assert any("ibd-in-adults" in i["canonicalUrl"] for i in items)
