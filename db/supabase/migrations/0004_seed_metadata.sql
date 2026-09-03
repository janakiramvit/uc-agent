-- 0004_seed_metadata.sql  (Prompt v1.0.0)
-- Reversible: see 0004_seed_metadata.down.sql
-- METADATA ONLY. No source/claim rows. Generated from pipeline/enums.py by
-- pipeline/gen_seed_sql.py - tests/test_enums.py asserts this file matches enums.py.

INSERT INTO canonical.schema_version(version, description) VALUES
  ('1.0.0', 'Schema-compatibility gate: baseline-register + prototype-v1 datasets')
ON CONFLICT (version) DO NOTHING;

INSERT INTO canonical.enum_domain(dimension, description) VALUES
  ('condition', 'canonical vocabulary for condition'),
  ('confidence', 'canonical vocabulary for confidence'),
  ('disease_context', 'canonical vocabulary for disease_context'),
  ('evidence_level', 'canonical vocabulary for evidence_level'),
  ('evidence_status', 'canonical vocabulary for evidence_status'),
  ('outcome_type', 'canonical vocabulary for outcome_type'),
  ('prototype_eligibility_status', 'canonical vocabulary for prototype_eligibility_status'),
  ('review_status', 'canonical vocabulary for review_status'),
  ('source_type', 'canonical vocabulary for source_type')
ON CONFLICT (dimension) DO NOTHING;

INSERT INTO canonical.enum_value(dimension, value, ordinal) VALUES
  ('condition', 'ulcerative_colitis', 0),
  ('condition', 'crohns_disease', 1),
  ('condition', 'ibd_general', 2),
  ('condition', 'general_population', 3),
  ('condition', 'unclear', 4),
  ('disease_context', 'active_disease', 0),
  ('disease_context', 'remission', 1),
  ('disease_context', 'post_surgery', 2),
  ('disease_context', 'stricture_or_obstruction_risk', 3),
  ('disease_context', 'perioperative', 4),
  ('disease_context', 'general_or_unspecified', 5),
  ('disease_context', 'not_applicable', 6),
  ('disease_context', 'unclear', 7),
  ('outcome_type', 'symptoms', 0),
  ('outcome_type', 'inflammation', 1),
  ('outcome_type', 'biomarkers', 2),
  ('outcome_type', 'disease_activity', 3),
  ('outcome_type', 'remission_induction', 4),
  ('outcome_type', 'remission_maintenance', 5),
  ('outcome_type', 'relapse_risk', 6),
  ('outcome_type', 'hospitalisation', 7),
  ('outcome_type', 'surgery', 8),
  ('outcome_type', 'nutritional_status', 9),
  ('outcome_type', 'quality_of_life', 10),
  ('outcome_type', 'adverse_effects', 11),
  ('outcome_type', 'adherence', 12),
  ('outcome_type', 'general_patient_education', 13),
  ('outcome_type', 'obstruction_risk', 14),
  ('outcome_type', 'perioperative_nutrition_management', 15),
  ('outcome_type', 'evidence_uncertainty', 16),
  ('outcome_type', 'unclear', 17),
  ('evidence_level', 'formal_guideline', 0),
  ('evidence_level', 'consensus_statement', 1),
  ('evidence_level', 'systematic_review', 2),
  ('evidence_level', 'meta_analysis', 3),
  ('evidence_level', 'randomized_trial', 4),
  ('evidence_level', 'controlled_trial', 5),
  ('evidence_level', 'observational', 6),
  ('evidence_level', 'official_patient_information', 7),
  ('evidence_level', 'expert_explanation', 8),
  ('evidence_level', 'other', 9),
  ('confidence', 'high', 0),
  ('confidence', 'moderate', 1),
  ('confidence', 'low', 2),
  ('source_type', 'guideline', 0),
  ('source_type', 'systematic_review', 1),
  ('source_type', 'meta_analysis', 2),
  ('source_type', 'randomized_trial', 3),
  ('source_type', 'controlled_trial', 4),
  ('source_type', 'observational', 5),
  ('source_type', 'patient_information', 6),
  ('source_type', 'expert_content', 7),
  ('source_type', 'other', 8),
  ('review_status', 'pending_human_review', 0),
  ('review_status', 'approved', 1),
  ('review_status', 'rejected', 2),
  ('evidence_status', 'ready_for_human_review', 0),
  ('evidence_status', 'still_needs_evidence', 1),
  ('prototype_eligibility_status', 'prototype_eligible', 0),
  ('prototype_eligibility_status', 'prototype_eligible_with_limitation', 1),
  ('prototype_eligibility_status', 'excluded', 2)
ON CONFLICT (dimension, value) DO NOTHING;

INSERT INTO canonical.enum_crosswalk(dimension, input_format, input_value, canonical_value, note) VALUES
  ('outcome_type', 'prototype_workbook', 'nutrition_status', 'nutritional_status', 'prototype label ''nutrition_status'' == canonical ''nutritional_status'''),
  ('outcome_type', 'qa_workbook', 'nutrition_status', 'nutritional_status', 'QA sheet label ''nutrition_status'' == canonical ''nutritional_status'''),
  ('condition', 'register_workbook', 'general population', 'general_population', 'spacing normalization only'),
  ('evidence_level', 'prototype_workbook', 'meta-analysis', 'meta_analysis', 'hyphen->underscore, same term'),
  ('evidence_level', 'prototype_workbook', 'systematic review', 'systematic_review', 'space->underscore, same term'),
  ('evidence_level', 'prototype_workbook', 'observational study', 'observational', 'same study design, canonical drops ''study'''),
  ('evidence_level', 'prototype_workbook', 'randomized controlled trial', 'randomized_trial', 'RCT == canonical randomized_trial'),
  ('evidence_level', 'prototype_workbook', 'official patient information', 'official_patient_information', 'space->underscore'),
  ('evidence_level', 'prototype_workbook', 'consensus statement', 'consensus_statement', 'space->underscore'),
  ('evidence_level', 'prototype_workbook', 'clinical guideline', 'formal_guideline', 'synonym; source_type for these rows is ''guideline'''),
  ('evidence_level', 'prototype_workbook', 'guideline/consensus', NULL, 'ambiguous: formal_guideline vs consensus_statement'),
  ('evidence_level', 'prototype_workbook', 'review', NULL, 'ambiguous: narrative vs systematic review'),
  ('evidence_level', 'prototype_workbook', 'EL5', NULL, 'ECCO evidence level 5 (expert opinion); expert_explanation vs other'),
  ('evidence_level', 'prototype_json', 'meta-analysis', 'meta_analysis', 'hyphen->underscore, same term'),
  ('evidence_level', 'prototype_json', 'systematic review', 'systematic_review', 'space->underscore, same term'),
  ('evidence_level', 'prototype_json', 'observational study', 'observational', 'same study design, canonical drops ''study'''),
  ('evidence_level', 'prototype_json', 'randomized controlled trial', 'randomized_trial', 'RCT == canonical randomized_trial'),
  ('evidence_level', 'prototype_json', 'official patient information', 'official_patient_information', 'space->underscore'),
  ('evidence_level', 'prototype_json', 'consensus statement', 'consensus_statement', 'space->underscore'),
  ('evidence_level', 'prototype_json', 'clinical guideline', 'formal_guideline', 'synonym; source_type for these rows is ''guideline'''),
  ('evidence_level', 'prototype_json', 'guideline/consensus', NULL, 'ambiguous: formal_guideline vs consensus_statement'),
  ('evidence_level', 'prototype_json', 'review', NULL, 'ambiguous: narrative vs systematic review'),
  ('evidence_level', 'prototype_json', 'EL5', NULL, 'ECCO evidence level 5 (expert opinion); expert_explanation vs other'),
  ('source_type', 'register_workbook', 'guideline', 'guideline', 'identity'),
  ('source_type', 'register_workbook', 'expert', 'expert_content', 'synonym'),
  ('source_type', 'register_workbook', 'study', NULL, 'ambiguous: RCT / observational / other'),
  ('source_type', 'register_workbook', 'review', NULL, 'ambiguous: systematic_review vs narrative'),
  ('source_type', 'prototype_workbook', 'guideline', 'guideline', 'identity'),
  ('source_type', 'prototype_workbook', 'expert', 'expert_content', 'synonym'),
  ('source_type', 'prototype_workbook', 'study', NULL, 'ambiguous: RCT / observational / other'),
  ('source_type', 'prototype_workbook', 'review', NULL, 'ambiguous: systematic_review vs narrative'),
  ('source_type', 'prototype_json', 'guideline', 'guideline', 'identity'),
  ('source_type', 'prototype_json', 'expert', 'expert_content', 'synonym'),
  ('source_type', 'prototype_json', 'study', NULL, 'ambiguous: RCT / observational / other'),
  ('source_type', 'prototype_json', 'review', NULL, 'ambiguous: systematic_review vs narrative'),
  ('source_type', 'candidate_claims_json', 'guideline', 'guideline', 'identity'),
  ('source_type', 'candidate_claims_json', 'expert', 'expert_content', 'synonym'),
  ('source_type', 'candidate_claims_json', 'study', NULL, 'ambiguous: RCT / observational / other'),
  ('source_type', 'candidate_claims_json', 'review', NULL, 'ambiguous: systematic_review vs narrative')
ON CONFLICT (dimension, input_format, input_value) DO NOTHING;

-- Version-aware dataset identity rows (metadata; not evidence).
INSERT INTO canonical.dataset(code, version, source_description, status) VALUES
  ('baseline-register', '1.0.0', 'ibd-evidence-review-final-remediation.xlsx (Sources+Claims register)', 'staged'),
  ('prototype-v1', '1.0.0', 'ibd-prototype-evidence-review.xlsx (existing 49/20 prototype cut)', 'staged')
ON CONFLICT (code, version) DO NOTHING;

