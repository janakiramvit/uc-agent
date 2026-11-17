# UC evidence discovery - daily report 2026-11-17

Run `uc-exp-38cb47f21255` - https://github.com/janakiramvit/uc-agent/actions/runs/44109705597

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-15 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-15 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-15 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-15 .. 2026-11-17
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-15 .. 2026-11-17

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PubMed/MEDLINE | published_study | **OK** | 2026-11-15 .. 2026-11-17 | 6 | 22 | 22 | 9 | 20 | 1 | 0 | 1 | 1 | yes |
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-15 .. 2026-11-17 | 3 | 11 | 11 | 11 | 2 | 0 | 0 | 9 | 0 | yes |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-15 .. 2026-11-17 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-15 .. 2026-11-17 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-15 .. 2026-11-17 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-15 .. 2026-11-17 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-15 .. 2026-11-17 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| Europe PMC | published_study | **OK** | 2026-11-10 .. 2026-11-17 | 10 | 134 | 134 | 126 | 96 | 13 | 22 | 3 | 2 | yes |
| **All** | | | | 35 | | 167 | 146 | 118 | 14 | 22 | 13 | 3 | |

## Per-provider detail

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/15..2026/11/15]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 4538
- Duplicates: 13 cross-provider/in-provider, 7 already seen in earlier runs
- Rejected: not_relevant x1

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-15,2026-11-15]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-16,2026-11-16]`
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-17,2026-11-17]`
- Canary (wide window, same syntax): 544
- Duplicates: 0 cross-provider/in-provider, 2 already seen in earlier runs

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/15..2026/11/15]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-15 .. 2026-11-17
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-15..2026-11-17) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/15..2026/11/15]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-15 .. 2026-11-17

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/15..2026/11/15]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-15 .. 2026-11-17
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-15..2026-11-17)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-15 .. 2026-11-17

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-15 .. 2026-11-17
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-15..2026-11-17) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/15..2026/11/15]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/16..2026/11/16]`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/17..2026/11/17]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-15 .. 2026-11-17

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
- Duplicates: 8 cross-provider/in-provider, 88 already seen in earlier runs
- Rejected: not_relevant x12, out_of_scope x1
- Deferred: missing_required_metadata x21, no_usable_abstract x1

## Accepted this run (staging only)

- `SRC-169` [ongoing_trial] Randomized Controlled Trial of Online Pain Education Programs for Inflammatory Bowel Disease
- `SRC-170` [ongoing_trial] A MULTI-CENTER, PROSPECTIVE, NON-INTERVENTIONAL STUDY OF REAL-WORLD EFFECTIVENESS OF ETRASIMOD IN PATIENTS WITH ULCERATIVE COLITIS (ENDEAVOUR-UC)
- `SRC-171` [ongoing_trial] A Phase 3b Extension Study to Evaluate the Long-term Safety of Vedolizumab Subcutaneous in Pediatric Subjects With Ulcerative Colitis or Crohn's Disease
- `SRC-172` [ongoing_trial] Improving Outcomes and Reducing Disparities for Patients With Inflammatory Bowel Disease Through Epidemiology and Enhanced Disease Management (PROMOTE IBD)
- `SRC-173` [ongoing_trial] A Phase I Clinical Trial to Evaluate the Safety, Tolerability, Pharmacokinetics, and Pharmacodynamics of Subcutaneous Injection or Intravenous Infusion of SHR-7590 Injection in Healthy Chinese Participants and Participants With Moderate-to-Severe Inflammatory Bowel Disease (Ulcerative Colitis and Crohn's Disease)
- `SRC-174` [published_study] Integrating Mouse Transcriptomics and Human Multi-Cohort Data Reveals an Inflammatory Gene Signature Mediating Jaceosidin's Therapeutic Effect in Ulcerative Colitis
- `SRC-175` [published_study] Faecal calprotectin as a biomarker in patients with hidradenitis suppurativa: A narrative review
- `SRC-176` [ongoing_trial] A Phase I, Multicenter, Open-Label, Single-Agent Study to Assess the Pharmacokinetics of Cytochrome P450 Substrates After Treatment With Afimkibart in Participants With Moderately to Severely Active Ulcerative Colitis
- `SRC-177` [published_study] Venous thromboembolism in inflammatory bowel disease: a phase-specific framework for risk stratification and anticoagulant management
- `SRC-178` [ongoing_trial] Visceral Hypersensitivity, Urgency and Persistent Symptoms After Mucosal Healing in Ulcerative Colitis Patients: A Prospective Cohort Study in Switzerland
- `SRC-179` [ongoing_trial] Phase 2 Platform Trial to Assess the Efficacy and Safety of Long-acting Antibodies as Single Agents and in Combinations for Moderately to Severely Active Ulcerative Colitis
- `SRC-180` [completed_trial_record] Simple Nut Supplementation Induces Positive Gut Metabolic Signals in Patients With Inflammatory Bowel Disease
- `SRC-181` [published_study] [Mechanism of electroacupuncture on improving intestinal barrier injury in rats with ulcerative colitis by regulating RhoA/ROCK pathway]
