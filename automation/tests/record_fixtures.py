"""Re-record the API fixtures used by the offline tests (NOT a test; run by hand: ``python tests/record_fixtures.py``).

Responses are fetched with the real guarded HTTP client, then trimmed to a handful of records so the fixtures stay small.
Only public metadata/abstracts are stored; nothing authenticated, no PDFs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uc_evidence_discovery.apis import clinicaltrials, europepmc, pubmed  # noqa: E402
from uc_evidence_discovery.apis.http import Http  # noqa: E402
from uc_evidence_discovery.providers.europepmc import EuropePmcProvider  # noqa: E402
from uc_evidence_discovery.providers.base import Window  # noqa: E402
import datetime as dt  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
FIX.mkdir(exist_ok=True)
W = Window(dt.date(2026, 11, 3), dt.date(2026, 11, 10))


def shorten_abstracts(xml: str, limit: int = 400) -> str:
    def cut(m):
        body = m.group(2)
        return f"{m.group(1)}{body[:limit]}</AbstractText>"
    return re.sub(r"(<AbstractText[^>]*>)(.*?)</AbstractText>", cut, xml, flags=re.S)


def dump(name: str, text: str) -> None:
    (FIX / name).write_text(text, encoding="utf-8")
    print("wrote", name, len(text))


def main() -> None:
    http = Http(enabled=True)

    # Europe PMC: raw JSON (core) trimmed to 4 results
    q = EuropePmcProvider().build_query(W)
    raw = http.get_json(f"{europepmc.BASE}/search", {"query": q, "format": "json", "resultType": "core",
                                                       "pageSize": "4", "cursorMark": "*"})
    raw["resultList"]["result"] = raw["resultList"]["result"][:4]
    for r in raw["resultList"]["result"]:          # fixtures keep only a short excerpt of each (publisher-owned) abstract
        r["abstractText"] = (r.get("abstractText") or "")[:400]
    dump("europepmc_window.json", json.dumps(raw, indent=1))
    dump("europepmc_zero_pubmed_syntax.json", json.dumps(http.get_json(
        f"{europepmc.BASE}/search", {"query": '"ulcerative colitis" AND (2021:2026[pub_year])', "format": "json",
                                    "resultType": "lite", "pageSize": "2", "cursorMark": "*"}), indent=1))

    # PubMed
    es = http.get_json(f"{pubmed.BASE}/esearch.fcgi", {
        "db": "pubmed", "term": '("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])', "retmode": "json",
        "retmax": "3", "datetype": "edat", "mindate": "2026/11/03", "maxdate": "2026/11/10", "sort": "pub_date"})
    dump("pubmed_esearch.json", json.dumps(es, indent=1))
    ids = es["esearchresult"]["idlist"][:3]
    dump("pubmed_efetch.xml", shorten_abstracts(http.get_text(f"{pubmed.BASE}/efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})))
    bad = http.get_json(f"{pubmed.BASE}/esearch.fcgi", {"db": "pubmed", "term": '"ulcerative colitis"[badfield] AND (',
                                                          "retmode": "json", "retmax": "1"})
    dump("pubmed_esearch_garbage_query.json", json.dumps(bad, indent=1))
    gid = http.get_json(f"{pubmed.BASE}/esearch.fcgi", {
        "db": "pubmed", "term": '("ulcerative colitis"[tiab]) AND (guideline[pt] OR "practice guideline"[pt])',
        "retmode": "json", "retmax": "2", "sort": "date"})["esearchresult"]["idlist"]
    gx = http.get_text(f"{pubmed.BASE}/efetch.fcgi", {"db": "pubmed", "id": ",".join(gid), "retmode": "xml"})
    gx = re.sub(r"<ReferenceList>.*?</ReferenceList>", "", gx, flags=re.S)
    gx = re.sub(r"<MeshHeadingList>.*?</MeshHeadingList>", "", gx, flags=re.S)
    gx = re.sub(r"<CommentsCorrectionsList>.*?</CommentsCorrectionsList>", "", gx, flags=re.S)
    dump("pubmed_efetch_guideline.xml", shorten_abstracts(gx))

    # ClinicalTrials.gov
    ct = http.get_json(f"{clinicaltrials.BASE}/studies", {
        "query.cond": "ulcerative colitis", "filter.advanced": "AREA[LastUpdatePostDate]RANGE[2026-11-03,2026-11-10]",
        "pageSize": "4", "countTotal": "true", "format": "json"})
    keep_mods = ("identificationModule", "statusModule", "descriptionModule", "designModule", "conditionsModule",
                 "sponsorCollaboratorsModule")
    ct["studies"] = [{"protocolSection": {k: v for k, v in st["protocolSection"].items() if k in keep_mods}}
                     for st in ct["studies"][:4]]
    dump("clinicaltrials_window.json", json.dumps(ct, indent=1))
    dump("clinicaltrials_bad_range.json", json.dumps(http.get_json(f"{clinicaltrials.BASE}/studies", {
        "query.cond": "ulcerative colitis", "filter.advanced": "AREA[LastUpdatePostDate]RANGE[2026-13-99,2026-11-10]",
        "pageSize": "1", "format": "json"}), indent=1))

    # robots.txt (policy inputs)
    for host in ("gi.org", "www.nice.org.uk", "www.bsg.org.uk"):
        dump(f"robots_{host}.txt", http.get_text(f"https://{host}/robots.txt"))
    for host in ("gastro.org",):
        dump(f"robots_{host}.txt", http.get_text(f"https://{host}/robots.txt"))

    # ACG listing: keep the UC / IBD guideline cards only
    html = http.get_text("https://gi.org/guidelines/")
    cards = re.findall(r'<div class="grid-item\s+guideline".*?(?=<div class="grid-item|\Z)', html, re.S)
    keep = [c for c in cards if re.search(r"Ulcerative|Crohn|Inflammatory Bowel", c)][:4]
    dump("acg_guidelines_listing.html", "<html><body>" + "".join(keep) + "</body></html>")

    # BSG sitemap: keep only clinical-resource URLs (all 156 are tiny) matching IBD/colitis
    sm = http.get_text("https://www.bsg.org.uk/sitemap.xml")
    urls = re.findall(r"<url>\s*<loc>[^<]+</loc>\s*<lastmod>[^<]+</lastmod>.*?</url>", sm, re.S)
    keepu = [u for u in urls if re.search(r"/clinical-resource/", u) and re.search(r"ibd|colitis|crohn|inflammatory|cholangio", u, re.I)]
    dump("bsg_sitemap.xml", '<?xml version="1.0"?><urlset>' + "".join(keepu) + "</urlset>")

    # NICE NG130: <head> + the dates/links region only
    nice = http.get_text("https://www.nice.org.uk/guidance/ng130")
    head = re.search(r"<head>.*?</head>", nice, re.S).group(0)
    times = "".join(re.findall(r"<time[^>]*>.*?</time>", nice, re.S))
    links = "".join(f'<a href="{m}"></a>' for m in sorted(set(re.findall(r'/guidance/(?:ng|ta|cg|qs)\d+', nice))))
    dump("nice_ng130.html", f"<html>{head}<body>{times}{links}</body></html>")


if __name__ == "__main__":
    main()
