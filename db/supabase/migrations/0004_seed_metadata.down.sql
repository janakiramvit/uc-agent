-- Reverse of 0004_seed_metadata.sql. Removes ONLY the seeded metadata rows.
DELETE FROM canonical.dataset
 WHERE (code, version) IN (('baseline-register', '1.0.0'), ('prototype-v1', '1.0.0'))
   AND status = 'staged';
DELETE FROM canonical.enum_crosswalk;
DELETE FROM canonical.enum_value;
DELETE FROM canonical.enum_domain;
DELETE FROM canonical.schema_version WHERE version = '1.0.0';
