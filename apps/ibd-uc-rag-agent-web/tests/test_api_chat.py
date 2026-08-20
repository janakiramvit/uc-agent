"""End-to-end HTTP test of the actual Vercel entrypoint (api/chat.py),
run over a real local socket -- not just the underlying graph functions
-- so the request parsing, rate limiting, and error-response wiring are
exercised exactly as Vercel would invoke them."""

import json
import threading
from http.client import HTTPConnection
from http.server import HTTPServer

import pytest

from agent_core.rate_limit import reset_rate_limits


@pytest.fixture
def server():
    import chat  # api/chat.py, imported as top-level module via sys.path

    reset_rate_limits()
    httpd = HTTPServer(("127.0.0.1", 0), chat.handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()
    thread.join()
    reset_rate_limits()


def _post(port, payload):
    conn = HTTPConnection("127.0.0.1", port, timeout=30)
    body = json.dumps(payload).encode("utf-8")
    conn.request("POST", "/api/chat", body=body, headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    return resp.status, data


def test_get_health_check(server):
    conn = HTTPConnection("127.0.0.1", server.server_address[1], timeout=10)
    conn.request("GET", "/api/chat")
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    assert resp.status == 200
    assert data == {"status": "ok"}


def test_post_missing_query_is_400(server):
    status, data = _post(server.server_address[1], {})
    assert status == 400
    assert data["error"] == "bad_request"


def test_post_valid_query_without_llm_key_returns_honest_status(server, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status, data = _post(server.server_address[1], {"query": "Is fibre good for UC?"})
    assert status == 200
    # Must be an honest "we have evidence but can't synthesize" state,
    # never a fabricated "answered".
    assert data["status"] == "llm_unavailable"
    assert "visitedNodes" in data


def test_post_query_too_long_is_400(server):
    status, data = _post(server.server_address[1], {"query": "x" * 3000})
    assert status == 400
    assert data["error"] == "query_too_long"


def test_rate_limit_kicks_in_after_burst(server):
    port = server.server_address[1]
    statuses = [ _post(port, {"query": "Is fibre good for UC?"})[0] for _ in range(11) ]
    assert 429 in statuses
