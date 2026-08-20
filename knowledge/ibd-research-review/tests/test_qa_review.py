from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DATA = ROOT / "processing/checkpoints/research-data.json"
QA_DATA = ROOT / "processing/checkpoints/qa-review.json"
QA_WORKBOOK = ROOT / "ibd-evidence-review-qa.xlsx"
BACKUP_DIR = ROOT / "backups/2026-07-29-evidence-qa"


@pytest.fixture(scope="module")
def original():
    return json.loads(ORIGINAL_DATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def qa():
    return json.loads(QA_DATA.read_text(encoding="utf-8"))


def test_original_ids_are_preserved(original, qa):
    assert [row["sourceId"] for row in qa["sources"]] == [row["sourceId"] for row in original["sources"]]
    assert [row["claimId"] for row in qa["claims"]] == [row["claimId"] for row in original["claims"]]
    assert [row["conflictId"] for row in qa["conflicts"]] == [row["conflictId"] for row in original["conflicts"]]


def test_original_claims_are_preserved(original, qa):
    originals = {row["claimId"]: row["claim"] for row in original["claims"]}
    assert all(row["originalClaim"] == originals[row["claimId"]] for row in qa["claims"])


def test_all_conflicts_have_one_valid_primary_classification(qa):
    allowed = {
        "true_conflict", "different_condition", "different_disease_state",
        "different_population", "different_intervention", "different_comparator",
        "different_outcome", "symptom_vs_inflammation", "association_vs_intervention",
        "guideline_vs_primary_study", "older_vs_newer_evidence",
        "indirect_general_population_evidence", "duplicate_or_near_duplicate",
        "insufficient_information", "not_materially_comparable",
    }
    assert len(qa["conflicts"]) == 80
    assert all(row["primaryClassification"] in allowed for row in qa["conflicts"])
    assert all(isinstance(row["primaryClassification"], str) and row["primaryClassification"] for row in qa["conflicts"])


def test_abstract_only_confidence_handling(qa):
    assert len(qa["abstractOnlyReview"]) == 9
    remaining = {row["sourceId"] for row in qa["abstractOnlyReview"] if row["fullTextBecameAvailable"] == "No"}
    assert remaining == {"SRC-002", "SRC-015", "SRC-017"}
    for claim in qa["claims"]:
        if claim["sourceId"] in remaining:
            assert claim["confidence"] != "high"


def test_blocked_sources_are_verified_without_automatic_approval(qa):
    blocked = [row for row in qa["accessIssues"] if row["sourceId"] in {"SRC-021", "SRC-022"}]
    assert len(blocked) == 2
    assert all(row["resolutionStatus"] == "resolved" for row in blocked)
    assert all(row["userDecision"] == "" for row in qa["sources"] if row["sourceId"] in {"SRC-021", "SRC-022"})


def test_human_review_fields_are_blank(qa):
    assert all(row["userDecision"] == "" and row["userNotes"] == "" for row in qa["sources"])
    assert all(
        row["userDecision"] == "" and row["userEditedClaim"] == "" and row["reviewerNotes"] == ""
        for row in qa["claims"]
    )


def test_backup_creation():
    expected = {"ibd-evidence-review.xlsx", "source-verification-report.md", "run-summary.json"}
    assert expected == {path.name for path in BACKUP_DIR.iterdir()}
    assert all((BACKUP_DIR / name).stat().st_size > 0 for name in expected)


def test_workbook_contains_required_sheets():
    assert QA_WORKBOOK.exists() and QA_WORKBOOK.stat().st_size > 0
    with zipfile.ZipFile(QA_WORKBOOK) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
    for sheet in (
        "Sources", "Claims", "Conflict Review", "Coverage Matrix",
        "Abstract-Only Review", "Access and Verification Issues",
        "Rejected Candidates", "QA Summary",
    ):
        assert f'name="{sheet}"' in workbook_xml


def test_workbook_has_no_literal_formula_errors():
    with zipfile.ZipFile(QA_WORKBOOK) as archive:
        xml_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )
    for error in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"):
        assert error not in xml_text


def test_visual_validation_outputs_all_sheets():
    verification = json.loads((ROOT / "logs/qa-workbook-verification.json").read_text(encoding="utf-8"))
    assert len(verification["sheets"]) == 8
    assert all(Path(row["preview"]).exists() and Path(row["preview"]).stat().st_size > 0 for row in verification["sheets"])
