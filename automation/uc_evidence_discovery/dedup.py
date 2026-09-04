"""Normalisation + duplicate detection across DOI / PMID / PMCID / trial id / canonical URL /
normalised title / SHA-256 content hash."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")


def norm_doi(value: Optional[str]) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    v = re.sub(r"^doi:\s*", "", v)
    return v.strip()


def norm_pmid(value: Optional[str]) -> str:
    if not value:
        return ""
    m = re.search(r"\d+", str(value))
    return m.group(0) if m else ""


def norm_pmcid(value: Optional[str]) -> str:
    if not value:
        return ""
    m = re.search(r"(?:PMC)?(\d+)", str(value).upper())
    return f"PMC{m.group(1)}" if m else ""


def norm_nct(value: Optional[str]) -> str:
    if not value:
        return ""
    m = re.search(r"NCT\d{8}", str(value).upper())
    return m.group(0) if m else ""


def norm_url(value: Optional[str]) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    v = re.sub(r"^https?://", "", v)
    v = re.sub(r"^www\.", "", v)
    return v.rstrip("/")


def norm_title(value: Optional[str]) -> str:
    if not value:
        return ""
    v = _PUNCT.sub(" ", value.strip().lower())
    return _WS.sub(" ", v).strip()


def content_hash(*parts: Optional[str]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").strip().lower().encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


@dataclass
class ProcessedIndex:
    doi: set = field(default_factory=set)
    pmid: set = field(default_factory=set)
    pmcid: set = field(default_factory=set)
    trial_id: set = field(default_factory=set)
    canonical_url: set = field(default_factory=set)
    checksum: set = field(default_factory=set)
    normalized_title: set = field(default_factory=set)

    @classmethod
    def from_checkpoint(cls, checkpoint: dict) -> "ProcessedIndex":
        psi = checkpoint.get("processedSourceIdentifiers", {}) or {}
        idx = cls(
            doi={norm_doi(x) for x in psi.get("doi", [])},
            pmid={norm_pmid(x) for x in psi.get("pubmedId", [])},
            pmcid={norm_pmcid(x) for x in psi.get("pmcid", [])},
            trial_id={norm_nct(x) for x in psi.get("trialId", [])},
            canonical_url={norm_url(x) for x in psi.get("canonicalUrl", [])},
            checksum=set(psi.get("checksum", [])),
            normalized_title={norm_title(x) for x in psi.get("normalizedTitle", [])},
        )
        for s in (idx.doi, idx.pmid, idx.pmcid, idx.trial_id, idx.canonical_url, idx.normalized_title):
            s.discard("")
        return idx

    def merge_sources_json(self, sources_doc: dict) -> "ProcessedIndex":
        for s in sources_doc.get("sources", []):
            self.doi.add(norm_doi(s.get("doi")))
            self.pmid.add(norm_pmid(s.get("pubmedId")))
            self.pmcid.add(norm_pmcid(s.get("pmcId") or s.get("pmcid")))
            self.trial_id.add(norm_nct(s.get("clinicalTrialsId") or s.get("nctId")))
            self.canonical_url.add(norm_url(s.get("canonicalUrl")))
            self.normalized_title.add(norm_title(s.get("title")))
        for s in (self.doi, self.pmid, self.pmcid, self.trial_id, self.canonical_url, self.normalized_title):
            s.discard("")
        return self

    def duplicate_reason(self, rec: "CandidateKey") -> Optional[str]:
        if rec.doi and rec.doi in self.doi:
            return f"duplicate_doi:{rec.doi}"
        if rec.pmid and rec.pmid in self.pmid:
            return f"duplicate_pmid:{rec.pmid}"
        if rec.pmcid and rec.pmcid in self.pmcid:
            return f"duplicate_pmcid:{rec.pmcid}"
        if rec.trial_id and rec.trial_id in self.trial_id:
            return f"duplicate_trial_id:{rec.trial_id}"
        if rec.canonical_url and rec.canonical_url in self.canonical_url:
            return f"duplicate_canonical_url:{rec.canonical_url}"
        if rec.checksum and rec.checksum in self.checksum:
            return f"duplicate_content_hash:{rec.checksum[:12]}"
        if rec.normalized_title and rec.normalized_title in self.normalized_title:
            return f"duplicate_normalized_title:{rec.normalized_title[:60]}"
        return None

    def add(self, rec: "CandidateKey") -> None:
        for attr, val in (
            ("doi", rec.doi), ("pmid", rec.pmid), ("pmcid", rec.pmcid),
            ("trial_id", rec.trial_id), ("canonical_url", rec.canonical_url),
            ("checksum", rec.checksum), ("normalized_title", rec.normalized_title),
        ):
            if val:
                getattr(self, attr).add(val)


@dataclass(frozen=True)
class CandidateKey:
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    trial_id: str = ""
    canonical_url: str = ""
    checksum: str = ""
    normalized_title: str = ""

    @classmethod
    def from_record(cls, rec: dict) -> "CandidateKey":
        title = rec.get("title") or ""
        abstract = rec.get("abstract") or rec.get("abstractText") or ""
        return cls(
            doi=norm_doi(rec.get("doi")),
            pmid=norm_pmid(rec.get("pmid") or rec.get("pubmedId")),
            pmcid=norm_pmcid(rec.get("pmcid") or rec.get("pmcId")),
            trial_id=norm_nct(rec.get("nctId") or rec.get("trialId")),
            canonical_url=norm_url(rec.get("canonicalUrl") or rec.get("url")),
            checksum=content_hash(title, abstract),
            normalized_title=norm_title(title),
        )
