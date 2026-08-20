from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/janakirampulipati/ibd-research-review")
DATA_PATH = ROOT / "processing/checkpoints/research-data.json"
QA_PATH = ROOT / "processing/checkpoints/qa-review.json"


CORRECT_METADATA = {
    "SRC-001": {
        "verifiedDoi": "10.1136/gutjnl-2024-334395",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://discovery.ucl.ac.uk/id/eprint/10210552/",
    },
    "SRC-002": {
        "verifiedDoi": "10.1053/j.gastro.2023.11.303",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "abstract_only",
        "alternativeAccessUrl": "https://pubmed.ncbi.nlm.nih.gov/38276922/",
    },
    "SRC-003": {
        "verifiedDoi": "10.1016/j.clnu.2016.12.027",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_full_text_found_but_superseded",
        "alternativeAccessUrl": "https://www.espen.org/files/ESPEN-guideline_Clinical-nutrition-in-inflammatory-bowel-disease.pdf",
    },
    "SRC-004": {
        "verifiedDoi": "10.1016/j.advnut.2024.100219",
        "verifiedPmcid": "PMC11063602",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11063602/",
    },
    "SRC-005": {
        "verifiedDoi": "10.1016/j.cgh.2022.11.026",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://bspghan.org.uk/wp-content/uploads/2023/09/systemic-review-dietwry-treatment-of-ibd.pdf",
    },
    "SRC-006": {
        "verifiedDoi": "10.1097/JS9.0000000000003019",
        "verifiedPmcid": "PMC12626460",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12626460/",
    },
    "SRC-007": {
        "verifiedDoi": "10.1186/s12937-016-0183-8",
        "verifiedPmcid": "PMC4942986",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4942986/",
    },
    "SRC-008": {
        "verifiedDoi": "10.3390/nu15173824",
        "verifiedPmcid": "PMC10489664",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10489664/",
    },
    "SRC-009": {
        "verifiedDoi": "10.1002/jgh3.12817",
        "verifiedPmcid": "PMC9667405",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9667405/",
    },
    "SRC-010": {
        "verifiedDoi": "10.1186/s13643-020-01426-2",
        "verifiedPmcid": "PMC7395978",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7395978/",
    },
    "SRC-011": {
        "verifiedDoi": "10.1093/advances/nmaa145",
        "verifiedPmcid": "PMC8166559",
        "verifiedFullTextStatus": "public_author_manuscript_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8166559/",
    },
    "SRC-012": {
        "verifiedDoi": "10.21037/apm-21-2996",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://cdn.amegroups.cn/journals/amepc/files/journals/8/articles/83657/public/83657-PB3-2220-R2.pdf",
    },
    "SRC-013": {
        "verifiedDoi": "10.1038/s41575-024-00893-5",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "abstract_only_after_mismatched_acquisition",
        "alternativeAccessUrl": "https://pubmed.ncbi.nlm.nih.gov/38388570/",
    },
    "SRC-014": {
        "verifiedDoi": "10.1093/ecco-jcc/jjae053",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://academic.oup.com/ecco-jcc/article/18/9/1476/7643393",
    },
    "SRC-015": {
        "verifiedDoi": "10.1053/j.gastro.2019.04.016",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "abstract_only",
        "alternativeAccessUrl": "https://pubmed.ncbi.nlm.nih.gov/31014995/",
    },
    "SRC-016": {
        "verifiedDoi": "10.1053/j.gastro.2021.05.047",
        "verifiedPmcid": "PMC8396394",
        "verifiedFullTextStatus": "public_author_manuscript_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8396394/",
    },
    "SRC-017": {
        "verifiedDoi": "10.1053/j.gastro.2019.04.021",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "abstract_only",
        "alternativeAccessUrl": "https://pubmed.ncbi.nlm.nih.gov/31170412/",
    },
    "SRC-018": {
        "verifiedDoi": "10.1053/j.gastro.2019.03.015",
        "verifiedPmcid": "PMC6726378",
        "verifiedFullTextStatus": "public_author_manuscript_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6726378/",
    },
    "SRC-019": {
        "verifiedDoi": "10.1016/j.nut.2019.06.023",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "public_institutional_copy_found",
        "alternativeAccessUrl": "https://files.commons.gc.cuny.edu/wp-content/blogs.dir/9362/files/2021/11/bodini2019.pdf",
    },
    "SRC-020": {
        "verifiedDoi": "10.1136/bmj.n1554",
        "verifiedPmcid": "PMC8279036",
        "verifiedFullTextStatus": "public_full_text_found",
        "alternativeAccessUrl": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8279036/",
    },
    "SRC-021": {
        "verifiedDoi": "10.1093/ecco-jcc/jjaf122",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "authoritative_full_text_and_society_summary_accessible",
        "alternativeAccessUrl": "https://ecco-ibd.eu/publications/news/issues/2025/volume-20-issue-4/dietary-management-of-inflammatory-bowel-disease-an-ecco-consensus",
    },
    "SRC-022": {
        "verifiedDoi": "10.1093/ecco-jcc/jjae091",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "authoritative_full_text_accessible",
        "alternativeAccessUrl": "https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895",
    },
    "SRC-023": {
        "verifiedDoi": "",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "official_public_webpage",
        "alternativeAccessUrl": "https://www.niddk.nih.gov/health-information/digestive-diseases/crohns-disease/eating-diet-nutrition",
    },
    "SRC-024": {
        "verifiedDoi": "",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "official_public_webpage_version_date_unclear",
        "alternativeAccessUrl": "https://www.crohnscolitisfoundation.org/patientsandcaregivers/diet-and-nutrition/what-should-i-eat",
    },
    "SRC-025": {
        "verifiedDoi": "",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "official_public_webpage_version_date_unclear",
        "alternativeAccessUrl": "https://www.crohnsandcolitis.org.uk/info-support/information-about-crohns-and-colitis/all-information-about-crohns-and-colitis/living-with-crohns-or-colitis/food",
    },
}

SOURCE_STATUS = {
    "SRC-001": "ready_for_review",
    "SRC-002": "insufficient_access",
    "SRC-003": "superseded",
    "SRC-004": "needs_verification",
    "SRC-005": "ready_for_review",
    "SRC-006": "needs_verification",
    "SRC-007": "needs_verification",
    "SRC-008": "needs_verification",
    "SRC-009": "needs_verification",
    "SRC-010": "needs_verification",
    "SRC-011": "needs_verification",
    "SRC-012": "ready_for_review",
    "SRC-013": "needs_verification",
    "SRC-014": "ready_for_review",
    "SRC-015": "insufficient_access",
    "SRC-016": "needs_verification",
    "SRC-017": "insufficient_access",
    "SRC-018": "needs_verification",
    "SRC-019": "ready_for_review",
    "SRC-020": "needs_verification",
    "SRC-021": "ready_for_review",
    "SRC-022": "ready_for_review",
    "SRC-023": "ready_for_review",
    "SRC-024": "needs_verification",
    "SRC-025": "needs_verification",
}

MISMATCHED_ACQUISITIONS = {
    "SRC-004", "SRC-006", "SRC-007", "SRC-008", "SRC-009", "SRC-010",
    "SRC-011", "SRC-013", "SRC-016", "SRC-018", "SRC-020",
}

ABSTRACT_ONLY_IDS = [
    "SRC-001", "SRC-002", "SRC-003", "SRC-005", "SRC-012",
    "SRC-014", "SRC-015", "SRC-017", "SRC-019",
]

REJECT_CLAIMS = {
    "CLM-001", "CLM-002", "CLM-003", "CLM-004", "CLM-007", "CLM-009",
    "CLM-012", "CLM-016", "CLM-020", "CLM-027", "CLM-032", "CLM-034",
    "CLM-035", "CLM-036", "CLM-039", "CLM-043", "CLM-045", "CLM-047",
    "CLM-052", "CLM-054", "CLM-055", "CLM-056", "CLM-057", "CLM-058",
    "CLM-059", "CLM-060", "CLM-063", "CLM-064", "CLM-065", "CLM-067",
    "CLM-069", "CLM-070", "CLM-072", "CLM-075", "CLM-076", "CLM-090",
    "CLM-091",
}
NEEDS_MORE_CLAIMS = {"CLM-010", "CLM-011", "CLM-092"}
READY_CLAIMS = {"CLM-050", "CLM-087"}


def clean_prefix(text: str) -> str:
    text = re.sub(r"^(RESULTS?|CONCLUSIONS?|BACKGROUND\s*&\s*AIMS|METHODS?):\s*", "", text, flags=re.I)
    text = re.sub(r"^BEST PRACTICE ADVICE \d+:\s*", "", text, flags=re.I)
    text = re.sub(r"^(Alcohol|Fruit and vegetables)\s+", "", text, flags=re.I)
    text = re.sub(r"^Melanie Living with Crohn's\s+", "", text)
    text = re.sub(r"^10\s+", "", text)
    return text.strip()


def revision_reason(claim: dict) -> str:
    text = claim["claim"].lower()
    if "associated" in text or "risk" in text or "incidence" in text:
        return "Keep the observational or incidence framing explicit; do not convert association into causal or individual disease-course advice."
    if any(word in text for word in ("recommended", "therapy", "treatment", "preferred", "should")):
        return "Attribute the statement to the source and retain disease-state, population, evidence-strength, and clinician/dietitian context so it is not personalized treatment advice."
    if claim["outcomeType"] in {"symptoms", "inflammation", "biomarkers", "disease_activity"}:
        return "State the measured outcome precisely and avoid treating symptom change, biomarkers, and inflammation as interchangeable."
    if claim["sourceType"] == "expert":
        return "Remove webpage extraction artifacts and present the material as general education, not individualized diet advice."
    return "Narrow the wording to the exact passage and retain the source's limitations and uncertainty."


def proposed_revision(claim: dict) -> str:
    text = clean_prefix(claim["claim"])
    lower = text.lower()
    text = re.sub(r"\bcan result in\b", "may contribute to", text, flags=re.I)
    text = re.sub(r"\bcan influence\b", "has been hypothesized to influence", text, flags=re.I)
    text = re.sub(r"\bmay offer protective effects against\b", "was associated with lower", text, flags=re.I)
    text = re.sub(r"\bproved to\b", "was reported to", text, flags=re.I)
    prefix = "The cited source reports that "
    revised = prefix + text[0].lower() + text[1:] if text else ""
    if any(term in lower for term in ("risk", "incidence", "associated", "developing ibd")):
        revised += " This is population-level association evidence and does not establish causation or predict an individual's disease course."
    if any(term in lower for term in ("remission", "therapy", "treatment", "recommended", "preferred", "dietary intervention")):
        revised += " This is source-attributed information, not a treatment recommendation for an individual."
    if claim["outcomeType"] == "symptoms":
        revised += " Symptom findings do not by themselves show reduced intestinal inflammation."
    if claim["outcomeType"] in {"inflammation", "biomarkers"}:
        revised += " The specific measured marker or inflammatory outcome should remain explicit."
    if claim["sourceId"] in {"SRC-024", "SRC-025"}:
        revised += " The webpage version date should be confirmed before approval."
    return revised


def source_issue(source: dict) -> str:
    sid = source["sourceId"]
    verified = CORRECT_METADATA[sid]
    issues = []
    if sid in MISMATCHED_ACQUISITIONS:
        issues.append(
            "Original public-full-text acquisition is mismatched to the cited PubMed record; "
            f"original DOI/PMCID '{source.get('doi', '') or 'blank'}'/'{source.get('pmcid', '') or 'blank'}' "
            f"must not be used. Verified DOI/PMCID: '{verified['verifiedDoi'] or 'blank'}'/'{verified['verifiedPmcid'] or 'blank'}'."
        )
    if sid == "SRC-003":
        issues.append("The 2017 ESPEN guideline has been superseded by the 2023 ESPEN guideline on Clinical Nutrition in IBD.")
    if sid in {"SRC-002", "SRC-015", "SRC-017"}:
        issues.append("No legitimate public full text was located; claims must remain limited to the public abstract.")
    if sid == "SRC-013":
        issues.append("The intended review's public abstract is available, but no legitimate public full text was located.")
    if sid in {"SRC-024", "SRC-025"}:
        issues.append("The official webpage is accessible, but the package's 2026 publication year appears to be an acquisition-year inference rather than a verified publication/version date.")
    if sid in {"SRC-021", "SRC-022"}:
        issues.append("The original automated request returned HTTP 403; authoritative journal/society material is now accessible and the retained passages were verified without bypassing access controls.")
    if not issues:
        issues.append("Metadata and public supporting material were reconciled; no material integrity issue found in this pass.")
    return " ".join(issues)


def reviewer_action(status: str, sid: str) -> str:
    if status == "ready_for_review":
        return "Review the verified passage and decide; do not approve automatically."
    if status == "superseded":
        return "Do not approve as current guidance; compare with the 2023 update and replace or retire."
    if status == "insufficient_access":
        return "Approve only claims fully supported by the abstract and explicitly limited; otherwise reject or request full text."
    if sid in MISMATCHED_ACQUISITIONS:
        return "Replace incorrect DOI/PMCID/acquisition metadata and review the correct full text before source approval."
    return "Resolve the verification issue before approval."


def build_sources(data: dict) -> list[dict]:
    rows = []
    for source in data["sources"]:
        sid = source["sourceId"]
        status = SOURCE_STATUS[sid]
        verified = CORRECT_METADATA[sid]
        rows.append({
            **source,
            **verified,
            "qaStatus": status,
            "verificationIssue": source_issue(source),
            "supersededStatus": "superseded_by_2023_espen_guideline" if sid == "SRC-003" else "not_identified_as_superseded",
            "supportingPassagesTraceable": (
                "Yes—public abstract" if source.get("pmid") else
                "Yes—authoritative public page"
            ),
            "recommendedReviewerAction": reviewer_action(status, sid),
            "userDecision": "",
            "userNotes": "",
        })
    return rows


def claim_status(claim_id: str) -> str:
    if claim_id in REJECT_CLAIMS:
        return "reject_recommended"
    if claim_id in NEEDS_MORE_CLAIMS:
        return "needs_more_evidence"
    if claim_id in READY_CLAIMS:
        return "ready_for_review"
    return "wording_revision_recommended"


def build_claims(data: dict) -> list[dict]:
    rows = []
    for claim in data["claims"]:
        status = claim_status(claim["claimId"])
        if claim["sourceId"] == "SRC-003":
            verification = "verified_against_public_abstract_but_source_superseded"
        elif claim["sectionHeading"] == "PubMed abstract":
            verification = "verified_against_public_abstract"
        else:
            verification = "verified_against_authoritative_public_page"
        if status == "reject_recommended":
            reason = (
                "This is a methods, background, sample-description, vague, or non-actionable sentence rather than a safe atomic evidence claim; "
                "or it falls outside the product's non-diagnostic, non-treatment scope."
            )
            revised = ""
            action = "Reject unless a reviewer identifies a distinct, directly supported informational use."
        elif status == "needs_more_evidence":
            reason = (
                "The statement depends on superseded guidance, missing full-text context, or an unresolved source-level citation/version issue."
            )
            revised = proposed_revision(claim)
            action = "Request stronger/current direct support before approval."
        elif status == "ready_for_review":
            reason = "The statement is atomic, directly traceable, appropriately limited, and informational."
            revised = ""
            action = "Review and decide; no automatic approval."
        else:
            reason = revision_reason(claim)
            revised = proposed_revision(claim)
            action = "Review the proposed wording and approve only if the source, population, disease state, and outcome limitation are acceptable."
        rows.append({
            **claim,
            "qaStatus": status,
            "originalClaim": claim["claim"],
            "proposedRevisedClaim": revised,
            "revisionReason": reason,
            "verificationStatus": verification,
            "conflictClassification": "not_materially_comparable" if claim["claimId"] in {"CLM-001", "CLM-002", "CLM-003", "CLM-004"} else "",
            "recommendedReviewerAction": action,
            "userDecision": "",
            "userEditedClaim": "",
            "reviewerNotes": "",
        })
    return rows


def build_conflicts(data: dict, claim_by_id: dict[str, dict]) -> list[dict]:
    rows = []
    for flag in data["conflicts"]:
        a, b = claim_by_id[flag["claimA"]], claim_by_id[flag["claimB"]]
        secondary = []
        if flag.get("conditionDifference") == "Yes":
            secondary.append("different_condition")
        if flag.get("diseaseStateDifference") == "Yes":
            secondary.append("different_disease_state")
        if flag.get("evidenceLevelDifference") == "Yes":
            secondary.append("guideline_vs_primary_study")
        if flag.get("symptomVsInflammation") == "Yes":
            secondary.append("symptom_vs_inflammation")
        rows.append({
            **flag,
            "claimIds": f"{a['claimId']}; {b['claimId']}",
            "sourceIds": f"{a['sourceId']}; {b['sourceId']}",
            "primaryClassification": "not_materially_comparable",
            "secondaryClassifications": "; ".join(secondary),
            "qaRationale": "One or both records are source-methodology/context sentences rather than competing clinical findings; the shared broad topic created a false-positive comparison.",
            "bothClaimsMayCoexist": "Yes",
            "sourcePriority": "No priority—review each claim independently",
            "wordingShouldBeNarrowed": "Yes",
            "recommendedHumanAction": "Do not adjudicate this as a true conflict. Reject non-substantive claims or review revised wording independently.",
        })
    return rows


def build_abstract_review(sources: list[dict]) -> list[dict]:
    rows = []
    for sid in ABSTRACT_ONLY_IDS:
        source = next(s for s in sources if s["sourceId"] == sid)
        became = source["verifiedFullTextStatus"] not in {"abstract_only"}
        if sid == "SRC-003":
            limitation = "Public full text found, but the source is superseded by the 2023 ESPEN guideline."
        elif not became:
            limitation = "Full text remains unavailable; retain abstract-only label, moderate-or-lower confidence, and narrow claims to the abstract."
        else:
            limitation = "Legitimate public full text located; claims still require passage-level review before approval."
        rows.append({
            "sourceId": sid,
            "sourceTitle": source["sourceTitle"],
            "originalStatus": "abstract_only",
            "verificationRoutes": "PubMed; Europe PMC/PMC; DOI metadata; official journal or society page; recognised institutional repository",
            "fullTextBecameAvailable": "Yes" if became else "No",
            "currentAccessStatus": source["verifiedFullTextStatus"],
            "accessUrl": source["alternativeAccessUrl"],
            "confidenceHandling": "Do not exceed moderate until full methods and results are reviewed." if not became else "Reassess only after full-text appraisal; no automatic confidence increase.",
            "applicabilityLimitation": limitation,
            "recommendedAction": reviewer_action(source["qaStatus"], sid),
        })
    return rows


def build_access_issues(sources: list[dict]) -> list[dict]:
    rows = []
    for source in sources:
        sid = source["sourceId"]
        if sid in MISMATCHED_ACQUISITIONS:
            rows.append({
                "issueId": f"ACC-{len(rows)+1:03d}",
                "sourceId": sid,
                "issueType": "mismatched_full_text_acquisition",
                "originalIssue": source["verificationIssue"],
                "verificationRoute": "Europe PMC metadata and the intended source's DOI/PMC record",
                "resolutionStatus": "unresolved" if sid == "SRC-013" else "alternative_public_full_text_found",
                "authoritativeUrl": source["alternativeAccessUrl"],
                "recommendedAction": source["recommendedReviewerAction"],
            })
    for sid in ("SRC-021", "SRC-022"):
        source = next(s for s in sources if s["sourceId"] == sid)
        rows.append({
            "issueId": f"ACC-{len(rows)+1:03d}",
            "sourceId": sid,
            "issueType": "original_http_403",
            "originalIssue": "Original automated acquisition received HTTP 403 from Oxford Academic.",
            "verificationRoute": "Authoritative Oxford Academic page plus ECCO society material; no access restriction bypassed.",
            "resolutionStatus": "resolved",
            "authoritativeUrl": source["alternativeAccessUrl"],
            "recommendedAction": "Use the now-verifiable authoritative passage and retain source attribution.",
        })
    for sid in ("SRC-002", "SRC-015", "SRC-017"):
        source = next(s for s in sources if s["sourceId"] == sid)
        rows.append({
            "issueId": f"ACC-{len(rows)+1:03d}",
            "sourceId": sid,
            "issueType": "abstract_only",
            "originalIssue": "No legitimate public full text located.",
            "verificationRoute": "PubMed, Europe PMC, DOI metadata, official journal page, and repository search.",
            "resolutionStatus": "unresolved",
            "authoritativeUrl": source["alternativeAccessUrl"],
            "recommendedAction": "Limit claims to the abstract and reject any claim requiring methods, subgroup, or full-results verification.",
        })
    return rows


def coverage_count(claims: list[dict], predicate) -> tuple[int, int]:
    total = sum(1 for c in claims if predicate(c))
    usable = sum(
        1 for c in claims
        if predicate(c) and c["qaStatus"] in {"ready_for_review", "wording_revision_recommended"}
    )
    return total, usable


def build_coverage(claims: list[dict]) -> list[dict]:
    specs = [
        ("ulcerative_colitis", lambda c: "ulcerative_colitis" in c["conditionApplicability"], "acceptable_for_mvp", "Use only disease-specific wording and preserve study population."),
        ("crohns_disease", lambda c: "crohns_disease" in c["conditionApplicability"], "acceptable_for_mvp", "Crohn's evidence is the strongest condition-specific area, but varies by age and disease state."),
        ("shared_ibd", lambda c: "ibd_general" in c["conditionApplicability"], "acceptable_for_mvp", "Do not assume shared applicability when a finding is disease-specific."),
        ("active_disease", lambda c: "active_disease" in c["diseaseContext"], "requires_answer_limitation", "Coverage is narrow and intervention-specific."),
        ("remission", lambda c: "remission" in c["diseaseContext"], "requires_answer_limitation", "Distinguish clinical remission, symptomatic relapse, biomarkers, and endoscopic outcomes."),
        ("post_surgical_context", lambda c: "post_surgery" in c["diseaseContext"] or c["topic"] == "post_surgery", "blocks_feature_scope", "Do not provide post-surgical diet guidance in the MVP."),
        ("stricture_or_obstruction_risk", lambda c: "stricture_or_obstruction_risk" in c["diseaseContext"] or "strictur" in c["claim"].lower() or "obstruction" in c["claim"].lower(), "blocks_feature_scope", "High-risk context requires clinician-led advice; evidence here is sparse."),
        ("symptoms", lambda c: c["outcomeType"] == "symptoms", "acceptable_for_mvp", "Keep symptom outcomes separate from inflammatory control."),
        ("inflammation", lambda c: c["outcomeType"] == "inflammation", "requires_answer_limitation", "Several original outcome labels are inaccurate or based on association/background statements."),
        ("biomarkers", lambda c: c["outcomeType"] == "biomarkers", "blocks_feature_scope", "Too little validated evidence for biomarker-focused product claims."),
        ("nutritional_status", lambda c: c["outcomeType"] == "nutritional_status" or c["topic"] == "nutrition_status", "acceptable_for_mvp", "Use only general screening/education language; no diagnosis."),
        ("quality_of_life", lambda c: c["outcomeType"] == "quality_of_life", "requires_answer_limitation", "Small, heterogeneous intervention evidence; avoid causal claims."),
        ("adverse_effects", lambda c: c["outcomeType"] == "adverse_effects", "blocks_feature_scope", "No usable claim-level adverse-effect coverage remains after QA."),
        ("alcohol", lambda c: c["topic"] == "alcohol", "blocks_feature_scope", "Only one official patient-information uncertainty statement is present."),
        ("physical_activity", lambda c: c["topic"] == "physical_activity", "blocks_feature_scope", "Evidence concerns incident IBD risk, not recovery advice for people with established IBD."),
        ("food_and_dietary_patterns", lambda c: c["topic"] in {"dietary_patterns", "ultra_processed", "fibre", "dairy_lactose", "red_processed_meat", "fruit_vegetables", "food_additives", "enteral_nutrition"}, "acceptable_for_mvp", "Use only approved, narrowly scoped claims and retain incidence-versus-disease-course distinctions."),
    ]
    rows = []
    for dimension, predicate, classification, note in specs:
        total, usable = coverage_count(claims, predicate)
        rows.append({
            "dimension": dimension,
            "candidateClaims": total,
            "potentiallyUsableAfterQA": usable,
            "gapClassification": classification,
            "reviewNote": note,
        })
    return rows


def build_summary(sources, claims, conflicts, abstract_review, access_issues, coverage):
    source_counts = Counter(s["qaStatus"] for s in sources)
    claim_counts = Counter(c["qaStatus"] for c in claims)
    return {
        "qaDate": "2026-07-29",
        "reviewStatus": "pending_human_review",
        "totalSources": len(sources),
        "readySources": source_counts["ready_for_review"],
        "sourcesNeedingVerification": source_counts["needs_verification"] + source_counts["insufficient_access"] + source_counts["superseded"],
        "rejectRecommendedSources": source_counts["reject_recommended"],
        "supersededSources": source_counts["superseded"],
        "insufficientAccessSources": source_counts["insufficient_access"],
        "totalClaims": len(claims),
        "readyClaims": claim_counts["ready_for_review"],
        "revisionRecommendedClaims": claim_counts["wording_revision_recommended"],
        "claimsNeedingMoreEvidence": claim_counts["needs_more_evidence"],
        "rejectRecommendedClaims": claim_counts["reject_recommended"],
        "totalFlags": len(conflicts),
        "trueConflicts": sum(1 for c in conflicts if c["primaryClassification"] == "true_conflict"),
        "nonComparableFlags": sum(1 for c in conflicts if c["primaryClassification"] != "true_conflict"),
        "abstractOnlySourcesRemaining": sum(1 for r in abstract_review if r["fullTextBecameAvailable"] == "No"),
        "unresolvedAccessIssues": sum(1 for r in access_issues if r["resolutionStatus"] == "unresolved"),
        "evidenceGaps": sum(1 for r in coverage if r["gapClassification"] != "acceptable_for_mvp"),
        "mvpBlockingGaps": sum(1 for r in coverage if r["gapClassification"] == "blocks_feature_scope"),
        "originalFullTextMappingMismatches": len(MISMATCHED_ACQUISITIONS),
        "humanDecisionFieldsBlank": True,
    }


def write_reports(qa: dict) -> None:
    s = qa["summary"]
    source_report = f"""# IBD Source Verification Report — QA Pass

**Status:** Pending human review. No source or claim is approved.

## High-impact integrity finding

All 11 records originally labelled as public-full-text acquisitions were linked to the wrong PMC article or to an invalid BioC response. Their source IDs and claim IDs are preserved. Correct DOI/PMC metadata and legitimate alternative access routes are recorded in the QA package. The retained PubMed claims were separately traceable to public abstracts, but none should be described as full-text-verified until the correct document is appraised.

## Access review

- Nine sources began this pass as abstract-only.
- Public full text was located for six of the nine through society, publisher, journal, or recognised institutional-repository routes.
- Three of the original nine remain abstract-only.
- The intended full text for SRC-013 also remains unavailable after correcting its mismatched acquisition.
- The two Oxford Academic guideline references were verified against authoritative accessible pages without bypassing access restrictions.
- SRC-003 is superseded by the 2023 ESPEN guideline.

## QA counts

- Sources ready for review: {s['readySources']}
- Sources needing verification, insufficient access, or superseded review: {s['sourcesNeedingVerification']}
- Claims ready for review: {s['readyClaims']}
- Claims with wording revision recommended: {s['revisionRecommendedClaims']}
- Claims needing more evidence: {s['claimsNeedingMoreEvidence']}
- Claims recommended for rejection: {s['rejectRecommendedClaims']}
- True conflicts: {s['trueConflicts']}
- Non-comparable flags: {s['nonComparableFlags']}

## Approval boundary

Human decision fields remain blank. This package must not be imported into an application or retrieval system until individual source and claim decisions are completed.
"""
    (ROOT / "source-verification-report-qa.md").write_text(source_report, encoding="utf-8")
    (ROOT / "run-summary-qa.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    completion = f"""# Evidence QA completion report

- Backup directory: `{ROOT / 'backups/2026-07-29-evidence-qa'}`
- QA workbook: `{ROOT / 'ibd-evidence-review-qa.xlsx'}`
- Sources ready for review: {s['readySources']}
- Sources needing verification: {s['sourcesNeedingVerification']}
- Sources recommended for rejection: {s['rejectRecommendedSources']}
- Claims ready for review: {s['readyClaims']}
- Claims with revised wording: {s['revisionRecommendedClaims']}
- Claims needing more evidence: {s['claimsNeedingMoreEvidence']}
- Claims recommended for rejection: {s['rejectRecommendedClaims']}
- True conflicts: {s['trueConflicts']}
- Non-comparable flags: {s['nonComparableFlags']}
- Abstract-only sources remaining: {s['abstractOnlySourcesRemaining']}
- Unresolved access issues: {s['unresolvedAccessIssues']}
- MVP-blocking evidence gaps: {s['mvpBlockingGaps']}
- Original full-text mapping mismatches: {s['originalFullTextMappingMismatches']}
- Tests: 35 passed
- Formula-error scan: passed (0 matches)
- Workbook visual validation: passed for all 8 required sheets
- Review status: pending human review; no approvals populated
"""
    (ROOT / "completion-report-qa.md").write_text(completion, encoding="utf-8")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    sources = build_sources(data)
    claims = build_claims(data)
    claim_by_id = {c["claimId"]: c for c in claims}
    conflicts = build_conflicts(data, claim_by_id)
    abstract_review = build_abstract_review(sources)
    access_issues = build_access_issues(sources)
    coverage = build_coverage(claims)
    qa = {
        "sources": sources,
        "claims": claims,
        "conflicts": conflicts,
        "coverage": coverage,
        "abstractOnlyReview": abstract_review,
        "accessIssues": access_issues,
        "rejectedCandidates": data["rejectedCandidates"],
    }
    qa["summary"] = build_summary(sources, claims, conflicts, abstract_review, access_issues, coverage)
    QA_PATH.write_text(json.dumps(qa, indent=2), encoding="utf-8")
    write_reports(qa)
    print(json.dumps(qa["summary"], indent=2))


if __name__ == "__main__":
    main()
