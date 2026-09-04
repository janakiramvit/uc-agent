# UC Evidence-Expansion — QA Report

**Run ID:** `uc-exp-e648136e30e7` · **Generated:** 2026-09-02T13:21:21Z

> Automated QA only. Automated QA does NOT constitute clinical approval. Every check is itself pending human/clinical review.

**Result: 21 / 21 automated checks PASS** (0 fail).

| # | Check | Result | Evidence / detail |
|---|---|---|---|
| QA-01 | Every candidate claim references a source present in sources.json | **PASS** | All 13 claims map to SRC-028/SRC-033. |
| QA-02 | Every claim has a non-empty exact supporting excerpt AND an exact locator | **PASS** | All 13 claims carry both. |
| QA-03 | Each supporting excerpt is a verbatim substring of the retrieved source abstract | **PASS** | 13/13 excerpts substring-verified against retrieval-cache API responses. |
| QA-04 | DOI, PubMed ID and canonical URL present and well-formed for every source | **PASS** | SRC-028 DOI 10.1053/j.gastro.2022.12.007 PMID 36822736; SRC-033 DOI 10.1053/j.gastro.2020.12.031 PMID 33359090; SRC-034 DOI 10.1053/j.gastro.2020.01.006 PMID 31945371. All canonical URLs are doi.org resolvers. |
| QA-05 | UC-specific applicability is NOT inferred from Crohn's-only or IBD-general evidence | **PASS** | No Crohn's-only claims. All 6 STRIDE-II (IBD-general) claims are labelled conditionApplicability=ibd_general; the 7 AGA claims are UC-specific because the AGA guideline is UC-specific. |
| QA-06 | IBD-general evidence remains labelled ibd_general | **PASS** | 6 claims labelled ibd_general (CLM-122..127, from STRIDE-II). Limitations text on each states 'not a UC-only statement'. |
| QA-07 | Archived source files have valid checksums and provenance | **PASS** | 0 source files archived this run (source-files/ empty). Retrieval-cache provenance recorded with SHA-256 in ingestion-manifest.json. |
| QA-08 | No restricted / unlicensed PDF was copied | **PASS** | pdfsDownloaded=0. Unpaywall listed a 'free' publisher PDF for SRC-028; not downloaded (redistribution licence not established). |
| QA-09 | No duplicate sources or claims were added | **PASS** | STRIDE-II new_unique. SRC-034 new_unique. SRC-028 adopted the never-materialized planned id for the same PMID/DOI (documented). No claim IDs collide with CLM-001..114. |
| QA-10 | Conflicts and limitations remain visible | **PASS** | 5 conflicts in Conflicts sheet (CONF-01..05); every claim has non-empty limitations + conflictsWithExistingEvidence fields; 9 gaps in Evidence Gaps sheet. |
| QA-11 | Every patient-question mapping is to a real question-tree node and every claim is mapped | **PASS** | All 13 claims mapped; target nodes L2-1.1, L2-1.2, L3-1.2.1, L3-1.2.2, L3-1.2.3, L3-1.3.3 all exist in uc_39_question_tree.json. |
| QA-12 | Canada/US applicability is explicitly assessed for every source | **PASS** | Each source has regionalApplicability.canada + .unitedStates + narrative assessment; each claim has a regionalApplicabilityNote. |
| QA-13 | All human-review / clinical-review / decision / signature / date fields are blank | **PASS** | Verified blank across all 3 sources and all 13 claims, and across every reviewer column in reviewer-workbook.xlsx. |
| QA-14 | No credentials or secrets appear in outputs | **PASS** | Regex scan of all JSON outputs found no key/secret/token patterns. |
| QA-15 | Checkpoint counters agree with the actual outputs / run report | **PASS** | checkpoint sourcesAccepted=3 == sources.json (3); claimsExtracted=13 == candidate-claims.json (13); pdfsDownloaded=0. |
| QA-16 | The next manual run can determine exactly where to resume | **PASS** | checkpoint.nextRecommendedOperation gives topicId=T-UCX-03, searchId=S-UCX-03-a, cursor=0, firstNewSourceId=SRC-035, firstNewClaimId=CLM-128; pendingSearches has 2 queued items. |
| QA-17 | All JSON output files parse | **PASS** | 7 JSON files parsed OK. |
| QA-18 | Checkpoint validates against the versioned checkpoint schema | **PASS** | checkpoint.json validates against checkpoint.schema.json (draft-07). |
| QA-19 | No source or claim advanced beyond pending_clinical_review; nothing marked approved | **PASS** | All claims lifecycleState=extracted / reviewStatus=pending_clinical_review. Sources are 'extracted' (SRC-028/033) or 'eligible' (SRC-034). No 'approved' anywhere. |
| QA-20 | Nothing promoted to production app / vector index / live answer set | **PASS** | ingestion-manifest.targetIndex = NONE (staged package only). No app code, deployment or Vercel change. No scheduler/cron/Action created. |
| QA-21 | reviewer-workbook.xlsx opens and every required sheet is present and populated | **PASS** | Opened OK. Sheets: ['Run Summary', 'Sources', 'Candidate Claims', 'Question Coverage', 'Conflicts', 'Evidence Gaps', 'Licensing and Access', 'QA Results', 'Method and Limitations']. Rows per sheet: Run Summary=23, Sources=7, Candidate Claims=17, Question Coverage=18, Conflicts=9, Evidence Gaps=13, Licensing and Access=7, QA Results=25, Method and Limitations=17 |

## Interpretation

- Every candidate claim is a **verbatim substring** of its source's retrieved structured abstract (QA-03), mapped to a real source (QA-01) and a real Reddit question-tree node (QA-11).
- **UC vs IBD-general is preserved** (QA-05, QA-06): the 6 STRIDE-II claims stay `ibd_general`; only the UC-specific AGA guideline yields `ulcerative_colitis` claims. No Crohn's-only evidence was converted to UC.
- **No restricted content was copied** (QA-08): 0 PDFs; a reachable Unpaywall PDF for SRC-028 was left alone.
- **Lifecycle ceiling respected** (QA-19): everything is `extracted` / `pending_clinical_review`; nothing `approved`; every human-review / clinical-review / decision / date field is blank (QA-13).
- **Resumable** (QA-15, QA-16): checkpoint counters equal the actual outputs and the checkpoint names the exact next operation, topic, search ID, cursor, and first free IDs.
- **Schema-valid & parseable** (QA-17, QA-18): all JSON parses; the checkpoint validates against the versioned draft-07 schema.
- **Workbook** (QA-21): opens; all 9 required sheets present and populated.

## Not covered by automated QA (needs human / clinical review)

- Clinical correctness and safety of every normalized claim.
- Whether abstract-level locators are sufficient, or full-text page/section locators must be added before use.
- Whether the AGA fecal-calprotectin thresholds should be surfaced to patients at all, and with what framing.
- Canada/US regional transfer (assay calibration, drug access) — assessed but not clinician-confirmed (GAP-09).
- Reconciliation with the never-materialized planned `SRC-027…032` / `CLM-101…114` set.
