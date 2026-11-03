import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import pytest

from agent_core.safety_rules import SafetyBoundary, check_safety_boundaries


@pytest.mark.parametrize("q", [
    "I have severe bloody diarrhea, fever and severe abdominal pain right now",
    "I'm passing a lot of blood, what does the evidence say?",
    "severe stomach pain and I fainted",
    "Should I go to the ER?",
    "chest pain and ulcerative colitis",
])
def test_red_flag_queries_route_to_urgent_care(q):
    r = check_safety_boundaries(q)
    assert r.triggered and r.boundary is SafetyBoundary.URGENT_CARE
    assert "emergency" in r.message.lower()


@pytest.mark.parametrize("q", [
    "What does the evidence say about diet in ulcerative colitis?",
    "Is alcohol associated with UC flares?",
    "What is the evidence for colectomy risk in UC?",
])
def test_normal_queries_do_not_trigger_urgent_care(q):
    assert check_safety_boundaries(q).boundary is not SafetyBoundary.URGENT_CARE
