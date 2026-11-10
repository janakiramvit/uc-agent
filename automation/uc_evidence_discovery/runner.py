"""Orchestrator.

Order (enforced; see tests/test_state_root_separation.py):

    resolve & validate --state-root (a git worktree of automation/uc-evidence-staging,
        never on sys.path, outside the trusted-code tree)
    -> acquire lock (inside state-root)
    -> checkpoint validation (from state-root; schema read from the main checkout)
    -> continuation (resume the saved topic / search / cursor)
    -> research  (stop at the 450 s soft deadline or any hard daily limit)
    -> QA
    -> atomic checkpoint update (+ known-good) inside state-root
    -> journal
    -> redacted artifact (under the main checkout)
    -> commit + push the staging branch (no empty commits)
    -> release lock
    -> remove the worktree (from the main checkout, explicit target path)

Every read/write of evidence/checkpoint/journal/lock goes through ``--state-root``. Schema
files, rule tables and all Python load only from the ``main`` checkout.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

from . import PROMPT_VERSION, __version__
from . import artifact as artifact_mod
from . import checkpoint as checkpoint_mod
from . import config, gitio, ids
from . import journal as journal_mod
from . import discover, lockfile, package, provider_state, qa, reporting, screening
from .alerts import has_errors
from .apis.http import Http
from .clock import Deadline
from .dedup import CandidateKey, ProcessedIndex
from .errors import LockHeld, SafeStop, UntrustedStateRoot
from .extract import extract_candidates, verify_verbatim
from .licensing import plan_archival


# ----------------------------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="uc_evidence_discovery")
    p.add_argument("--state-root", required=True,
                   help="path to a git worktree checked out on automation/uc-evidence-staging")
    p.add_argument("--soft-deadline-seconds", type=int, default=config.SOFT_DEADLINE_SECONDS)
    p.add_argument("--finalize-deadline-seconds", type=int, default=config.FINALIZE_DEADLINE_SECONDS)
    p.add_argument("--dry-run", action="store_true", help="run everything except commit/push")
    p.add_argument("--no-network", action="store_true", help="skip the research loop entirely")
    p.add_argument("--no-push", action="store_true",
                   help="do the research and write the worktree, but skip commit/push (controlled live runs)")
    p.add_argument("--validate-checkpoint", action="store_true",
                   help="load + schema-validate the state-root checkpoint, print status, exit")
    p.add_argument("--allow-bootstrap", action="store_true",
                   help="(manual seed only) tolerate an empty/missing package")
    return p.parse_args(argv)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> _dt.date:
    """UTC calendar date of this run. ``UC_DISCOVERY_TODAY=YYYY-MM-DD`` overrides it (tests, controlled runs)."""
    override = os.environ.get("UC_DISCOVERY_TODAY")
    if override:
        return _dt.date.fromisoformat(override)
    return _dt.datetime.now(_dt.timezone.utc).date()


def _github_run_url() -> str:
    # Constructed by the workflow; never assume a built-in GITHUB_RUN_URL.
    return os.environ.get("GITHUB_RUN_URL", "")


def _run_id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1] if url else ""


def _actions_run_active(run_id: str):
    """True/False/None. Only used to decide whether a *stale* lock may be reclaimed."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not (token and repo and run_id.isdigit()):
        return None
    try:
        import requests

        r = requests.get(
            f"https://api.github.com/repos/{repo}/actions/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "User-Agent": config.USER_AGENT},
            timeout=15,
        )
        if r.status_code == 404:
            return False
        r.raise_for_status()
        status = r.json().get("status", "")
        return status not in ("completed",)
    except Exception:
        return None


# ----------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    try:
        paths = gitio.resolve_state_root(args.state_root)
    except (UntrustedStateRoot, SafeStop) as exc:
        print(f"[uc-evidence] SAFE STOP: {exc}", file=sys.stderr)
        return 0

    # Hard guarantee: the state root is not importable and does not shadow trusted code.
    assert str(paths.root) not in sys.path, "state-root leaked onto sys.path"

    if args.validate_checkpoint:
        try:
            res = checkpoint_mod.load(paths)
        except SafeStop as exc:
            print(f"[uc-evidence] checkpoint INVALID: {exc}")
            return 1
        print(f"[uc-evidence] checkpoint OK (source={res.source}, recovered={res.recovered})")
        if res.prompt_difference:
            print(f"[uc-evidence] prompt/checkpoint difference: {json.dumps(res.prompt_difference)}")
        return 0

    clock = Deadline(soft_seconds=args.soft_deadline_seconds,
                     finalize_seconds=args.finalize_deadline_seconds)
    run_url = _github_run_url()
    run_id = checkpoint_mod.new_run_id()
    triggering_commit = os.environ.get("GITHUB_SHA", "")
    journal = journal_mod.Journal(paths.journal_path, run_id)
    journal.append("run_started",
                   f"runner {__version__} / {PROMPT_VERSION}; state-root={paths.root.name}; "
                   f"dry_run={args.dry_run} no_network={args.no_network}")

    lock_info = lockfile.LockInfo.new(
        run_id=run_id, run_url=run_url, commit=triggering_commit,
        ttl_seconds=config.HARD_TIMEOUT_SECONDS + 600,
    )
    lock_acquired = False
    status = "completed"
    error_categories: list[str] = []
    try:
        try:
            lockfile.acquire(paths.lock_path, lock_info, is_run_active=_actions_run_active)
            lock_acquired = True
        except LockHeld as exc:
            journal.append("lock_not_acquired", str(exc))
            print(f"[uc-evidence] SAFE STOP: {exc}", file=sys.stderr)
            return 0

        # ---- checkpoint ---------------------------------------------------------------------
        try:
            loaded = checkpoint_mod.load(paths)
        except SafeStop as exc:
            journal.append("checkpoint_invalid", str(exc))
            print(f"[uc-evidence] SAFE STOP: {exc}", file=sys.stderr)
            return 0
        cp = checkpoint_mod.upgrade_schema_version(dict(loaded.doc))
        if loaded.recovered:
            journal.append("checkpoint_recovered", "primary invalid; restored from known-good")
        if loaded.prompt_difference:
            journal.append("prompt_vs_checkpoint",
                           "checkpoint is authoritative; prompt resume hints ignored")
            cp["promptVsCheckpointDifference"] = loaded.prompt_difference

        try:
            pstate = provider_state.load(paths)
        except SafeStop as exc:
            journal.append("provider_state_invalid", str(exc))
            print(f"[uc-evidence] SAFE STOP: {exc}", file=sys.stderr)
            return 1

        index = ProcessedIndex.from_checkpoint(cp)
        if paths.sources_path.exists():
            index.merge_sources_json(json.loads(paths.sources_path.read_text("utf-8")))
        allocator = ids.Allocator.from_state(paths, cp)

        # ---- research --------------------------------------------------------------------
        research = _ResearchState(cp)
        today = _today()
        if not args.no_network and not args.dry_run:
            discover.run(http=Http(enabled=True), clock=clock, pstate=pstate, index=index, allocator=allocator,
                         st=research, journal=journal, today=today)
        else:
            journal.append("research_skipped",
                           "no_network/dry_run: discovery loop not executed")

        # ---- finalize (must complete before the finalize deadline) ------------------------
        cutoff = research.latest_pub_seen or _now_iso()
        merge_summary = {"newSources": 0, "newClaims": 0, "sourcesTotal": 0, "claimsTotal": 0}
        licensing_entries = [a["licensing"] for a in research.accepted]
        if research.accepted:
            merge_summary = package.merge(
                paths, run_id=run_id, accepted=research.accepted, licensing_entries=licensing_entries,
            )
            package.update_coverage_map(
                paths, run_id=run_id, topic_id=research.topic_id,
                next_topic_id=research.next_topic_id,
            )
            all_sources = json.loads(paths.sources_path.read_text("utf-8"))["sources"]
            all_claims = json.loads(paths.claims_path.read_text("utf-8"))["claims"]
            package.write_reviewer_workbook(paths, run_id=run_id, sources=all_sources, claims=all_claims)

        counters = research.counters(clock)
        new_cp = _build_checkpoint(cp, run_id, run_url, triggering_commit, research, counters,
                                   cutoff, status_hint=research.status)
        qa_summary = qa.run_checks(paths, run_id=run_id, checkpoint_doc=new_cp, counters=counters)
        package.write_reports(
            paths, run_id=run_id, run_url=run_url, counters=counters,
            dispositions=research.disposition_counts(), qa_summary=qa_summary,
            next_operation=new_cp["nextRecommendedOperation"], status=research.status,
        )

        checkpoint_mod.save(paths, new_cp)
        if research.funnel is not None:
            _write_provider_outputs(paths, run_id, run_url, today, research, pstate)
        journal.append("checkpoint_saved",
                       f"status={research.status}; accepted={counters['sourcesAccepted']}; "
                       f"claims={counters['claimsExtracted']}; screened={counters['recordsScreened']}")

        accepted_source_records = [a["sourceRecord"] for a in research.accepted]
        artifact_mod.build(
            run_id=run_id, run_url=run_url, started_at=cp.get("_runnerStartedAt", _now_iso()),
            finished_at=_now_iso(), source_data_cutoff=cutoff, status=research.status,
            counters=counters, disposition_reason_categories=research.reason_categories(),
            accepted_sources=accepted_source_records, query_labels=research.query_labels,
            qa_summary=qa_summary, checkpoint_valid=not checkpoint_mod.validate(new_cp),
            next_topic_id=research.next_topic_id, error_categories=error_categories,
            provider_health=(reporting.provider_health_for_artifact(research.funnel) if research.funnel else None),
            alert_counts=_alert_counts(research.alerts),
        )
        journal.append("artifact_written", "redacted artifact built under the main checkout")

        if args.no_push:
            journal.append("no_push", "commit/push skipped (--no-push); results left in the state worktree")
        elif not args.dry_run:
            staged = gitio.stage_paths(paths)
            sha = gitio.commit(paths, date=_dt.date.today().isoformat())
            if sha:
                gitio.push(paths)
                journal.append("staging_pushed", f"commit {sha[:12]} to {config.STAGING_BRANCH}")
            else:
                journal.append("no_changes", "nothing to commit; no empty commit created")
        else:
            journal.append("dry_run", "commit/push skipped")

        status = research.status
        for line in reporting.github_annotations(research.alerts):
            print(line)
        if has_errors(research.alerts):
            # evidence + state are already staged; a non-zero exit makes GitHub flag the run so it is not silent
            print("[uc-evidence] one or more ERROR alerts - see DAILY-REPORT.md on the staging branch", file=sys.stderr)
            return 1
        return 0

    except Exception as exc:  # noqa: BLE001 - last-resort: preserve recoverable state, don't crash the job
        error_categories.append(type(exc).__name__)
        journal.append("error_handled", f"{type(exc).__name__}: {exc}")
        print(f"[uc-evidence] handled error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"::error title=UC discovery crashed::{type(exc).__name__}")
        status = "failed"
        return 1
    finally:
        if lock_acquired:
            lockfile.release(paths.lock_path, run_id)
            journal.append("lock_released", "run lock released in finally")
        # journal lives inside the worktree -- write the final entry BEFORE any removal
        journal.append("run_finished", f"status={status}")
        # --dry-run intentionally leaves the worktree in place so a developer can inspect the
        # would-be checkpoint/journal/reports (see automation/README.md); every real run
        # (including a safe-stop or a handled crash) removes it, from its own primary
        # checkout, with an explicit target path.
        if not args.dry_run and not args.no_push:
            gitio.remove_worktree(paths.root, paths.primary_checkout or config.REPO_ROOT)


# ----------------------------------------------------------------------------------------------
class _ResearchState:
    def __init__(self, cp: dict) -> None:
        nro = cp.get("nextRecommendedOperation", {}) or {}
        self.topic_id = nro.get("topicId") or cp.get("currentTopicId") or "T-UCX-03"
        self.next_topic_id = self.topic_id
        self.pending = list(cp.get("pendingSearches", []) or [])
        self.query_labels: list[str] = []
        self.screened = 0
        self.queries = 0
        self.accepted: list[dict] = []
        self.claims_made = 0
        self.dispositions: list[screening.Disposition] = []
        self.latest_pub_seen = ""
        self.consecutive_empty = 0
        self.stop_reason = "no_research_executed"
        self._elapsed = 0.0
        self.funnel = None                 # RunFunnel, set by discover.run
        self.alerts: list = []
        self.missed_dates: list[str] = []
        self.provider_windows: dict = {}
        self.cross_provider_merges: list = []

    @property
    def status(self) -> str:
        if not self.accepted and self.screened == 0 and self.queries == 0:
            return "partial_no_op"
        if (self.queries >= config.MAX_QUERIES or self.screened >= config.MAX_SCREENED
                or len(self.accepted) >= config.MAX_ACCEPTED or self.claims_made >= config.MAX_CLAIMS
                or self.pending):
            return "partial"
        return "completed"

    def counters(self, clock: Deadline) -> dict:
        return {
            "elapsedResearchSeconds": round(self._elapsed or clock.elapsed(), 1),
            "queriesConsumed": self.queries,
            "recordsScreened": self.screened,
            "sourcesAccepted": len(self.accepted),
            "pdfsDownloaded": 0,
            "claimsExtracted": self.claims_made,
        }

    def disposition_counts(self) -> dict:
        out = {k: 0 for k in screening.DISPOSITIONS}
        for d in self.dispositions:
            out[d.status] += 1
        return out

    def reason_categories(self) -> dict:
        cats: dict[str, int] = {}
        for d in self.dispositions:
            cat = d.reason.split(":", 1)[0]
            cats[cat] = cats.get(cat, 0) + 1
        return cats


def _alert_counts(alerts: list) -> dict:
    out: dict[str, int] = {}
    for a in alerts:
        key = f"{a.level}:{a.code}"
        out[key] = out.get(key, 0) + 1
    return out


def _write_provider_outputs(paths, run_id: str, run_url: str, today: _dt.date, st, pstate: dict) -> None:
    """Funnel JSON + human-readable daily report on the staging branch, then the provider cutoffs."""
    doc = reporting.funnel_document(run_id, today, st.funnel, st.alerts, st.missed_dates)
    paths.provider_funnel_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                                          encoding="utf-8")
    accepted = [(a["sourceRecord"]["sourceId"], a["sourceRecord"].get("evidenceType", ""),
                 a["sourceRecord"].get("title", "")) for a in st.accepted]
    paths.daily_report_path.write_text(
        reporting.render_daily_report(run_id, run_url, today, st.funnel, st.alerts, st.missed_dates, accepted),
        encoding="utf-8")
    pstate.setdefault("runHistory", []).append({
        "date": today.isoformat(), "runId": run_id,
        "window": next(iter(st.funnel.providers.values())).window.split(";")[0] if st.funnel.providers else "",
        "missedDates": st.missed_dates,
        "providerStatus": {n: f.status for n, f in st.funnel.providers.items()},
        "alerts": len(st.alerts), "errors": sum(1 for a in st.alerts if a.level == "ERROR")})
    pstate["lastRunId"] = run_id
    provider_state.save(paths, pstate)


def _build_checkpoint(cp: dict, run_id: str, run_url: str, commit: str, st: _ResearchState,
                      counters: dict, cutoff: str, status_hint: str) -> dict:
    now = _now_iso()
    out = dict(cp)
    out["schemaVersion"] = config.SCHEMA_VERSION_1_1_0
    out["runId"] = run_id
    out["promptVersion"] = PROMPT_VERSION
    out["workflowRunUrl"] = run_url
    out["triggeringCommit"] = commit
    out["runStartTime"] = cp.get("runStartTime") or now
    out["runFinishTime"] = now
    out["lastCheckpointTime"] = now
    out["runStatus"] = "partially_completed" if status_hint.startswith("partial") else (
        "completed" if status_hint == "completed" else "partially_completed"
    )
    out["sourceDataCutoff"] = cutoff
    out["latestPublicationTimestampEncountered"] = st.latest_pub_seen or cp.get(
        "latestPublicationTimestampEncountered")

    # accepted / rejected / deferred / duplicate — mutually exclusive, each with a reason
    accepted_records = list(cp.get("acceptedRecords", []))
    rejected_records = list(cp.get("rejectedRecords", []))
    deferred_records = list(cp.get("deferredRecords", []))
    duplicate_records = list(cp.get("duplicateRecords", []))
    for a, d in zip(st.accepted, [x for x in st.dispositions if x.status == "accepted"]):
        accepted_records.append({
            "sourceId": a["sourceRecord"]["sourceId"],
            "pubmedId": a["record"].get("pmid", ""),
            "decision": "accepted",
            "reason": d.reason,
            "archivalStatus": a["sourceRecord"]["archivalStatus"],
            "requiresHumanReview": d.requires_human_review,
        })
    for d in st.dispositions:
        entry = {"identifier": _disp_identifier(d), "reason": d.reason}
        if d.status == "rejected":
            rejected_records.append(entry)
        elif d.status == "deferred":
            deferred_records.append(entry)
        elif d.status == "duplicate":
            duplicate_records.append(entry)
    out["acceptedRecords"] = accepted_records
    out["rejectedRecords"] = rejected_records
    out["deferredRecords"] = deferred_records
    out["duplicateRecords"] = duplicate_records

    out["completedSearches"] = list(cp.get("completedSearches", [])) + [
        {"searchId": f"{name}-{run_id[-6:]}", "service": name,
         "query": (f.queries[0] if f.queries else f.window)[:300],
         "resultsScreened": f.records_screened, "executedAt": now}
        for name, f in ((st.funnel.providers.items()) if st.funnel else [])
    ]
    out["pendingSearches"] = st.pending
    out["currentTopicId"] = st.topic_id
    out["currentSearchStrategyId"] = (st.pending[0].get("searchId") if st.pending else None)
    out["currentSearchQuery"] = (st.pending[0].get("query") if st.pending else None)
    out["currentApiCursor"] = (st.pending[0].get("cursor", 0) if st.pending else 0)
    out["lastProcessedRecord"] = f"{counters['recordsScreened']} screened this run"

    # processed identifiers (v1.1.0 adds pmcid + trialId)
    psi = {
        "doi": sorted({*_as_list(cp, "doi"), *[a["record"].get("doi", "") for a in st.accepted]} - {""}),
        "pubmedId": sorted({*_as_list(cp, "pubmedId"), *[a["record"].get("pmid", "") for a in st.accepted]} - {""}),
        "pmcid": sorted({*_as_list(cp, "pmcid"), *[a["record"].get("pmcid", "") for a in st.accepted]} - {""}),
        "trialId": sorted({*_as_list(cp, "trialId"), *[a["record"].get("nctId", "") for a in st.accepted]} - {""}),
        "canonicalUrl": sorted({*_as_list(cp, "canonicalUrl"),
                                *[a["record"].get("canonicalUrl", "") for a in st.accepted]} - {""}),
        "checksum": sorted({*_as_list(cp, "checksum"),
                            *[CandidateKey.from_record(a["record"]).checksum for a in st.accepted]} - {""}),
        "normalizedTitle": sorted({*_as_list(cp, "normalizedTitle"),
                                   *[CandidateKey.from_record(a["record"]).normalized_title
                                     for a in st.accepted]} - {""}),
    }
    out["processedSourceIdentifiers"] = psi

    prev = cp.get("counters", {})
    out["counters"] = {
        "elapsedResearchSeconds": counters["elapsedResearchSeconds"],
        "queriesConsumed": counters["queriesConsumed"],
        "recordsScreened": counters["recordsScreened"],
        "sourcesAccepted": counters["sourcesAccepted"],
        "pdfsDownloaded": 0,
        "claimsExtracted": counters["claimsExtracted"],
    }
    out["limitConsumption"] = {
        "queries": f"{counters['queriesConsumed']}/{config.MAX_QUERIES}",
        "screened": f"{counters['recordsScreened']}/{config.MAX_SCREENED}",
        "accepted": f"{counters['sourcesAccepted']}/{config.MAX_ACCEPTED}",
        "claims": f"{counters['claimsExtracted']}/{config.MAX_CLAIMS}",
    }
    out["failedItems"] = list(cp.get("failedItems", []))
    out["retryCounts"] = cp.get("retryCounts", {})
    out["stopReason"] = st.stop_reason
    out["accessAndLicensingStatus"] = "all sources link_only; no redistribution licence established; 0 files archived; no PDFs downloaded"
    out["completedTopics"] = sorted(set(cp.get("completedTopics", [])) |
                                    ({st.topic_id} if status_hint == "completed" else set()))
    out["pendingTopics"] = cp.get("pendingTopics", [])

    first_src = st.accepted and None
    out["nextRecommendedOperation"] = {
        "description": (
            "Next run: search every configured provider (Europe PMC, PubMed, ClinicalTrials.gov, AGA, ACG, ECCO, NICE, "
            "BSG) for evidence published or updated since that provider's last successful cutoff "
            "(state/provider-state.json). Skip every identifier in processedSourceIdentifiers. "
            f"Allocate new ids from {_peek(cp, st)} onward."
        ),
        "topicId": st.next_topic_id,
        "searchId": out["currentSearchStrategyId"],
        "cursor": out["currentApiCursor"],
        "firstNewSourceId": _next_src_after(cp, st),
        "firstNewClaimId": _next_clm_after(cp, st),
        "doNot": [
            "approve any source or claim",
            "download a PDF whose redistribution licence is not established",
            "promote anything to the production RAG/vector index or Supabase",
            "convert Crohn's-only or IBD-general findings to UC-specific claims",
            "make any paid model or API call",
        ],
    }
    out.pop("_runnerStartedAt", None)
    if "limits" in cp:
        out["limits"] = cp["limits"]
    return out


def _as_list(cp: dict, key: str) -> set:
    return set((cp.get("processedSourceIdentifiers", {}) or {}).get(
        {"pmid": "pubmedId"}.get(key, key), []) or [])


def _disp_identifier(d: screening.Disposition) -> str:
    return f"topic={d.topic_id};applicability={d.applicability};kw={','.join(d.matched_keywords[:3])}"


def _peek(cp: dict, st: _ResearchState) -> str:
    return f"{_next_src_after(cp, st)}/{_next_clm_after(cp, st)}"


def _next_src_after(cp: dict, st: _ResearchState) -> str:
    used = set()
    blob = json.dumps(cp)
    import re as _re

    used |= {int(m) for m in _re.findall(r"SRC-(\d{3,})", blob)}
    used |= {int(a["sourceRecord"]["sourceId"].split("-")[1]) for a in st.accepted}
    n = max(used | {config.SOURCE_ID_FLOOR}) + 1
    return f"SRC-{n:03d}"


def _next_clm_after(cp: dict, st: _ResearchState) -> str:
    used = set()
    import re as _re

    used |= {int(m) for m in _re.findall(r"CLM-(\d{3,})", json.dumps(cp))}
    for a in st.accepted:
        for c in a["claims"]:
            used.add(int(c["claimId"].split("-")[1]))
    n = max(used | {config.CLAIM_ID_FLOOR}) + 1
    return f"CLM-{n:03d}"
