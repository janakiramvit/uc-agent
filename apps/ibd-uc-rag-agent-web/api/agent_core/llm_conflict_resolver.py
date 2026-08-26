"""Model-powered conflict resolver: takes the deterministic
``conflict_detector``'s flagged topic-level conflicts (a structural
signal -- differing confidence/evidence-level ratings within one topic)
and classifies WHY, using structured output constrained to a fixed set
of dimensions.

Hard invariant, enforced in code, not by prompting alone: this node can
only ADD an explanation. It never removes a claim from the conflict
report, never merges two claims into one, and never silently prefers one
claim over the other -- both claim IDs from the deterministic report are
always preserved verbatim in the output regardless of what the model
says.

Fails safe: if unconfigured or the call fails, the deterministic
conflict report is used unchanged (already correct and safe on its own,
just without the dimension explanation).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from agent_core.model_router import call_structured
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens

Dimension = Literal[
    "population",
    "condition",
    "outcome",
    "intervention_or_exposure",
    "study_design",
    "evidence_strength",
    "time_period_or_setting",
    "none",
]


class ConflictResolution(BaseModel):
    is_true_contradiction: bool
    differing_dimension: Optional[Dimension] = None
    explanation: str = ""


SYSTEM_PROMPT = """You are the conflict resolver in a UC (ulcerative colitis) evidence agent. You are \
given two evidence claims on the same topic that a deterministic check flagged as having differing \
confidence or evidence-level ratings. Decide:

1. is_true_contradiction: do they actually assert opposite things about the same population,
   condition, outcome, intervention, and time period? Most flagged pairs are NOT true
   contradictions -- they usually differ in study design, evidence strength, population, or
   scope, while pointing the same direction.
2. If not a true contradiction, name the single dimension that best explains the difference:
   population, condition, outcome, intervention_or_exposure, study_design, evidence_strength,
   time_period_or_setting, or none.
3. Give a short, factual explanation grounded ONLY in the claim text given -- do not speculate
   beyond it.

You must NEVER recommend discarding, merging, or picking one claim over the other -- both remain
in the answer regardless of your classification."""


def _format_pair(claim_a: dict, claim_b: dict) -> str:
    return (
        f"Claim A ({claim_a.get('claimId')}): {claim_a.get('claimText')}\n"
        f"Claim B ({claim_b.get('claimId')}): {claim_b.get('claimText')}"
    )


def make_llm_conflict_resolver_node(package):
    claims_by_id = {c["claimId"]: c for c in package.all_claims}

    def llm_conflict_resolver_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("conflict_resolver")

        conflict_report = state.get("conflict_report") or {"has_conflicts": False, "conflicts": []}
        resolved_conflicts = []

        for conflict in conflict_report.get("conflicts", []):
            claim_ids = conflict.get("claimIds", [])
            resolution_entry = {**conflict, "resolution": None}

            if len(claim_ids) >= 2 and all(cid in claims_by_id for cid in claim_ids[:2]):
                pair_text = _format_pair(claims_by_id[claim_ids[0]], claims_by_id[claim_ids[1]])
                user_prompt = f"Topic: {conflict.get('topic')}\n\n{pair_text}"
                estimated = estimate_tokens(SYSTEM_PROMPT, user_prompt)
                if not check_and_consume_token_budget(state, estimated):
                    result, status, provider, model = None, "token_budget_exceeded", None, None
                else:
                    result, status, provider, model = call_structured(
                        "reasoning", ConflictResolution, SYSTEM_PROMPT, user_prompt
                    )

                if result is not None:
                    resolution_entry["resolution"] = {
                        "mode": "llm",
                        "is_true_contradiction": result.is_true_contradiction,
                        "differing_dimension": result.differing_dimension,
                        "explanation": result.explanation,
                        "status": status,
                        "provider": provider,
                        "model": model,
                    }
                else:
                    resolution_entry["resolution"] = {"mode": "deterministic_fallback", "status": status}
            else:
                resolution_entry["resolution"] = {"mode": "skipped", "status": "insufficient_claim_data"}

            # claim_ids are carried through verbatim from the deterministic
            # report -- this loop only ever ADDS a "resolution" key.
            resolved_conflicts.append(resolution_entry)

        state["conflict_report"] = {**conflict_report, "conflicts": resolved_conflicts}
        state.setdefault("trace", [])
        state["trace"].append(
            {
                "node": "conflict_resolver",
                "output": {"resolved_count": len(resolved_conflicts)},
            }
        )
        return state

    return llm_conflict_resolver_node
