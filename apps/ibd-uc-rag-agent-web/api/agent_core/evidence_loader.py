"""
Evidence loader for the IBD / UC RAG prototype.

Reads the fixed, read-only evidence JSON package and builds LangChain
``Document`` objects for the claims that are eligible for use in this
UC-only prototype.

CRITICAL FILTERING RULE
------------------------
Only claims whose ``conditionApplicability`` field CONTAINS the substring
"ulcerative_colitis" are eligible. This is a strict substring filter and is
NOT the same as the broader "ibd_general" rule used in other, unrelated
prototypes. Do not widen this filter.

Structural exclusions
----------------------
The evidence file's ``claims`` array already excludes the IDs listed in
``excludedClaimIds`` (12 claims) -- they are simply absent from the data.
This loader defensively re-checks that no excluded ID ever appears in the
eligible set, in case the source data changes in the future.

This module never writes to the source evidence file. It only reads it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

UC_SUBSTRING = "ulcerative_colitis"

# Claim fields that must always be preserved verbatim (never summarized,
# reworded, or invented) when displayed to the user.
VERBATIM_FIELDS = (
    "claimText",
    "supportingExcerpt",
    "sourceUrl",
    "exactLocator",
    "evidenceLevel",
    "confidence",
    "limitations",
    "applicabilityLimitations",
)

DEFAULT_EVIDENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "ibd-prototype-evidence.json"


@dataclass(frozen=True)
class EvidencePackage:
    """Container for the loaded, filtered evidence."""

    version: str
    created_at: str
    intended_use: str
    sources_by_id: dict[str, dict[str, Any]]
    all_claims: list[dict[str, Any]]
    excluded_claim_ids: set[str]
    uc_eligible_claims: list[dict[str, Any]]
    crohns_only_claims: list[dict[str, Any]]
    limitations: Any
    # Which loader produced this package. Set by the loader itself, only after a
    # successful read - never inferred from env vars.
    backend: str = "file"
    # Which dataset the DB loader read ("prototype-v1" or "pilot"); "prototype-v1" for the JSON file.
    dataset: str = "prototype-v1"

    def citable_sources(self) -> list[dict[str, Any]]:
        """Sources that support at least one UC-eligible claim - the only sources an answer can ever cite."""
        ids = {c.get("sourceId") for c in self.uc_eligible_claims}
        return [s for sid, s in self.sources_by_id.items() if sid in ids]

    def source_counts(self, source_ids: "set[str] | None" = None) -> dict[str, int]:
        """Reviewed sources by kind. ``source_ids=None`` -> every citable source in the package."""
        pool = self.citable_sources() if source_ids is None else [
            self.sources_by_id[i] for i in source_ids if i in self.sources_by_id]
        out = {"total": len(pool), "studies": 0, "guidelines": 0, "trialRecords": 0, "patientInformation": 0}
        for s in pool:
            out[_KIND_KEY[source_kind(s)]] += 1
        return out

    def sources_for_claims(self, claim_ids: "list[str]") -> set[str]:
        by_claim = {c["claimId"]: c.get("sourceId") for c in self.all_claims}
        return {by_claim[c] for c in claim_ids if by_claim.get(c)}

    def provenance(self) -> dict[str, Any]:
        """Non-secret fingerprint of the evidence actually in memory."""
        return {
            "backend": self.backend,
            "dataset": self.dataset,
            "packageVersion": self.version,
            "sourceCount": len(self.sources_by_id),
            "claimCount": len(self.all_claims),
            "ucEligibleCount": len(self.uc_eligible_claims),
            "ucEligibleClaimIds": sorted(c["claimId"] for c in self.uc_eligible_claims),
            "reviewedSources": self.source_counts(),
        }


_KIND_KEY = {"study": "studies", "guideline": "guidelines", "trial_record": "trialRecords",
             "patient_information": "patientInformation"}


def source_kind(source: dict[str, Any]) -> str:
    """study | guideline | trial_record | patient_information - from the source's recorded type. Never 'papers'."""
    t = (source.get("sourceType") or "").lower()
    if "trial registry" in t or "registry record" in t or "trial record" in t:
        return "trial_record"
    if "guideline" in t or "consensus" in t:
        return "guideline"
    if "patient" in t or "official" in t:
        return "patient_information"
    return "study"


def load_raw_evidence(path: str | Path = DEFAULT_EVIDENCE_PATH) -> dict[str, Any]:
    """Read the evidence JSON file (read-only). Never writes to ``path``."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_uc_eligible(claim: dict[str, Any]) -> bool:
    """Strict substring filter: conditionApplicability must contain
    'ulcerative_colitis'. This is the ONLY eligibility rule for this
    prototype's UC evidence set -- do not also allow bare 'ibd_general'.
    """
    condition_applicability = claim.get("conditionApplicability") or ""
    return UC_SUBSTRING in condition_applicability


def is_crohns_only(claim: dict[str, Any]) -> bool:
    """True when a claim's conditionApplicability is exactly 'crohns_disease'
    (Crohn's-only evidence that must never be surfaced for a UC query).
    """
    return (claim.get("conditionApplicability") or "").strip() == "crohns_disease"


def load_evidence_package(path: str | Path = DEFAULT_EVIDENCE_PATH) -> EvidencePackage:
    """Load and filter the evidence package.

    Applies:
      1. Structural exclusion: any claimId present in ``excludedClaimIds``
         is dropped (defense in depth -- normally already absent).
      2. UC substring eligibility filter (see ``is_uc_eligible``).
    """
    raw = load_raw_evidence(path)

    sources_by_id = {s["sourceId"]: s for s in raw.get("sources", [])}
    excluded_claim_ids = set(raw.get("excludedClaimIds", []))

    all_claims = [
        c for c in raw.get("claims", []) if c.get("claimId") not in excluded_claim_ids
    ]

    uc_eligible_claims = [c for c in all_claims if is_uc_eligible(c)]
    crohns_only_claims = [c for c in all_claims if is_crohns_only(c)]

    return EvidencePackage(
        version=raw.get("version", ""),
        created_at=raw.get("createdAt", ""),
        intended_use=raw.get("intendedUse", ""),
        sources_by_id=sources_by_id,
        all_claims=all_claims,
        excluded_claim_ids=excluded_claim_ids,
        uc_eligible_claims=uc_eligible_claims,
        crohns_only_claims=crohns_only_claims,
        limitations=raw.get("limitations"),
    )


def claim_to_document(claim: dict[str, Any]) -> Document:
    """Wrap a single eligible claim as a LangChain ``Document``.

    ``page_content`` is built from fields useful for keyword/BM25 retrieval
    (topic, outcomeType, claim text, plain-language explanation, excerpt).
    All original claim fields are preserved verbatim in ``metadata`` for
    display -- nothing is summarized or reworded here.
    """
    content_parts = [
        claim.get("topic") or "",
        claim.get("outcomeType") or "",
        claim.get("diseaseContext") or "",
        claim.get("claimText") or "",
        claim.get("plainLanguageExplanation") or "",
        claim.get("supportingExcerpt") or "",
    ]
    page_content = "\n".join(p for p in content_parts if p)

    metadata = dict(claim)  # verbatim copy of every original field
    return Document(page_content=page_content, metadata=metadata)


def build_uc_documents(package: EvidencePackage) -> list[Document]:
    """Build the list of Documents for the UC-eligible claim set only."""
    return [claim_to_document(c) for c in package.uc_eligible_claims]


def get_topic_vocabulary(package: EvidencePackage) -> list[str]:
    """Distinct topics present across the UC-eligible claim set, for the
    Streamlit topic filter dropdown.
    """
    topics = sorted({c["topic"] for c in package.uc_eligible_claims if c.get("topic")})
    return topics
