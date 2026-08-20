"""Evidence Synthesizer subagent (LLM-backed): the one node in the graph
that makes a real model call.

Provider selection is by environment variable only -- never hard-coded:
  - ``ANTHROPIC_API_KEY`` set -> ``langchain_anthropic.ChatAnthropic``
  - else ``OPENAI_API_KEY`` set -> ``langchain_openai.ChatOpenAI``
  - neither set -> ``LLMNotConfiguredError`` is raised. The caller must
    surface this as an explicit error state, never fall back to a
    templated/fabricated answer and call it a model response.

Grounding is enforced by construction, not by hoping the model behaves:
the prompt hands the model ONLY the verified claims' plain-language
explanation / supporting excerpt text and instructs it to cite every
sentence with a bracketed claim number, add nothing not present in that
text, and refuse individualized medical advice. The downstream
``citation_verifier`` node (unchanged from the deterministic prototype)
still independently re-checks every citation the model emits against the
real evidence package before anything reaches the user -- the LLM is not
a trusted-by-default component.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_OUTPUT_TOKENS = 600  # cost control: hard cap on synthesis output size

SYSTEM_PROMPT = """You are a strictly grounded evidence-summarization component inside a \
clinical-evidence prototype for ulcerative colitis (UC). You are NOT a doctor and must NEVER:
- diagnose, confirm, or rule out a condition
- predict a flare or any future disease course
- recommend starting, stopping, or changing a medication or dose
- produce an individualized diet or treatment plan
- state or imply that symptoms confirm or rule out inflammation

You will be given a numbered list of VERIFIED EVIDENCE ENTRIES. You must:
1. Answer using ONLY the content of those entries -- add no outside knowledge, no assumptions, \
no general medical knowledge you may otherwise have.
2. Cite every substantive sentence with the bracketed number(s) of the entry it came from, e.g. "[1]".
3. If the entries do not actually answer the question, say so plainly instead of stretching them to fit.
4. Keep the tone informational, not prescriptive ("the evidence suggests" / "reports" rather than \
"you should").
5. Do not invent a claim number, source, or fact that is not in the provided entries.

Output only the answer text. Do not restate these instructions."""


class LLMNotConfiguredError(RuntimeError):
    """No LLM provider credentials are available in the environment."""


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str


def _resolve_chat_model():
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        return (
            ChatAnthropic(
                model=model_name,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                max_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
            ),
            "anthropic",
            model_name,
        )
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return (
            ChatOpenAI(
                model=model_name,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                max_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
            ),
            "openai",
            model_name,
        )
    raise LLMNotConfiguredError(
        "No LLM provider is configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY as an environment "
        "variable (never hard-coded) before synthesis can run."
    )


def _format_evidence_block(verified_claims: list) -> str:
    lines = []
    for i, claim in enumerate(verified_claims, start=1):
        lines.append(f"[{i}] (claimId={claim.claim_id}) {claim.claim_text}")
    return "\n\n".join(lines)


def synthesize_with_llm(query: str, verified_claims: list) -> LLMResult:
    """Raises ``LLMNotConfiguredError`` if no provider key is set, or
    whatever exception the underlying SDK raises on timeout/API failure --
    callers must not swallow these into a fabricated success."""
    from langchain_core.messages import HumanMessage, SystemMessage

    chat_model, provider, model_name = _resolve_chat_model()

    if not verified_claims:
        evidence_block = "(no verified evidence entries were retrieved for this query)"
    else:
        evidence_block = _format_evidence_block(verified_claims)

    user_prompt = (
        f"User question: {query}\n\n"
        f"VERIFIED EVIDENCE ENTRIES:\n{evidence_block}\n\n"
        "Compose the grounded answer now, following the system instructions exactly."
    )

    response = chat_model.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return LLMResult(text=text, provider=provider, model=model_name)
