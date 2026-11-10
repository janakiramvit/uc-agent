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


def esearch_window(http: Http, term: str, *, mindate: str, maxdate: str, retstart: int = 0,
                   retmax: int = 25, datetype: str = "edat") -> dict:
    """Date-filtered esearch. Dates are ``YYYY/MM/DD`` (PubMed syntax - NOT reused from any other provider).

    Returns the ids, the total count and NCBI's own ``querytranslation`` / error / warning lists, which the
    provider uses to detect a query NCBI silently reinterpreted (it ignores unknown fields instead of failing).
    """
    params = {"db": "pubmed", "term": term, "retmode": "json", "retstart": str(retstart),
              "retmax": str(retmax), "sort": "pub_date", "datetype": datetype,
              "mindate": mindate, "maxdate": maxdate}
    data = http.get_json(f"{BASE}/esearch.fcgi", params)
    result = data.get("esearchresult", {}) or {}
    if data.get("error"):
        raise ValueError(f"PubMed error: {data['error']}")
    return {
        "ids": result.get("idlist", []) or [],
        "count": int(result.get("count", 0) or 0),
        "translation": result.get("querytranslation", "") or "",
        "errors": result.get("errorlist") or {},
        "warnings": result.get("warninglist") or {},
    }


def efetch(http: Http, ids: list[str]) -> list[dict]:
    """PubMed XML -> normalised records WITH abstracts (public metadata + abstract + DOI only)."""
    if not ids:
        return []
    xml_text = http.get_text(f"{BASE}/efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
    return parse_pubmed_xml(xml_text)


def parse_pubmed_xml(xml_text: str) -> list[dict]:
    from defusedxml import ElementTree as ET     # refuses entity-expansion / external entities

    root = ET.fromstring(xml_text)
    if root.tag != "PubmedArticleSet":
        raise RuntimeError("efetch returned something other than a PubmedArticleSet")
    out = []
    for art in root.findall("PubmedArticle"):
        mc = art.find("MedlineCitation")
        if mc is None:
            continue
        pmid = (mc.findtext("PMID") or "").strip()
        a = mc.find("Article")
        if a is None:
            continue
        title = "".join(a.find("ArticleTitle").itertext()).strip().rstrip(".") if a.find("ArticleTitle") is not None else ""
        abstract = " ".join(
            "".join(t.itertext()).strip() for t in a.findall("Abstract/AbstractText")
        ).strip()
        jr = a.find("Journal")
        journal = (jr.findtext("Title") or "") if jr is not None else ""
        pd = jr.find("JournalIssue/PubDate") if jr is not None else None
        year = (pd.findtext("Year") or "") if pd is not None else ""
        medline = (pd.findtext("MedlineDate") or "") if pd is not None else ""
        pubdate = "-".join(x for x in (year, pd.findtext("Month") or "", pd.findtext("Day") or "") if x) if pd is not None else ""
        authors = ", ".join(
            f"{au.findtext('LastName') or ''} {au.findtext('Initials') or ''}".strip()
            for au in a.findall("AuthorList/Author") if au.findtext("LastName")
        )
        doi = pmcid = ""
        for aid in art.findall("PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = (aid.text or "").strip()
            elif aid.get("IdType") == "pmc":
                pmcid = (aid.text or "").strip()
        if not doi:
            for el in a.findall("ELocationID"):
                if el.get("EIdType") == "doi":
                    doi = (el.text or "").strip()
        ptypes = [(pt.text or "").strip() for pt in a.findall("PublicationTypeList/PublicationType")]
        out.append({
            "provider": "pubmed", "pmid": pmid, "title": title, "authors": authors, "journal": journal,
            "pubYear": year or medline[:4], "publicationDate": pubdate or medline, "doi": doi, "pmcid": pmcid,
            "nctId": "", "abstractText": abstract, "isOpenAccess": "Y" if pmcid else "N", "license": "",
            "canonicalUrl": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "alternateUrl": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "retrievedVia": f"NCBI E-utilities efetch (PMID {pmid})", "publicationTypes": ptypes,
            "isPreprint": False,
        })
    return out
