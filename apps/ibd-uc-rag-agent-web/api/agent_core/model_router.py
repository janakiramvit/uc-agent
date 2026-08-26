"""Central model routing for every LLM-powered node in graph_v2.

Provider and model are resolved PURELY from environment variables, never
hard-coded (only safe, documented *defaults* live in this file, and even
those are overridden the moment an env var is set). Four independent
routing categories map to the eight required env vars:

  category    provider var          model var           used by
  ---------   -------------------   -----------------   ----------------------------------
  planner     PLANNER_PROVIDER      PLANNER_MODEL        planner, query classifier,
                                                          query reformulator (cheap/fast)
  reasoning   REASONING_PROVIDER    REASONING_MODEL      evidence analyst, conflict resolver
  synthesis   SYNTHESIS_PROVIDER    SYNTHESIS_MODEL       grounded synthesizer
  critic      CRITIC_PROVIDER       CRITIC_MODEL          citation reviewer, safety critic,
                                                          QA evaluator

``call_structured`` is the single safe-fail entrypoint every node should
use: it NEVER raises. Every failure mode (no key, unsupported provider,
network/timeout error, malformed/incomplete model output, token-budget
exhaustion) comes back as ``(None, "<reason>: detail", provider, model)``
so a node can degrade to its deterministic fallback without a bespoke
try/except at every call site.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 20

CATEGORY_ENV_VARS: dict[str, tuple[str, str]] = {
    "planner": ("PLANNER_PROVIDER", "PLANNER_MODEL"),
    "reasoning": ("REASONING_PROVIDER", "REASONING_MODEL"),
    "synthesis": ("SYNTHESIS_PROVIDER", "SYNTHESIS_MODEL"),
    "critic": ("CRITIC_PROVIDER", "CRITIC_MODEL"),
}

# Defaults only apply when the corresponding env var is unset. Planning/
# classification/reformulation default to a cheap, fast model; reasoning,
# synthesis, and critic categories default to a stronger model.
DEFAULT_PROVIDER_BY_CATEGORY = {
    "planner": "anthropic",
    "reasoning": "anthropic",
    "synthesis": "anthropic",
    "critic": "anthropic",
}

DEFAULT_MODEL_BY_CATEGORY_AND_PROVIDER = {
    ("planner", "anthropic"): "claude-haiku-4-5",
    ("planner", "openai"): "gpt-4o-mini",
    ("reasoning", "anthropic"): "claude-sonnet-4-5",
    ("reasoning", "openai"): "gpt-4o",
    ("synthesis", "anthropic"): "claude-sonnet-4-5",
    ("synthesis", "openai"): "gpt-4o",
    ("critic", "anthropic"): "claude-sonnet-4-5",
    ("critic", "openai"): "gpt-4o",
}

MAX_OUTPUT_TOKENS_BY_CATEGORY = {
    "planner": 400,
    "reasoning": 800,
    "synthesis": 700,
    "critic": 500,
}

SUPPORTED_PROVIDERS = ("openai", "anthropic")


class ModelNotConfiguredError(RuntimeError):
    """No usable provider credentials for this category."""


def resolve_provider_and_model(category: str) -> tuple[str, str]:
    if category not in CATEGORY_ENV_VARS:
        raise ModelNotConfiguredError(f"Unknown routing category {category!r}.")
    provider_var, model_var = CATEGORY_ENV_VARS[category]
    provider = (os.getenv(provider_var) or DEFAULT_PROVIDER_BY_CATEGORY[category]).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ModelNotConfiguredError(
            f"{provider_var}={provider!r} is not supported; must be 'openai' or 'anthropic'."
        )
    model = os.getenv(model_var) or DEFAULT_MODEL_BY_CATEGORY_AND_PROVIDER[(category, provider)]
    key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.getenv(key_var):
        raise ModelNotConfiguredError(f"{key_var} is not set (required for {category} category, provider={provider}).")
    return provider, model


def get_chat_model(category: str, max_tokens: int | None = None):
    """Returns (chat_model, provider, model_name). Raises
    ModelNotConfiguredError if unavailable -- callers needing the
    never-raises contract should use ``call_structured`` instead."""
    provider, model = resolve_provider_and_model(category)
    max_tokens = max_tokens or MAX_OUTPUT_TOKENS_BY_CATEGORY.get(category, 600)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        chat = ChatAnthropic(model=model, timeout=DEFAULT_TIMEOUT_SECONDS, max_tokens=max_tokens)
    else:
        from langchain_openai import ChatOpenAI

        chat = ChatOpenAI(model=model, timeout=DEFAULT_TIMEOUT_SECONDS, max_tokens=max_tokens)
    return chat, provider, model


def call_structured(
    category: str,
    schema: type,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int | None = None,
) -> tuple[Any | None, str, str | None, str | None]:
    """Never raises. Returns (result, status, provider, model):
      status == "ok"              -> result is a validated `schema` instance
      status starts with "not_configured" -> no usable API key for this category
      status starts with "provider_error" -> network/timeout/API failure
      status starts with "invalid_output"  -> model responded but not per schema
    """
    try:
        chat, provider, model = get_chat_model(category, max_tokens=max_tokens)
    except ModelNotConfiguredError as exc:
        return None, f"not_configured: {exc}", None, None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        structured_chat = chat.with_structured_output(schema)
        result = structured_chat.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    except Exception as exc:  # noqa: BLE001 - any provider/timeout/parsing failure must fail safe, not crash the graph
        return None, f"provider_error: {exc}", provider, model

    if not isinstance(result, schema):
        return None, "invalid_output: structured response did not match the expected schema", provider, model

    return result, "ok", provider, model


def call_text(
    category: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int | None = None,
) -> tuple[str | None, str, str | None, str | None]:
    """Same contract as ``call_structured`` but for free-text generation
    (used only by the grounded synthesizer, where the final answer IS
    prose, not a structured judgment)."""
    try:
        chat, provider, model = get_chat_model(category, max_tokens=max_tokens)
    except ModelNotConfiguredError as exc:
        return None, f"not_configured: {exc}", None, None

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = chat.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    except Exception as exc:  # noqa: BLE001
        return None, f"provider_error: {exc}", provider, model

    text = response.content if isinstance(response.content, str) else str(response.content)
    if not text or not text.strip():
        return None, "invalid_output: empty response", provider, model

    return text, "ok", provider, model
