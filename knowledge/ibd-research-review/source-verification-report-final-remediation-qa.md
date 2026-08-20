# Final independent QA of the targeted-remediation IBD evidence package

## Decision

**NOT_READY_FOR_HUMAN_APPROVAL**

No source or claim was approved. Human-review fields remain blank.

The targeted source-text remediation is substantially successful: all 60 supported active claims resolve to active authoritative sources, the six ECCO locators are precise, CLM-097 is narrowed, CLM-098 through CLM-100 are directly supported by ESPEN, and CLM-092 is correctly excluded. Approval preparation still fails because 17 ready-tagged claims have inaccurate or missing condition/outcome metadata, including five ESPEN rows with no core scope metadata. The workbook also lacks frozen headers and decision dropdown validation.

## Scope and method

The review was confined to `/Users/janakirampulipati/ibd-research-review`. It independently checked:

- the final-remediation workbook and three final-remediation reports;
- all 61 active claim rows;
- official ECCO article text and packaged authoritative captures;
- the official ESPEN 2023 guideline PDF and packaged extraction;
- packaged PubMed abstracts and public-health webpages;
- active-source references, locators, claim IDs, replacement links, reviewer fields, counts, formulas, workbook controls, and all eight rendered source sheets.

The prohibited application repository was not accessed by this QA. Its historical non-modification during remediation could not be independently inspected without violating the user’s no-touch instruction; that assertion is supported by the remediation audit records.

## Task 1 — CLM-081 through CLM-086

| Claim | Classification | Independent finding |
|---|---|---|
| CLM-081 | `qa_pass` | Authentic Statement 1 text; precise Section 3 locator; IBD-general applicability is appropriate. |
| CLM-082 | `qa_pass_with_limitation` | Text and Section 4.1 locator pass. Outcome metadata says general patient education, but the claim is about evidence quality and endpoint coverage. |
| CLM-083 | `qa_fail_scope` | Statement 21.1 and Section 4.3.2 locator pass, and the final wording preserves no-data/mechanism/obstructive-symptom limitations. The row is incorrectly tagged for UC and general IBD, uses a general-education outcome instead of obstruction risk, and assigns high confidence despite EL5 mechanism-based reasoning. |
| CLM-084 | `qa_pass_with_limitation` | Practice Point 2A sentence 1 passes. Outcome metadata should identify inflammatory burden rather than general patient education. |
| CLM-085 | `qa_pass_with_limitation` | Practice Point 2A sentence 3 supports the claim. The legacy supporting-excerpt field is a faithful condensation rather than the exact sentence; the separate authoritative-passage field preserves the exact text. |
| CLM-086 | `qa_pass_with_limitation` | Practice Point 2B sentence 1 supports the claim. Outcome metadata should identify maintenance of remission; the legacy excerpt is condensed, while the exact authoritative passage is retained separately. |

Authoritative ECCO sources:

- https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055
- https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895

The package’s non-empty `SRC-021` and `SRC-022` verification captures contain the cited passages.

## Task 2 — CLM-097 through CLM-100

All four claims have unique IDs, active SRC-026 references, direct official-PDF support, journal page 357 locators, and intact split/audit links.

| Claim | Classification | Support and locator | Limitation |
|---|---|---|---|
| CLM-097 | `qa_pass_with_limitation` | Section 5, Recommendation 15 commentary, final paragraph | Missing condition applicability, disease context, outcome type, study type, and confidence |
| CLM-098 | `qa_pass_with_limitation` | Section 5, Recommendation 16 | Same five core metadata fields are missing |
| CLM-099 | `qa_pass_with_limitation` | Section 5, Recommendation 17 | Same five core metadata fields are missing |
| CLM-100 | `qa_pass_with_limitation` | Commentary for Recommendations 16–17, paragraph immediately before Recommendation 18 | Same five core metadata fields are missing |

CLM-097 is now atomic. CLM-098 and CLM-099 are population-specific recommendation statements. CLM-100 is one evidence-limitation statement drawn from one guideline sentence. The 2017 source is retained only in the superseded/replacement audit and is not cited as current guidance.

Official ESPEN source:

https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf

CLM-096, another active 2023 ESPEN replacement claim, is also missing the same five core metadata fields.

## Task 3 — CLM-092 exclusion

Classification: **`correctly_excluded`**

- Evidence status: `still_needs_evidence`
- Final-QA eligibility: `unresolved_not_approval_ready`
- Approved-export eligibility: `excluded_until_evidence_resolved_and_explicitly_approved`
- Ready-for-review count inclusion: no
- Visible in `Unresolved Claims`: yes
- Duplicate supported occurrence: none
- Missing evidence: the webpage version date is unconfirmed and the broad worse-outcomes statement lacks sufficiently specific, directly appraised evidence.

No approved-data export artifact was present.

## Task 4 — active-claim reconciliation

| Metric | Independent result |
|---|---:|
| Ready-tagged active claims | 60 |
| Active claims needing evidence | 1 |
| Total active claims | 61 |
| Cumulative removed original claims | 37 |
| Original claims replaced | 2 |
| New split claims created in final remediation | 3 |
| Duplicate active IDs | 0 |
| Invalid replacement links | 0 |
| Invalid active-source references | 0 |

The arithmetic statement `60 + 1 = 61` is correct. Gaps among CLM-001 through CLM-095 are accounted for by the removed/replaced ledger; CLM-096 through CLM-100 are present and unique.

## Task 5 — source, locator, and metadata integrity

Across all 61 active rows:

- active source exists: 61 of 61;
- reference to superseded SRC-003: 0;
- authoritative excerpt/passage traceability: 61 of 61;
- precise locators: 61 of 61;
- formula-error matches: 0;
- blank reviewer fields: 61 of 61.

However, **17 ready-tagged claims fail metadata integrity**:

- Overbroad or incomplete condition applicability: CLM-018, CLM-019, CLM-025, CLM-048, CLM-071, CLM-083.
- Inaccurate outcome type: CLM-018, CLM-025, CLM-026, CLM-030, CLM-033, CLM-048, CLM-082, CLM-083, CLM-084, CLM-086.
- Missing condition applicability, disease context, outcome type, study type, and confidence: CLM-096 through CLM-100.

These sets overlap and affect 17 unique claims.

The most important scope error is CLM-083: its evidence is specifically stricturing Crohn’s disease with obstructive symptoms, but its active tags include ulcerative colitis and general IBD. This could cause a product to surface Crohn’s-specific mechanism-based guidance in the wrong condition context.

## Task 6 — safety and product boundaries

No supported claim directly diagnoses IBD, predicts an individual flare, recommends stopping or changing medication, guarantees an outcome, or presents symptom improvement as proof of reduced inflammation.

The following require strict attribution and boundary preservation:

- CLM-038 and CLM-040: weak-to-moderate causal language comes from a Bradford-Hill review and must not be strengthened.
- CLM-073: the source’s short-term safety finding must not be generalized beyond the studied setting.
- CLM-083, CLM-084, CLM-086, CLM-098, and CLM-099: guideline or population statements must not become individualized diet prescriptions.

The incorrect condition tags described above are a safety-boundary defect even though the prose itself is source-attributed.

## Task 7 — workbook integrity

The source workbook contains the required eight sheets and all were visually inspected. Layout, wrapping, widths, status colors, blank human-input cells, tables, and filters are legible.

Passed:

- 8 exact sheet names
- filter-enabled tables on the 7 data sheets
- blank human-review fields
- no hidden approval defaults
- unique IDs and valid source references
- 60/1/61 counts
- no formula errors or broken references
- no active reference to SRC-003
- visual inspection of all 8 sheets

Failed:

- **Frozen headers:** all eight worksheet XML files contain no frozen-pane definition.
- **Valid decision dropdowns:** the workbook contains zero data-validation definitions.

## Task 8 — report reconciliation

The workbook, source report, completion report, and JSON summary agree on:

- 60 ready-tagged, 1 unresolved, 61 total;
- 37 removed, 2 replaced, 3 new split claims;
- 25 active sources and 26 source rows including superseded;
- 67 tests passed;
- 0 formula errors;
- blank reviewer fields;
- no human approvals.

Discrepancies:

1. The reports describe 60 claims as ready for final QA without disclosing that 17 have inaccurate or missing condition/outcome metadata.
2. The reports do not disclose the absence of frozen panes and decision-field dropdown validations.
3. The historical repository-isolation assertion is audit-record-supported, not independently rechecked, because repository access was prohibited.

## Required remediation before human approval

1. Correct the 17 row-level metadata defects, including complete metadata for CLM-096 through CLM-100.
2. Restrict CLM-083 to Crohn’s disease, use an obstruction-risk outcome, and align confidence/limitations with EL5 mechanism-based reasoning.
3. Freeze table headers on the data sheets.
4. Add blank-default reviewer-decision dropdowns without setting any approval value.
5. Rerun this independent QA and preserve CLM-092’s exclusion.

**Overall status: NOT_READY_FOR_HUMAN_APPROVAL**
