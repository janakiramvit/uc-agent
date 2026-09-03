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
    """The DSN host looks like production - connection refused."""


class NoDatabaseError(RuntimeError):
    """No DATABASE_URL configured."""


def _host_of(dsn: str) -> str:
    from urllib.parse import urlsplit

    return (urlsplit(dsn).hostname or "").lower()


def guard_dsn(settings: Settings) -> None:
    if not settings.database_url:
        raise NoDatabaseError(
            "DATABASE_URL is not set. Put a DEV Supabase connection string in db/.env."
        )
    host = _host_of(settings.database_url)
    for needle in settings.prod_host_denylist:
        if needle and needle.lower() in host:
            raise RefusedProdError(
                f"DSN host {host!r} matches PROD_HOST_DENYLIST entry {needle!r}; refusing."
            )


def connect(settings: Settings):
    """Return a psycopg connection (caller manages the transaction)."""
    guard_dsn(settings)
    import psycopg

    conn = psycopg.connect(settings.database_url, autocommit=False)
    print(f"  connected: {redact_dsn(settings.database_url)}")
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
