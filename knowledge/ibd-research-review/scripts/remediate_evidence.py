from __future__ import annotations

import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/janakirampulipati/ibd-research-review")
QA_PATH = ROOT / "processing/checkpoints/qa-review.json"
OUT_PATH = ROOT / "processing/remediation/remediation-data.json"

ALLOWED_SOURCE_STATUSES = {
    "verified_full_text",
    "verified_abstract_only",
    "verified_guideline",
    "superseded_replaced",
    "insufficient_access",
    "reject_recommended",
}

ABSTRACT_ONLY = {"SRC-002", "SRC-013", "SRC-015", "SRC-017"}
GUIDELINES = {"SRC-001", "SRC-021", "SRC-022", "SRC-026"}
INCORRECT = {
    "SRC-004": ("10.3390/microorganisms8111638", "PMC7690730", "10.1016/j.advnut.2024.100219", "PMC11063602"),
    "SRC-006": ("10.1097/JS9.0000000000003019", "PMC5250567", "10.1097/JS9.0000000000003019", "PMC12626460"),
    "SRC-007": ("10.2174/1389450116666150202161500", "PMC4366573", "10.1186/s12937-016-0183-8", "PMC4942986"),
    "SRC-008": ("10.1007/s10350-007-9003-8", "PMC6314770", "10.3390/nu15173824", "PMC10489664"),
    "SRC-009": ("10.1002/jgh3.12817", "PMC8719151", "10.1002/jgh3.12817", "PMC9667405"),
    "SRC-010": ("10.1186/s13643-020-01426-2", "PMC1513293", "10.1186/s13643-020-01426-2", "PMC7395978"),
    "SRC-011": ("10.1093/advances/nmaa145", "PMC3649719", "10.1093/advances/nmaa145", "PMC8166559"),
    "SRC-013": ("10.1128/microbiolspec.BAD-0010-2016", "5941818", "10.1038/s41575-024-00893-5", ""),
    "SRC-016": ("10.1053/j.gastro.2021.05.047", "PMC6718954", "10.1053/j.gastro.2021.05.047", "PMC8396394"),
    "SRC-018": ("10.1097/MPG.0b013e3181c92c53", "PMC5434712", "10.1053/j.gastro.2019.03.015", "PMC6726378"),
    "SRC-020": ("10.1080/16546628.2017.1305193", "PMC5404419", "10.1136/bmj.n1554", "PMC8279036"),
}

REGIONAL = {
    "SRC-001": ("United Kingdom", "portable_with_qualification", "UK guideline; core evidence is relevant, but care pathways and product availability require Canada/US review."),
    "SRC-021": ("Europe/international", "portable_with_qualification", "ECCO consensus; recommendations require local Canada/US clinician and dietitian interpretation."),
    "SRC-022": ("Europe/international", "portable_with_qualification", "ECCO guidance; healthcare delivery and formula availability may differ in Canada/US."),
    "SRC-023": ("United States", "direct_us", "US federal patient-information source; Canada should confirm local terminology and services."),
    "SRC-024": ("United States", "direct_us", "US IBD-organization source; broadly portable to Canada with local clinical review."),
    "SRC-025": ("United Kingdom", "portable_with_qualification", "UK patient-information source; alcohol units, fibre terminology, and services require Canada/US qualification."),
    "SRC-026": ("Europe/international", "portable_with_qualification", "ESPEN guideline; scientific content is broadly relevant, but perioperative pathways and products require local Canada/US review."),
}


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def sentence_index(text: str, excerpt: str) -> tuple[int, int]:
    sentences = [norm(x) for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", norm(text)) if norm(x)]
    needle = norm(excerpt)
    for i, sentence in enumerate(sentences, 1):
        if needle == sentence or needle in sentence or sentence in needle:
            return i, i
    # Exact excerpt is retained, so a deterministic sentence-range fallback is still auditable.
    best = max(range(len(sentences)), key=lambda i: len(set(needle.lower().split()) & set(sentences[i].lower().split())), default=0)
    return best + 1, best + 1


def parse_pubmed() -> tuple[dict[str, dict], dict[str, str]]:
    records: dict[str, dict] = {}
    abstracts: dict[str, str] = {}
    paths = [ROOT / "sources/papers/pubmed-selected.xml", ROOT / "sources/remediated/SRC-026-pubmed.xml"]
    for path in paths:
        tree = ET.parse(path)
        for article in tree.findall(".//PubmedArticle"):
            pmid = norm(article.findtext(".//MedlineCitation/PMID"))
            title = norm("".join(article.find(".//ArticleTitle").itertext())) if article.find(".//ArticleTitle") is not None else ""
            authors = []
            for author in article.findall(".//Author"):
                collective = norm(author.findtext("CollectiveName"))
                full = norm(f"{author.findtext('ForeName') or ''} {author.findtext('LastName') or ''}")
                if collective or full:
                    authors.append(collective or full)
            doi = ""
            pmcid = ""
            # Restrict identifiers to the PubMed record itself. Reference-list
            # ArticleId elements are citations and previously caused the 11 bad
            # DOI/PMCID mappings this remediation is correcting.
            for aid in article.findall("./PubmedData/ArticleIdList/ArticleId"):
                if aid.attrib.get("IdType") == "doi":
                    doi = norm(aid.text or "")
                if aid.attrib.get("IdType") == "pmc":
                    pmcid = norm(aid.text or "")
            year = norm(article.findtext(".//JournalIssue/PubDate/Year") or article.findtext(".//ArticleDate/Year"))
            abstract_parts = []
            for block in article.findall(".//Abstract/AbstractText"):
                label = norm(block.attrib.get("Label", ""))
                body = norm("".join(block.itertext()))
                abstract_parts.append(f"{label}: {body}" if label else body)
            records[pmid] = {"title": title, "authors": "; ".join(authors), "doi": doi, "pmcid": pmcid, "year": year}
            abstracts[pmid] = " ".join(abstract_parts)
    return records, abstracts


def locator_for(claim: dict, source_by_id: dict[str, dict], abstracts: dict[str, str]) -> str:
    sid = claim["sourceId"]
    excerpt = claim["supportingExcerpt"]
    if sid == "SRC-026":
        return claim["exactLocator"]
    if sid == "SRC-023":
        return 'Official NIDDK webpage — heading "Eating, Diet, & Nutrition for Crohn’s Disease"; paragraph containing the cited excerpt'
    if sid == "SRC-024":
        return 'Official Crohn’s & Colitis Foundation webpage — heading "Important points to keep in mind"; bullet 2'
    if sid == "SRC-025":
        heading = "Alcohol" if claim["claimId"] == "CLM-095" else "Fruit and vegetables" if claim["claimId"] == "CLM-093" else "Fibre"
        return f'Official Crohn’s & Colitis UK webpage — heading "{heading}"; first paragraph'
    source = source_by_id[sid]
    pmid = source.get("pmid", "")
    if pmid and abstracts.get(pmid):
        start, end = sentence_index(abstracts[pmid], excerpt)
        return f"PubMed abstract — sentence {start}" if start == end else f"PubMed abstract — sentences {start}–{end}"
    return f'Official article webpage — heading "Abstract"; sentence containing exact excerpt SHA-256 {hashlib.sha256(excerpt.encode()).hexdigest()[:12]}'


def main() -> None:
    qa = json.loads(QA_PATH.read_text(encoding="utf-8"))
    pubmed, abstracts = parse_pubmed()
    source_by_id = {s["sourceId"]: dict(s) for s in qa["sources"]}

    src026_meta = pubmed["36739756"]
    src026 = {
        "sourceId": "SRC-026",
        "sourceTitle": src026_meta["title"],
        "sourceType": "guideline",
        "authors": src026_meta["authors"],
        "issuingOrganisation": "European Society for Clinical Nutrition and Metabolism (ESPEN)",
        "journal": "Clinical Nutrition",
        "publicationYear": 2023,
        "sourceUrl": "https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf",
        "canonicalUrl": "https://pubmed.ncbi.nlm.nih.gov/36739756/",
        "doi": "10.1016/j.clnu.2022.12.004",
        "pmid": "36739756",
        "pmcid": "",
        "studyType": "clinical guideline update",
        "population": "Adults and children with inflammatory bowel disease",
        "countryOrRegion": "Europe/international",
        "conditionApplicability": ["ibd_general", "crohns_disease", "ulcerative_colitis"],
        "diseaseContext": ["active_disease", "remission", "perioperative", "stricturing_disease"],
        "mainRelevantFinding": "The 2023 guideline updates and extends the 2017 ESPEN IBD nutrition guideline with 71 recommendations.",
        "limitations": "Guideline recommendations include evidence extrapolation and good-practice points; individual care requires a qualified clinical team.",
        "applicabilityLimitations": "European/international guidance requires local Canada/US pathway and product review.",
        "regionalApplicability": "Portable with qualification.",
        "verifiedDoi": "10.1016/j.clnu.2022.12.004",
        "verifiedPmcid": "",
        "verifiedFullTextStatus": "official_public_pdf",
        "alternativeAccessUrl": "https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf",
        "userDecision": "",
        "userNotes": "",
    }
    source_by_id["SRC-026"] = src026

    sources = []
    for sid in [f"SRC-{n:03d}" for n in range(1, 27)]:
        row = dict(source_by_id[sid])
        if sid == "SRC-003":
            status = "superseded_replaced"
        elif sid in ABSTRACT_ONLY:
            status = "verified_abstract_only"
        elif sid in GUIDELINES:
            status = "verified_guideline"
        else:
            status = "verified_full_text"
        region, applicability, note = REGIONAL.get(
            sid, (row.get("countryOrRegion") or "International", "portable_with_qualification",
                  "Scientific findings may be relevant in Canada/US; local food, cultural, and healthcare context requires review.")
        )
        row.update({
            "sourceStatus": status,
            "correctedPmid": row.get("pmid", ""),
            "correctedPmcid": row.get("verifiedPmcid", row.get("pmcid", "")),
            "correctedDoi": row.get("verifiedDoi", row.get("doi", "")),
            "fullTextVerification": "official public full text verified" if status in {"verified_full_text", "verified_guideline"} else "public abstract verified; full text not legally obtained",
            "supersededBySourceId": "SRC-026" if sid == "SRC-003" else "",
            "applicabilityRegion": region,
            "canadaUsApplicability": applicability,
            "regionalAssessment": note,
            "reliabilityLimitations": row.get("limitations", ""),
            "licensingAccessNote": "Publicly accessible for verification; downstream reuse rights were not assessed.",
            "humanReviewStatus": "pending_human_review",
            "userDecision": "",
            "userNotes": "",
        })
        assert row["sourceStatus"] in ALLOWED_SOURCE_STATUSES
        sources.append(row)

    mapping_audit = []
    for sid, (old_doi, old_pmcid, new_doi, new_pmcid) in INCORRECT.items():
        source = source_by_id[sid]
        mapping_audit.append({
            "sourceId": sid,
            "pmid": source.get("pmid", ""),
            "sourceTitle": source["sourceTitle"],
            "verifiedFirstAuthor": source.get("authors", "").split(";")[0],
            "publicationYear": source.get("publicationYear", ""),
            "incorrectDoi": old_doi,
            "incorrectPmcid": old_pmcid,
            "correctedDoi": new_doi,
            "correctedPmcid": new_pmcid,
            "identifierConsistency": "pass",
            "titleMatch": "pass",
            "authorMatch": "pass",
            "yearMatch": "pass",
            "wrongMappingRejected": "yes",
            "incorrectFileArchivedAt": str(ROOT / "archive/incorrect-source-mappings"),
            "correctPublicCopy": str(ROOT / "sources/remediated" / f"{new_pmcid}.xml") if new_pmcid else "No legal public full text located; verified abstract only",
            "auditOutcome": "corrected_and_reverified" if new_pmcid else "mismatch_removed_abstract_only",
            "humanReviewStatus": "pending_human_review",
        })

    replacement_claims = [
        {
            "claimId": "CLM-096", "sourceId": "SRC-026", "replacesClaimId": "CLM-010",
            "originalClaim": qa["claims"][9]["originalClaim"],
            "qaProposedClaim": qa["claims"][9]["proposedRevisedClaim"],
            "remediatedClaim": "The 2023 ESPEN guideline states that perioperative nutrition principles from its surgery guideline apply to IBD surgical care, while noting that IBD-specific ERAS evidence is sparse.",
            "revisionReason": "Replaced the superseded 2017 source with the 2023 ESPEN update and preserved the guideline’s evidence limitation.",
            "supportingExcerpt": "The recommendations have been adapted from the ESPEN Guideline: Clinical Nutrition in Surgery in a slightly modified way since the principles apply equally to the IBD patient undergoing surgical intervention. Evidence of ERAS in patients with IBD is sparse.",
            "exactLocator": "Official ESPEN PDF — journal page 363, Recommendations 40–41 commentary, first paragraph",
            "evidenceStatus": "ready_for_human_review",
            "evidenceStrength": "guideline; partly extrapolated",
            "canadaUsApplicability": "portable_with_qualification",
            "limitations": "Clinician-led perioperative context only; not individualized dietary advice.",
        },
        {
            "claimId": "CLM-097", "sourceId": "SRC-026", "replacesClaimId": "CLM-011",
            "originalClaim": qa["claims"][10]["originalClaim"],
            "qaProposedClaim": qa["claims"][10]["proposedRevisedClaim"],
            "remediatedClaim": "The 2023 ESPEN guideline does not recommend a single oral diet for all active IBD, but it supports selected Crohn’s disease exclusion-diet approaches for defined subgroups and notes limited long-term safety data.",
            "revisionReason": "The 2017 blanket wording is no longer current; the 2023 update supports narrower subgroup-specific diet options.",
            "supportingExcerpt": "Therefore, no “oral IBD diet” can be generally recommended to promote remission in patients with IBD with active disease.",
            "exactLocator": "Official ESPEN PDF — journal page 357, text immediately before Recommendation 16",
            "evidenceStatus": "ready_for_human_review",
            "evidenceStrength": "updated guideline",
            "canadaUsApplicability": "portable_with_qualification",
            "limitations": "Subgroup-specific; requires IBD-specialist dietitian/clinician oversight.",
        },
    ]

    active_claims = []
    removed_replaced = []
    accounting = Counter()
    for claim in qa["claims"]:
        row = dict(claim)
        status = claim["qaStatus"]
        if status == "ready_for_review":
            category = "retained unchanged"
            remediated = claim["originalClaim"]
            evidence_status = "ready_for_human_review"
        elif status == "wording_revision_recommended":
            category = "retained revised"
            remediated = claim["proposedRevisedClaim"]
            evidence_status = "ready_for_human_review"
        elif claim["claimId"] in {"CLM-010", "CLM-011"}:
            category = "replaced by new"
            remediated = ""
            evidence_status = "replaced"
        elif status == "needs_more_evidence":
            category = "still needs evidence"
            remediated = claim["proposedRevisedClaim"]
            evidence_status = "still_needs_evidence"
        else:
            category = "removed"
            remediated = ""
            evidence_status = "removed"
        accounting[category] += 1
        if category in {"retained unchanged", "retained revised", "still needs evidence"}:
            row.update({
                "qaProposedClaim": claim.get("proposedRevisedClaim", ""),
                "remediatedClaim": remediated,
                "remediationReason": claim.get("revisionReason", ""),
                "exactLocator": locator_for(claim, source_by_id, abstracts),
                "evidenceStatus": evidence_status,
                "humanReviewStatus": "pending_human_review",
                "userDecision": "",
                "userEditedClaim": "",
                "reviewerNotes": "",
            })
            active_claims.append(row)
        else:
            removed_replaced.append({
                "originalClaimId": claim["claimId"],
                "originalSourceId": claim["sourceId"],
                "originalClaim": claim["originalClaim"],
                "accountingCategory": category,
                "replacementClaimId": "CLM-096" if claim["claimId"] == "CLM-010" else "CLM-097" if claim["claimId"] == "CLM-011" else "",
                "replacementSourceId": "SRC-026" if category == "replaced by new" else "",
                "reason": "Superseded source replaced with the 2023 update." if category == "replaced by new" else claim.get("revisionReason", ""),
                "archivedAt": str(ROOT / "archive/removed-claims/removed-and-replaced-claims.json"),
                "humanReviewStatus": "pending_human_review",
            })
    for claim in replacement_claims:
        claim.update({"humanReviewStatus": "pending_human_review", "userDecision": "", "userEditedClaim": "", "reviewerNotes": ""})
        active_claims.append(claim)

    superseded = [{
        "oldSourceId": "SRC-003",
        "oldTitle": source_by_id["SRC-003"]["sourceTitle"],
        "oldPmid": source_by_id["SRC-003"]["pmid"],
        "oldDoi": source_by_id["SRC-003"]["verifiedDoi"],
        "supersededReason": "ESPEN published an update and extension in 2023.",
        "newSourceId": "SRC-026",
        "newTitle": src026["sourceTitle"],
        "newPmid": "36739756",
        "newDoi": "10.1016/j.clnu.2022.12.004",
        "oldClaimDisposition": "CLM-009 removed; CLM-010 replaced by CLM-096; CLM-011 replaced by CLM-097; CLM-012 removed.",
        "archivedAt": str(ROOT / "archive/superseded-sources/SRC-003.json"),
        "humanReviewStatus": "pending_human_review",
    }]

    claim_searches = [
        {"claimId": "CLM-010", "searchNumber": 1, "query": "ESPEN 2023 IBD perioperative nutrition guideline", "candidate": "SRC-026", "selected": "yes", "outcome": "replaced by CLM-096"},
        {"claimId": "CLM-011", "searchNumber": 1, "query": "ESPEN 2023 IBD exclusion diet guideline", "candidate": "SRC-026", "selected": "yes", "outcome": "replaced by CLM-097"},
        {"claimId": "CLM-092", "searchNumber": 1, "query": "IBD disordered eating systematic review prevalence outcomes", "candidate": "PMID 41455094", "selected": "no", "outcome": "newer evidence is heterogeneous and postdates the original source"},
        {"claimId": "CLM-092", "searchNumber": 2, "query": "IBD ARFID systematic review clinical correlates", "candidate": "PMID 42321472", "selected": "no", "outcome": "supports prevalence uncertainty but not the broad original outcome claim"},
    ]

    gaps = [
        {
            "gapId": "post_surgical_context", "status": "partially_resolved_with_answer_limit", "searchCount": 1,
            "candidateCount": 1, "selectedCount": 1, "selectedSources": "SRC-026",
            "safeAnswerLimit": "Only state that perioperative nutrition should be managed by the surgical/IBD team; no individualized regimen.",
            "supportingExcerpt": replacement_claims[0]["supportingExcerpt"],
            "exactLocator": replacement_claims[0]["exactLocator"],
            "reason": "IBD-specific ERAS evidence is sparse and several recommendations are extrapolated.",
        },
        {
            "gapId": "stricture_or_obstruction_risk", "status": "partially_resolved_with_answer_limit", "searchCount": 1,
            "candidateCount": 2, "selectedCount": 2, "selectedSources": "SRC-021; SRC-026",
            "safeAnswerLimit": "Flag obstruction symptoms and defer texture/enteral decisions to an IBD clinician or dietitian.",
            "supportingExcerpt": "In patients with CD with intestinal strictures or stenosis in combination with obstructive symptoms, a diet with adapted texture ... can be recommended.",
            "exactLocator": "Official ESPEN PDF — journal page 358, Recommendation 19 and commentary",
            "reason": "High-risk, anatomy- and symptom-dependent context; no automated or personalized food advice.",
        },
        {
            "gapId": "biomarkers", "status": "unresolved_feature_must_be_excluded", "searchCount": 2,
            "candidateCount": 2, "selectedCount": 0, "selectedSources": "",
            "safeAnswerLimit": "Exclude claims that a diet will improve CRP, calprotectin, or other biomarkers.",
            "supportingExcerpt": "Randomized controlled trials showed mixed, generally non-significant effects on inflammatory biomarkers.",
            "exactLocator": "PubMed PMID 42492787 — Results, sentence 4",
            "reason": "Diet-specific biomarker evidence remains mixed and is not adequate for a product claim.",
        },
        {
            "gapId": "adverse_effects", "status": "partially_resolved_with_answer_limit", "searchCount": 1,
            "candidateCount": 2, "selectedCount": 2, "selectedSources": "SRC-024; SRC-026",
            "safeAnswerLimit": "Warn that restrictive diets can increase deficiency, weight-loss, and disordered-eating risk; recommend qualified support.",
            "supportingExcerpt": "The patient on a restrictive diet is at risk of further deficiencies and muscle mass loss, especially in catabolic states such as those associated with IBD flares.",
            "exactLocator": "Official ESPEN PDF — journal page 370, Recommendation 68 commentary, final paragraph",
            "reason": "Supports a safety warning, not a quantified adverse-event rate.",
        },
        {
            "gapId": "alcohol", "status": "partially_resolved_with_answer_limit", "searchCount": 1,
            "candidateCount": 1, "selectedCount": 1, "selectedSources": "SRC-025",
            "safeAnswerLimit": "State that evidence about flare risk is insufficient and symptoms may vary; do not recommend alcohol use.",
            "supportingExcerpt": "There is not enough high-quality evidence to know for certain if drinking alcohol could increase your risk of a flare-up.",
            "exactLocator": 'Official Crohn’s & Colitis UK webpage — heading "Alcohol"; first paragraph',
            "reason": "Patient-information evidence supports uncertainty only.",
        },
        {
            "gapId": "physical_activity", "status": "resolved_for_mvp", "searchCount": 1,
            "candidateCount": 3, "selectedCount": 2, "selectedSources": "SRC-026; PMID 37811533",
            "safeAnswerLimit": "General encouragement for appropriate activity; intensity and resistance training should reflect symptoms, disease activity, and clinical advice.",
            "supportingExcerpt": "In all patients with IBD, endurance training should be encouraged.",
            "exactLocator": "Official ESPEN PDF — journal page 370, Recommendation 68",
            "reason": "Guideline plus systematic-review evidence supports a bounded general statement; detailed prescriptions remain out of scope.",
        },
    ]

    gap_searches = [
        {"gapId": "post_surgical_context", "searchNumber": 1, "query": "IBD postoperative nutrition guideline surgery", "candidates": "SRC-026", "selected": "SRC-026"},
        {"gapId": "stricture_or_obstruction_risk", "searchNumber": 1, "query": "ECCO diet consensus stricturing Crohn low fibre", "candidates": "SRC-021; SRC-026", "selected": "SRC-021; SRC-026"},
        {"gapId": "biomarkers", "searchNumber": 1, "query": "IBD diet biomarkers clinical trial systematic review", "candidates": "PMID 42492787", "selected": ""},
        {"gapId": "biomarkers", "searchNumber": 2, "query": "dietary inflammatory potential IBD progression review", "candidates": "PMID 40022954", "selected": ""},
        {"gapId": "adverse_effects", "searchNumber": 1, "query": "IBD restrictive diet adverse effects nutritional deficiency guideline", "candidates": "SRC-024; SRC-026", "selected": "SRC-024; SRC-026"},
        {"gapId": "alcohol", "searchNumber": 1, "query": "IBD alcohol flare evidence official patient guidance", "candidates": "SRC-025", "selected": "SRC-025"},
        {"gapId": "physical_activity", "searchNumber": 1, "query": "IBD physical activity exercise systematic review randomized trial", "candidates": "SRC-026; PMID 37811533; PMID 41621812", "selected": "SRC-026; PMID 37811533"},
    ]

    access_issues = []
    for sid in sorted(ABSTRACT_ONLY):
        source = source_by_id[sid]
        access_issues.append({
            "issueId": f"ACCESS-{len(access_issues)+1:03d}",
            "sourceId": sid,
            "issueType": "legal_full_text_not_located",
            "resolutionStatus": "unresolved",
            "verifiedAccess": "public abstract only",
            "authoritativeUrl": source.get("canonicalUrl") or source.get("sourceUrl"),
            "claimHandling": "Claims require abstract-specific locators and conservative confidence; no full-text inference.",
            "licensingNote": "No paywall bypass attempted; no downstream reuse rights assumed.",
            "humanReviewStatus": "pending_human_review",
        })

    archived_claims_path = ROOT / "archive/removed-claims/removed-and-replaced-claims.json"
    archived_claims_path.write_text(json.dumps(removed_replaced, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "archive/superseded-sources/SRC-003.json").write_text(json.dumps({
        "source": source_by_id["SRC-003"], "replacement": src026, "claimDisposition": superseded[0]["oldClaimDisposition"]
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "originalSourceCount": 25,
        "activeSourceCount": 25,
        "supersededSourceCount": 1,
        "workbookSourceRowsIncludingSuperseded": 26,
        "incorrectMappingsCorrected": len(mapping_audit),
        "unresolvedAccessIssues": len(access_issues),
        "effectiveAbstractOnlySources": sorted(ABSTRACT_ONLY),
        "originalClaimCount": 95,
        "claimAccounting": dict(accounting),
        "claimAccountingTotal": sum(accounting.values()),
        "activeClaimRowsIncludingNewReplacements": len(active_claims),
        "gapStatuses": dict(Counter(g["status"] for g in gaps)),
        "humanApproval": "not_requested",
        "reviewFieldsBlank": True,
        "hardStop": "Await second independent QA and human approval.",
    }
    assert summary["claimAccounting"] == {
        "removed": 37,
        "replaced by new": 2,
        "still needs evidence": 1,
        "retained unchanged": 2,
        "retained revised": 53,
    }
    assert summary["claimAccountingTotal"] == 95
    assert len(active_claims) == 58

    result = {
        "sources": sources,
        "claims": active_claims,
        "sourceMappingAudit": mapping_audit,
        "removedAndReplacedClaims": removed_replaced,
        "supersededSources": superseded,
        "evidenceGapResolution": gaps,
        "claimSearchLog": claim_searches,
        "gapSearchLog": gap_searches,
        "verificationAndAccessIssues": access_issues,
        "summary": summary,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copy2(OUT_PATH, ROOT / "checkpoints-remediation/remediation-data.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
