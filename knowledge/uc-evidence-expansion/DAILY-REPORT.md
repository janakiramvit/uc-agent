# UC evidence discovery - daily report 2026-11-15

Run `uc-exp-4daef5e63bb7` - https://github.com/janakiramvit/uc-agent/actions/runs/43753430405

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-13 .. 2026-11-15
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-13 .. 2026-11-15
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-13 .. 2026-11-15
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-13 .. 2026-11-15
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-13 .. 2026-11-15

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-13 .. 2026-11-15 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-13 .. 2026-11-15 | 3 | 51 | 51 | 34 | 40 | 3 | 5 | 3 | 7 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-13 .. 2026-11-15 | 6 | 30 | 30 | 17 | 23 | 5 | 0 | 2 | 2 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-13 .. 2026-11-15 | 3 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-13 .. 2026-11-15 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-13 .. 2026-11-15 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-13 .. 2026-11-15 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-13 .. 2026-11-15 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 28 | | 82 | 52 | 64 | 8 | 5 | 5 | 9 | |

## Per-provider detail

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-13..2026-11-15) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/13..2026/11/13]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/14..2026/11/14]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/15..2026/11/15]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-13 .. 2026-11-15

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-13 TO 2026-11-13]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-14 TO 2026-11-14]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-15 TO 2026-11-15]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14614
- Duplicates: 17 cross-provider/in-provider, 23 already seen in earlier runs
- Rejected: not_relevant x3
- Deferred: missing_required_metadata x4, no_usable_abstract x1

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/13..2026/11/13]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/14..2026/11/14]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/15..2026/11/15]`
- Canary (wide window, same syntax): 4562
- Duplicates: 13 cross-provider/in-provider, 10 already seen in earlier runs
- Rejected: not_relevant x5

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-13,2026-11-13]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-14,2026-11-14]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-15,2026-11-15]`
- Canary (wide window, same syntax): 542
- Duplicates: 0 cross-provider/in-provider, 1 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/13..2026/11/13]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/14..2026/11/14]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/15..2026/11/15]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-13 .. 2026-11-15
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-13..2026-11-15) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/13..2026/11/13]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/14..2026/11/14]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/15..2026/11/15]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-13 .. 2026-11-15

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/13..2026/11/13]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/14..2026/11/14]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/15..2026/11/15]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-13 .. 2026-11-15
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-13 .. 2026-11-15
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-13..2026-11-15)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-13 .. 2026-11-15

## Accepted this run (staging only)

- `SRC-157` [published_study] Cognitive screening performance in patients with inflammatory bowel disease in remission: a case-control study
- `SRC-158` [published_study] Bioactive metabolites and botanical preparations from plants used as medicines and foods in ulcerative colitis: a mechanism-oriented narrative review of multi-target regulation
- `SRC-159` [published_study] A wearable perspiration biosensor for continuous biomarker monitoring in inflammatory bowel disease: Feasibility, concordance, and exploratory temporal dynamics
- `SRC-160` [published_study] Sequence-dependent real-world efficacy of anti-TNF antibodies and vedolizumab in ulcerative colitis: a propensity score-weighted cohort study
- `SRC-161` [published_study] Microbiota transplant therapy improves ulcerative colitis symptoms independent of donor engraftment in a pilot randomized placebo-controlled trial
