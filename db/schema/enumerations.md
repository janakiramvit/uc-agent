# Canonical enumerations & crosswalk (v1.0.0)

_Single source of truth: `db/pipeline/enums.py`. `0004_seed_metadata.sql` is generated from it (`python -m pipeline.gen_seed_sql`); `tests/test_enums.py` asserts they match._

## Policy

- A value that is already canonical -> used as-is.
- A non-canonical value with an **explicit crosswalk row** below -> mapped (documented, reviewable).
- A value with neither -> **unmapped**:
  - `condition` on a claim's `condition_applicability` -> **quarantine** (retrieval-safety).
  - dimensions `confidence, evidence_level, evidence_status, outcome_type, prototype_eligibility_status, review_status, source_type` -> **pending**: canonical column left NULL, `<field>_raw` keeps the verbatim value, record flagged `pending_human_classification`. Never inferred.

## Canonical vocabulary

- **condition**: `ulcerative_colitis`, `crohns_disease`, `ibd_general`, `general_population`, `unclear`
- **disease_context**: `active_disease`, `remission`, `post_surgery`, `stricture_or_obstruction_risk`, `perioperative`, `general_or_unspecified`, `not_applicable`, `unclear`
- **outcome_type**: `symptoms`, `inflammation`, `biomarkers`, `disease_activity`, `remission_induction`, `remission_maintenance`, `relapse_risk`, `hospitalisation`, `surgery`, `nutritional_status`, `quality_of_life`, `adverse_effects`, `adherence`, `general_patient_education`, `obstruction_risk`, `perioperative_nutrition_management`, `evidence_uncertainty`, `unclear`
- **evidence_level**: `formal_guideline`, `consensus_statement`, `systematic_review`, `meta_analysis`, `randomized_trial`, `controlled_trial`, `observational`, `official_patient_information`, `expert_explanation`, `other`
- **confidence**: `high`, `moderate`, `low`
- **source_type**: `guideline`, `systematic_review`, `meta_analysis`, `randomized_trial`, `controlled_trial`, `observational`, `patient_information`, `expert_content`, `other`
- **review_status**: `pending_human_review`, `approved`, `rejected`
- **evidence_status**: `ready_for_human_review`, `still_needs_evidence`
- **prototype_eligibility_status**: `prototype_eligible`, `prototype_eligible_with_limitation`, `excluded`

## Crosswalk (non-identity rows)

| dimension | input_format | input_value | -> canonical | note |
|---|---|---|---|---|
| outcome_type | prototype_workbook | `nutrition_status` | `nutritional_status` | prototype label 'nutrition_status' == canonical 'nutritional_status' |
| outcome_type | qa_workbook | `nutrition_status` | `nutritional_status` | QA sheet label 'nutrition_status' == canonical 'nutritional_status' |
| condition | register_workbook | `general population` | `general_population` | spacing normalization only |
| evidence_level | prototype_workbook | `meta-analysis` | `meta_analysis` | hyphen->underscore, same term |
| evidence_level | prototype_workbook | `systematic review` | `systematic_review` | space->underscore, same term |
| evidence_level | prototype_workbook | `observational study` | `observational` | same study design, canonical drops 'study' |
| evidence_level | prototype_workbook | `randomized controlled trial` | `randomized_trial` | RCT == canonical randomized_trial |
| evidence_level | prototype_workbook | `official patient information` | `official_patient_information` | space->underscore |
| evidence_level | prototype_workbook | `consensus statement` | `consensus_statement` | space->underscore |
| evidence_level | prototype_workbook | `clinical guideline` | `formal_guideline` | synonym; source_type for these rows is 'guideline' |
| evidence_level | prototype_workbook | `guideline/consensus` | _(pending)_ | ambiguous: formal_guideline vs consensus_statement |
| evidence_level | prototype_workbook | `review` | _(pending)_ | ambiguous: narrative vs systematic review |
| evidence_level | prototype_workbook | `EL5` | _(pending)_ | ECCO evidence level 5 (expert opinion); expert_explanation vs other |
| evidence_level | prototype_json | `meta-analysis` | `meta_analysis` | hyphen->underscore, same term |
| evidence_level | prototype_json | `systematic review` | `systematic_review` | space->underscore, same term |
| evidence_level | prototype_json | `observational study` | `observational` | same study design, canonical drops 'study' |
| evidence_level | prototype_json | `randomized controlled trial` | `randomized_trial` | RCT == canonical randomized_trial |
| evidence_level | prototype_json | `official patient information` | `official_patient_information` | space->underscore |
| evidence_level | prototype_json | `consensus statement` | `consensus_statement` | space->underscore |
| evidence_level | prototype_json | `clinical guideline` | `formal_guideline` | synonym; source_type for these rows is 'guideline' |
| evidence_level | prototype_json | `guideline/consensus` | _(pending)_ | ambiguous: formal_guideline vs consensus_statement |
| evidence_level | prototype_json | `review` | _(pending)_ | ambiguous: narrative vs systematic review |
| evidence_level | prototype_json | `EL5` | _(pending)_ | ECCO evidence level 5 (expert opinion); expert_explanation vs other |
| source_type | register_workbook | `guideline` | `guideline` | identity |
| source_type | register_workbook | `expert` | `expert_content` | synonym |
| source_type | register_workbook | `study` | _(pending)_ | ambiguous: RCT / observational / other |
| source_type | register_workbook | `review` | _(pending)_ | ambiguous: systematic_review vs narrative |
| source_type | prototype_workbook | `guideline` | `guideline` | identity |
| source_type | prototype_workbook | `expert` | `expert_content` | synonym |
| source_type | prototype_workbook | `study` | _(pending)_ | ambiguous: RCT / observational / other |
| source_type | prototype_workbook | `review` | _(pending)_ | ambiguous: systematic_review vs narrative |
| source_type | prototype_json | `guideline` | `guideline` | identity |
| source_type | prototype_json | `expert` | `expert_content` | synonym |
| source_type | prototype_json | `study` | _(pending)_ | ambiguous: RCT / observational / other |
| source_type | prototype_json | `review` | _(pending)_ | ambiguous: systematic_review vs narrative |
| source_type | candidate_claims_json | `guideline` | `guideline` | identity |
| source_type | candidate_claims_json | `expert` | `expert_content` | synonym |
| source_type | candidate_claims_json | `study` | _(pending)_ | ambiguous: RCT / observational / other |
| source_type | candidate_claims_json | `review` | _(pending)_ | ambiguous: systematic_review vs narrative |

