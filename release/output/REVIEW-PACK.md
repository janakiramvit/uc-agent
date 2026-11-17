# Pilot evidence release - owner review pack (2026-11-17)

Evidence frozen at staging commit `9c7cd28` (all 8 providers' cutoffs 2026-11-17). Nothing here is approved or promoted. Your decisions are recorded as `owner_reviewed_for_pilot` - never as clinician approval.

## Summary

- Sources: **119 -> 99** after exact de-duplication (20 merged: all baseline-register copies of production sources).
- Claims: **171 -> 125** after de-duplication (46 exact duplicates removed) **+ 2 curator-authored claims** (IDs CLM-701, CLM-702, verbatim from public abstracts).
- By origin (before dedup): production 49 claims / 20 sources; baseline register 61 / 26; staging (Phase 2 + daily discovery) 61 / 73.
- **Proposed inclusions: 10** (decide below). Deferred claims: 117. Source types: animal preclinical 17, case report 3, published or guideline 53, trial record 26.

### Deferred (not for patients) by reason

_(117 deferred claim records in total: 53 staged (Phase 2 + daily discovery), 49 production claims that are already not served, 15 baseline-register-only.)_

- ibd general unclear: 62
- incomplete or unverifiable: 22
- crohns only: 17
- case report: 7
- animal preclinical: 5
- conflicting: 3
- ibd general with uc subgroup: 1

### Conflicts and unresolved issues

- Claim ID `CLM-081` exists in both production and the baseline register with different content (production:CLM-081, baseline-register:CLM-081); kept apart, baseline copy deferred as conflicting.
- Claim ID `CLM-083` exists in both production and the baseline register with different content (production:CLM-083, baseline-register:CLM-083); kept apart, baseline copy deferred as conflicting.
- Claim ID `CLM-085` exists in both production and the baseline register with different content (production:CLM-085, baseline-register:CLM-085); kept apart, baseline copy deferred as conflicting.
- Source IDs: no source ID maps to two different sources; no claim ID is reused for a different claim among staged claims.
- Several staged claims share a source with one proposed claim; only the verbatim-verified, non-overstating ones are proposed.
- 26 trial registry records (24 ongoing, 2 completed) are kept as labelled trial sources only: **no efficacy claim can come from them**.

### Question coverage if you approve everything proposed

- Before: covered 1, partial 2, not covered 36 (of 39).
- After: covered 8, partial 5, not covered 26 (of 39).

## A. Proposed inclusions - please mark `approve` or `defer`

Excerpts were re-verified verbatim against the public PubMed abstract on 2026-11-17 (full text never accessed; every claim needs full-text verification before any stronger use).

### 1. CLM-115 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** If you have ulcerative colitis and feel well (symptomatic remission), the AGA guideline suggests checking a biomarker test together with your symptoms, rather than relying on symptoms alone.
- **Exact excerpt:** "In patients with UC in symptomatic remission, the panel suggests the use of a biomarker- and symptom-based monitoring strategy over a symptom-based monitoring strategy."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** conditional guideline recommendation (GRADE; AGA)
- **Limitations:** Conditional recommendation; the guideline does not specify monitoring frequency in the retrieved abstract. Applies to established UC, not diagnosis.
- **Patient questions:** L2-1.2, L3-1.2.1
- **Why:** UC-specific AGA practice guideline recommendation; excerpt is verbatim and the claim restates it without adding.
- **Your decision:** `[ ] approve   [ ] defer`

### 2. CLM-116 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** If you have ulcerative colitis in symptomatic remission, the AGA guideline suggests that a fecal calprotectin below 150 µg/g, a normal fecal lactoferrin and/or a normal CRP can be used to rule out active inflammation, so routine endoscopy can be avoided.
- **Exact excerpt:** "For patients in symptomatic remission, the panel suggests using fecal calprotectin <150 μg/g, normal fecal lactoferrin, and/or normal CRP to rule out active inflammation and avoid routine endoscopic assessment of disease."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** conditional guideline recommendation (GRADE; AGA)
- **Limitations:** Conditional recommendation. 150 μg/g is a guideline decision threshold, not a diagnostic cut-off for an individual; calprotectin assays are not interchangeable and vary within-day / within-stool.
- **Patient questions:** L3-1.2.1, L3-1.2.3
- **Why:** UC-specific AGA guideline recommendation; thresholds are decision thresholds, not individual diagnoses (stated in limitations).
- **Your decision:** `[ ] approve   [ ] defer`

### 3. CLM-117 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** If you have ulcerative colitis with moderate-to-severe symptoms, the AGA guideline suggests that a fecal calprotectin above 150 µg/g, an elevated fecal lactoferrin or an elevated CRP can help guide treatment decisions without routine endoscopy.
- **Exact excerpt:** "In patients with UC with moderate to severe symptoms, the panel suggests using fecal calprotectin >150 μg/g, elevated fecal lactoferrin, or elevated CRP to inform treatment decisions and avoid routine endoscopic assessment of disease."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** conditional guideline recommendation (GRADE; AGA)
- **Limitations:** Conditional recommendation. Concordant elevated biomarker + moderate/severe symptoms; interpretation and any treatment change are clinician-led.
- **Patient questions:** L3-1.2.1, L2-1.1
- **Why:** UC-specific AGA guideline recommendation; verbatim excerpt.
- **Your decision:** `[ ] approve   [ ] defer`

### 4. CLM-118 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** When symptoms and biomarker tests disagree (feeling well but raised markers, or moderate-to-severe symptoms with normal markers), the AGA guideline suggests an endoscopic assessment to guide treatment.
- **Exact excerpt:** "However, in patients in symptomatic remission but elevated biomarkers, and in patients with moderate to severe symptoms with normal biomarkers, the panel suggests endoscopic assessment of disease to inform treatment decisions."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** conditional guideline recommendation (GRADE; AGA)
- **Limitations:** Conditional recommendation. Explicitly a case where non-invasive biomarkers are insufficient and endoscopy is preferred.
- **Patient questions:** L3-1.2.2
- **Why:** UC-specific AGA guideline recommendation addressing a common patient question (do symptoms always match inflammation?).
- **Your decision:** `[ ] approve   [ ] defer`

### 5. CLM-119 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** If you have ulcerative colitis with only mild symptoms, the AGA guideline suggests an endoscopic assessment of disease activity to guide treatment decisions.
- **Exact excerpt:** "In patients with UC with mild symptoms, the panel suggests endoscopic assessment of disease activity to inform treatment decisions."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** conditional guideline recommendation (GRADE; AGA)
- **Limitations:** Conditional recommendation; in the mild-symptom setting the guideline does not endorse biomarker-only assessment.
- **Patient questions:** L3-1.2.2
- **Why:** UC-specific AGA guideline recommendation; verbatim excerpt.
- **Your decision:** `[ ] approve   [ ] defer`

### 6. CLM-120 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** The AGA guideline panel noted it is not yet known whether monitoring with biomarkers is better than monitoring with endoscopy; it listed this as a knowledge gap.
- **Exact excerpt:** "The panel identified the use of a biomarker-based monitoring strategy over an endoscopy-based monitoring strategy as a knowledge gap."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** guideline-identified knowledge gap
- **Limitations:** This is a statement about evidence limitations, not a management recommendation. All recommendations in the guideline are conditional.
- **Patient questions:** L2-1.2
- **Why:** UC-specific guideline statement of uncertainty; included so the agent can say what is NOT known rather than overstate biomarkers.
- **Your decision:** `[ ] approve   [ ] defer`

### 7. CLM-121 - SRC-028 - **proposed_include**

- **Source:** AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis (2023) - clinical guideline - https://doi.org/10.1053/j.gastro.2022.12.007
- **Patient-friendly claim:** The AGA guideline concludes that non-invasive tests, including fecal calprotectin, fecal lactoferrin and blood CRP, can inform monitoring and management of ulcerative colitis.
- **Exact excerpt:** "In patients with UC, noninvasive biomarkers, including fecal calprotectin, fecal lactoferrin, and serum CRP can inform disease monitoring and management."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with established ulcerative colitis
- **Evidence strength:** guideline conclusion (GRADE; AGA)
- **Limitations:** 'Can inform' - supportive, not a mandate to replace clinical or endoscopic assessment. Conditional-recommendation evidence base.
- **Patient questions:** L2-1.2, L3-1.2.1
- **Why:** UC-specific AGA guideline conclusion; verbatim excerpt.
- **Your decision:** `[ ] approve   [ ] defer`

### 8. CLM-126 - SRC-033 - **proposed_include**

- **Source:** STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD (2021) - clinical guideline - https://doi.org/10.1053/j.gastro.2020.12.031
- **Patient-friendly claim:** The STRIDE-II consensus says histological healing in ulcerative colitis is not a formal treatment target but should be assessed as a measure of how deep remission is.
- **Exact excerpt:** "Transmural healing in Crohn's disease and histological healing in ulcerative colitis are not formal targets but should be assessed as measures of the remission depth."  (verbatim in public abstract: **yes**)
- **UC applicability:** ibd general with uc subgroup (ibd_general)
- **Study type / population:** Consensus statement; Adults and children with IBD (ulcerative colitis and Crohn's disease)
- **Evidence strength:** expert consensus recommendation (systematic review + Delphi, 89 IOIBD members; 13 of 15 recommendations endorsed)
- **Limitations:** The UC-relevant element is histological healing; the Crohn's element (transmural healing) is out of scope for UC. Consensus position as of 2021; the role of histologic remission in UC is an actively evolving area and later guidance may weigh it differently.
- **Patient questions:** L3-1.2.3
- **Why:** IBD-general consensus with an explicit ulcerative-colitis statement; the claim keeps the source's 'not a formal target' wording. If approved its claim-level applicability is recorded as ulcerative_colitis (the source stays IBD-general) so the app can serve it.
- **Your decision:** `[ ] approve   [ ] defer`

### 9. CLM-701 - SRC-141 - **proposed_include**

- **Source:** A randomized controlled trial of alternate-day versus daily iron therapy in ulcerative colitis in remission (2026) - published study - https://doi.org/10.1016/j.isci.2026.118014
- **Patient-friendly claim:** In a small randomized, open-label trial of 56 people with ulcerative colitis in remission who had iron-deficiency anaemia, daily and alternate-day oral iron did not differ significantly in haemoglobin, red-cell indices or iron measures after 8 weeks, nor in side effects or disease flares.
- **Exact excerpt:** "Our study did not show any significant difference in mean hemoglobin levels, RBC indices, or iron profiles between the daily and alternate-day oral iron groups."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Randomized open-label trial; Adults with ulcerative colitis in remission and iron-deficiency anaemia (n = 56)
- **Evidence strength:** single small open-label randomized trial (low)
- **Limitations:** 56 participants, open-label, 8 weeks, one oral iron formulation, single country; the authors say larger studies are needed. 'No significant difference' does not prove the two schedules are equivalent.
- **Patient questions:** L3-2.2.3
- **Why:** Human randomized trial in UC; excerpt is a direct, appropriately hedged result. Small open-label trial: strength recorded as low.
- **Your decision:** `[ ] approve   [ ] defer`

### 10. CLM-702 - SRC-152 - **proposed_include**

- **Source:** [Guidelines ulcerative colitis: surgery : Status November 2025] (2026) - published study - https://doi.org/10.1007/s00104-026-02615-w
- **Patient-friendly claim:** A German guideline update on ulcerative colitis surgery (status November 2025) states that in acute severe ulcerative colitis, colectomy (surgery to remove the colon) is still indicated when standard drug treatment has failed; in selected cases a JAK inhibitor can be considered as an alternative third-line treatment in specialised centres.
- **Exact excerpt:** "In patients with acute severe ulcerative colitis, colectomy is still indicated for treatment after failure of standard pharmacotherapy, in selected cases a Janus kinase (JAK) inhibitor can be considered as an alternative third line treatment in centers."  (verbatim in public abstract: **yes**)
- **UC applicability:** uc specific human (ulcerative_colitis)
- **Study type / population:** Clinical practice guideline; Adults with acute severe ulcerative colitis who failed standard pharmacotherapy
- **Evidence strength:** national guideline statement (abstract only)
- **Limitations:** German national guideline summarised in a journal abstract; the recommendation grade, evidence level and the full text were not read. Applicability to Canada/US care pathways is not assessed. Decisions about surgery are made with the treating team.
- **Patient questions:** L3-2.3.3, L3-1.1.2
- **Why:** UC-specific national guideline statement on acute severe UC and colectomy; fills a surgery/urgent-care coverage gap. Abstract-level only.
- **Your decision:** `[ ] approve   [ ] defer`

## B. Existing live claims - keep or retire?

These five claims are already live (production `prototype-v1`). Under the stricter 'directly applicable to UC' rule used for this release, only CLM-014 names ulcerative colitis in its excerpt; the others are IBD-general sources tagged UC at source level. Default is **keep** (no change) unless you retire them.

| Claim | Excerpt (start) | Decision |
|---|---|---|
| CLM-014 (ibd general with uc subgroup) | Some differences seem to exist between UC and CD and their risk factors, with increased intake of dietary fiber being inversely associated with CD inc | `[ ] keep  [ ] retire` |
| CLM-081 (ibd general unclear) | Statement 1: In the absence of a specific dietary intervention that is recommended by an IBD healthcare professional, healthy eating guidelines should | `[ ] keep  [ ] retire` |
| CLM-093 (ibd general unclear) | Melanie Living with Crohn's Fruit and vegetables It is recommended that people try to eat at least five portions of a variety of fruit and vegetables  | `[ ] keep  [ ] retire` |
| CLM-094 (ibd general unclear) | Guidelines recommend that you eat 30g of fibre a day. | `[ ] keep  [ ] retire` |
| CLM-095 (ibd general unclear) | Alcohol There is not enough high-quality evidence to know for certain if drinking alcohol could increase your risk of a flare-up. | `[ ] keep  [ ] retire` |

## C. Deferred records

Full list with reasons: `reviewer-workbook.xlsx` (Deferred sheet) and `claims-classified.json`. Highlights worth a second look:

- CLM-244/245/246 (vedolizumab vs anti-TNF sequencing, retrospective n=219) - deferred as observational/treatment-advice risk.
- CLM-252 (VTE prophylaxis for hospitalised IBD) - IBD-general; a UC-specific source would be needed.
- SRC-034 (AGA 2020 moderate-to-severe UC guideline) - staged without claims because PubMed holds no abstract for it.

