-- Reverse of 0006_secure_schema_migration.sql.
ALTER TABLE canonical.schema_migration NO FORCE ROW LEVEL SECURITY;
ALTER TABLE canonical.schema_migration DISABLE ROW LEVEL SECURITY;
-- REVOKE is not un-done: Postgres tables carry no PUBLIC/anon/authenticated privileges
-- by default, so there is nothing to re-grant to restore the pre-migration state.
