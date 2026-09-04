"""Redacted GitHub Actions artifact builder.

**Allowlist only.** The artifact may carry run id + timestamps, safe normalised query labels,
aggregate counts, accepted internal source ids + titles + DOI/PMID/PMCID/NCT + canonical
public URLs, QA pass/fail totals, disposition-reason *categories*, checkpoint-validation
status, the next topic id, and safe error categories. It must never carry abstracts,
supporting excerpts, candidate-claim text, PDF/XML content, personal data, credentials,
tokens, auth headers, connection strings, environment-variable values, raw API responses, or
stack traces with sensitive values.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path

from . import config

_FORBIDDEN_SUBSTRINGS = ("-----BEGIN", "ghp_", "gho_", "postgres://", "postgresql://")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _query_label(raw: str) -> str:
    """Reduce a query string to a safe, coarse label."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", raw or "")
    keep = [t.lower() for t in tokens if t.lower() not in {"and", "or", "not", "src", "ext"}][:6]
    return " ".join(keep) or "discovery-query"


def build(
    *,
    run_id: str,
    run_url: str,
    started_at: str,
    finished_at: str,
    source_data_cutoff: str,
    status: str,
    counters: dict,
    disposition_reason_categories: dict,
    accepted_sources: list[dict],
    query_labels: list[str],
    qa_summary: dict,
    checkpoint_valid: bool,
    next_topic_id: str | None,
    error_categories: list[str],
    out_dir: Path = config.ARTIFACT_DIR,
) -> Path:
    doc = {
        "artifactSchema": "uc-daily-evidence-discovery/redacted-run/1",
        "runId": run_id,
        "workflowRunUrl": run_url,
        "startedAt": started_at,
        "finishedAt": finished_at,
        "sourceDataCutoff": source_data_cutoff,
        "status": status,
        "counters": {
            k: counters.get(k)
            for k in ("elapsedResearchSeconds", "queriesConsumed", "recordsScreened",
                      "sourcesAccepted", "claimsExtracted", "pdfsDownloaded")
        },
        "dispositionReasonCategories": disposition_reason_categories,
        "queryLabels": [_query_label(q) for q in query_labels],
        "acceptedSources": [
            {
                "sourceId": s.get("sourceId"),
                "title": s.get("title"),
                "doi": s.get("doi") or None,
                "pubmedId": s.get("pubmedId") or None,
                "pmcId": s.get("pmcId") or None,
                "clinicalTrialsId": s.get("clinicalTrialsId") or None,
                "canonicalUrl": s.get("canonicalUrl") or None,
                "ucApplicability": s.get("ucApplicability"),
                "reviewStatus": "pending_clinical_review",
            }
            for s in accepted_sources
        ],
        "qa": {"total": qa_summary.get("total"), "passed": qa_summary.get("passed"),
               "failed": qa_summary.get("failed")},
        "checkpointValidation": "valid" if checkpoint_valid else "invalid",
        "nextTopicId": next_topic_id,
        "errorCategories": sorted(set(error_categories)),
        "note": "Redacted. Contains no abstracts, excerpts, claim text, raw responses, or secrets.",
    }
    _assert_clean(doc)

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"redacted-run-{run_id}.json"
    json_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# Redacted run artifact — `{run_id}`",
        "",
        f"- Status: **{status}**  ·  Workflow: {run_url or 'local'}",
        f"- Window: {started_at} → {finished_at}  ·  source-data cutoff {source_data_cutoff}",
        f"- Queries {doc['counters']['queriesConsumed']}/{config.MAX_QUERIES} · "
        f"screened {doc['counters']['recordsScreened']}/{config.MAX_SCREENED} · "
        f"accepted {doc['counters']['sourcesAccepted']}/{config.MAX_ACCEPTED} · "
        f"excerpts {doc['counters']['claimsExtracted']}/{config.MAX_CLAIMS}",
        f"- QA: {doc['qa']['passed']}/{doc['qa']['total']} PASS  ·  checkpoint {doc['checkpointValidation']}",
        f"- Next topic: `{next_topic_id}`",
        "",
        "## Accepted sources (identifiers + titles only)",
        "",
        "| sourceId | title | DOI/PMID/PMCID/NCT | ucApplicability |",
        "|---|---|---|---|",
    ]
    for s in doc["acceptedSources"]:
        ident = s["doi"] or s["pubmedId"] or s["pmcId"] or s["clinicalTrialsId"] or "—"
        md.append(f"| {s['sourceId']} | {s['title']} | {ident} | {s['ucApplicability']} |")
    md_path = out_dir / f"redacted-run-{run_id}.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return json_path


def _assert_clean(doc: dict) -> None:
    blob = json.dumps(doc).lower()
    for bad in _FORBIDDEN_SUBSTRINGS:
        if bad.lower() in blob:
            raise AssertionError(f"redacted artifact contains forbidden token {bad!r}")
    # 'abstract'/'excerpt' are only allowed inside the fixed, static 'note' string
    for key, val in doc.items():
        if key == "note":
            continue
        if isinstance(val, str) and ("abstract" in val.lower() or "excerpt" in val.lower()):
            raise AssertionError(f"redacted artifact field {key!r} mentions abstract/excerpt text")
