"""Europe PMC connector. Syntax is Europe PMC's OWN: ``FIRST_IDATE:[YYYY-MM-DD TO YYYY-MM-DD]``.

Root cause of the old zero-result runs: the runner sent a PubMed-style ``(2021:2026[pub_year])`` expression.
Europe PMC does not understand it and returns HTTP 200 with ``hitCount: 0`` - no error, just silence.
A malformed (e.g. unbalanced) Europe PMC query is no better: it can silently drop the clause and return the whole
corpus. So queries are generated here (never hand-typed), linted, and cross-checked against a wide-window canary.
"""

from __future__ import annotations

from ..apis import europepmc as api
from ..apis.http import Http
from .base import EvidenceType, InvalidQuery, Provider, SearchOutcome, Window
from .common import classify_publication, guarded, lint_query_balanced

_PUBMED_ONLY_TAGS = ("[pub_year]", "[tiab]", "[mesh", "[dp]", "[pdat]", "[ti]", "[tw]")


class EuropePmcProvider(Provider):
    name = "europepmc"
    label = "Europe PMC"
    evidence_type = EvidenceType.PUBLISHED_STUDY
    expects_daily_results = True

    def build_query(self, window: Window) -> str:
        s, e = window.iso()
        # FIRST_IDATE = date the record first entered Europe PMC: catches newly published AND newly indexed
        # items (FIRST_PDATE alone misses late-indexed records). Preprints are excluded: not peer reviewed.
        q = (f'("ulcerative colitis" OR "colitis, ulcerative") AND (FIRST_IDATE:[{s} TO {e}]) NOT SRC:PPR')
        self._lint(q)
        return q

    @staticmethod
    def _lint(q: str) -> None:
        lint_query_balanced(q, "europepmc")
        low = q.lower()
        for tag in _PUBMED_ONLY_TAGS:
            if tag in low:
                raise InvalidQuery(f"europepmc: PubMed-style field tag {tag!r} is not valid Europe PMC syntax")
        if "first_idate:[" not in low or " to " not in low:
            raise InvalidQuery("europepmc: generated query has no Europe PMC date range")

    def search_range(self, http: Http, window: Window, *, max_pages: int) -> SearchOutcome:
        out = SearchOutcome()
        query = self.build_query(window)
        out.queries.append(query)
        cursor = "*"
        for _ in range(max_pages):
            page = guarded(self.name, api.search, http, query, cursor=cursor, page_size=25)
            out.searches += 1
            out.hit_count = int(page["hitCount"] or 0)
            for rec in page["records"]:
                rec["evidenceType"] = classify_publication(rec).value
                rec["accessStatus"] = ("open_access_abstract_only" if rec.get("isOpenAccess") == "Y"
                                       else "paywalled_metadata_and_abstract_only")
                rec["requiresFullTextVerification"] = True
                out.records.append(rec)
            nxt = page["nextCursor"]
            if not nxt or nxt == cursor or not page["records"]:
                break
            cursor = nxt
        out.truncated = out.hit_count > len(out.records)
        return out
