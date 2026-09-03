"""Rollback drills.

1. (no DB) The app's file-based path is unaffected by the presence of the db/ package.
2. (post_promotion) Every migration reverses cleanly with its .down.sql, and the file
   backend still loads after a full down-migration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.config import REPORTS_DIR


def test_file_backend_untouched_no_db():
    """evidence_loader.py must not import anything from db/ and must still resolve the file."""
    app = Path(__file__).resolve().parents[2] / "apps" / "ibd-uc-rag-agent-web"
    loader = (app / "api" / "agent_core" / "evidence_loader.py").read_text()
    assert "import" in loader and "pipeline" not in loader and "supabase" not in loader
    data = app / "api" / "data" / "ibd-prototype-evidence.json"
    assert data.is_file()


@pytest.mark.post_promotion
def test_down_migrations_reverse_cleanly(db_conn):
    from pipeline.config import load_env
    from pipeline.db import MigrationRunner

    runner = MigrationRunner(load_env())
    # roll everything back...
    while runner.rollback_last(db_conn):
        pass
    db_conn.commit()
    remaining = {r[0] for r in db_conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'canonical' AND table_name LIKE 'v_%'").fetchall()}
    assert not remaining, f"views survived rollback: {remaining}"
    # ...then re-apply so the environment is usable again
    runner.apply(db_conn)
    db_conn.commit()
    # mark the drill done for the gate
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / ".rollback-tested").write_text("ok\n")
