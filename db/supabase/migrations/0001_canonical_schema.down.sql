-- Reverse of 0001_canonical_schema.sql. Drops canonical evidence objects only.
-- Safe because 0001 never inserts evidence rows. Ordered for FK dependencies.
DROP TABLE IF EXISTS canonical.ingest_provenance;
DROP TABLE IF EXISTS canonical.reconciliation_note;
DROP TABLE IF EXISTS canonical.excluded_claim;
DROP TABLE IF EXISTS canonical.claim_qa;
DROP TABLE IF EXISTS canonical.claim_citation;
DROP TABLE IF EXISTS canonical.claim;
DROP TABLE IF EXISTS canonical.source;
DROP TABLE IF EXISTS canonical.dataset_limitation;
DROP TABLE IF EXISTS canonical.dataset;
DROP TABLE IF EXISTS canonical.enum_crosswalk;
DROP TABLE IF EXISTS canonical.enum_value;
DROP TABLE IF EXISTS canonical.enum_domain;
DROP TABLE IF EXISTS canonical.schema_version;
-- canonical.schema_migration and the canonical schema itself are left in place
-- (the runner manages the ledger; the schema may be shared with the runner bootstrap).
