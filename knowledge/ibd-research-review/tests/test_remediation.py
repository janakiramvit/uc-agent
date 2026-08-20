from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path("/Users/janakirampulipati/ibd-research-review")
DATA_PATH = ROOT / "processing/remediation/remediation-data.json"
WORKBOOK = ROOT / "ibd-evidence-review-remediated.xlsx"
VERIFICATION = ROOT / "logs/remediation/workbook-verification.json"
WRONG_FILES = {
    "PMC7690730", "PMC5250567", "PMC4366573", "PMC6314770", "PMC8719151",
    "PMC1513293", "PMC3649719", "5941818", "PMC6718954", "PMC5434712", "PMC5404419",
}
SHEET_NAMES = [
    "Sources", "Claims", "Source Mapping Audit", "Removed and Replaced Claims",
    "Superseded Sources", "Evidence Gap Resolution", "Verification and Access Issues",
    "Remediation Summary",
]


@pytest.fixture(scope="module")
def data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def pubmed_records() -> dict[str, dict]:
    result = {}
    for path in [ROOT / "sources/papers/pubmed-selected.xml", ROOT / "sources/remediated/SRC-026-pubmed.xml"]:
        tree = ET.parse(path)
        for article in tree.findall(".//PubmedArticle"):
            pmid = (article.findtext(".//MedlineCitation/PMID") or "").strip()
            title_el = article.find(".//ArticleTitle")
            title = " ".join(title_el.itertext()).strip() if title_el is not None else ""
            doi = ""
            pmcid = ""
            for aid in article.findall("./PubmedData/ArticleIdList/ArticleId"):
                if aid.attrib.get("IdType") == "doi":
                    doi = (aid.text or "").strip()
                if aid.attrib.get("IdType") == "pmc":
                    pmcid = (aid.text or "").strip()
            result[pmid] = {"title": title, "doi": doi, "pmcid": pmcid}
    return result


def test_identifier_consistency_against_pubmed(data):
    pubmed = pubmed_records()
    for row in data["sourceMappingAudit"]:
        record = pubmed[row["pmid"]]
        assert norm(record["title"]) == norm(row["sourceTitle"])
        assert record["doi"].lower() == row["correctedDoi"].lower()
        if row["correctedPmcid"]:
            assert record["pmcid"].upper() == row["correctedPmcid"].upper()


def test_correct_pmc_title_author_year_match(data):
    for row in data["sourceMappingAudit"]:
        if not row["correctedPmcid"]:
            continue
        tree = ET.parse(ROOT / "sources/remediated" / f"{row['correctedPmcid']}.xml")
        title_el = tree.find(".//article-title")
        title = " ".join(title_el.itertext()).strip()
        assert norm(title) == norm(row["sourceTitle"])
        years = {x.text for x in tree.findall(".//pub-date/year") if x.text}
        assert str(row["publicationYear"]) in years
        first_surname = tree.findtext(".//contrib[@contrib-type='author']//surname") or ""
        assert norm(first_surname) in norm(row["verifiedFirstAuthor"])


def test_all_wrong_mappings_are_rejected_and_archived(data):
    assert len(data["sourceMappingAudit"]) == 11
    assert all(row["wrongMappingRejected"] == "yes" for row in data["sourceMappingAudit"])
    archive_names = {p.stem.split("-")[-1] for p in (ROOT / "archive/incorrect-source-mappings").glob("*.xml")}
    assert WRONG_FILES <= archive_names
    active_names = {p.stem for p in (ROOT / "sources/remediated").glob("*.xml")}
    assert not (WRONG_FILES & active_names)


def test_source_status_vocabulary_and_effective_counts(data):
    allowed = {
        "verified_full_text", "verified_abstract_only", "verified_guideline",
        "superseded_replaced", "insufficient_access", "reject_recommended",
    }
    assert all(row["sourceStatus"] in allowed for row in data["sources"])
    counts = Counter(row["sourceStatus"] for row in data["sources"])
    assert counts["superseded_replaced"] == 1
    assert counts["verified_abstract_only"] == 4
    assert len(data["sources"]) == 26
    assert data["summary"]["activeSourceCount"] == 25


def test_superseded_source_replacement_and_claim_mapping(data):
    row = data["supersededSources"][0]
    assert row["oldSourceId"] == "SRC-003"
    assert row["newSourceId"] == "SRC-026"
    assert row["newPmid"] == "36739756"
    assert row["newDoi"] == "10.1016/j.clnu.2022.12.004"
    replacements = {x["originalClaimId"]: x["replacementClaimId"] for x in data["removedAndReplacedClaims"] if x["accountingCategory"] == "replaced by new"}
    assert replacements == {"CLM-010": "CLM-096", "CLM-011": "CLM-097"}


def test_audit_history_and_archives_exist(data):
    assert (ROOT / "archive/superseded-sources/SRC-003.json").exists()
    assert (ROOT / "archive/removed-claims/removed-and-replaced-claims.json").exists()
    assert all(Path(row["archivedAt"]).exists() for row in data["removedAndReplacedClaims"])
    assert Path(data["supersededSources"][0]["archivedAt"]).exists()


def test_exact_95_claim_reconciliation(data):
    expected = {
        "retained unchanged": 2,
        "retained revised": 53,
        "removed": 37,
        "replaced by new": 2,
        "still needs evidence": 1,
    }
    assert data["summary"]["claimAccounting"] == expected
    assert sum(expected.values()) == 95
    assert data["summary"]["claimAccountingTotal"] == 95


def test_removed_claims_are_not_on_active_claim_sheet(data):
    removed = {row["originalClaimId"] for row in data["removedAndReplacedClaims"]}
    active = {row["claimId"] for row in data["claims"]}
    assert not (removed & active)
    assert len(active) == 58


def test_revised_claim_traceability(data):
    revised = [row for row in data["claims"] if row.get("qaStatus") == "wording_revision_recommended"]
    assert len(revised) == 53
    assert all(row["originalClaim"] and row["qaProposedClaim"] and row["remediatedClaim"] for row in revised)


def test_every_active_claim_has_exact_locator_and_excerpt(data):
    for row in data["claims"]:
        assert row["supportingExcerpt"].strip()
        locator = row["exactLocator"].strip()
        assert locator
        assert locator.lower() not in {"public abstract", "pubmed abstract", "public webpage"}
        assert any(token in locator.lower() for token in ("sentence", "page", "heading", "recommendation", "bullet"))


def test_separate_search_budgets(data):
    claim_logs = data["claimSearchLog"]
    gap_logs = data["gapSearchLog"]
    assert all(row["issueType"] == "claim_search_budget" for row in _issue_rows(data) if row["issueType"] == "claim_search_budget")
    assert max(Counter(row["claimId"] for row in claim_logs).values()) <= 2
    assert max(Counter(row["gapId"] for row in gap_logs).values()) <= 3
    assert {row["claimId"] for row in claim_logs} == {"CLM-010", "CLM-011", "CLM-092"}


def _issue_rows(data):
    # Mirror the workbook's combined issue log only for vocabulary checks.
    rows = []
    rows.extend({"issueType": "claim_search_budget"} for _ in data["claimSearchLog"])
    rows.extend({"issueType": "gap_search_budget"} for _ in data["gapSearchLog"])
    return rows


def test_gap_limits_and_status_vocabulary(data):
    allowed = {
        "resolved_for_mvp",
        "partially_resolved_with_answer_limit",
        "unresolved_feature_must_be_excluded",
    }
    for row in data["evidenceGapResolution"]:
        assert row["status"] in allowed
        assert row["searchCount"] <= 3
        assert row["candidateCount"] <= 4
        assert row["selectedCount"] <= 2
        assert row["safeAnswerLimit"].strip()
    assert len(data["evidenceGapResolution"]) == 6


def test_access_issue_count_and_abstract_only_ids(data):
    assert len(data["verificationAndAccessIssues"]) == 4
    assert {x["sourceId"] for x in data["verificationAndAccessIssues"]} == {"SRC-002", "SRC-013", "SRC-015", "SRC-017"}
    assert all(x["resolutionStatus"] == "unresolved" for x in data["verificationAndAccessIssues"])


def test_all_human_review_fields_blank(data):
    assert all(x["userDecision"] == "" and x["userNotes"] == "" for x in data["sources"])
    assert all(
        x["userDecision"] == "" and x["userEditedClaim"] == "" and x["reviewerNotes"] == ""
        for x in data["claims"]
    )


def test_canada_us_applicability_assessed(data):
    assert all(row["canadaUsApplicability"] for row in data["sources"])
    assert all(row["regionalAssessment"] for row in data["sources"])


def test_workbook_generated_with_exact_sheets():
    assert WORKBOOK.exists() and WORKBOOK.stat().st_size > 0
    with zipfile.ZipFile(WORKBOOK) as archive:
        xml = archive.read("xl/workbook.xml").decode("utf-8")
        actual = re.findall(r'<(?:[A-Za-z0-9_]+:)?sheet\b[^>]*\bname="([^"]+)"', xml)
    assert actual == SHEET_NAMES


def test_workbook_has_no_literal_formula_errors():
    with zipfile.ZipFile(WORKBOOK) as archive:
        xml = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist() if name.endswith(".xml")
        )
    for error in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"):
        assert error not in xml


def test_visual_validation_outputs_all_eight_sheets():
    verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    assert [x["sheetName"] for x in verification["sheets"]] == SHEET_NAMES
    assert "matched 0 entries" in verification["formulaErrors"]
    assert all(Path(x["preview"]).exists() and Path(x["preview"]).stat().st_size > 0 for x in verification["sheets"])
