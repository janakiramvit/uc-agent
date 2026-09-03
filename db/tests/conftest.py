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


def pytest_collection_modifyitems(config, items):
    settings = load_env()
    if settings.has_db:
        return
    skip = pytest.mark.skip(reason="post_promotion: needs a dev DATABASE_URL in db/.env")
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
