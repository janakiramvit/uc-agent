"""Hard, code-enforced guard shared by both memory stores.

Neither ``SessionMemory`` nor ``UserPreferenceMemory`` may ever hold:
  - a diagnosis ("you have UC", "you have ulcerative colitis", ...)
  - an inferred disease-activity judgment ("your UC is active/in flare")
  - a predicted flare ("you will flare", "you are about to flare")
  - a treatment/medication recommendation ("you should start/stop/take X")
  - an unsupported medical conclusion / unreviewed evidence treated as
    approved fact ("this is clinically approved", "this is proven to cure")

This module reuses the same style of keyword/pattern denylist as
``app/safety_rules.py`` (pure regex, no LLM) so both the pre-query
safety boundary checks and this storage guard stay conceptually
consistent. It is a genuine guard, not just documentation: every write
path in both memory stores calls ``validate_before_store`` first.
"""

from __future__ import annotations

import re

_DENYLIST_PATTERNS = [
    # Diagnosis / disease-activity judgments
    r"\byou have (uc|ulcerative colitis|ibd|crohn'?s)\b",
    r"\byour (uc|ulcerative colitis) is (active|in flare|flaring|severe|mild|moderate)\b",
    r"\bdiagnos(is|ed|es)\b.*\b(you|patient)\b",
    r"\byou are (having|in) a flare\b",
    r"\bconfirmed (diagnosis|flare)\b",
    # Flare prediction
    r"\byou will (have|get) a flare\b",
    r"\byou will flare\b",
    r"\byou('re| are) (going|about) to flare\b",
    r"\bflare (is|likely) (coming|imminent|predicted)\b",
    # Medication / treatment recommendation
    r"\byou should (start|stop|take|increase|decrease|reduce) .*(medication|drug|biologic|steroid|mesalamine|azathioprine|infliximab|adalimumab|prednisone|dose)\b",
    r"\brecommend(ed|s)? (starting|stopping|taking|increasing|decreasing) .*(medication|dose|drug)\b",
    r"\bprescri(be|bed|ption)\b",
    # Unsupported medical conclusion / unreviewed evidence as approved fact
    r"\bclinically approved\b",
    r"\bproven to (cure|treat|fix)\b",
    r"\bguarantee(d|s)? to (cure|treat|work)\b",
    r"\bthis (cures|treats|fixes) (your|the) (uc|ulcerative colitis)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DENYLIST_PATTERNS]


class ClinicalContentRejected(ValueError):
    """Raised when a value being stored in memory matches a blocked
    clinical-content category (diagnosis, flare prediction, medication
    change, or unsupported medical conclusion treated as fact)."""


def contains_blocked_content(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _COMPILED)


def validate_before_store(value):
    """Recursively validate a value (str, dict, list, or scalar) before it
    is stored in either memory store. Raises ``ClinicalContentRejected``
    if any string within it matches a blocked category. Returns the value
    unchanged when it passes (by construction, this function never
    "cleans" text into something different -- it either accepts memory
    content verbatim or rejects the whole write, so nothing blocked can
    silently be stored in a mangled form).
    """
    if isinstance(value, str):
        if contains_blocked_content(value):
            raise ClinicalContentRejected(
                f"Refused to store value containing blocked clinical content: {value!r}"
            )
        return value
    if isinstance(value, dict):
        for k, v in value.items():
            validate_before_store(k)
            validate_before_store(v)
        return value
    if isinstance(value, (list, tuple, set)):
        for item in value:
            validate_before_store(item)
        return value
    return value
