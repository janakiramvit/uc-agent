from agent_core.planner import build_plan, decompose_query, identify_topics

TOPIC_VOCAB = ["fibre", "alcohol", "fruit_vegetables", "core_condition_knowledge"]


def test_decompose_query_splits_on_and():
    parts = decompose_query("What about fibre and alcohol?")
    assert "fibre" in " ".join(parts)
    assert "alcohol" in " ".join(parts)
    assert len(parts) >= 2


def test_decompose_query_single_segment_for_simple_question():
    parts = decompose_query("Is fibre good for UC?")
    assert len(parts) == 1


def test_identify_topics_matches_known_vocabulary():
    segments = ["fibre intake", "alcohol use"]
    topics = identify_topics(segments, TOPIC_VOCAB)
    assert set(topics) == {"fibre", "alcohol"}


def test_identify_topics_no_match_returns_empty():
    topics = identify_topics(["something unrelated"], TOPIC_VOCAB)
    assert topics == []


def test_build_plan_compound_query_adds_subtopic_step():
    plan = build_plan("What about fibre and alcohol?", TOPIC_VOCAB)
    assert set(plan.identified_topics) == {"fibre", "alcohol"}
    assert "retrieve_evidence_per_subtopic" in plan.steps


def test_build_plan_simple_query_has_core_steps_only():
    plan = build_plan("Is fibre good for UC?", TOPIC_VOCAB)
    assert plan.identified_topics == ["fibre"]
    assert "retrieve_evidence_per_subtopic" not in plan.steps
    assert plan.steps[0] == "classify_intent"
    assert plan.steps[-1] == "run_qa_pass"


def test_planner_node_records_visit_and_trace():
    from agent_core.planner import make_planner_node

    node = make_planner_node(TOPIC_VOCAB)
    state = {"query": "Is fibre good for UC?", "visited_nodes": [], "trace": []}
    result = node(state)
    assert "planner" in result["visited_nodes"]
    assert result["plan"]["identified_topics"] == ["fibre"]
    assert result["trace"][-1]["node"] == "planner"
