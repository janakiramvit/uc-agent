from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator

Condition = Literal[
    "ulcerative_colitis", "crohns_disease", "ibd_general",
    "general_population", "unclear"
]
DiseaseContext = Literal[
    "active_disease", "remission", "post_surgery",
    "stricture_or_obstruction_risk", "general_or_unspecified",
    "not_applicable", "unclear"
]
OutcomeType = Literal[
    "symptoms", "inflammation", "biomarkers", "disease_activity",
    "remission_induction", "remission_maintenance", "relapse_risk",
    "hospitalisation", "surgery", "nutritional_status", "quality_of_life",
    "adverse_effects", "adherence", "general_patient_education", "unclear"
]
EvidenceLevel = Literal[
    "formal_guideline", "consensus_statement", "systematic_review",
    "meta_analysis", "randomized_trial", "controlled_trial",
    "observational", "official_patient_information",
    "expert_explanation", "other"
]


class SourceRecord(BaseModel):
    sourceId: str
    sourceType: str
    sourceTitle: str
    sourceUrl: HttpUrl
    canonicalUrl: HttpUrl
    authors: str = ""
    issuingOrganisation: str = ""
    journal: str = ""
    publicationYear: int = Field(ge=1900, le=2100)
    doi: str = ""
    studyType: str
    population: str
    sampleSize: str = "Not reported"
    countryOrRegion: str = "Not reported"
    conditionApplicability: list[Condition]
    diseaseContext: list[DiseaseContext]
    interventionOrExposure: str = ""
    comparator: str = ""
    outcomes: str
    mainRelevantFinding: str
    limitations: str
    applicabilityLimitations: str
    regionalApplicability: str
    relevantTopics: list[str]
    fullTextAvailability: Literal["public_full_text", "abstract_only", "public_webpage"]
    acquisitionMethod: str
    acquisitionStatus: str
    sourceQuality: Literal["high", "moderate", "limited"]
    directRelevance: Literal["direct", "indirect", "uncertain"]
    recommendation: Literal["select", "reject", "hold"]
    recommendationReason: str
    addedValue: str
    discoveredAt: datetime
    pmid: str = ""
    pmcid: str = ""

    @model_validator(mode="after")
    def abstract_quality(self):
        if self.fullTextAvailability == "abstract_only" and self.sourceQuality == "high":
            self.sourceQuality = "moderate"
        return self


class ClaimRecord(BaseModel):
    claimId: str
    sourceId: str
    sourceTitle: str
    sourceType: str
    sourceUrl: HttpUrl
    conditionApplicability: list[Condition]
    diseaseContext: list[DiseaseContext]
    topic: str
    outcomeType: OutcomeType
    claim: str = Field(min_length=25)
    plainLanguageExplanation: str = Field(min_length=25)
    possibleProductUse: str
    supportingExcerpt: str = Field(min_length=20)
    sectionHeading: str
    pageNumber: str = ""
    evidenceLevel: EvidenceLevel
    studyType: str
    population: str
    sampleSize: str = "Not reported"
    countryOrRegion: str = "Not reported"
    interventionOrExposure: str = ""
    comparator: str = ""
    outcome: str
    limitations: str
    applicabilityLimitations: str
    regionalApplicability: str
    confidence: Literal["high", "moderate", "low"]
    extractionMethod: str
    extractionVersion: str
    extractedAt: datetime
    reviewStatus: Literal["pending_human_review"] = "pending_human_review"
    userDecision: str = ""
    userEditedClaim: str = ""
    reviewerNotes: str = ""
    rejectionReason: str = ""

    @model_validator(mode="after")
    def enforce_review_and_confidence(self):
        if self.evidenceLevel in {"expert_explanation", "official_patient_information"}:
            if self.confidence == "high":
                raise ValueError("expert/patient information cannot receive high confidence")
        if any([self.userDecision, self.userEditedClaim, self.reviewerNotes]):
            raise ValueError("human-review fields must be blank")
        return self

