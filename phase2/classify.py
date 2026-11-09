"""Deterministic validation-status classification. No inference, no research.

Every record gets exactly one status, from this precedence (most restrictive first):

    crohns_only   applicability is Crohn's disease only - never usable for UC
    unverifiable  cannot be traced to a resolvable source / URL / excerpt / locator,
                  or the dataset itself marks verification as failed/absent
    conflicting   the same claim ID disagrees across datasets (applicability or text), or the
                  record itself declares a conflict
    incomplete    traceable, but a required field or an evidence status is missing/unresolved
    usable        complete, traceable, UC- or IBD-applicable, no conflict

All reasons are kept in ``status_reasons`` even when a higher-precedence status wins.
"""

from __future__ import annotations

import re
from collections import defaultdict

from phase2.loaders import Record

STATUSES = ("usable", "incomplete", "conflicting", "crohns_only", "unverifiable")

_UC = "ulcerative_colitis"
_CROHNS = "crohns_disease"
_UNVERIFIED_RE = re.compile(r"(unverif|not_verified|cannot_verify|failed|unable)", re.I)
_UNRESOLVED_STATUS_RE = re.compile(r"(still_needs_evidence|unresolved|needs_evidence|missing)", re.I)
_DECLARED_CONFLICT_RE = re.compile(r"^\s*(conflicts?\b|contradict|inconsisten|not consistent|disagree)", re.I)


def applicability_class(tokens: list[str]) -> str:
    """uc_specific | ibd_general | crohns_only | unspecified (mirrors production's substring rule)."""
    toks = {t.lower() for t in tokens}
    if not toks:
        return "unspecified"
    if _UC in toks:
        return "uc_specific"
    if toks == {_CROHNS}:
        return "crohns_only"
    if toks <= {_CROHNS, "ibd_general"} and "ibd_general" in toks:
        return "ibd_general"
    return "ibd_general" if "ibd_general" in toks else "unspecified"


def _norm_text(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def find_conflicts(records: list[Record]) -> dict[str, list[str]]:
    """record_id -> reasons, for claim IDs whose records disagree materially across datasets."""
    by_id: dict[str, list[Record]] = defaultdict(list)
    for r in records:
        by_id[r.claim_id].append(r)
    out: dict[str, list[str]] = {}
    for cid, recs in by_id.items():
        if len(recs) < 2:
            continue
        # A missing value is an incompleteness (flagged separately), not a disagreement.
        app = {frozenset(t.lower() for t in r.uc_applicability) for r in recs if r.uc_applicability}
        txt = {_norm_text(r.claim_text) for r in recs if r.claim_text}
        reasons = []
        if len(app) > 1:
            reasons.append("applicability differs across datasets: " + " | ".join(
                f"{r.dataset}={sorted(r.uc_applicability)}" for r in recs if r.uc_applicability))
        if len(txt) > 1:
            reasons.append("claim text differs across datasets: " + ", ".join(sorted({r.dataset for r in recs})))
        if reasons:
            for r in recs:
                out.setdefault(f"{r.dataset}:{r.claim_id}", []).extend(reasons)
    return out


def classify(record: Record, conflicts: dict[str, list[str]]) -> tuple[str, list[str]]:
    rid = f"{record.dataset}:{record.claim_id}"
    app = applicability_class(record.uc_applicability)

    unverifiable, conflicting, incomplete = [], list(conflicts.get(rid, [])), []

    if not record.source_id or not record.source_resolved:
        unverifiable.append("source does not resolve to a source record")
    if not record.source_url:
        unverifiable.append("no authoritative source URL")
    if not record.excerpt:
        unverifiable.append("no supporting excerpt")
    if not record.locator:
        unverifiable.append("no locator")
    if record.verification_status and _UNVERIFIED_RE.search(record.verification_status):
        unverifiable.append(f"dataset verification status: {record.verification_status}")

    if record.declared_conflict_note and _DECLARED_CONFLICT_RE.search(record.declared_conflict_note):
        conflicting.append("record declares a conflict: " + record.declared_conflict_note[:120])

    if not record.claim_text:
        incomplete.append("no claim text")
    if app == "unspecified":
        incomplete.append("UC applicability missing or unrecognised")
    if record.evidence_status and _UNRESOLVED_STATUS_RE.search(record.evidence_status):
        incomplete.append(f"evidence status unresolved: {record.evidence_status}")
    if not record.publication_date:
        incomplete.append("publication date missing")

    reasons = ([f"crohns_only: applicability is Crohn's disease only"] if app == "crohns_only" else []) \
        + [f"unverifiable: {x}" for x in unverifiable] \
        + [f"conflicting: {x}" for x in conflicting] \
        + [f"incomplete: {x}" for x in incomplete]

    if app == "crohns_only":
        status = "crohns_only"
    elif unverifiable:
        status = "unverifiable"
    elif conflicting:
        status = "conflicting"
    elif incomplete:
        status = "incomplete"
    else:
        status = "usable"
    return status, reasons


_CD_TEXT_RE = re.compile(r"\b(crohn'?s?|CD)\b", re.I)
_UC_TEXT_RE = re.compile(r"\b(ulcerative colitis|UC)\b", re.I)


def review_flags(record: Record) -> list[str]:
    """Advisory flags for the owner. They never change the status - they point at things a reviewer should
    look at before relying on a claim."""
    flags = []
    text = record.claim_text or ""
    if applicability_class(record.uc_applicability) == "uc_specific" and _CD_TEXT_RE.search(text) \
            and not _UC_TEXT_RE.search(text):
        flags.append("applicability lists ulcerative colitis, but the claim text itself refers only to Crohn's disease "
                     "(the applicability may come from the whole source, not this finding)")
    return flags
