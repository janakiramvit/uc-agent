"""Checkpoint load / validate / atomic-save with known-good recovery.

* The JSON *schema* is always read from the trusted ``main`` checkout
  (:data:`config.SCHEMA_V1_1_0`), never from ``--state-root``.
* On a primary-checkpoint failure the runner falls back to
  ``<state-root>/state/checkpoint.json.known-good`` (the single, real filename).
* If both are invalid the runner raises :class:`SafeStop` and does no research.
* Prompt-supplied resume hints never override a newer checkpoint; a difference is recorded.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import jsonschema

from . import config
from .errors import SafeStop


def _load_schema(path: Path = config.SCHEMA_V1_1_0) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(doc: dict, *, schema_path: Path = config.SCHEMA_V1_1_0) -> list[str]:
    """Return a list of human-readable validation errors (empty ⇒ valid)."""
    schema = _load_schema(schema_path)
    validator = jsonschema.Draft7Validator(schema)
    return [
        f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    ]


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


@dataclass
class LoadResult:
    doc: dict
    source: str                       # "primary" | "known_good"
    recovered: bool
    prompt_difference: Optional[dict]  # None if the checkpoint matches PROMPT_EXPECTATIONS


def load(paths: config.StatePaths) -> LoadResult:
    primary = _read_json(paths.checkpoint_path)
    if primary is not None and not validate(primary):
        return LoadResult(primary, "primary", False, _diff_against_prompt(primary))

    known_good = _read_json(paths.known_good_path)
    if known_good is not None and not validate(known_good):
        return LoadResult(known_good, "known_good", True, _diff_against_prompt(known_good))

    reasons = []
    reasons.append("primary missing/invalid" if primary is None else "primary fails schema")
    reasons.append(
        "known-good missing/invalid" if known_good is None else "known-good fails schema"
    )
    raise SafeStop("cannot start research: " + "; ".join(reasons))


def _diff_against_prompt(doc: dict) -> Optional[dict]:
    nro = doc.get("nextRecommendedOperation", {}) or {}
    exp = config.PROMPT_EXPECTATIONS
    got = {
        "topicId": nro.get("topicId"),
        "searchId": nro.get("searchId"),
        "cursor": nro.get("cursor"),
        "firstNewSourceId": nro.get("firstNewSourceId"),
        "firstNewClaimId": nro.get("firstNewClaimId"),
    }
    if all(got.get(k) == exp.get(k) for k in exp):
        return None
    return {"promptExpected": exp, "checkpointHas": got,
            "resolution": "checkpoint is authoritative; prompt hints ignored"}


# --------------------------------------------------------------------------------------------
# save
# --------------------------------------------------------------------------------------------
def _atomic_write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def save(paths: config.StatePaths, doc: dict) -> None:
    """Validate → atomically write the primary checkpoint → re-read & re-validate → only then
    update the known-good copy. Raises if the document does not validate (nothing written)."""
    errors = validate(doc)
    if errors:
        raise SafeStop("refusing to write an invalid checkpoint: " + "; ".join(errors[:5]))
    _atomic_write_json(paths.checkpoint_path, doc)

    reread = _read_json(paths.checkpoint_path)
    if reread is None or validate(reread):
        raise SafeStop("primary checkpoint failed post-write validation; known-good left intact")
    _atomic_write_json(paths.known_good_path, reread)


def upgrade_schema_version(doc: dict) -> dict:
    """Non-destructively move a v1.0.0 document onto the v1.1.0 version string."""
    if doc.get("schemaVersion") != config.SCHEMA_VERSION_1_1_0:
        doc.setdefault("schemaMigratedFrom", doc.get("schemaVersion", "unknown"))
        doc["schemaVersion"] = config.SCHEMA_VERSION_1_1_0
    return doc


def new_run_id() -> str:
    import secrets

    return "uc-exp-" + secrets.token_hex(6)
