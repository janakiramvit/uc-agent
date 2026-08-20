# Independent QA of remediated IBD evidence

## Decision

**NOT_READY_FOR_HUMAN_APPROVAL**

No source or claim was approved. Human-review fields remain blank.

The remediation is materially improved: all 11 known DOI/PMCID mismatches were corrected and independently reverified, the ESPEN 2023 replacement identity is correct, all 95 original claims reconcile exactly, and no active claim cites superseded SRC-003. However, seven active claims are not approval-ready because of two material evidence-traceability findings.

## Scope and method

This was a second independent QA review of the remediated package in `/Users/janakirampulipati/ibd-research-review`. Checks used the packaged PubMed records, corrected JATS full texts, the official ESPEN PDF/text extraction, packaged public-health pages, and authoritative ECCO journal pages. The application repository was neither inspected nor modified.

The review checked source identity, active identifiers, archived incorrect files, source-to-claim references, excerpt presence, exact locator accuracy, full-claim support, ESPEN replacement handling, original-claim accounting, evidence gaps, blank reviewer fields, workbook structure, formula errors, and rendered sheet layout.

## Material findings

### F-001 — Six ECCO exact locators are false

Affected claims: `CLM-081` through `CLM-086`.

The six excerpts are authentic, but every active locator says `Official article webpage — heading "Abstract"`. The authoritative pages place the material elsewhere:

| Claim | Correct location |
|---|---|
| CLM-081 | SRC-021, section 3, “Translation and execution of dietary management,” Statement 1 |
| CLM-082 | SRC-021, section 4.1 introductory paragraph |
| CLM-083 | SRC-021, stricturing Crohn’s disease section and applicable statement/commentary |
| CLM-084 | SRC-022, section 3.8.2.1, Practice Point 2A, sentence 1 |
| CLM-085 | SRC-022, section 3.8.2.1, Practice Point 2A, sentence 3 |
| CLM-086 | SRC-022, section 3.8.2.2, Practice Point 2B |

The packaged `SRC-021.html` and `SRC-022.html` files are also zero bytes. The official pages are accessible and support the excerpts, but the package does not contain a usable local verification copy.

Required correction: replace all six locators with the relevant numbered section, statement, or practice point. Package a non-empty authoritative capture where permitted, or explicitly document online-only verification and preserve the authoritative URL.

Authoritative pages:

- SRC-021: https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055
- SRC-022: https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895

### F-002 — CLM-097 is broader than its displayed evidence

`CLM-097` states three propositions:

1. no single oral diet can be recommended for all active IBD;
2. selected Crohn’s disease exclusion-diet approaches are supported for defined subgroups; and
3. long-term safety data are limited.

Its displayed excerpt and locator support only the first proposition: “Therefore, no ‘oral IBD diet’ can be generally recommended …”

The ESPEN document contains relevant nearby discussion of the Crohn’s Disease Exclusion Diet and unavailable long-term effectiveness/risk data, but those passages are not quoted or located in the active claim row.

Required correction: either narrow `CLM-097` to the displayed excerpt or add the exact supporting passages and journal-page-357 locators for the subgroup and long-term-data clauses.

Authoritative ESPEN source: https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf

## Source mapping QA

All 11 corrected mappings passed independent identity checks against the PubMed record identifiers and, where available, corrected JATS front matter:

| Source | Correct DOI | Correct PMCID | Result |
|---|---|---|---|
| SRC-004 | 10.1016/j.advnut.2024.100219 | PMC11063602 | PASS |
| SRC-006 | 10.1097/JS9.0000000000003019 | PMC12626460 | PASS |
| SRC-007 | 10.1186/s12937-016-0183-8 | PMC4942986 | PASS |
| SRC-008 | 10.3390/nu15173824 | PMC10489664 | PASS |
| SRC-009 | 10.1002/jgh3.12817 | PMC9667405 | PASS |
| SRC-010 | 10.1186/s13643-020-01426-2 | PMC7395978 | PASS |
| SRC-011 | 10.1093/advances/nmaa145 | PMC8166559 | PASS |
| SRC-013 | 10.1038/s41575-024-00893-5 | abstract-only | PASS |
| SRC-016 | 10.1053/j.gastro.2021.05.047 | PMC8396394 | PASS |
| SRC-018 | 10.1053/j.gastro.2019.03.015 | PMC6726378 | PASS |
| SRC-020 | 10.1136/bmj.n1554 | PMC8279036 | PASS |

Each rejected prior file is present in `archive/incorrect-source-mappings`. Active source rows use the corrected identifier fields, and active claims do not reference archived incorrect files.

## ESPEN replacement QA

- SRC-003 is correctly marked `superseded_replaced` and points to SRC-026.
- SRC-026 identity passes: 2023, DOI `10.1016/j.clnu.2022.12.004`, PMID `36739756`.
- CLM-096 passes excerpt, locator, scope, and safety review.
- CLM-097 fails full-claim support as described in F-002.
- Removed claims remain archived and traceable.

## Claim reconciliation and active-claim QA

The 95 original claims reconcile into mutually exclusive categories:

- 2 retained unchanged
- 53 retained revised
- 37 removed
- 2 replaced by new claims
- 1 still needs evidence

Total: **95**.

The active set contains 58 rows, including replacement claims CLM-096 and CLM-097:

- 50 PASS
- 7 FAIL
- 1 NEEDS_EVIDENCE

The seven failures are CLM-081 through CLM-086 and CLM-097. CLM-092 remains the single explicit needs-evidence claim; its webpage version date and broad outcome wording are not resolved.

All 43 PubMed-abstract claim excerpts were found in the cited abstracts and their stated sentence numbers were independently reproduced. Public-health page excerpts for SRC-023 through SRC-025 were present at the cited headings. No active claim cites SRC-003.

## MVP evidence-gap QA

The declared accounting is preserved:

- 1 resolved for MVP: physical activity
- 4 partially resolved with mandatory answer limits: post-surgical context, stricture/obstruction risk, adverse effects, alcohol
- 1 excluded: biomarker-improvement claims

The safe-answer limits are appropriately conservative. They are evidence boundaries, not clinical approval. The stricture/obstruction gap inherits the SRC-021 locator-packaging limitation described in F-001.

## Workbook and package integrity

- Required QA workbook sheets: 8 of 8 present.
- Source rows including superseded: 26.
- Active sources: 25.
- Active claims: 58.
- Original claims reconciled: 95.
- Corrected mappings: 11.
- Human reviewer fields: blank.
- Archived source referenced by an active claim: 0.
- Formula-error scan: 0 matches.
- Visual render validation: all 8 sheets rendered and inspected; no clipping, overlap, unreadable headers, or broken layout was observed.

## Approval preparation

The package should return to remediation for the seven affected active claims. After the six ECCO locators and CLM-097 evidence scope are corrected, rerun this independent QA before asking a human reviewer to approve any source or claim.

**Overall status: NOT_READY_FOR_HUMAN_APPROVAL**
