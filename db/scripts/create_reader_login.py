"""Create (or rotate) the app's LOGIN role: ``evidence_app`` (member of ``evidence_reader``).

``evidence_reader`` is a NOLOGIN group role holding SELECT on the ``canonical.v_*`` views
only. The deployed app needs something it can log in as; this creates ``evidence_app``
with exactly that membership and nothing else (no owner/admin rights, no staging,
quarantine or base-table access, a short statement timeout, a connection cap).

The password is generated here and written ONLY to ``db/.env.reader`` (gitignored,
mode 600) as ``EVIDENCE_SUPABASE_DB_URL``. It is never printed or logged. Run it again
to rotate. Dev target guard applies (same as every other DB step).

    python -m scripts.create_reader_login --i-understand-server-only
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import DB_DIR, load_env  # noqa: E402
from pipeline.db import connect, require_dev_target  # noqa: E402

ROLE = "evidence_app"
OUT = DB_DIR / ".env.reader"


def main(argv: list[str]) -> int:
    if "--i-understand-server-only" not in argv:
        print("refused: pass --i-understand-server-only (creates a DB LOGIN role; its URL is "
              "server-side only, never NEXT_PUBLIC_*).")
        return 2
    s = load_env()
    ident = require_dev_target(s)
    print(f"  dev target confirmed: {ident}")

    password = secrets.token_urlsafe(32)
    conn = connect(s)
    try:
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (ROLE,)).fetchone()
        verb = "ALTER" if exists else "CREATE"
        # password is a generated URL-safe token; role/identifier is a constant.
        conn.execute(
            f"{verb} ROLE {ROLE} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION "
            f"NOBYPASSRLS CONNECTION LIMIT 10 PASSWORD '{password}'"
        )
        if not exists:
            conn.execute(f"GRANT evidence_reader TO {ROLE}")
        conn.execute(f"ALTER ROLE {ROLE} SET statement_timeout = '15s'")
        conn.execute(f"ALTER ROLE {ROLE} SET default_transaction_read_only = on")
        conn.commit()
    finally:
        conn.close()

    # Same host/port/db as the owner URL; only the credentials differ. On the Supabase
    # pooler the username carries the project ref: "<role>.<ref>".
    u = urlsplit(s.database_url)
    owner_user = u.username or ""
    suffix = owner_user.split(".", 1)[1] if "." in owner_user else ""
    user = f"{ROLE}.{suffix}" if suffix else ROLE
    netloc = f"{quote(user, safe='.')}:{quote(password, safe='')}@{u.hostname}"
    if u.port:
        netloc += f":{u.port}"
    dsn = urlunsplit((u.scheme, netloc, u.path, "sslmode=require", ""))
    OUT.write_text(f"EVIDENCE_SUPABASE_DB_URL={dsn}\n")
    os.chmod(OUT, 0o600)
    print(f"  {verb.lower()}d role {ROLE!r} (LOGIN, member of evidence_reader only).")
    print(f"  wrote {OUT.name} (gitignored, mode 600); value not printed.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
