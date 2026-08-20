from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/janakirampulipati/ibd-research-review")
INPUT = ROOT / "processing/remediation/remediation-data.json"
OUTPUT = ROOT / "processing/final-remediation/final-remediation-data.json"

ECCO_021_URL = "https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055"
ECCO_022_URL = "https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895"
ESPEN_URL = "https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf"

ECCO_021_CAPTURE = ROOT / "sources/final-remediation/SRC-021-authoritative.html"
ECCO_022_CAPTURE = ROOT / "sources/final-remediation/SRC-022-authoritative.html"
ESPEN_CAPTURE = ROOT / "sources/remediated/SRC-026-ESPEN-2023.pdf"

LOCATOR_FIXES = {
    "CLM-081": {
        "sourceUrl": ECCO_021_URL,
        "correctedLocator": (
            'Official ECCO consensus article — Section 3, "Translation and execution of dietary management"; '
            'Statement 1; paragraph beginning "Statement 1: In the absence of a specific dietary intervention..."'
        ),
        "authoritativePassage": (
            "Statement 1: In the absence of a specific dietary intervention that is recommended by an IBD "
            "healthcare professional, healthy eating guidelines should be followed by people with IBD, as "
            "recommended for the general population. (EL5) (Consensus: 100%)"
        ),
        "capture": str(ECCO_021_CAPTURE),
        "remediationNote": "Replaced false Abstract locator with Section 3, Statement 1. Claim wording unchanged.",
    },
    "CLM-082": {
        "sourceUrl": ECCO_021_URL,
        "correctedLocator": (
            'Official ECCO consensus article — Section 4.1, "Dietary therapy to induce and maintain remission '
            'of IBD"; opening paragraph; sentence beginning "Most evidence for dietary interventions..."'
        ),
        "authoritativePassage": (
            "Most evidence for dietary interventions was of low quality, with few studies measuring endoscopic, "
            "radiological, or biochemical end points or durability of response."
        ),
        "capture": str(ECCO_021_CAPTURE),
        "remediationNote": "Replaced false Abstract locator with Section 4.1 opening paragraph. Claim wording unchanged.",
    },
    "CLM-083": {
        "sourceUrl": ECCO_021_URL,
        "correctedLocator": (
            'Official ECCO consensus article — Section 4.3.2, "Strictures"; Statement 21.1, paragraph 1; '
            'paragraph beginning "Statement 21.1: While there are no data supporting..."'
        ),
        "authoritativePassage": (
            "Statement 21.1: While there are no data supporting a modified or low-fiber diet to manage "
            "stricturing Crohn’s disease (CD), mechanism-based reasoning suggests that a diet low in bulking "
            "fiber in people with stricturing CD and obstructive symptoms might reduce the risk of developing "
            "intestinal obstruction. (EL5) (Consensus: 100%)"
        ),
        "capture": str(ECCO_021_CAPTURE),
        "remediationNote": (
            "Replaced false Abstract locator with Section 4.3.2, Statement 21.1. Narrowed the claim to preserve "
            "the no-data, mechanism-based, and obstructive-symptom limitations."
        ),
        "narrowedClaim": (
            "The ECCO consensus states that no data support a modified or low-fiber diet to manage stricturing "
            "Crohn’s disease; based on mechanism-based reasoning, a low-bulking-fiber diet in people with "
            "stricturing Crohn’s disease and obstructive symptoms might reduce the risk of intestinal "
            "obstruction. This is source-attributed guidance, not individualized treatment advice."
        ),
    },
    "CLM-084": {
        "sourceUrl": ECCO_022_URL,
        "correctedLocator": (
            'Official ECCO guideline article — Section 3.8.2.1, "Dietary therapy for the induction of remission '
            'in CD"; Practice Point 2A, sentence 1'
        ),
        "authoritativePassage": (
            "Practice Point 2A. There is emerging evidence that dietary therapies may be beneficial in reducing "
            "the inflammatory burden in CD."
        ),
        "capture": str(ECCO_022_CAPTURE),
        "remediationNote": "Replaced false Abstract locator with Section 3.8.2.1, Practice Point 2A, sentence 1.",
    },
    "CLM-085": {
        "sourceUrl": ECCO_022_URL,
        "correctedLocator": (
            'Official ECCO guideline article — Section 3.8.2.1, "Dietary therapy for the induction of remission '
            'in CD"; Practice Point 2A, sentence 3'
        ),
        "authoritativePassage": (
            "Dietary intervention should primarily be considered based on disease activity, the patient’s "
            "motivation, the current evidence, and the availability of dietetic support."
        ),
        "capture": str(ECCO_022_CAPTURE),
        "remediationNote": "Replaced false Abstract locator with Section 3.8.2.1, Practice Point 2A, sentence 3.",
    },
    "CLM-086": {
        "sourceUrl": ECCO_022_URL,
        "correctedLocator": (
            'Official ECCO guideline article — Section 3.8.2.2, "Dietary therapy for the maintenance of remission '
            'in CD"; Practice Point 2B, sentence 1'
        ),
        "authoritativePassage": (
            "Practice Point 2B. Partial enteral nutrition might be considered as a strategy for maintaining "
            "remission, with or without additional medication, in a subset of patients who are willing and able "
            "to tolerate the formula with routine monitoring. [Consensus: 100%]"
        ),
        "capture": str(ECCO_022_CAPTURE),
        "remediationNote": "Replaced false Abstract locator with Section 3.8.2.2, Practice Point 2B, sentence 1.",
    },
}


def verify_capture(path: Path, passages: list[str]) -> None:
    assert path.exists() and path.stat().st_size > 0, f"Missing authoritative capture: {path}"
    text = " ".join(path.read_text(encoding="utf-8", errors="ignore").split())
    for passage in passages:
        anchor = " ".join(passage.split())[:80]
        assert anchor in text, f"Passage anchor not found in {path.name}: {anchor}"


def make_split_claim(template: dict, claim_id: str, claim: str, excerpt: str, locator: str, note: str) -> dict:
    row = deepcopy(template)
    row.update({
        "claimId": claim_id,
        "sourceId": "SRC-026",
        "replacesClaimId": "",
        "splitFromClaimId": "CLM-097",
        "originalClaim": template["remediatedClaim"],
        "qaProposedClaim": "",
        "remediatedClaim": claim,
        "remediationReason": "Split from the pre-remediation multi-assertion CLM-097 to preserve one atomic idea.",
        "revisionReason": "",
        "supportingExcerpt": excerpt,
        "authoritativePassage": excerpt,
        "exactLocator": locator,
        "sourceUrl": ESPEN_URL,
        "verificationStatus": "direct_support_verified_official_pdf",
        "finalQaEligibility": "ready_for_final_independent_qa",
        "futureApprovedExportEligibility": "pending_explicit_human_approval",
        "evidenceStatus": "ready_for_human_review",
        "humanReviewStatus": "pending_human_review",
        "userDecision": "",
        "userEditedClaim": "",
        "reviewerNotes": "",
        "finalRemediationNote": note,
    })
    return row


def main() -> None:
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    sources = deepcopy(data["sources"])
    claims = deepcopy(data["claims"])

    verify_capture(
        ECCO_021_CAPTURE,
        [
            LOCATOR_FIXES["CLM-081"]["authoritativePassage"],
            LOCATOR_FIXES["CLM-082"]["authoritativePassage"],
            LOCATOR_FIXES["CLM-083"]["authoritativePassage"],
        ],
    )
    verify_capture(
        ECCO_022_CAPTURE,
        [
            LOCATOR_FIXES["CLM-084"]["authoritativePassage"],
            LOCATOR_FIXES["CLM-085"]["authoritativePassage"],
            LOCATOR_FIXES["CLM-086"]["authoritativePassage"],
        ],
    )
    assert ESPEN_CAPTURE.exists() and ESPEN_CAPTURE.stat().st_size > 0

    source_updates = {
        "SRC-021": (ECCO_021_URL, ECCO_021_CAPTURE),
        "SRC-022": (ECCO_022_URL, ECCO_022_CAPTURE),
    }
    active_source_ids = set()
    source_title_by_id = {}
    for source in sources:
        source_title_by_id[source["sourceId"]] = source["sourceTitle"]
        if source["sourceStatus"] != "superseded_replaced":
            active_source_ids.add(source["sourceId"])
        if source["sourceId"] in source_updates:
            url, capture = source_updates[source["sourceId"]]
            source["sourceUrl"] = url
            source["alternativeAccessUrl"] = url
            source["localVerificationCopy"] = str(capture)
            source["locatorVerificationStatus"] = "numbered_sections_verified_against_nonempty_authoritative_capture"
            source["licensingAccessNote"] = (
                "Official public article captured for verification only; downstream reuse rights were not assessed."
            )
        source["userDecision"] = ""
        source["userNotes"] = ""

    locator_corrections = []
    claim_by_id = {claim["claimId"]: claim for claim in claims}
    for claim_id, fix in LOCATOR_FIXES.items():
        claim = claim_by_id[claim_id]
        old_locator = claim["exactLocator"]
        original_excerpt = claim["supportingExcerpt"]
        claim["exactLocator"] = fix["correctedLocator"]
        claim["sourceUrl"] = fix["sourceUrl"]
        claim["authoritativePassage"] = fix["authoritativePassage"]
        claim["verificationStatus"] = "direct_support_verified_official_ecco_article"
        claim["finalQaEligibility"] = "ready_for_final_independent_qa"
        claim["futureApprovedExportEligibility"] = "pending_explicit_human_approval"
        claim["finalRemediationNote"] = fix["remediationNote"]
        if fix.get("narrowedClaim"):
            claim["remediatedClaim"] = fix["narrowedClaim"]
        claim["userDecision"] = ""
        claim["userEditedClaim"] = ""
        claim["reviewerNotes"] = ""
        assert claim["supportingExcerpt"] == original_excerpt
        locator_corrections.append({
            "claimId": claim_id,
            "sourceId": claim["sourceId"],
            "preservedSupportingExcerpt": original_excerpt,
            "oldLocator": old_locator,
            "correctedLocator": fix["correctedLocator"],
            "authoritativePassage": fix["authoritativePassage"],
            "sourceUrl": fix["sourceUrl"],
            "localVerificationCopy": fix["capture"],
            "verificationStatus": "PASS_direct_support_and_numbered_locator",
            "remediationNote": fix["remediationNote"],
            "humanReviewStatus": "pending_human_review",
        })

    clm097 = claim_by_id["CLM-097"]
    pre_remediation_097 = clm097["remediatedClaim"]
    clm097.update({
        "remediatedClaim": (
            "The 2023 ESPEN guideline states that no oral IBD diet can be generally recommended to promote "
            "remission in patients with active IBD."
        ),
        "supportingExcerpt": (
            "Therefore, no “oral IBD diet” can be generally recommended to promote remission in patients with "
            "IBD with active disease."
        ),
        "authoritativePassage": (
            "Therefore, no “oral IBD diet” can be generally recommended to promote remission in patients with "
            "IBD with active disease."
        ),
        "exactLocator": (
            'Official ESPEN PDF — journal page 357, Section 5 "Dietetic recommendations in active disease"; '
            'Recommendation 15 commentary, final paragraph beginning "Therefore, no oral IBD diet..."'
        ),
        "sourceUrl": ESPEN_URL,
        "verificationStatus": "PASS_direct_support_verified_official_pdf",
        "finalQaEligibility": "ready_for_final_independent_qa",
        "futureApprovedExportEligibility": "pending_explicit_human_approval",
        "finalRemediationNote": (
            "Narrowed to the single assertion directly supported by the displayed excerpt. The other supported "
            "ideas were split into CLM-098 through CLM-100."
        ),
        "userDecision": "",
        "userEditedClaim": "",
        "reviewerNotes": "",
    })

    split_claims = [
        make_split_claim(
            clm097,
            "CLM-098",
            "The 2023 ESPEN guideline states that a Crohn’s disease exclusion diet plus partial enteral nutrition "
            "should be considered as an alternative to exclusive enteral nutrition in pediatric patients with "
            "mild-to-moderate Crohn’s disease to achieve remission.",
            "CD exclusion diet (plus partial EN) should be considered as an alternative to exclusive EN in "
            "pediatric patients with mild to moderate CD to achieve remission.",
            'Official ESPEN PDF — journal page 357, Section 5 "Dietetic recommendations in active disease"; '
            "Recommendation 16",
            "Created as a pediatric-population atomic split from the former broad CLM-097.",
        ),
        make_split_claim(
            clm097,
            "CLM-099",
            "The 2023 ESPEN guideline states that, in adults with mild-to-moderate active Crohn’s disease, a "
            "Crohn’s disease exclusion diet can be considered with or without enteral nutrition.",
            "In adult patients, a CD exclusion diet can be considered with or without EN in mild to moderate "
            "active CD.",
            'Official ESPEN PDF — journal page 357, Section 5 "Dietetic recommendations in active disease"; '
            "Recommendation 17",
            "Created as an adult-population atomic split from the former broad CLM-097.",
        ),
        make_split_claim(
            clm097,
            "CLM-100",
            "The 2023 ESPEN guideline states that data on long-term effectiveness and the possible risk of "
            "nutritional deficiencies or eating-behavior disturbances from long-term exclusion-diet use are "
            "not yet available.",
            "Data on long-term effectiveness and possible risk of nutritional deficiencies or eating behavior "
            "disturbances due to long-term use of exclusion diets are not (yet) available.",
            'Official ESPEN PDF — journal page 357, Section 5 "Dietetic recommendations in active disease"; '
            "commentary for Recommendations 16 and 17, paragraph ending immediately before Recommendation 18",
            "Created as an evidence-limitation atomic split from the former broad CLM-097.",
        ),
    ]
    claims.extend(split_claims)

    clm092 = claim_by_id["CLM-092"]
    clm092.update({
        "evidenceStatus": "still_needs_evidence",
        "finalQaEligibility": "unresolved_not_approval_ready",
        "futureApprovedExportEligibility": "excluded_until_evidence_resolved_and_explicitly_approved",
        "missingEvidenceExplanation": (
            "The webpage version date remains unconfirmed, and the broad claim that disordered eating is "
            "associated with worse disease outcomes lacks sufficiently specific, directly appraised evidence "
            "in this package."
        ),
        "finalRemediationNote": "Status preserved without additional research, as required.",
        "userDecision": "",
        "userEditedClaim": "",
        "reviewerNotes": "",
    })

    for claim in claims:
        claim["sourceTitle"] = claim.get("sourceTitle") or source_title_by_id[claim["sourceId"]]
        if claim["claimId"] != "CLM-092":
            claim.setdefault("finalQaEligibility", "ready_for_final_independent_qa")
            claim.setdefault("futureApprovedExportEligibility", "pending_explicit_human_approval")
        claim["userDecision"] = ""
        claim["userEditedClaim"] = ""
        claim["reviewerNotes"] = ""
        assert claim["sourceId"] in active_source_ids

    ids = [claim["claimId"] for claim in claims]
    assert len(ids) == len(set(ids))
    assert set(ids[-3:]) == {"CLM-098", "CLM-099", "CLM-100"}

    clm097_remediation = [
        {
            "assertionId": "CLM-097-A",
            "preRemediationAssertion": "No single oral diet can be recommended for all active IBD.",
            "supportStatus": "supported",
            "finalDisposition": "Retained as narrowed atomic CLM-097",
            "claimId": "CLM-097",
            "supportingExcerpt": clm097["supportingExcerpt"],
            "exactLocator": clm097["exactLocator"],
            "sourceUrl": ESPEN_URL,
            "verificationStatus": "PASS_direct_support",
        },
        {
            "assertionId": "CLM-097-B1",
            "preRemediationAssertion": "A pediatric Crohn’s disease exclusion-diet approach is supported.",
            "supportStatus": "independently supported",
            "finalDisposition": "Split to atomic CLM-098",
            "claimId": "CLM-098",
            "supportingExcerpt": split_claims[0]["supportingExcerpt"],
            "exactLocator": split_claims[0]["exactLocator"],
            "sourceUrl": ESPEN_URL,
            "verificationStatus": "PASS_direct_support",
        },
        {
            "assertionId": "CLM-097-B2",
            "preRemediationAssertion": "An adult Crohn’s disease exclusion-diet approach is supported.",
            "supportStatus": "independently supported",
            "finalDisposition": "Split to atomic CLM-099",
            "claimId": "CLM-099",
            "supportingExcerpt": split_claims[1]["supportingExcerpt"],
            "exactLocator": split_claims[1]["exactLocator"],
            "sourceUrl": ESPEN_URL,
            "verificationStatus": "PASS_direct_support",
        },
        {
            "assertionId": "CLM-097-C",
            "preRemediationAssertion": "Long-term effectiveness and possible-risk data are limited.",
            "supportStatus": "independently supported",
            "finalDisposition": "Split to atomic CLM-100",
            "claimId": "CLM-100",
            "supportingExcerpt": split_claims[2]["supportingExcerpt"],
            "exactLocator": split_claims[2]["exactLocator"],
            "sourceUrl": ESPEN_URL,
            "verificationStatus": "PASS_direct_support",
        },
    ]

    removed_or_replaced = deepcopy(data["removedAndReplacedClaims"])
    removed_or_replaced.append({
        "originalClaimId": "CLM-097",
        "originalSourceId": "SRC-026",
        "originalClaim": pre_remediation_097,
        "accountingCategory": "narrowed_and_split_in_place",
        "replacementClaimId": "CLM-097; CLM-098; CLM-099; CLM-100",
        "replacementSourceId": "SRC-026",
        "reason": "The pre-remediation claim contained multiple assertions; it was narrowed and split into atomic claims.",
        "archivedAt": str(OUTPUT),
        "humanReviewStatus": "pending_human_review",
    })

    ready = [c for c in claims if c["finalQaEligibility"] == "ready_for_final_independent_qa"]
    unresolved = [c for c in claims if c["evidenceStatus"] == "still_needs_evidence"]
    assert len(ready) == 60
    assert [c["claimId"] for c in unresolved] == ["CLM-092"]
    assert len(claims) == 61

    summary = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scope": "targeted_remaining_QA_failures_only",
        "targetedClaims": ["CLM-081", "CLM-082", "CLM-083", "CLM-084", "CLM-085", "CLM-086", "CLM-097"],
        "targetedClaimsRepaired": 7,
        "targetedClaimsRemoved": 0,
        "activeClaimsReadyForFinalIndependentQa": 60,
        "activeClaimsNeedingMoreEvidence": 1,
        "cumulativeOriginalClaimsRemoved": 37,
        "newSplitClaimsCreated": 3,
        "newSplitClaimIds": ["CLM-098", "CLM-099", "CLM-100"],
        "totalActiveClaims": 61,
        "originalClaimAccountingTotal": 95,
        "activeSources": 25,
        "sourceRowsIncludingSuperseded": 26,
        "genericActiveLocators": 0,
        "humanReviewFieldsBlank": True,
        "approvalGranted": False,
        "hardStop": "Await one final independent QA.",
    }

    result = {
        "sources": sources,
        "claims": claims,
        "locatorCorrections": locator_corrections,
        "clm097Remediation": clm097_remediation,
        "unresolvedClaims": unresolved,
        "removedOrReplacedClaims": removed_or_replaced,
        "validationSummary": [],
        "summary": summary,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
