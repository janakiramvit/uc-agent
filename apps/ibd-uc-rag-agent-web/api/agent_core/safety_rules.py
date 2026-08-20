"""
Safety / guardrail rules for the UC RAG prototype.

Pure keyword/pattern based (no LLM). These checks are deliberately
conservative -- when in doubt, the query is routed to a refusal rather
than to compose_answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SafetyBoundary(Enum):
    NONE = "none"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    FLARE_PREDICTION = "flare_prediction"
    MEDICATION_CHANGE = "medication_change"
    INDIVIDUALIZED_DIET_PLAN = "individualized_diet_plan"
    SYMPTOM_INFLAMMATION_EQUIVALENCE = "symptom_inflammation_equivalence"
    CROHNS_TO_UC_MISAPPLICATION = "crohns_to_uc_misapplication"


@dataclass
class SafetyCheckResult:
    boundary: SafetyBoundary
    triggered: bool
    message: str


REFUSAL_MESSAGES = {
    SafetyBoundary.DIAGNOSIS_REQUEST: (
        "This prototype cannot diagnose ulcerative colitis or confirm whether you are "
        "having a flare. Diagnosis and flare assessment require a qualified clinician "
        "using your full clinical picture, not a general evidence summary tool."
    ),
    SafetyBoundary.FLARE_PREDICTION: (
        "This prototype cannot predict individual flares. Flare risk and timing depend on "
        "factors specific to you that this tool does not have access to and is not "
        "designed to evaluate. Please speak with your care team about symptom monitoring."
    ),
    SafetyBoundary.MEDICATION_CHANGE: (
        "This prototype cannot recommend starting, stopping, or changing any medication. "
        "Medication decisions must be made with your prescribing clinician."
    ),
    SafetyBoundary.INDIVIDUALIZED_DIET_PLAN: (
        "This prototype cannot generate an individualized or prescriptive diet plan. "
        "It can share general, non-individualized evidence summaries on nutrition topics "
        "in the reviewed UC evidence set; a registered dietitian can help translate that "
        "into a personal plan."
    ),
    SafetyBoundary.SYMPTOM_INFLAMMATION_EQUIVALENCE: (
        "Symptoms and measurable intestinal inflammation do not always move together in "
        "ulcerative colitis -- a person can have symptoms without active inflammation, or "
        "inflammation with few or no symptoms. This tool cannot confirm or rule out "
        "inflammation based on symptoms alone. Objective testing and clinical assessment "
        "are needed for that."
    ),
    SafetyBoundary.CROHNS_TO_UC_MISAPPLICATION: (
        "The evidence located for that request applies to Crohn's disease only and cannot "
        "be applied to ulcerative colitis in this tool. This prototype only surfaces "
        "evidence explicitly reviewed as applicable to ulcerative colitis."
    ),
}

UNSUPPORTED_TOPIC_MESSAGE = "This topic is not currently covered by the reviewed UC evidence set."

SYMPTOM_INFLAMMATION_CAVEAT = (
    "Note: symptoms and measurable intestinal inflammation do not always move together in "
    "ulcerative colitis. This information does not confirm or rule out active inflammation."
)

# --- keyword patterns -------------------------------------------------

_DIAGNOSIS_PATTERNS = [
    r"\bdo i have (uc|ulcerative colitis)\b",
    r"\bis this (a )?flare\b",
    r"\bam i (having|in) a flare\b",
    r"\bdiagnos\w*\s+me\b",
    r"\bcan you diagnos\w*\b",
    r"\bdo i have ibd\b",
    r"\bwhat('s| is) wrong with me\b",
]

_FLARE_PREDICTION_PATTERNS = [
    r"\bwill i (have|get) a flare\b",
    r"\bpredict\w* .*(flare)\b",
    r"\bwhen will (my|i) flare\b",
    r"\bam i (going|about) to flare\b",
]

_MEDICATION_PATTERNS = [
    r"\bshould i (start|stop|change|increase|decrease|reduce) .*(medication|drug|biologic|steroid|mesalamine|azathioprine|infliximab|adalimumab|humira|remicade|prednisone)\b",
    r"\b(start|stop|change) my (medication|meds|dose|dosage)\b",
    r"\bwhat (medication|dose) should i (take|use)\b",
    r"\bincrease my dose\b",
    r"\bcan i stop taking\b",
]

_DIET_PLAN_PATTERNS = [
    r"\bgive me a diet plan\b",
    r"\b(create|build|make|design) (me )?a (meal|diet|eating) plan\b",
    r"\bwhat should i eat (today|this week|for my)\b.*\bpersonal\b",
    r"\bpersonalized (diet|meal) plan\b",
    r"\bmy (specific|personal) diet plan\b",
    r"\bplan (my|out my) meals\b",
]

_SYMPTOM_INFLAMMATION_PATTERNS = [
    r"\bdoes my pain mean i('?m| am) inflamed\b",
    r"\bdoes .*(pain|symptom).*(mean|indicate|prove).*(inflam)",
    r"\bif i have symptoms.*(does|is).*(inflam)",
    r"\bno symptoms.*(mean|means).*(no inflammation|not inflamed)\b",
]

_CROHNS_MISAPPLICATION_PATTERNS = [
    r"\bcrohn'?s.*(claim|evidence|study|finding).*(apply|use).*(\buc\b|ulcerative colitis)\b",
    r"\bapply .*crohn'?s.* to (\buc\b|ulcerative colitis)\b",
    r"\buse .*crohn'?s.* (evidence|claim|result).* for (\buc\b|ulcerative colitis)\b",
    r"\btreat .*crohn'?s.* evidence as.*(\buc\b|ulcerative colitis)\b",
]

_CROHNS_KEYWORD = re.compile(r"\bcrohn'?s\b")
_UC_KEYWORD = re.compile(r"\buc\b|\bulcerative colitis\b")
_APPLY_KEYWORDS = re.compile(r"\b(apply|use|treat|extend|generalize|carry over|transfer)\b")


def _is_crohns_to_uc_misapplication(text: str) -> bool:
    """Broader heuristic catch-all: the query mentions Crohn's, mentions
    UC, and uses an "apply/use/treat/extend" verb -- i.e. it is trying to
    get Crohn's-only evidence applied to a UC question. Deliberately
    broad/conservative: false positives here just mean an extra refusal,
    which is the safer failure mode for this boundary.
    """
    if not _CROHNS_KEYWORD.search(text):
        return False
    if not _UC_KEYWORD.search(text):
        return False
    return bool(_APPLY_KEYWORDS.search(text))


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)


def check_safety_boundaries(query: str) -> SafetyCheckResult:
    """Run all safety/guardrail checks against a raw user query.

    Returns the FIRST triggered boundary (checked in a fixed priority
    order), or a NONE result if nothing is triggered.
    """
    text = (query or "").lower().strip()

    if _matches_any(text, _CROHNS_MISAPPLICATION_PATTERNS) or _is_crohns_to_uc_misapplication(text):
        return SafetyCheckResult(
            SafetyBoundary.CROHNS_TO_UC_MISAPPLICATION,
            True,
            REFUSAL_MESSAGES[SafetyBoundary.CROHNS_TO_UC_MISAPPLICATION],
        )

    if _matches_any(text, _DIAGNOSIS_PATTERNS):
        return SafetyCheckResult(
            SafetyBoundary.DIAGNOSIS_REQUEST, True, REFUSAL_MESSAGES[SafetyBoundary.DIAGNOSIS_REQUEST]
        )

    if _matches_any(text, _FLARE_PREDICTION_PATTERNS):
        return SafetyCheckResult(
            SafetyBoundary.FLARE_PREDICTION, True, REFUSAL_MESSAGES[SafetyBoundary.FLARE_PREDICTION]
        )

    if _matches_any(text, _MEDICATION_PATTERNS):
        return SafetyCheckResult(
            SafetyBoundary.MEDICATION_CHANGE, True, REFUSAL_MESSAGES[SafetyBoundary.MEDICATION_CHANGE]
        )

    if _matches_any(text, _DIET_PLAN_PATTERNS):
        return SafetyCheckResult(
            SafetyBoundary.INDIVIDUALIZED_DIET_PLAN,
            True,
            REFUSAL_MESSAGES[SafetyBoundary.INDIVIDUALIZED_DIET_PLAN],
        )

    if _matches_any(text, _SYMPTOM_INFLAMMATION_PATTERNS):
        return SafetyCheckResult(
            SafetyBoundary.SYMPTOM_INFLAMMATION_EQUIVALENCE,
            True,
            REFUSAL_MESSAGES[SafetyBoundary.SYMPTOM_INFLAMMATION_EQUIVALENCE],
        )

    return SafetyCheckResult(SafetyBoundary.NONE, False, "")


def mentions_symptoms_or_inflammation(text: str) -> bool:
    text = (text or "").lower()
    return "symptom" in text or "inflam" in text


# Topics/keywords known to have zero UC-eligible claims in the current
# evidence set. classify_topic uses this to short-circuit straight to the
# fixed unsupported-topic fallback without even running retrieval.
KNOWN_UNSUPPORTED_KEYWORDS = [
    "esr",
    "erythrocyte sedimentation rate",
    "biologic",
    "infliximab",
    "adalimumab",
    "vedolizumab",
    "ustekinumab",
    "jak inhibitor",
    "tofacitinib",
    "upadacitinib",
    "mucosal healing",
    "colonoscopy",
    "intestinal ultrasound",
    "bowel ultrasound",
    "crp",
    "c-reactive protein",
    "fecal calprotectin",
    "calprotectin",
]


def is_known_unsupported_topic(query: str) -> bool:
    text = (query or "").lower()
    return any(kw in text for kw in KNOWN_UNSUPPORTED_KEYWORDS)
