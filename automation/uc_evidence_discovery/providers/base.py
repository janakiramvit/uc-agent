"""Provider contract, evidence types and the error taxonomy.

Evidence types are kept strictly separate end to end:

    published_study       peer-reviewed article (abstract only; never full text)
    clinical_guideline    society / agency guideline or consensus statement
    ongoing_trial         registered trial that is not finished
    completed_trial_record  registry entry of a finished trial (a registry record, NOT a publication)

A trial record is *never* turned into a treatment-effect claim (see ``extract``).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from ..apis.http import Http


class EvidenceType(str, Enum):
    PUBLISHED_STUDY = "published_study"
    CLINICAL_GUIDELINE = "clinical_guideline"
    ONGOING_TRIAL = "ongoing_trial"
    COMPLETED_TRIAL_RECORD = "completed_trial_record"

    @property
    def is_trial(self) -> bool:
        return self in (EvidenceType.ONGOING_TRIAL, EvidenceType.COMPLETED_TRIAL_RECORD)


# -- errors -------------------------------------------------------------------------------------
class ProviderError(RuntimeError):
    code = "PROVIDER_FAILURE"


class ProviderUnavailable(ProviderError):
    """Network/5xx/timeout after retries."""
    code = "PROVIDER_FAILURE"


class InvalidQuery(ProviderError):
    """The provider rejected the query (HTTP 400) or returned a syntax/validation error."""
    code = "INVALID_QUERY"


class AccessLimited(ProviderError):
    """Automated access is not permitted (robots.txt / terms). Legitimate; reported, never bypassed."""
    code = "ACCESS_LIMITED"


# -- window -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Window:
    """Inclusive date window [start, end]. Providers format it in their own syntax."""

    start: _dt.date
    end: _dt.date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def iso(self) -> tuple[str, str]:
        return self.start.isoformat(), self.end.isoformat()


@dataclass
class SearchOutcome:
    records: list[dict] = field(default_factory=list)
    hit_count: int = 0                 # total the provider says matched the window
    searches: int = 0                  # HTTP search calls made
    queries: list[str] = field(default_factory=list)    # exact provider-syntax queries (for the report)
    truncated: bool = False            # hit_count > records fetched (page cap) -> window not complete
    access_limits: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class Provider:
    """Subclasses set the class attributes and implement ``search_window`` and ``build_query``."""

    name = ""
    label = ""
    evidence_type = EvidenceType.PUBLISHED_STUDY
    #: Europe PMC / PubMed index UC literature daily; a zero window there is suspicious.
    expects_daily_results = False

    def build_query(self, window: Window) -> str:                      # pragma: no cover - interface
        raise NotImplementedError

    def search_window(self, http: Http, window: Window, *, max_pages: int) -> SearchOutcome:  # pragma: no cover
        raise NotImplementedError

    def canary_window(self, today: _dt.date) -> Window:
        """A deliberately wide window in the SAME syntax: if it is also empty the query/provider is broken."""
        return Window(today - _dt.timedelta(days=365), today)

    def canary_count(self, http: Http, today: _dt.date) -> int:
        out = self.search_window(http, self.canary_window(today), max_pages=1)
        return out.hit_count


RecordFilter = Callable[[dict], bool]
