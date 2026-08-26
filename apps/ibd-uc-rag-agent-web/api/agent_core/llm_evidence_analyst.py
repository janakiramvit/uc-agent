"""Model-powered evidence analyst: summarizes what the verified,
already-retrieved claims say and flags sufficiency -- it does not
retrieve, filter, or introduce evidence. Any claim ID the model mentions
that is NOT in the actual verified set is dropped and flagged rather
than trusted, so a hallucinated claim ID can never reach the user (the
model can only comment on evidence that was already deterministically
retrieved and applicability-checked upstream).

Fails safe to a purely deterministic sufficiency judgment (non-empty
verified set => "sufficient") when unconfigured or on error.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agent_core.model_router import call_structured
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens

Sufficiency = Literal["sufficient", "partial", "insufficient"]
Relevance = Literal["high", "medium", "low"]


class ClaimRelevance(BaseModel):
    claim_id: str
    relevance: Relevance
    note: str = ""


class EvidenceAnalysisOutput(BaseModel):
    sufficiency: Sufficiency
    key_points: list[str] = Field(default_factory=list)
    per_claim: list[ClaimRelevance] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the evidence analyst in a UC (ulcerative colitis) evidence agent. You are \
given a list of ALREADY-VERIFIED evidence claims (each with a real claimId) and must:
1. Judge whether they are sufficient to answer the user's question ("sufficient" / "partial" /
   "insufficient" -- e.g. if the claims are tangential or thin, say so).
2. List key points strictly drawn from the given claim text -- add no outside knowledge.
3. For each claim you actually reference, rate its relevance to the question, using ONLY the
   claimId values given to you. Never invent a claimId that was not provided."""


def _format_claims(verified_claims: list) -> str:
    lines = []
    for c in verified_claims:
        lines.append(f"claimId={c.claim_id} topic={c.topic}: {c.claim_text}")
    return "\n".join(lines) if lines else "(no verified claims were retrieved)"


def make_llm_evidence_analyst_node():
    def llm_evidence_analyst_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("evidence_analyst")
        verified = state.get("verified_claims", [])
        real_ids = {c.claim_id for c in verified}

        user_prompt = f"Question: {state.get('query', '')!r}\n\nVerified claims:\n{_format_claims(verified)}"
        estimated = estimate_tokens(SYSTEM_PROMPT, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured(
                "reasoning", EvidenceAnalysisOutput, SYSTEM_PROMPT, user_prompt
            )

        if result is not None:
            # Hard defense: drop any claimId the model mentioned that
            # isn't actually in the verified set -- never trust model
            # text to introduce evidence that wasn't really retrieved.
            safe_per_claim = [c.model_dump() for c in result.per_claim if c.claim_id in real_ids]
            dropped = [c.claim_id for c in result.per_claim if c.claim_id not in real_ids]
            analysis = {
                "mode": "llm",
                "sufficiency": result.sufficiency,
                "key_points": result.key_points,
                "per_claim": safe_per_claim,
                "dropped_hallucinated_claim_ids": dropped,
                "status": status,
                "provider": provider,
                "model": model,
            }
        else:
            analysis = {
                "mode": "deterministic_fallback",
                "sufficiency": "sufficient" if verified else "insufficient",
                "key_points": [],
                "per_claim": [],
                "dropped_hallucinated_claim_ids": [],
                "status": status,
            }

        state["evidence_analysis"] = analysis
        state.setdefault("trace", [])
        state["trace"].append({"node": "evidence_analyst", "output": analysis})
        return state

    return llm_evidence_analyst_node
