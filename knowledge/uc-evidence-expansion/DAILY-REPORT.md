# UC evidence discovery - daily report 2026-11-10

Run `uc-exp-18f1e85b8e6a` - https://github.com/janakiramvit/uc-agent/actions/runs/42898030632

> Discovery and staging only. Nothing here is approved, published or promoted; every new record is `pending_clinical_review` and every claim needs full-text verification.

## Alerts

- **ERROR** `REPEATED_UNEXPECTED_ZERO` (europepmc): 3 consecutive runs returned zero for a provider that normally returns results daily
- **WARNING** `ACCESS_LIMITED` (aga): gastro.org: robots.txt disallows automated access to /guidelines/; covered via other channel only
- **WARNING** `ACCESS_LIMITED` (ecco): www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients); covered via other channel only
- **INFO** `NO_NEW_RECORDS` (acg): provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-10
- **INFO** `NO_NEW_RECORDS` (aga): provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-10
- **INFO** `NO_NEW_RECORDS` (bsg): provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-10
- **INFO** `NO_NEW_RECORDS` (ecco): provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-10
- **INFO** `NO_NEW_RECORDS` (nice): provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-10

## Provider health

| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | Accepted | Claims | Cutoff advanced |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ClinicalTrials.gov | ongoing_trial | **OK** | 2026-11-10 .. 2026-11-10 | 1 | 4 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | no |
| AGA guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ACG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| ECCO guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| NICE guidance | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| BSG guidelines | clinical_guideline | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| Europe PMC | published_study | **NO NEW RECORDS** | 2026-11-10 .. 2026-11-10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | no |
| PubMed/MEDLINE | published_study | **OK** | 2026-11-10 .. 2026-11-10 | 2 | 14 | 14 | 14 | 0 | 4 | 1 | 9 | 13 | no |
| **All** | | | | 12 | | 18 | 18 | 0 | 4 | 1 | 13 | 13 | |

## Per-provider detail

### ClinicalTrials.gov

- Status: **OK**; evidence type: `ongoing_trial`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[2026-11-10,2026-11-10]`
- Canary (wide window, same syntax): 540

### AGA guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND (AGA[tiab] OR "American Gastroenterological Association"[tiab]))  [edat 2026/11/10..2026/11/10]`
- Canary (wide window, same syntax): 11
- Zero-result reason: provider healthy (wide-window canary returned 11); no new matching records in 2026-11-10 .. 2026-11-10
- Access limitation: gastro.org: robots.txt disallows automated access to /guidelines/

### ACG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `site:gi.org (robots-permitting listing; window 2026-11-10..2026-11-10) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Am J Gastroenterol"[ta])  [edat 2026/11/10..2026/11/10]`
- Canary (wide window, same syntax): 7
- Zero-result reason: provider healthy (wide-window canary returned 7); no new matching records in 2026-11-10 .. 2026-11-10

### ECCO guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "J Crohns Colitis"[ta])  [edat 2026/11/10..2026/11/10]`
- Canary (wide window, same syntax): 8
- Zero-result reason: provider healthy (wide-window canary returned 8); no new matching records in 2026-11-10 .. 2026-11-10
- Access limitation: www.ecco-ibd.eu: robots.txt returned HTTP 403 (site refuses automated clients)

### NICE guidance

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `site:www.nice.org.uk (robots-permitting listing; window 2026-11-10..2026-11-10)`
- Canary (wide window, same syntax): 2
- Zero-result reason: provider healthy (wide-window canary returned 2); no new matching records in 2026-11-10 .. 2026-11-10

### BSG guidelines

- Status: **NO NEW RECORDS**; evidence type: `clinical_guideline`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `site:www.bsg.org.uk (robots-permitting listing; window 2026-11-10..2026-11-10) | ("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))`
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms]) AND ((guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR "clinical practice update"[ti] OR recommendations[ti]) AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab]))  [edat 2026/11/10..2026/11/10]`
- Canary (wide window, same syntax): 6
- Zero-result reason: provider healthy (wide-window canary returned 6); no new matching records in 2026-11-10 .. 2026-11-10

### Europe PMC

- Status: **NO NEW RECORDS**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[2026-11-10 TO 2026-11-10]) NOT SRC:PPR`
- Canary (wide window, same syntax): 14562
- Zero-result reason: provider healthy (wide-window canary returned 14562); no new matching records in 2026-11-10 .. 2026-11-10

### PubMed/MEDLINE

- Status: **OK**; evidence type: `published_study`
- Window: 2026-11-10 .. 2026-11-10
- Query (this provider's own syntax): `("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])  [edat 2026/11/10..2026/11/10]`
- Canary (wide window, same syntax): 4550
- Rejected: not_relevant x3, out_of_scope x1
- Deferred: no_usable_abstract x1

## Accepted this run (staging only)

- `SRC-105` [ongoing_trial] Longitudinal Immunophenotyping of Patients With Inflammatory Bowel Disease
- `SRC-106` [published_study] Comparative effectiveness of infliximab and tofacitinib in advanced therapy-naive and -exposed patients with ulcerative colitis: a multicenter real-world study
- `SRC-107` [ongoing_trial] Evaluation of a Remote Monitoring Application in the Follow-up of Patients With Active Inflammatory Bowel Diseases: The SECURITY Trial
- `SRC-108` [ongoing_trial] A Phase 3 Extension Study to Evaluate the Long-term Safety and Efficacy of Tulisokibart in Participants With Crohn's Disease or Ulcerative Colitis
- `SRC-109` [published_study] Cellular therapies and immune reprogramming in inflammatory bowel disease: lessons learned and the promise of CAR T-cell therapy
- `SRC-110` [ongoing_trial] Safety and Efficacy of a STOPping Strategy Versus Classical Maintenance Dose of JAK Inhibitors in Deep Remission Patients With Ulcerative Colitis: a Randomized Controlled Trial
- `SRC-111` [published_study] Impact of in vitro fertilization on disease activity and pregnancy outcomes in women with inflammatory bowel disease
- `SRC-112` [published_study] Laparoscopic first-stage subtotal colectomy for ulcerative and indeterminate colitis: a propensity-matched study
- `SRC-113` [published_study] An ulcerative colitis taxonomy defined by individual patient-reported response trajectories
- `SRC-114` [published_study] Intestinal obstruction due to rectal neoplasia in a patient with ulcerative colitis undergoing surgery with total mesorectal excision: case report and literature review
- `SRC-115` [published_study] Enteric Neurons and Glial Cells Are Partially Protected in P2X7 Receptor-Deficient Mice With Ulcerative Colitis
- `SRC-116` [published_study] Diagnostic prediction of ulcerative colitis using simplified endoscopic features and blood count-derived indices: a multicenter study
- `SRC-117` [published_study] Metabolic glycoengineered exosomes enable in situ PD-L1-Fc assembly for targeted immunotherapy in ulcerative colitis
