"""Pure, transport-independent implementations of the MCP tool functions.

These functions are the single source of truth for the read-only,
eligibility-filtered view exposed both by the MCP server (``server.py``)
and reused directly by the LangGraph "Gap Detector" subagent in
``app/subagents.py`` -- so there is exactly one place that computes
evidence gaps, claim applicability, etc.

No function in this module ever writes, approves, edits, or deletes any
data. Everything here is read-only over an already-loaded
``EvidencePackage`` (see ``app.evidence_loader``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_core.evidence_loader import EvidencePackage, is_crohns_only, is_uc_eligible
from agent_core.retrieval import UCEvidenceRetriever

# Fields that must always be preserved unmodified in any claim payload
# returned by an MCP tool (see task spec: claim ID, source ID, source
# URL, supporting excerpt, exact locator, evidence level, limitations,
# applicability limitations).
CLAIM_VERBATIM_FIELDS = (
    "claimId",
    "sourceId",
    "sourceUrl",
    "sourceTitle",
    "claimText",
    "supportingExcerpt",
    "exactLocator",
    "evidenceLevel",
    "confidence",
    "limitations",
    "applicabilityLimitations",
    "topic",
    "outcomeType",
    "conditionApplicability",
    "diseaseContext",
)


@dataclass
class MCPToolContext:
    """Bundles the loaded package + retriever the tools operate over."""

    package: EvidencePackage
    retriever: UCEvidenceRetriever


def _claim_by_id(package: EvidencePackage, claim_id: str) -> dict[str, Any] | None:
    for c in package.all_claims:
        if c.get("claimId") == claim_id:
            return c
    return None


def _verbatim_claim_payload(claim: dict[str, Any]) -> dict[str, Any]:
    """Return a dict containing only the verbatim claim fields, unmodified."""
    return {field: claim.get(field, "") for field in CLAIM_VERBATIM_FIELDS}


# --- 1. search_uc_claims -------------------------------------------------


def search_uc_claims(ctx: MCPToolContext, query: str, topic: str | None = None) -> dict[str, Any]:
    """Search UC-eligible claims via the existing retrieval module.

    Returns only claims from the 5-claim UC-eligible set (never Crohn's-
    only or excluded claims), with all fields preserved verbatim.
    """
    results = ctx.retriever.retrieve(query=query or "", topic_filter=topic)
    claims = []
    for r in results:
        original = _claim_by_id(ctx.package, r.claim_id)
        if original is None:
            continue
        # Defense in depth -- never return a non-UC-eligible claim.
        if not is_uc_eligible(original) or is_crohns_only(original):
            continue
        claims.append(_verbatim_claim_payload(original))
    return {"query": query, "topic": topic, "count": len(claims), "claims": claims}


# --- 2. get_claim ----------------------------------------------------------


def get_claim(ctx: MCPToolContext, claim_id: str) -> dict[str, Any]:
    """Return one claim's full fields if and only if it is UC-eligible.

    Hard boundary: Crohn's-only claims, excluded claims, and unknown IDs
    are all refused (never returned), even when asked for directly by ID.
    """
    if claim_id in ctx.package.excluded_claim_ids:
        return {"found": False, "claimId": claim_id, "reason": "excluded_claim", "claim": None}
    original = _claim_by_id(ctx.package, claim_id)
    if original is None:
        return {"found": False, "claimId": claim_id, "reason": "unknown_claim_id", "claim": None}
    if is_crohns_only(original):
        return {"found": False, "claimId": claim_id, "reason": "crohns_only_not_uc_eligible", "claim": None}
    if not is_uc_eligible(original):
        return {"found": False, "claimId": claim_id, "reason": "not_uc_eligible", "claim": None}
    return {"found": True, "claimId": claim_id, "reason": "uc_eligible", "claim": _verbatim_claim_payload(original)}


# --- 3. get_source -----------------------------------------------------------


def get_source(ctx: MCPToolContext, source_id: str) -> dict[str, Any]:
    """Return source metadata for a given sourceId, if it exists."""
    source = ctx.package.sources_by_id.get(source_id)
    if source is None:
        return {"found": False, "sourceId": source_id, "source": None}
    return {"found": True, "sourceId": source_id, "source": dict(source)}


# --- 4. list_supported_topics -----------------------------------------------


def list_supported_topics(ctx: MCPToolContext) -> dict[str, Any]:
    """Topic vocabulary that actually has UC-eligible claims today.

    Reflects only the 5-claim reality, not the full 49-claim topic list.
    """
    topics = sorted({c["topic"] for c in ctx.package.uc_eligible_claims if c.get("topic")})
    return {"topics": topics, "count": len(topics)}


# --- 5. check_claim_applicability --------------------------------------------


def check_claim_applicability(ctx: MCPToolContext, claim_id: str) -> dict[str, Any]:
    """Return whether a claim is UC-eligible, Crohn's-only, or excluded."""
    if claim_id in ctx.package.excluded_claim_ids:
        return {
            "claimId": claim_id,
            "status": "excluded",
            "reason": "This claim ID is present in excludedClaimIds and is never retrievable.",
        }

    original = _claim_by_id(ctx.package, claim_id)
    if original is None:
        return {
            "claimId": claim_id,
            "status": "unknown",
            "reason": "No claim with this ID exists in the loaded evidence package.",
        }

    if is_crohns_only(original):
        return {
            "claimId": claim_id,
            "status": "crohns_only",
            "reason": "conditionApplicability is exactly 'crohns_disease'; not applicable to UC.",
        }

    if is_uc_eligible(original):
        return {
            "claimId": claim_id,
            "status": "uc_eligible",
            "reason": "conditionApplicability contains 'ulcerative_colitis'.",
        }

    return {
        "claimId": claim_id,
        "status": "not_uc_eligible",
        "reason": f"conditionApplicability={original.get('conditionApplicability')!r} does not contain 'ulcerative_colitis'.",
    }


# --- 6. get_evidence_gaps -----------------------------------------------------


def compute_evidence_gaps(package: EvidencePackage) -> dict[str, Any]:
    """Compute the known unsupported topics.

    Two sources are combined, both computed/derived (not hand-typed
    twice) to keep a single source of truth:

      1. Data-driven gaps: any topic present anywhere in the full
         (post-exclusion) claim set that has zero UC-eligible claims --
         computed dynamically by diffing the full topic vocabulary
         against the UC-eligible topic vocabulary.
      2. Known-absent categories: topics/keywords (ESR, CRP, fecal
         calprotectin, biologics, JAK inhibitors, mucosal healing,
         colonoscopy, intestinal ultrasound, ...) that never appear as a
         claim topic in the data at all -- reused from
         ``app.safety_rules.KNOWN_UNSUPPORTED_KEYWORDS`` so there is one
         source of truth for this list, not two.
    """
    from agent_core.safety_rules import KNOWN_UNSUPPORTED_KEYWORDS

    full_topic_vocab = sorted({c.get("topic") for c in package.all_claims if c.get("topic")})
    uc_topic_vocab = {c.get("topic") for c in package.uc_eligible_claims if c.get("topic")}
    data_driven_gaps = sorted(t for t in full_topic_vocab if t not in uc_topic_vocab)

    return {
        "data_driven_gap_topics": data_driven_gaps,
        "known_absent_categories": list(KNOWN_UNSUPPORTED_KEYWORDS),
        "all_gap_terms": sorted(set(data_driven_gaps) | set(KNOWN_UNSUPPORTED_KEYWORDS)),
    }


def get_evidence_gaps(ctx: MCPToolContext) -> dict[str, Any]:
    return compute_evidence_gaps(ctx.package)
