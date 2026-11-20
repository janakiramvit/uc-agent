# UC evidence discovery - daily report 2026-11-20

Run `uc-exp-7b925ac2b136` - https://github.com/janakiramvit/uc-agent/actions/runs/44822710334

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-18 .. 2026-11-20
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-18 .. 2026-11-20
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-18 .. 2026-11-20
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-18 .. 2026-11-20
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-18 .. 2026-11-20

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-18 .. 2026-11-20 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-18 .. 2026-11-20 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-18 .. 2026-11-20 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-18 .. 2026-11-20 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-12 .. 2026-11-20 | 17 | 234 | 234 | 229 | 109 | 81 | 38 | 6 | 9 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-18 .. 2026-11-20 | 6 | 41 | 41 | 18 | 28 | 6 | 2 | 5 | 9 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-18 .. 2026-11-20 | 3 | 17 | 17 | 17 | 12 | 0 | 0 | 5 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-18 .. 2026-11-20 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 42 | | 292 | 264 | 149 | 87 | 40 | 16 | 18 | |

## Per-provider detail

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-18..2026-11-20) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/18..2026/11/18]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/19..2026/11/19]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/20..2026/11/20]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-18 .. 2026-11-20

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/18..2026/11/18]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/19..2026/11/19]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/20..2026/11/20]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-18 .. 2026-11-20
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-18..2026-11-20)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-18 .. 2026-11-20

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-18..2026-11-20) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/18..2026/11/18]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/19..2026/11/19]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/20..2026/11/20]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-18 .. 2026-11-20

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-12 .. 2026-11-20
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-12 TO 2026-11-12]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-13 TO 2026-11-13]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-14 TO 2026-11-14]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-15 TO 2026-11-15]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-16 TO 2026-11-16]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-17 TO 2026-11-17]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-18 TO 2026-11-18]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-19 TO 2026-11-19]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14828
- Duplicates: 5 cross-provider/in-provider, 104 already seen in earlier runs
- Rejected: not_relevant x79, out_of_scope x2
- Deferred: missing_required_metadata x35, no_usable_abstract x3

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/18..2026/11/18]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/19..2026/11/19]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/20..2026/11/20]`
- Canary (wide window, same syntax): 4559
- Duplicates: 23 cross-provider/in-provider, 5 already seen in earlier runs
- Rejected: not_relevant x5, out_of_scope x1
- Deferred: no_usable_abstract x2

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-18,2026-11-18]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-19,2026-11-19]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-20,2026-11-20]`
- Canary (wide window, same syntax): 547
- Duplicates: 0 cross-provider/in-provider, 12 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-18 .. 2026-11-20
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/18..2026/11/18]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/19..2026/11/19]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/20..2026/11/20]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-18 .. 2026-11-20
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

## Accepted this run (staging only)

- `SRC-218` [published_study] EXPRESS: Dry Eye Disease in Inflammatory Bowel Disease: A Cross-Sectional Analysis of Associated Clinical and Systemic Factors
- `SRC-219` [published_study] Whole-blood transcriptomics reveal molecular compatibility and complementarity across advanced therapies in ulcerative colitis
- `SRC-220` [completed_trial_record] A Multinational, Multicenter Extension Study to Investigate the Long-term Safety, Tolerability and Efficacy of Balinatunfib in Adults With Crohn's Disease or Ulcerative Colitis
- `SRC-221` [published_study] Time-to-response in acute severe ulcerative colitis: when to continue, optimize, or stop treatment
- `SRC-222` [completed_trial_record] A Phase 2, Multinational, Multicenter, Randomized, Double-blind, Placebo-controlled, Dose-ranging Study to Evaluate the Efficacy and Safety of SAR441566 in Adults With Moderate-to-severe Ulcerative Colitis
- `SRC-223` [completed_trial_record] Analysis of Barriers and Facilitators to Adapted Physical Activity for Pediatric Patients With Chronic Inflammatory Bowel Diseases
- `SRC-224` [ongoing_trial] A Multicenter, Multinational, Randomized, Double-blind, Placebo-controlled Phase 3, Induction Study to Evaluate the Efficacy and Safety of Duvakitug in Participants With Moderately to Severely Active Ulcerative Colitis.
- `SRC-225` [published_study] Multi-source analysis identifies an NPC2-associated macrophage transcriptional program in ulcerative colitis
- `SRC-226` [ongoing_trial] A Multi-centre, Double-blind Randomised Controlled Trial to Compare Modafinil Versus Placebo Over 12 Weeks in Patients With Severe Fatigue and Inflammatory Bowel Disease (MFI): a Feasibility Study
- `SRC-227` [published_study] A propensity score weighted comparison of intravenous and subcutaneous infliximab as maintenance treatment in patients with inflammatory bowel disease: The CISI study
- `SRC-228` [published_study] Long-Term Real-World Switch Rates and Adherence Among Patients With Ulcerative Colitis Treated With Upadacitinib or Tumour Necrosis Factor Inhibitors
- `SRC-229` [published_study] A glucomannan from Dendrobium huoshanense ameliorating ulcerative colitis by regulating gut microbiota
- `SRC-230` [published_study] Cellular determinants of treatment-responsiveness in ulcerative colitis
- `SRC-231` [published_study] Upadacitinib-associated modulation of NLRP3 inflammasome signaling: mechanistic evidence and translational implications
- `SRC-232` [published_study] Hierarchical benefit of multidimensional remission in ulcerative colitis: a systematic review and meta-analysis
- `SRC-233` [published_study] Etrasimod
