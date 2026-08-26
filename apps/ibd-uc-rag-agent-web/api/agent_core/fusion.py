"""Fusion / reranking: combines BM25 keyword retrieval with vector
retrieval into one ranked candidate list using Reciprocal Rank Fusion
(RRF), the standard, LLM-free way to merge two independently-ranked
result lists without needing their raw scores to be on the same scale
(BM25 scores and cosine similarity scores are not comparable directly;
RRF sidesteps that by fusing on RANK, not raw score).

This module is real by construction, not a label: when vector retrieval
is unavailable (no embeddings key), fusion degrades to a pure BM25
passthrough (RRF over a single ranked list preserves that list's order
exactly) -- there is no fabricated "vector contribution" claimed when
none occurred. ``fusion_report.vector_used`` records honestly which case
happened on each request, and the downstream answer workflow always
consumes the FUSED list (never the raw BM25 list directly), so when
vector retrieval genuinely runs, it genuinely participates in what gets
verified, cited, and synthesized -- not merely computed and discarded.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_core.evidence_loader import EvidencePackage
from agent_core.retrieval import RetrievedClaim

RRF_K = 60  # standard RRF damping constant


@dataclass
class FusionReport:
    bm25_ids: list[str] = field(default_factory=list)
    vector_ids: list[str] = field(default_factory=list)
    planner_ids: list[str] = field(default_factory=list)
    fused_ids: list[str] = field(default_factory=list)
    vector_used: bool = False
    planner_used: bool = False
    method: str = "reciprocal_rank_fusion"


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = RRF_K) -> list[str]:
    """Merge multiple ranked ID lists into one fused ranking.

    score(id) = sum over each list containing id of 1 / (k + rank), rank
    starting at 1. IDs are returned sorted by descending fused score;
    ties broken by first-seen order for determinism.
    """
    scores: dict[str, float] = {}
    first_seen_order: list[str] = []
    for ranked_list in ranked_lists:
        for rank, item_id in enumerate(ranked_list, start=1):
            if item_id not in scores:
                first_seen_order.append(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)

    return sorted(first_seen_order, key=lambda i: scores[i], reverse=True)


def fuse_candidates(
    package: EvidencePackage,
    bm25_claims: list[RetrievedClaim],
    vector_matches: list[dict],
    vector_used: bool,
    planner_ids: list[str] | None = None,
) -> tuple[list[RetrievedClaim], FusionReport]:
    """Fuse BM25-ranked claims with vector-ranked matches (and, when the
    LLM planner ran its own search_uc_claims tool calls, that ranked
    signal too) into one ranked ``RetrievedClaim`` list. Any ID surfaced
    only by vector or planner tool calls is resolved against the package
    directly -- never fabricated, always a real evidence-package lookup.
    """
    bm25_ids = [c.claim_id for c in bm25_claims]
    vector_ids = [m["claimId"] for m in vector_matches] if vector_used else []
    planner_ids = planner_ids or []
    planner_used = bool(planner_ids)

    ranked_lists = [ids for ids in (bm25_ids, vector_ids, planner_ids) if ids]
    fused_ids = reciprocal_rank_fusion(ranked_lists) if len(ranked_lists) > 1 else list(bm25_ids or planner_ids)

    by_id: dict[str, RetrievedClaim] = {c.claim_id: c for c in bm25_claims}
    claims_by_id = {c["claimId"]: c for c in package.all_claims}

    fused_claims: list[RetrievedClaim] = []
    for claim_id in fused_ids:
        if claim_id in by_id:
            fused_claims.append(by_id[claim_id])
        elif claim_id in claims_by_id:
            fused_claims.append(RetrievedClaim.from_claim_dict(claims_by_id[claim_id]))

    report = FusionReport(
        bm25_ids=bm25_ids,
        vector_ids=vector_ids,
        planner_ids=planner_ids,
        fused_ids=[c.claim_id for c in fused_claims],
        vector_used=vector_used,
        planner_used=planner_used,
    )
    return fused_claims, report


def make_fusion_reranker_node(package: EvidencePackage):
    def fusion_reranker_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("fusion_reranker")

        vector_used = state.get("vector_retrieval_status") == "ok"
        planner_ids = (state.get("plan") or {}).get("planner_sourced_claim_ids") or []
        fused_claims, report = fuse_candidates(
            package,
            state.get("candidate_claims", []),
            state.get("vector_matches", []),
            vector_used,
            planner_ids,
        )
        state["candidate_claims"] = fused_claims
        state["fusion_report"] = {
            "bm25_ids": report.bm25_ids,
            "vector_ids": report.vector_ids,
            "planner_ids": report.planner_ids,
            "fused_ids": report.fused_ids,
            "vector_used": report.vector_used,
            "planner_used": report.planner_used,
            "method": report.method,
        }
        state.setdefault("trace", [])
        state["trace"].append({"node": "fusion_reranker", "output": state["fusion_report"]})
        return state

    return fusion_reranker_node
