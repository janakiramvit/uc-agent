"""NCBI E-utilities client (https://eutils.ncbi.nlm.nih.gov/entrez/eutils).

Used for discovery (``esearch``) and lightweight metadata (``esummary``). Abstract text is
taken from Europe PMC; this module does not fetch or store full text.
"""

from __future__ import annotations

from .http import Http

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def esearch(http: Http, term: str, *, retstart: int = 0, retmax: int = 20) -> dict:
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retstart": str(retstart),
        "retmax": str(retmax),
        "sort": "date",
    }
    data = http.get_json(f"{BASE}/esearch.fcgi", params)
    result = data.get("esearchresult", {})
    return {
        "ids": result.get("idlist", []) or [],
        "count": int(result.get("count", 0) or 0),
        "retstart": int(result.get("retstart", retstart) or retstart),
    }


def esummary(http: Http, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
    data = http.get_json(f"{BASE}/esummary.fcgi", params)
    result = data.get("result", {})
    out = []
    for uid in result.get("uids", []):
        item = result.get(uid, {})
        doi = ""
        for aid in item.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        out.append(
            {
                "provider": "pubmed",
                "pmid": uid,
                "title": (item.get("title") or "").strip().rstrip("."),
                "authors": ", ".join(a.get("name", "") for a in item.get("authors", [])),
                "journal": item.get("fulljournalname") or item.get("source") or "",
                "pubYear": (item.get("pubdate") or "")[:4],
                "publicationDate": item.get("pubdate") or "",
                "doi": doi,
                "pmcid": "",
                "nctId": "",
                "abstractText": "",
                "isOpenAccess": "N",
                "license": "",
                "canonicalUrl": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "alternateUrl": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "retrievedVia": f"NCBI E-utilities esummary (PMID {uid})",
            }
        )
    return out
