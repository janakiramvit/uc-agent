"""Tests for the memory layers (memory/).

Covers: session/preference store isolation, clearing, and the hard
guard that neither store can ever hold diagnosis/flare/medication-
change/unsupported-conclusion content.
"""

from __future__ import annotations

import json

import pytest

from memory import clear_all_memory
from memory.guard import ClinicalContentRejected, validate_before_store
from memory.preference_memory import UserPreferenceMemory
from memory.session_memory import SessionMemory


# --- SessionMemory basics ---------------------------------------------------------


def test_session_memory_defaults_are_empty():
    mem = SessionMemory()
    assert mem.current_question is None
    assert mem.retrieved_claim_ids == []
    assert mem.turns == []
    assert mem.safety_warnings_shown == []


def test_session_memory_records_question_claims_and_turns():
    mem = SessionMemory()
    mem.set_current_question("What does the evidence say about fibre?")
    mem.set_retrieved_claim_ids(["CLM-014", "CLM-094"])
    mem.add_turn("What does the evidence say about fibre?", "Based on the reviewed evidence...")
    mem.add_safety_warning("This prototype cannot diagnose ulcerative colitis...")

    assert mem.current_question == "What does the evidence say about fibre?"
    assert mem.retrieved_claim_ids == ["CLM-014", "CLM-094"]
    assert len(mem.turns) == 1
    assert mem.turns[0]["question"] == "What does the evidence say about fibre?"
    assert len(mem.safety_warnings_shown) == 1


def test_session_memory_dedupes_safety_warnings():
    mem = SessionMemory()
    mem.add_safety_warning("same warning")
    mem.add_safety_warning("same warning")
    assert mem.safety_warnings_shown == ["same warning"]


def test_session_memory_clear_empties_all_fields():
    mem = SessionMemory()
    mem.set_current_question("q")
    mem.set_retrieved_claim_ids(["CLM-014"])
    mem.add_turn("q", "a")
    mem.add_safety_warning("w")

    mem.clear()

    assert mem.current_question is None
    assert mem.retrieved_claim_ids == []
    assert mem.turns == []
    assert mem.safety_warnings_shown == []


# --- session isolation ---------------------------------------------------------


def test_two_session_memories_do_not_leak_into_each_other():
    session_a = SessionMemory(backing={})
    session_b = SessionMemory(backing={})

    session_a.set_current_question("session A question")
    session_a.set_retrieved_claim_ids(["CLM-014"])
    session_a.add_turn("session A question", "session A answer")

    assert session_b.current_question is None
    assert session_b.retrieved_claim_ids == []
    assert session_b.turns == []


def test_session_memory_is_never_written_to_disk(tmp_path):
    """Sanity check: SessionMemory has no path/file concept at all --
    there is no way to construct one that touches disk."""
    mem = SessionMemory()
    assert not hasattr(mem, "path")
    assert not hasattr(mem, "_save")


# --- UserPreferenceMemory ---------------------------------------------------------


def test_preference_memory_defaults(tmp_path):
    pref = UserPreferenceMemory(path=tmp_path / "prefs.json")
    assert pref.answer_length == "standard"
    assert pref.language == "en"
    assert pref.citations_expanded_default is False


def test_preference_memory_set_and_persist_across_reload(tmp_path):
    path = tmp_path / "prefs.json"
    pref = UserPreferenceMemory(path=path)
    pref.set_answer_length("detailed")
    pref.set_language("es")
    pref.set_citations_expanded_default(True)

    assert path.exists()

    reloaded = UserPreferenceMemory(path=path)
    assert reloaded.answer_length == "detailed"
    assert reloaded.language == "es"
    assert reloaded.citations_expanded_default is True


def test_preference_memory_rejects_invalid_answer_length(tmp_path):
    pref = UserPreferenceMemory(path=tmp_path / "prefs.json")
    with pytest.raises(ValueError):
        pref.set_answer_length("extremely long and rambling")


def test_preference_memory_persists_under_project_memory_store_dir():
    default_path = UserPreferenceMemory().path
    assert "memory_store" in str(default_path)
    assert "data" not in default_path.parts  # never the evidence data/ dir


def test_preference_memory_clear_resets_to_defaults(tmp_path):
    path = tmp_path / "prefs.json"
    pref = UserPreferenceMemory(path=path)
    pref.set_answer_length("short")
    pref.set_language("fr")
    pref.set_citations_expanded_default(True)

    pref.clear()

    assert pref.answer_length == "standard"
    assert pref.language == "en"
    assert pref.citations_expanded_default is False
    with path.open() as f:
        on_disk = json.load(f)
    assert on_disk["answer_length"] == "standard"


# --- clear_all_memory ---------------------------------------------------------


def test_clear_all_memory_empties_both_stores(tmp_path):
    session = SessionMemory()
    session.set_current_question("q")
    session.add_turn("q", "a")

    pref = UserPreferenceMemory(path=tmp_path / "prefs.json")
    pref.set_answer_length("detailed")

    clear_all_memory(session, pref)

    assert session.current_question is None
    assert session.turns == []
    assert pref.answer_length == "standard"


def test_clear_all_memory_tolerates_missing_session_memory(tmp_path):
    pref = UserPreferenceMemory(path=tmp_path / "prefs.json")
    pref.set_answer_length("short")
    clear_all_memory(None, pref)  # should not raise
    assert pref.answer_length == "standard"


# --- the hard clinical-content guard ---------------------------------------------------------


@pytest.mark.parametrize(
    "blocked_text",
    [
        "You have ulcerative colitis.",
        "Your UC is active right now.",
        "You will flare next week.",
        "You should stop taking your medication.",
        "This is clinically approved and proven to cure UC.",
    ],
)
def test_validate_before_store_rejects_clinical_content(blocked_text):
    with pytest.raises(ClinicalContentRejected):
        validate_before_store(blocked_text)


def test_validate_before_store_accepts_safe_content():
    assert validate_before_store("What does the evidence say about fibre?") == "What does the evidence say about fibre?"
    assert validate_before_store(["CLM-014", "CLM-094"]) == ["CLM-014", "CLM-094"]


def test_session_memory_rejects_diagnosis_like_string_in_question():
    """The guard test required by the spec: try to stuff a diagnosis-like
    string into memory and assert it is rejected."""
    mem = SessionMemory()
    with pytest.raises(ClinicalContentRejected):
        mem.set_current_question("You have ulcerative colitis and should stop taking your medication.")
    # Nothing was stored -- the field remains at its default.
    assert mem.current_question is None


def test_session_memory_rejects_diagnosis_like_string_in_turn():
    mem = SessionMemory()
    with pytest.raises(ClinicalContentRejected):
        mem.add_turn("some question", "Your UC is active and you will flare soon.")
    assert mem.turns == []


def test_preference_memory_rejects_diagnosis_like_language_tag(tmp_path):
    pref = UserPreferenceMemory(path=tmp_path / "prefs.json")
    with pytest.raises(ClinicalContentRejected):
        pref.set_language("You have ulcerative colitis")
    assert pref.language == "en"
