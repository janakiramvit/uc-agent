"""Individually named, individually testable QA Agent checks.

Each function returns a ``QACheckResult`` (pass/fail + message). The
QA Agent node in ``app/subagents.py`` runs all of these as a final pass
and returns a structured report with one entry per check -- never just
a single overall boolean.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.evidence_loader import EvidencePackage, is_crohns_only, is_uc_eligible

EXPECTED_UC_CLAIM_IDS = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}


@dataclass
class QACheckResult:
    name: str
    passed: bool
    message: str


# --- 1. UC-only filtering -------------------------------------------------


def check_uc_only_filtering(package: EvidencePackage) -> QACheckResult:
    bad = [c["claimId"] for c in package.uc_eligible_claims if not is_uc_eligible(c)]
    passed = not bad
    return QACheckResult("uc_only_filtering", passed, "ok" if passed else f"non-UC-eligible claims leaked: {bad}")


# --- 2. Crohn's-only exclusion -------------------------------------------------


def check_crohns_only_exclusion(package: EvidencePackage) -> QACheckResult:
    uc_ids = {c["claimId"] for c in package.uc_eligible_claims}
    crohns_ids = {c["claimId"] for c in package.crohns_only_claims}
    leaked = uc_ids & crohns_ids
    passed = not leaked
    return QACheckResult(
        "crohns_only_exclusion", passed, "ok" if passed else f"Crohn's-only claims present in UC set: {leaked}"
    )


# --- 3. No superseded-source use -------------------------------------------------


def check_no_superseded_source_use(package: EvidencePackage) -> QACheckResult:
    bad = []
    for c in package.all_claims:
        source = package.sources_by_id.get(c["sourceId"])
        if source is None:
            bad.append(c["claimId"])
            continue
        # Defense in depth: if the data model ever adds supersession
        # fields, no active claim may point at a superseded source.
        if source.get("supersededBy") or source.get("superseded_by") or source.get("status") == "superseded":
            bad.append(c["claimId"])
    passed = not bad
    return QACheckResult(
        "no_superseded_source_use", passed, "ok" if passed else f"claims referencing missing/superseded sources: {bad}"
    )


# --- 4. Unique claim IDs -------------------------------------------------


def check_unique_claim_ids(package: EvidencePackage) -> QACheckResult:
    ids = [c["claimId"] for c in package.all_claims]
    passed = len(ids) == len(set(ids))
    return QACheckResult("unique_claim_ids", passed, "ok" if passed else "duplicate claimIds found")


# --- 5. Source existence -------------------------------------------------


def check_source_existence(package: EvidencePackage) -> QACheckResult:
    bad = [c["claimId"] for c in package.all_claims if c["sourceId"] not in package.sources_by_id]
    passed = not bad
    return QACheckResult("source_existence", passed, "ok" if passed else f"claims with unresolved sourceId: {bad}")


# --- 6. Exact locator presence -------------------------------------------------


def check_exact_locator_presence(citations: list[dict[str, Any]]) -> QACheckResult:
    bad = [c.get("claimId") for c in citations if not (c.get("exactLocator") or "").strip()]
    passed = not bad
    return QACheckResult("exact_locator_presence", passed, "ok" if passed else f"missing exactLocator for: {bad}")


# --- 7. Excerpt presence -------------------------------------------------


def check_excerpt_presence(citations: list[dict[str, Any]]) -> QACheckResult:
    bad = [c.get("claimId") for c in citations if not (c.get("supportingExcerpt") or "").strip()]
    passed = not bad
    return QACheckResult("excerpt_presence", passed, "ok" if passed else f"missing supportingExcerpt for: {bad}")


# --- 8. Limitation preservation -------------------------------------------------


def check_limitation_preservation(citations: list[dict[str, Any]], package: EvidencePackage) -> QACheckResult:
    claims_by_id = {c["claimId"]: c for c in package.all_claims}
    bad = []
    for c in citations:
        original = claims_by_id.get(c.get("claimId"))
        if original is None:
            bad.append(c.get("claimId"))
            continue
        if not (c.get("limitations") or "").strip() or not (c.get("applicabilityLimitations") or "").strip():
            bad.append(c.get("claimId"))
            continue
        if c.get("limitations") != original.get("limitations"):
            bad.append(c.get("claimId"))
        if c.get("applicabilityLimitations") != original.get("applicabilityLimitations"):
            bad.append(c.get("claimId"))
    passed = not bad
    return QACheckResult(
        "limitation_preservation", passed, "ok" if passed else f"limitations not preserved/present for: {bad}"
    )


# --- 9. Unsupported-topic fallback correctness -------------------------------------------------


def check_unsupported_topic_fallback_correctness(answer: str, citations: list[dict[str, Any]]) -> QACheckResult:
    from app.safety_rules import UNSUPPORTED_TOPIC_MESSAGE

    if citations:
        return QACheckResult("unsupported_topic_fallback_correctness", True, "ok (citations present, fallback n/a)")
    passed = answer == UNSUPPORTED_TOPIC_MESSAGE
    return QACheckResult(
        "unsupported_topic_fallback_correctness",
        passed,
        "ok" if passed else f"no citations but answer != fixed fallback message: {answer!r}",
    )


# --- 10. ESR remains unsupported -------------------------------------------------


def check_esr_unsupported(gap_terms: list[str]) -> QACheckResult:
    passed = "esr" in [t.lower() for t in gap_terms]
    return QACheckResult("esr_remains_unsupported", passed, "ok" if passed else "'esr' missing from evidence gap terms")


# --- 11-15. Output-safety checks on the final composed answer -------------------------------------------------

_DIAGNOSIS_OUTPUT_PATTERNS = [
    r"\byou have (uc|ulcerative colitis)\b",
    r"\byou are diagnosed\b",
    r"\bthis confirms you have\b",
    r"\byour (uc|ulcerative colitis) is (active|in flare|flaring)\b",
]

_FLARE_OUTPUT_PATTERNS = [
    r"\byou will flare\b",
    r"\byou('re| are) (going|about) to flare\b",
    r"\bflare is (imminent|coming|predicted)\b",
]

_MEDICATION_OUTPUT_PATTERNS = [
    r"\byou should (start|stop|take|increase|decrease|reduce) .*(medication|dose|drug|biologic|steroid)\b",
    r"\bstart taking\b",
    r"\bstop taking\b",
]

_DIET_PRESCRIPTION_OUTPUT_PATTERNS = [
    r"\byour (personal|individualized|specific) diet plan\b",
    r"\byou must eat\b",
    r"\bhere is your meal plan\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(re.search(p, lowered) for p in patterns)


def check_no_diagnosis_in_answer(answer: str) -> QACheckResult:
    passed = not _matches_any(answer, _DIAGNOSIS_OUTPUT_PATTERNS)
    return QACheckResult("no_diagnosis_in_answer", passed, "ok" if passed else "answer contains diagnosis language")


def check_no_flare_prediction_in_answer(answer: str) -> QACheckResult:
    passed = not _matches_any(answer, _FLARE_OUTPUT_PATTERNS)
    return QACheckResult(
        "no_flare_prediction_in_answer", passed, "ok" if passed else "answer contains flare-prediction language"
    )


def check_no_medication_change_in_answer(answer: str) -> QACheckResult:
    passed = not _matches_any(answer, _MEDICATION_OUTPUT_PATTERNS)
    return QACheckResult(
        "no_medication_change_in_answer", passed, "ok" if passed else "answer contains medication-change language"
    )


def check_no_diet_prescription_in_answer(answer: str) -> QACheckResult:
    passed = not _matches_any(answer, _DIET_PRESCRIPTION_OUTPUT_PATTERNS)
    return QACheckResult(
        "no_diet_prescription_in_answer",
        passed,
        "ok" if passed else "answer contains an individualized diet prescription",
    )


# --- 16. No association-to-causation upgrade -------------------------------------------------

_HEDGE_WORDS = ("associated", "association", "may be linked", "linked to", "correlat", "observational")
_CAUSAL_WORDS = (
    "causes",
    "cause of",
    "proven to cause",
    "results in",
    "leads to",
    "is caused by",
)


def check_no_causation_upgrade(answer: str, citations: list[dict[str, Any]]) -> QACheckResult:
    """If any cited claim's own text uses hedged/associative language, the
    composed answer must not strengthen it to causal language anywhere.
    """
    lowered_answer = (answer or "").lower()
    any_hedged_source = any(
        any(h in (c.get("claimText") or "").lower() for h in _HEDGE_WORDS) for c in citations
    )
    causal_in_answer = any(w in lowered_answer for w in _CAUSAL_WORDS)
    if causal_in_answer and any_hedged_source:
        return QACheckResult(
            "no_causation_upgrade",
            False,
            "answer uses causal language while underlying evidence is only associative/hedged",
        )
    # Also flag causal language not present verbatim in any cited claim text
    # (i.e. invented certainty not grounded in any source at all).
    if causal_in_answer:
        grounded = any(any(w in (c.get("claimText") or "").lower() for w in _CAUSAL_WORDS) for c in citations)
        if not grounded:
            return QACheckResult(
                "no_causation_upgrade", False, "answer uses causal language not present in any cited claim text"
            )
    return QACheckResult("no_causation_upgrade", True, "ok")


ALL_CHECK_NAMES = (
    "uc_only_filtering",
    "crohns_only_exclusion",
    "no_superseded_source_use",
    "unique_claim_ids",
    "source_existence",
    "exact_locator_presence",
    "excerpt_presence",
    "limitation_preservation",
    "unsupported_topic_fallback_correctness",
    "esr_remains_unsupported",
    "no_diagnosis_in_answer",
    "no_flare_prediction_in_answer",
    "no_medication_change_in_answer",
    "no_diet_prescription_in_answer",
    "no_causation_upgrade",
)


def run_all_qa_checks(
    package: EvidencePackage,
    answer: str,
    citations: list[dict[str, Any]],
    gap_terms: list[str],
) -> dict[str, Any]:
    """Run every QA check and return a structured pass/fail report."""
    results = [
        check_uc_only_filtering(package),
        check_crohns_only_exclusion(package),
        check_no_superseded_source_use(package),
        check_unique_claim_ids(package),
        check_source_existence(package),
        check_exact_locator_presence(citations),
        check_excerpt_presence(citations),
        check_limitation_preservation(citations, package),
        check_unsupported_topic_fallback_correctness(answer, citations),
        check_esr_unsupported(gap_terms),
        check_no_diagnosis_in_answer(answer),
        check_no_flare_prediction_in_answer(answer),
        check_no_medication_change_in_answer(answer),
        check_no_diet_prescription_in_answer(answer),
        check_no_causation_upgrade(answer, citations),
    ]
    checks = {r.name: {"passed": r.passed, "message": r.message} for r in results}
    overall_pass = all(r.passed for r in results)
    return {"overall_pass": overall_pass, "checks": checks}
