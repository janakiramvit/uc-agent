# UC evidence discovery - daily report 2026-11-13

Run `uc-exp-bad40544162e` - https://github.com/janakiramvit/uc-agent/actions/runs/43504799937

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-11 .. 2026-11-13
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-11 .. 2026-11-13
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-11 .. 2026-11-13
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-11 .. 2026-11-13
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-11 .. 2026-11-13

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-11 .. 2026-11-13 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-11 .. 2026-11-13 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-11 .. 2026-11-13 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-11 .. 2026-11-13 | 7 | 76 | 76 | 72 | 47 | 16 | 10 | 3 | 3 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-11 .. 2026-11-13 | 6 | 24 | 24 | 11 | 15 | 4 | 0 | 5 | 1 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-11 .. 2026-11-13 | 3 | 11 | 11 | 11 | 10 | 0 | 0 | 1 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-11 .. 2026-11-13 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-11 .. 2026-11-13 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 32 | | 111 | 94 | 72 | 20 | 10 | 9 | 4 | |

## Per-provider detail

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/12..2026/11/12]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/13..2026/11/13]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-11 .. 2026-11-13
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-11..2026-11-13)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-11 .. 2026-11-13

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-11..2026-11-13) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/12..2026/11/12]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/13..2026/11/13]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-11 .. 2026-11-13

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-11 TO 2026-11-11]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-12 TO 2026-11-12]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-13 TO 2026-11-13]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14640
- Duplicates: 4 cross-provider/in-provider, 43 already seen in earlier runs
- Rejected: not_relevant x15, out_of_scope x1
- Deferred: missing_required_metadata x10

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/12..2026/11/12]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/13..2026/11/13]`
- Canary (wide window, same syntax): 4560
- Duplicates: 13 cross-provider/in-provider, 2 already seen in earlier runs
- Rejected: not_relevant x4

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-11,2026-11-11]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-12,2026-11-12]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-13,2026-11-13]`
- Canary (wide window, same syntax): 543
- Duplicates: 0 cross-provider/in-provider, 10 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/12..2026/11/12]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/13..2026/11/13]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-11 .. 2026-11-13
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-11 .. 2026-11-13
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-11..2026-11-13) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/12..2026/11/12]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/13..2026/11/13]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-11 .. 2026-11-13

## Accepted this run (staging only)

- `SRC-141` [published_study] A randomized controlled trial of alternate-day versus daily iron therapy in ulcerative colitis in remission
- `SRC-142` [published_study] Pediatric inflammatory bowel diseases in patients with genetic syndromes: A case-control multicentre SIGENP study
- `SRC-143` [published_study] Optimized W1/O/W2 Double Emulsions for Lactobacillus paracasei Encapsulation: Stability, Viability, and Anti-Inflammatory Efficacy in a Rat Model of Ulcerative Colitis
- `SRC-144` [published_study] Identification of Candidate Targets and Immune Characteristics of Salvianolic Acid E Against Ulcerative Colitis via Integrative Transcriptomic Analysis and Machine Learning
- `SRC-145` [published_study] Panhypopituitarism: A Case Report of a Rare Complication of Cerebral Venous Thrombosis Secondary to Ulcerative Colitis
- `SRC-146` [ongoing_trial] Cohorte Nantaise de Maladies Inflammatoires Chroniques Intestinales
- `SRC-147` [published_study] N-Trans Caffeoyltyramine Alleviates Ulcerative Colitis by Targeting FXR to Promote Epithelial Barrier Protection and M2 Macrophage Polarization
- `SRC-148` [published_study] Benefit-risk trade-offs among patients and providers selecting advanced therapy for moderate-to-severe ulcerative colitis
- `SRC-149` [published_study] Preoperative computed tomography measurement for predicting difficulty in hand-sewn ileal pouch-anal anastomosis: a refined single-center cohort study
