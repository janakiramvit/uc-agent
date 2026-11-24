# UC evidence discovery - daily report 2026-11-24

Run `uc-exp-4e38f9464db9` - https://github.com/janakiramvit/uc-agent/actions/runs/45509696601

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-23 .. 2026-11-24
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-23 .. 2026-11-24
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-23 .. 2026-11-24
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-23 .. 2026-11-24
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-23 .. 2026-11-24

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Europe PMC | published_study | **OK** | 2026-11-17 .. 2026-11-24 | 14 | 184 | 184 | 178 | 137 | 19 | 26 | 2 | 2 | no |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-23 .. 2026-11-24 | 4 | 20 | 20 | 11 | 9 | 5 | 0 | 6 | 3 | no |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-23 .. 2026-11-24 | 2 | 13 | 13 | 13 | 6 | 0 | 0 | 7 | 0 | no |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-24 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-24 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-24 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-24 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-23 .. 2026-11-24 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| **All** | | | | 32 | | 217 | 202 | 152 | 24 | 26 | 15 | 5 | |

## Per-provider detail

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-17 .. 2026-11-24
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-17 TO 2026-11-17]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-18 TO 2026-11-18]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-19 TO 2026-11-19]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-20 TO 2026-11-20]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-21 TO 2026-11-21]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-22 TO 2026-11-22]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-23 TO 2026-11-23]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-24 TO 2026-11-24]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14750
- Duplicates: 6 cross-provider/in-provider, 131 already seen in earlier runs
- Rejected: not_relevant x19
- Deferred: missing_required_metadata x25, no_usable_abstract x1

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/24..2026/11/24]`
- Canary (wide window, same syntax): 4539
- Duplicates: 9 cross-provider/in-provider, 0 already seen in earlier runs
- Rejected: not_relevant x4, out_of_scope x1

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-23,2026-11-23]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-24,2026-11-24]`
- Canary (wide window, same syntax): 540
- Duplicates: 0 cross-provider/in-provider, 6 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/24..2026/11/24]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-23 .. 2026-11-24
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-23..2026-11-24) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/24..2026/11/24]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-23 .. 2026-11-24

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/24..2026/11/24]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-23 .. 2026-11-24
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-23..2026-11-24)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-23 .. 2026-11-24

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-23 .. 2026-11-24
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-23..2026-11-24) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/23..2026/11/23]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/24..2026/11/24]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-23 .. 2026-11-24

## Accepted this run (staging only)

- `SRC-260` [published_study] Targeting convergent pathogenic pathways: precision nutrition and lifestyle strategies in ulcerative colitis
- `SRC-261` [published_study] Nitidine chloride alleviates DSS-induced ulcerative colitis in mice by modulating inflammation-intestinal barrier crosstalk and gut microbiota-metabolite interactions
- `SRC-262` [published_study] Prevalence, etiology, and trajectory of anemia in pediatric inflammatory bowel disease: a systematic review and meta-analysis
- `SRC-263` [published_study] Upadacitinib durability and clinical relapse following step-down from induction to maintenance dosing in pediatric inflammatory bowel disease
- `SRC-264` [ongoing_trial] A Randomized, Multicenter, Double-Blind, Placebo-Controlled Development Program to Evaluate the Efficacy and Safety of LY4268989 (MORF-057) for the Treatment of Adults With Moderately to Severely Active Ulcerative Colitis (EMERALD-3)
- `SRC-265` [completed_trial_record] Implementing a Multimodal RCT Intervention to Improve the Transition of Patients With Crohn's Disease From Pediatric to Adult Care
- `SRC-266` [published_study] IMPRECTO: prevalence, impact, and under-recognition of urgency and fecal incontinence in pediatric ulcerative colitis: a GETAID pédiatrique study
- `SRC-267` [completed_trial_record] A Phase 2 Long-Term Extension (LTE) Study to Evaluate The Safety and Efficacy of Efavaleukin Alfa in Subjects With Moderately to Severely Active Ulcerative Colitis
- `SRC-268` [ongoing_trial] A Study to Evaluate the Long-term Safety and Efficacy of Long-acting Antibodies as Single Agents and in Combinations in Participants With Inflammatory Bowel Disease
- `SRC-269` [published_study] Delta Neutrophil Index as a Novel Marker of Disease Activity in Pediatric Inflammatory Bowel Disease
- `SRC-270` [ongoing_trial] A Phase 1b Study Evaluating ABBV-319 in Subjects With Advanced Therapy Experienced, Moderately to Severely Active Ulcerative Colitis
- `SRC-271` [ongoing_trial] A Master Protocol for Phase 2, Randomized, Controlled Studies of Multiple Interventions for the Treatment of Adults With Moderately to Severely Active Ulcerative Colitis or Crohn's Disease
- `SRC-272` [ongoing_trial] Randomized Trial of Non-Invasive Vagal Nerve Stimulation in UC-IBS and Mild Ulcerative Colitis: NIH Aim 3
- `SRC-273` [published_study] A santonin derivative, QX-6, alleviates ulcerative colitis by suppressing macrophage oxidative stress and inflammatory responses via modulation of ferroptosis-related signaling
- `SRC-274` [published_study] Fluconazole-Resistant Candida albicans Isolates Blunt Infliximab Responsiveness in Ulcerative Colitis
