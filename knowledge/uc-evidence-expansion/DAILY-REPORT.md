# UC evidence discovery - daily report 2026-11-28

Run `uc-exp-f7b2e7cb04d4` - https://github.com/janakiramvit/uc-agent/actions/runs/46192412657

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-26 .. 2026-11-28
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-26 .. 2026-11-28
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-26 .. 2026-11-28
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-26 .. 2026-11-28
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-26 .. 2026-11-28

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-26 .. 2026-11-28 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-26 .. 2026-11-28 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-26 .. 2026-11-28 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-26 .. 2026-11-28 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-20 .. 2026-11-28 | 24 | 367 | 367 | 359 | 266 | 39 | 60 | 2 | 4 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-26 .. 2026-11-28 | 8 | 57 | 57 | 5 | 54 | 1 | 0 | 2 | 5 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-26 .. 2026-11-28 | 3 | 7 | 7 | 7 | 7 | 0 | 0 | 0 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-26 .. 2026-11-28 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 51 | | 431 | 371 | 327 | 40 | 60 | 4 | 9 | |

## Per-provider detail

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-26..2026-11-28) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/27..2026/11/27]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/28..2026/11/28]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-26 .. 2026-11-28

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/27..2026/11/27]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/28..2026/11/28]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-26 .. 2026-11-28
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-26..2026-11-28)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-26 .. 2026-11-28

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-26..2026-11-28) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/27..2026/11/27]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/28..2026/11/28]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-26 .. 2026-11-28

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-20 .. 2026-11-28
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-21 TO 2026-11-21]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-22 TO 2026-11-22]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-23 TO 2026-11-23]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-24 TO 2026-11-24]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-25 TO 2026-11-25]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-26 TO 2026-11-26]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-27 TO 2026-11-27]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-28 TO 2026-11-28]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14837
- Duplicates: 8 cross-provider/in-provider, 258 already seen in earlier runs
- Rejected: not_relevant x38, out_of_scope x1
- Deferred: missing_required_metadata x59, no_usable_abstract x1

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/27..2026/11/27]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/28..2026/11/28]`
- Canary (wide window, same syntax): 4574
- Duplicates: 52 cross-provider/in-provider, 2 already seen in earlier runs
- Rejected: not_relevant x1

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-26,2026-11-26]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-27,2026-11-27]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-28,2026-11-28]`
- Canary (wide window, same syntax): 543
- Duplicates: 0 cross-provider/in-provider, 7 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-26 .. 2026-11-28
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/27..2026/11/27]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/28..2026/11/28]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-26 .. 2026-11-28
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

## Accepted this run (staging only)

- `SRC-338` [published_study] Obesity is associated with greater treatment requirements in ulcerative colitis: a propensity score-matched real-world study
- `SRC-339` [published_study] Molecular mechanisms of plant-derived saponins against ulcerative colitis: a narrative review
- `SRC-340` [published_study] Cross cohort evaluation of eight candidate genes associated with ferroptosis and mucosal inflammation in ulcerative colitis
- `SRC-341` [published_study] Efficacy and Safety of Janus Kinase Inhibitors in Older versus Younger Patients with Ulcerative Colitis: A Systematic Review and Meta-analysis
