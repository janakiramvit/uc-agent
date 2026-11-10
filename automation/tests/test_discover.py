"""Multi-provider orchestration with fake providers: isolation, funnel accounting, zero-result explanations, alerts,
cross-provider de-duplication, limits, cutoff advancement and missed-run catch-up."""

from __future__ import annotations

import datetime as dt

import pytest

from uc_evidence_discovery import config, discover, ids, provider_state, runner
from uc_evidence_discovery.clock import Deadline
from uc_evidence_discovery.dedup import ProcessedIndex
from uc_evidence_discovery.providers.base import (AccessLimited, EvidenceType, InvalidQuery, Provider, ProviderUnavailable,
                                                  SearchOutcome, Window)

TODAY = dt.date(2026, 11, 10)

UC_ABSTRACT = ("In this randomised study of ulcerative colitis, fecal calprotectin was measured at baseline and at week "
               "eight. Treat to target strategies and mucosal healing were assessed in all participants. "
               "Endoscopic remission rates were higher in the intervention arm than in the control arm of this "
               "ulcerative colitis cohort.")


def make_record(i: int, provider: str, **kw) -> dict:
    rec = {"provider": provider, "title": f"Mucosal healing and treat to target in ulcerative colitis study {i}",
           "doi": f"10.9999/x{i}", "pmid": str(900000 + i), "pmcid": "", "nctId": "", "journal": "Gut",
           "pubYear": "2026", "publicationDate": "2026-11-10", "abstractText": UC_ABSTRACT,
           "canonicalUrl": f"https://doi.org/10.9999/x{i}", "evidenceType": "published_study",
           "requiresFullTextVerification": True, "accessStatus": "open_access_abstract_only",
           "retrievedVia": f"fake {provider}", "license": ""}
    rec.update(kw)
    return rec


class FakeProvider(Provider):
    def __init__(self, name, records=None, *, error=None, canary=100000, hits=None, truncated=False, access=None,
                 expects_daily=False, evidence_type=EvidenceType.PUBLISHED_STUDY, covered=None, canary_error=True):
        self.name, self.label, self.evidence_type = name, name.upper(), evidence_type
        self.expects_daily_results = expects_daily
        self._records, self._error, self._canary = list(records or []), error, canary
        self._hits, self._truncated, self._access = hits, truncated, access or []
        self._covered = covered
        self.canary_zero_is_error = canary_error
        self.windows: list[Window] = []
        self.searched = 0

    def build_query(self, window):
        return f"{self.name}-query {window.iso()}"

    def search_window(self, http, window, *, max_pages):
        self.searched += 1
        self.windows.append(window)
        if self._error:
            raise self._error
        recs = [dict(r) for r in self._records]
        covered = self._covered(window) if callable(self._covered) else self._covered
        return SearchOutcome(records=recs, hit_count=self._hits if self._hits is not None else len(recs), searches=1,
                             queries=[self.build_query(window)], truncated=self._truncated, access_limits=list(self._access),
                             covered_through=covered)

    def canary_count(self, http, today, window=None):
        return self._canary


class Journal:
    def append(self, *a, **k):
        pass


def run_once(providers, *, pstate=None, index=None, today=TODAY, soft=999.0, http=None):
    st = runner._ResearchState({"nextRecommendedOperation": {"topicId": "T-UCX-03"}, "pendingSearches": []})
    pstate = pstate if pstate is not None else provider_state.empty_state()
    index = index if index is not None else ProcessedIndex()
    discover.run(http=http or object(), clock=Deadline(soft_seconds=soft, finalize_seconds=soft + 60), pstate=pstate,
                 index=index, allocator=ids.Allocator(set(), set()), st=st, journal=Journal(), today=today,
                 providers=providers)
    return st, pstate


def codes(st, level=None):
    return [(a.level, a.code, a.provider) for a in st.alerts if level is None or a.level == level]


# ------------------------------------------------------------------ isolation + reporting
def test_every_provider_is_attempted_and_independently_reported_even_when_one_fails():
    provs = [FakeProvider("europepmc", [make_record(1, "europepmc")]),
             FakeProvider("pubmed", error=ProviderUnavailable("pubmed: HTTP 503")),
             FakeProvider("clinicaltrials", [make_record(3, "clinicaltrials", doi="", pmid="", nctId="NCT01234567",
                                                          evidenceType="ongoing_trial", journal="ClinicalTrials.gov registry",
                                                          canonicalUrl="https://clinicaltrials.gov/study/NCT01234567",
                                                          title="Ulcerative colitis trial treat to target")]),
             FakeProvider("acg", access=["gi.org: robots.txt disallows"], records=[])]
    st, ps = run_once(provs)
    assert set(st.funnel.providers) == {"europepmc", "pubmed", "clinicaltrials", "acg"}
    assert all(p.searched == 1 for p in provs)                         # the failure did not stop the others
    assert st.funnel.providers["pubmed"].status == "failed"
    assert ("ERROR", "PROVIDER_FAILURE", "pubmed") in codes(st)
    assert st.funnel.providers["europepmc"].accepted == 1


def test_funnel_accounts_for_every_returned_record_exactly_once():
    recs = [make_record(i, "europepmc") for i in range(6)]
    recs[1]["abstractText"] = ""                                        # deferred: no abstract
    recs[2]["title"] = "Crohn disease dietary study"; recs[2]["abstractText"] = "crohn disease " * 30   # rejected
    dup = make_record(0, "pubmed")                                       # cross-provider duplicate of recs[0]
    st, _ = run_once([FakeProvider("europepmc", recs), FakeProvider("pubmed", [dup, make_record(50, "pubmed")])])
    for f in st.funnel.providers.values():
        assert f.reconcile() == [], (f.provider, f.reconcile())
    e, p = st.funnel.providers["europepmc"], st.funnel.providers["pubmed"]
    assert e.results_returned == 6 and e.deferred == 1 and e.rejected == 1
    assert p.duplicates_cross == 1 and p.results_returned == 2


def test_cross_provider_duplicate_becomes_one_accepted_source_listing_both_finders():
    same_e = make_record(7, "europepmc")
    same_p = make_record(7, "pubmed", pmcid="PMC77")
    st, _ = run_once([FakeProvider("europepmc", [same_e]), FakeProvider("pubmed", [same_p])])
    assert len(st.accepted) == 1
    assert sorted(st.accepted[0]["sourceRecord"]["foundBy"]) == ["europepmc", "pubmed"]
    assert st.accepted[0]["sourceRecord"]["pmcId"] == "PMC77"
    assert sum(f.duplicates for f in st.funnel.providers.values()) == 1


def test_second_run_reports_already_seen_records_as_duplicates_not_new_sources():
    idx = ProcessedIndex()
    prov = lambda: [FakeProvider("europepmc", [make_record(1, "europepmc"), make_record(2, "europepmc")])]
    st1, ps = run_once(prov(), index=idx)
    st2, _ = run_once(prov(), index=idx, pstate=ps, today=TODAY + dt.timedelta(days=1))
    assert len(st1.accepted) == 2 and len(st2.accepted) == 0
    assert st2.funnel.providers["europepmc"].duplicates_prior == 2


def test_rejected_records_are_remembered_and_not_rescreened():
    bad = make_record(9, "europepmc", title="Crohn disease diet", abstractText="crohn disease " * 30)
    st1, ps = run_once([FakeProvider("europepmc", [bad])])
    assert st1.funnel.providers["europepmc"].rejected == 1
    st2, _ = run_once([FakeProvider("europepmc", [bad])], pstate=ps, today=TODAY + dt.timedelta(days=1))
    f = st2.funnel.providers["europepmc"]
    assert f.rejected == 0 and f.duplicates_prior == 1 and f.duplicate_reasons["duplicate_previously_rejected"] == 1


# ------------------------------------------------------------------ trials are never claims
def test_trial_registry_records_are_accepted_as_labelled_trials_with_zero_claims():
    trial = make_record(1, "clinicaltrials", doi="", pmid="", nctId="NCT07000001", evidenceType="ongoing_trial",
                        journal="ClinicalTrials.gov registry", canonicalUrl="https://clinicaltrials.gov/study/NCT07000001",
                        title="Mirikizumab treat to target ulcerative colitis trial",
                        abstractText="This ulcerative colitis study will evaluate whether mucosal healing improves." * 3)
    st, _ = run_once([FakeProvider("clinicaltrials", [trial], evidence_type=EvidenceType.ONGOING_TRIAL)])
    (acc,) = st.accepted
    assert acc["claims"] == [] and st.claims_made == 0
    src = acc["sourceRecord"]
    assert src["evidenceType"] == "ongoing_trial" and "ongoing clinical trial" in src["sourceType"]
    assert src["clinicalTrialsId"] == "NCT07000001" and "NOT evidence of treatment effect" in src["limitations"]


def test_extract_candidates_refuses_trial_records_even_if_called_directly():
    from uc_evidence_discovery.extract import extract_candidates
    rec = make_record(1, "clinicaltrials", evidenceType="completed_trial_record")
    assert extract_candidates(rec, source_id="SRC-1", applicability="ulcerative_colitis", topic_id="T",
                              mapped_question_ids=[], allocate_claim_id=lambda: "CLM-1", remaining_global=5) == []


def test_study_and_guideline_stay_distinct_types_through_to_the_source_records():
    g = make_record(2, "acg", evidenceType="clinical_guideline", society="ACG", abstractText="", doi="10.1/g",
                    title="Ulcerative colitis in adults guideline")
    st, _ = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")]),
                      FakeProvider("acg", [g], evidence_type=EvidenceType.CLINICAL_GUIDELINE)])
    types = {a["sourceRecord"]["evidenceType"] for a in st.accepted}
    assert types == {"published_study", "clinical_guideline"}
    guideline = next(a for a in st.accepted if a["sourceRecord"]["evidenceType"] == "clinical_guideline")
    assert guideline["claims"] == [] and guideline["sourceRecord"]["requiresFullTextVerification"] is True
    assert guideline["sourceRecord"]["fullTextStatus"] == "metadata_only_no_abstract"


def test_every_extracted_claim_is_flagged_for_full_text_verification():
    st, _ = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")])])
    claims = [c for a in st.accepted for c in a["claims"]]
    assert claims and all(c["requiresFullTextVerification"] and c["verificationBasis"] == "abstract_only" for c in claims)
    assert all(c["reviewStatus"] == "pending_clinical_review" and not c["humanReviewStatus"] for c in claims)


# ------------------------------------------------------------------ zero results are explained
def test_zero_window_with_healthy_canary_is_explained_not_failed():
    st, _ = run_once([FakeProvider("clinicaltrials", [], canary=612)])
    f = st.funnel.providers["clinicaltrials"]
    assert f.status == "no_new_records" and "canary returned 612" in f.zero_reason
    assert not codes(st, "ERROR")


def test_zero_window_AND_zero_canary_is_an_invalid_query_error():
    st, _ = run_once([FakeProvider("europepmc", [], canary=0, expects_daily=True)])
    assert st.funnel.providers["europepmc"].status == "invalid_query"
    assert ("ERROR", "INVALID_QUERY", "europepmc") in codes(st)


def test_a_date_filter_that_is_ignored_is_caught_when_the_window_exceeds_the_wide_canary():
    st, _ = run_once([FakeProvider("pubmed", [], hits=64066, canary=300)])         # whole database "matched" the 1-day window
    # pubmed-named provider triggers the filter-ignored check
    f = st.funnel.providers["pubmed"]
    assert f.status == "invalid_query" and "date filter is being ignored" in f.error
    assert ("ERROR", "INVALID_QUERY", "pubmed") in codes(st) and f.results_returned == 0


def test_invalid_query_from_the_provider_is_an_error_alert_with_no_cutoff_advance():
    st, ps = run_once([FakeProvider("pubmed", error=InvalidQuery("pubmed: HTTP 400"))])
    assert ("ERROR", "INVALID_QUERY", "pubmed") in codes(st)
    assert ps["providers"]["pubmed"]["lastSuccessfulCutoff"] is None


def test_repeated_unexpected_zero_escalates_warning_then_error_across_runs():
    ps = provider_state.empty_state()
    levels = []
    for i in range(3):
        st, ps = run_once([FakeProvider("europepmc", [], canary=900, expects_daily=True)], pstate=ps,
                          today=TODAY + dt.timedelta(days=i))
        levels.append([c for c in codes(st) if c[2] == "europepmc"])
    assert not any(l[0] in ("WARNING", "ERROR") for l in levels[0])
    assert ("WARNING", "UNEXPECTED_ZERO", "europepmc") in levels[1]
    assert ("ERROR", "REPEATED_UNEXPECTED_ZERO", "europepmc") in levels[2]


def test_a_result_resets_the_zero_counter():
    ps = provider_state.empty_state()
    for i in range(2):
        _, ps = run_once([FakeProvider("europepmc", [], canary=900, expects_daily=True)], pstate=ps, today=TODAY + dt.timedelta(days=i))
    assert ps["providers"]["europepmc"]["consecutiveUnexpectedZero"] == 2
    _, ps = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")], expects_daily=True)], pstate=ps,
                     today=TODAY + dt.timedelta(days=2))
    assert ps["providers"]["europepmc"]["consecutiveUnexpectedZero"] == 0


def test_access_limited_provider_is_a_warning_not_an_error_and_others_continue():
    st, _ = run_once([FakeProvider("nice", error=AccessLimited("www.nice.org.uk: robots.txt disallows")),
                      FakeProvider("europepmc", [make_record(1, "europepmc")])])
    assert st.funnel.providers["nice"].status == "access_limited"
    assert ("WARNING", "ACCESS_LIMITED", "nice") in codes(st) and not codes(st, "ERROR")


# ------------------------------------------------------------------ limits and deadline
def test_hard_limits_are_enforced_and_unscreened_records_keep_the_window_open():
    recs = [make_record(i, "europepmc") for i in range(config.MAX_SCREENED + 30)]
    st, ps = run_once([FakeProvider("europepmc", recs)])
    assert st.screened <= config.MAX_SCREENED
    assert len(st.accepted) <= config.MAX_ACCEPTED and st.claims_made <= config.MAX_CLAIMS
    f = st.funnel.providers["europepmc"]
    assert f.not_screened_limit > 0 and f.reconcile() == []
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] is None        # NOT advanced: nothing is skipped


def test_expired_soft_deadline_skips_every_provider_with_an_alert_and_keeps_windows():
    provs = [FakeProvider("europepmc", [make_record(1, "europepmc")]), FakeProvider("pubmed", [make_record(2, "pubmed")])]
    st, ps = run_once(provs, soft=0.0)
    assert all(f.status == "skipped_deadline" for f in st.funnel.providers.values())
    assert all(p.searched == 0 for p in provs)
    assert {c[1] for c in codes(st)} == {"SKIPPED_DEADLINE"}
    assert all(p["lastSuccessfulCutoff"] is None for p in ps["providers"].values())


def test_screening_is_round_robin_so_one_provider_cannot_starve_another(monkeypatch):
    monkeypatch.setattr(config, "MAX_SCREENED", 6)
    a = [make_record(i, "europepmc") for i in range(20)]
    b = [make_record(100 + i, "pubmed") for i in range(20)]
    st, _ = run_once([FakeProvider("europepmc", a), FakeProvider("pubmed", b)])
    assert st.funnel.providers["europepmc"].records_screened == 3 and st.funnel.providers["pubmed"].records_screened == 3


# ------------------------------------------------------------------ cutoffs, no backfill, no silent skips
def test_first_run_searches_only_today_and_advances_the_cutoff_when_complete():
    p = FakeProvider("europepmc", [make_record(1, "europepmc")])
    st, ps = run_once([p])
    assert p.windows[0] == Window(dt.date(2026, 11, 10), dt.date(2026, 11, 10))
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] == "2026-11-10"
    assert st.funnel.providers["europepmc"].advanced_cutoff


def test_failed_provider_keeps_its_cutoff_so_the_next_run_catches_up_from_it():
    ps = provider_state.empty_state()
    _, ps = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")])], pstate=ps)         # ok on day 1
    _, ps = run_once([FakeProvider("europepmc", error=ProviderUnavailable("down"))], pstate=ps,
                     today=TODAY + dt.timedelta(days=1))                                             # fails day 2
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] == "2026-11-10"
    p = FakeProvider("europepmc", [make_record(5, "europepmc")])
    st, ps = run_once([p], pstate=ps, today=TODAY + dt.timedelta(days=2))                            # day 3
    assert p.windows[0].start == dt.date(2026, 11, 10) and p.windows[0].end == dt.date(2026, 11, 12)  # days 11 AND 12 covered
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] == "2026-11-12"


def test_missed_run_dates_are_reported_loudly():
    ps = provider_state.empty_state()
    _, ps = run_once([FakeProvider("europepmc", [])], pstate=ps)
    st, _ = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")])], pstate=ps, today=TODAY + dt.timedelta(days=4))
    (alert,) = [a for a in st.alerts if a.code == "MISSED_RUNS"]
    assert "2026-11-11, 2026-11-12, 2026-11-13" in alert.message and st.missed_dates == ["2026-11-11", "2026-11-12", "2026-11-13"]


def test_truncated_window_without_any_complete_day_does_not_advance_the_cutoff_and_alerts():
    st, ps = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")], hits=500, truncated=True)])
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] is None
    assert ("WARNING", "WINDOW_NOT_COMPLETE", "europepmc") in codes(st)
    assert st.funnel.providers["europepmc"].status == "partial"


def test_a_busy_day_cannot_deadlock_catch_up_the_cutoff_advances_over_the_complete_days():
    ps = provider_state.empty_state()
    _, ps = run_once([FakeProvider("europepmc", [make_record(1, "europepmc")])], pstate=ps)       # cutoff 11-10
    # 4 days later: days 10,11,12 complete, day 13 too busy (truncated) -> cutoff moves to 11-12, not stuck at 11-10
    p = FakeProvider("europepmc", [make_record(2, "europepmc")], hits=900, truncated=True,
                     covered=dt.date(2026, 11, 12))
    st, ps = run_once([p], pstate=ps, today=dt.date(2026, 11, 14))
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] == "2026-11-12"
    assert ("WARNING", "WINDOW_NOT_COMPLETE", "europepmc") in codes(st)


def test_repeated_incomplete_windows_escalate_to_an_error():
    ps = provider_state.empty_state()
    levels = []
    for i in range(3):
        st, ps = run_once([FakeProvider("europepmc", [make_record(i, "europepmc")], hits=900, truncated=True)],
                          pstate=ps, today=TODAY + dt.timedelta(days=i))
        levels.append(("ERROR", "REPEATED_INCOMPLETE_WINDOW", "europepmc") in codes(st))
    assert levels == [False, False, True]


def test_one_provider_raising_any_exception_does_not_take_down_the_run():
    class Boom(FakeProvider):
        def search_window(self, http, window, *, max_pages):
            raise RuntimeError("html error page parsed as json")
    st, ps = run_once([Boom("pubmed"), FakeProvider("europepmc", [make_record(1, "europepmc")])])
    assert st.funnel.providers["pubmed"].status == "failed" and st.funnel.providers["europepmc"].accepted == 1
    assert ("ERROR", "PROVIDER_FAILURE", "pubmed") in codes(st)


def test_zero_unexplained_does_not_advance_the_cutoff():
    class NoCanary(FakeProvider):
        def canary_count(self, http, today, window=None):
            raise ProviderUnavailable("canary down")
    st, ps = run_once([NoCanary("europepmc", [], expects_daily=True)])
    assert st.funnel.providers["europepmc"].status == "zero_unexplained"
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] is None


def test_guideline_body_with_zero_window_and_zero_canary_is_a_warning_not_an_error():
    st, ps = run_once([FakeProvider("aga", [], canary=0, canary_error=False,
                                    evidence_type=EvidenceType.CLINICAL_GUIDELINE)])
    f = st.funnel.providers["aga"]
    assert f.status == "no_new_records" and not codes(st, "ERROR")
    assert ("WARNING", "ZERO_CANARY_UNCONFIRMED", "aga") in codes(st)
    assert ps["providers"]["aga"]["lastSuccessfulCutoff"] == "2026-11-10"


def test_listing_baseline_is_not_committed_when_the_window_was_not_completed():
    p = FakeProvider("acg", [], hits=3, truncated=True)
    p.listing_seen = {"https://example.org/g1"}
    _, ps = run_once([p])
    assert ps["providers"]["acg"]["knownListingUrls"] == []


def test_title_only_rejection_is_not_remembered_so_a_later_abstract_gets_a_fresh_look():
    title_only = make_record(9, "europepmc", title="Colonic study of 9", abstractText="")
    _, ps = run_once([FakeProvider("europepmc", [title_only])])
    assert ps["providers"]["europepmc"]["rejectedKeys"] == []


def test_nothing_is_ever_searched_before_the_discovery_start_date():
    p = FakeProvider("europepmc", [make_record(1, "europepmc")])
    st, ps = run_once([p], today=dt.date(2026, 11, 9))
    assert p.searched == 0 and st.funnel.providers["europepmc"].status == "no_new_records"


def test_listing_baseline_is_stored_for_site_channel_providers():
    p = FakeProvider("acg", [])
    p.listing_seen = {"https://example.org/g1", "https://example.org/g2"}
    _, ps = run_once([p])
    assert set(ps["providers"]["acg"]["knownListingUrls"]) == p.listing_seen


def test_a_window_bigger_than_the_screening_budget_still_finishes_over_several_runs(monkeypatch):
    """N1 regression: prior-run duplicates must not re-consume the budget, or the same first N records starve the rest."""
    monkeypatch.setattr(config, "MAX_SCREENED", 50)
    monkeypatch.setattr(config, "MAX_ACCEPTED", 10)
    recs = [make_record(i, "europepmc") for i in range(120)]
    ps, idx, accepted = provider_state.empty_state(), ProcessedIndex(), 0
    for run in range(14):
        st, ps = run_once([FakeProvider("europepmc", recs)], pstate=ps, index=idx, today=TODAY + dt.timedelta(days=run))
        accepted += len(st.accepted)
        if ps["providers"]["europepmc"]["lastSuccessfulCutoff"]:
            break
    assert accepted == 120                                                     # every record accepted exactly once
    assert ps["providers"]["europepmc"]["lastSuccessfulCutoff"] is not None   # and the window finally completed
    assert run < 13


def test_the_day_walk_stops_at_the_soft_deadline_and_keeps_the_days_already_done():
    from uc_evidence_discovery.providers.base import Provider
    class Days(Provider):
        name = "x"; label = "X"
        def search_range(self, http, window, *, max_pages):
            return SearchOutcome(records=[make_record(1, "x")], hit_count=1, searches=1, queries=["q"])
    p = Days()
    calls = {"n": 0}
    def stop():
        calls["n"] += 1
        return calls["n"] > 1
    p.should_stop = stop
    out = p.search_window(object(), Window(dt.date(2026, 11, 10), dt.date(2026, 11, 14)), max_pages=1)
    assert out.truncated and out.covered_through == dt.date(2026, 11, 11) or out.covered_through == dt.date(2026, 11, 10)


def test_two_runs_on_the_same_date_count_as_one_zero_day():
    ps = provider_state.empty_state()
    for _ in range(3):
        st, ps = run_once([FakeProvider("europepmc", [], canary=900, expects_daily=True)], pstate=ps)
    assert ps["providers"]["europepmc"]["consecutiveUnexpectedZero"] == 1
    assert not [c for c in codes(st) if c[0] in ("WARNING", "ERROR") and c[1].endswith("ZERO")]
