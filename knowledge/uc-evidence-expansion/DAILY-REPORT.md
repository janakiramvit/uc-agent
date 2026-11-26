# UC evidence discovery - daily report 2026-11-26

Run `uc-exp-a44b68b5d7a7` - https://github.com/janakiramvit/uc-agent/actions/runs/45907450574

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **WARNING** `WINDOW_NOT_COMPLETE` (europepmc): window not fully retrieved/screened; the cutoff advanced only over complete days and the rest continues next run
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-24 .. 2026-11-26
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-24 .. 2026-11-26
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-24 .. 2026-11-26
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-24 .. 2026-11-26
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-24 .. 2026-11-26

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-24 .. 2026-11-26 | 3 | 16 | 16 | 16 | 16 | 0 | 0 | 0 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-24 .. 2026-11-26 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-24 .. 2026-11-26 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-24 .. 2026-11-26 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-24 .. 2026-11-26 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-24 .. 2026-11-26 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **PARTIAL** | 2026-11-18 .. 2026-11-26 | 23 | 368 | 368 | 329 | 189 | 120 | 41 | 10 | 5 | no |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-24 .. 2026-11-26 | 8 | 70 | 70 | 29 | 41 | 9 | 1 | 19 | 22 | yes |
| **All** | | | | 50 | | 454 | 374 | 246 | 129 | 42 | 29 | 27 | |

## Per-provider detail

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-24,2026-11-24]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-25,2026-11-25]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-26,2026-11-26]`
- Canary (wide window, same syntax): 545
- Duplicates: 0 cross-provider/in-provider, 16 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/26..2026/11/26]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-24 .. 2026-11-26
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-24..2026-11-26) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/26..2026/11/26]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-24 .. 2026-11-26

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/26..2026/11/26]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-24 .. 2026-11-26
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-24..2026-11-26)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-24 .. 2026-11-26

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-24..2026-11-26) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/26..2026/11/26]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-24 .. 2026-11-26

### Europe PMC

- Status: **PARTIAL**; evidence type: `published_study`
- Window: 2026-11-18 .. 2026-11-26
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-18 TO 2026-11-18]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-19 TO 2026-11-19]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-21 TO 2026-11-21]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-22 TO 2026-11-22]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-23 TO 2026-11-23]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-24 TO 2026-11-24]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-25 TO 2026-11-25]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-26 TO 2026-11-26]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14866
- Duplicates: 31 cross-provider/in-provider, 158 already seen in earlier runs
- Rejected: not_relevant x120
- Deferred: missing_required_metadata x40, no_usable_abstract x1

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-24 .. 2026-11-26
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/24..2026/11/24]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/25..2026/11/25]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/26..2026/11/26]`
- Canary (wide window, same syntax): 4589
- Duplicates: 41 cross-provider/in-provider, 0 already seen in earlier runs
- Rejected: not_relevant x9
- Deferred: no_usable_abstract x1

## Accepted this run (staging only)

- `SRC-292` [published_study] Atractylodes macrocephala in Ulcerative Colitis: Bioactive Constituents, Microbiota, and Translational Gaps
- `SRC-293` [published_study] Pectin as a Multifunctional Therapeutic Platform for Ulcerative Colitis: Integrating Colonic Targeting, Microbiota Remodeling, and Antioxidant Synergy
- `SRC-294` [published_study] Environmentally Friendly LC-MS/MS Method for the Determination of Etrasimod in Human Plasma via Advanced Phospholipid Matrix Removal
- `SRC-295` [published_study] Increased Relative Abundance of Lactobacilli Species in the Gut Microbiota of Patients with Crohn's Disease and Ulcerative Colitis
- `SRC-296` [published_study] Prevalence of Fatigue in Swedish Patients with Inflammatory Bowel Disease, and Factors Contributing to Fatigue-A Mixed-Methods Study
- `SRC-297` [published_study] HLA-DQA1*05 and HLA-DQA1*05/HLA-DQB1*02 Co-Carriage in Relation to Anti-TNF Antibody Concentrations and Response in Iraqi Patients with Inflammatory Bowel Disease
- `SRC-298` [published_study] Biochemical and Serological Changes, Including Thyroid Function and Helicobacter pylori, in Inflammatory Bowel Disease Patients Treated with Upadacitinib: A Retrospective Observational Study
- `SRC-299` [published_study] Microbiota-Driven Gut-Liver Axis Dysregulation in Primary Sclerosing Cholangitis-Ulcerative Colitis Comorbidity: A Narrative Review
- `SRC-300` [published_study] Natural Fungal Fermentation Broth of Scleroderma bovista Ameliorates Ulcerative Colitis by Suppressing the NF-κB Pathway and Gut Microbial Dysbiosis
- `SRC-301` [published_study] Leucine-Rich Alpha-2 Glycoprotein as a Useful Biomarker for Monitoring Endoscopic and Histological Activity in Ulcerative Colitis
- `SRC-302` [published_study] Advanced Combination Therapy in IBD
- `SRC-303` [published_study] Pithecellobium clypearia ameliorates ulcerative colitis through regulation of purine metabolism and gut microbiota
- `SRC-304` [published_study] Identification and characterization of ion channel-related signatures in ulcerative colitis: an integrated multi-omics and machine learning analysis
- `SRC-305` [published_study] Safety profile and potential favorable reporting signals of liraglutide in patients with ulcerative colitis: A FAERS pharmacovigilance and network pharmacology study
- `SRC-306` [published_study] Updates in dysplasia surveillance in inflammatory bowel disease
- `SRC-307` [published_study] From p40 to p19 Inhibition in Pediatric Inflammatory Bowel Disease: Translating Adult Comparative Evidence into Pediatric Practice
- `SRC-308` [published_study] Saikosaponin D Suppresses NLRP3 Inflammasome Activation to Alleviate Ulcerative Colitis
- `SRC-309` [published_study] Maintenance of Efficacy Outcomes at Week 52 Among Etrasimod Induction Responders: An Analysis From the Phase 3 ELEVATE UC 52 Trial
- `SRC-310` [published_study] Upadacitinib for Acute Severe Ulcerative Colitis: Real-World Tertiary Care Outcomes
- `SRC-311` [published_study] Prebiotic Blends and Remission in Inflammatory Bowel Disease: A Brazilian Year-Long Nonrandomized Pilot Trial
- `SRC-312` [published_study] LGALS1-Associated Candidate Myeloid Signature and In Silico Regulatory Analysis in Ulcerative Colitis: A Bioinformatics Study
- `SRC-313` [published_study] Integrated Single-Cell and Bulk Transcriptomics Reveal Myeloid-Cell Heterogeneity in Ulcerative Colitis
- `SRC-314` [published_study] Clinical characteristics, genetics, and long-term outcomes in children with very early-onset inflammatory bowel disease: a Turkish cohort
- `SRC-315` [published_study] High-Fat Diet Aggravates Dampness-Heat Ulcerative Colitis via Palmitic Acid-Mediated Trained Immunity and the Regulatory Effect of Shaoyao Decoction
- `SRC-316` [published_study] Integrated profiling of the extracellular redox metabolome is characterized by compensated oxidative stress in ulcerative colitis
- `SRC-317` [published_study] Palmatine alleviates ulcerative colitis by targeting genes associated with the neutrophil phase
- `SRC-318` [published_study] Interleukin Networks in Ulcerative Colitis: Pathogenic Mechanisms, Context-Dependent Functions, and Therapeutic Opportunities
- `SRC-319` [published_study] Mucosal Gene Expression Signatures Associated with Response to Tofacitinib and Upadacitinib in Ulcerative Colitis
- `SRC-320` [published_study] Microbial butyrate and tryptophan enzyme profiles and host immunometabolic programmes in ulcerative colitis: A secondary multi-omics analysis of public metagenomic and mucosal transcriptomic data
