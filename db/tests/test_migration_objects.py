"""After `--step migrate`: the schema exists, is empty of evidence, RLS is on.
Marked post_promotion only because it needs a DB connection (it does NOT need promotion;
run it right after migrate)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.post_promotion


EVIDENCE_TABLES = [
    "canonical.source", "canonical.claim", "canonical.claim_citation",
    "canonical.claim_qa", "canonical.excluded_claim",
    "canonical.reconciliation_note", "canonical.ingest_provenance",
]
VIEWS = [
    "v_dataset", "v_source", "v_claim", "v_claim_qa", "v_schema_reconciliation",
    "v_prototype_source", "v_prototype_claim", "v_prototype_excluded_claim_id",
    "v_prototype_limitation", "v_uc_eligible_claim",
]


def test_schemas_present(db_conn):
    names = {r[0] for r in db_conn.execute(
        "SELECT nspname FROM pg_namespace").fetchall()}
    assert {"canonical", "staging", "quarantine"} <= names


def test_all_views_exist(db_conn):
    got = {r[0] for r in db_conn.execute(
        "SELECT table_name FROM information_schema.views WHERE table_schema='canonical'"
    ).fetchall()}
    assert set(VIEWS) <= got


def test_schema_version_seeded(db_conn):
    (v,) = db_conn.execute(
        "SELECT version FROM canonical.schema_version").fetchone()
    assert v == "1.0.0"


def test_enum_seed_present(db_conn):
    (nv,) = db_conn.execute("SELECT count(*) FROM canonical.enum_value").fetchone()
    (nx,) = db_conn.execute("SELECT count(*) FROM canonical.enum_crosswalk").fetchone()
    assert nv >= 40 and nx >= 20


def test_dataset_identity_rows_only(db_conn):
    rows = db_conn.execute(
        "SELECT code, version, status FROM canonical.dataset ORDER BY code").fetchall()
    assert (("baseline-register", "1.0.0") in [(r[0], r[1]) for r in rows])
    assert (("prototype-v1", "1.0.0") in [(r[0], r[1]) for r in rows])


@pytest.mark.parametrize("table", EVIDENCE_TABLES)
def test_evidence_tables_empty_at_migrate_checkpoint(db_conn, table):
    (n,) = db_conn.execute(f"SELECT count(*) FROM {table}").fetchone()
    assert n == 0, f"{table} is not empty - promotion happened"


@pytest.mark.parametrize("table", EVIDENCE_TABLES + ["staging.source_raw", "quarantine.record",
                                                     "canonical.schema_migration"])
def test_rls_forced(db_conn, table):
    schema, name = table.split(".")
    row = db_conn.execute(
        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname = %s", (schema, name)).fetchone()
    assert row == (True, True), f"{table} RLS not forced"


def test_every_base_table_is_rls_forced(db_conn):
    """23/23 -> N/N, whatever N genuinely is: every base table in the three schemas,
    with none named individually here, so a newly added table can't silently slip
    through un-forced the way canonical.schema_migration originally did."""
    rows = db_conn.execute(
        "SELECT n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname IN ('canonical', 'staging', 'quarantine') AND c.relkind = 'r'"
    ).fetchall()
    total = len(rows)
    not_forced = [f"{ns}.{name}" for ns, name, en, fo in rows if not (en and fo)]
    assert total > 0
    assert not_forced == [], (
        f"{len(not_forced)}/{total} base tables NOT RLS-forced: {not_forced}"
    )


def test_no_browser_role_grants_on_any_base_table_or_staging_or_quarantine(db_conn):
    (n,) = db_conn.execute(
        "SELECT count(*) FROM information_schema.role_table_grants "
        "WHERE table_schema IN ('canonical', 'staging', 'quarantine') "
        "AND grantee IN ('anon', 'authenticated')"
    ).fetchone()
    assert n == 0


def test_evidence_reader_has_no_grant_on_schema_migration(db_conn):
    (n,) = db_conn.execute(
        "SELECT count(*) FROM information_schema.role_table_grants "
        "WHERE table_schema = 'canonical' AND table_name = 'schema_migration' "
        "AND grantee = 'evidence_reader'"
    ).fetchone()
    assert n == 0


def test_migration_runner_still_reads_and_writes_the_ledger_after_0006(db_conn):
    """Proof that 0006 did not damage the migration runner: it connects with the same
    credentials as this test fixture and must still be able to read AND write
    canonical.schema_migration (INSERT/DELETE, wrapped in a rollback here)."""
    before = db_conn.execute(
        "SELECT count(*) FROM canonical.schema_migration").fetchone()[0]
    assert before >= 6          # 0001..0006 all recorded as applied
    db_conn.execute(
        "INSERT INTO canonical.schema_migration (filename, sha256) VALUES (%s, %s)",
        ("__rls_probe__", "0" * 64),
    )
    after = db_conn.execute(
        "SELECT count(*) FROM canonical.schema_migration "
        "WHERE filename = '__rls_probe__'").fetchone()[0]
    assert after == 1
    db_conn.execute(
        "DELETE FROM canonical.schema_migration WHERE filename = '__rls_probe__'")
    # db_conn fixture rolls back at teardown regardless; the DELETE above is just
    # extra hygiene in case a future fixture change makes it commit.
