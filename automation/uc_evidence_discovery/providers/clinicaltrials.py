"""ClinicalTrials.gov connector (API v2). Syntax is its OWN: ``filter.advanced=AREA[LastUpdatePostDate]RANGE[a,b]``.

Registry records are labelled as trials and NEVER as treatment-effect evidence:
    not finished  -> ongoing_trial            finished -> completed_trial_record (a registry entry, not a publication)
Downstream, no claim is ever extracted from either type. A malformed date range returns an empty 200 here,
so the wide-window canary is what detects a broken filter."""

from __future__ import annotations

from ..apis import clinicaltrials as api
from ..apis.http import Http
from .base import EvidenceType, Provider, SearchOutcome, Window
from .common import guarded

FINISHED = {"COMPLETED", "TERMINATED", "WITHDRAWN"}


def trial_evidence_type(status: str) -> EvidenceType:
    return EvidenceType.COMPLETED_TRIAL_RECORD if (status or "").upper() in FINISHED else EvidenceType.ONGOING_TRIAL


class ClinicalTrialsProvider(Provider):
    name = "clinicaltrials"
    label = "ClinicalTrials.gov"
    evidence_type = EvidenceType.ONGOING_TRIAL
    expects_daily_results = False

    def build_query(self, window: Window) -> str:
        s, e = window.iso()
        return f"cond=ulcerative colitis; AREA[LastUpdatePostDate]RANGE[{s},{e}]"

    def search_range(self, http: Http, window: Window, *, max_pages: int) -> SearchOutcome:
        out = SearchOutcome()
        s, e = window.iso()
        out.queries.append(self.build_query(window))
        token = None
        for _ in range(max_pages):
            page = guarded(self.name, api.search_window, http, start=s, end=e, page_token=token, page_size=25)
            out.searches += 1
            out.hit_count = int(page["hitCount"] or 0)
            for rec in page["records"]:
                rec["evidenceType"] = trial_evidence_type(rec.get("overallStatus", "")).value
                rec["accessStatus"] = "public_registry_record"
                rec["requiresFullTextVerification"] = False
                rec["noClaimsReason"] = "trial_registry_record_is_not_evidence_of_treatment_effect"
                out.records.append(rec)
            token = page["nextCursor"]
            if not token or not page["records"]:
                break
        out.truncated = out.hit_count > len(out.records)
        return out
