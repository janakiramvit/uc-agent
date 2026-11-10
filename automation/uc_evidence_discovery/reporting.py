"""Daily report: per-provider health and funnel. Written to the staging branch (DAILY-REPORT.md,
provider-funnel.json); a counts-only summary also goes into the redacted GitHub artifact."""

from __future__ import annotations

import datetime as _dt
import json

from . import config
from .alerts import Alert, has_errors
from .funnel import RunFunnel

_ICON = {"ok": "OK", "partial": "PARTIAL", "no_new_records": "NO NEW RECORDS", "zero_unexplained": "ZERO (UNEXPLAINED)",
         "failed": "FAILED", "invalid_query": "INVALID QUERY", "access_limited": "ACCESS LIMITED",
         "skipped_deadline": "SKIPPED (DEADLINE)"}


def funnel_document(run_id: str, today: _dt.date, funnel: RunFunnel, alerts: list[Alert], missed: list[str]) -> dict:
    return {"schema": "uc-provider-funnel/1", "runId": run_id, "date": today.isoformat(),
            "missedDates": missed, "alerts": [a.to_dict() for a in alerts], **funnel.to_dict()}


def render_daily_report(run_id: str, run_url: str, today: _dt.date, funnel: RunFunnel, alerts: list[Alert],
                        missed: list[str], accepted_titles: list[tuple[str, str, str]]) -> str:
    t = funnel.totals()
    L = [f"# UC evidence discovery - daily report {today.isoformat()}", "",
         f"Run `{run_id}` - {run_url or 'local'}", "",
         "> Discovery and staging only. Nothing here is approved, published or promoted; every new record is "
         "`pending_clinical_review` and every claim needs full-text verification.", ""]
    L += ["## Alerts", ""]
    if alerts:
        order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
        for a in sorted(alerts, key=lambda a: (order.get(a.level, 3), a.provider)):
            L.append(f"- **{a.level}** `{a.code}` ({a.provider}): {a.message}")
    else:
        L.append("- none")
    if missed:
        L += ["", f"**Missed run date(s): {', '.join(missed)}** - covered by catch-up from each provider's last successful cutoff."]
    L += ["", "## Provider health", "",
          "| Provider | Type | Status | Window | Searches | Hits | Returned | Screened | Dupes | Rejected | Deferred | "
          "Accepted | Claims | Cutoff advanced |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in funnel.providers.values():
        L.append(f"| {f.label} | {f.evidence_type} | **{_ICON.get(f.status, f.status)}** | {f.window.split(';')[0]} | "
                 f"{f.searches_attempted} | {f.hit_count} | {f.results_returned} | {f.records_screened} | "
                 f"{f.duplicates} | {f.rejected} | {f.deferred} | {f.accepted} | {f.claims_extracted} | "
                 f"{'yes' if f.advanced_cutoff else 'no'} |")
    L.append(f"| **All** | | | | {t['searches_attempted']} | | {t['results_returned']} | {t['records_screened']} | "
             f"{t['duplicates']} | {t['rejected']} | {t['deferred']} | {t['accepted']} | {t['claims_extracted']} | |")
    L += ["", "## Per-provider detail", ""]
    for f in funnel.providers.values():
        L += [f"### {f.label}", "", f"- Status: **{_ICON.get(f.status, f.status)}**; evidence type: `{f.evidence_type}`",
              f"- Window: {f.window}"]
        for q in f.queries:
            L.append(f"- Query (this provider's own syntax): `{q}`")
        if f.canary_hits is not None:
            L.append(f"- Canary (wide window, same syntax): {f.canary_hits}")
        if f.zero_reason:
            L.append(f"- Zero-result reason: {f.zero_reason}")
        if f.error:
            L.append(f"- Error: {f.error}")
        for a in f.access_limits:
            L.append(f"- Access limitation: {a}")
        for n in f.notes:
            L.append(f"- Note: {n}")
        if f.duplicates_cross or f.duplicates_prior:
            L.append(f"- Duplicates: {f.duplicates_cross} cross-provider/in-provider, {f.duplicates_prior} already seen in earlier runs")
        for label, c in (("Rejected", f.rejected_reasons), ("Deferred", f.deferred_reasons)):
            if c:
                L.append(f"- {label}: " + ", ".join(f"{k} x{v}" for k, v in sorted(c.items())))
        L.append("")
    L += ["## Accepted this run (staging only)", ""]
    L += ([f"- `{sid}` [{etype}] {title}" for sid, etype, title in accepted_titles] or ["- none"])
    return "\n".join(L) + "\n"


def provider_health_for_artifact(funnel: RunFunnel) -> dict:
    """Counts + status only: no queries with free text, abstracts, error bodies or URLs."""
    return {name: {"status": f.status, "evidenceType": f.evidence_type, "searches": f.searches_attempted,
                   "hits": f.hit_count, "returned": f.results_returned, "screened": f.records_screened,
                   "duplicates": f.duplicates, "rejected": f.rejected, "deferred": f.deferred,
                   "accepted": f.accepted, "claims": f.claims_extracted,
                   "cutoffAdvanced": f.advanced_cutoff}
            for name, f in funnel.providers.items()}


def github_annotations(alerts: list[Alert]) -> list[str]:
    return [a.github_annotation() for a in alerts if a.level in ("ERROR", "WARNING")]
