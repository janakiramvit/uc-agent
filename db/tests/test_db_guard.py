"""The dev-target guard positively identifies development or refuses (no DB needed)."""

from __future__ import annotations

import pytest

from pipeline.config import Settings
from pipeline.db import NoDatabaseError, RefusedProdError, require_dev_target

DEV = "postgresql://u:p@db.devproject123.supabase.co:5432/postgres"
DEV_HOST = "db.devproject123.supabase.co"


def _s(**kw):
    base = dict(database_url=DEV, db_environment="development",
               expected_dev_host=DEV_HOST,
               prod_host_denylist=("db.prodproject.supabase.co", "production"))
    base.update(kw)
    return Settings(**base)


def test_happy_path_returns_identifier_with_no_host_user_or_password():
    ident = require_dev_target(_s())
    for leak in ("devproject123", "db.devproject123.supabase.co", ":p@", "u:", "postgresql://u"):
        assert leak not in ident, f"{leak!r} leaked into {ident!r}"
    assert "host-fingerprint:" in ident      # a one-way fingerprint, not the host itself


def test_no_call_path_ever_prints_the_full_dsn_url_or_password():
    """Belt-and-suspenders: nothing returned or raised contains the raw DSN pieces."""
    secrets = ("u:p@", "postgresql://u:p", "db.devproject123.supabase.co")
    ident = require_dev_target(_s())
    assert not any(s in ident for s in secrets)
    for bad_kwargs in (dict(db_environment=""), dict(expected_dev_host=""),
                      dict(expected_dev_host="db.someotherproject.supabase.co"),
                      dict(database_url="postgresql://u:p@db.prodproject.supabase.co:5432/postgres",
                           expected_dev_host="db.prodproject.supabase.co")):
        try:
            require_dev_target(_s(**bad_kwargs))
        except RefusedProdError as exc:
            assert not any(s in str(exc) for s in secrets)


def test_refuses_without_database_url():
    with pytest.raises(NoDatabaseError):
        require_dev_target(_s(database_url=None))


def test_refuses_without_explicit_dev_affirmation():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(db_environment=""))
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(db_environment="staging"))


def test_allows_empty_denylist_when_no_real_prod_host_declared():
    # PROD_HOST_DENYLIST is optional: do not force a placeholder when no real
    # production database exists yet. Positive identification still comes from
    # DB_ENVIRONMENT + EXPECTED_DEV_HOST + the prod-hint substring check.
    ident = require_dev_target(_s(prod_host_denylist=()))
    assert ident.startswith("postgres://<redacted>@<host-fingerprint:")


def test_refuses_without_expected_dev_host():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(expected_dev_host=""))


def test_refuses_on_expected_dev_host_mismatch():
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(expected_dev_host="db.someotherproject.supabase.co"))


def test_refuses_denylisted_host_even_if_it_matches_expected_dev_host():
    # A denylist entry is a hard stop even if EXPECTED_DEV_HOST was (mis)configured
    # to match it - denylist wins.
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.prodproject.supabase.co:5432/postgres",
            expected_dev_host="db.prodproject.supabase.co"))


def test_refuses_prod_hint_in_host_or_dbname():
    # even when EXPECTED_DEV_HOST is (mis)configured to match, an obvious prod hint
    # in the host or db name is still a hard refusal.
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.acme-production.supabase.co:5432/postgres",
            expected_dev_host="db.acme-production.supabase.co"))
    with pytest.raises(RefusedProdError):
        require_dev_target(_s(
            database_url="postgresql://u:p@db.acme123.supabase.co:5432/prod",
            expected_dev_host="db.acme123.supabase.co"))
