"""Per-provider checkpoint: last successful cutoff, health counters, rejected-record memory.

Stored beside (not inside) the evidence checkpoint so the v1.1.0 checkpoint schema is untouched.
Atomic write + known-good copy, schema-validated from the trusted main checkout."""

from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema

from . import config
from .errors import SafeStop

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "provider-state.schema.json"
SCHEMA_VERSION = "uc-provider-state-1.0.0"
MAX_REJECTED_KEYS = 4000
MAX_RECENT_HITS = 14
MAX_HISTORY = 60


def empty_state() -> dict:
    return {"schemaVersion": SCHEMA_VERSION, "discoveryStartDate": config.EARLIEST_DISCOVERY_DATE,
            "lastRunDate": None, "lastRunId": None, "providers": {}, "runHistory": []}


def validate(doc: dict) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text("utf-8"))
    v = jsonschema.Draft7Validator(schema)
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
            for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))]


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load(paths: config.StatePaths) -> dict:
    """Primary, else known-good, else (only if neither file exists) an empty first-run state.
    A present-but-invalid pair is a safe stop: silently resetting would re-open a backfill window."""
    primary = _read(paths.provider_state_path)
    if primary is not None and not validate(primary):
        return primary
    known_good = _read(paths.provider_state_known_good_path)
    if known_good is not None and not validate(known_good):
        return known_good
    if primary is None and known_good is None:
        return empty_state()
    raise SafeStop("provider-state.json present but invalid and no valid known-good copy; refusing to reset the cutoff")


def provider(state: dict, name: str) -> dict:
    return state["providers"].setdefault(name, {
        "lastSuccessfulCutoff": None, "lastSuccessfulRunAt": None, "lastStatus": None,
        "consecutiveUnexpectedZero": 0, "consecutiveFailures": 0, "recentHitCounts": [],
        "rejectedKeys": [], "knownListingUrls": []})


def _atomic_write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def save(paths: config.StatePaths, doc: dict) -> None:
    for p in doc["providers"].values():
        p["rejectedKeys"] = p.get("rejectedKeys", [])[-MAX_REJECTED_KEYS:]
        p["recentHitCounts"] = p.get("recentHitCounts", [])[-MAX_RECENT_HITS:]
    doc["runHistory"] = doc.get("runHistory", [])[-MAX_HISTORY:]
    errs = validate(doc)
    if errs:
        raise SafeStop("refusing to write invalid provider-state: " + "; ".join(errs[:4]))
    _atomic_write(paths.provider_state_path, doc)
    reread = _read(paths.provider_state_path)
    if reread is None or validate(reread):
        raise SafeStop("provider-state failed post-write validation; known-good left intact")
    _atomic_write(paths.provider_state_known_good_path, reread)
