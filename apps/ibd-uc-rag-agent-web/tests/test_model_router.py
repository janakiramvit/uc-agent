"""Provider/model routing must be driven purely by environment variables
(PLANNER_/REASONING_/SYNTHESIS_/CRITIC_ PROVIDER+MODEL), with safe
defaults, and call_structured/call_text must NEVER raise -- every
failure mode comes back as a status string."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from agent_core.model_router import (
    ModelNotConfiguredError,
    call_structured,
    call_text,
    resolve_provider_and_model,
)


class _Schema(BaseModel):
    value: str


def test_defaults_to_anthropic_for_every_category(monkeypatch):
    for var in ("PLANNER_PROVIDER", "REASONING_PROVIDER", "SYNTHESIS_PROVIDER", "CRITIC_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    for category in ("planner", "reasoning", "synthesis", "critic"):
        provider, _ = resolve_provider_and_model(category)
        assert provider == "anthropic"


def test_env_var_overrides_provider_per_category(monkeypatch):
    monkeypatch.setenv("REASONING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    provider, model = resolve_provider_and_model("reasoning")
    assert provider == "openai"
    assert model  # has a sensible default


def test_env_var_overrides_model_name(monkeypatch):
    monkeypatch.setenv("CRITIC_PROVIDER", "anthropic")
    monkeypatch.setenv("CRITIC_MODEL", "claude-custom-critic-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    _, model = resolve_provider_and_model("critic")
    assert model == "claude-custom-critic-model"


def test_unsupported_provider_raises(monkeypatch):
    monkeypatch.setenv("PLANNER_PROVIDER", "not-a-real-provider")
    with pytest.raises(ModelNotConfiguredError):
        resolve_provider_and_model("planner")


def test_missing_key_for_selected_provider_raises(monkeypatch):
    monkeypatch.setenv("SYNTHESIS_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ModelNotConfiguredError):
        resolve_provider_and_model("synthesis")


def test_call_structured_never_raises_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result, status, provider, model = call_structured("planner", _Schema, "sys", "user")
    assert result is None
    assert status.startswith("not_configured")
    assert provider is None


def test_call_structured_never_raises_on_provider_exception(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    with patch("agent_core.model_router.get_chat_model") as mock_get:
        mock_chat = MagicMock()
        mock_chat.with_structured_output.side_effect = RuntimeError("simulated network failure")
        mock_get.return_value = (mock_chat, "anthropic", "claude-test")
        result, status, provider, model = call_structured("planner", _Schema, "sys", "user")
    assert result is None
    assert status.startswith("provider_error")
    assert provider == "anthropic"


def test_call_structured_flags_invalid_output_shape(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    with patch("agent_core.model_router.get_chat_model") as mock_get:
        mock_chat = MagicMock()
        structured = MagicMock()
        structured.invoke.return_value = {"not": "a schema instance"}  # wrong type
        mock_chat.with_structured_output.return_value = structured
        mock_get.return_value = (mock_chat, "anthropic", "claude-test")
        result, status, provider, model = call_structured("planner", _Schema, "sys", "user")
    assert result is None
    assert status.startswith("invalid_output")


def test_call_structured_ok_path_returns_validated_schema(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    with patch("agent_core.model_router.get_chat_model") as mock_get:
        mock_chat = MagicMock()
        structured = MagicMock()
        structured.invoke.return_value = _Schema(value="ok")
        mock_chat.with_structured_output.return_value = structured
        mock_get.return_value = (mock_chat, "anthropic", "claude-test")
        result, status, provider, model = call_structured("planner", _Schema, "sys", "user")
    assert status == "ok"
    assert isinstance(result, _Schema)
    assert result.value == "ok"


def test_call_text_never_raises_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    text, status, provider, model = call_text("synthesis", "sys", "user")
    assert text is None
    assert status.startswith("not_configured")
