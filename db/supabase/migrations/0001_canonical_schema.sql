-- 0001_canonical_schema.sql  (Prompt v1.0.0 / canonical schema v1.0.0)
-- Reversible: see 0001_canonical_schema.down.sql
--
-- Canonical evidence schema. Base tables only; created EMPTY. No source/claim rows are
-- inserted here or by any migration - promotion is a separate, approved step.
-- Every clinical / applicability / evidence-strength / licensing / review column is
-- NULL-able and stays NULL when the input does not carry the value.

CREATE SCHEMA IF NOT EXISTS canonical;

-- Applied-migration ledger (also created by the Python runner; idempotent).
CREATE TABLE IF NOT EXISTS canonical.schema_migration (
    filename    text PRIMARY KEY,
    sha256      text NOT NULL,
    applied_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE canonical.schema_version (
    version     text PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now(),
    description text
);

-- ---------------------------------------------------------------- enumerations
CREATE TABLE canonical.enum_domain (
    dimension   text PRIMARY KEY,
    description text
);

CREATE TABLE canonical.enum_value (
    dimension text NOT NULL REFERENCES canonical.enum_domain(dimension),
    value     text NOT NULL,
    ordinal   int  NOT NULL DEFAULT 0,
    PRIMARY KEY (dimension, value)
);

-- Every non-canonical input value must have an explicit crosswalk row (canonical_value
-- may be NULL = "known, deliberately not auto-mapped -> pending human classification").
CREATE TABLE canonical.enum_crosswalk (
    id              bigserial PRIMARY KEY,
    dimension       text NOT NULL REFERENCES canonical.enum_domain(dimension),
    input_format    text NOT NULL,
    input_value     text NOT NULL,
    canonical_value text,
    note            text,
    UNIQUE (dimension, input_format, input_value)
);

-- ---------------------------------------------------------------- datasets
CREATE TABLE canonical.dataset (
    dataset_id         bigserial PRIMARY KEY,
    code               text NOT NULL,
    version            text NOT NULL,
    source_description  text,
    load_batch_id      uuid,
    ingested_at        timestamptz,
    status             text NOT NULL DEFAULT 'staged'
        CHECK (status IN ('staged', 'promoted', 'superseded')),
    package_meta       jsonb NOT NULL DEFAULT '{}'::jsonb,   -- intended_use, limitations[], created_at
    UNIQUE (code, version)                                    -- version-aware identity
);

CREATE TABLE canonical.dataset_limitation (
    dataset_id bigint NOT NULL REFERENCES canonical.dataset(dataset_id) ON DELETE CASCADE,
    ordinal    int    NOT NULL,
    text       text   NOT NULL,
    PRIMARY KEY (dataset_id, ordinal)
);

-- ---------------------------------------------------------------- sources
CREATE TABLE canonical.source (
    id                        bigserial PRIMARY KEY,
    dataset_id                bigint NOT NULL REFERENCES canonical.dataset(dataset_id),
    source_ref                text NOT NULL,
    title                     text,
    source_type               text,          -- canonical enum value (NULL if pending)
    source_type_raw           text,          -- verbatim input
    status                    text,
    authors                   text,
    journal                   text,
    pub_year                  int,
    authoritative_url         text,
    canonical_url             text,
    pmid                      text,
    pmcid                     text,
    doi                       text,
    full_text_verification    text,
    condition_applicability   text[],        -- canonical tokens (NULL if any unmapped)
    condition_applicability_raw text,
    disease_context           text[],
    disease_context_raw       text,
    main_relevant_finding     text,
    evidence_limitations      text,
    access_licensing_note     text,
    region_applicability_note text,
    regional_assessment       text,
    review_status             text,
    review_status_raw         text,
    UNIQUE (dataset_id, source_ref)
);

-- ---------------------------------------------------------------- claims
CREATE TABLE canonical.claim (
    id                          bigserial PRIMARY KEY,
    dataset_id                  bigint NOT NULL REFERENCES canonical.dataset(dataset_id),
    claim_ref                   text NOT NULL,
    source_ref                  text NOT NULL,
    split_from_ref              text,
    source_title                text,
    topic                       text,
    condition_applicability     text[],
    condition_applicability_raw text,
    disease_context             text[],
    disease_context_raw         text,
    claim_text                  text NOT NULL,
    original_claim_text         text,
    qa_proposed_claim_text      text,
    supporting_excerpt          text NOT NULL,
    exact_authoritative_passage text,
    precise_locator             text NOT NULL,
    authoritative_url           text,
    evidence_status             text,
    final_qa_eligibility        text,
    approved_export_eligibility text,
    verification_status         text,
    remediation_note            text,
    limitations                 text,
    applicability_limitations   text,
    plain_language_explanation  text,
    outcome_type                text,
    outcome_type_raw            text,
    study_type                  text,
    evidence_level              text,
    evidence_level_raw          text,
    confidence                  text,
    confidence_raw              text,
    review_status               text,
    review_status_raw           text,
    prototype_eligibility_status text,
    prototype_eligibility_status_raw text,
    UNIQUE (dataset_id, claim_ref),
    FOREIGN KEY (dataset_id, source_ref)
        REFERENCES canonical.source (dataset_id, source_ref)
);

-- Preserve-verbatim citation/locator fields as their own testable 1:1 table.
CREATE TABLE canonical.claim_citation (
    claim_id             bigint PRIMARY KEY REFERENCES canonical.claim(id) ON DELETE CASCADE,
    dataset_id           bigint NOT NULL REFERENCES canonical.dataset(dataset_id),
    citation_url         text,
    exact_locator        text,
    supporting_excerpt   text,
    authoritative_passage text
);

-- QA-workbook overlay. NOT joined into claim. May reference claims that were never
-- promoted (e.g. an excluded claim), so no FK to canonical.claim.
CREATE TABLE canonical.claim_qa (
    id           bigserial PRIMARY KEY,
    dataset_id   bigint NOT NULL REFERENCES canonical.dataset(dataset_id),
    claim_ref    text NOT NULL,
    qa_dimension text NOT NULL,
    qa_outcome   text,
    qa_note      text,
    findings     jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (dataset_id, claim_ref, qa_dimension)
);

CREATE TABLE canonical.excluded_claim (
    dataset_id bigint NOT NULL REFERENCES canonical.dataset(dataset_id),
    claim_ref  text NOT NULL,
    result     text,
    reason     text,
    origin     text,
    PRIMARY KEY (dataset_id, claim_ref)
);

-- Populated ONLY at promotion, from the approved staging.reconciliation_result snapshot.
CREATE TABLE canonical.reconciliation_note (
    id          bigserial PRIMARY KEY,
    dataset_id  bigint REFERENCES canonical.dataset(dataset_id),
    comparison  text,
    entity_type text,
    entity_ref  text,
    field       text,
    status      text,
    material    boolean,
    left_label  text,
    right_label text,
    detail      text,
    snapshot_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE canonical.ingest_provenance (
    id              bigserial PRIMARY KEY,
    table_name      text NOT NULL,
    row_pk          bigint,
    dataset_id      bigint REFERENCES canonical.dataset(dataset_id),
    src_file        text,
    src_sheet       text,
    src_row         int,
    adapter         text,
    adapter_version text,
    transform       text,
    ingested_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_claim_dataset      ON canonical.claim (dataset_id);
CREATE INDEX ix_claim_source_ref   ON canonical.claim (dataset_id, source_ref);
CREATE INDEX ix_claim_qa_claim_ref ON canonical.claim_qa (dataset_id, claim_ref);
CREATE INDEX ix_recon_entity       ON canonical.reconciliation_note (dataset_id, entity_ref);

REVOKE ALL ON ALL TABLES IN SCHEMA canonical FROM PUBLIC;
REVOKE ALL ON SCHEMA canonical FROM PUBLIC;
