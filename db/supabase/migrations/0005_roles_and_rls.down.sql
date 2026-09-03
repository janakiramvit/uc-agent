-- Reverse of 0005_roles_and_rls.sql.
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
        EXECUTE format('ALTER TABLE %s NO FORCE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %s DISABLE ROW LEVEL SECURITY', t);
    END LOOP;
END
$$;

REVOKE SELECT ON
    canonical.v_dataset, canonical.v_source, canonical.v_claim, canonical.v_claim_qa,
    canonical.v_schema_reconciliation, canonical.v_prototype_source,
    canonical.v_prototype_claim, canonical.v_prototype_excluded_claim_id,
    canonical.v_prototype_limitation, canonical.v_uc_eligible_claim
FROM evidence_reader;
REVOKE USAGE ON SCHEMA canonical FROM evidence_reader;

-- evidence_reader is left in place: dropping a role fails if anything still depends on
-- it. Drop it manually once no login role is GRANTed evidence_reader:
--   DROP ROLE IF EXISTS evidence_reader;
