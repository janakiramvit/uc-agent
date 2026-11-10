"""Per-provider funnel and run-level aggregation.

For every provider, every run: searches attempted -> results returned -> records screened ->
duplicates -> rejected/deferred (with reasons) -> sources accepted -> claims extracted."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

STATUSES = ("ok", "no_new_records", "zero_unexplained", "failed", "invalid_query", "access_limited",
            "skipped_deadline", "partial")


@dataclass
class ProviderFunnel:
    provider: str
    label: str
    evidence_type: str
    window: str = ""
    queries: list[str] = field(default_factory=list)
    searches_attempted: int = 0
    searches_failed: int = 0
    hit_count: int = 0
    results_returned: int = 0
    records_screened: int = 0
    duplicates_cross: int = 0      # merged into another provider's (or this provider's own) record before screening
    duplicates_prior: int = 0      # already accepted/rejected in an earlier run (found at screening)
    rejected: int = 0
    deferred: int = 0
    accepted: int = 0
    claims_extracted: int = 0
    not_screened_limit: int = 0
    rejected_reasons: Counter = field(default_factory=Counter)
    deferred_reasons: Counter = field(default_factory=Counter)
    duplicate_reasons: Counter = field(default_factory=Counter)
    status: str = "ok"
    zero_reason: Optional[str] = None
    canary_hits: Optional[int] = None
    error: Optional[str] = None
    access_limits: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    advanced_cutoff: bool = False

    @property
    def duplicates(self) -> int:
        return self.duplicates_cross + self.duplicates_prior

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["duplicates"] = self.duplicates
        for k in ("rejected_reasons", "deferred_reasons", "duplicate_reasons"):
            d[k] = dict(sorted(d[k].items()))
        return d

    def reconcile(self) -> list[str]:
        """Internal-consistency checks used by tests and QA: every returned record has exactly one fate."""
        problems = []
        if self.rejected + self.deferred + self.accepted + self.duplicates_prior != self.records_screened:
            problems.append("dispositions do not add up to records screened")
        if self.duplicates_cross + self.records_screened + self.not_screened_limit != self.results_returned:
            problems.append("every returned record must be exactly one of: merged duplicate, screened, not screened")
        return problems


@dataclass
class RunFunnel:
    providers: dict[str, ProviderFunnel] = field(default_factory=dict)

    def get(self, name: str) -> ProviderFunnel:
        return self.providers[name]

    def totals(self) -> dict:
        keys = ("searches_attempted", "results_returned", "records_screened", "duplicates", "rejected",
                "deferred", "accepted", "claims_extracted")
        return {k: sum(getattr(p, k) for p in self.providers.values()) for k in keys}

    def to_dict(self) -> dict:
        return {"totals": self.totals(), "providers": {k: v.to_dict() for k, v in self.providers.items()}}
