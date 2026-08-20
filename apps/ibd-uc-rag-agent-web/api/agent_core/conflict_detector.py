"""Conflict Detector subagent: flags when the verified claim set contains
potentially discordant evidence on the same topic (e.g. differing
confidence levels or evidence levels for the same outcome), so the
synthesizer/QA layer can surface that tension instead of silently
picking one side.

Heuristic and deterministic -- groups verified claims by topic and
compares their ``confidence`` / ``evidenceLevel`` fields. This does not
require an LLM call: it is a structural check over already-retrieved,
already-verified claim metadata.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ConflictReport:
    has_conflicts: bool
    conflicts: list[dict] = field(default_factory=list)


def detect_conflicts(verified_claims: list) -> ConflictReport:
    by_topic: dict[str, list] = defaultdict(list)
    for claim in verified_claims:
        by_topic[claim.topic or "unspecified"].append(claim)

    conflicts = []
    for topic, claims in by_topic.items():
        if len(claims) < 2:
            continue
        confidences = {c.confidence for c in claims if c.confidence}
        evidence_levels = {c.evidence_level for c in claims if c.evidence_level}
        if len(confidences) > 1 or len(evidence_levels) > 1:
            conflicts.append(
                {
                    "topic": topic,
                    "claimIds": [c.claim_id for c in claims],
                    "confidenceValues": sorted(confidences),
                    "evidenceLevelValues": sorted(evidence_levels),
                    "reason": "Claims on the same topic carry differing confidence or evidence-level ratings.",
                }
            )
    return ConflictReport(has_conflicts=bool(conflicts), conflicts=conflicts)


def make_conflict_detector_node():
    def conflict_detector_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("conflict_detector")
        report = detect_conflicts(state.get("verified_claims", []))
        state["conflict_report"] = {"has_conflicts": report.has_conflicts, "conflicts": report.conflicts}
        state.setdefault("trace", [])
        state["trace"].append({"node": "conflict_detector", "output": state["conflict_report"]})
        return state

    return conflict_detector_node
