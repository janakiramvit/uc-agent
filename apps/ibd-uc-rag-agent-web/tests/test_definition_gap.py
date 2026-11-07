import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

import pytest

from agent_core.safety_rules import is_known_unsupported_topic


@pytest.mark.parametrize("q", ["What is ulcerative colitis?", "Define UC", "explain ulcerative colitis", "what is UC"])
def test_definition_questions_are_a_known_coverage_gap(q):
    assert is_known_unsupported_topic(q)


@pytest.mark.parametrize("q", [
    "What is the evidence for fibre in ulcerative colitis?",
    "Is alcohol associated with UC flares?",
    "what are the dietary recommendations for ulcerative colitis",
])
def test_covered_topics_not_blocked(q):
    assert not is_known_unsupported_topic(q)
