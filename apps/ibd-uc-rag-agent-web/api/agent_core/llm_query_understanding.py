"""Model-powered query classifier and query reformulator.

Both are ADDITIVE, never authoritative over safety: the classifier's
intent judgment is recorded for routing/trace visibility, but the actual
refusal decision always comes from the deterministic, regex-based
``agent_core.safety_rules.check_safety_boundaries`` -- that hard gate
runs unconditionally and cannot be relaxed by an LLM classifying a
request as benign. Likewise the reformulator can only ADD an auxiliary
BM25 query to widen recall; it never replaces or narrows the original
query's own retrieval pass.

Both fail safe to their existing deterministic equivalents
(``agent_core.subagents.classify_intent`` / the original query text)
when no provider is configured or the model call fails.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from agent_core.model_router import call_structured
from agent_core.rate_limit import check_and_consume_token_budget, estimate_tokens
from agent_core.safety_rules import is_known_unsupported_topic
from agent_core.subagents import classify_intent as deterministic_classify_intent

Intent = Literal[
    "question",
    "diagnosis_seeking",
    "flare_prediction_seeking",
    "medication_change_seeking",
    "diet_plan_seeking",
    "symptom_inflammation_question",
    "crohns_misapplication",
]


class ClassifierOutput(BaseModel):
    intent: Intent
    primary_topic: Optional[str] = None
    rationale: str = ""


CLASSIFIER_SYSTEM_PROMPT = """Classify the INTENT of a user's question to a UC (ulcerative colitis) \
evidence tool. This classification is for routing/logging ONLY -- it never grants or blocks access \
by itself. Choose exactly one intent:
- question: a general evidence question
- diagnosis_seeking: asking whether they personally have UC or a flare
- flare_prediction_seeking: asking whether/when they will flare
- medication_change_seeking: asking about starting/stopping/changing medication
- diet_plan_seeking: asking for a personalized/individualized diet plan
- symptom_inflammation_question: asking whether symptoms confirm inflammation
- crohns_misapplication: asking to apply Crohn's-specific evidence to UC
Also name the single most relevant topic keyword if one is obvious, else leave it null."""


class ReformulationOutput(BaseModel):
    reformulated_query: str
    added_terms: list[str] = Field(default_factory=list)
    rationale: str = ""


REFORMULATOR_SYSTEM_PROMPT = """Rewrite the user's UC (ulcerative colitis) evidence question to \
maximize keyword recall for a BM25 search, by adding close synonyms or related terms actually \
likely to appear in a nutrition/lifestyle evidence claim (e.g. "fiber"/"fibre", "booze"/"alcohol", \
"produce"/"fruit and vegetables"). Do NOT change the meaning, do NOT add new medical topics not \
implied by the original question, and do NOT ask a different question. Return the reformulated \
query as one sentence."""


def _deterministic_classify_topic(query: str, topic_vocabulary: list[str]) -> str | None:
    lower = query.lower()
    for topic in topic_vocabulary:
        keyword = topic.replace("_", " ")
        if keyword and keyword in lower:
            return topic
    return None


def make_llm_query_classifier_node(topic_vocabulary: list[str]):
    def llm_query_classifier_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("query_classifier")
        query = state.get("query", "")

        # Deterministic and non-bypassable regardless of LLM availability:
        # gap-routing must not depend on a model call succeeding.
        state["known_unsupported"] = is_known_unsupported_topic(query)
        explicit_filter = state.get("topic_filter")
        state["classified_topic"] = explicit_filter or _deterministic_classify_topic(query, topic_vocabulary)

        user_prompt = f"Question: {query!r}"
        estimated = estimate_tokens(CLASSIFIER_SYSTEM_PROMPT, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured(
                "planner", ClassifierOutput, CLASSIFIER_SYSTEM_PROMPT, user_prompt
            )

        if result is not None:
            state["query_intent"] = result.intent
            if result.primary_topic and result.primary_topic in topic_vocabulary:
                state["classified_topic"] = result.primary_topic
            classifier_info = {
                "mode": "llm",
                "intent": result.intent,
                "primary_topic": result.primary_topic,
                "status": status,
                "provider": provider,
                "model": model,
            }
        else:
            # Deterministic fallback: reuses the single source of truth
            # for intent patterns (safety_rules), unchanged from before.
            state["query_intent"] = deterministic_classify_intent(query)
            classifier_info = {"mode": "deterministic_fallback", "intent": state["query_intent"], "status": status}

        state["classifier_info"] = classifier_info
        state.setdefault("trace", [])
        state["trace"].append({"node": "query_classifier", "output": classifier_info})
        return state

    return llm_query_classifier_node


def make_llm_query_reformulator_node():
    def llm_query_reformulator_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("query_reformulator")
        query = state.get("query", "")

        user_prompt = f"Question: {query!r}"
        estimated = estimate_tokens(REFORMULATOR_SYSTEM_PROMPT, user_prompt)
        if not check_and_consume_token_budget(state, estimated):
            result, status, provider, model = None, "token_budget_exceeded", None, None
        else:
            result, status, provider, model = call_structured(
                "planner", ReformulationOutput, REFORMULATOR_SYSTEM_PROMPT, user_prompt
            )

        if result is not None and result.reformulated_query.strip():
            state["reformulated_query"] = result.reformulated_query.strip()
            info = {
                "mode": "llm",
                "reformulated_query": state["reformulated_query"],
                "added_terms": result.added_terms,
                "status": status,
                "provider": provider,
                "model": model,
            }
        else:
            state["reformulated_query"] = query  # safe fallback: original query, unchanged
            info = {"mode": "deterministic_fallback", "reformulated_query": query, "status": status}

        state["reformulation_info"] = info
        state.setdefault("trace", [])
        state["trace"].append({"node": "query_reformulator", "output": info})
        return state

    return llm_query_reformulator_node
