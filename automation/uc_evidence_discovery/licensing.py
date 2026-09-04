"""Licensing / access gate.

A full-text file (PDF / XML) is archived only when it is legitimately public **and** its
licence explicitly permits the intended storage **and** licence + retrieval URL + checksum +
retrieval timestamp are all recorded. Accessibility is never treated as redistribution
permission. This deterministic daily runner does not download full text at all, so archival
count is structurally 0 — but the gate is implemented and tested so a future change cannot
silently archive.
"""

from __future__ import annotations

from dataclasses import dataclass

# Licences whose plain terms permit local archival + redistribution of the article file.
_OPEN_LICENCES = (
    "cc0", "cc-0", "public domain", "publicdomain",
    "cc by", "cc-by", "ccby", "creativecommons.org/licenses/by",
    "cc by-sa", "cc-by-sa",
)


def licence_permits_archival(licence: str | None, is_open_access: str | None) -> bool:
    if not licence:
        return False
    lic = licence.strip().lower()
    if is_open_access not in ("Y", "y", "yes", True):
        return False
    return any(tok in lic for tok in _OPEN_LICENCES)


@dataclass
class ArchivalDecision:
    archival_status: str        # "link_only" | "archive_eligible"
    redistribution_status: str  # "not_established" | "permitted_open_licence"
    reason: str
    stored: bool = False        # this runner never sets True


def plan_archival(source_record: dict) -> ArchivalDecision:
    lic = source_record.get("license") or source_record.get("licence")
    ioa = source_record.get("isOpenAccess")
    if licence_permits_archival(lic, ioa):
        return ArchivalDecision(
            archival_status="link_only",   # eligible, but this runner still does not fetch files
            redistribution_status="permitted_open_licence",
            reason=f"open_licence_detected({lic!r});archival_eligible_but_runner_stores_link_only",
        )
    return ArchivalDecision(
        archival_status="link_only",
        redistribution_status="not_established",
        reason="licence_not_established_or_not_open;retain_citation+canonical_link_only",
    )
