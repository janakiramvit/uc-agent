from __future__ import annotations

from pathlib import Path

from uc_evidence_discovery import config


def test_no_openai_or_anthropic_call_site_or_import_anywhere():
    """Prose mentions (docstrings explaining the boundary, denylist entries, negative-test
    fixture URLs) are fine and expected; an actual import or call-site is not."""
    banned_patterns = (
        "import openai", "from openai", "import anthropic", "from anthropic",
        "openai.chatcompletion", "openai.completion", "anthropic.anthropic",
        "client.messages.create", "openai.api_key", "anthropic_api_key",
    )
    this_file = Path(__file__)
    hits = []
    for p in config.AUTOMATION_DIR.rglob("*.py"):
        if "__pycache__" in p.parts or ".venv" in p.parts or p == this_file:
            continue
        text = p.read_text("utf-8", errors="ignore").lower()
        for b in banned_patterns:
            if b in text:
                hits.append((str(p), b))
    assert hits == []


def test_config_py_has_no_hardcoded_api_key_or_credential_for_a_paid_provider():
    config_text = (config.PKG_DIR / "config.py").read_text("utf-8").lower()
    for bad in ("api_key =", "api_key=", "sk-ant-", "sk-proj-", "bearer "):
        assert bad not in config_text


def test_host_allowlist_has_no_paid_or_llm_provider():
    for host in config.API_HOST_ALLOWLIST:
        assert "openai" not in host
        assert "anthropic" not in host


def test_deny_list_blocks_paid_providers_defensively():
    assert any("openai" in d for d in config.DENY_HOST_SUBSTRINGS)
    assert any("anthropic" in d for d in config.DENY_HOST_SUBSTRINGS)


def test_http_client_refuses_a_disallowed_host():
    from uc_evidence_discovery.apis.http import DisallowedHost, Http

    http = Http(enabled=True)
    try:
        http.get("https://api.openai.com/v1/models")
        assert False, "expected DisallowedHost"
    except DisallowedHost:
        pass
