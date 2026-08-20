from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest

ROOT = Path("/Users/janakirampulipati/ibd-research-review")
PREVIOUS = ROOT / "processing/remediation/remediation-data.json"
FINAL = ROOT / "processing/final-remediation/final-remediation-data.json"
WORKBOOK = ROOT / "ibd-evidence-review-final-remediation.xlsx"
VERIFICATION = ROOT / "logs/final-remediation/workbook-verification.json"
SHEETS = [
    "Sources",
    "Claims",
    "Locator Corrections",
    "CLM-097 Remediation",
    "Unresolved Claims",
    "Removed or Replaced Claims",
    "Validation Summary",
    "Final Remediation Summary",
]


@pytest.fixture(scope="module")
def previous():
    return json.loads(PREVIOUS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def final():
    return json.loads(FINAL.read_text(encoding="utf-8"))


def claims_by_id(data):
    return {row["claimId"]: row for row in data["claims"]}


def test_ecco_supporting_excerpts_are_preserved(previous, final):
    old = claims_by_id(previous)
    new = claims_by_id(final)
    for claim_id in [f"CLM-{number:03d}" for number in range(81, 87)]:
        assert new[claim_id]["supportingExcerpt"] == old[claim_id]["supportingExcerpt"]


def test_ecco_locators_are_precise_and_numbered(final):
    rows = {row["claimId"]: row for row in final["locatorCorrections"]}
    assert set(rows) == {f"CLM-{number:03d}" for number in range(81, 87)}
    assert "Section 3" in rows["CLM-081"]["correctedLocator"]
    assert "Statement 1" in rows["CLM-081"]["correctedLocator"]
    assert "Section 4.1" in rows["CLM-082"]["correctedLocator"]
    assert "opening paragraph" in rows["CLM-082"]["correctedLocator"]
    assert "Section 4.3.2" in rows["CLM-083"]["correctedLocator"]
    assert "Statement 21.1" in rows["CLM-083"]["correctedLocator"]
    assert "Section 3.8.2.1" in rows["CLM-084"]["correctedLocator"]
    assert "Practice Point 2A, sentence 1" in rows["CLM-084"]["correctedLocator"]
    assert "Practice Point 2A, sentence 3" in rows["CLM-085"]["correctedLocator"]
    assert "Section 3.8.2.2" in rows["CLM-086"]["correctedLocator"]
    assert "Practice Point 2B, sentence 1" in rows["CLM-086"]["correctedLocator"]
    assert all(row["verificationStatus"].startswith("PASS") for row in rows.values())


def test_ecco_authoritative_captures_are_nonempty_and_contain_passages(final):
    for row in final["locatorCorrections"]:
        capture = Path(row["localVerificationCopy"])
        assert capture.exists() and capture.stat().st_size > 0
        text = " ".join(capture.read_text(encoding="utf-8", errors="ignore").split())
        anchor = " ".join(row["authoritativePassage"].split())[:80]
        assert anchor in text


def test_clm083_preserves_required_limitations(final):
    claim = claims_by_id(final)["CLM-083"]["remediatedClaim"].lower()
    assert "no data support" in claim
    assert "mechanism-based reasoning" in claim
    assert "obstructive symptoms" in claim
    assert "not individualized treatment advice" in claim


def test_clm097_is_atomic_and_directly_supported(final):
    claim = claims_by_id(final)["CLM-097"]
    text = claim["remediatedClaim"].lower()
    assert "no oral ibd diet" in text
    assert "exclusion-diet approaches" not in text
    assert "long-term" not in text
    assert "but it supports" not in text
    assert claim["supportingExcerpt"] == claim["authoritativePassage"]
    assert "Recommendation 15 commentary" in claim["exactLocator"]
    assert claim["verificationStatus"].startswith("PASS")


def test_clm097_split_claims_are_unique_atomic_and_supported(final):
    rows = claims_by_id(final)
    ids = [row["claimId"] for row in final["claims"]]
    assert len(ids) == len(set(ids))
    assert {"CLM-098", "CLM-099", "CLM-100"} <= set(ids)
    for claim_id in ("CLM-098", "CLM-099", "CLM-100"):
        row = rows[claim_id]
        assert row["splitFromClaimId"] == "CLM-097"
        assert row["sourceId"] == "SRC-026"
        assert row["supportingExcerpt"] == row["authoritativePassage"]
        assert "journal page 357" in row["exactLocator"]
        assert row["verificationStatus"] == "direct_support_verified_official_pdf"
    assert "pediatric" in rows["CLM-098"]["remediatedClaim"].lower()
    assert "adults" in rows["CLM-099"]["remediatedClaim"].lower()
    assert "not yet available" in rows["CLM-100"]["remediatedClaim"].lower()


def test_clm092_remains_unresolved_and_export_excluded(final):
    claim = claims_by_id(final)["CLM-092"]
    assert claim["evidenceStatus"] == "still_needs_evidence"
    assert claim["finalQaEligibility"] == "unresolved_not_approval_ready"
    assert claim["futureApprovedExportEligibility"] == "excluded_until_evidence_resolved_and_explicitly_approved"
    assert claim["missingEvidenceExplanation"]
    assert [row["claimId"] for row in final["unresolvedClaims"]] == ["CLM-092"]


def test_active_claim_counts_reconcile(final):
    ready = [row for row in final["claims"] if row["finalQaEligibility"] == "ready_for_final_independent_qa"]
    unresolved = [row for row in final["claims"] if row["evidenceStatus"] == "still_needs_evidence"]
    assert len(ready) == 60
    assert len(unresolved) == 1
    assert len(final["claims"]) == 61
    assert final["summary"]["newSplitClaimsCreated"] == 3
    assert final["summary"]["cumulativeOriginalClaimsRemoved"] == 37


def test_every_active_claim_references_an_active_source(final):
    active_sources = {
        row["sourceId"] for row in final["sources"]
        if row["sourceStatus"] != "superseded_replaced"
    }
    assert len(active_sources) == 25
    assert all(row["sourceId"] in active_sources for row in final["claims"])
    assert all(row["sourceId"] != "SRC-003" for row in final["claims"])


def test_no_active_claim_has_a_generic_locator(final):
    exact_generic = {"abstract", "webpage", "full text", "ecco section", "public abstract", "public webpage"}
    required_tokens = ("sentence", "page", "heading", "recommendation", "statement", "practice point", "bullet", "paragraph", "section")
    for row in final["claims"]:
        locator = row["exactLocator"].strip().lower()
        assert locator not in exact_generic
        assert 'heading "abstract"' not in locator
        assert any(token in locator for token in required_tokens), (row["claimId"], locator)


def test_human_review_fields_remain_blank(final):
    assert all(row["userDecision"] == "" and row["userNotes"] == "" for row in final["sources"])
    assert all(
        row["userDecision"] == "" and row["userEditedClaim"] == "" and row["reviewerNotes"] == ""
        for row in final["claims"]
    )


def test_workbook_has_exact_requested_sheets():
    assert WORKBOOK.exists() and WORKBOOK.stat().st_size > 0
    with zipfile.ZipFile(WORKBOOK) as archive:
        xml = archive.read("xl/workbook.xml").decode("utf-8")
    actual = re.findall(r'<(?:[A-Za-z0-9_]+:)?sheet\b[^>]*\bname="([^"]+)"', xml)
    assert actual == SHEETS


def test_workbook_has_no_literal_formula_errors():
    with zipfile.ZipFile(WORKBOOK) as archive:
        xml = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        )
    for error in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"):
        assert error not in xml


def test_workbook_formula_scan_and_visual_validation():
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    assert "matched 0 entries" in verification["formulaErrors"]
    assert [row["sheetName"] for row in verification["sheets"]] == SHEETS
    assert all(
        Path(row["preview"]).exists() and Path(row["preview"]).stat().st_size > 0
        for row in verification["sheets"]
    )
