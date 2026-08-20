# IBD Evidence Research-Review Completion Report

**Status:** Complete for human review. All sources and claims remain pending; no review field is pre-populated.

## Workspace and boundaries

- Workspace: `/Users/janakirampulipati/ibd-research-review`
- The excluded application repository and its GitHub repository were not inspected, cloned, opened, edited, or otherwise touched.
- No application architecture, RAG, embeddings, retrieval, LangChain/LangGraph, Azure AI Search, API/UI changes, paid model calls, or production infrastructure were created.

## Primary files

- `ibd-evidence-review.xlsx`
- `source-verification-report.md`
- `run-summary.json`
- `config/research-limits.json`
- Validated schemas, bounded acquisition and processing scripts, fixtures/tests, caches, extracted text, candidate-claim JSON, chunks, logs, and eight workbook preview renders.

## Dependencies

- Local Python virtual environment
- Pydantic 2.11.7
- requests 2.32.4
- Beautiful Soup 4.13.4
- pypdf 5.8.0
- pytest 8.4.1
- Bundled `@oai/artifact-tool` 2.8.6+ for workbook authoring, rendering, and export

## Verification

- Automated tests: **25 passed, 0 failed**
- Workbook sheets: **8**
- Workbook review dropdown validations: **2**
- Formula/error scan: **0 matches**
- Human-review fields: **blank**
- Visual review: **all eight sheets rendered and inspected; timestamp display and empty-duplicates presentation were repaired and rechecked**

## Research run

- Searches performed: **33**
- Candidates discovered: **60**
- Sources selected: **25**
- Source-type breakdown: **5 guidelines, 12 reviews, 5 studies, 3 trusted expert/patient-information sources**
- Ulcerative-colitis-specific sources: **12**
- Crohn’s-disease-specific sources: **18**
- Shared-IBD sources: **21**
- Public full-text XML acquisitions: **11**
- PDFs acquired: **0**
- Abstract-only sources: **9**
- Public webpages: **5**, including **2 partial guideline acquisitions** for which public-page access returned HTTP 403 and traceable public-page fallback passages were retained for review
- Chunks generated: **142**
- Candidate claims retained: **95**
- Candidate claims rejected by safety/validation filters: **0**
- Duplicate groups detected: **0**
- Conflict/non-comparability flags preserved: **80**

## Coverage and regional gaps

Under-covered dimensions in this bounded first pass include:

- post-surgical context
- stricture or obstruction-risk context
- adverse effects
- biomarkers
- remission maintenance
- alcohol
- physical activity

Canada/US applicability was recorded separately from scientific relevance. **19** candidate claims directly discuss a Canada/US context; **76** require additional Canada/US transferability review. International evidence was retained when scientifically relevant, with practical food availability, cultural fit, labelling/fortification, cost, dietetic access, and healthcare-pathway limitations recorded.

## Limits and API usage

- Limit reached: **maximum selected sources (25)**
- No configured limit was silently exceeded.
- PubMed search requests: **33**
- PubMed metadata fetch requests: **1**
- Public full-text acquisition requests: **11**
- Successful official-web requests: **3**
- Estimated PubMed records fetched: **60**
- Paid model calls: **0**

## Unresolved limitations

- Nine sources are abstract-only, limiting methods, risk-of-bias, table, and subgroup appraisal.
- Two Oxford Academic guideline pages returned HTTP 403 to the scripted client; the failure is logged and the sources require direct human verification.
- Deterministic sentence extraction preserves supporting passages but may omit surrounding qualifications.
- Some candidate claims are background or methods statements retained for human triage rather than product-ready language.
- Conflict flags are deliberately sensitive and include non-comparability due to disease, disease state, outcome, population, evidence level, or region; they are not assertions that either claim is wrong.
- Coverage counts describe candidate claims, not approved evidence.

## Hard stop

The package must not be copied into an application, retrieval system, embedding index, API, or UI until a human explicitly approves individual sources and claims.
