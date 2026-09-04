"""ClinicalTrials.gov API v2 client (https://clinicaltrials.gov/api/v2).

Discovery of completed / results-reported UC trials. Registry text (brief summary) is public;
no protected documents are fetched.
"""

from __future__ import annotations

from .http import Http

BASE = "https://clinicaltrials.gov/api/v2"


def _norm(study: dict) -> dict:
    ps = study.get("protocolSection", {})
    idmod = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    desc = ps.get("descriptionModule", {})
    design = ps.get("designModule", {})
    conds = ps.get("conditionsModule", {}).get("conditions", [])
    nct = idmod.get("nctId", "")
    return {
        "provider": "clinicaltrials",
        "nctId": nct,
        "title": idmod.get("officialTitle") or idmod.get("briefTitle") or "",
        "authors": (ps.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}) or {}).get("name", ""),
        "journal": "ClinicalTrials.gov registry",
        "pubYear": (status.get("completionDateStruct", {}) or {}).get("date", "")[:4],
        "publicationDate": (status.get("completionDateStruct", {}) or {}).get("date", ""),
        "doi": "",
        "pmid": "",
        "pmcid": "",
        "abstractText": (desc.get("briefSummary") or "").strip(),
        "isOpenAccess": "Y",
        "license": "ClinicalTrials.gov public registry record",
        "sourceType": "clinical trial registry record",
        "studyDesign": design.get("studyType", ""),
        "conditions": conds,
        "overallStatus": status.get("overallStatus", ""),
        "canonicalUrl": f"https://clinicaltrials.gov/study/{nct}" if nct else "",
        "alternateUrl": "",
        "retrievedVia": f"ClinicalTrials.gov API v2 /studies ({nct})",
    }


def search(http: Http, query: str, *, page_token: str | None = None, page_size: int = 20) -> dict:
    params = {
        "query.term": query,
        "pageSize": str(page_size),
        "countTotal": "true",
        "filter.overallStatus": "COMPLETED",
    }
    if page_token:
        params["pageToken"] = page_token
    data = http.get_json(f"{BASE}/studies", params)
    return {
        "records": [_norm(s) for s in data.get("studies", [])],
        "nextCursor": data.get("nextPageToken", ""),
        "hitCount": data.get("totalCount", 0),
    }
