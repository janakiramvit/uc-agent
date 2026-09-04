from __future__ import annotations

import requests

from uc_evidence_discovery.apis.http import DisallowedHost, Http, NetworkDisabled, ResponseTooLarge, host_allowed


class _FakeResponse:
    def __init__(self, status_code=200, json_body=None, text_body="", headers=None):
        self.status_code = status_code
        self._json = json_body if json_body is not None else {}
        self.text = text_body
        self.headers = headers or {}
        self._content = (text_body or "").encode("utf-8")
        self._content_consumed = False

    def json(self):
        return self._json

    def iter_content(self, chunk_size):
        yield self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class _FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.headers = {}

    def get(self, url, params=None, timeout=None, stream=None, allow_redirects=None):
        resp = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return resp


def test_disallowed_host_rejected_without_any_request():
    session = _FakeSession([_FakeResponse(200, {"ok": True})])
    http = Http(enabled=True, session=session, sleep=lambda _s: None)
    try:
        http.get_json("https://evil.example.com/x")
        assert False
    except DisallowedHost:
        pass
    assert session.calls == 0


def test_no_network_mode_never_touches_the_session():
    session = _FakeSession([_FakeResponse(200, {"ok": True})])
    http = Http(enabled=False, session=None, sleep=lambda _s: None)
    try:
        http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
        assert False
    except NetworkDisabled:
        pass
    assert session.calls == 0


def test_retries_on_5xx_then_succeeds():
    session = _FakeSession([_FakeResponse(503), _FakeResponse(503), _FakeResponse(200, {"ok": 1})])
    slept = []
    http = Http(enabled=True, session=session, retries=2, backoff_base=0.001, sleep=slept.append)
    data = http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
    assert data == {"ok": 1}
    assert session.calls == 3
    assert len(slept) >= 2


def test_gives_up_after_retry_budget_exhausted():
    session = _FakeSession([_FakeResponse(503)] * 10)
    http = Http(enabled=True, session=session, retries=2, backoff_base=0.001, sleep=lambda _s: None)
    try:
        http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
        assert False
    except requests.HTTPError:
        pass
    assert session.calls == 3  # 1 initial + 2 retries


def test_response_too_large_is_rejected_by_declared_content_length():
    resp = _FakeResponse(200, headers={"Content-Length": "999999999"})
    session = _FakeSession([resp])
    http = Http(enabled=True, session=session, max_bytes=1000, sleep=lambda _s: None)
    try:
        http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
        assert False
    except ResponseTooLarge:
        pass


def test_response_too_large_is_rejected_by_streamed_size_even_without_content_length():
    resp = _FakeResponse(200, text_body="x" * 2000)
    session = _FakeSession([resp])
    http = Http(enabled=True, session=session, max_bytes=100, sleep=lambda _s: None)
    try:
        http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
        assert False
    except ResponseTooLarge:
        pass


def test_rate_limiting_sleeps_between_consecutive_calls_to_the_same_host():
    session = _FakeSession([_FakeResponse(200, {}), _FakeResponse(200, {})])
    slept = []
    http = Http(enabled=True, session=session, min_interval=5.0, sleep=slept.append)
    http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
    http.get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search")
    assert any(s > 0 for s in slept)


def test_host_allowed_helper():
    assert host_allowed("https://www.ebi.ac.uk/x") is True
    assert host_allowed("https://reddit.com/x") is False
    assert host_allowed("https://api.openai.com/x") is False
    assert host_allowed("https://unknown-host.example/x") is False
