-- 0003_canonical_views.sql  (Prompt v1.0.0)
-- Reversible: see 0003_canonical_views.down.sql
-- The ONLY objects the application is allowed to read. Created now; return 0 rows until
-- an approved promotion populates the base tables.

CREATE VIEW canonical.v_dataset AS
SELECT dataset_id, code, version, status, source_description, ingested_at, package_meta
FROM canonical.dataset;

CREATE VIEW canonical.v_source AS
SELECT s.*, d.code AS dataset_code, d.version AS dataset_version
FROM canonical.source s
JOIN canonical.dataset d USING (dataset_id);

CREATE VIEW canonical.v_claim AS
SELECT c.*,
       d.code    AS dataset_code,
       d.version AS dataset_version,
       cc.citation_url,
       cc.exact_locator          AS citation_exact_locator,
       cc.supporting_excerpt     AS citation_supporting_excerpt,
       cc.authoritative_passage  AS citation_authoritative_passage
FROM canonical.claim c
JOIN canonical.dataset d USING (dataset_id)
LEFT JOIN canonical.claim_citation cc ON cc.claim_id = c.id;

CREATE VIEW canonical.v_claim_qa AS
SELECT q.*, d.code AS dataset_code
FROM canonical.claim_qa q
JOIN canonical.dataset d USING (dataset_id);

CREATE VIEW canonical.v_schema_reconciliation AS
SELECT r.*, d.code AS dataset_code
FROM canonical.reconciliation_note r
LEFT JOIN canonical.dataset d USING (dataset_id);

-- ---- prototype-v1 shadow shape: byte-parity with ibd-prototype-evidence.json ----
-- Uses the *_raw (verbatim) columns so the emitted objects equal the file exactly.

CREATE VIEW canonical.v_prototype_source AS
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
WHERE d.code = 'prototype-v1';

CREATE VIEW canonical.v_prototype_claim AS
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
WHERE d.code = 'prototype-v1';

CREATE VIEW canonical.v_prototype_excluded_claim_id AS
SELECT e.claim_ref
FROM canonical.excluded_claim e
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code = 'prototype-v1'
ORDER BY e.claim_ref;

CREATE VIEW canonical.v_prototype_limitation AS
SELECT l.ordinal, l.text
FROM canonical.dataset_limitation l
JOIN canonical.dataset d USING (dataset_id)
WHERE d.code = 'prototype-v1'
ORDER BY l.ordinal;

-- The app's exact eligibility rule: conditionApplicability contains 'ulcerative_colitis'.
CREATE VIEW canonical.v_uc_eligible_claim AS
SELECT * FROM canonical.v_prototype_claim
WHERE "conditionApplicability" ILIKE '%ulcerative_colitis%';

REVOKE ALL ON ALL TABLES IN SCHEMA canonical FROM PUBLIC;
