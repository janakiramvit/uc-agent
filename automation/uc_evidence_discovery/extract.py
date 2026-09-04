"""Mechanical candidate-excerpt extraction.

Every candidate is a *verbatim substring* of the retrieved abstract — no paraphrase, no
inference, no association→causation, no population broadening. Each carries an exact locator,
the abstract-only vs full-text verification basis, applicability + limitations, stays
``pending_clinical_review`` with all human-approval fields blank, and is explicitly marked as
mechanically extracted.
"""

from __future__ import annotations

import datetime as _dt
import re
from typing import Optional

from . import config

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")
_UC_TERMS = ("ulcerative colitis", "uc ", " uc.", " uc,", "inflammatory bowel disease", "ibd")


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    return [s.strip() for s in _SENT_SPLIT.split(text) if len(s.strip()) >= 40]


def _locator(source_record: dict) -> str:
    ext = source_record.get("raw_ext_id") or source_record.get("pmid") or "n/a"
    journal = source_record.get("journal") or "source"
    year = source_record.get("pubYear") or ""
    return (
        f"Abstract (retrieved), Results/Conclusions — Europe PMC record EXT_ID:{ext}; "
        f"{journal} {year}. Statement/page-level locators require full text (link_only)."
    )


def extract_candidates(
    source_record: dict,
    *,
    source_id: str,
    applicability: str,
    topic_id: str,
    mapped_question_ids: list[str],
    allocate_claim_id,
    remaining_global: int,
    topic_keywords: tuple[str, ...] = (),
    max_per_source: int = 4,
) -> list[dict]:
    abstract = (source_record.get("abstractText") or source_record.get("abstract") or "").strip()
    if not abstract or remaining_global <= 0:
        return []

    kws = tuple(k.lower() for k in (tuple(config.RESEARCH_PRIORITY_KEYWORDS) + tuple(topic_keywords)))
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[dict] = []
    for sentence in _sentences(abstract):
        if len(out) >= max_per_source or len(out) >= remaining_global:
            break
        low = sentence.lower()
        if not any(k in low for k in kws):
            continue
        if not any(t in low for t in _UC_TERMS) and applicability != "ulcerative_colitis":
            # only keep an IBD-general sentence if it is clearly on-topic
            continue
        if sentence not in abstract:            # defensive: must be verbatim
            continue
        out.append(
            {
                "claimId": allocate_claim_id(),
                "sourceId": source_id,
                "normalizedClaim": sentence,
                "exactSupportingExcerpt": sentence,
                "exactLocator": _locator(source_record),
                "verificationBasis": "abstract_only",
                "conditionApplicability": applicability,   # never upgraded downstream
                "diseaseContext": [topic_id],
                "evidenceStrength": "not_stated_by_source",
                "extractionMethod": "mechanical_verbatim_sentence_selection",
                "isMechanicallyExtractedCandidate": True,
                "mappedPatientQuestionIds": list(mapped_question_ids),
                "limitations": (
                    "Mechanically selected from the retrieved abstract; not full-text verified; "
                    "evidence strength not asserted by this runner; applicability label is "
                    f"'{applicability}' and was not broadened."
                ),
                "conflictsWithExistingEvidence": "requires_human_review",
                "regionalApplicabilityNote": "requires_human_review (Canada/US applicability not assessed mechanically)",
                "extractedAt": now,
                "lifecycleState": "extracted",
                "reviewStatus": "pending_clinical_review",
                "humanReviewStatus": "",
                "clinicalReviewStatus": "",
                "reviewerDecision": "",
                "reviewerNotes": "",
                "reviewDate": "",
            }
        )
    return out


def verify_verbatim(claim: dict, abstract_text: str) -> Optional[str]:
    """Return an error string if the excerpt is not a verbatim substring, else ``None``."""
    excerpt = claim.get("exactSupportingExcerpt", "")
    if not excerpt:
        return "empty excerpt"
    if excerpt not in re.sub(r"\s+", " ", abstract_text.strip()):
        return "excerpt is not a verbatim substring of the retrieved abstract"
    return None
