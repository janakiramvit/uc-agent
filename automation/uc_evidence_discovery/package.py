"""Merge a run's accepted sources + candidate claims + dispositions into the staged package
under ``<state-root>/knowledge/uc-evidence-expansion/`` — preserving the existing schemas.

Nothing here approves evidence, promotes to any index, or touches Supabase / the app.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

from . import config


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _dump(path: Path, doc: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_source_record(rec: dict, *, source_id: str, applicability: str, archival, disposition_reason: str) -> dict:
    return {
        "sourceId": source_id,
        "title": rec.get("title", ""),
        "authors": rec.get("authors", ""),
        "publishingOrganisation": rec.get("publishingOrganisation", ""),
        "journalOrPublisher": rec.get("journal", ""),
        "sourceType": rec.get("sourceType", "") or "journal article",
        "studyDesign": rec.get("studyDesign", "") or "not_reported",
        "publicationDate": rec.get("publicationDate", "") or rec.get("pubYear", "") or "unknown",
        "doi": rec.get("doi", ""),
        "pubmedId": rec.get("pmid", "") or rec.get("pubmedId", ""),
        "pmcId": rec.get("pmcid", ""),
        "clinicalTrialsId": rec.get("nctId", ""),
        "canonicalUrl": rec.get("canonicalUrl", ""),
        "alternateUrl": rec.get("alternateUrl", ""),
        "accessDate": _dt.date.today().isoformat(),
        "fullTextStatus": "abstract_only_retrieved",
        "abstractOrFullTextLocator": rec.get("retrievedVia", ""),
        "studyPopulation": "not_reported",
        "ucApplicability": applicability,
        "ucSpecificSampleSize": "not_reported",
        "interventionOrExposure": "not_reported",
        "comparator": "not_reported",
        "outcomes": "not_reported",
        "limitations": "Retrieved as abstract/registry metadata only; full recommendation text not accessed.",
        "regionalApplicability": {
            "canada": "requires_human_review",
            "unitedStates": "requires_human_review",
            "assessment": "Not assessed mechanically.",
        },
        "accessMethod": rec.get("retrievedVia", ""),
        "licence": rec.get("license", "") or "not stated in retrieved metadata",
        "redistributionStatus": archival.redistribution_status,
        "archivalStatus": archival.archival_status,
        "archivalPermission": "not_established",
        "provenance": {
            "retrievedVia": rec.get("retrievedVia", ""),
            "retrievedAt": _dt.date.today().isoformat(),
            "provider": rec.get("provider", ""),
        },
        "retrievalTimestamp": _now(),
        "screeningDispositionReason": disposition_reason,
        "automatedQaStatus": "pending",
        "lifecycleState": "extracted",
        "humanReviewStatus": "",
        "clinicalReviewStatus": "",
        "reviewerNotes": "",
    }


def merge(
    paths: config.StatePaths,
    *,
    run_id: str,
    accepted: list[dict],       # [{"record":..., "sourceRecord":..., "claims":[...]}]
    licensing_entries: list[dict],
) -> dict:
    """Write the JSON package files. Returns a small summary dict."""
    sources_doc = _load(paths.sources_path, {"schemaVersion": config.SCHEMA_VERSION_1_1_0, "sources": []})
    claims_doc = _load(paths.claims_path, {"schemaVersion": config.SCHEMA_VERSION_1_1_0, "claims": []})
    manifest = _load(
        paths.manifest_path,
        {"schemaVersion": config.SCHEMA_VERSION_1_1_0, "targetIndex": "NONE", "sourceFiles": [], "linkOnlySources": []},
    )
    licensing = _load(paths.licensing_path, {"schemaVersion": config.SCHEMA_VERSION_1_1_0, "entries": []})

    new_sources = [a["sourceRecord"] for a in accepted]
    new_claims = [c for a in accepted for c in a["claims"]]

    sources_doc["sources"].extend(new_sources)
    sources_doc["runId"] = run_id
    sources_doc["generatedAt"] = _now()
    sources_doc["sourcesAcceptedThisRun"] = len(new_sources)

    claims_doc["claims"].extend(new_claims)
    claims_doc["runId"] = run_id
    claims_doc["generatedAt"] = _now()
    claims_doc["claimsExtractedThisRun"] = len(new_claims)
    claims_doc.setdefault(
        "extractionRules",
        [
            "Every claim is a verbatim substring of a retrieved abstract.",
            "No inference beyond the source; associations not converted to causation.",
            "IBD-general content stays ibd_general and is not relabelled UC-specific.",
            "All claims are pending_clinical_review; no claim is approved.",
            "All claims are mechanically extracted candidates.",
        ],
    )

    for s in new_sources:
        manifest["linkOnlySources"].append(
            {
                "sourceId": s["sourceId"],
                "pubmedId": s.get("pubmedId", ""),
                "doi": s.get("doi", ""),
                "canonicalUrl": s.get("canonicalUrl", ""),
                "reason": "licence for local archival/redistribution not established; retained as link_only.",
            }
        )
    manifest["targetIndex"] = "NONE - staged package only. Nothing ingested into any production index."
    manifest["productionPromotion"] = "blocked_by_design"
    manifest["runId"] = run_id
    manifest["generatedAt"] = _now()

    licensing["entries"].extend(licensing_entries)
    licensing["runId"] = run_id
    licensing["generatedAt"] = _now()

    _dump(paths.sources_path, sources_doc)
    _dump(paths.claims_path, claims_doc)
    _dump(paths.manifest_path, manifest)
    _dump(paths.licensing_path, licensing)

    return {
        "sourcesTotal": len(sources_doc["sources"]),
        "claimsTotal": len(claims_doc["claims"]),
        "newSources": len(new_sources),
        "newClaims": len(new_claims),
    }


def update_coverage_map(paths: config.StatePaths, *, run_id: str, topic_id: str, next_topic_id: str | None) -> None:
    doc = _load(paths.coverage_map_path, {"schemaVersion": config.SCHEMA_VERSION_1_1_0})
    doc["runId"] = run_id
    doc["generatedAt"] = _now()
    history = doc.setdefault("automatedRunHistory", [])
    history.append({"runId": run_id, "topicId": topic_id, "at": _now()})
    if next_topic_id:
        doc["nextRecommendedTopic"] = {"topicId": next_topic_id, "setBy": "automated-runner", "at": _now()}
    _dump(paths.coverage_map_path, doc)


def write_reports(
    paths: config.StatePaths,
    *,
    run_id: str,
    run_url: str,
    counters: dict,
    dispositions: dict,
    qa_summary: dict,
    next_operation: dict,
    status: str,
) -> None:
    date = _dt.date.today().isoformat()
    disp_lines = "\n".join(f"| {k} | {v} |" for k, v in sorted(dispositions.items()))
    run_report = f"""# UC Evidence-Discovery — Daily Run Report

**Run ID:** `{run_id}` · **Run:** {run_url or 'local'} · **Date:** {date}
**Run status:** `{status}`

> Automated discovery + staging only. Nothing here is clinically approved. All new records are
> `pending_clinical_review`. No application code, deployment, Vercel config, Supabase table, or
> production RAG/vector index was touched. No paid model or API call was made.

## Limits vs actuals

| Limit | Ceiling | This run |
|---|---|---|
| Internal research | {config.SOFT_DEADLINE_SECONDS}s soft / {config.FINALIZE_DEADLINE_SECONDS}s finalize | {counters.get('elapsedResearchSeconds', 0)}s |
| Discovery queries | {config.MAX_QUERIES} | {counters.get('queriesConsumed', 0)} |
| Records screened | {config.MAX_SCREENED} | {counters.get('recordsScreened', 0)} |
| New sources accepted | {config.MAX_ACCEPTED} | {counters.get('sourcesAccepted', 0)} |
| Candidate excerpts | {config.MAX_CLAIMS} | {counters.get('claimsExtracted', 0)} |
| PDFs archived | 0 (policy) | {counters.get('pdfsDownloaded', 0)} |

## Dispositions

| Disposition | Count |
|---|---|
{disp_lines}

## QA

{qa_summary.get('passed', 0)} / {qa_summary.get('total', 0)} automated checks PASS
(automated QA is **not** clinical approval).

## Exact next operation

```json
{json.dumps(next_operation, indent=2)}
```
"""
    paths.run_report_path.write_text(run_report, encoding="utf-8")

    gaps = f"""# UC Evidence Gaps (auto-maintained)

_Last updated {date} by run `{run_id}`._

This file is regenerated each automated run. Gap analysis beyond keyword coverage
`requires_human_review`. See `question-coverage-map.json` for the topic roadmap.
"""
    paths.evidence_gaps_path.write_text(gaps, encoding="utf-8")


def write_reviewer_workbook(paths: config.StatePaths, *, run_id: str, sources: list[dict], claims: list[dict]) -> None:
    """Regenerate the 9-sheet reviewer workbook. Every reviewer/approval column stays blank."""
    try:
        from openpyxl import Workbook
    except Exception:      # pragma: no cover - openpyxl is pinned; guard only
        return
    wb = Workbook()
    sheets = [
        "Run Summary", "Sources", "Candidate Claims", "Question Coverage", "Conflicts",
        "Evidence Gaps", "Licensing and Access", "QA Results", "Method and Limitations",
    ]
    wb.active.title = sheets[0]
    for name in sheets[1:]:
        wb.create_sheet(name)

    wb["Run Summary"].append(["runId", "generatedAt", "note"])
    wb["Run Summary"].append([run_id, _now(), "Automated daily discovery. Nothing approved."])

    ws = wb["Sources"]
    ws.append(["sourceId", "title", "doi", "pubmedId", "ucApplicability", "archivalStatus",
               "humanReviewStatus", "clinicalReviewStatus", "reviewerNotes"])
    for s in sources:
        ws.append([s.get("sourceId"), s.get("title"), s.get("doi"), s.get("pubmedId"),
                   s.get("ucApplicability"), s.get("archivalStatus"), "", "", ""])

    ws = wb["Candidate Claims"]
    ws.append(["claimId", "sourceId", "conditionApplicability", "verificationBasis",
               "reviewStatus", "humanReviewStatus", "clinicalReviewStatus", "reviewerDecision", "reviewDate"])
    for c in claims:
        ws.append([c.get("claimId"), c.get("sourceId"), c.get("conditionApplicability"),
                   c.get("verificationBasis"), c.get("reviewStatus"), "", "", "", ""])

    for name in ("Question Coverage", "Conflicts", "Evidence Gaps"):
        wb[name].append(["see", "companion JSON / MD files"])
    wb["Licensing and Access"].append(["sourceId", "licence", "redistributionStatus", "archivalStatus"])
    for s in sources:
        wb["Licensing and Access"].append([s.get("sourceId"), s.get("licence"),
                                           s.get("redistributionStatus"), s.get("archivalStatus")])
    wb["QA Results"].append(["see", "qa-results.json"])
    wb["Method and Limitations"].append([
        "method", "Deterministic keyword/metadata screening; verbatim abstract excerpts; no LLM."
    ])
    wb.save(paths.reviewer_workbook_path)
