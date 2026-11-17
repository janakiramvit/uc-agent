# UC evidence discovery - daily report 2026-11-17

Run `uc-exp-959cc2beb321` - https://github.com/janakiramvit/uc-agent/actions/runs/44186439276

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-16 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-16 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-16 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-16 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-16 .. 2026-11-17

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PubMed/MEDLINE | published_study | **OK** | 2026-11-16 .. 2026-11-17 | 4 | 23 | 23 | 12 | 13 | 2 | 1 | 7 | 8 | no |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-16 .. 2026-11-17 | 2 | 11 | 11 | 11 | 11 | 0 | 0 | 0 | 0 | no |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-16 .. 2026-11-17 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-16 .. 2026-11-17 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-16 .. 2026-11-17 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-16 .. 2026-11-17 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-16 .. 2026-11-17 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| Europe PMC | published_study | **OK** | 2026-11-10 .. 2026-11-17 | 10 | 134 | 134 | 133 | 107 | 5 | 22 | 0 | 0 | no |
| **All** | | | | 28 | | 168 | 156 | 131 | 7 | 23 | 7 | 8 | |

## Per-provider detail

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 4542
- Duplicates: 11 cross-provider/in-provider, 2 already seen in earlier runs
- Rejected: not_relevant x2
- Deferred: no_usable_abstract x1

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-16,2026-11-16]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-17,2026-11-17]`
- Canary (wide window, same syntax): 544
- Duplicates: 0 cross-provider/in-provider, 11 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-16 .. 2026-11-17
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-16..2026-11-17) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-16 .. 2026-11-17

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-16 .. 2026-11-17
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-16..2026-11-17)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-16 .. 2026-11-17

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-16 .. 2026-11-17
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-16..2026-11-17) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-16 .. 2026-11-17

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-10 TO 2026-11-10]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-11 TO 2026-11-11]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-12 TO 2026-11-12]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-13 TO 2026-11-13]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-14 TO 2026-11-14]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-15 TO 2026-11-15]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-16 TO 2026-11-16]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-17 TO 2026-11-17]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14729
- Duplicates: 1 cross-provider/in-provider, 106 already seen in earlier runs
- Rejected: not_relevant x5
- Deferred: missing_required_metadata x22

## Accepted this run (staging only)

- `SRC-183` [published_study] The role of histologic remission as disease clearance: Emerging treat-to-target in pediatric ulcerative colitis
- `SRC-184` [published_study] Addition of Curcumin-QingDai correlates with clinical benefit in pediatric ulcerative colitis and inflammatory bowel disease-unclassified
- `SRC-185` [published_study] High rates of flares after anti-tumor necrosis factor withdrawal in pediatric inflammatory bowel disease: A multi-center study
- `SRC-186` [published_study] Epithelial inflammatory memory in ulcerative colitis: molecular mechanisms and translational implications
- `SRC-187` [published_study] Immune-epithelial coordination of barrier repair in inflammatory bowel disease: from cell survival to functional healing
- `SRC-188` [published_study] The metabolic crossfire hypothesis: glycolytic crosstalk between immune and epithelial cells in ulcerative colitis pathogenesis
- `SRC-189` [published_study] Dose escalation of IL-23 inhibitors in inflammatory bowel disease: a systematic review of efficacy and safety
