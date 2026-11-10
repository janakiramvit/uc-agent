"""Guideline-body connectors: AGA, ACG, ECCO, NICE, BSG.

Each body has up to two lawful channels:
  * ``site``    - the body's own public listing/sitemap/page, used ONLY when its robots.txt allows it;
  * ``indexed`` - the body's guideline publications as indexed in PubMed (official NCBI API), filtered by journal and
                  guideline publication type. This is how AGA and ECCO are covered: gastro.org disallows all generic bots
                  and ecco-ibd.eu answers 403, so their sites are never fetched (reported as a legitimate access limitation).

Only public metadata (title, date, DOI, link) and - via PubMed - the abstract are retained. No PDFs are fetched or stored;
PDF links found on listings are discarded. Every record is flagged ``requiresFullTextVerification``.
"""

from __future__ import annotations

import datetime as _dt
import html
import re
from typing import Callable, Optional
from urllib.parse import urlparse

from .. import config
from ..apis.http import Http
from .base import (AccessLimited, EvidenceType, InvalidQuery, Provider, ProviderUnavailable, SearchOutcome, Window)
from .common import classify_publication, guarded
from .pubmed import PubMedProvider
from .robots import RobotsPolicy

UC_TEXT = re.compile(r"ulcerative colitis|\bUC\b|colitis|inflammatory bowel|\bIBD\b", re.I)
_PDF_OR_MEDIA = re.compile(r"\.(pdf|mp3|mp4|docx?|xlsx?)(\?|$)", re.I)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _canonical_url(u: str) -> str:
    u = html.unescape(u).replace("\\", "/")
    p = urlparse(u)
    return f"{p.scheme}://{p.netloc}{p.path}"          # drop tracking/context query strings


# ------------------------------------------------------------------ parsers (pure, fixture-tested)
def parse_acg_listing(page_html: str) -> list[dict]:
    """ACG ``/guidelines/`` cards -> records. Metadata only; PDF/podcast links are discarded."""
    out = []
    for m in re.finditer(r'<div class="grid-item\s+guideline"([^>]*)>(.*?)(?=<div class="grid-item|\Z)', page_html, re.S):
        attrs, body = m.group(1), m.group(2)
        ts = re.search(r'data-date-created="(\d+)"', attrs)
        name = re.search(r'<span class="name">(.*?)</span>', body, re.S)
        if not name:
            continue
        title = _clean(name.group(1))
        links = [html.unescape(l) for l in re.findall(r'href="([^"]+)"', body) if l.startswith("http")]
        links = [l for l in links if not _PDF_OR_MEDIA.search(l.replace("\\", "/"))]
        main = links[0] if links else ""
        doi = ""
        dm = re.search(r"doi\.org/(10\.\d{4,9}/[^\s\"'?#]+)", main)
        if dm:
            doi = dm.group(1)
        date = ""
        if ts:
            date = _dt.datetime.fromtimestamp(int(ts.group(1)) / 1000, _dt.timezone.utc).date().isoformat()
        status_text = _clean(re.search(r'text-sm m-b-xs m-t-xs">(.*?)</p>', body, re.S).group(1)) \
            if re.search(r'text-sm m-b-xs m-t-xs">', body) else ""
        out.append({"title": title, "canonicalUrl": _canonical_url(main) if main else "", "doi": doi,
                    "publicationDate": date, "listingNote": status_text})
    return out


def _slug_title(slug: str) -> str:
    caps = {"bsg", "ibd", "uk", "nice", "crc", "ercp", "esge"}
    words = [w.upper() if w.lower() in caps else w for w in re.split(r"[-_]+", slug) if w]
    text = " ".join(words)
    return text[:1].upper() + text[1:]


def parse_bsg_sitemap(xml_text: str) -> list[dict]:
    """BSG sitemap -> UC/IBD guideline resources: {url, lastmod, title-from-slug}."""
    out = []
    for m in re.finditer(r"<url>\s*<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", xml_text):
        url, lastmod = html.unescape(m.group(1)), m.group(2)[:10]
        if "/clinical-resource/" not in url:
            continue
        slug = url.rsplit("/", 1)[-1]
        if slug.startswith("(sss)") or not re.search(r"guideline|guidance|consensus", slug, re.I):
            continue
        if not re.search(r"ibd|colitis|crohn|inflammatory", slug, re.I):
            continue
        out.append({"title": _slug_title(slug),
                    "canonicalUrl": url, "publicationDate": lastmod, "doi": "", "titleSource": "url_slug"})
    return out


def parse_nice_page(page_html: str, url: str) -> Optional[dict]:
    t = re.search(r"<title>(.*?)</title>", page_html, re.S)
    if not t:
        return None
    parts = [p.strip() for p in _clean(t.group(1)).split("|")]
    title = parts[1] if len(parts) >= 3 else parts[0]
    dates = sorted({d for d in re.findall(r'datetime="(\d{4}-\d{2}-\d{2})"', page_html)})
    if not title:
        return None
    return {"title": title, "canonicalUrl": url, "doi": "",
            "publicationDate": dates[-1] if dates else "", "datesSeen": dates}


# ------------------------------------------------------------------ composite provider
class _IndexChannel(PubMedProvider):
    """PubMed-indexed guideline publications for one society's journal(s)."""

    def __init__(self, name: str, clause: str) -> None:
        self.name = name
        self.extra_clause = clause
        self.expect_in_translation = ("[Journal]",)

    def canary_window(self, today, window=None):
        # guideline publications are rare: a 1-year canary can legitimately be empty, so look back 5 years
        start = (window.start if window else today) - _dt.timedelta(days=5 * 365)
        return Window(start, today)


class SocietyProvider(Provider):
    evidence_type = EvidenceType.CLINICAL_GUIDELINE
    expects_daily_results = False
    canary_zero_is_error = False       # guideline bodies publish rarely; an empty canary cannot prove a broken query

    def __init__(self, *, name: str, label: str, society: str, robots_host: str, robots_probe: str,
                 site: Optional[Callable] = None, index_clause: str = "") -> None:
        self.name, self.label, self.society = name, label, society
        self.robots_host, self.robots_probe = robots_host, robots_probe
        self._site = site
        self._index = _IndexChannel(name, index_clause) if index_clause else None
        self.known_listing_urls: set[str] = set()
        self.listing_seen: set[str] = set()
        self.listing_total = 0

    def build_query(self, window: Window) -> str:
        parts = []
        if self._site:
            parts.append(f"site:{self.robots_host} (robots-permitting listing; window {window.iso()[0]}..{window.iso()[1]})")
        if self._index:
            parts.append(self._index.build_query(window))
        return " | ".join(parts) or f"{self.robots_host} robots probe"

    # -- helpers
    def _tag(self, rec: dict, channel: str) -> dict:
        rec.update({"provider": self.name, "society": self.society, "evidenceType": EvidenceType.CLINICAL_GUIDELINE.value,
                    "journal": rec.get("journal") or self.society, "publishingOrganisation": self.society,
                    "requiresFullTextVerification": True, "channel": channel,
                    "accessStatus": rec.get("accessStatus") or "public_listing_metadata_only",
                    "license": rec.get("license") or "", "isOpenAccess": rec.get("isOpenAccess", "N")})
        rec.setdefault("abstractText", "")
        rec.setdefault("pubYear", (rec.get("publicationDate") or "")[:4])
        rec.setdefault("retrievedVia", f"{self.label} public listing")
        return rec

    def _in_window(self, rec: dict, window: Window) -> bool:
        d = (rec.get("publicationDate") or "")[:10]
        dated = len(d) == 10
        if dated and d < config.EARLIEST_DISCOVERY_DATE:
            return False          # nothing older than the discovery start date is ever ingested (no backfill)
        new_url = bool(self.known_listing_urls) and rec.get("canonicalUrl") not in self.known_listing_urls
        return new_url or (dated and window.start.isoformat() <= d <= window.end.isoformat())

    def search_window(self, http: Http, window: Window, *, max_pages: int) -> SearchOutcome:
        out = SearchOutcome()
        out.queries.append(self.build_query(window))
        robots = RobotsPolicy(http)
        self.listing_seen = set()          # committed to state by the orchestrator only if the window is completed
        site_ok = False
        try:
            robots.require(self.robots_probe)          # always learn (and report) the site's policy
            if self._site:
                site_ok = True
            else:
                out.notes.append(f"{self.robots_host}: robots.txt permits access but no site connector is configured; "
                                 "covered through the PubMed index only")
        except AccessLimited as exc:
            out.access_limits.append(str(exc))

        if site_ok:
            items = self._site(self, http, robots, window, out)
            self.listing_total = len(items)
            self.listing_seen = {i["canonicalUrl"] for i in items if i.get("canonicalUrl")}
            for it in items:
                if self._in_window(it, window):
                    out.records.append(self._tag(it, "site"))
            out.hit_count += len(out.records)

        if self._index:
            sub = self._index.search_window(http, window, max_pages=max_pages)
            out.covered_through = sub.covered_through
            out.searches += sub.searches
            out.queries.extend(sub.queries)
            kept = 0
            for rec in sub.records:
                if classify_publication(rec) is EvidenceType.CLINICAL_GUIDELINE:
                    rec["retrievedVia"] = f"PubMed index ({self.society} journal guideline filter) via NCBI E-utilities"
                    out.records.append(self._tag(rec, "pubmed_index"))
                    kept += 1
            skipped = len(sub.records) - kept
            if skipped:
                out.notes.append(f"{skipped} non-guideline record(s) from the {self.society} journal filter ignored")
            out.hit_count += kept
            out.truncated = out.truncated or sub.truncated
        if not site_ok and not self._index:
            raise AccessLimited("; ".join(out.access_limits) or f"{self.robots_host}: not accessible")
        return out

    def canary_count(self, http: Http, today: _dt.date, window: Optional[Window] = None) -> int:
        """Listing channel: how many UC/IBD guidelines are visible at all (not date-filtered)."""
        robots = RobotsPolicy(http)
        total = 0
        if self._site:
            try:
                robots.require(self.robots_probe)
                scratch = SearchOutcome()
                total += len(self._site(self, http, robots, Window(today, today), scratch))
            except AccessLimited:
                pass
        if self._index:
            total += self._index.canary_count(http, today, window)
        return total


# ------------------------------------------------------------------ site channels
def _acg_site(p: SocietyProvider, http: Http, robots: RobotsPolicy, window: Window, out: SearchOutcome) -> list[dict]:
    robots.require("https://gi.org/guidelines/")
    page = guarded(p.name, http.get_text, "https://gi.org/guidelines/")
    out.searches += 1
    items = [i for i in parse_acg_listing(page) if UC_TEXT.search(i["title"])]
    if not items:
        out.notes.append("ACG listing parsed but no UC/IBD guideline cards found (page layout may have changed)")
    return items


def _bsg_site(p: SocietyProvider, http: Http, robots: RobotsPolicy, window: Window, out: SearchOutcome) -> list[dict]:
    robots.require("https://www.bsg.org.uk/sitemap.xml")
    xml = guarded(p.name, http.get_text, "https://www.bsg.org.uk/sitemap.xml")
    out.searches += 1
    return parse_bsg_sitemap(xml)


NICE_SEED_PAGES = ("https://www.nice.org.uk/guidance/ng130",)   # UC: management. Related guidance is followed from it.


def _nice_site(p: SocietyProvider, http: Http, robots: RobotsPolicy, window: Window, out: SearchOutcome) -> list[dict]:
    items, queue, seen = [], list(NICE_SEED_PAGES), set()
    while queue and len(seen) < config.MAX_GUIDELINE_PAGES_PER_RUN:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        robots.require(url)
        page = guarded(p.name, http.get_text, url)
        out.searches += 1
        rec = parse_nice_page(page, url)
        if rec:
            items.append(rec)
        for rel in sorted(set(re.findall(r'href="(/guidance/(?:ng|ta|cg|qs)\d+)"', page))):
            full = f"https://www.nice.org.uk{rel}"
            if full not in seen and full not in queue:
                queue.append(full)
    return items


# ------------------------------------------------------------------ registry of the five bodies
def build_guideline_providers() -> list[SocietyProvider]:
    kind = ('(guideline[pt] OR "practice guideline"[pt] OR guideline[ti] OR consensus[ti] OR '
            '"clinical practice update"[ti] OR recommendations[ti])')
    return [
        SocietyProvider(name="aga", label="AGA guidelines", society="American Gastroenterological Association",
                        robots_host="gastro.org", robots_probe="https://gastro.org/guidelines/", site=None,
                        index_clause=f'{kind} AND ("Gastroenterology"[ta] OR "Clin Gastroenterol Hepatol"[ta]) AND '
                                     f'(AGA[tiab] OR "American Gastroenterological Association"[tiab])'),
        SocietyProvider(name="acg", label="ACG guidelines", society="American College of Gastroenterology",
                        robots_host="gi.org", robots_probe="https://gi.org/guidelines/", site=_acg_site,
                        index_clause=f'{kind} AND "Am J Gastroenterol"[ta]'),
        SocietyProvider(name="ecco", label="ECCO guidelines",
                        society="European Crohn's and Colitis Organisation", robots_host="www.ecco-ibd.eu",
                        robots_probe="https://www.ecco-ibd.eu/publications/ecco-guidelines-science.html", site=None,
                        index_clause=f'{kind} AND "J Crohns Colitis"[ta]'),
        SocietyProvider(name="nice", label="NICE guidance", society="National Institute for Health and Care Excellence",
                        robots_host="www.nice.org.uk", robots_probe="https://www.nice.org.uk/guidance/ng130",
                        site=_nice_site, index_clause=""),
        SocietyProvider(name="bsg", label="BSG guidelines", society="British Society of Gastroenterology",
                        robots_host="www.bsg.org.uk", robots_probe="https://www.bsg.org.uk/sitemap.xml", site=_bsg_site,
                        index_clause=f'{kind} AND "Gut"[ta] AND ("British Society of Gastroenterology"[tiab] OR BSG[tiab])'),
    ]
