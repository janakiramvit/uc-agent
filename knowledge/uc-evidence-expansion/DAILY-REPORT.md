# UC evidence discovery - daily report 2026-11-12

Run `uc-exp-d2aed195360a` - https://github.com/janakiramvit/uc-agent/actions/runs/43309315361

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-12
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-12
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-12
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-12
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-12

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-12 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-12 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-12 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-12 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-10 .. 2026-11-12 | 7 | 83 | 83 | 80 | 18 | 47 | 18 | 0 | 0 | yes |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-10 .. 2026-11-12 | 6 | 30 | 30 | 4 | 27 | 0 | 0 | 3 | 5 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-10 .. 2026-11-12 | 3 | 14 | 14 | 14 | 4 | 0 | 0 | 10 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-12 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| **All** | | | | 32 | | 127 | 98 | 49 | 47 | 18 | 13 | 5 | |

## Per-provider detail

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-10..2026-11-12) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/12..2026/11/12]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-12

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/12..2026/11/12]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-12
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-10..2026-11-12)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-12

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-10..2026-11-12) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/12..2026/11/12]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-12

### Europe PMC

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-10 TO 2026-11-10]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-11 TO 2026-11-11]) NOT SRC:PPR`
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-12 TO 2026-11-12]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14678
- Duplicates: 3 cross-provider/in-provider, 15 already seen in earlier runs
- Rejected: not_relevant x45, out_of_scope x2
- Deferred: missing_required_metadata x16, no_usable_abstract x2

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/12..2026/11/12]`
- Canary (wide window, same syntax): 4566
- Duplicates: 26 cross-provider/in-provider, 1 already seen in earlier runs

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-10,2026-11-10]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-11,2026-11-11]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-12,2026-11-12]`
- Canary (wide window, same syntax): 542
- Duplicates: 0 cross-provider/in-provider, 4 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-12
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/10..2026/11/10]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/11..2026/11/11]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/12..2026/11/12]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-12
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

## Accepted this run (staging only)

- `SRC-127` [published_study] The hidden burden of sarcopenia in inflammatory bowel disease: a strong predictor of complications
- `SRC-128` [published_study] Design and Synthesis of Novel, Non-ATP-Competitive MKK3 Modulators as Suppressors of TNF-α Production for the Treatment of Ulcerative Colitis
- `SRC-129` [published_study] Comment on: "Performance of existing predictive scores of response in patients with moderately active ulcerative colitis treated with oral corticosteroids"
- `SRC-130` [ongoing_trial] A Multicenter, Randomized, Double-Blind, Placebo-Controlled Phase I Study to Evaluate the Safety, Tolerability, Pharmacokinetics, and Pharmacodynamics of Single and Multiple Ascending Doses of VDJ010 for Subcutaneous Injection in Healthy Chinese Subjects and Patients With Ulcerative Colitis
- `SRC-131` [ongoing_trial] A Phase Ib Study of Nivolumab in Patients With Autoimmune Disorders and Advanced Malignancies (AIM-NIVO)
- `SRC-132` [ongoing_trial] A Phase 2a Randomized, Double-Blind, Placebo-Controlled Study to Evaluate the Efficacy and Safety of MK-8690 in Adult Participants With Moderately to Severely Active Ulcerative Colitis
- `SRC-133` [ongoing_trial] EFFECTIVENESS OF ETRASIMOD ON DISEASE ACTIVITY AND PATIENT-REPORTED OUTCOMES IN ULCERATIVE COLITIS - EFFECT-UC
- `SRC-134` [ongoing_trial] A Phase 2, Multicenter, Randomized, Double-Blind, Placebo-Controlled, Dose-Ranging Study to Evaluate the Efficacy and Safety of IPG11406 Tablets in Adult Patients With Moderately to Severely Active Ulcerative Colitis
- `SRC-135` [ongoing_trial] Multicentric Evaluation of a Strategy for Early Infliximab Optimization Among Adult Inflammatory Bowel Disease Patients
- `SRC-136` [ongoing_trial] Testing of an Educational Tool for Patients With Melanoma and Concomitant Autoimmune Disease Who Are Candidates for Adjuvant Therapy With Immune Checkpoint Inhibitors: Acceptability and Usability With Patients and Providers
- `SRC-137` [ongoing_trial] Phase IIa, Sequential Cohort, Open-label, Multi-center Clinical Trial to Evaluate the Efficacy, Safety, and Tolerability of Intravenous Induction and Subcutaneous Maintenance Treatment With BI 3032950 in Patients With Moderate to Severe Ulcerative Colitis
- `SRC-138` [ongoing_trial] A Phase 2, Multicenter, Randomized, Double-Blind, Placebo-Controlled, Dose Ranging Study to Evaluate the Efficacy, Safety, Pharmacokinetics, and Pharmacodynamics of Induction and Maintenance Therapy With PALI-2108 in Participants With Moderately to Severely Active Ulcerative Colitis
- `SRC-139` [ongoing_trial] A Phase 2b, Randomized, Double-Blind Long-Term Extension Study to Evaluate Pharmacokinetics, Efficacy, Safety, and Tolerability of TEV-48574 in Adult Patients With Moderate to Severe Ulcerative Colitis or Crohn's Disease Who Completed the Treatment Phase of the Dose-Ranging Study (RELIEVE UCCD LTE)
