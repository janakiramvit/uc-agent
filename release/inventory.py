"""Unified inventory of every evidence record we possess, with exact de-duplication and ID-collision checks.

Origins (retention priority):  production (prototype-v1, live)  >  baseline-register  >  staging (Phase 2 + daily discovery,
frozen at the cutoff commit).  Sources are merged by DOI / PMID / PMCID / NCT / canonical URL / normalised title (a title never merges
two records whose strong identifiers differ). Claims are exact duplicates only when source group, normalised claim text AND exact
excerpt all match. Nothing is deleted: every decision is returned as data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PRODUCTION_JSON = REPO / "apps" / "ibd-uc-rag-agent-web" / "api" / "data" / "ibd-prototype-evidence.json"
BASELINE_XLSX = REPO / "knowledge" / "ibd-research-review" / "ibd-evidence-review-final-remediation.xlsx"
FROZEN = REPO / "release" / "frozen"
ORIGINS = ("production", "baseline-register", "staging")


def n_doi(v):
    v = (v or "").strip().lower()
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v)
    return re.sub(r"^doi:\s*", "", v).strip()


def n_pmid(v):
    m = re.search(r"\d+", str(v or ""))
    return m.group(0) if m else ""


def n_pmcid(v):
    m = re.search(r"PMC\d+", str(v or "").upper())
    return m.group(0) if m else ""


def n_nct(v):
    m = re.search(r"NCT\d{8}", str(v or "").upper())
    return m.group(0) if m else ""


def n_url(v):
    v = re.sub(r"^https?://(www\.)?", "", (v or "").strip().lower())
    return v.rstrip("/")


def n_title(v):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (v or "").lower())).strip()


def n_text(v):
    return re.sub(r"\s+", " ", (v or "").strip().lower())


@dataclass
class Src:
    origin: str
    source_id: str
    title: str
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    nct: str = ""
    url: str = ""
    date: str = ""
    evidence_type: str = "published_study"
    raw: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.origin}:{self.source_id}"

    def keys(self) -> list[str]:
        ks = [f"doi:{n_doi(self.doi)}", f"pmid:{n_pmid(self.pmid)}", f"pmcid:{n_pmcid(self.pmcid)}",
              f"nct:{n_nct(self.nct)}", f"url:{n_url(self.url)}"]
        ks = [k for k in ks if not k.endswith(":")]
        t = n_title(self.title)
        if len(t) >= 25:
            ks.append(f"title:{t}")
        return ks


@dataclass
class Clm:
    origin: str
    claim_id: str
    source_id: str
    text: str
    excerpt: str
    locator: str = ""
    applicability: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        return f"{self.origin}:{self.claim_id}"


# ------------------------------------------------------------------ loaders
def _ids_from_url(url: str) -> dict:
    out = {}
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url or "")
    if m:
        out["pmid"] = m.group(1)
    m = re.search(r"(PMC\d+)", url or "", re.I)
    if m:
        out["pmcid"] = m.group(1).upper()
    m = re.search(r"(10\.\d{4,9}/[^\s?#]+)", url or "")
    if m:
        out["doi"] = m.group(1)
    return out


def load_production() -> tuple[list[Src], list[Clm]]:
    d = json.loads(PRODUCTION_JSON.read_text())
    srcs = [Src("production", s["sourceId"], s["sourceTitle"], url=s.get("sourceUrl", ""), date=str(s.get("publicationYear", "")),
                raw=s, **_ids_from_url(s.get("sourceUrl", ""))) for s in d["sources"]]
    clms = [Clm("production", c["claimId"], c["sourceId"], c["claimText"], c["supportingExcerpt"], c.get("exactLocator", ""),
                c.get("conditionApplicability", ""), c) for c in d["claims"]]
    return srcs, clms


def _xlsx_table(path, sheet, header_row_idx=3):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb[sheet].iter_rows(values_only=True))
    wb.close()
    h = [str(c).strip() if c not in (None, "") else f"c{i}" for i, c in enumerate(rows[header_row_idx])]
    return [dict(zip(h, r)) for r in rows[header_row_idx + 1:] if any(v not in (None, "") for v in r)]


def load_baseline() -> tuple[list[Src], list[Clm]]:
    c = lambda v: None if v in (None, "", "None") else str(v)          # noqa: E731
    srcs = [Src("baseline-register", str(r["Source ID"]), c(r.get("Source title")) or "", doi=c(r.get("DOI")) or "",
                pmid=c(r.get("PMID")) or "", pmcid=c(r.get("PMCID")) or "",
                url=c(r.get("Authoritative source URL")) or c(r.get("Canonical URL")) or "", date=c(r.get("Year")) or "", raw=r)
            for r in _xlsx_table(BASELINE_XLSX, "Sources")]
    clms = [Clm("baseline-register", str(r["Claim ID"]), c(r.get("Source ID")) or "", c(r.get("Final remediated claim")) or "",
                c(r.get("Preserved supporting excerpt")) or "", c(r.get("Precise locator")) or "",
                c(r.get("Condition applicability")) or "", r)
            for r in _xlsx_table(BASELINE_XLSX, "Claims")]
    return srcs, clms


def load_staging() -> tuple[list[Src], list[Clm]]:
    S = json.loads((FROZEN / "staging-sources.json").read_text())["sources"]
    C = json.loads((FROZEN / "staging-candidate-claims.json").read_text())["claims"]
    srcs = [Src("staging", s["sourceId"], s["title"], doi=s.get("doi") or "", pmid=s.get("pubmedId") or "",
                pmcid=s.get("pmcId") or "", nct=s.get("clinicalTrialsId") or "", url=s.get("canonicalUrl") or "",
                date=s.get("publicationDate") or "", evidence_type=s.get("evidenceType") or "published_study", raw=s) for s in S]
    clms = [Clm("staging", c["claimId"], c["sourceId"], c["normalizedClaim"], c["exactSupportingExcerpt"], c.get("exactLocator", ""),
                c.get("conditionApplicability", ""), c) for c in C]
    return srcs, clms


# ------------------------------------------------------------------ source de-duplication
def _conflict(a: Src, b: Src) -> bool:
    for f in ("doi", "pmid", "pmcid", "nct"):
        x, y = {"doi": n_doi, "pmid": n_pmid, "pmcid": n_pmcid, "nct": n_nct}[f](getattr(a, f)), \
               {"doi": n_doi, "pmid": n_pmid, "pmcid": n_pmcid, "nct": n_nct}[f](getattr(b, f))
        if x and y and x != y:
            return True
    return False


@dataclass
class SourceGroup:
    gid: str
    keeper: Src
    members: list[Src]
    matched_on: list[str]


def dedupe_sources(srcs: list[Src]) -> tuple[list[SourceGroup], list[dict]]:
    rank = {o: i for i, o in enumerate(ORIGINS)}
    parent = list(range(len(srcs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    seen: dict[str, int] = {}
    reasons: dict[tuple[int, int], set] = {}
    for i, s in enumerate(srcs):
        for k in s.keys():
            if k in seen:
                j = seen[k]
                if k.startswith(("title:", "url:")) and _conflict(s, srcs[j]):
                    continue
                a, b = find(i), find(j)
                if a != b:
                    parent[max(a, b)] = min(a, b)
                reasons.setdefault((min(i, j), max(i, j)), set()).add(k.split(":", 1)[0])
            else:
                seen[k] = i
    groups: dict[int, list[int]] = {}
    for i in range(len(srcs)):
        groups.setdefault(find(i), []).append(i)
    out, decisions = [], []
    for n, (root, idxs) in enumerate(sorted(groups.items(), key=lambda kv: kv[0]), 1):
        members = [srcs[i] for i in idxs]
        keeper = min(members, key=lambda s: (rank[s.origin], s.source_id))
        matched = sorted({r for (a, b), rs in reasons.items() if a in idxs and b in idxs for r in rs})
        g = SourceGroup(f"SG{n:03d}", keeper, members, matched)
        out.append(g)
        if len(members) > 1:
            decisions.append({"group": g.gid, "kept": keeper.uid, "merged": [m.uid for m in members if m is not keeper],
                              "matchedOn": matched, "title": keeper.title[:90]})
    return out, decisions


# ------------------------------------------------------------------ claim de-duplication
def dedupe_claims(clms: list[Clm], src_group: dict[str, str]) -> tuple[list[Clm], list[dict], list[dict]]:
    """Exact duplicates: same source GROUP + normalised claim + normalised excerpt. Also reports claim-ID collisions
    (same ID, different content) and same-excerpt/different-text pairs, none of which are merged."""
    rank = {o: i for i, o in enumerate(ORIGINS)}
    ordered = sorted(clms, key=lambda c: (rank[c.origin], c.claim_id))
    keep: dict[tuple, Clm] = {}
    kept, decisions = [], []
    for c in ordered:
        key = (src_group.get(f"{c.origin}:{c.source_id}", c.source_id), n_text(c.text), n_text(c.excerpt))
        if key in keep:
            decisions.append({"duplicate": c.uid, "keptAs": keep[key].uid, "rule": "same source group + claim text + excerpt"})
            continue
        keep[key] = c
        kept.append(c)
    by_id: dict[str, list[Clm]] = {}
    for c in kept:
        by_id.setdefault(c.claim_id, []).append(c)
    collisions = [{"claimId": cid, "records": [c.uid for c in cs],
                   "note": "same claim ID, different content - kept apart, never merged or re-labelled"}
                  for cid, cs in by_id.items() if len(cs) > 1]
    return kept, decisions, collisions


def build() -> dict:
    ps, pc = load_production()
    bs, bc = load_baseline()
    ss, sc = load_staging()
    all_src, all_clm = ps + bs + ss, pc + bc + sc
    groups, sdec = dedupe_sources(all_src)
    uid_to_group = {m.uid: g.gid for g in groups for m in g.members}
    kept, cdec, collisions = dedupe_claims(all_clm, uid_to_group)
    # source-ID collisions: same source_id string, different groups
    by_sid: dict[str, set] = {}
    for g in groups:
        for m in g.members:
            by_sid.setdefault(m.source_id, set()).add(g.gid)
    sid_collisions = [{"sourceId": k, "groups": sorted(v)} for k, v in by_sid.items() if len(v) > 1]
    return {"sources_before": len(all_src), "sources_after": len(groups), "claims_before": len(all_clm), "claims_after": len(kept),
            "by_origin": {"sources": {o: sum(1 for s in all_src if s.origin == o) for o in ORIGINS},
                          "claims": {o: sum(1 for c in all_clm if c.origin == o) for o in ORIGINS}},
            "groups": groups, "uid_to_group": uid_to_group, "claims": kept, "all_claims": all_clm, "all_sources": all_src,
            "source_decisions": sdec, "claim_decisions": cdec, "claim_id_collisions": collisions,
            "source_id_collisions": sid_collisions}
