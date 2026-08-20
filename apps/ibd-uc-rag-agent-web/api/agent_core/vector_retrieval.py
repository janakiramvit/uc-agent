"""Vector-based evidence retrieval, complementary to the BM25 keyword
retriever in ``agent_core.retrieval``.

Requires a real embeddings provider (OpenAI ``text-embedding-3-small``)
configured via ``OPENAI_API_KEY``. There is no local/offline fallback and
no fabricated similarity score: when no API key is present this module
reports ``unavailable_no_api_key`` explicitly rather than silently
returning BM25 results relabeled as "vector" results.

Embeddings for the (small, fixed) UC-eligible claim set are computed once
per process and cached in memory -- this keeps the per-query cost to a
single embedding call (the query itself) rather than re-embedding the
whole evidence set on every request.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from agent_core.evidence_loader import EvidencePackage

EMBEDDING_MODEL = "text-embedding-3-small"

_claim_embedding_cache: dict[str, list[float]] = {}


@dataclass
class VectorMatch:
    claim_id: str
    score: float


class VectorRetrievalUnavailable(RuntimeError):
    """Raised when no embeddings provider is configured. Callers must
    surface this as an explicit status, never silently degrade."""


def _client():
    if not os.getenv("OPENAI_API_KEY"):
        raise VectorRetrievalUnavailable("OPENAI_API_KEY is not set; vector retrieval requires OpenAI embeddings.")
    from openai import OpenAI  # imported lazily so the package is optional when unused

    return OpenAI()


def _embed(texts: list[str]) -> list[list[float]]:
    client = _client()
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _ensure_claim_embeddings(package: EvidencePackage) -> None:
    missing = [c for c in package.uc_eligible_claims if c["claimId"] not in _claim_embedding_cache]
    if not missing:
        return
    texts = [f"{c.get('topic', '')}: {c.get('plainLanguageExplanation') or c.get('claimText', '')}" for c in missing]
    vectors = _embed(texts)
    for claim, vector in zip(missing, vectors):
        _claim_embedding_cache[claim["claimId"]] = vector


def vector_retrieve(package: EvidencePackage, query: str, top_k: int = 5) -> list[VectorMatch]:
    """Raises ``VectorRetrievalUnavailable`` if no embeddings key is set."""
    _ensure_claim_embeddings(package)
    (query_vector,) = _embed([query])
    scored = [
        VectorMatch(claim_id=claim_id, score=_cosine(query_vector, vector))
        for claim_id, vector in _claim_embedding_cache.items()
    ]
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored[:top_k]


def make_vector_retriever_node(package: EvidencePackage):
    def vector_retriever_node(state: dict) -> dict:
        state.setdefault("visited_nodes", [])
        state["visited_nodes"].append("vector_retriever")
        try:
            matches = vector_retrieve(package, state.get("query", ""))
            state["vector_retrieval_status"] = "ok"
            state["vector_matches"] = [{"claimId": m.claim_id, "score": m.score} for m in matches]
        except VectorRetrievalUnavailable as exc:
            state["vector_retrieval_status"] = "unavailable_no_api_key"
            state["vector_matches"] = []
            state["vector_retrieval_error"] = str(exc)
        state.setdefault("trace", [])
        state["trace"].append(
            {
                "node": "vector_retriever",
                "output": {"status": state["vector_retrieval_status"], "match_count": len(state["vector_matches"])},
            }
        )
        return state

    return vector_retriever_node
