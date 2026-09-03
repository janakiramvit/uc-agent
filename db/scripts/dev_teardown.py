"""DESTRUCTIVE dev-only teardown. NOT the routine rollback path.

Routine rollback = the paired ``NNNN_x.down.sql`` migrations (see db/README.md). Use this
only to wipe a scratch dev database completely.

Guards (all must pass):
  * ``--i-understand-dev-only`` flag present
  * the target database name is retyped at the prompt
  * the DSN host does NOT match any ``PROD_HOST_DENYLIST`` entry
  * ``PROD_HOST_DENYLIST`` is non-empty (refuses to run if you haven't declared prod hosts)

    python -m scripts.dev_teardown --i-understand-dev-only
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import load_env, redact_dsn  # noqa: E402

_DROP = """
DROP SCHEMA IF EXISTS quarantine CASCADE;
DROP SCHEMA IF EXISTS staging CASCADE;
DROP SCHEMA IF EXISTS canonical CASCADE;
DROP ROLE IF EXISTS evidence_reader;
"""


def main(argv: list[str]) -> int:
    if "--i-understand-dev-only" not in argv:
        print("refused: pass --i-understand-dev-only (this DROPs canonical/staging/quarantine).")
        return 2

    s = load_env()
    if not s.database_url:
        print("refused: no DATABASE_URL in db/.env")
        return 2
    if not s.prod_host_denylist:
        print("refused: PROD_HOST_DENYLIST is empty. Declare your prod hosts in db/.env first.")
        return 2

    host = (urlsplit(s.database_url).hostname or "").lower()
    db = (urlsplit(s.database_url).path or "").lstrip("/")
    for needle in s.prod_host_denylist:
        if needle and needle.lower() in host:
            print(f"refused: host {host!r} matches PROD_HOST_DENYLIST entry {needle!r}.")
            return 2

    print(f"About to DROP ALL schemas + evidence_reader on: {redact_dsn(s.database_url)}")
    typed = input(f'Retype the database name ("{db}") to confirm: ').strip()
    if typed != db:
        print("refused: database name mismatch.")
        return 2

    import psycopg

    with psycopg.connect(s.database_url, autocommit=True) as conn:
        conn.execute(_DROP)
    print("done: dev database torn down.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
