"""Multi-provider discovery: window -> per-provider search -> cross-provider de-duplication -> screening ->
funnel/alerts/state.

Design notes
* Every provider is attempted every run and reported independently; a failure in one never stops the others.
* The query is "everything new for ulcerative colitis since the last successful cutoff" in each provider's own syntax,
  not a rotating topic keyword: a date window is complete by construction, so nothing is skipped between runs.
* A provider's cutoff advances only when its whole window was retrieved AND screened. Otherwise the window is kept and
  the next run continues from it (missed days are reported, never silently dropped).
* A zero-result window is always explained: a wide-window "canary" in the same syntax distinguishes "no new records"
  from "broken query / outage".
"""

from __future__ import annotations

import datetime as _dt
from collections import Counter
from typing import Optional

from . import config, crossdedupe, provider_state, screening
from .alerts import ERROR, INFO, WARNING, Alert
from .apis.http import Http
from .clock import Deadline
from .dedup import CandidateKey, ProcessedIndex
from .extract import extract_candidates, verify_verbatim
from .funnel import ProviderFunnel, RunFunnel
from .licensing import plan_archival
from .providers.base import AccessLimited, EvidenceType, InvalidQuery, Provider, ProviderError, SearchOutcome
from .providers.registry import build_providers, rotated
from .window import plan_window
from . import package

TOPIC_ID = "T-DAILY"


def _identity(rec: dict) -> str:
    k = CandidateKey.from_record(rec)
    for tag, val in (("doi", k.doi), ("pmid", k.pmid), ("nct", k.trial_id), ("url", k.canonical_url),
                     ("title", k.normalized_title)):
        if val:
            return f"{tag}:{val}"[:200]
    return ""


def _reason_category(reason: str) -> str:
    return reason.split(":", 1)[0].split(";", 1)[0]


def run(*, http: Http, clock: Deadline, pstate: dict, index: ProcessedIndex, allocator, st, journal,
        today: _dt.date, providers: Optional[list[Provider]] = None, canary_http: Optional[Http] = None) -> None:
    """Populate ``st`` (the runner's research state) and update ``pstate`` in place."""
    providers = providers if providers is not None else build_providers()
    funnel = RunFunnel()
    alerts: list[Alert] = []
    outcomes: dict[str, SearchOutcome] = {}
    windows: dict[str, object] = {}
    st.funnel, st.alerts, st.provider_windows = funnel, alerts, windows

    # ---- run-level: report missed days (never silent) -------------------------------------------------
    last_run = pstate.get("lastRunDate")
    if last_run:
        gap = (today - _dt.date.fromisoformat(last_run)).days - 1
        if gap > 0:
            missed = [(_dt.date.fromisoformat(last_run) + _dt.timedelta(days=i)).isoformat() for i in range(1, gap + 1)]
            alerts.append(Alert(WARNING, "MISSED_RUNS", "all",
                                f"{gap} day(s) had no run: {', '.join(missed)}. Each provider catches up from its own "
                                "last successful cutoff."))
            st.missed_dates = missed

    # ---- 1. search every provider, independently -------------------------------------------------------
    for prov in rotated(providers, today):
        ps = provider_state.provider(pstate, prov.name)
        f = ProviderFunnel(prov.name, prov.label, prov.evidence_type.value)
        funnel.providers[prov.name] = f
        wp = plan_window(ps.get("lastSuccessfulCutoff"), today)
        windows[prov.name] = wp
        f.window = wp.describe()
        if wp.window.days <= 0:
            f.status, f.zero_reason = "no_new_records", "discovery has not started yet (before the configured start date)"
            continue
        if not clock.may_start_new_work():
            f.status = "skipped_deadline"
            alerts.append(Alert(WARNING, "SKIPPED_DEADLINE", prov.name,
                                "research soft deadline reached before this provider; its window is retained for the next run"))
            continue
        if hasattr(prov, "known_listing_urls"):
            prov.known_listing_urls = set(ps.get("knownListingUrls", []))
        st.queries += 1
        try:
            out = prov.search_window(http, wp.window, max_pages=config.MAX_PAGES_PER_SEARCH)
        except AccessLimited as exc:
            f.status, f.error = "access_limited", str(exc)
            f.access_limits.append(str(exc))
            alerts.append(Alert(WARNING, "ACCESS_LIMITED", prov.name, str(exc)))
            journal.append("provider_access_limited", f"{prov.name}: {exc}")
            continue
        except InvalidQuery as exc:
            f.status, f.error, f.searches_failed = "invalid_query", str(exc), 1
            f.searches_attempted = 1
            alerts.append(Alert(ERROR, "INVALID_QUERY", prov.name, str(exc)))
            journal.append("provider_invalid_query", f"{prov.name}: {exc}")
            ps["consecutiveFailures"] = ps.get("consecutiveFailures", 0) + 1
            continue
        except ProviderError as exc:
            f.status, f.error, f.searches_failed = "failed", str(exc), 1
            f.searches_attempted = 1
            alerts.append(Alert(ERROR, "PROVIDER_FAILURE", prov.name, str(exc)))
            journal.append("provider_failure", f"{prov.name}: {exc}")
            ps["consecutiveFailures"] = ps.get("consecutiveFailures", 0) + 1
            if ps["consecutiveFailures"] >= config.REPEATED_ZERO_ERROR:
                alerts.append(Alert(ERROR, "REPEATED_PROVIDER_FAILURE", prov.name,
                                    f"{ps['consecutiveFailures']} consecutive failed runs"))
            continue

        outcomes[prov.name] = out
        ps["consecutiveFailures"] = 0
        st.query_labels.extend(out.queries)
        f.queries = list(out.queries)
        f.searches_attempted = out.searches
        f.hit_count = out.hit_count
        f.results_returned = len(out.records)
        f.access_limits.extend(out.access_limits)
        f.notes.extend(out.notes)
        for lim in out.access_limits:
            alerts.append(Alert(WARNING, "ACCESS_LIMITED", prov.name, f"{lim}; covered via other channel only"))

        # sanity + zero explanation via a wide canary in the SAME syntax
        needs_canary = out.hit_count == 0 or prov.name in ("europepmc", "pubmed", "clinicaltrials")
        if needs_canary and clock.may_start_new_work():
            try:
                st.queries += 1
                f.canary_hits = prov.canary_count(canary_http or http, today)
            except ProviderError as exc:
                alerts.append(Alert(WARNING, "CANARY_FAILED", prov.name, str(exc)))
        if f.canary_hits is not None and out.hit_count > f.canary_hits and prov.name in ("europepmc", "pubmed", "clinicaltrials"):
            f.status = "invalid_query"
            f.error = (f"window returned {out.hit_count} hits but the wider {365}-day canary only {f.canary_hits}: "
                       "the date filter is being ignored")
            alerts.append(Alert(ERROR, "INVALID_QUERY", prov.name, f.error))
            outcomes.pop(prov.name, None)
            f.results_returned = 0
            continue

        if out.hit_count == 0 and not out.records:
            _explain_zero(prov, f, ps, alerts)
        else:
            ps["consecutiveUnexpectedZero"] = 0
        ps.setdefault("recentHitCounts", []).append(out.hit_count)
        journal.append("provider_searched",
                       f"{prov.name}: hits={out.hit_count} returned={len(out.records)} canary={f.canary_hits}")

    # ---- 2. cross-provider de-duplication --------------------------------------------------------------
    flat: list[dict] = []
    for name, out in outcomes.items():
        for rec in out.records:
            rec.setdefault("provider", name)
            flat.append(rec)
    merged = crossdedupe.merge(flat)
    for prov_name, n in merged.absorbed_by_provider.items():
        if prov_name in funnel.providers:
            funnel.providers[prov_name].duplicates_cross += n
            funnel.providers[prov_name].duplicate_reasons["cross_provider_duplicate"] += n
    st.cross_provider_merges = merged.merge_log

    # ---- 3. screen, round-robin across providers so none starves another ------------------------------------
    queues: dict[str, list[dict]] = {}
    for rec in merged.records:
        queues.setdefault(rec.get("provider", ""), []).append(rec)
    order = [p.name for p in rotated(providers, today) if p.name in queues]
    rejected_memory = {n: set(provider_state.provider(pstate, n).get("rejectedKeys", [])) for n in order}
    interleaved: list[dict] = []
    while any(queues[n] for n in order):
        for n in order:
            if queues[n]:
                interleaved.append(queues[n].pop(0))

    limit_hit = False
    for rec in interleaved:
        name = rec.get("provider", "")
        f = funnel.providers.get(name)
        if limit_hit or not clock.may_start_new_work() or st.screened >= config.MAX_SCREENED \
                or len(st.accepted) >= config.MAX_ACCEPTED:
            limit_hit = True
            if f:
                f.not_screened_limit += 1
            st.stop_reason = "limit_or_deadline_during_screening"
            continue
        ident = _identity(rec)
        st.screened += 1
        if f:
            f.records_screened += 1
        if ident and ident in rejected_memory.get(name, set()):
            disp = screening.Disposition("duplicate", "duplicate_previously_rejected", topic_id=TOPIC_ID,
                                         evidence_type=rec.get("evidenceType", "published_study"))
        else:
            disp = screening.screen(rec, index=index, topic_id=TOPIC_ID, topic_keywords=())
        st.dispositions.append(disp)
        d = rec.get("publicationDate") or rec.get("pubYear") or ""
        if d and d > st.latest_pub_seen:
            st.latest_pub_seen = d
        index.add(CandidateKey.from_record(rec))
        _tally(f, disp)
        if disp.status == "rejected" and ident:
            rejected_memory.setdefault(name, set()).add(ident)
        if disp.status != "accepted":
            continue

        src_id = allocator.source_id()
        arch = plan_archival(rec)
        claims: list[dict] = []
        if disp.claims_allowed:
            claims = extract_candidates(
                rec, source_id=src_id, applicability=disp.applicability, topic_id=TOPIC_ID,
                mapped_question_ids=[], allocate_claim_id=allocator.claim_id,
                remaining_global=config.MAX_CLAIMS - st.claims_made, topic_keywords=())
            abstract = rec.get("abstractText") or ""
            claims = [c for c in claims if not verify_verbatim(c, abstract)]
        st.claims_made += len(claims)
        if f:
            f.accepted += 1
            f.claims_extracted += len(claims)
        st.accepted.append({
            "record": rec, "sourceRecord": package.build_source_record(
                rec, source_id=src_id, applicability=disp.applicability, archival=arch,
                disposition_reason=disp.reason),
            "claims": claims,
            "licensing": {
                "sourceId": src_id, "title": rec.get("title", ""), "canonicalUrl": rec.get("canonicalUrl", ""),
                "doi": rec.get("doi", ""), "pubmedId": rec.get("pmid", ""),
                "statedLicence": rec.get("license", "") or "not stated in retrieved metadata",
                "localArchivalPermitted": "no_not_established",
                "redistributionPermitted": arch.redistribution_status, "archivalStatus": arch.archival_status,
                "acquisitionDate": _dt.date.today().isoformat(),
                "retainedArtifacts": ["citation metadata", "DOI/PMID/NCT", "public link"]
                                     + (["public abstract text"] if (rec.get("abstractText") or "").strip() else []),
                "notStored": ["full text", "publisher PDF"],
            },
        })

    # ---- 4. state: cutoffs advance only for fully retrieved + fully screened windows ----------------------
    for prov in providers:
        f = funnel.providers.get(prov.name)
        if f is None:
            continue
        ps = provider_state.provider(pstate, prov.name)
        out = outcomes.get(prov.name)
        wp = windows.get(prov.name)
        complete = (out is not None and not out.truncated and f.not_screened_limit == 0
                    and f.status not in ("failed", "invalid_query", "skipped_deadline", "access_limited"))
        if f.status == "ok" and (out is None or out.truncated or f.not_screened_limit):
            f.status = "partial"
        if complete and wp is not None:
            ps["lastSuccessfulCutoff"] = wp.window.end.isoformat()
            ps["lastSuccessfulRunAt"] = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            f.advanced_cutoff = True
        elif out is not None and (out.truncated or f.not_screened_limit):
            alerts.append(Alert(WARNING, "WINDOW_NOT_COMPLETE", prov.name,
                                "window not fully retrieved/screened; cutoff NOT advanced - continues next run"))
        ps["lastStatus"] = f.status
        ps["rejectedKeys"] = sorted(rejected_memory.get(prov.name, set(ps.get("rejectedKeys", []))))[-provider_state.MAX_REJECTED_KEYS:]
        if hasattr(prov, "listing_seen") and prov.listing_seen:
            ps["knownListingUrls"] = sorted(prov.listing_seen | set(ps.get("knownListingUrls", [])))[:500]

    st.stop_reason = st.stop_reason if st.stop_reason != "no_research_executed" else "all_providers_attempted"
    pstate["lastRunDate"] = today.isoformat()
    journal.append("research_done",
                   f"providers={len(funnel.providers)} queries={st.queries} screened={st.screened} "
                   f"accepted={len(st.accepted)} claims={st.claims_made} alerts={len(alerts)}")


def _tally(f: Optional[ProviderFunnel], disp: screening.Disposition) -> None:
    if not f:
        return
    cat = _reason_category(disp.reason)
    if disp.status == "rejected":
        f.rejected += 1
        f.rejected_reasons[cat] += 1
    elif disp.status == "deferred":
        f.deferred += 1
        f.deferred_reasons[cat] += 1
    elif disp.status == "duplicate":
        f.duplicates_prior += 1
        f.duplicate_reasons[cat] += 1


def _explain_zero(prov: Provider, f: ProviderFunnel, ps: dict, alerts: list[Alert]) -> None:
    """A zero-result window must carry an explanation, and the right alert."""
    c = f.canary_hits
    if c is None:
        f.status, f.zero_reason = "zero_unexplained", "0 results and the wide-window canary could not be run"
        alerts.append(Alert(WARNING, "UNEXPECTED_ZERO", prov.name, f.zero_reason))
        return
    if c == 0:
        f.status = "invalid_query"
        f.zero_reason = ("0 results AND the wide-window canary in the same syntax also returned 0: the query/date filter is "
                         "broken or the provider is returning nothing")
        f.error = f.zero_reason
        alerts.append(Alert(ERROR, "INVALID_QUERY", prov.name, f.zero_reason))
        return
    f.status = "no_new_records"
    f.zero_reason = (f"provider healthy (wide-window canary returned {c}); no new matching records in "
                     f"{f.window.split(';')[0]}")
    if prov.expects_daily_results:
        ps["consecutiveUnexpectedZero"] = ps.get("consecutiveUnexpectedZero", 0) + 1
        n = ps["consecutiveUnexpectedZero"]
        if n >= config.REPEATED_ZERO_ERROR:
            alerts.append(Alert(ERROR, "REPEATED_UNEXPECTED_ZERO", prov.name,
                                f"{n} consecutive runs returned zero for a provider that normally returns results daily"))
        elif n >= config.REPEATED_ZERO_WARN:
            alerts.append(Alert(WARNING, "UNEXPECTED_ZERO", prov.name,
                                f"{n} consecutive zero-result runs for a provider that normally returns results daily"))
    else:
        alerts.append(Alert(INFO, "NO_NEW_RECORDS", prov.name, f.zero_reason))
