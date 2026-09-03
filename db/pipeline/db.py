"""Database I/O: connection guard + reversible-migration runner.

Nothing here runs without ``DATABASE_URL`` in ``db/.env``. The connection is refused
outright if the DSN host matches ``PROD_HOST_DENYLIST`` - migrations and staging are for
a **dev** Supabase project only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pipeline.config import MIGRATIONS_DIR, Settings, redact_dsn


class RefusedProdError(RuntimeError):
    """The target could not be positively identified as development - connection refused."""


class NoDatabaseError(RuntimeError):
    """No DATABASE_URL configured."""


_PROD_HINTS = ("prod", "production", "live")


def _host_of(dsn: str) -> str:
    from urllib.parse import urlsplit

    return (urlsplit(dsn).hostname or "").lower()


def _dbname_of(dsn: str) -> str:
    from urllib.parse import urlsplit

    return (urlsplit(dsn).path or "").lstrip("/").lower()


def require_dev_target(settings: Settings) -> str:
    """Positively identify the target as development, or raise.

    Requires ALL of:
      * DATABASE_URL present;
      * DB_ENVIRONMENT explicitly = 'development' (or 'dev') in db/.env - a deliberate
        operator affirmation, not an inference;
      * PROD_HOST_DENYLIST non-empty (you must have declared what prod looks like);
      * the DSN host is not in PROD_HOST_DENYLIST;
      * neither host nor db name contains an obvious prod hint (prod/production/live).
    Returns a redacted identifier for logging.
    """
    if not settings.database_url:
        raise NoDatabaseError(
            "DATABASE_URL is not set. Put a DEV Supabase connection string in db/.env."
        )
    if not settings.is_declared_development:
        raise RefusedProdError(
            "DB_ENVIRONMENT is not 'development' in db/.env. Refusing to connect: the "
            "target cannot be positively identified as a development project."
        )
    if not settings.prod_host_denylist:
        raise RefusedProdError(
            "PROD_HOST_DENYLIST is empty in db/.env. Declare your production host(s) "
            "first so this tool can refuse them."
        )
    host, dbname = _host_of(settings.database_url), _dbname_of(settings.database_url)
    for needle in settings.prod_host_denylist:
        if needle and needle.lower() in host:
            raise RefusedProdError(
                f"DSN host matches PROD_HOST_DENYLIST entry {needle!r}; refusing."
            )
    for hint in _PROD_HINTS:
        if hint in host or hint in dbname:
            raise RefusedProdError(
                f"DSN host/db name contains {hint!r}; refusing (looks like production)."
            )
    return redact_dsn(settings.database_url)


# Back-compat alias.
guard_dsn = require_dev_target


def connect(settings: Settings):
    """Return a psycopg connection (caller manages the transaction). Dev-target-gated."""
    ident = require_dev_target(settings)
    import psycopg

    conn = psycopg.connect(settings.database_url, autocommit=False)
    print(f"  connected (dev target confirmed): {ident}")
    return conn


# --------------------------------------------------------------------------- migrations


@dataclass
class Migration:
    filename: str
    path: Path
    sql: str
    down_path: Path | None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.sql.encode()).hexdigest()


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    out: list[Migration] = []
    for p in sorted(directory.glob("*.sql")):
        if p.name.endswith(".down.sql"):
            continue
        down = p.with_name(p.name[:-4] + ".down.sql")
        out.append(Migration(p.name, p, p.read_text(), down if down.is_file() else None))
    return out


_TRACK_TABLE = """
CREATE SCHEMA IF NOT EXISTS canonical;
CREATE TABLE IF NOT EXISTS canonical.schema_migration (
    filename    text PRIMARY KEY,
    sha256      text NOT NULL,
    applied_at  timestamptz NOT NULL DEFAULT now()
);
"""


class MigrationRunner:
    def __init__(self, settings: Settings, directory: Path = MIGRATIONS_DIR):
        self.settings = settings
        self.directory = directory
        self.migrations = discover_migrations(directory)

    def _applied(self, conn) -> dict[str, str]:
        conn.execute(_TRACK_TABLE)
        rows = conn.execute(
            "SELECT filename, sha256 FROM canonical.schema_migration"
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def status(self, conn) -> list[tuple[str, str]]:
        applied = self._applied(conn)
        out = []
        for m in self.migrations:
            if m.filename not in applied:
                out.append((m.filename, "pending"))
            elif applied[m.filename] != m.sha256:
                out.append((m.filename, "DRIFT (checksum changed after apply)"))
            else:
                out.append((m.filename, "applied"))
        return out

    def apply(self, conn) -> list[str]:
        applied = self._applied(conn)
        done: list[str] = []
        for m in self.migrations:
            if m.filename in applied:
                if applied[m.filename] != m.sha256:
                    raise RuntimeError(
                        f"{m.filename} already applied but its checksum changed; "
                        "author a new migration instead of editing this one."
                    )
                continue
            with conn.transaction():
                conn.execute(m.sql)
                conn.execute(
                    "INSERT INTO canonical.schema_migration(filename, sha256) VALUES (%s, %s)",
                    (m.filename, m.sha256),
                )
            print(f"  applied {m.filename}")
            done.append(m.filename)
        return done

    def rollback_last(self, conn) -> str | None:
        applied = self._applied(conn)
        for m in reversed(self.migrations):
            if m.filename in applied:
                if not m.down_path:
                    raise RuntimeError(f"{m.filename} has no .down.sql; cannot auto-rollback")
                with conn.transaction():
                    conn.execute(m.down_path.read_text())
                    conn.execute(
                        "DELETE FROM canonical.schema_migration WHERE filename = %s",
                        (m.filename,),
                    )
                print(f"  rolled back {m.filename}")
                return m.filename
        return None
