-- Reverse of 0002_staging.sql.
DROP TABLE IF EXISTS quarantine.record;
DROP TABLE IF EXISTS staging.reconciliation_result;
DROP TABLE IF EXISTS staging.reconcile_raw;
DROP TABLE IF EXISTS staging.excluded_raw;
DROP TABLE IF EXISTS staging.claim_qa_raw;
DROP TABLE IF EXISTS staging.claim_raw;
DROP TABLE IF EXISTS staging.source_raw;
DROP TABLE IF EXISTS staging.ingest_batch;
DROP SCHEMA IF EXISTS quarantine;
DROP SCHEMA IF EXISTS staging;
-- pgcrypto left installed (may be used elsewhere).
