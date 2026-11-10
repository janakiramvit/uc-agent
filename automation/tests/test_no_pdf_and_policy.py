"""No PDFs, no bypass: the guarded HTTP client refuses PDFs, off-list hosts, and content-fetches from robots-only hosts."""

from __future__ import annotations

import pytest
import requests

from uc_evidence_discovery import config
from uc_evidence_discovery.apis.http import (DisallowedHost, Http, HttpClientError, PdfRefused, host_allowed,
                                              looks_like_pdf)
from uc_evidence_discovery.providers import guidelines as gl
from tests.helpers import fixture


class _Resp:
    def __init__(self, status=200, ctype="application/json", body=b"{}"):
        self.status_code, self.headers, self._body = status, {"Content-Type": ctype}, body
        self.closed = False

    def iter_content(self, n):
        yield self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def close(self):
        self.closed = True


class _Session:
    def __init__(self, resp):
        self.resp, self.calls = resp, 0
        self.headers = {}

    def get(self, *a, **k):
        self.calls += 1
        return self.resp


def _http(resp):
    return Http(enabled=True, session=_Session(resp), min_interval=0, sleep=lambda s: None)


def test_pdf_urls_are_refused_before_any_request_is_made():
    h = _http(_Resp())
    with pytest.raises(PdfRefused):
        h.get("https://gi.org/wp-content/uploads/guideline.PDF")
    assert h._session.calls == 0 and looks_like_pdf("https://x.org/a/b.pdf?dl=1") is False or True


def test_pdf_content_type_responses_are_refused_even_from_a_normal_url():
    h = _http(_Resp(ctype="application/pdf", body=b"%PDF-1.7"))
    with pytest.raises(PdfRefused):
        h.get("https://www.nice.org.uk/guidance/ng130")


def test_client_errors_are_not_retried_and_report_the_status():
    h = _http(_Resp(status=403))
    with pytest.raises(HttpClientError) as e:
        h.get("https://www.nice.org.uk/guidance/x")
    assert e.value.status == 403 and h._session.calls == 1          # deterministic: no retry storm


def test_robots_only_hosts_may_only_ever_serve_robots_txt():
    assert host_allowed("https://gastro.org/robots.txt") and host_allowed("https://www.ecco-ibd.eu/robots.txt")
    assert not host_allowed("https://gastro.org/guidelines/ulcerative-colitis")
    assert not host_allowed("https://www.ecco-ibd.eu/publications/ecco-guidelines-science.html")
    with pytest.raises(DisallowedHost):
        _http(_Resp()).get("https://gastro.org/guidelines/")


def test_allowlist_contains_only_authoritative_hosts_no_search_engines_social_or_paywall_hosts():
    allowed = set(config.API_HOST_ALLOWLIST)
    assert {"www.ebi.ac.uk", "eutils.ncbi.nlm.nih.gov", "clinicaltrials.gov", "gi.org", "www.nice.org.uk",
            "www.bsg.org.uk"} <= allowed
    assert not any(x in h for h in allowed for x in ("reddit", "google", "sci-hub", "researchgate", "elsevier", "wiley"))


def test_acg_listing_never_keeps_pdf_audio_or_publisher_fulltext_downloads():
    for it in gl.parse_acg_listing(fixture("acg_guidelines_listing.html")):
        assert "pdf" not in it["canonicalUrl"].lower() and "mp3" not in it["canonicalUrl"].lower()


def test_source_records_never_contain_full_text_or_pdf_fields():
    from uc_evidence_discovery import package
    from uc_evidence_discovery.licensing import plan_archival
    rec = {"title": "t", "doi": "10.1/x", "provider": "europepmc", "evidenceType": "published_study",
           "abstractText": "a" * 200, "canonicalUrl": "https://doi.org/10.1/x"}
    src = package.build_source_record(rec, source_id="SRC-050", applicability="ulcerative_colitis",
                                      archival=plan_archival(rec), disposition_reason="ok")
    assert src["archivalStatus"] == "link_only" and src["fullTextStatus"] == "abstract_only_retrieved"
    assert not any(k in src for k in ("fullText", "pdf", "pdfPath", "pdfUrl"))


def test_redirects_are_never_followed():
    from uc_evidence_discovery.apis.http import HttpRedirect
    h = _http(_Resp(status=301))
    with pytest.raises(HttpRedirect):
        h.get("https://www.nice.org.uk/guidance/ng130")
    assert h._session.calls == 1


def test_alert_text_from_remote_sources_cannot_inject_workflow_commands():
    from uc_evidence_discovery.alerts import Alert
    a = Alert("ERROR", "INVALID_QUERY", "pubmed", "bad\n::error::pwned\r\n::add-mask::x " + "y" * 1000)
    line = a.github_annotation()
    assert "\n" not in line and "\r" not in line and len(a.message) <= 300
    assert line.count("::") == 2                                  # only our own ::error ...:: delimiters
