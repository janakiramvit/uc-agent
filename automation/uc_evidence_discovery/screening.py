"""Deterministic screening: relevance, UC-applicability labelling, disposition.

Hard rules (never violated, and asserted by tests):

* a Crohn's-only or IBD-general record is *never* relabelled ``ulcerative_colitis``;
* every disposition carries a non-empty ``reason``;
* ``accepted`` / ``deferred`` / ``rejected`` / ``duplicate`` are mutually exclusive;
* anything the deterministic rules cannot resolve is flagged ``requires_human_review`` — the
  runner never invents a clinical judgement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import config
from .dedup import CandidateKey, ProcessedIndex

APPLICABILITY_VALUES = ("ulcerative_colitis", "ibd_general", "crohns_only", "unknown")
DISPOSITIONS = ("accepted", "deferred", "rejected", "duplicate")


def applicability_label(record: dict) -> str:
    text = f"{record.get('title','')} {record.get('abstractText','') or record.get('abstract','')}".lower()
    conds = " ".join(record.get("conditions", []) or []).lower()
    text = f"{text} {conds}"
    has_uc = "ulcerative colitis" in text or "ulcerative-colitis" in text
    has_cd = "crohn" in text
    if has_uc and not has_cd:
        return "ulcerative_colitis"
    if has_cd and not has_uc:
        return "crohns_only"
    if has_uc and has_cd:
        return "ibd_general"
    if "inflammatory bowel disease" in text or " ibd " in f" {text} ":
        return "ibd_general"
    return "unknown"


def relevance(record: dict, extra_keywords: tuple[str, ...] = ()) -> tuple[bool, list[str]]:
    text = f"{record.get('title','')} {record.get('abstractText','') or record.get('abstract','')}".lower()
    kws = tuple(config.RESEARCH_PRIORITY_KEYWORDS) + tuple(extra_keywords)
    matched = [k for k in kws if k in text]
    return (bool(matched), matched)


def _has_min_metadata(record: dict) -> bool:
    has_title = bool((record.get("title") or "").strip())
    has_id = any(
        record.get(k) for k in ("doi", "pmid", "pubmedId", "pmcid", "nctId", "trialId")
    )
    has_venue = bool((record.get("journal") or record.get("publishingOrganisation") or "").strip())
    return has_title and has_id and has_venue


@dataclass
class Disposition:
    status: str                     # one of DISPOSITIONS
    reason: str
    applicability: str = "unknown"
    requires_human_review: bool = False
    topic_id: Optional[str] = None
    matched_keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        assert self.status in DISPOSITIONS, self.status
        assert self.reason, "every disposition needs a reason"
        assert self.applicability in APPLICABILITY_VALUES, self.applicability


def screen(
    record: dict,
    *,
    index: ProcessedIndex,
    topic_id: str,
    topic_keywords: tuple[str, ...] = (),
) -> Disposition:
    key = CandidateKey.from_record(record)

    dup = index.duplicate_reason(key)
    if dup:
        return Disposition("duplicate", dup, applicability_label(record), topic_id=topic_id)

    label = applicability_label(record)

    is_rel, matched = relevance(record, topic_keywords)
    if not is_rel:
        return Disposition("rejected", "not_relevant:no_priority_topic_keyword_match", label, topic_id=topic_id)

    if label == "crohns_only":
        return Disposition(
            "rejected", "out_of_scope:crohns_only_not_uc", label, topic_id=topic_id,
            matched_keywords=tuple(matched),
        )

    if not _has_min_metadata(record):
        return Disposition(
            "deferred", "missing_required_metadata:need_title+id+venue", label,
            requires_human_review=True, topic_id=topic_id, matched_keywords=tuple(matched),
        )

    abstract = (record.get("abstractText") or record.get("abstract") or "").strip()
    if len(abstract) < 120:
        return Disposition(
            "deferred", "no_usable_abstract:full_text_not_retrieved_within_limits", label,
            requires_human_review=True, topic_id=topic_id, matched_keywords=tuple(matched),
        )

    rhr = label in ("unknown", "ibd_general")
    reason = "passes_relevance_provenance_and_min_metadata"
    if label == "ibd_general":
        reason += ";ibd_general_label_retained_not_upgraded_to_uc"
    return Disposition(
        "accepted", reason, label, requires_human_review=rhr, topic_id=topic_id,
        matched_keywords=tuple(matched),
    )
