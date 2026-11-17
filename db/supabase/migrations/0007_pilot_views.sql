-- 0007_pilot_views.sql  (pilot evidence release 2026-11-17)
-- Reversible: see 0007_pilot_views.down.sql
--
-- The pilot package = the live prototype-v1 dataset PLUS owner-reviewed additions held in a separate dataset
-- ('pilot-additions'). Keeping them apart means prototype-v1 stays byte-identical to the JSON oracle and the rollback is a
-- single environment switch (EVIDENCE_DATASET=prototype-v1). These views have exactly the shape of the v_prototype_* views
-- and are the only new objects the application may read.

CREATE VIEW canonical.v_pilot_source AS
SELECT
    s.source_ref                                   AS "sourceId",
    s.title                                        AS "sourceTitle",
    s.authoritative_url                            AS "sourceUrl",
    s.pub_year                                     AS "publicationYear",
    s.source_type_raw                              AS "sourceType",
    s.condition_applicability_raw                  AS "conditionApplicability",
    s.disease_context_raw                          AS "diseaseContext",
    s.evidence_limitations                         AS "evidenceLimitations",
    s.region_applicability_note                    AS "canadaUsApplicability",
    s.regional_assessment                          AS "regionalAssessment",
    COALESCE(s.review_status_raw, '')              AS "reviewStatus",
    d.code                                         AS "datasetCode",
    jsonb_build_object(
        'sourceId', s.source_ref, 'sourceTitle', s.title, 'sourceUrl', s.authoritative_url,
        'publicationYear', s.pub_year, 'sourceType', s.source_type_raw,
        'conditionApplicability', s.condition_applicability_raw,
        'diseaseContext', s.disease_context_raw,
        'evidenceLimitations', s.evidence_limitations,
        'canadaUsApplicability', s.region_applicability_note,
        'regionalAssessment', s.regional_assessment,
        'reviewStatus', COALESCE(s.review_status_raw, '')
    )                                              AS source_json
FROM canonical.source s
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code IN ('prototype-v1', 'pilot-additions') AND d.status = 'promoted';

CREATE VIEW canonical.v_pilot_claim AS
SELECT
    c.claim_ref                                    AS "claimId",
    c.source_ref                                   AS "sourceId",
    c.source_title                                 AS "sourceTitle",
    c.authoritative_url                            AS "sourceUrl",
    c.condition_applicability_raw                  AS "conditionApplicability",
    c.disease_context_raw                          AS "diseaseContext",
    c.topic                                        AS "topic",
    c.outcome_type_raw                             AS "outcomeType",
    c.claim_text                                   AS "claimText",
    c.plain_language_explanation                   AS "plainLanguageExplanation",
    c.supporting_excerpt                           AS "supportingExcerpt",
    c.precise_locator                              AS "exactLocator",
    c.evidence_level_raw                           AS "evidenceLevel",
    c.limitations                                  AS "limitations",
    c.applicability_limitations                    AS "applicabilityLimitations",
    c.confidence_raw                               AS "confidence",
    c.prototype_eligibility_status_raw             AS "prototypeEligibilityStatus",
    d.code                                         AS "datasetCode",
    jsonb_build_object(
        'claimId', c.claim_ref, 'sourceId', c.source_ref, 'sourceTitle', c.source_title,
        'sourceUrl', c.authoritative_url,
        'conditionApplicability', c.condition_applicability_raw,
        'diseaseContext', c.disease_context_raw, 'topic', c.topic,
        'outcomeType', c.outcome_type_raw, 'claimText', c.claim_text,
        'plainLanguageExplanation', c.plain_language_explanation,
        'supportingExcerpt', c.supporting_excerpt, 'exactLocator', c.precise_locator,
        'evidenceLevel', c.evidence_level_raw, 'limitations', c.limitations,
        'applicabilityLimitations', c.applicability_limitations,
        'confidence', c.confidence_raw,
        'prototypeEligibilityStatus', c.prototype_eligibility_status_raw
    )                                              AS claim_json
FROM canonical.claim c
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code IN ('prototype-v1', 'pilot-additions') AND d.status = 'promoted';

CREATE VIEW canonical.v_pilot_excluded_claim_id AS
SELECT e.claim_ref
FROM canonical.excluded_claim e
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code IN ('prototype-v1', 'pilot-additions') AND d.status = 'promoted'
ORDER BY e.claim_ref;

-- limitations of BOTH datasets, prototype first, then the pilot additions (ordinal restarts per dataset)
CREATE VIEW canonical.v_pilot_limitation AS
SELECT row_number() OVER (ORDER BY (d.code <> 'prototype-v1'), l.ordinal) AS ordinal, l.text
FROM canonical.dataset_limitation l
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code IN ('prototype-v1', 'pilot-additions') AND d.status = 'promoted'
ORDER BY 1;

GRANT SELECT ON canonical.v_pilot_source, canonical.v_pilot_claim,
                canonical.v_pilot_excluded_claim_id, canonical.v_pilot_limitation
TO evidence_reader;
