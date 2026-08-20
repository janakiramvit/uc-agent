# IBD evidence remediation — completion report

Date: 2026-07-30  
Status: completed and stopped for human approval  
Approval state: none granted

## Completion outcome

The bounded remediation task is complete. The standalone evidence package now has corrected source identities, an auditable superseded-source replacement, exact claim accounting, claim-level locators, bounded gap decisions, separate search-budget logs, and an eight-sheet workbook ready for second independent QA.

The work remained inside `/Users/janakirampulipati/ibd-research-review`. The excluded application repository was not inspected or touched. No application, RAG, embeddings, retrieval, LangChain/LangGraph, Azure AI Search, API, UI, or production-infrastructure work was performed.

## Delivered files

- `ibd-evidence-review-remediated.xlsx`
- `source-verification-report-remediated.md`
- `run-summary-remediated.json`
- `completion-report-remediated.md`

Supporting audit data:

- `processing/remediation/remediation-data.json`
- `checkpoints-remediation/remediation-data.json`
- `logs/remediation/workbook-verification.json`
- `archive/incorrect-source-mappings/`
- `archive/superseded-sources/`
- `archive/removed-claims/`
- `previews-remediated/`

## Backup and preservation

Before remediation, the five authoritative/working inputs were copied to:

`/Users/janakirampulipati/ibd-research-review/backups/2026-07-30T075404-0700-remediation`

The directory includes SHA-256 checksums. Incorrect mappings, the superseded source, and removed/replaced claims were archived rather than deleted.

## Key results

- 11 incorrect DOI/PMCID/full-text mappings corrected and reverified
- SRC-003 classified as superseded and mapped to SRC-026, the official 2023 ESPEN update
- 4 legal full-text access issues remain unresolved
- 4 effective abstract-only sources remain
- 95 original claims reconciled exactly:
  - 2 retained unchanged
  - 53 retained revised
  - 37 removed
  - 2 replaced by new
  - 1 still needs evidence
- 6 MVP gaps classified:
  - 1 resolved for MVP
  - 4 partially resolved with mandatory answer limits
  - 1 unresolved and excluded from feature scope

## Workbook verification

The workbook contains exactly these eight sheets:

1. Sources
2. Claims
3. Source Mapping Audit
4. Removed and Replaced Claims
5. Superseded Sources
6. Evidence Gap Resolution
7. Verification and Access Issues
8. Remediation Summary

All eight sheets were rendered and visually inspected. Titles, headers, wrapped text, row heights, status highlighting, audit columns, and blank yellow human-input fields are visible. The workbook formula-error scan found no error values.

## Automated tests

Command:

`PYTHONPATH=. .venv/bin/pytest -q`

Result:

- Passed: 53
- Failed: 0

The tests cover identifier consistency, PubMed/PMC title-author-year matching, wrong-mapping rejection, archive history, superseded-source replacement, old/new claim mapping, rejected-claim removal, revised-claim traceability, exact 95-claim reconciliation, locator requirements, separate search budgets, blank review fields, evidence-gap limits, exact workbook sheets, formula scanning, and visual-validation outputs.

## Remaining limitations

- Four records are supported only by public abstracts.
- No reuse or republication licence has been inferred from public access.
- Guideline recommendations include consensus and evidence extrapolation.
- Canada/US transferability requires local clinical, dietetic, food-availability, cultural, and healthcare-pathway review.
- High-risk topics remain clinician-led and cannot be personalized from this evidence package.
- The biomarker feature gap remains excluded.
- CLM-092 remains explicitly marked as needing more evidence.

## Required next action

Stop here. A second independent QA pass and explicit human decisions are required. All source decisions, source notes, claim decisions, user-edited claims, and reviewer notes remain blank.
