"""Cross-provider de-duplication and record merging.

Records are grouped by ANY shared identifier - DOI, PMID, PMCID, NCT ID, canonical URL, normalised
title - via union-find, so a paper found by Europe PMC AND PubMed becomes one record that remembers
both finders. Trial registry records are never merged with publications (evidence types stay separate)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .dedup import norm_doi, norm_nct, norm_pmcid, norm_pmid, norm_title, norm_url
from .providers.base import EvidenceType

# lower number = preferred keeper when two records describe the same item
PROVIDER_PRIORITY = {"europepmc": 0, "pubmed": 1, "aga": 2, "acg": 2, "ecco": 2, "nice": 2, "bsg": 2,
                     "clinicaltrials": 3}
_TITLE_MIN_CHARS = 25     # very short titles are too generic to merge on


def _keys(rec: dict) -> list[str]:
    ks = []
    for tag, val in (("doi", norm_doi(rec.get("doi"))), ("pmid", norm_pmid(rec.get("pmid"))),
                     ("pmcid", norm_pmcid(rec.get("pmcid"))), ("nct", norm_nct(rec.get("nctId"))),
                     ("url", norm_url(rec.get("canonicalUrl")))):
        if val:
            ks.append(f"{tag}:{val}")
    t = norm_title(rec.get("title"))
    if len(t) >= _TITLE_MIN_CHARS:
        ks.append(f"title:{t}")
    return ks


def _conflict(a: dict, b: dict) -> bool:
    """Two records whose strong identifiers DIFFER are different items even if their titles match (e.g. two versions
    of the same guideline, each with its own DOI/PMID)."""
    for key, norm in (("doi", norm_doi), ("pmid", norm_pmid), ("pmcid", norm_pmcid), ("nctId", norm_nct)):
        x, y = norm(a.get(key)), norm(b.get(key))
        if x and y and x != y:
            return True
    return False


def _is_trial(rec: dict) -> bool:
    return rec.get("evidenceType") in (EvidenceType.ONGOING_TRIAL.value, EvidenceType.COMPLETED_TRIAL_RECORD.value)


def _richness(rec: dict) -> tuple:
    return (bool((rec.get("abstractText") or "").strip()), sum(bool(rec.get(k)) for k in ("doi", "pmid", "pmcid")),
            -PROVIDER_PRIORITY.get(rec.get("provider", ""), 9))


@dataclass
class MergeResult:
    records: list[dict]
    absorbed_by_provider: dict = field(default_factory=dict)      # provider -> records merged away
    merge_log: list[dict] = field(default_factory=list)


def merge(records: list[dict]) -> MergeResult:
    parent = list(range(len(records)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen: dict[str, int] = {}
    for i, rec in enumerate(records):
        for k in _keys(rec):
            # a trial registry record and a publication never merge, even if they share a title/NCT id
            token = f"trial|{k}" if _is_trial(rec) else k
            if token in seen:
                weak = k.startswith(("title:", "url:"))
                if weak and _conflict(rec, records[seen[token]]):
                    continue                         # same title/url but different DOI/PMID/NCT: different items
                a, b = find(i), find(seen[token])
                if a != b:
                    parent[max(a, b)] = min(a, b)
            else:
                seen[token] = i

    groups: dict[int, list[int]] = {}
    for i in range(len(records)):
        groups.setdefault(find(i), []).append(i)

    out, absorbed, log = [], {}, []
    for members in groups.values():
        group = [records[i] for i in members]
        keeper_idx = max(range(len(group)), key=lambda j: _richness(group[j]))
        keeper = dict(group[keeper_idx])
        found_by = sorted({r.get("provider", "") for r in group})
        for r in group:
            for k in ("doi", "pmid", "pmcid", "nctId", "alternateUrl", "abstractText", "journal", "authors",
                      "license", "publicationDate", "pubYear"):
                if not keeper.get(k) and r.get(k):
                    keeper[k] = r[k]
            if (r.get("evidenceType") == EvidenceType.CLINICAL_GUIDELINE.value
                    and keeper.get("evidenceType") == EvidenceType.PUBLISHED_STUDY.value):
                keeper["evidenceType"] = EvidenceType.CLINICAL_GUIDELINE.value
                keeper["society"] = r.get("society", keeper.get("society", ""))
            if r.get("requiresFullTextVerification"):
                keeper["requiresFullTextVerification"] = True
        keeper["foundBy"] = found_by
        out.append(keeper)
        for j, r in enumerate(group):
            if j != keeper_idx:
                prov = r.get("provider", "")
                absorbed[prov] = absorbed.get(prov, 0) + 1
        if len(group) > 1:
            log.append({"keptFrom": keeper.get("provider", ""), "foundBy": found_by,
                        "title": (keeper.get("title") or "")[:80]})
    return MergeResult(out, absorbed, log)
