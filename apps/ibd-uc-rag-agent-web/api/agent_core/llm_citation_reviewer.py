"""Model-powered citation reviewer: a SEMANTIC check layered on top of
the deterministic ``citation_verifier`` (agent_core.subagents), which
remains the hard gate on citation EXISTENCE and field-for-field integrity
(claimId is real, sourceUrl/excerpt/locator match the evidence package
verbatim). This node only runs after the deterministic check has already
passed, and asks: does the cited excerpt actually support the sentence
that cites it?

The LLM can only make citation review STRICTER, never looser: if the
deterministic verifier already failed, this node is never invoked (the
graph routes straight to retry/refuse). If this node is unavailable, the
deterministic pass already reached is sufficient to proceed -- citation
review does not block on missing credentials.
"""

from __future__ import annotations

from pydantic import BaseModel

from agent_core.model_router import call_structured
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens

MAX_CITATIONS_REVIEWED = 5  # cost/token bound: review at most this many per request


class CitationReview(BaseModel):
    claim_id: str
    semantically_supported: bool
    concern: str = ""


class CitationReviewBatch(BaseModel):
    reviews: list[CitationReview]


SYSTEM_PROMPT = """You are the citation reviewer in a UC (ulcerative colitis) evidence agent. You are \
given a drafted answer and the citations attached to it (each with its real supporting excerpt from \
the evidence package). For EACH citation, judge whether the supporting excerpt genuinely supports \
what the answer says near that citation number. Flag semantically_supported=false only for a real \
mismatch (the excerpt doesn't back up the claim near it) -- not for stylistic preferences."""


def _format_review_input(draft_answer: str, citations: list[dict]) -> str:
    lines = [f"Draft answer:\n{draft_answer}", "\nCitations:"]
    for c in citations[:MAX_CITATIONS_REVIEWED]:
        lines.append(f"[{c.get('number')}] claimId={c.get('claimId')} excerpt: {c.get('supportingExcerpt')}")
    return "\n".join(lines)


def make_llm_citation_reviewer_node():
    def llm_citation_reviewer_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("citation_reviewer")

        draft_answer = state.get("draft_answer", "")
        citations = state.get("draft_citations", [])

        if not citations:
            result_info = {"mode": "skipped", "status": "no_citations", "passed": True, "reviews": []}
        else:
            user_prompt = _format_review_input(draft_answer, citations)
            estimated = estimate_tokens(SYSTEM_PROMPT, user_prompt)
            if not check_and_consume_token_budget(state, estimated):
                result, status, provider, model = None, "token_budget_exceeded", None, None
            else:
                result, status, provider, model = call_structured(
                    "critic", CitationReviewBatch, SYSTEM_PROMPT, user_prompt
                )

            if result is not None:
                reviews = [r.model_dump() for r in result.reviews]
                passed = all(r["semantically_supported"] for r in reviews)
                result_info = {
                    "mode": "llm",
                    "status": status,
                    "provider": provider,
                    "model": model,
                    "passed": passed,
                    "reviews": reviews,
                }
            else:
                # Deterministic citation_verifier already passed before this
                # node runs -- unavailability here does not block the answer.
                result_info = {"mode": "deterministic_fallback", "status": status, "passed": True, "reviews": []}

        state["citation_review_result"] = result_info
        state.setdefault("trace", [])
        state["trace"].append({"node": "citation_reviewer", "output": result_info})
        return state

    return llm_citation_reviewer_node
