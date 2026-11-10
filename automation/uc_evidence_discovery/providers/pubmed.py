"""PubMed/MEDLINE connector. Syntax is PubMed's OWN: field tags (``[tiab]``, ``[MeSH Terms]``) and
``mindate``/``maxdate`` with ``datetype=edat`` (Entrez date), dates as ``YYYY/MM/DD``.

NCBI does not fail on unknown fields or unbalanced syntax - it quietly drops them and returns the whole database
(verified: a garbage term returned 64,066 hits). So every response is checked: NCBI's own ``querytranslation`` must
still contain our terms AND the Entrez-date filter, and error/warning lists must be empty.
"""

from __future__ import annotations

from ..apis import pubmed as api
from ..apis.http import Http
from .base import EvidenceType, InvalidQuery, Provider, SearchOutcome, Window
from .common import classify_publication, guarded, lint_query_balanced

UC_TERM = '("ulcerative colitis"[tiab] OR "colitis, ulcerative"[MeSH Terms])'


def _non_empty(d: dict) -> dict:
    return {k: v for k, v in (d or {}).items() if v}


def check_translation(translation: str, errors: dict, warnings: dict, *, expect: tuple[str, ...]) -> None:
    """Raise InvalidQuery if NCBI reinterpreted/ignored part of the query."""
    errs = _non_empty(errors)
    if errs:
        raise InvalidQuery(f"pubmed: NCBI reported query errors: {sorted(errs)}")
    warn = _non_empty(warnings)
    if warn:
        raise InvalidQuery(f"pubmed: NCBI query warnings: {sorted(warn)}")
    low = translation.lower()
    missing = [x for x in expect if x.lower() not in low]
    if missing:
        raise InvalidQuery(f"pubmed: NCBI query translation lost expected part(s): {missing}")


class PubMedProvider(Provider):
    name = "pubmed"
    label = "PubMed/MEDLINE"
    evidence_type = EvidenceType.PUBLISHED_STUDY
    expects_daily_results = True
    #: extra Boolean clause (PubMed syntax) - used by society-guideline channels
    extra_clause = ""
    expect_in_translation: tuple[str, ...] = ()

    def build_query(self, window: Window) -> str:
        q = UC_TERM + (f" AND ({self.extra_clause})" if self.extra_clause else "")
        lint_query_balanced(q, "pubmed")
        return q

    def _dates(self, window: Window) -> tuple[str, str]:
        s, e = window.iso()
        return s.replace("-", "/"), e.replace("-", "/")

    def search_window(self, http: Http, window: Window, *, max_pages: int) -> SearchOutcome:
        out = SearchOutcome()
        term = self.build_query(window)
        mindate, maxdate = self._dates(window)
        out.queries.append(f"{term}  [edat {mindate}..{maxdate}]")
        ids: list[str] = []
        start = 0
        for _ in range(max_pages):
            hit = guarded(self.name, api.esearch_window, http, term, mindate=mindate, maxdate=maxdate,
                          retstart=start, retmax=25)
            out.searches += 1
            out.hit_count = hit["count"]
            check_translation(hit["translation"], hit["errors"], hit["warnings"],
                              expect=("Date - Entry", "ulcerative colitis", *self.expect_in_translation))
            ids.extend(hit["ids"])
            start += len(hit["ids"])
            if not hit["ids"] or start >= hit["count"]:
                break
        for i in range(0, len(ids), 25):
            recs = guarded(self.name, api.efetch, http, ids[i:i + 25])
            out.searches += 1
            for rec in recs:
                rec["evidenceType"] = classify_publication(rec).value
                rec["accessStatus"] = ("open_access_abstract_only" if rec.get("pmcid")
                                       else "paywalled_metadata_and_abstract_only")
                rec["requiresFullTextVerification"] = True
                out.records.append(rec)
        out.truncated = out.hit_count > len(ids)
        return out
