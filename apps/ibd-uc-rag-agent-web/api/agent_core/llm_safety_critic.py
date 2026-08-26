"""Model-powered safety critic, layered ON TOP OF (never instead of) the
deterministic regex-based ``safety_critic_review`` in
``agent_core.subagents``.

Hard invariant: ``passed = deterministic_passed AND llm_passed``. The
model can only make the combined verdict STRICTER (catch something the
regex patterns miss) -- it can never turn a deterministic failure into a
pass, and if the model is unavailable the deterministic check alone
still governs (unchanged, already-safe behavior).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.model_router import call_structured
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens
from agent_core.subagents import safety_critic_review as deterministic_safety_critic_review


class SafetyCriticOutput(BaseModel):
    passed: bool
    concerns: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the safety critic reviewing a DRAFTED ANSWER (not the original question) \
from a UC (ulcerative colitis) evidence tool. Fail it (passed=false) if the draft: states or implies \
a diagnosis; predicts a flare; recommends starting/stopping/changing medication; gives an \
individualized diet/treatment plan; overstates a causal claim ("causes", "proven to cause") beyond \
what an association/observational claim supports; or confuses symptoms with confirmed inflammation. \
Otherwise passed=true. List each concern briefly."""


def make_llm_safety_critic_node():
    def llm_safety_critic_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("safety_critic")

        draft_answer = state.get("draft_answer", "")
        deterministic_result = deterministic_safety_critic_review(draft_answer)

        user_prompt = f"Drafted answer:\n{draft_answer}"
        estimated = estimate_tokens(SYSTEM_PROMPT, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured("critic", SafetyCriticOutput, SYSTEM_PROMPT, user_prompt)

        if result is not None:
            combined_passed = deterministic_result["passed"] and result.passed
            combined = {
                "mode": "llm",
                "status": status,
                "provider": provider,
                "model": model,
                "passed": combined_passed,
                "deterministic_passed": deterministic_result["passed"],
                "deterministic_failures": deterministic_result["failures"],
                "llm_passed": result.passed,
                "llm_concerns": result.concerns,
            }
        else:
            # Deterministic regex check is the safe floor -- always governs
            # on its own when the model is unavailable.
            combined = {
                "mode": "deterministic_fallback",
                "status": status,
                "passed": deterministic_result["passed"],
                "deterministic_passed": deterministic_result["passed"],
                "deterministic_failures": deterministic_result["failures"],
                "llm_passed": None,
                "llm_concerns": [],
            }

        state["safety_critic_result"] = combined
        state.setdefault("trace", [])
        state["trace"].append({"node": "safety_critic", "output": combined})
        return state

    return llm_safety_critic_node
