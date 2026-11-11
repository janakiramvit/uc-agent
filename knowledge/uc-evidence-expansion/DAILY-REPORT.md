# UC evidence discovery - daily report 2026-11-11

Run `uc-exp-f96662ebf3d4` - https://github.com/janakiramvit/uc-agent/actions/runs/43100207814

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **ERROR** `REPEATED_UNEXPECTED_ZERO` (europepmc): 4 consecutive runs returned zero for a provider that normally returns results daily
- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-11
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-11
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-11
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-11
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-11

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-11 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-10 .. 2026-11-11 | 4 | 25 | 25 | 25 | 13 | 3 | 2 | 7 | 6 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-10 .. 2026-11-11 | 2 | 4 | 4 | 4 | 4 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 20 | | 29 | 29 | 17 | 3 | 2 | 7 | 6 | |

## Per-provider detail

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/11..2026/11/11]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-11
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-10..2026-11-11) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/11..2026/11/11]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-11

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/11..2026/11/11]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-11
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-10..2026-11-11)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-11

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-10..2026-11-11) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/11..2026/11/11]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-11

### Europe PMC

- Status: **NO NEW RECORDS**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-10 TO 2026-11-10]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-11 TO 2026-11-11]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14562
- Zero-result reason: provider healthy (wide-window canary returned 14562); no new matching records in 2026-11-10 .. 2026-11-11

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/11..2026/11/11]`
- Canary (wide window, same syntax): 4561
- Duplicates: 0 cross-provider/in-provider, 13 already seen in earlier runs
- Rejected: not_relevant x3
- Deferred: no_usable_abstract x2

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-10 .. 2026-11-11
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-10,2026-11-10]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-11,2026-11-11]`
- Canary (wide window, same syntax): 540
- Duplicates: 0 cross-provider/in-provider, 4 already seen in earlier runs

## Accepted this run (staging only)

- `SRC-119` [published_study] Lactobacillus-Based Therapy for Ulcerative Colitis: From Strain Heterogeneity and TCM-Mediated Modulation to Engineered Delivery and Precision Translation
- `SRC-120` [published_study] Caffeic acid regulates the gut microbiota-tryptophan metabolic axis to improve intestinal barrier function and relieve ulcerative colitis
- `SRC-121` [published_study] Weiling decoction alleviates dampness-exacerbated ulcerative colitis in a spleen-deficient mouse model: associations with the gut microbiota composition and TLR4/NF-κB-related inflammatory responses
- `SRC-122` [published_study] Clinical profiles and management strategies in older adults with mild-to-moderate ulcerative colitis: a multicenter, comparative, real-world study
- `SRC-123` [published_study] Real-world paediatric inflammatory bowel disease surgery: International variation in care and practice
- `SRC-124` [published_study] Infliximab for Refractory Diffuse Sclerosing Osteomyelitis of the Mandible Associated With Ulcerative Colitis: A Case Report
- `SRC-125` [published_study] Intestinal Ultrasound in Inflammatory Bowel Disease: From Point-of-Care Assessment to Standardized Treat-to-Target Monitoring
