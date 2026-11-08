"""Exact-duplicate removal only. Near-duplicates and same-ID/different-content records are KEPT."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from phase2 import paths
from phase2.loaders import Record


def _n(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def content_hash(r: Record) -> str:
    """Hash of every field that defines what the claim asserts and where it comes from.

    Dataset, review/evidence status and mapping are deliberately excluded: the same claim held in two
    datasets is an exact duplicate; its differing status is carried in ``also_in``.
    """
    payload = "\x1f".join([
        _n(r.claim_text), _n(r.excerpt), _n(r.source_url), _n(r.locator),
        _n(r.source_id), "|".join(sorted(t.lower() for t in r.uc_applicability)),
    ])
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class DedupeResult:
    kept: list[Record]
    # retained record_id -> list of {"dataset","claim_id"} that were collapsed into it
    merged: dict[str, list[dict]] = field(default_factory=dict)
    before: int = 0
    after: int = 0


def dedupe_exact(records: list[Record]) -> DedupeResult:
    rank = {d: i for i, d in enumerate(paths.DATASET_PRIORITY)}
    ordered = sorted(records, key=lambda r: (rank.get(r.dataset, 99), r.claim_id))
    seen: dict[tuple[str, str], Record] = {}
    merged: dict[str, list[dict]] = {}
    kept: list[Record] = []
    for r in ordered:
        # same content AND same claim id; identical text under a different claim id is a different claim
        key = (r.claim_id, content_hash(r))
        if key in seen:
            keeper = seen[key]
            merged.setdefault(f"{keeper.dataset}:{keeper.claim_id}", []).append(
                {"dataset": r.dataset, "claim_id": r.claim_id})
            keeper.in_production = keeper.in_production or r.in_production
            continue
        seen[key] = r
        kept.append(r)
    return DedupeResult(kept=kept, merged=merged, before=len(records), after=len(kept))
