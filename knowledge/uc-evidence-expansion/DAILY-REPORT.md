# UC evidence discovery - daily report 2026-11-25

Run `uc-exp-0b1a2e55a3d1` - https://github.com/janakiramvit/uc-agent/actions/runs/45717646768

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-23 .. 2026-11-25
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-23 .. 2026-11-25
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-23 .. 2026-11-25
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-23 .. 2026-11-25
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-23 .. 2026-11-25

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PubMed/MEDLINE | published_study | **OK** | 2026-11-23 .. 2026-11-25 | 6 | 34 | 34 | 8 | 26 | 3 | 0 | 5 | 5 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-23 .. 2026-11-25 | 3 | 21 | 21 | 21 | 14 | 0 | 0 | 7 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-25 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-25 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-25 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-25 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-25 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-17 .. 2026-11-25 | 16 | 231 | 231 | 226 | 149 | 46 | 33 | 3 | 0 | yes |
| **All** | | | | 41 | | 286 | 255 | 189 | 49 | 33 | 15 | 5 | |

## Per-provider detail

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/25..2026/11/25]`
- Canary (wide window, same syntax): 4553
- Duplicates: 26 cross-provider/in-provider, 0 already seen in earlier runs
- Rejected: not_relevant x3

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-23,2026-11-23]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-24,2026-11-24]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-25,2026-11-25]`
- Canary (wide window, same syntax): 545
- Duplicates: 0 cross-provider/in-provider, 14 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/25..2026/11/25]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-23 .. 2026-11-25
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-23..2026-11-25) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/25..2026/11/25]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-23 .. 2026-11-25

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/25..2026/11/25]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-23 .. 2026-11-25
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-23..2026-11-25)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-23 .. 2026-11-25

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-25
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-23..2026-11-25) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/25..2026/11/25]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-23 .. 2026-11-25

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-17 .. 2026-11-25
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-17 TO 2026-11-17]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-18 TO 2026-11-18]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-19 TO 2026-11-19]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-21 TO 2026-11-21]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-22 TO 2026-11-22]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-23 TO 2026-11-23]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-24 TO 2026-11-24]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-25 TO 2026-11-25]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14777
- Duplicates: 5 cross-provider/in-provider, 144 already seen in earlier runs
- Rejected: not_relevant x45, out_of_scope x1
- Deferred: missing_required_metadata x32, no_usable_abstract x1

## Accepted this run (staging only)

- `SRC-276` [published_study] Tofacitinib-based advanced combination therapy in refractory inflammatory bowel disease: A real-world cohort study
- `SRC-277` [published_study] Two-Year Efficacy and Safety of Mirikizumab in Chinese Patients with Moderately to Severely Active Ulcerative Colitis: A Subpopulation Analysis of LUCENT-3 Open-Label Extension Study
- `SRC-278` [published_study] Pre-Treatment Immune Signatures and Cytokine Patterns Associated with Vedolizumab Response in Inflammatory Bowel Disease: A Pilot Study
- `SRC-279` [published_study] Identification of hub genes involved in the pathogenesis of ulcerative colitis: a multi-omics study integrating machine learning, Mendelian randomization, and mediation analysis
- `SRC-280` [published_study] Intestinal Diseases in Men and Women: Etiology, Diagnosis, and Therapeutic Approaches
- `SRC-281` [completed_trial_record] A Phase 2, Multi-center, Randomized, Double-blind, Placebo-controlled Parallel-group Study to Evaluate the Efficacy and Safety of Dupilumab Therapy in Patients With Moderately to Severely Active Ulcerative Colitis With an Eosinophilic Phenotype
- `SRC-282` [ongoing_trial] Microbiome-targeted Diet Therapy in Ulcerative Colitis
- `SRC-283` [ongoing_trial] Assessment of Gut Microbiota Dysbiosis in Inflammatory Bowel Disease by Real-Time Polymerase Chain Reaction: Correlation With Disease Severity
- `SRC-284` [ongoing_trial] Characterization of Alternative Holobiont States in Ulcerative Colitis to Pave the Way for Innovative Treatment Strategies (CHARTS)
- `SRC-285` [ongoing_trial] Impact of a Human Origin Heat Inactivated Probiotics-Lactobacillus Paracasei D3.5 (LpD3.5) as Dietary Supplement on Gut Mucin and Intestinal Permeability in Adults With IBD
- `SRC-286` [ongoing_trial] Implementation of a Family-Based Mediterranean-Style Dietary Intervention in First-Degree Relatives of Children With IBD: A Prospective Multicenter Interventional Cohort Study
- `SRC-287` [ongoing_trial] Carrot Juice as Treatment for Chronic Pouchitis
- `SRC-288` [published_study] SLC15A3 regulates ulcerative colitis progression by orchestrating intestinal macrophage infiltration and activation
- `SRC-289` [published_study] Fucoidan-functionalized Prussian blue nanozymes loaded with baicalin for ulcerative colitis therapy via intracellular-extracellular ROS regulation
- `SRC-290` [published_study] Missed Diagnosis of Mantle Cell Lymphoma in a Patient Initially Diagnosed With Ulcerative Colitis: A Case Report
