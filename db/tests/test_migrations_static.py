"""Static checks on the SQL migrations (no database)."""

from __future__ import annotations

import re

from pipeline.config import MIGRATIONS_DIR
from pipeline.db import discover_migrations


def test_every_migration_is_reversible():
    migs = discover_migrations()
    assert [m.filename for m in migs] == [
        "0001_canonical_schema.sql", "0002_staging.sql", "0003_canonical_views.sql",
        "0004_seed_metadata.sql", "0005_roles_and_rls.sql",
    ]
    for m in migs:
        assert m.down_path is not None and m.down_path.is_file(), \
            f"{m.filename} has no .down.sql"


def test_no_drop_schema_cascade_anywhere():
    for p in MIGRATIONS_DIR.glob("*.sql"):
        assert "drop schema" not in p.read_text().lower() or "cascade" not in p.read_text().lower() \
            or p.name == "never", f"{p.name} uses DROP SCHEMA ... CASCADE"
    # the routine teardown must be reversible migrations, not a schema drop
    for p in MIGRATIONS_DIR.glob("*.sql"):
        assert "CASCADE" not in p.read_text() or "DROP SCHEMA" not in p.read_text().upper()


def test_schemas_are_locked_down_from_public():
    text = "\n".join(p.read_text() for p in MIGRATIONS_DIR.glob("*.sql")
                     if not p.name.endswith(".down.sql"))
    assert "REVOKE ALL ON SCHEMA canonical" in text
    assert "REVOKE ALL ON SCHEMA staging FROM PUBLIC" in text
    assert "REVOKE ALL ON SCHEMA quarantine FROM PUBLIC" in text
    assert "ENABLE ROW LEVEL SECURITY" in text
    assert "CREATE ROLE evidence_reader" in text


def test_balanced_parens_and_terminated_statements():
    for p in MIGRATIONS_DIR.glob("*.sql"):
        body = re.sub(r"--.*", "", p.read_text())
        assert body.count("(") == body.count(")"), f"{p.name}: unbalanced parens"
        assert body.strip().endswith(";"), f"{p.name}: does not end with ';'"


def test_no_source_or_claim_inserts_in_migrations():
    for p in MIGRATIONS_DIR.glob("*.sql"):
        if p.name.endswith(".down.sql"):
            continue
        low = p.read_text().lower()
        assert "insert into canonical.source" not in low
        assert "insert into canonical.claim" not in low
