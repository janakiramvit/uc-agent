"""Europe PMC REST client (https://www.ebi.ac.uk/europepmc/webservices/rest).

Public bibliographic metadata + abstracts only. ``resultType=core`` returns the abstract
text inline, so this is the primary discovery + abstract source.
"""

from __future__ import annotations

from typing import Optional

from .http import Http

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def _norm(result: dict) -> dict:
    return {
        "provider": "europepmc",
        "title": (result.get("title") or "").strip().rstrip("."),
        "authors": result.get("authorString") or "",
        "journal": result.get("journalTitle") or result.get("bookOrReportDetails", {}).get("publisher", ""),
        "pubYear": result.get("pubYear") or "",
        "publicationDate": result.get("firstPublicationDate") or "",
        "doi": result.get("doi") or "",
        "pmid": result.get("pmid") or "",
        "pmcid": result.get("pmcid") or "",
        "nctId": "",
        "abstractText": (result.get("abstractText") or "").strip(),
        "isOpenAccess": result.get("isOpenAccess") or "N",
        "license": result.get("license") or "",
        "sourceType": result.get("pubType") or "",
        "canonicalUrl": (
            f"https://doi.org/{result['doi']}" if result.get("doi")
            else f"https://europepmc.org/abstract/{result.get('source','MED')}/{result.get('id','')}"
        ),
        "alternateUrl": (
            f"https://pubmed.ncbi.nlm.nih.gov/{result['pmid']}/" if result.get("pmid") else ""
        ),
        "retrievedVia": f"Europe PMC REST /search ({result.get('source','MED')}:{result.get('id','')})",
        "raw_ext_id": result.get("id", ""),
        "raw_source": result.get("source", "MED"),
    }


def search(
    http: Http,
    query: str,
    *,
    cursor: str = "*",
    page_size: int = 25,
) -> dict:
    """One results page. Returns ``{records, nextCursor, hitCount}``."""
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": str(page_size),
        "cursorMark": cursor or "*",
        "sort": "P_PDATE_D desc",
    }
    data = http.get_json(f"{BASE}/search", params)
    results = (data.get("resultList") or {}).get("result", []) or []
    return {
        "records": [_norm(r) for r in results],
        "nextCursor": data.get("nextCursorMark", ""),
        "hitCount": data.get("hitCount", 0),
        "requestQuery": (data.get("request") or {}).get("queryString", query),
    }


def by_pmid(http: Http, pmid: str) -> Optional[dict]:
    res = search(http, f"EXT_ID:{pmid} AND SRC:MED", page_size=1)
    return res["records"][0] if res["records"] else None
