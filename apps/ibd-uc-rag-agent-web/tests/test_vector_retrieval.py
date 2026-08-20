"""Vector retrieval must report an explicit 'unavailable' status when no
embeddings provider key is configured -- it must never silently fall
back to something else and call it a vector match."""

from agent_core.vector_retrieval import (
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
