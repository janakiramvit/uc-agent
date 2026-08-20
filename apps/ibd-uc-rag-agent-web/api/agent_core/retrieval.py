"""
LangChain-based retrieval module for the UC RAG prototype.

Uses LangChain's BM25Retriever (local, deterministic, no embeddings/API
calls) over Documents built exclusively from the UC-eligible claim set.

Metadata filtering happens BEFORE ranking: the retriever is built only
from Documents that already passed the UC-substring eligibility filter
and the excluded-claim-id filter in ``evidence_loader``. Optional topic /
disease filters supplied by the caller (e.g. from the Streamlit UI) are
also applied as a pre-filter on the candidate set before BM25 scoring,
never as a post-hoc re-ranking step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from agent_core.evidence_loader import (
    EvidencePackage,
    build_uc_documents,
    is_crohns_only,
    is_uc_eligible,
)

DISEASE_FILTER_FIXED_VALUE = "ulcerative_colitis"


@dataclass
class RetrievedClaim:
    """Verbatim, display-ready representation of one retrieved claim."""

    claim_id: str
    source_title: str
    source_url: str
    claim_text: str
    supporting_excerpt: str
    exact_locator: str
    evidence_level: str
    confidence: str
    limitations: str
    applicability_limitations: str
    topic: str
    outcome_type: str
    condition_applicability: str
    disease_context: str
    score: float = 0.0

    @classmethod
    def from_document(cls, doc: Document, score: float = 0.0) -> "RetrievedClaim":
        m = doc.metadata
        return cls(
            claim_id=m.get("claimId", ""),
            source_title=m.get("sourceTitle", ""),
            source_url=m.get("sourceUrl", ""),
            claim_text=m.get("claimText", ""),
            supporting_excerpt=m.get("supportingExcerpt", ""),
            exact_locator=m.get("exactLocator", ""),
            evidence_level=m.get("evidenceLevel", ""),
            confidence=m.get("confidence", ""),
            limitations=m.get("limitations", ""),
            applicability_limitations=m.get("applicabilityLimitations", ""),
            topic=m.get("topic", ""),
            outcome_type=m.get("outcomeType", ""),
            condition_applicability=m.get("conditionApplicability", ""),
            disease_context=m.get("diseaseContext", ""),
            score=score,
        )


class UCEvidenceRetriever:
    """Wraps a LangChain BM25Retriever restricted to UC-eligible claims."""

    def __init__(self, package: EvidencePackage, k: int = 5):
        self.package = package
        self.documents = build_uc_documents(package)
        self.k = k
        if self.documents:
            self._bm25 = BM25Retriever.from_documents(self.documents)
            self._bm25.k = max(k, len(self.documents))
        else:
            self._bm25 = None

    def _candidate_documents(self, topic_filter: str | None = None) -> list[Document]:
        """Pre-filter candidate documents by metadata BEFORE any ranking."""
        candidates = self.documents
        # Eligibility filter (defense in depth; documents were already
        # built only from eligible claims, but re-verify per-document).
        candidates = [d for d in candidates if is_uc_eligible(d.metadata)]
        candidates = [d for d in candidates if not is_crohns_only(d.metadata)]
        candidates = [
            d for d in candidates if d.metadata.get("claimId") not in self.package.excluded_claim_ids
        ]
        if topic_filter:
            candidates = [d for d in candidates if d.metadata.get("topic") == topic_filter]
        return candidates

    def retrieve(
        self,
        query: str,
        topic_filter: str | None = None,
        disease_filter: str = DISEASE_FILTER_FIXED_VALUE,
        k: int | None = None,
    ) -> list[RetrievedClaim]:
        """Retrieve UC-eligible claims relevant to ``query``.

        Filtering (eligibility, exclusion, topic) is always applied before
        BM25 relevance ranking.
        """
        if disease_filter != DISEASE_FILTER_FIXED_VALUE:
            # This prototype is UC-only; any other disease filter yields
            # no candidates by design.
            return []

        candidates = self._candidate_documents(topic_filter=topic_filter)
        if not candidates:
            return []

        k = k or self.k

        if not query or not query.strip():
            # No query text -- return the filtered candidate set as-is
            # (e.g. pure topic-filter browsing), in stable claimId order.
            ordered = sorted(candidates, key=lambda d: d.metadata.get("claimId", ""))
            return [RetrievedClaim.from_document(d, score=0.0) for d in ordered[:k]]

        local_bm25 = BM25Retriever.from_documents(candidates)
        local_bm25.k = min(k, len(candidates))
        ranked_docs = local_bm25.invoke(query)

        results = [RetrievedClaim.from_document(d) for d in ranked_docs]
        return results


def build_retriever(package: EvidencePackage, k: int = 5) -> UCEvidenceRetriever:
    return UCEvidenceRetriever(package, k=k)
