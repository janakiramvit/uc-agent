"""Query Planner subagent: decomposes a user query into an ordered list of
sub-topics/tool-call steps before retrieval runs.

Deterministic and dependency-free (no LLM call) so it is fully unit
testable and never blocked by missing LLM credentials -- planning is a
control-flow concern, not a generation concern. Splits compound questions
("What about fibre and alcohol?") into individually-classifiable segments
against the known topic vocabulary, so downstream retrieval can be run
once per identified sub-topic instead of losing the second half of a
compound question to a single BM25 pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SPLIT_PATTERN = re.compile(r"\band\b|\bor\b|[,;]|\?", flags=re.IGNORECASE)


@dataclass
class QueryPlan:
    original_query: str
    segments: list[str] = field(default_factory=list)
    identified_topics: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)


def decompose_query(query: str) -> list[str]:
    """Split a compound question into candidate sub-segments.

    Pure string splitting -- not NLP. Good enough to catch the common
    "X and Y" / "X, Y, and Z" patterns clinicians and patients actually
    type, without requiring a model call to do it.
    """
    parts = [p.strip() for p in _SPLIT_PATTERN.split(query) if p.strip()]
    return parts or [query.strip()]


def identify_topics(segments: list[str], topic_vocabulary: list[str]) -> list[str]:
    found: list[str] = []
    for segment in segments:
        lower = segment.lower()
        for topic in topic_vocabulary:
            keyword = topic.replace("_", " ")
            if keyword and keyword in lower and topic not in found:
                found.append(topic)
    return found


def build_plan(query: str, topic_vocabulary: list[str]) -> QueryPlan:
    segments = decompose_query(query)
    topics = identify_topics(segments, topic_vocabulary)

    steps = ["classify_intent", "retrieve_evidence"]
    if len(topics) > 1:
        steps.append("retrieve_evidence_per_subtopic")
    steps += [
        "check_source_applicability",
        "detect_conflicts",
        "detect_gaps",
        "check_safety_boundaries",
        "synthesize_grounded_answer",
        "verify_safety_and_citations",
        "run_qa_pass",
    ]

    return QueryPlan(
        original_query=query,
        segments=segments,
        identified_topics=topics,
        steps=steps,
    )


def make_planner_node(topic_vocabulary: list[str]):
    def planner_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("planner")
        plan = build_plan(state.get("query", ""), topic_vocabulary)
        state["plan"] = {
            "segments": plan.segments,
            "identified_topics": plan.identified_topics,
            "steps": plan.steps,
        }
        state.setdefault("trace", [])
        state["trace"].append({"node": "planner", "output": state["plan"]})
        return state

    return planner_node
