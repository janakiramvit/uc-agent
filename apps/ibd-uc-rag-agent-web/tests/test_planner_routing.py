"""Planner routing: proves the planner's identified sub-topics actually
change how retrieval is executed (real tool orchestration), not just a
label attached to the response."""

from agent_core.graph_v2 import make_planned_evidence_retriever_node


def test_single_topic_query_uses_single_retrieval_call(retriever):
    node = make_planned_evidence_retriever_node(retriever)
    state = {
        "query": "Is fibre good for UC?",
        "classified_topic": "fibre",
        "plan": {"identified_topics": ["fibre"]},
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
    }
    result = node(state)
    assert result["trace"][-1]["output"]["mode"] == "single_query"
    ids = {c.claim_id for c in result["candidate_claims"]}
    assert ids == {"CLM-014", "CLM-094"}


def test_compound_query_routes_one_retrieval_per_subtopic(retriever):
    node = make_planned_evidence_retriever_node(retriever)
    state = {
        "query": "What about fibre and alcohol?",
        "classified_topic": None,
        "plan": {"identified_topics": ["fibre", "alcohol"]},
        "disease_filter": "ulcerative_colitis",
        "visited_nodes": [],
        "trace": [],
    }
    result = node(state)
    trace_output = result["trace"][-1]["output"]
    assert trace_output["mode"] == "per_subtopic"
    assert trace_output["topics"] == ["fibre", "alcohol"]
    ids = {c.claim_id for c in result["candidate_claims"]}
    # Both sub-topics' claims must be present -- proof the second
    # sub-topic wasn't silently dropped by a single combined BM25 call.
    assert {"CLM-014", "CLM-094"}.issubset(ids)
    assert "CLM-095" in ids


def test_known_unsupported_short_circuits_without_retrieval_call(retriever):
    node = make_planned_evidence_retriever_node(retriever)
    state = {
        "query": "What does ESR tell me?",
        "known_unsupported": True,
        "plan": {"identified_topics": []},
        "visited_nodes": [],
        "trace": [],
    }
    result = node(state)
    assert result["candidate_claims"] == []
    assert result["trace"][-1]["output"]["skipped"] == "known_unsupported"
