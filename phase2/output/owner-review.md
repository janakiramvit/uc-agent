# Owner review - non-production evidence that is usable and UC-applicable

Nothing below is approved, promoted or served. These records sit in dev staging only.

**12 records** are usable and UC-applicable (`ulcerative_colitis` in the applicability, the same rule production uses); **11** more are usable but IBD-general only (listed after, not UC-eligible under the production rule). Counts are discovered from the manifest, not assumed.

## A. Usable and UC-applicable

### 1. CLM-018 - `baseline-register:CLM-018`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that the Mediterranean diet was similar to the Specific Carbohydrate Diet (low certainty of evidence), and partial enteral nutrition (PEN) was similar to exclusive enteral nutrition (very low certainty of evidence).
- **Source:** SRC-005 - Dietary Interventions for the Treatment of Inflammatory Bowel Diseases: An Updated Systematic Review and Meta-analysis.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/36470529/
- **Publication date:** 2023
- **Supporting excerpt:** "The Mediterranean diet was similar to the Specific Carbohydrate Diet (low certainty of evidence), and partial enteral nutrition (PEN) was similar to exclusive enteral nutrition (very low certainty of evidence)."
- **Locator:** PubMed abstract — sentence 7
- **Applicability:** ulcerative_colitis, crohns_disease, ibd_general (uc_specific); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Abstract-only record limits appraisal.
- **Related patient questions** (topic_rule): L3-2.2.2 - How can I evaluate suspected trigger foods or restrictive diets during remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 2. CLM-019 - `baseline-register:CLM-019`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that pEN reduced risk of relapse (very low certainty of evidence), whereas reduction of red meat or refined carbohydrates did not (low certainty of evidence). This is population-level association evidence and does not establish causation or predict an individual's disease course.
- **Source:** SRC-005 - Dietary Interventions for the Treatment of Inflammatory Bowel Diseases: An Updated Systematic Review and Meta-analysis.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/36470529/
- **Publication date:** 2023
- **Supporting excerpt:** "PEN reduced risk of relapse (very low certainty of evidence), whereas reduction of red meat or refined carbohydrates did not (low certainty of evidence)."
- **Locator:** PubMed abstract — sentence 8
- **Applicability:** ulcerative_colitis, crohns_disease, ibd_general (uc_specific); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Abstract-only record limits appraisal.
- **Related patient questions** (unmapped): none mapped
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 3. CLM-048 - `baseline-register:CLM-048`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that meta-analysis showed that there was no significant difference between the clinical recurrence rate of probiotics in the CD remission phase and the control group [relative risk (RR): 0.80, 95% confidence interval (CI): 0.61-1.06, P=0.12]. This is population-level association evidence and does not establish causation or predict an individual's disease course. This is source-attributed information, not a treatment recommendation for an individual.
- **Source:** SRC-012 - Efficacy and safety of probiotics in the induction and maintenance of inflammatory bowel disease remission: a systematic review and meta-analysis.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/34872306/
- **Publication date:** 2021
- **Supporting excerpt:** "Meta-analysis showed that there was no significant difference between the clinical recurrence rate of probiotics in the CD remission phase and the control group [relative risk (RR): 0.80, 95% confidence interval (CI): 0.61-1.06, P=0.12]."
- **Locator:** PubMed abstract — sentence 8
- **Applicability:** ulcerative_colitis, crohns_disease, ibd_general (uc_specific); disease context: remission
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Abstract-only record limits appraisal.
- **Related patient questions** (topic_rule): L3-2.2.2 - How can I evaluate suspected trigger foods or restrictive diets during remission?
- **Reviewer attention:** applicability lists ulcerative colitis, but the claim text itself refers only to Crohn's disease (the applicability may come from the whole source, not this finding)
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 4. CLM-081 - `baseline-register:CLM-081`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that in the absence of a specific dietary intervention that is recommended by an IBD healthcare professional, healthy eating guidelines should be followed by people with IBD, as recommended for the general population. This is source-attributed information, not a treatment recommendation for an individual.
- **Source:** SRC-021 - European Crohn’s and Colitis Organisation consensus on dietary management of inflammatory bowel disease
- **Source URL:** https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055
- **Publication date:** 2025
- **Supporting excerpt:** "In the absence of a specific dietary intervention that is recommended by an IBD healthcare professional, healthy eating guidelines should be followed by people with IBD, as recommended for the general population."
- **Locator:** Official ECCO consensus article — Section 3, "Translation and execution of dietary management"; Statement 1; paragraph beginning "Statement 1: In the absence of a specific dietary intervention..."
- **Applicability:** ulcerative_colitis, crohns_disease, ibd_general (uc_specific); disease context: general_or_unspecified
- **Limitations:** Patient information is explanatory, not a substitute for clinical evidence or individualized care.
- **Related patient questions** (claim_override): L2-2.2 - How should I think about food, nutrition, and symptom-trigger questions?
- **Variant note:** a record with the same claim ID exists as `prototype-v1:CLM-081`; differs in: supporting_excerpt.
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 5. CLM-082 - `baseline-register:CLM-082`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that most evidence for dietary interventions was of low quality, with few studies measuring endoscopic, radiological, or biochemical endpoints or durability of response. This is source-attributed information, not a treatment recommendation for an individual.
- **Source:** SRC-021 - European Crohn’s and Colitis Organisation consensus on dietary management of inflammatory bowel disease
- **Source URL:** https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055
- **Publication date:** 2025
- **Supporting excerpt:** "Most evidence for dietary interventions was of low quality, with few studies measuring endoscopic, radiological, or biochemical endpoints or durability of response."
- **Locator:** Official ECCO consensus article — Section 4.1, "Dietary therapy to induce and maintain remission of IBD"; opening paragraph; sentence beginning "Most evidence for dietary interventions..."
- **Applicability:** ulcerative_colitis, crohns_disease, ibd_general (uc_specific); disease context: general_or_unspecified
- **Limitations:** Patient information is explanatory, not a substitute for clinical evidence or individualized care.
- **Related patient questions** (unmapped): none mapped
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 6. CLM-115 - `uc-evidence-expansion:CLM-115`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** In people with ulcerative colitis in symptomatic remission, the AGA guideline panel suggests a monitoring strategy that combines a non-invasive biomarker with symptoms rather than symptoms alone.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "In patients with UC in symptomatic remission, the panel suggests the use of a biomarker- and symptom-based monitoring strategy over a symptom-based monitoring strategy."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: symptomatic_remission
- **Limitations:** Conditional recommendation; the guideline does not specify monitoring frequency in the retrieved abstract. Applies to established UC, not diagnosis.
- **Related patient questions** (source_provided): L2-1.2 - How should I understand monitoring results and whether I am in remission?; L3-1.2.1 - What do fecal calprotectin, CRP, ESR, and other tests contribute to monitoring?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 7. CLM-116 - `uc-evidence-expansion:CLM-116`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** For a person with ulcerative colitis in symptomatic remission, the panel suggests using fecal calprotectin below 150 micrograms per gram, a normal fecal lactoferrin, and/or a normal CRP to rule out active inflammation and avoid routine endoscopic assessment.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "For patients in symptomatic remission, the panel suggests using fecal calprotectin <150 μg/g, normal fecal lactoferrin, and/or normal CRP to rule out active inflammation and avoid routine endoscopic assessment of disease."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: symptomatic_remission
- **Limitations:** Conditional recommendation. 150 μg/g is a guideline decision threshold, not a diagnostic cut-off for an individual; calprotectin assays are not interchangeable and vary within-day / within-stool.
- **Related patient questions** (source_provided): L3-1.2.1 - What do fecal calprotectin, CRP, ESR, and other tests contribute to monitoring?; L3-1.2.3 - What is the difference between symptom control and clinical, endoscopic, or deeper remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 8. CLM-117 - `uc-evidence-expansion:CLM-117`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** For a person with ulcerative colitis who has moderate-to-severe symptoms, the panel suggests using fecal calprotectin above 150 micrograms per gram, an elevated fecal lactoferrin, or an elevated CRP to inform treatment decisions and avoid routine endoscopic assessment.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "In patients with UC with moderate to severe symptoms, the panel suggests using fecal calprotectin >150 μg/g, elevated fecal lactoferrin, or elevated CRP to inform treatment decisions and avoid routine endoscopic assessment of disease."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: active_disease, moderate_to_severe_symptoms
- **Limitations:** Conditional recommendation. Concordant elevated biomarker + moderate/severe symptoms; interpretation and any treatment change are clinician-led.
- **Related patient questions** (source_provided): L3-1.2.1 - What do fecal calprotectin, CRP, ESR, and other tests contribute to monitoring?; L2-1.1 - How can I recognize a possible flare and judge how urgently I need help?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 9. CLM-118 - `uc-evidence-expansion:CLM-118`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** When symptoms and biomarkers disagree in ulcerative colitis — symptomatic remission with elevated biomarkers, or moderate-to-severe symptoms with normal biomarkers — the panel suggests endoscopic assessment of disease to inform treatment decisions.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "However, in patients in symptomatic remission but elevated biomarkers, and in patients with moderate to severe symptoms with normal biomarkers, the panel suggests endoscopic assessment of disease to inform treatment decisions."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: symptomatic_remission, active_disease, biomarker_symptom_discordance
- **Limitations:** Conditional recommendation. Explicitly a case where non-invasive biomarkers are insufficient and endoscopy is preferred.
- **Related patient questions** (source_provided): L3-1.2.2 - Why might colonoscopy, biopsy, or imaging be recommended when symptoms or labs look reassuring?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 10. CLM-119 - `uc-evidence-expansion:CLM-119`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** For a person with ulcerative colitis who has only mild symptoms, the panel suggests endoscopic assessment of disease activity to inform treatment decisions.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "In patients with UC with mild symptoms, the panel suggests endoscopic assessment of disease activity to inform treatment decisions."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: mild_symptoms
- **Limitations:** Conditional recommendation; in the mild-symptom setting the guideline does not endorse biomarker-only assessment.
- **Related patient questions** (source_provided): L3-1.2.2 - Why might colonoscopy, biopsy, or imaging be recommended when symptoms or labs look reassuring?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 11. CLM-120 - `uc-evidence-expansion:CLM-120`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** The AGA guideline panel made 7 conditional recommendations on biomarker use in ulcerative colitis, and identified using a biomarker-based rather than an endoscopy-based monitoring strategy as a knowledge gap.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "The panel identified the use of a biomarker-based monitoring strategy over an endoscopy-based monitoring strategy as a knowledge gap."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372. Page/statement-level locators require full text (link_only).
- **Applicability:** ulcerative_colitis (uc_specific); disease context: general_monitoring
- **Limitations:** This is a statement about evidence limitations, not a management recommendation. All recommendations in the guideline are conditional.
- **Related patient questions** (source_provided): L2-1.2 - How should I understand monitoring results and whether I am in remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 12. CLM-121 - `uc-evidence-expansion:CLM-121`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** The guideline concludes that in ulcerative colitis, non-invasive biomarkers including fecal calprotectin, fecal lactoferrin and serum CRP can inform disease monitoring and management.
- **Source:** SRC-028 - AGA Clinical Practice Guideline on the Role of Biomarkers for the Management of Ulcerative Colitis
- **Source URL:** https://doi.org/10.1053/j.gastro.2022.12.007
- **Publication date:** 2023-03
- **Supporting excerpt:** "In patients with UC, noninvasive biomarkers, including fecal calprotectin, fecal lactoferrin, and serum CRP can inform disease monitoring and management."
- **Locator:** Abstract (structured), Conclusions section — Europe PMC record EXT_ID:36822736; Gastroenterology 2023;164(3):344-372.
- **Applicability:** ulcerative_colitis (uc_specific); disease context: general_monitoring
- **Limitations:** 'Can inform' - supportive, not a mandate to replace clinical or endoscopic assessment. Conditional-recommendation evidence base.
- **Related patient questions** (source_provided): L2-1.2 - How should I understand monitoring results and whether I am in remission?; L3-1.2.1 - What do fecal calprotectin, CRP, ESR, and other tests contribute to monitoring?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

## B. Usable, IBD-general only (not UC-eligible under the production rule)

### 1. CLM-025 - `baseline-register:CLM-025`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that of these 17 were included in meta-analysis which showed overall increased lactose maldigestion in both diseases.
- **Source:** SRC-007 - Systematic review and meta-analysis of lactose digestion, its impact on intolerance and nutritional effects of dairy food restriction in inflammatory bowel diseases.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/27411934/
- **Publication date:** 2016
- **Supporting excerpt:** "Of these 17 were included in meta-analysis which showed overall increased lactose maldigestion in both diseases."
- **Locator:** PubMed abstract — sentence 6
- **Applicability:** crohns_disease, ibd_general (ibd_general); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Public full text available for deeper review.
- **Related patient questions** (topic_rule): L3-2.2.2 - How can I evaluate suspected trigger foods or restrictive diets during remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 2. CLM-026 - `baseline-register:CLM-026`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that lactose maldigestion in inflammatory bowel disease is dependent on ethnic makeup of the population and usually not disease. The specific measured marker or inflammatory outcome should remain explicit.
- **Source:** SRC-007 - Systematic review and meta-analysis of lactose digestion, its impact on intolerance and nutritional effects of dairy food restriction in inflammatory bowel diseases.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/27411934/
- **Publication date:** 2016
- **Supporting excerpt:** "CONCLUSIONS: Lactose maldigestion in inflammatory bowel disease is dependent on ethnic makeup of the population and usually not disease."
- **Locator:** PubMed abstract — sentence 12
- **Applicability:** ibd_general (ibd_general); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Public full text available for deeper review.
- **Related patient questions** (topic_rule): L3-2.2.2 - How can I evaluate suspected trigger foods or restrictive diets during remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 3. CLM-030 - `baseline-register:CLM-030`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that during the disease course, most Inflammatory Bowel Disease patients present a condition of malnutrition, undernutrition, or even overnutrition. The specific measured marker or inflammatory outcome should remain explicit.
- **Source:** SRC-008 - Nutrition, Nutritional Status, Micronutrients Deficiency, and Disease Course of Inflammatory Bowel Disease.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/37686856/
- **Publication date:** 2023
- **Supporting excerpt:** "During the disease course, most Inflammatory Bowel Disease patients present a condition of malnutrition, undernutrition, or even overnutrition."
- **Locator:** PubMed abstract — sentence 1
- **Applicability:** ibd_general (ibd_general); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Public full text available for deeper review.
- **Related patient questions** (topic_rule): L3-2.2.3 - When do weight loss, poor intake, dehydration, anemia, or nutrient concerns need specialist help?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 4. CLM-033 - `baseline-register:CLM-033`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that poor sleep in people with inflammatory bowel disease (IBD) has been demonstrated to be prevalent and has been associated with disease activity. This is population-level association evidence and does not establish causation or predict an individual's disease course. The specific measured marker or inflammatory outcome should remain explicit.
- **Source:** SRC-009 - Systematic review and meta-analysis of sleep quality in inactive inflammatory bowel disease.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/36406652/
- **Publication date:** 2022
- **Supporting excerpt:** "Poor sleep in people with inflammatory bowel disease (IBD) has been demonstrated to be prevalent and has been associated with disease activity."
- **Locator:** PubMed abstract — sentence 1
- **Applicability:** ibd_general (ibd_general); disease context: general_or_unspecified
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Public full text available for deeper review.
- **Related patient questions** (unmapped): none mapped
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 5. CLM-071 - `baseline-register:CLM-071`

- **Status:** usable (not approved; review status `pending_human_review`, evidence status `ready_for_human_review`)
- **Claim:** The cited source reports that in an analysis of data from the FACES trial, we found that among patients with CD in remission, level of red and processed meat consumption was not associated with time to symptomatic relapse. This is population-level association evidence and does not establish causation or predict an individual's disease course. This is source-attributed information, not a treatment recommendation for an individual.
- **Source:** SRC-018 - A Diet Low in Red and Processed Meat Does Not Reduce Rate of Crohn's Disease Flares.
- **Source URL:** https://pubmed.ncbi.nlm.nih.gov/30872105/
- **Publication date:** 2019
- **Supporting excerpt:** "CONCLUSIONS: In an analysis of data from the FACES trial, we found that among patients with CD in remission, level of red and processed meat consumption was not associated with time to symptomatic relapse."
- **Locator:** PubMed abstract — sentence 10
- **Applicability:** crohns_disease, ibd_general (ibd_general); disease context: remission
- **Limitations:** Automated metadata and passage extraction; full methods and tables require human review. Public full text available for deeper review.
- **Related patient questions** (unmapped): none mapped
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 6. CLM-122 - `uc-evidence-expansion:CLM-122`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** The STRIDE-II consensus was informed by a systematic review in which 11,278 manuscripts were screened and 435 were included.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "In the systematic review, 11,278 manuscripts were screened, of which 435 were included."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583. Page/statement-level locators require full text (link_only).
- **Applicability:** ibd_general (ibd_general); disease context: evidence_base
- **Limitations:** Describes the evidence base, not a clinical target. IBD-general (UC + Crohn's).
- **Related patient questions** (source_provided): L2-1.2 - How should I understand monitoring results and whether I am in remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 7. CLM-123 - `uc-evidence-expansion:CLM-123`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** An initial IOIBD survey rated the most important treat-to-target goals in IBD as clinical response and remission, endoscopic healing, and normalisation of C-reactive protein / erythrocyte sedimentation rate and calprotectin.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "The first IOIBD survey identified the following targets as most important: clinical response and remission, endoscopic healing, and normalization of C-reactive protein/erythrocyte sedimentation rate and calprotectin."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583. Page/statement-level locators require full text (link_only).
- **Applicability:** ibd_general (ibd_general); disease context: target_setting
- **Limitations:** IBD-general (UC + Crohn's); not a UC-only statement. Reflects expert prioritisation, not diagnostic-accuracy data. ESR appears here only as a general IBD marker, not a validated UC-specific target.
- **Related patient questions** (source_provided): L3-1.2.1 - What do fecal calprotectin, CRP, ESR, and other tests contribute to monitoring?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 8. CLM-124 - `uc-evidence-expansion:CLM-124`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** STRIDE-II confirmed the STRIDE-I long-term targets of clinical remission and endoscopic healing, and added absence of disability, restoration of quality of life, and normal growth in children.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "STRIDE-II confirmed STRIDE-I long-term targets of clinical remission and endoscopic healing and added absence of disability, restoration of quality of life, and normal growth in children."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583. Page/statement-level locators require full text (link_only).
- **Applicability:** ibd_general (ibd_general); disease context: remission, long_term_targets
- **Limitations:** IBD-general (UC + Crohn's). Consensus-based; 'endoscopic healing' definitions vary by scoring index and are not defined in the abstract.
- **Related patient questions** (source_provided): L3-1.2.3 - What is the difference between symptom control and clinical, endoscopic, or deeper remission?; L2-1.2 - How should I understand monitoring results and whether I am in remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 9. CLM-125 - `uc-evidence-expansion:CLM-125`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** STRIDE-II designates symptomatic relief and normalisation of serum and fecal markers as short-term treatment targets in IBD.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "Symptomatic relief and normalization of serum and fecal markers have been determined as short-term targets."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583. Page/statement-level locators require full text (link_only).
- **Applicability:** ibd_general (ibd_general); disease context: short_term_targets, active_disease
- **Limitations:** IBD-general (UC + Crohn's). 'Normalization' is not given a numeric threshold in the abstract.
- **Related patient questions** (source_provided): L3-1.2.3 - What is the difference between symptom control and clinical, endoscopic, or deeper remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 10. CLM-126 - `uc-evidence-expansion:CLM-126`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** In STRIDE-II, transmural healing in Crohn's disease and histological healing in ulcerative colitis are not formal treatment targets but should be assessed as measures of the depth of remission.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "Transmural healing in Crohn's disease and histological healing in ulcerative colitis are not formal targets but should be assessed as measures of the remission depth."
- **Locator:** Abstract (structured), Results section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583. Page/statement-level locators require full text (link_only).
- **Applicability:** ibd_general (ibd_general); disease context: remission, remission_depth, histologic_healing
- **Limitations:** The UC-relevant element is histological healing; the Crohn's element (transmural healing) is out of scope for UC. Consensus position as of 2021; the role of histologic remission in UC is an actively evolving area and later guidance may weigh it differently.
- **Related patient questions** (source_provided): L3-1.2.3 - What is the difference between symptom control and clinical, endoscopic, or deeper remission?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

### 11. CLM-127 - `uc-evidence-expansion:CLM-127`

- **Status:** usable (not approved; review status `pending_clinical_review`, evidence status `extracted`)
- **Claim:** STRIDE-II states that its treat-to-target framework should be adapted to individual patients and to local resources in order to improve outcomes.
- **Source:** SRC-033 - STRIDE-II: An Update on the Selecting Therapeutic Targets in Inflammatory Bowel Disease (STRIDE) Initiative of the International Organization for the Study of IBD (IOIBD): Determining Therapeutic Goals for Treat-to-Target strategies in IBD
- **Source URL:** https://doi.org/10.1053/j.gastro.2020.12.031
- **Publication date:** 2021-04
- **Supporting excerpt:** "should be adapted to individual patients and local resources to improve outcomes."
- **Locator:** Abstract (structured), Conclusions section — Europe PMC record EXT_ID:33359090; Gastroenterology 2021;160(5):1570-1583.
- **Applicability:** ibd_general (ibd_general); disease context: implementation
- **Limitations:** Explicit implementation caveat: targets and monitoring must be individualised and resource-adjusted. IBD-general. NOTE: the Europe PMC abstract record concatenates 'framework' and 'should' ('frameworkshould') as a text-rendering artifact; the excerpt is quoted from 'should be adapted...'. Confirm exact wording against the publisher full text at human review.
- **Related patient questions** (source_provided): L2-1.2 - How should I understand monitoring results and whether I am in remission?; L3-1.3.3 - What can I do when treatment, specialist appointments, tests, or medicines are delayed or unaffordable?
- **Owner decision:** `[ ] approve   [ ] reject   [ ] needs work`  (left blank - nothing is approved)

