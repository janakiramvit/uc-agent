"""LLM provider selection for the synthesis category must be driven only
by environment variables (SYNTHESIS_PROVIDER / SYNTHESIS_MODEL, routed
through agent_core.model_router), and must fail loudly (never fabricate
a response) when no usable provider key is configured."""

import pytest

from agent_core.llm_synthesizer import LLMNotConfiguredError, synthesize_with_llm


def test_raises_when_no_provider_key_present(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMNotConfiguredError):
        synthesize_with_llm("Is fibre good for UC?", [])


def test_defaults_to_anthropic_when_synthesis_provider_unset(monkeypatch):
    monkeypatch.delenv("SYNTHESIS_PROVIDER", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    from agent_core.llm_synthesizer import _resolve_chat_model

    _, provider, _ = _resolve_chat_model()
    assert provider == "anthropic"


def test_synthesis_provider_env_var_selects_openai(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    from agent_core.llm_synthesizer import _resolve_chat_model

    _, provider, _ = _resolve_chat_model()
    assert provider == "openai"


def test_synthesis_provider_openai_without_key_raises(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMNotConfiguredError):
        synthesize_with_llm("Is fibre good for UC?", [])


def test_synthesis_model_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_PROVIDER", "anthropic")
    monkeypatch.setenv("SYNTHESIS_MODEL", "claude-custom-test-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    from agent_core.llm_synthesizer import _resolve_chat_model

    _, _, model = _resolve_chat_model()
    assert model == "claude-custom-test-model"
