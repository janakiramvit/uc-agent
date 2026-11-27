# UC evidence discovery - daily report 2026-11-27

Run `uc-exp-bf2271e21c38` - https://github.com/janakiramvit/uc-agent/actions/runs/46077188451

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-25 .. 2026-11-27
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-25 .. 2026-11-27
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-25 .. 2026-11-27
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-25 .. 2026-11-27
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-25 .. 2026-11-27

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-25 .. 2026-11-27 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-25 .. 2026-11-27 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-25 .. 2026-11-27 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-25 .. 2026-11-27 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-25 .. 2026-11-27 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-18 .. 2026-11-27 | 25 | 392 | 392 | 386 | 211 | 109 | 68 | 4 | 1 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-25 .. 2026-11-27 | 8 | 71 | 71 | 9 | 63 | 4 | 0 | 4 | 5 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-25 .. 2026-11-27 | 3 | 15 | 15 | 15 | 8 | 0 | 0 | 7 | 0 | yes |
| **All** | | | | 52 | | 478 | 410 | 282 | 113 | 68 | 15 | 6 | |

## Per-provider detail

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/27..2026/11/27]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-25 .. 2026-11-27
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-25..2026-11-27) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/27..2026/11/27]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-25 .. 2026-11-27

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/27..2026/11/27]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-25 .. 2026-11-27
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-25..2026-11-27)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-25 .. 2026-11-27

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-25..2026-11-27) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/27..2026/11/27]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-25 .. 2026-11-27

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-18 .. 2026-11-27; catching up 1 missed day(s)
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-18 TO 2026-11-18]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-19 TO 2026-11-19]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-21 TO 2026-11-21]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-22 TO 2026-11-22]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-23 TO 2026-11-23]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-24 TO 2026-11-24]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-25 TO 2026-11-25]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-26 TO 2026-11-26]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-27 TO 2026-11-27]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14897
- Duplicates: 6 cross-provider/in-provider, 205 already seen in earlier runs
- Rejected: not_relevant x108, out_of_scope x1
- Deferred: missing_required_metadata x67, no_usable_abstract x1

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/26..2026/11/26]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/27..2026/11/27]`
- Canary (wide window, same syntax): 4575
- Duplicates: 62 cross-provider/in-provider, 1 already seen in earlier runs
- Rejected: not_relevant x4

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-25 .. 2026-11-27
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-25,2026-11-25]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-26,2026-11-26]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-27,2026-11-27]`
- Canary (wide window, same syntax): 546
- Duplicates: 0 cross-provider/in-provider, 8 already seen in earlier runs

## Accepted this run (staging only)

- `SRC-322` [published_study] High sensitivity of anti-integrin αvβ6 immunoglobulin G serology in differentiating ulcerative colitis from acute diarrhoeal disease
- `SRC-323` [published_study] Predictors of Response to Anti-Tumour Necrosis Factor Treatment in Inflammatory Bowel Disease: A Nationwide Danish Cohort Study
- `SRC-324` [published_study] Exploratory Analysis of N6-Methyladenosine Regulator Expression and Predicted Traditional Chinese Medicine-Target Associations in Ulcerative Colitis
- `SRC-325` [published_study] Does Epstein-Barr virus contribute to the causation of inflammatory bowel disease?
- `SRC-326` [ongoing_trial] A Phase IIb, Multicenter, Double-blind, Placebo-controlled Induction Study With an Active Treatment Extension to Assess the Efficacy, Safety, and Pharmacokinetics of RO7837195 in Patients With Moderately to Severely Active Ulcerative Colitis
- `SRC-327` [ongoing_trial] Effects of a Fermented Food-Supplemented on Patients With Ulcerative Colitis
- `SRC-328` [ongoing_trial] Provide Pre-approval Single Patient Expanded Access (Compassionate Use) of Etrasimod for Patients.
- `SRC-329` [ongoing_trial] An Open-Label, Proof of Concept Study of Vorinostat for the Treatment of Moderate-to-Severe Crohn's Disease, Ulcerative Colitis, and Chronic Granulomatous Disease Colitis Patients and Maintenance Therapy With Ustekinumab
- `SRC-330` [ongoing_trial] A Phase IIa, Multicenter, Randomized, Double-blind, Placebo-controlled, Clinical Study to Evaluate the Safety, Tolerability, Pharmacokinetics and Clinical Efficacy of ISM5411 in Adult Patients With Active Ulcerative Colitis
- `SRC-331` [ongoing_trial] The Influence of a Fasting Mimicking Diet on Ulcerative Colitis
- `SRC-332` [ongoing_trial] An Open-Label, Single-Arm Study to Evaluate the Efficacy, Pharmacokinetics, and Safety of Etrasimod in Adolescent Participants With Moderately to Severely Active Ulcerative Colitis
- `SRC-333` [published_study] An anti-inflammatory diet is associated with enrichment of beneficial bacteria and increased microbial richness/evenness in adults with and without Inflammatory Bowel Disease: results from a cross-sectional Dietary Inflammatory Index study
- `SRC-334` [published_study] Liver Biochemical and Clinical Outcomes After IL-23 Pathway Therapy in IBD Patients With Mild Baseline Liver Test Abnormalities: A Propensity-Matched Cohort Study
- `SRC-335` [published_study] P300 as an epigenetic regulatory node linking berberine to attenuated H3K27ac/STAT3 inflammatory transcription in ulcerative colitis
- `SRC-336` [published_study] Quantitative image feature integrated digital pathology model based on deep learning and machine learning for binary histological severity stratification of ulcerative colitis
