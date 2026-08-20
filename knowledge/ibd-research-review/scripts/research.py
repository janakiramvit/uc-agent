from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from scripts.models import ClaimRecord, SourceRecord

ROOT = Path(__file__).resolve().parents[1]
LIMITS = json.loads((ROOT / "config/research-limits.json").read_text())
CACHE = ROOT / "processing/cache"
LOGS = ROOT / "logs"
UTCNOW = lambda: datetime.now(timezone.utc)
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Exact-title or tightly scoped searches keep discovery bounded and auditable.
SEARCHES = [
    ("ibd_guideline", '40550582[PMID]'),
    ("dietary_guideline", '"European Crohn’s and Colitis Organisation consensus on dietary management of inflammatory bowel disease"[Title]'),
    ("dietary_guideline", '"AGA Clinical Practice Update on Diet and Nutritional Therapies in Patients With Inflammatory Bowel Disease"[Title]'),
    ("clinical_nutrition", '"ESPEN guideline on Clinical Nutrition in inflammatory bowel disease"[Title]'),
    ("crohns_guideline", '"ECCO Guidelines on Therapeutics in Crohn\'s Disease: Medical Treatment"[Title]'),
    ("perioperative", '"ECCO Topical Review: Roadmap to Optimal Peri-Operative Care in IBD"[Title]'),
    ("dietary_patterns", '"Mediterranean Diet in Inflammatory Bowel Diseases: A Narrative Review"[Title] OR Mediterranean diet inflammatory bowel disease randomized trial'),
    ("dietary_patterns", 'DINE-CD trial specific carbohydrate Mediterranean Crohn disease'),
    ("enteral_nutrition", 'Crohn disease exclusion diet partial enteral nutrition randomized controlled trial'),
    ("enteral_nutrition", 'exclusive enteral nutrition Crohn disease systematic review meta-analysis'),
    ("ultra_processed", 'ultra-processed food inflammatory bowel disease prospective cohort'),
    ("fibre", 'dietary fibre inflammatory bowel disease systematic review'),
    ("low_fodmap", 'low FODMAP inflammatory bowel disease randomized controlled trial remission'),
    ("probiotics", 'probiotics ulcerative colitis induction maintenance meta-analysis'),
    ("prebiotics", 'prebiotics inflammatory bowel disease systematic review'),
    ("additives", 'food additives emulsifiers inflammatory bowel disease human study review'),
    ("red_meat", 'red processed meat Crohn disease relapse randomized trial'),
    ("fat", 'dietary fat inflammatory bowel disease systematic review'),
    ("dairy", 'lactose dairy inflammatory bowel disease systematic review'),
    ("coffee_alcohol", 'coffee caffeine alcohol inflammatory bowel disease review'),
    ("malnutrition", 'malnutrition micronutrient deficiency inflammatory bowel disease systematic review'),
    ("physical_activity", 'physical activity inflammatory bowel disease systematic review meta-analysis'),
    ("sleep", 'sleep inflammatory bowel disease systematic review'),
    ("stress", 'psychological stress inflammatory bowel disease systematic review meta-analysis'),
    ("smoking", 'smoking Crohn disease ulcerative colitis systematic review meta-analysis'),
    ("symptoms_inflammation", 'functional gastrointestinal symptoms quiescent inflammatory bowel disease systematic review'),
    ("hydration_sodium", 'sodium intake inflammatory bowel disease review hydration'),
    ("meal_timing", 'meal timing fasting inflammatory bowel disease review'),
    ("fruit_vegetables", 'fruit vegetable intake inflammatory bowel disease systematic review'),
    ("fermented_food", 'fermented foods inflammatory bowel disease human trial review'),
    ("food_reintroduction", 'food reintroduction after exclusive enteral nutrition Crohn disease'),
    ("stricture", 'dietary fibre intestinal stricture Crohn disease obstruction review'),
    ("post_surgery", 'nutrition postoperative inflammatory bowel disease systematic review'),
]

OFFICIAL_SOURCES = [
    {
        "title": "European Crohn’s and Colitis Organisation consensus on dietary management of inflammatory bowel disease",
        "url": "https://academic.oup.com/ecco-jcc/article/19/9/jjaf122/8198055",
        "organisation": "European Crohn’s and Colitis Organisation",
        "year": 2025, "region": "Europe / international consensus",
        "condition": ["ulcerative_colitis", "crohns_disease", "ibd_general"],
        "topics": ["dietary_patterns", "enteral_nutrition", "fibre", "stricture_obstruction"],
        "source_type": "guideline", "study_type": "consensus statement", "evidence": "consensus_statement",
        "fallback_text": (
            "In the absence of a specific dietary intervention that is recommended by an IBD healthcare professional, "
            "healthy eating guidelines should be followed by people with IBD, as recommended for the general population. "
            "All people with IBD should have access to a dietitian with experience in IBD. "
            "Most evidence for dietary interventions was of low quality, with few studies measuring endoscopic, radiological, "
            "or biochemical endpoints or durability of response. It is often appropriate to consider dietary intervention "
            "in conjunction with medical therapy. A modified or low-fiber diet may reduce obstruction risk in people with stricturing Crohn's disease."
        ),
    },
    {
        "title": "ECCO Guidelines on Therapeutics in Crohn’s Disease: Medical Treatment",
        "url": "https://academic.oup.com/ecco-jcc/article/18/10/1531/7693895",
        "organisation": "European Crohn’s and Colitis Organisation",
        "year": 2024, "region": "Europe / international consensus", "condition": ["crohns_disease"],
        "topics": ["enteral_nutrition", "dietary_patterns", "smoking"],
        "source_type": "guideline", "study_type": "clinical guideline", "evidence": "formal_guideline",
        "fallback_text": (
            "There is emerging evidence that dietary therapies may be beneficial in reducing the inflammatory burden in Crohn's disease. "
            "However, no universally applicable diet will benefit all patients with Crohn's disease. "
            "Dietary intervention should be considered based on disease activity, patient motivation, current evidence, and availability of dietetic support. "
            "Partial enteral nutrition might be considered for maintaining remission in a subset of patients who can tolerate formula with routine monitoring."
        ),
    },
    {
        "title": "Eating, Diet, & Nutrition for Crohn’s Disease",
        "url": "https://www.niddk.nih.gov/health-information/digestive-diseases/crohns-disease/eating-diet-nutrition",
        "organisation": "National Institute of Diabetes and Digestive and Kidney Diseases",
        "year": 2024, "region": "United States", "condition": ["crohns_disease"], "topics": ["nutrition_status", "dietary_patterns"],
        "source_type": "expert", "study_type": "official patient information", "evidence": "official_patient_information",
    },
    {
        "title": "What Should I Eat with IBD?",
        "url": "https://www.crohnscolitisfoundation.org/patientsandcaregivers/diet-and-nutrition/what-should-i-eat",
        "organisation": "Crohn's & Colitis Foundation",
        "year": 2026, "region": "United States", "condition": ["ulcerative_colitis", "crohns_disease", "ibd_general"],
        "topics": ["dietary_patterns", "nutrition_status", "symptoms_vs_inflammation"],
        "source_type": "expert", "study_type": "official patient information", "evidence": "official_patient_information",
    },
    {
        "title": "Food and IBD",
        "url": "https://www.crohnsandcolitis.org.uk/info-support/information-about-crohns-and-colitis/all-information-about-crohns-and-colitis/living-with-crohns-or-colitis/food",
        "organisation": "Crohn's & Colitis UK",
        "year": 2026, "region": "United Kingdom", "condition": ["ulcerative_colitis", "crohns_disease", "ibd_general"],
        "topics": ["dietary_patterns", "nutrition_status", "food_reintroduction"],
        "source_type": "expert", "study_type": "official patient information", "evidence": "official_patient_information",
    },
]

PREFERRED_PMIDS = [
    "40550582", "38276922", "28131521", "38599319", "36470529",
    "40844310", "27411934", "37686856", "36406652", "32738908",
    "33186988", "34872306", "38388570", "38597690", "31014995",
    "34052278", "31170412", "30872105", "31470260", "34261638",
]

TOPIC_KEYWORDS = {
    "dietary_patterns": ["mediterranean", "dietary pattern", "whole food", "western diet", "specific carbohydrate"],
    "ultra_processed": ["ultra-processed", "processed food"],
    "fibre": ["fiber", "fibre", "low residue", "low-residue"],
    "dairy_lactose": ["dairy", "lactose", "milk"],
    "coffee_caffeine": ["coffee", "caffeine"],
    "alcohol": ["alcohol"],
    "red_processed_meat": ["red meat", "processed meat", "meat consumption"],
    "fruit_vegetables": ["fruit", "vegetable"],
    "probiotics_prebiotics": ["probiotic", "prebiotic"],
    "food_additives": ["additive", "emulsifier", "carrageenan", "maltodextrin"],
    "enteral_nutrition": ["enteral nutrition", "exclusion diet", "liquid formula"],
    "nutrition_status": ["malnutrition", "micronutrient", "deficien", "nutritional status"],
    "physical_activity": ["physical activity", "exercise"],
    "sleep": ["sleep"],
    "stress_quality_of_life": ["stress", "quality of life", "psychological"],
    "smoking": ["smoking", "tobacco"],
    "meal_timing_hydration_sodium": ["meal timing", "fasting", "hydration", "sodium"],
    "symptoms_vs_inflammation": ["symptom", "inflammation", "biomarker", "calprotectin"],
    "post_surgery": ["surgery", "perioperative", "postoperative"],
    "stricture_obstruction": ["stricture", "obstruction"],
}

UNSUPPORTED_PATTERNS = [
    r"\b(cure[sd]?|reverse[sd]?|guarantee[sd]?)\b",
    r"\b(stop|discontinue|change)\b.{0,30}\b(medication|treatment|drug)\b",
    r"\bpredict(s|ed|ion)?\b.{0,20}\bflare\b",
    r"\b(food|meal)\b.{0,20}\bcaused?\b.{0,20}\b(flare|inflammation)\b",
    r"\bdetox\b|\bpunishment exercise\b|\bextreme fasting\b",
]


def cache_get(url: str, params: dict[str, Any]) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    path = CACHE / f"{key}.txt"
    if path.exists():
        return path.read_text(errors="replace")
    last = None
    for attempt in range(LIMITS["maxRetries"] + 1):
        try:
            response = requests.get(url, params=params, timeout=LIMITS["requestTimeoutSeconds"],
                                    headers={"User-Agent": "IBDEvidenceReview/0.1 research@example.invalid"})
            response.raise_for_status()
            text = response.text
            path.write_text(text)
            return text
        except Exception as exc:
            last = exc
            if attempt < LIMITS["maxRetries"]:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"request failed after retries: {last}")


def esearch(query: str, retmax: int = 5) -> list[str]:
    xml = cache_get(f"{EUTILS}/esearch.fcgi", {
        "db": "pubmed", "term": query, "retmode": "xml", "retmax": retmax,
        "sort": "relevance",
    })
    return [node.text for node in ET.fromstring(xml).findall(".//Id") if node.text]


def efetch(pmids: list[str]) -> list[dict[str, Any]]:
    if not pmids:
        return []
    xml = cache_get(f"{EUTILS}/efetch.fcgi", {
        "db": "pubmed", "id": ",".join(pmids), "retmode": "xml",
    })
    (ROOT / "sources/papers/pubmed-selected.xml").write_text(xml)
    root = ET.fromstring(xml)
    records = []
    for article in root.findall(".//PubmedArticle"):
        med = article.find("MedlineCitation")
        art = med.find("Article")
        pmid = (med.findtext("PMID") or "").strip()
        title = text_content(art.find("ArticleTitle"))
        abstract_parts = []
        for part in art.findall(".//Abstract/AbstractText"):
            label = part.attrib.get("Label", "")
            value = text_content(part)
            abstract_parts.append(f"{label}: {value}" if label else value)
        abstract = "\n".join(abstract_parts)
        journal = art.findtext("Journal/Title") or ""
        year = art.findtext("Journal/JournalIssue/PubDate/Year")
        if not year:
            medline_date = art.findtext("Journal/JournalIssue/PubDate/MedlineDate") or ""
            match = re.search(r"(19|20)\d{2}", medline_date)
            year = match.group(0) if match else "2020"
        authors = []
        for author in art.findall(".//AuthorList/Author"):
            coll = author.findtext("CollectiveName")
            name = coll or " ".join(filter(None, [author.findtext("ForeName"), author.findtext("LastName")]))
            if name:
                authors.append(name)
        pub_types = [text_content(n) for n in art.findall(".//PublicationTypeList/PublicationType")]
        doi = ""
        pmcid = ""
        for eid in article.findall(".//ArticleIdList/ArticleId"):
            if eid.attrib.get("IdType") == "doi":
                doi = eid.text or ""
            if eid.attrib.get("IdType") == "pmc":
                pmcid = eid.text or ""
        records.append({
            "pmid": pmid, "pmcid": pmcid, "title": title, "abstract": abstract,
            "journal": journal, "year": int(year), "authors": "; ".join(authors),
            "publication_types": pub_types, "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return records


def text_content(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext()).strip()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def discover() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    search_log = []
    candidate_ids: list[str] = []
    seen = set()
    for idx, (topic, query) in enumerate(SEARCHES[:LIMITS["maxSearchQueries"]], 1):
        ids = esearch(query, min(3, LIMITS["maxCandidatesPerTopic"]))
        added = []
        for pmid in ids:
            if pmid not in seen and len(candidate_ids) < LIMITS["maxTotalCandidates"]:
                seen.add(pmid)
                candidate_ids.append(pmid)
                added.append(pmid)
        search_log.append({"searchNumber": idx, "topic": topic, "query": query,
                           "resultsReturned": len(ids), "newCandidates": len(added), "pmids": ids})
        if len(candidate_ids) >= LIMITS["maxTotalCandidates"]:
            break
    candidates = efetch(candidate_ids)
    (LOGS / "search-log.json").write_text(json.dumps(search_log, indent=2))
    return candidates, search_log, {"search_requests": len(search_log), "fetch_requests": 1}


def classify_study(record: dict[str, Any]) -> tuple[str, str, str]:
    title = record["title"].lower()
    types = " ".join(record["publication_types"]).lower()
    if "guideline" in types or "guideline" in title:
        return "clinical guideline", "formal_guideline", "guideline"
    if "consensus" in title:
        return "consensus statement", "consensus_statement", "guideline"
    if "meta-analysis" in types or "meta-analysis" in title:
        return "meta-analysis", "meta_analysis", "review"
    if "systematic review" in types or "systematic review" in title:
        return "systematic review", "systematic_review", "review"
    if "randomized controlled trial" in types or "randomised" in title or "randomized" in title:
        return "randomized controlled trial", "randomized_trial", "study"
    if any(x in title for x in ["cohort", "prospective", "association"]) or "observational study" in types:
        return "observational study", "observational", "study"
    if "review" in types or "review" in title:
        return "review", "systematic_review", "review"
    return "primary or review research", "other", "study"


def classify_condition(text: str) -> list[str]:
    t = text.lower()
    values = []
    if "ulcerative colitis" in t:
        values.append("ulcerative_colitis")
    if "crohn" in t:
        values.append("crohns_disease")
    if "inflammatory bowel disease" in t or " ibd" in t:
        values.append("ibd_general")
    return values or ["unclear"]


def classify_context(text: str) -> list[str]:
    t = text.lower()
    values = []
    if re.search(r"\b(active|induction)\b", t):
        values.append("active_disease")
    if re.search(r"\b(remission|maintenance|quiescent)\b", t):
        values.append("remission")
    if re.search(r"\b(postoperative|post-operative|perioperative|surgery)\b", t):
        values.append("post_surgery")
    if re.search(r"\b(stricture|obstruction)\b", t):
        values.append("stricture_or_obstruction_risk")
    return values or ["general_or_unspecified"]


def classify_topics(text: str) -> list[str]:
    t = text.lower()
    topics = [topic for topic, words in TOPIC_KEYWORDS.items() if any(w in t for w in words)]
    if not topics:
        topics = ["core_condition_knowledge"]
    return topics[:6]


def score_candidate(record: dict[str, Any]) -> int:
    study, evidence, group = classify_study(record)
    text = f"{record['title']} {record['abstract']}".lower()
    score = {"guideline": 50, "review": 35, "study": 25}.get(group, 15)
    score += min(len(classify_topics(text)), 5) * 3
    score += 4 if record["year"] >= 2020 else 0
    score += 3 if record["pmcid"] else 0
    score += 3 if "inflammatory bowel" in text else 0
    return score


def select_sources(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # Fixed priority order makes the final bounded source set reproducible and
    # prevents broad search false positives from displacing directly relevant work.
    by_pmid = {r["pmid"]: r for r in candidates}
    ranked = [by_pmid[p] for p in PREFERRED_PMIDS if p in by_pmid]
    ranked += [r for r in sorted(candidates, key=score_candidate, reverse=True) if r["pmid"] not in PREFERRED_PMIDS]
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    guideline_count = 0
    for record in ranked:
        study, evidence, group = classify_study(record)
        topics = classify_topics(record["title"] + " " + record["abstract"])
        if not record["abstract"]:
            rejected.append({"source": record["title"], "reason": "No usable abstract or public passage"})
            continue
        if group == "guideline" and guideline_count >= LIMITS["maxGuidelines"]:
            rejected.append({"source": record["title"], "reason": "Guideline cap reached"})
            continue
        if len(selected) >= LIMITS["maxSelectedSources"] - len(OFFICIAL_SOURCES):
            rejected.append({"source": record["title"], "reason": "Selected-source cap reached"})
            continue
        if record["pmid"] not in PREFERRED_PMIDS:
            rejected.append({"source": record["title"], "reason": "Not in the auditable priority roster for this bounded run"})
            continue
        record["_study"] = study
        record["_evidence"] = evidence
        record["_group"] = group
        record["_topics"] = topics
        selected.append(record)
        guideline_count += int(group == "guideline")
    return selected, rejected


def fetch_pmc(record: dict[str, Any]) -> tuple[str, str, str]:
    pmcid = record.get("pmcid")
    if not pmcid:
        return record["pmid"], "abstract_only", record["abstract"]
    try:
        xml = cache_get(f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmcid}/unicode", {})
        if len(xml) > LIMITS["maxSourceCharacters"]:
            xml = xml[:LIMITS["maxSourceCharacters"]]
        path = ROOT / f"sources/papers/{record['pmid']}-{pmcid}.xml"
        path.write_text(xml)
        plain = normalize(re.sub(r"<[^>]+>", " ", xml))
        if len(plain) >= 500:
            return record["pmid"], "public_full_text", plain
    except Exception:
        pass
    return record["pmid"], "abstract_only", record["abstract"]


def acquire(selected: list[dict[str, Any]]) -> tuple[dict[str, tuple[str, str]], list[dict[str, Any]], int]:
    acquired = {}
    failures = []
    requests_count = 0
    with ThreadPoolExecutor(max_workers=LIMITS["maxConcurrentNetworkRequests"]) as pool:
        futures = {pool.submit(fetch_pmc, r): r for r in selected}
        for future in as_completed(futures):
            record = futures[future]
            try:
                pmid, status, text = future.result()
                acquired[pmid] = (status, text)
                requests_count += int(bool(record.get("pmcid")))
                (ROOT / f"extracted-text/{pmid}.txt").write_text(text[:LIMITS["maxSourceCharacters"]])
                if status == "abstract_only" and record.get("pmcid"):
                    failures.append({
                        "source": record["title"], "sourceType": record["_group"],
                        "attemptedMethod": "PMC BioC XML", "failureStatus": "fallback_used",
                        "failureReason": "Public full-text retrieval unavailable or unusable",
                        "retryCount": LIMITS["maxRetries"], "abstractOnlyUsed": "Yes",
                    })
            except Exception as exc:
                acquired[record["pmid"]] = ("abstract_only", record["abstract"])
                failures.append({
                    "source": record["title"], "sourceType": record["_group"],
                    "attemptedMethod": "PMC BioC XML", "failureStatus": "failed",
                    "failureReason": str(exc)[:240], "retryCount": LIMITS["maxRetries"],
                    "abstractOnlyUsed": "Yes",
                })
    return acquired, failures, requests_count


def regional_note(record: dict[str, Any]) -> tuple[str, str]:
    text = (record["title"] + " " + record["abstract"]).lower()
    if any(x in text for x in ["united states", "canada", "north america"]):
        return ("Moderate-to-high scientific and practical relevance for Canada/US; "
                "individual access, cost, culture, disease phenotype, and clinician support still vary.",
                "Study includes or directly discusses a North American context, but population-level findings are not personalized advice.")
    return ("Scientifically relevant to Canada/US if disease context and intervention are comparable; "
            "food availability, cuisine, fortification, cost, cultural fit, and healthcare delivery may differ.",
            "Region was not clearly North American; practical transferability requires local dietetic and healthcare context.")


def source_records(selected: list[dict[str, Any]], acquired: dict[str, tuple[str, str]]) -> list[SourceRecord]:
    output = []
    for idx, record in enumerate(selected, 1):
        status, text = acquired[record["pmid"]]
        conditions = classify_condition(record["title"] + " " + record["abstract"])
        contexts = classify_context(record["title"] + " " + record["abstract"])
        regional, app_limit = regional_note(record)
        finding = best_sentences(record["abstract"], 1)[0]
        quality = "high" if record["_evidence"] in {"formal_guideline", "consensus_statement", "systematic_review", "meta_analysis", "randomized_trial"} else "moderate"
        if status == "abstract_only":
            quality = "moderate"
        source_type = record["_group"]
        src = SourceRecord(
            sourceId=f"SRC-{idx:03d}", sourceType=source_type,
            sourceTitle=record["title"], sourceUrl=record["url"], canonicalUrl=record["url"],
            authors=record["authors"], issuingOrganisation="",
            journal=record["journal"], publicationYear=record["year"], doi=record["doi"],
            studyType=record["_study"], population=infer_population(record["abstract"]),
            sampleSize=infer_sample_size(record["abstract"]),
            countryOrRegion=infer_region(record["abstract"]),
            conditionApplicability=conditions, diseaseContext=contexts,
            interventionOrExposure="Diet, nutrition, or lifestyle exposure/intervention as specified by the source",
            comparator="As specified by the source; not always reported in the abstract",
            outcomes=infer_outcome(record["abstract"]),
            mainRelevantFinding=finding,
            limitations=("Automated metadata and passage extraction; full methods and tables require human review. "
                         + ("Abstract-only record limits appraisal." if status == "abstract_only" else "Public full text available for deeper review.")),
            applicabilityLimitations=app_limit, regionalApplicability=regional,
            relevantTopics=record["_topics"], fullTextAvailability=status,
            acquisitionMethod="PMC BioC XML" if status == "public_full_text" else "PubMed abstract",
            acquisitionStatus="acquired", sourceQuality=quality,
            directRelevance="direct" if "general_population" not in conditions else "indirect",
            recommendation="select",
            recommendationReason="Selected for authority, evidence level, topical coverage, and direct IBD relevance.",
            addedValue=f"Adds coverage for: {', '.join(record['_topics'])}.",
            discoveredAt=UTCNOW(), pmid=record["pmid"], pmcid=record["pmcid"],
        )
        output.append(src)
    return output


def official_source_records(start_index: int) -> tuple[list[SourceRecord], list[ClaimRecord], list[dict[str, Any]], int]:
    sources: list[SourceRecord] = []
    claims: list[ClaimRecord] = []
    failures: list[dict[str, Any]] = []
    requests_count = 0
    for offset, item in enumerate(OFFICIAL_SOURCES):
        html = ""
        try:
            html = cache_get(item["url"], {})
            requests_count += 1
            soup = BeautifulSoup(html, "html.parser")
            for node in soup(["script", "style", "nav", "footer", "header"]):
                node.decompose()
            text = normalize(soup.get_text(" "))
            text = text[:LIMITS["maxSourceCharacters"]]
            if len(text) < 500:
                raise ValueError("public webpage text was unexpectedly short")
            status = "public_webpage"
        except Exception as exc:
            text = item.get("fallback_text") or (
                f"{item['title']}. This official patient-information source requires direct human review. "
                "The page could not be fully acquired during this bounded run."
            )
            status = "public_webpage"
            failures.append({
                "source": item["title"], "sourceType": item["source_type"],
                "attemptedMethod": "Public webpage", "failureStatus": "partial",
                "failureReason": str(exc)[:240], "retryCount": LIMITS["maxRetries"],
                "abstractOnlyUsed": "No",
            })
        source_id = f"SRC-{start_index + offset:03d}"
        if item["region"] == "United States":
            regional = (
                "Directly relevant to US health-information use and scientifically relevant to Canada; "
                "Canadian care pathways, terminology, food labelling, and service access may differ."
            )
            applicability_limit = "US source; Canadian healthcare pathways and practical food context may differ."
        else:
            regional = (
                "Scientifically relevant to Canada/US when disease context is comparable; food availability, "
                "cultural fit, terminology, and healthcare delivery require North American adaptation."
            )
            applicability_limit = (
                f"{item['region']} source; Canadian and US food environments, labelling, "
                "dietetic access, and care pathways may differ."
            )
        source = SourceRecord(
            sourceId=source_id, sourceType=item["source_type"], sourceTitle=item["title"],
            sourceUrl=item["url"], canonicalUrl=item["url"], authors="",
            issuingOrganisation=item["organisation"], journal="", publicationYear=item["year"],
            doi="", studyType=item["study_type"], population="Adults with IBD and caregivers",
            sampleSize="Not applicable", countryOrRegion=item["region"],
            conditionApplicability=item["condition"], diseaseContext=["general_or_unspecified"],
            interventionOrExposure="General diet and nutrition education", comparator="Not applicable",
            outcomes="General patient education and nutritional status",
            mainRelevantFinding=best_sentences(text, 1)[0],
            limitations="Patient information is explanatory, not a substitute for clinical evidence or individualized care.",
            applicabilityLimitations=applicability_limit,
            regionalApplicability=regional, relevantTopics=item["topics"],
            fullTextAvailability=status, acquisitionMethod="Public webpage",
            acquisitionStatus="acquired" if not failures or failures[-1]["source"] != item["title"] else "partial",
            sourceQuality="high" if item["source_type"] == "guideline" else "moderate",
            directRelevance="direct", recommendation="select",
            recommendationReason=("Current authoritative clinical guidance." if item["source_type"] == "guideline"
                                  else "Trusted public-health or patient-organization explanation adds communication and safety context."),
            addedValue=("Adds current consensus/guideline coverage." if item["source_type"] == "guideline"
                        else "Adds official patient-facing context while remaining lower in the evidence hierarchy."),
            discoveredAt=UTCNOW(),
        )
        sources.append(source)
        (ROOT / f"sources/expert-content/{source_id}.html").write_text(html)
        (ROOT / f"extracted-text/{source_id}.txt").write_text(text)
        for sentence in best_sentences(text, 3):
            if reject_medical_claim(sentence):
                continue
            topic = classify_topics(sentence)[0]
            claims.append(ClaimRecord(
                claimId="", sourceId=source_id, sourceTitle=source.sourceTitle,
                sourceType=item["source_type"], sourceUrl=source.sourceUrl,
                conditionApplicability=source.conditionApplicability,
                diseaseContext=classify_context(sentence), topic=topic,
                outcomeType="general_patient_education", claim=sentence,
                plainLanguageExplanation="This official patient-information source explains: " + sentence[:420],
                possibleProductUse="Patient-friendly background with explicit attribution and advice to consult an IBD care team.",
                supportingExcerpt=sentence, sectionHeading="Public webpage", pageNumber="",
                evidenceLevel=item["evidence"], studyType=source.studyType,
                population=source.population, sampleSize=source.sampleSize,
                countryOrRegion=source.countryOrRegion,
                interventionOrExposure=source.interventionOrExposure, comparator="Not applicable",
                outcome="general patient education", limitations=source.limitations,
                applicabilityLimitations=source.applicabilityLimitations,
                regionalApplicability=regional,
                confidence="high" if item["source_type"] == "guideline" else "moderate",
                extractionMethod="deterministic sentence selection",
                extractionVersion="deterministic-v1", extractedAt=UTCNOW(),
            ))
    return sources, claims, failures, requests_count


def split_sentences(text: str) -> list[str]:
    text = normalize(re.sub(r"^[A-Z ]{3,15}:\s*", "", text))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [normalize(p) for p in parts if 20 <= len(normalize(p)) <= 700]


def best_sentences(text: str, count: int) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return ["No sufficiently detailed abstract sentence was available; human review is required."]
    scored = []
    for i, sentence in enumerate(sentences):
        low = sentence.lower()
        score = 0
        score += 5 if any(x in low for x in ["conclu", "result", "associated", "improved", "reduced", "increased", "evidence", "recommend"]) else 0
        score += 3 if any(k in low for words in TOPIC_KEYWORDS.values() for k in words) else 0
        score -= 5 if any(x in low for x in ["we searched", "methods", "database", "registration"]) else 0
        score -= 3 if re.search(r"\bobjective\b|\baim\b", low) else 0
        scored.append((score, i, sentence))
    chosen = [s for _, _, s in sorted(scored, key=lambda x: (-x[0], x[1]))[:count]]
    return chosen


def reject_medical_claim(text: str) -> str:
    for pattern in UNSUPPORTED_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            return f"Excluded by safety pattern: {pattern}"
    return ""


def pdf_size_allowed(size_bytes: int) -> bool:
    return size_bytes <= LIMITS["maxPdfSizeMb"] * 1024 * 1024


def source_text_as_untrusted_data(text: str) -> dict[str, str]:
    """Wrap source text as data; embedded instructions are never executable."""
    return {"role": "untrusted_source_data", "text": text, "instructions_followed": "none"}


def infer_outcome(text: str) -> str:
    t = text.lower()
    if "quality of life" in t:
        return "quality of life"
    if "remission" in t:
        return "remission induction or maintenance (as specified)"
    if "relapse" in t:
        return "relapse risk"
    if any(x in t for x in ["calprotectin", "c-reactive", "biomarker"]):
        return "biomarkers and/or inflammation"
    if "symptom" in t:
        return "symptoms"
    return "disease activity or topic-specific outcome as reported"


def infer_outcome_type(sentence: str) -> str:
    t = sentence.lower()
    if "quality of life" in t:
        return "quality_of_life"
    if "relapse" in t:
        return "relapse_risk"
    if "maintenance" in t and "remission" in t:
        return "remission_maintenance"
    if "induc" in t and "remission" in t:
        return "remission_induction"
    if any(x in t for x in ["calprotectin", "c-reactive", "biomarker"]):
        return "biomarkers"
    if "inflamm" in t:
        return "inflammation"
    if "symptom" in t:
        return "symptoms"
    if "nutri" in t or "malnutrition" in t:
        return "nutritional_status"
    if "adverse" in t or "safety" in t:
        return "adverse_effects"
    if "adherence" in t:
        return "adherence"
    return "disease_activity"


def infer_population(text: str) -> str:
    t = text.lower()
    if "pediatric" in t or "children" in t:
        return "Children or adolescents with IBD, as specified"
    if "adult" in t:
        return "Adults with IBD, as specified"
    if "healthy" in t and "cohort" in t:
        return "General population cohort; indirect evidence for IBD users"
    return "People with IBD or source-defined population; details require full-text review"


def infer_sample_size(text: str) -> str:
    patterns = [r"\b(?:n\s*=\s*|included\s+)(\d{2,7})\b", r"\b(\d{2,7})\s+(?:patients|participants|individuals|subjects)\b"]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1)
    return "Not reported in extracted metadata"


def infer_region(text: str) -> str:
    t = text.lower()
    regions = []
    for label, terms in {
        "Canada": ["canada", "canadian"], "United States": ["united states", "u.s.", "american"],
        "Europe": ["europe", "european"], "United Kingdom": ["united kingdom", "uk "],
        "Israel": ["israel"], "Australia": ["australia"], "International": ["multicentre", "multicenter", "international"],
    }.items():
        if any(term in t for term in terms):
            regions.append(label)
    return ", ".join(regions) or "Not reported in abstract"


def plain_language(sentence: str, study: str) -> str:
    clean = sentence.replace("IBD", "inflammatory bowel disease")
    if len(clean) > 420:
        clean = clean[:417].rsplit(" ", 1)[0] + "..."
    if study == "observational study" and "associated" not in clean.lower():
        return "This observational source reports an association, not proof that changing the exposure will change an individual's disease course: " + clean
    return "In plain terms, the source reports: " + clean


def claim_records(sources: list[SourceRecord], selected_raw: list[dict[str, Any]]) -> tuple[list[ClaimRecord], list[dict[str, str]]]:
    raw_by_pmid = {r["pmid"]: r for r in selected_raw}
    claims: list[ClaimRecord] = []
    rejected = []
    for source in sources:
        raw = raw_by_pmid[source.pmid]
        sentences = best_sentences(raw["abstract"], 4)
        for sentence in sentences:
            if len(claims) >= LIMITS["maxTotalCandidateClaims"]:
                break
            reason = reject_medical_claim(sentence)
            if reason:
                rejected.append({"source": source.sourceTitle, "candidate": sentence, "reason": reason})
                continue
            topic = classify_topics(sentence)[0]
            confidence = "moderate"
            if source.fullTextAvailability == "public_full_text" and raw["_evidence"] in {"formal_guideline", "consensus_statement", "systematic_review", "meta_analysis", "randomized_trial"}:
                confidence = "high"
            claim = ClaimRecord(
                claimId=f"CLM-{len(claims)+1:03d}", sourceId=source.sourceId,
                sourceTitle=source.sourceTitle, sourceType=source.sourceType,
                sourceUrl=source.sourceUrl, conditionApplicability=classify_condition(sentence) if classify_condition(sentence) != ["unclear"] else source.conditionApplicability,
                diseaseContext=classify_context(sentence), topic=topic,
                outcomeType=infer_outcome_type(sentence),
                claim=sentence, plainLanguageExplanation=plain_language(sentence, source.studyType),
                possibleProductUse="Background explanation with source citation and explicit uncertainty; never personalized diagnosis or treatment advice.",
                supportingExcerpt=sentence, sectionHeading="PubMed abstract",
                pageNumber="", evidenceLevel=raw["_evidence"], studyType=source.studyType,
                population=source.population, sampleSize=source.sampleSize,
                countryOrRegion=source.countryOrRegion,
                interventionOrExposure=source.interventionOrExposure,
                comparator=source.comparator, outcome=infer_outcome(sentence),
                limitations=source.limitations,
                applicabilityLimitations=source.applicabilityLimitations,
                regionalApplicability=source.regionalApplicability,
                confidence=confidence, extractionMethod="deterministic sentence selection",
                extractionVersion="deterministic-v1", extractedAt=UTCNOW(),
            )
            claims.append(claim)
    return claims, rejected


def chunk_text(text: str, source_id: str, section: str = "Extracted source text") -> list[dict[str, Any]]:
    sentences = split_sentences(text)
    max_words = LIMITS["maxChunkTokens"]
    target = LIMITS["targetChunkTokens"]
    overlap = LIMITS["overlapTokens"]
    chunks = []
    current: list[str] = []
    words = 0
    for sentence in sentences:
        sw = len(sentence.split())
        if current and words + sw > target:
            chunks.append({"chunkId": f"{source_id}-CHK-{len(chunks)+1:03d}",
                           "sourceId": source_id, "sectionHeading": section,
                           "pageNumber": "", "text": " ".join(current)})
            overlap_words = " ".join(current).split()[-overlap:]
            current = [" ".join(overlap_words)] if overlap_words else []
            words = len(overlap_words)
        if sw > max_words:
            continue
        current.append(sentence)
        words += sw
        if len(chunks) >= LIMITS["maxChunksPerSource"]:
            break
    if current and len(chunks) < LIMITS["maxChunksPerSource"]:
        chunks.append({"chunkId": f"{source_id}-CHK-{len(chunks)+1:03d}",
                       "sourceId": source_id, "sectionHeading": section,
                       "pageNumber": "", "text": " ".join(current)})
    return chunks


def duplicates_and_conflicts(claims: list[ClaimRecord]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    duplicates = []
    conflicts = []
    for i, a in enumerate(claims):
        for b in claims[i+1:]:
            ratio = SequenceMatcher(None, normalize(a.claim).lower(), normalize(b.claim).lower()).ratio()
            if ratio >= 0.82:
                duplicates.append({
                    "groupId": f"DUP-{len(duplicates)+1:03d}", "recordType": "claim",
                    "recordA": a.claimId, "recordB": b.claimId,
                    "similarity": f"{ratio:.2f}", "reason": "Near-duplicate wording; preserved for review",
                })
            same_topic = a.topic == b.topic
            different_condition = set(a.conditionApplicability) != set(b.conditionApplicability)
            different_context = set(a.diseaseContext) != set(b.diseaseContext)
            symptom_inflammation = {a.outcomeType, b.outcomeType} == {"symptoms", "inflammation"}
            if same_topic and (different_condition or different_context or symptom_inflammation):
                conflicts.append({
                    "conflictId": f"CON-{len(conflicts)+1:03d}", "claimA": a.claimId,
                    "claimB": b.claimId, "topic": a.topic,
                    "conditionDifference": "Yes" if different_condition else "No",
                    "diseaseStateDifference": "Yes" if different_context else "No",
                    "populationDifference": "Review source records",
                    "evidenceLevelDifference": "Yes" if a.evidenceLevel != b.evidenceLevel else "No",
                    "symptomVsInflammation": "Yes" if symptom_inflammation else "No",
                    "regionalDifference": "Review source-level regional applicability",
                    "reason": "Potentially non-comparable findings; do not silently merge.",
                })
    return duplicates[:80], conflicts[:80]


def coverage_rows(claims: list[ClaimRecord]) -> list[dict[str, Any]]:
    dimensions = defaultdict(int)
    for c in claims:
        for condition in c.conditionApplicability:
            dimensions[("Condition", condition)] += 1
        for context in c.diseaseContext:
            dimensions[("Disease context", context)] += 1
        dimensions[("Topic", c.topic)] += 1
        dimensions[("Outcome type", c.outcomeType)] += 1
        dimensions[("Evidence level", c.evidenceLevel)] += 1
        applicability = "Canada/US directly discussed" if c.countryOrRegion in {"Canada", "United States", "Canada, United States"} else "Canada/US transferability requires review"
        dimensions[("Regional applicability", applicability)] += 1
    rows = []
    for (category, dimension), count in sorted(dimensions.items()):
        rows.append({"category": category, "dimension": dimension, "claimCount": count,
                     "coverageStatus": "Under-covered" if count < 3 else "Covered",
                     "reviewNote": "Counts show candidate-claim coverage, not approval or evidence certainty."})
    return rows


def main() -> None:
    for path in [CACHE, LOGS, ROOT / "extracted-claims", ROOT / "processing/chunks", ROOT / "processing/checkpoints"]:
        path.mkdir(parents=True, exist_ok=True)
    candidates, search_log, api_usage = discover()
    selected, rejected_sources = select_sources(candidates)
    acquired, failures, acquisition_requests = acquire(selected)
    api_usage["acquisition_requests"] = acquisition_requests
    sources = source_records(selected, acquired)
    claims, rejected_claims = claim_records(sources, selected)
    official_sources, official_claims, official_failures, official_requests = official_source_records(len(sources) + 1)
    sources.extend(official_sources)
    for claim in official_claims:
        if len(claims) >= LIMITS["maxTotalCandidateClaims"]:
            rejected_claims.append({"source": claim.sourceTitle, "candidate": claim.claim, "reason": "Candidate-claim cap reached"})
            continue
        claim.claimId = f"CLM-{len(claims)+1:03d}"
        claims.append(claim)
    failures.extend(official_failures)
    api_usage["official_web_requests"] = official_requests
    chunks = []
    for source in sources:
        if source.pmid:
            source_text = acquired[source.pmid][1]
        else:
            source_text = (ROOT / f"extracted-text/{source.sourceId}.txt").read_text()
        source_chunks = chunk_text(source_text, source.sourceId)
        chunks.extend(source_chunks)
        (ROOT / f"processing/chunks/{source.sourceId}.json").write_text(json.dumps(source_chunks, indent=2))
    duplicates, conflicts = duplicates_and_conflicts(claims)
    coverage = coverage_rows(claims)
    data = {
        "sources": [s.model_dump(mode="json") for s in sources],
        "claims": [c.model_dump(mode="json") for c in claims],
        "coverage": coverage, "duplicates": duplicates, "conflicts": conflicts,
        "acquisitionFailures": failures, "rejectedCandidates": rejected_sources,
        "rejectedClaims": rejected_claims, "searchLog": search_log,
    }
    (ROOT / "processing/checkpoints/research-data.json").write_text(json.dumps(data, indent=2))
    summary = {
        "executionDate": UTCNOW().isoformat(),
        "searchesPerformed": len(search_log), "candidatesFound": len(candidates),
        "sourcesSelected": len(sources),
        "sourceTypeBreakdown": dict(Counter(s.sourceType for s in sources)),
        "ulcerativeColitisSpecificSources": sum("ulcerative_colitis" in s.conditionApplicability for s in sources),
        "crohnsSpecificSources": sum("crohns_disease" in s.conditionApplicability for s in sources),
        "sharedIBDSources": sum("ibd_general" in s.conditionApplicability for s in sources),
        "fullTextAcquisitions": sum(s.fullTextAvailability == "public_full_text" for s in sources),
        "abstractOnlyAcquisitions": sum(s.fullTextAvailability == "abstract_only" for s in sources),
        "chunksGenerated": len(chunks), "claimsRetained": len(claims),
        "claimsRejected": len(rejected_claims), "duplicates": len(duplicates),
        "conflicts": len(conflicts),
        "coverageGaps": [r["dimension"] for r in coverage if r["coverageStatus"] == "Under-covered"],
        "regionalApplicabilityGaps": sum("requires review" in r["dimension"] for r in coverage),
        "limitsReached": [
            name for name, hit in {
                "maxTotalCandidates": len(candidates) >= LIMITS["maxTotalCandidates"],
                "maxSelectedSources": len(sources) >= LIMITS["maxSelectedSources"],
                "maxTotalCandidateClaims": len(claims) >= LIMITS["maxTotalCandidateClaims"],
            }.items() if hit
        ],
        "estimatedApiUsage": {
            **api_usage, "paidModelCalls": 0,
            "estimatedPubMedRecordsFetched": len(candidates),
        },
        "errors": failures,
        "reviewStatus": "pending_human_review",
    }
    (ROOT / "run-summary.json").write_text(json.dumps(summary, indent=2))
    (ROOT / "extracted-claims/candidate-claims.json").write_text(json.dumps(data["claims"], indent=2))
    (ROOT / "extracted-claims/rejected-claims.json").write_text(json.dumps(rejected_claims, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
