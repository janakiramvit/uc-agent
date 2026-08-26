"""Secrets must never appear in logs, traces, responses, or anywhere a
client could see them. Sets a distinctive fake key value via env vars,
runs real request paths, and asserts that exact value never appears
anywhere in the resulting state/trace/HTTP response -- only the env VAR
NAME should ever be mentioned in error messages, never the value."""

import json

FAKE_SECRET_VALUE = "sk-ant-THIS_EXACT_STRING_MUST_NEVER_LEAK_9f8e7d6c5b4a"


def _assert_secret_absent(obj) -> None:
    serialized = json.dumps(obj, default=str)
    assert FAKE_SECRET_VALUE not in serialized


def test_model_router_error_messages_never_include_the_key_value(monkeypatch):
    monkeypatch.setenv("PLANNER_PROVIDER", "not-a-real-provider")
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_SECRET_VALUE)
    from agent_core.model_router import call_structured
    from pydantic import BaseModel

    class _S(BaseModel):
        v: str

    result, status, provider, model = call_structured("planner", _S, "sys", "user")
    assert FAKE_SECRET_VALUE not in status
    assert result is None


def test_full_graph_state_never_contains_the_key_value(graph, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_SECRET_VALUE)
    from agent_core.graph_v2 import run_graph_v2

    result = run_graph_v2(graph, "Is fibre good or bad for my ulcerative colitis?")
    _assert_secret_absent(result)


def test_full_graph_state_never_leaks_key_even_on_provider_error(graph, monkeypatch):
    from unittest.mock import patch

    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_SECRET_VALUE)
    from agent_core.graph_v2 import run_graph_v2

    # Simulate a provider call that (mis-)behaves and echoes back its
    # inputs in an exception message -- the graph's own trace/state must
    # still never contain the raw key, since agent_core code never puts
    # the key value into any exception message or state field itself.
    with patch(
        "agent_core.llm_synthesizer.get_chat_model",
        side_effect=RuntimeError(f"connection using key ending in ...{FAKE_SECRET_VALUE[-6:]}"),
    ):
        result = run_graph_v2(graph, "Is fibre good or bad for my ulcerative colitis?")
    _assert_secret_absent(result)


def test_api_chat_http_response_never_contains_key_value(monkeypatch):
    import threading
    from http.client import HTTPConnection
    from http.server import HTTPServer

    from agent_core.rate_limit import reset_rate_limits

    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_SECRET_VALUE)
    reset_rate_limits()

    import chat  # api/chat.py

    httpd = HTTPServer(("127.0.0.1", 0), chat.handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=30)
        body = json.dumps({"query": "Is fibre good for UC?"}).encode("utf-8")
        conn.request("POST", "/api/chat", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
    finally:
        httpd.shutdown()
        thread.join()
        reset_rate_limits()

    assert FAKE_SECRET_VALUE not in raw.decode("utf-8")
