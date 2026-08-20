"""LLM provider selection must be driven only by environment variables,
and must fail loudly (never fabricate a response) when neither provider
is configured."""

import pytest

from agent_core.llm_synthesizer import LLMNotConfiguredError, synthesize_with_llm


def test_raises_when_no_provider_key_present(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMNotConfiguredError):
        synthesize_with_llm("Is fibre good for UC?", [])


def test_prefers_anthropic_when_both_keys_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    from agent_core.llm_synthesizer import _resolve_chat_model

    _, provider, _ = _resolve_chat_model()
    assert provider == "anthropic"


def test_falls_back_to_openai_when_only_openai_key_present(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    from agent_core.llm_synthesizer import _resolve_chat_model

    _, provider, _ = _resolve_chat_model()
    assert provider == "openai"
