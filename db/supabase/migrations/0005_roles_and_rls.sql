-- 0005_roles_and_rls.sql  (Prompt v1.0.0)
-- Reversible: see 0005_roles_and_rls.down.sql
--
-- Access model:
--   * evidence_reader  - server-only NOLOGIN group role. Holds SELECT on the approved
--     canonical.v_* views and NOTHING else. The Next.js API connects as a login role
--     that has been GRANTed evidence_reader; the browser never holds a DB URL.
--   * anon / authenticated (Supabase browser roles, if present) - no privileges on
--     canonical / staging / quarantine at all. RLS is enabled on every base table with
--     no policy for them.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'evidence_reader') THEN
        CREATE ROLE evidence_reader NOLOGIN;
    END IF;
END
$$;

-- Lock the schemas down, then hand back only what evidence_reader needs.
REVOKE ALL ON SCHEMA canonical, staging, quarantine FROM PUBLIC;
REVOKE ALL ON ALL TABLES    IN SCHEMA canonical, staging, quarantine FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA canonical, staging, quarantine FROM PUBLIC;

GRANT USAGE ON SCHEMA canonical TO evidence_reader;
GRANT SELECT ON
    canonical.v_dataset,
    canonical.v_source,
    canonical.v_claim,
    canonical.v_claim_qa,
    canonical.v_schema_reconciliation,
    canonical.v_prototype_source,
    canonical.v_prototype_claim,
    canonical.v_prototype_excluded_claim_id,
    canonical.v_prototype_limitation,
    canonical.v_uc_eligible_claim
TO evidence_reader;
-- Explicitly NOT granted: any base table, staging.*, quarantine.*, canonical.claim_qa base.

-- Row-level security ON for every base table; no policy => deny for everyone except
-- the table owner (which the views run as). FORCE so even the owner is filtered when
-- querying base tables directly outside a view.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'canonical.schema_version', 'canonical.enum_domain', 'canonical.enum_value',
        'canonical.enum_crosswalk', 'canonical.dataset', 'canonical.dataset_limitation',
        'canonical.source', 'canonical.claim', 'canonical.claim_citation',
        'canonical.claim_qa', 'canonical.excluded_claim',
        'canonical.reconciliation_note', 'canonical.ingest_provenance',
        'staging.ingest_batch', 'staging.source_raw', 'staging.claim_raw',
        'staging.claim_qa_raw', 'staging.excluded_raw', 'staging.reconcile_raw',
        'staging.reconciliation_result', 'quarantine.record'
    ]
    LOOP
        EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', t);
    END LOOP;
END
$$;

-- If the Supabase browser roles exist, strip every privilege on these schemas.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON SCHEMA canonical, staging, quarantine FROM anon, authenticated;
        REVOKE ALL ON ALL TABLES    IN SCHEMA canonical, staging, quarantine FROM anon, authenticated;
        REVOKE ALL ON ALL SEQUENCES IN SCHEMA canonical, staging, quarantine FROM anon, authenticated;
        REVOKE ALL ON ALL FUNCTIONS IN SCHEMA canonical, staging, quarantine FROM anon, authenticated;
    END IF;
END
$$;
