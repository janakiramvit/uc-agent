# IBD evidence source verification — final targeted remediation

Date: 2026-07-30  
Status: ready for one final independent QA; not approved  
Scope: remaining QA failures only

## Scope controls

This run was confined to `/Users/janakirampulipati/ibd-research-review`. The application repository was not inspected or modified. No broad research, evidence import, RAG, embeddings, Azure services, API work, UI work, LangChain, or LangGraph work was performed.

The authoritative inputs were the remediated workbook, independent-QA workbook and reports, the two official ECCO journal articles, and the official ESPEN 2023 PDF.

## ECCO locator corrections

All six authentic ECCO excerpts were preserved. Their false `Abstract` locators were replaced with precise numbered locations:

| Claim | Source | Corrected locator | Verification result |
|---|---|---|---|
| CLM-081 | SRC-021 | Section 3, “Translation and execution of dietary management”; Statement 1; paragraph beginning “Statement 1: In the absence…” | PASS |
| CLM-082 | SRC-021 | Section 4.1, “Dietary therapy to induce and maintain remission of IBD”; opening paragraph; sentence beginning “Most evidence…” | PASS |
| CLM-083 | SRC-021 | Section 4.3.2, “Strictures”; Statement 21.1, paragraph 1 | PASS |
| CLM-084 | SRC-022 | Section 3.8.2.1, “Dietary therapy for the induction of remission in CD”; Practice Point 2A, sentence 1 | PASS |
| CLM-085 | SRC-022 | Section 3.8.2.1; Practice Point 2A, sentence 3 | PASS |
| CLM-086 | SRC-022 | Section 3.8.2.2, “Dietary therapy for the maintenance of remission in CD”; Practice Point 2B, sentence 1 | PASS |

Authoritative URLs:

- SRC-021: `https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055`
- SRC-022: `https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895`

Non-empty official-article captures used for reproducible verification are stored at:

- `sources/final-remediation/SRC-021-authoritative.html`
- `sources/final-remediation/SRC-022-authoritative.html`

The direct Oxford article URLs returned access restrictions to automated download, so the captures use Oxford’s public article-minimal delivery endpoint. They are retained for verification only; downstream reuse rights were not assessed.

### CLM-083 narrowing

The independent QA’s suggested Section 4.2.2 locator did not match the authoritative article. The verified location is Section 4.3.2.

The final wording now retains every material limitation in Statement 21.1:

- no supporting data for managing stricturing Crohn’s disease with a modified or low-fibre diet;
- the rationale is mechanism-based;
- the population has stricturing Crohn’s disease with obstructive symptoms; and
- the statement is not individualized treatment advice.

## CLM-097 remediation

The former CLM-097 combined multiple substantive assertions. The final version is atomic:

- CLM-097 retains only the directly supported statement that no oral IBD diet can be generally recommended to promote remission in active IBD.
- Locator: ESPEN journal page 357, Section 5, Recommendation 15 commentary, final paragraph.

The additional independently supported ideas were split:

| New claim | Atomic idea | Exact locator |
|---|---|---|
| CLM-098 | Pediatric Crohn’s disease exclusion diet plus partial enteral nutrition as an alternative to exclusive enteral nutrition | Journal page 357, Recommendation 16 |
| CLM-099 | Adult Crohn’s disease exclusion diet with or without enteral nutrition in mild-to-moderate active disease | Journal page 357, Recommendation 17 |
| CLM-100 | Long-term effectiveness and possible nutritional-deficiency/eating-behaviour risk data are not yet available | Journal page 357, commentary for Recommendations 16 and 17, paragraph ending immediately before Recommendation 18 |

Official ESPEN source:

`https://www.espen.org/files/ESPEN-Guidelines/ESPEN_guideline_on_Clinical_nutrition_in_inflammatory_bowel_disease.pdf`

Each final claim has one atomic idea, an exact excerpt, and a page/section/recommendation/paragraph locator.

## CLM-092 status

CLM-092 was not researched further.

- Evidence status: `still_needs_evidence`
- Final-QA eligibility: `unresolved_not_approval_ready`
- Future approved-export eligibility: `excluded_until_evidence_resolved_and_explicitly_approved`

The unresolved evidence is stated explicitly: the webpage version date remains unconfirmed, and the broad worse-outcomes wording lacks sufficiently specific, directly appraised evidence in the package.

## Active-claim reconciliation

| Category | Count |
|---|---:|
| Active claims ready for final independent QA | 60 |
| Active claims needing more evidence | 1 |
| New split claims created | 3 |
| Targeted claims removed in this run | 0 |
| Total active claims | 61 |
| Cumulative original claims removed in prior remediation | 37 |

The original 95-claim accounting remains unchanged. The active count increased from 58 to 61 solely because CLM-097’s independently supported assertions were separated into three new atomic claims.

All active claim IDs are unique, every active claim references one of the 25 active sources, and no active claim references superseded SRC-003.

## Validation result

- Existing and focused tests passed: 67
- Failed tests: 0
- Generic active locators: 0
- Blank human-review fields: PASS
- Workbook formula-error matches: 0
- Workbook sheets rendered and inspected: 8 of 8

## Remaining limitations

- CLM-092 remains unresolved and excluded.
- The Oxford captures and ESPEN PDF are used for evidence verification only; no reuse licence is inferred.
- Evidence remains pending one final independent QA and subsequent explicit human decisions.
- No source or claim is approved.

Hard stop: await one final independent QA.
