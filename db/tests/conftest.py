"""Shared fixtures. Pre-promotion tests need no DB. ``post_promotion`` tests need a dev
``DATABASE_URL`` and are skipped otherwise."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

DB_DIR = Path(__file__).resolve().parent.parent
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))

from pipeline.adapters import (  # noqa: E402
    json_reconcile, prototype_workbook, qa_workbook, register_workbook,
)
from pipeline.config import input_registry, load_env  # noqa: E402
from pipeline.validate import validate_dataset  # noqa: E402


@pytest.fixture(scope="session")
def registry():
    return input_registry()


@pytest.fixture(scope="session")
def adapted(registry):
    return {
        "baseline-register": register_workbook.load(registry["register_workbook"].path),
        "prototype-v1": prototype_workbook.load(registry["prototype_workbook"].path),
        "qa": qa_workbook.load(registry["qa_workbook"].path),
        "refs": json_reconcile.load(
            {k: v.path for k, v in registry.items() if v.role in ("reconcile", "oracle")}
        ),
    }


@pytest.fixture(scope="session")
def validated(adapted):
    return {
        "baseline-register": validate_dataset(
            adapted["baseline-register"].records, dataset="baseline-register",
            input_format="register_workbook"),
        "prototype-v1": validate_dataset(
            adapted["prototype-v1"].records, dataset="prototype-v1",
            input_format="prototype_workbook"),
    }


def _promotion_has_happened(settings) -> bool:
    """True only if canonical.dataset actually has a promoted row. Deliberately
    fail-closed: any error (no DB, migrations not applied yet, wrong creds, ...)
    means "not promoted", not "assume yes". post_promotion tests include
    test_rollback's down-migration drill, which is destructive to an in-progress
    pre-promotion run - being staged/validated/reconciled is NOT "promoted"."""
    if not settings.has_db:
        return False
    try:
        from pipeline.db import connect

        conn = connect(settings)
        try:
            (n,) = conn.execute(
                "SELECT count(*) FROM canonical.dataset WHERE status = 'promoted'"
            ).fetchone()
            return n > 0
        finally:
            conn.rollback()
            conn.close()
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    settings = load_env()
    if _promotion_has_happened(settings):
        return
    skip = pytest.mark.skip(
        reason="post_promotion: no canonical.dataset row has status='promoted' yet "
               "(being staged/validated/reconciled is not 'promoted'); run explicitly "
               "with -m post_promotion only after an approved --step promote."
    )
    for item in items:
        if "post_promotion" in item.keywords:
            item.add_marker(skip)


@pytest.fixture()
def db_conn():
    settings = load_env()
    if not settings.has_db:
        pytest.skip("needs DATABASE_URL")
    from pipeline.db import connect

    conn = connect(settings)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()
