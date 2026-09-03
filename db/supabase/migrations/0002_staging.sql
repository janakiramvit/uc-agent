-- 0002_staging.sql  (Prompt v1.0.0)
-- Reversible: see 0002_staging.down.sql
-- Permissive staging + quarantine. All ingest lands here first and is validated here.
-- The application NEVER reads these schemas.

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS quarantine;

CREATE TABLE staging.ingest_batch (
    batch_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at     timestamptz NOT NULL DEFAULT now(),
    prompt_version text,
    note           text
);

-- One permissive shape reused for every staged entity kind.
CREATE TABLE staging.source_raw (
    id                bigserial PRIMARY KEY,
    batch_id          uuid REFERENCES staging.ingest_batch(batch_id),
    dataset_code      text NOT NULL,
    natural_key       text NOT NULL,
    fields            jsonb NOT NULL DEFAULT '{}'::jsonb,
    provenance        jsonb NOT NULL DEFAULT '{}'::jsonb,
    raw               jsonb NOT NULL DEFAULT '{}'::jsonb,
    validation_status text DEFAULT 'pending',   -- pending|valid|valid_with_flags|quarantine
    validation_errors jsonb NOT NULL DEFAULT '[]'::jsonb,
    validation_flags  jsonb NOT NULL DEFAULT '[]'::jsonb,
    canonical         jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (batch_id, dataset_code, natural_key)
);
CREATE TABLE staging.claim_raw     (LIKE staging.source_raw INCLUDING ALL);
CREATE TABLE staging.claim_qa_raw  (LIKE staging.source_raw INCLUDING ALL);
CREATE TABLE staging.excluded_raw  (LIKE staging.source_raw INCLUDING ALL);
CREATE TABLE staging.reconcile_raw (LIKE staging.source_raw INCLUDING ALL);

-- Field-by-field reconciliation output (pre-promotion). Never written to canonical
-- until an approved promotion snapshots it into canonical.reconciliation_note.
CREATE TABLE staging.reconciliation_result (
    id          bigserial PRIMARY KEY,
    batch_id    uuid REFERENCES staging.ingest_batch(batch_id),
    comparison  text NOT NULL,          -- 'A' | 'B' | 'C'
    left_label  text NOT NULL,
    right_label text NOT NULL,
    entity_type text NOT NULL,
    entity_ref  text NOT NULL,
    field       text NOT NULL,
    status      text NOT NULL,          -- match|mismatch|workbook_only|json_only|null_preserved
    material    boolean NOT NULL DEFAULT false,
    left_value  text,
    right_value text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quarantine.record (
    id             bigserial PRIMARY KEY,
    batch_id       uuid REFERENCES staging.ingest_batch(batch_id),
    dataset_code   text,
    entity_type    text,
    natural_key    text,
    raw            jsonb NOT NULL DEFAULT '{}'::jsonb,
    reasons        text[] NOT NULL DEFAULT '{}',
    source_step    text,                -- 'validate' | 'reconcile' | 'promote'
    quarantined_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_recon_result_batch    ON staging.reconciliation_result (batch_id, comparison);
CREATE INDEX ix_recon_result_material ON staging.reconciliation_result (material) WHERE material;
CREATE INDEX ix_quarantine_batch      ON quarantine.record (batch_id);

REVOKE ALL ON ALL TABLES IN SCHEMA staging FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA quarantine FROM PUBLIC;
REVOKE ALL ON SCHEMA staging FROM PUBLIC;
REVOKE ALL ON SCHEMA quarantine FROM PUBLIC;
