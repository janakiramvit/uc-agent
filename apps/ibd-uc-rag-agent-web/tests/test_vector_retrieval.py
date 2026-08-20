"""Vector retrieval must report an explicit 'unavailable' status when no
embeddings provider key is configured -- it must never silently fall
back to something else and call it a vector match."""

from unittest.mock import patch

from agent_core.vector_retrieval import (
    VectorMatch,
    VectorRetrievalUnavailable,
    make_vector_retriever_node,
    vector_retrieve,
)


def test_vector_retrieve_raises_without_api_key(package, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import pytest

    with pytest.raises(VectorRetrievalUnavailable):
        vector_retrieve(package, "fibre")


def test_vector_retriever_node_reports_unavailable_status(package, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    node = make_vector_retriever_node(package)
    state = {"query": "fibre", "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["vector_retrieval_status"] == "unavailable_no_api_key"
    assert result["vector_matches"] == []
    assert "vector_retriever" in result["visited_nodes"]


def test_vector_retriever_node_reports_ok_status_when_configured(package):
    """With a provider mocked in (no real network/API call), the node
    must report status='ok' and populate ranked matches -- proving the
    success path is real code, not aspirational."""
    with patch(
        "agent_core.vector_retrieval.vector_retrieve",
        return_value=[VectorMatch(claim_id="CLM-014", score=0.87), VectorMatch(claim_id="CLM-094", score=0.5)],
    ):
        node = make_vector_retriever_node(package)
        state = {"query": "fibre", "visited_nodes": [], "trace": []}
        result = node(state)

    assert result["vector_retrieval_status"] == "ok"
    assert [m["claimId"] for m in result["vector_matches"]] == ["CLM-014", "CLM-094"]
    assert result["vector_matches"][0]["score"] == 0.87
