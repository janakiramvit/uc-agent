"""Providers against RECORDED API responses (tests/fixtures/*, captured live 2026-11-10 by record_fixtures.py)."""

from __future__ import annotations

import datetime as dt

import pytest

from tests.helpers import FakeHttp, fixture, fixture_json, route_robots, url_has
from uc_evidence_discovery.apis import pubmed as pubmed_api
from uc_evidence_discovery.apis.http import HttpClientError
from uc_evidence_discovery.providers import guidelines as gl
from uc_evidence_discovery.providers.base import AccessLimited, InvalidQuery, ProviderUnavailable, Window
from uc_evidence_discovery.providers.clinicaltrials import ClinicalTrialsProvider
from uc_evidence_discovery.providers.europepmc import EuropePmcProvider
from uc_evidence_discovery.providers.pubmed import PubMedProvider
from uc_evidence_discovery.providers.robots import RobotsPolicy

W = Window(dt.date(2026, 11, 10), dt.date(2026, 11, 10))      # one day: providers walk windows day by day


# ------------------------------------------------------------------ Europe PMC
def test_europepmc_corrected_query_returns_records_where_the_old_one_returned_zero():
    old = fixture_json("europepmc_zero_pubmed_syntax.json")
    assert old["hitCount"] == 0                                  # the recorded root cause
    http = FakeHttp([(url_has("europepmc", "/search"), lambda u, p: fixture_json("europepmc_window.json"))])
    out = EuropePmcProvider().search_window(http, W, max_pages=1)
    assert out.hit_count == 190 and len(out.records) >= 4
    sent = http.calls[0][1]["query"]
    assert "FIRST_IDATE:[2026-11-10 TO 2026-11-10]" in sent and "pub_year" not in sent


def test_europepmc_records_are_tagged_and_flagged_for_full_text_verification():
    http = FakeHttp([(url_has("europepmc"), lambda u, p: fixture_json("europepmc_window.json"))])
    for r in EuropePmcProvider().search_window(http, W, max_pages=1).records:
        assert r["provider"] == "europepmc" and r["evidenceType"] == "published_study"
        assert r["requiresFullTextVerification"] is True
        assert r["accessStatus"] in ("open_access_abstract_only", "paywalled_metadata_and_abstract_only")


def test_europepmc_paywalled_paper_keeps_only_metadata_abstract_doi_and_link():
    http = FakeHttp([(url_has("europepmc"), lambda u, p: fixture_json("europepmc_window.json"))])
    rec = EuropePmcProvider().search_window(http, W, max_pages=1).records[0]
    assert rec["accessStatus"] == "paywalled_metadata_and_abstract_only"
    assert rec["canonicalUrl"].startswith("https://") and (rec["doi"] or rec["pmid"])
    assert not any(k in rec for k in ("fullText", "pdfUrl", "pdf"))


def test_europepmc_truncation_is_reported_when_pages_are_capped():
    http = FakeHttp([(url_has("europepmc"), lambda u, p: fixture_json("europepmc_window.json"))])
    out = EuropePmcProvider().search_window(http, W, max_pages=1)
    assert out.truncated is True                                   # 190 hits, only 4 fetched


def test_europepmc_http_400_is_an_invalid_query_and_5xx_is_a_provider_failure():
    with pytest.raises(InvalidQuery):
        EuropePmcProvider().search_window(FakeHttp([(url_has("europepmc"), lambda u, p: HttpClientError(400, "h"))]), W, max_pages=1)
    with pytest.raises(ProviderUnavailable):
        EuropePmcProvider().search_window(FakeHttp([(url_has("europepmc"), lambda u, p: HttpClientError(503, "h"))]), W, max_pages=1)


# ------------------------------------------------------------------ PubMed
def _pubmed_http():
    return FakeHttp([
        (url_has("esearch.fcgi"), lambda u, p: _esearch_json(p)),
        (url_has("efetch.fcgi"), lambda u, p: fixture("pubmed_efetch.xml")),
    ])


def _esearch_json(params):
    d = fixture_json("pubmed_esearch.json")
    d["esearchresult"]["count"] = "3"
    return d


def test_pubmed_corrected_query_returns_records_with_abstracts_and_dois():
    http = _pubmed_http()
    out = PubMedProvider().search_window(http, W, max_pages=1)
    assert len(out.records) >= 3 and all(len(r["abstractText"]) > 100 for r in out.records)
    assert all(r["doi"] for r in out.records)
    esearch_params = next(p for u, p in http.calls if "esearch" in u)
    assert esearch_params["datetype"] == "edat" and esearch_params["mindate"] == "2026/11/10"


def test_pubmed_xml_parse_extracts_publication_types_and_ids():
    recs = pubmed_api.parse_pubmed_xml(fixture("pubmed_efetch_guideline.xml"))
    assert recs and all("Practice Guideline" in r["publicationTypes"] for r in recs)
    assert all(r["pmid"] and r["title"] for r in recs)


def test_pubmed_silently_reinterpreted_query_is_detected_from_the_translation():
    def bad(u, p):
        d = fixture_json("pubmed_esearch_garbage_query.json")
        return d
    http = FakeHttp([(url_has("esearch.fcgi"), bad)])
    with pytest.raises(InvalidQuery):
        PubMedProvider().search_window(http, W, max_pages=1)


def test_pubmed_xml_parser_rejects_entity_expansion():
    bomb = ('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;&a;&a;">]><PubmedArticleSet>&b;'
            "</PubmedArticleSet>")
    with pytest.raises(Exception):
        pubmed_api.parse_pubmed_xml(bomb)


# ------------------------------------------------------------------ ClinicalTrials.gov
def _ct_http():
    return FakeHttp([(url_has("clinicaltrials.gov/api/v2/studies"), lambda u, p: fixture_json("clinicaltrials_window.json"))])


def test_clinicaltrials_records_are_labelled_as_trials_and_never_as_studies():
    out = ClinicalTrialsProvider().search_window(_ct_http(), W, max_pages=1)
    assert len(out.records) >= 4 and out.hit_count == 43
    types = {r["overallStatus"]: r["evidenceType"] for r in out.records}
    assert types["COMPLETED"] == "completed_trial_record" and types["RECRUITING"] == "ongoing_trial"
    assert all(r["evidenceType"] in ("ongoing_trial", "completed_trial_record") for r in out.records)
    assert all(r["noClaimsReason"] and r["requiresFullTextVerification"] is False for r in out.records)
    assert all(r["nctId"].startswith("NCT") for r in out.records)


def test_clinicaltrials_uses_its_own_filter_syntax_in_the_request():
    http = _ct_http()
    ClinicalTrialsProvider().search_window(http, W, max_pages=1)
    assert http.calls[0][1]["filter.advanced"] == "AREA[LastUpdatePostDate]RANGE[2026-11-10,2026-11-10]"


def test_clinicaltrials_bad_range_is_an_empty_200_which_only_the_canary_can_catch():
    assert fixture_json("clinicaltrials_bad_range.json") == {"studies": []}


# ------------------------------------------------------------------ robots.txt
def test_robots_aga_disallows_generic_bots_so_the_site_is_never_fetched():
    http = FakeHttp([route_robots("gastro.org", fixture("robots_gastro.org.txt"))])
    with pytest.raises(AccessLimited) as e:
        RobotsPolicy(http).require("https://gastro.org/guidelines/")
    assert "disallows" in str(e.value)
    assert [u for u, _ in http.calls] == ["https://gastro.org/robots.txt"]       # only robots.txt was requested


def test_robots_403_is_treated_as_not_permitted_ecco():
    http = FakeHttp([route_robots("www.ecco-ibd.eu", status=403)])
    with pytest.raises(AccessLimited) as e:
        RobotsPolicy(http).require("https://www.ecco-ibd.eu/publications/ecco-guidelines-science.html")
    assert "403" in str(e.value)


def test_robots_404_means_no_restriction_and_5xx_means_cannot_tell():
    RobotsPolicy(FakeHttp([route_robots("a.org", status=404)])).require("https://a.org/x")
    with pytest.raises(ProviderUnavailable):
        RobotsPolicy(FakeHttp([(url_has("b.org"), lambda u, p: RuntimeError("boom"))])).require("https://b.org/x")


def test_robots_crawl_delay_is_honoured():
    http = FakeHttp([route_robots("www.nice.org.uk", fixture("robots_www.nice.org.uk.txt"))])
    RobotsPolicy(http).require("https://www.nice.org.uk/guidance/ng130")
    assert http.host_intervals["www.nice.org.uk"] >= 1.0


# ------------------------------------------------------------------ guideline connectors
def _acg():
    return next(p for p in gl.build_guideline_providers() if p.name == "acg")


def _acg_http():
    return FakeHttp([route_robots("gi.org", fixture("robots_gi.org.txt")),
                     (url_has("gi.org/guidelines"), lambda u, p: fixture("acg_guidelines_listing.html")),
                     (url_has("esearch.fcgi"), lambda u, p: {"esearchresult": {"count": "0", "idlist": [], "querytranslation":
                                                             '"Am J Gastroenterol"[Journal] ulcerative colitis [Date - Entry]',
                                                             "errorlist": {}, "warninglist": {}}})])


def test_acg_finds_the_known_public_ulcerative_colitis_guideline_with_its_doi():
    items = gl.parse_acg_listing(fixture("acg_guidelines_listing.html"))
    uc = [i for i in items if "Ulcerative Colitis" in i["title"]]
    assert uc and uc[0]["doi"] == "10.14309/ajg.0000000000003463" and uc[0]["publicationDate"] == "2025-06-03"


def test_acg_listing_discards_pdf_and_podcast_links():
    for i in gl.parse_acg_listing(fixture("acg_guidelines_listing.html")):
        assert not i["canonicalUrl"].lower().endswith((".pdf", ".mp3"))
        assert "webfiles.gi.org" not in i["canonicalUrl"]


def test_acg_first_run_baselines_the_listing_without_backfilling_old_guidelines():
    p = _acg()
    out = p.search_window(_acg_http(), Window(dt.date(2026, 11, 10), dt.date(2026, 11, 10)), max_pages=1)
    assert out.records == []                                     # nothing in the window, nothing backfilled
    assert p.listing_total >= 1 and p.listing_seen                 # but the listing WAS read (baseline for next time)
    assert any("Ulcerative" in u or "doi.org" in u for u in p.listing_seen)


def test_acg_a_new_url_older_than_the_discovery_start_date_is_never_backfilled():
    p = _acg()
    p.known_listing_urls = {"https://www.doi.org/10.14309/ajg.0000000000003463"}
    out = p.search_window(_acg_http(), Window(dt.date(2026, 11, 10), dt.date(2026, 11, 10)), max_pages=1)
    assert out.records == []              # the other cards are new URLs but dated 2025: before the floor


def test_acg_a_new_listing_item_after_the_baseline_is_reported(monkeypatch):
    from uc_evidence_discovery import config
    monkeypatch.setattr(config, "EARLIEST_DISCOVERY_DATE", "2025-01-01")      # allow the 2025 fixture cards for this test
    p = _acg()
    p.known_listing_urls = {"https://www.doi.org/10.14309/ajg.0000000000003463"}     # baseline lacks the other cards
    out = p.search_window(_acg_http(), Window(dt.date(2026, 11, 10), dt.date(2026, 11, 10)), max_pages=1)
    assert out.records and all(r["evidenceType"] == "clinical_guideline" and r["society"] for r in out.records)
    assert all(r["requiresFullTextVerification"] for r in out.records)


def test_bsg_sitemap_yields_the_ibd_adult_guideline_and_ignores_service_improvement_pages():
    items = gl.parse_bsg_sitemap(fixture("bsg_sitemap.xml"))
    urls = [i["canonicalUrl"] for i in items]
    assert any(u.endswith("bsg-guidelines-on-ibd-in-adults-2025") for u in urls)
    assert not any("(sss)" in u for u in urls)
    assert all(i["titleSource"] == "url_slug" for i in items)


def test_nice_page_parser_reads_title_and_date_for_ng130():
    rec = gl.parse_nice_page(fixture("nice_ng130.html"), "https://www.nice.org.uk/guidance/ng130")
    assert rec["title"] == "Ulcerative colitis: management" and rec["publicationDate"] == "2019-05-03"


def test_aga_site_is_never_fetched_but_the_pubmed_index_channel_still_runs():
    aga = next(p for p in gl.build_guideline_providers() if p.name == "aga")
    http = FakeHttp([route_robots("gastro.org", fixture("robots_gastro.org.txt")),
                     (url_has("esearch.fcgi"), lambda u, p: {"esearchresult": {
                         "count": "1", "idlist": ["42928006"], "errorlist": {}, "warninglist": {},
                         "querytranslation": '"Gastroenterology"[Journal] AND ulcerative colitis [Date - Entry]'}}),
                     (url_has("efetch.fcgi"), lambda u, p: fixture("pubmed_efetch_guideline.xml"))])
    out = aga.search_window(http, W, max_pages=1)
    assert out.access_limits and "gastro.org" in out.access_limits[0]
    assert out.records and all(r["provider"] == "aga" and r["channel"] == "pubmed_index" for r in out.records)
    assert not any("gastro.org/guidelines" in u for u, _ in http.calls)
    assert all(r["evidenceType"] == "clinical_guideline" for r in out.records)


def test_a_site_only_body_that_blocks_us_raises_access_limited_not_a_failure():
    nice = next(p for p in gl.build_guideline_providers() if p.name == "nice")
    with pytest.raises(AccessLimited):
        nice.search_window(FakeHttp([route_robots("www.nice.org.uk", "User-agent: *\nDisallow: /\n")]), W, max_pages=1)


# ------------------------------------------------------------------ review hardening
def test_day_by_day_walk_makes_one_search_per_day_and_reports_covered_through():
    http = FakeHttp([(url_has("europepmc"), lambda u, p: {"hitCount": 2, "resultList": {"result": [
        {"id": "1", "source": "MED", "title": "a"}, {"id": "2", "source": "MED", "title": "b"}]}, "nextCursorMark": "*"})])
    out = EuropePmcProvider().search_window(http, Window(dt.date(2026, 11, 10), dt.date(2026, 11, 12)), max_pages=1)
    sent = [p["query"] for u, p in http.calls]
    assert len(sent) == 3 and "FIRST_IDATE:[2026-11-11 TO 2026-11-11]" in sent[1]
    assert out.covered_through == dt.date(2026, 11, 12) and not out.truncated


def test_a_too_busy_day_stops_the_walk_and_earlier_days_still_count():
    def resp(u, p):
        day = p["query"].split("FIRST_IDATE:[")[1][:10]
        return {"hitCount": 5000 if day == "2026-11-12" else 1, "resultList": {"result": [{"id": "1", "source": "MED", "title": "x"}]},
                "nextCursorMark": "*"}
    out = EuropePmcProvider().search_window(FakeHttp([(url_has("europepmc"), resp)]),
                                            Window(dt.date(2026, 11, 10), dt.date(2026, 11, 14)), max_pages=1)
    assert out.truncated and out.covered_through == dt.date(2026, 11, 11)


def test_pubmed_no_items_found_is_a_normal_empty_result_not_an_invalid_query():
    http = FakeHttp([(url_has("esearch.fcgi"), lambda u, p: {"esearchresult": {
        "count": "0", "idlist": [], "errorlist": None, "warninglist": {"phrasesignored": [], "quotedphrasesnotfound": [],
                                                                      "outputmessages": ["No items found."]},
        "querytranslation": '("ulcerative colitis"[Title/Abstract]) AND 2026/11/10[Date - Entry]'}})])
    out = PubMedProvider().search_window(http, W, max_pages=1)
    assert out.hit_count == 0 and out.records == []


def test_malformed_provider_payload_becomes_a_provider_failure_not_a_crash():
    http = FakeHttp([(url_has("esearch.fcgi"), lambda u, p: {"esearchresult": {"count": "1", "idlist": ["1"], "errorlist": {},
                      "warninglist": {}, "querytranslation": "ulcerative colitis [Date - Entry]"}}),
                     (url_has("efetch.fcgi"), lambda u, p: "<html>Service unavailable</html>")])
    with pytest.raises(ProviderUnavailable):
        PubMedProvider().search_window(http, W, max_pages=1)


def test_robots_redirect_is_not_followed_and_means_not_permitted():
    from uc_evidence_discovery.apis.http import HttpRedirect
    http = FakeHttp([(lambda u, p: u.endswith("/robots.txt"), lambda u, p: HttpRedirect(301, "x.org"))])
    with pytest.raises(AccessLimited) as e:
        RobotsPolicy(http).require("https://x.org/a")
    assert "redirected" in str(e.value)


def test_robots_crawl_delay_over_budget_is_not_permitted_instead_of_sleeping_for_a_day():
    http = FakeHttp([route_robots("x.org", "User-agent: *\nCrawl-delay: 86400\n")])
    with pytest.raises(AccessLimited) as e:
        RobotsPolicy(http).require("https://x.org/a")
    assert "Crawl-delay" in str(e.value)


def test_robots_wildcards_longest_match_and_allow_override_follow_rfc_9309():
    robots = "User-agent: *\nDisallow: /*?rul\nDisallow: /private/\nAllow: /private/public/\nDisallow: /*.pdf$\n"
    def ok(path):
        try:
            RobotsPolicy(FakeHttp([route_robots("x.org", robots)])).require("https://x.org" + path)
            return True
        except AccessLimited:
            return False
    assert ok("/guidelines/") and not ok("/guidelines?rul=1") and not ok("/private/a")
    assert ok("/private/public/a") and not ok("/g/a.pdf") and ok("/g/a.pdf.html")


def test_robots_group_for_our_agent_overrides_star():
    robots = "User-agent: *\nDisallow: /\n\nUser-agent: uc-agent-evidence-discovery\nAllow: /\n"
    RobotsPolicy(FakeHttp([route_robots("x.org", robots)])).require("https://x.org/anything")


def test_robots_hostile_patterns_are_bounded_and_never_match():
    robots = "User-agent: *\nDisallow: /" + "*a" * 20 + "\nDisallow: /" + "x" * 300 + "\n"
    RobotsPolicy(FakeHttp([route_robots("x.org", robots)])).require("https://x.org/" + "a" * 40)
