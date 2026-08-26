"""Conflict resolver: must classify true-contradiction vs. differing
dimension via structured output, and MUST NEVER drop either claim from
the deterministic conflict report regardless of what the model says."""

from unittest.mock import patch

from agent_core.conflict_detector import detect_conflicts
from agent_core.llm_conflict_resolver import ConflictResolution, make_llm_conflict_resolver_node


def _conflict_report_for_fibre(retriever):
    claims = retriever.retrieve(query="fibre", topic_filter="fibre")
    report = detect_conflicts(claims)
    return {"has_conflicts": report.has_conflicts, "conflicts": report.conflicts}


def test_both_claim_ids_preserved_when_llm_says_true_contradiction(package, retriever):
    conflict_report = _conflict_report_for_fibre(retriever)
    original_ids = set(conflict_report["conflicts"][0]["claimIds"])
    node = make_llm_conflict_resolver_node(package)
    mocked = ConflictResolution(is_true_contradiction=True, differing_dimension="none", explanation="test")
    with patch(
        "agent_core.llm_conflict_resolver.call_structured",
        return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"conflict_report": conflict_report, "visited_nodes": [], "trace": []}
        result = node(state)

    resolved = result["conflict_report"]["conflicts"][0]
    assert set(resolved["claimIds"]) == original_ids  # never dropped
    assert resolved["resolution"]["is_true_contradiction"] is True


def test_both_claim_ids_preserved_when_llm_explains_dimension_difference(package, retriever):
    conflict_report = _conflict_report_for_fibre(retriever)
    original_ids = set(conflict_report["conflicts"][0]["claimIds"])
    node = make_llm_conflict_resolver_node(package)
    mocked = ConflictResolution(
        is_true_contradiction=False, differing_dimension="evidence_strength", explanation="One is a systematic review, one is patient guidance."
    )
    with patch(
        "agent_core.llm_conflict_resolver.call_structured",
        return_value=(mocked, "ok", "anthropic", "claude-sonnet-4-5"),
    ):
        state = {"conflict_report": conflict_report, "visited_nodes": [], "trace": []}
        result = node(state)

    resolved = result["conflict_report"]["conflicts"][0]
    assert set(resolved["claimIds"]) == original_ids
    assert resolved["resolution"]["is_true_contradiction"] is False
    assert resolved["resolution"]["differing_dimension"] == "evidence_strength"


def test_falls_back_to_deterministic_report_when_unconfigured(package, retriever, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    conflict_report = _conflict_report_for_fibre(retriever)
    original_ids = set(conflict_report["conflicts"][0]["claimIds"])
    node = make_llm_conflict_resolver_node(package)
    state = {"conflict_report": conflict_report, "visited_nodes": [], "trace": []}
    result = node(state)

    resolved = result["conflict_report"]["conflicts"][0]
    assert set(resolved["claimIds"]) == original_ids  # preserved even without a model
    assert resolved["resolution"]["mode"] == "deterministic_fallback"


def test_no_conflicts_is_a_no_op(package):
    node = make_llm_conflict_resolver_node(package)
    state = {"conflict_report": {"has_conflicts": False, "conflicts": []}, "visited_nodes": [], "trace": []}
    result = node(state)
    assert result["conflict_report"]["conflicts"] == []
