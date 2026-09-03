"""The dev-target guard positively identifies development or refuses (no DB needed)."""

from __future__ import annotations

import pytest

from pipeline.config import Settings
from pipeline.db import NoDatabaseError, RefusedProdError, require_dev_target

DEV = "postgresql://u:p@db.devproject123.supabase.co:5432/postgres"


def _s(**kw):
    base = dict(database_url=DEV, db_environment="development",
               prod_host_denylist=("db.prodproject.supabase.co", "production"))
    base.update(kw)
    return Settings(**base)


def test_happy_path_returns_redacted_identifier():
    ident = require_dev_target(_s())
    assert "devproject123" in ident and ":p@" not in ident and "u:" not in ident


def test_refuses_without_database_url():
    with pytest.raises(NoDatabaseError):
        require_dev_target(_s(database_url=None))


def test_refuses_without_explicit_dev_affirmation():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(db_environment=""))
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(db_environment="staging"))


def test_refuses_with_empty_denylist():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(prod_host_denylist=()))


def test_refuses_denylisted_host():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.prodproject.supabase.co:5432/postgres"))


def test_refuses_prod_hint_in_host_or_dbname():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.acme-production.supabase.co:5432/postgres"))
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.acme123.supabase.co:5432/prod"))
