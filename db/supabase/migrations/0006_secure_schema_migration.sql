-- 0006_secure_schema_migration.sql  (Prompt v1.0.0 remediation)
-- Reversible: see 0006_secure_schema_migration.down.sql
--
-- Closes the one gap found by `--step status`: canonical.schema_migration (the
-- migration ledger created by MigrationRunner's bootstrap, before 0001 ever ran) was
-- never brought under the same lockdown as the other 21 base tables in
-- canonical/staging/quarantine (22 total; this migration does not add a 23rd table -
-- schema_migration was always one of the 22).
--
-- Migration-runner impact: NONE. The runner connects as the project's `postgres` role,
-- which owns every object here and carries BYPASSRLS - exactly how it already reads/
-- writes the other 21 RLS-forced tables without a policy. No policy is added for the
-- same reason 0005 added none: the intended reader (evidence_reader, via canonical.v_*)
-- has no business touching this table at all, so a policy is deliberately omitted
-- rather than crafted to `USE (false)` a table nobody but the owner should ever open -
-- ownership + FORCE RLS + no policy is the same pattern already proven safe by every
-- other table below.

REVOKE ALL ON canonical.schema_migration FROM PUBLIC;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON canonical.schema_migration FROM anon, authenticated;
    END IF;
END
$$;

ALTER TABLE canonical.schema_migration ENABLE ROW LEVEL SECURITY;
ALTER TABLE canonical.schema_migration FORCE ROW LEVEL SECURITY;
