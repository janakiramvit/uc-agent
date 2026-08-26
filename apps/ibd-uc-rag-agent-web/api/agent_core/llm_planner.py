"""Model-powered planner: dynamically selects and sequences which of the
six read-only evidence tools to call, and identifies query sub-topics --
via structured, schema-validated output, not free text.

Tool EXECUTION is always the real, deterministic ``agent_core.tools``
functions (the same ones backing search/applicability/gap checks
elsewhere in the graph) -- the model can only choose *which* of a fixed,
enum-constrained set of tools to call and with what arguments; it cannot
invent a new tool, and every dispatched call goes through the same
UC-eligibility/exclusion filtering the tools already enforce. This is
what makes tool selection "dynamic" rather than a fixed label: the
sequence and arguments genuinely come from the model's judgment on this
specific query, but what each tool call is ALLOWED to do is fixed code.

Fails safe: no configured provider, a timeout/API error, or a malformed
response all fall back to the original deterministic decomposition in
``agent_core.planner`` (unchanged, already tested) with
``plan["mode"] = "deterministic_fallback"`` and the failure reason
recorded -- the graph never blocks or crashes on a planner failure.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from agent_core.model_router import call_structured
from agent_core.planner import build_plan
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens
from agent_core.tools import (
    MCPToolContext,
    check_claim_applicability,
    get_claim,
    get_evidence_gaps,
    get_source,
    list_supported_topics,
    search_uc_claims,
)

MAX_PLANNER_TOOL_CALLS = 4

ToolName = Literal[
    "search_uc_claims",
    "get_claim",
    "get_source",
    "list_supported_topics",
    "check_claim_applicability",
    "get_evidence_gaps",
]


class PlannedToolCall(BaseModel):
    tool: ToolName
    query: Optional[str] = None
    topic: Optional[str] = None
    claim_id: Optional[str] = None
    source_id: Optional[str] = None


class PlannerOutput(BaseModel):
    identified_topics: list[str] = Field(default_factory=list)
    tool_calls: list[PlannedToolCall] = Field(default_factory=list)
    reasoning: str = ""


SYSTEM_PROMPT_TEMPLATE = """You are the planning component of an ulcerative colitis (UC) evidence \
retrieval agent. You do not answer the user's question yourself -- you decide which read-only \
evidence tools (if any) should be called to gather what's needed, and which sub-topics the \
question touches.

Known UC-eligible topics today: {topics}

Available tools (call zero or more, in any order):
- search_uc_claims(query, topic): keyword search over the UC-eligible evidence set
- get_claim(claim_id): fetch one claim by ID
- get_source(source_id): fetch source metadata by ID
- list_supported_topics(): list topics that currently have UC-eligible evidence
- check_claim_applicability(claim_id): check whether a claim ID is UC-eligible/Crohn's-only/excluded
- get_evidence_gaps(): list topics known NOT to be covered by the evidence set

Guidance:
- If the question mentions more than one distinct topic (e.g. "fibre and alcohol"), list each in
  identified_topics using the vocabulary above, and consider one search_uc_claims call per topic.
- Only use topics from the list above in identified_topics -- do not invent new topic names.
- Prefer search_uc_claims for general questions; use get_evidence_gaps if the question sounds like
  it may be about something outside the reviewed evidence (e.g. lab values, biologics, imaging).
- Keep tool_calls short and purposeful -- do not call tools that would not help.
"""


def execute_planned_tool_calls(ctx: MCPToolContext, tool_calls: list[PlannedToolCall]) -> list[dict]:
    results = []
    for call in tool_calls[:MAX_PLANNER_TOOL_CALLS]:
        entry: dict = {"tool": call.tool, "args": call.model_dump(exclude={"tool"}, exclude_none=True)}
        try:
            if call.tool == "search_uc_claims":
                entry["result"] = search_uc_claims(ctx, call.query or "", call.topic)
            elif call.tool == "get_claim":
                entry["result"] = get_claim(ctx, call.claim_id or "")
            elif call.tool == "get_source":
                entry["result"] = get_source(ctx, call.source_id or "")
            elif call.tool == "list_supported_topics":
                entry["result"] = list_supported_topics(ctx)
            elif call.tool == "check_claim_applicability":
                entry["result"] = check_claim_applicability(ctx, call.claim_id or "")
            elif call.tool == "get_evidence_gaps":
                entry["result"] = get_evidence_gaps(ctx)
            else:  # unreachable given the Literal type, defensive only
                entry["error"] = f"unknown tool {call.tool!r}"
        except Exception as exc:  # noqa: BLE001 - one bad tool call must not crash planning
            entry["error"] = str(exc)
        results.append(entry)
    return results


def _planner_sourced_claim_ids(tool_results: list[dict]) -> list[str]:
    """Extract claim IDs the planner's own search_uc_claims calls
    surfaced, in the order first seen -- these feed fusion as a genuine
    (not decorative) third ranked signal alongside BM25 and vector."""
    ids: list[str] = []
    for entry in tool_results:
        if entry.get("tool") == "search_uc_claims":
            for claim in (entry.get("result") or {}).get("claims", []):
                claim_id = claim.get("claimId")
                if claim_id and claim_id not in ids:
                    ids.append(claim_id)
    return ids


def make_llm_planner_node(topic_vocabulary: list[str], ctx: MCPToolContext):
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(topics=", ".join(topic_vocabulary) or "(none)")

    def llm_planner_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("planner")
        query = state.get("query", "")
        user_prompt = f"User question: {query!r}"

        estimated = estimate_tokens(system_prompt, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured("planner", PlannerOutput, system_prompt, user_prompt)

        if result is not None:
            identified_topics = [t for t in result.identified_topics if t in topic_vocabulary]
            tool_results = execute_planned_tool_calls(ctx, result.tool_calls)
            plan = {
                "mode": "llm",
                "identified_topics": identified_topics,
                "tool_calls": [tc.model_dump(exclude_none=True) for tc in result.tool_calls[:MAX_PLANNER_TOOL_CALLS]],
                "tool_results": tool_results,
                "planner_sourced_claim_ids": _planner_sourced_claim_ids(tool_results),
                "reasoning": result.reasoning,
                "status": status,
                "provider": provider,
                "model": model,
                "steps": [
                    "classify_intent",
                    "retrieve_evidence",
                    *(["retrieve_evidence_per_subtopic"] if len(identified_topics) > 1 else []),
                    "check_source_applicability",
                    "detect_conflicts",
                    "detect_gaps",
                    "check_safety_boundaries",
                    "synthesize_grounded_answer",
                    "verify_safety_and_citations",
                    "run_qa_pass",
                ],
            }
        else:
            fallback = build_plan(query, topic_vocabulary)
            plan = {
                "mode": "deterministic_fallback",
                "identified_topics": fallback.identified_topics,
                "tool_calls": [],
                "tool_results": [],
                "planner_sourced_claim_ids": [],
                "reasoning": "",
                "status": status,
                "provider": provider,
                "model": model,
                "steps": fallback.steps,
            }

        state["plan"] = plan
        state.setdefault("trace", [])
        state["trace"].append(
            {
                "node": "planner",
                "output": {
                    "mode": plan["mode"],
                    "status": plan["status"],
                    "identified_topics": plan["identified_topics"],
                    "tool_call_count": len(plan["tool_calls"]),
                },
            }
        )
        return state

    return llm_planner_node
