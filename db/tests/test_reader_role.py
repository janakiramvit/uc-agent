"""The app's LOGIN role (evidence_app) can read ONLY the approved views.

Needs the role's URL in ``db/.env.reader`` (created by scripts/create_reader_login.py);
skipped when absent. Runs after promotion. Read-only: only SELECTs and expected failures.
"""

from __future__ import annotations

import pytest

from pipeline.config import DB_DIR

pytestmark = pytest.mark.post_promotion


def _reader_dsn() -> str | None:
    f = DB_DIR / ".env.reader"
    if not f.is_file():
        return None
    for line in f.read_text().splitlines():
        if line.startswith("EVIDENCE_SUPABASE_DB_URL="):
            return line.split("=", 1)[1].strip()
    return None


@pytest.fixture()
def reader():
    dsn = _reader_dsn()
    if not dsn:
        pytest.skip("db/.env.reader not present (run scripts/create_reader_login.py)")
    import psycopg

    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=15)
    yield conn
    conn.close()


def test_reader_is_not_privileged(reader):
    sup, bypass, createrole = reader.execute(
        "SELECT rolsuper, rolbypassrls, rolcreaterole FROM pg_roles WHERE rolname=current_user"
    ).fetchone()
    assert (sup, bypass, createrole) == (False, False, False)


def test_reader_reads_the_approved_views(reader):
    (n,) = reader.execute("SELECT count(*) FROM canonical.v_prototype_claim").fetchone()
    assert n == 49
    (s,) = reader.execute("SELECT count(*) FROM canonical.v_prototype_source").fetchone()
    assert s == 20


@pytest.mark.parametrize("obj", [
    "staging.claim_raw", "staging.source_raw", "staging.reconciliation_result",
    "quarantine.record", "canonical.claim", "canonical.source", "canonical.claim_qa",
    "canonical.reconciliation_note", "canonical.schema_migration", "canonical.dataset",
])
def test_reader_cannot_select_base_staging_or_quarantine(reader, obj):
    import psycopg

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        reader.execute(f"SELECT 1 FROM {obj} LIMIT 1")


def test_reader_cannot_write(reader):
    import psycopg

    for stmt in ("DELETE FROM canonical.claim", "UPDATE canonical.source SET title='x'",
                 "INSERT INTO canonical.excluded_claim (dataset_id, claim_ref) VALUES (1,'X')",
                 "DELETE FROM canonical.v_prototype_claim"):
        with pytest.raises((psycopg.errors.InsufficientPrivilege,
                            psycopg.errors.ReadOnlySqlTransaction,
                            psycopg.errors.ObjectNotInPrerequisiteState)):
            reader.execute(stmt)
