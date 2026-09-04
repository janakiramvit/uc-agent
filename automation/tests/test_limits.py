from __future__ import annotations

from uc_evidence_discovery import config, ids, journal as journal_mod, runner
from uc_evidence_discovery.clock import Deadline
from uc_evidence_discovery.dedup import ProcessedIndex


def _synthetic_record(i: int) -> dict:
    return {
        "title": f"Acute severe ulcerative colitis rescue therapy trial {i}",
        "doi": f"10.9999/synthetic-{i}",
        "pmid": str(100000 + i),
        "journal": "Gut",
        "pubYear": "2025",
        "publicationDate": "2025-01-01",
        "abstractText": (
            f"In this trial of acute severe ulcerative colitis (record {i}), Truelove Witts "
            "criteria were used for hospitalisation. Intravenous corticosteroids, ciclosporin "
            "rescue therapy, and colectomy rates were assessed. Truelove Witts thresholds guided "
            "escalation to rescue therapy in this ulcerative colitis cohort."
        ),
        "canonicalUrl": f"https://doi.org/10.9999/synthetic-{i}",
        "provider": "synthetic",
        "retrievedVia": "synthetic-test-fixture",
    }


def _run_with_n_queries_of_m_records(n_queries: int, m_records: int, *, monkeypatch, soft_seconds=999):
    cp = {"nextRecommendedOperation": {"topicId": "T-UCX-03"}, "pendingSearches": []}
    st = runner._ResearchState(cp)
    st.pending = [
        {"searchId": f"S-{q}", "service": "europepmc", "query": f"query {q}", "cursor": 0}
        for q in range(n_queries)
    ]
    counter = {"n": 0}

    def fake_run_query(_http, _search, _query):
        out = []
        for _ in range(m_records):
            out.append(_synthetic_record(counter["n"]))
            counter["n"] += 1
        return out

    monkeypatch.setattr(runner, "_run_query", fake_run_query)
    clock = Deadline(soft_seconds=soft_seconds, finalize_seconds=soft_seconds + 60)
    index = ProcessedIndex()
    allocator = ids.Allocator(set(), set())
    j = journal_mod.Journal.__new__(journal_mod.Journal)
    j.append = lambda *a, **k: None  # no-op journal for this unit test

    class _Args:
        no_network = False
        dry_run = False

    runner._do_research(_Args(), clock, cp, index, allocator, st, j)
    return st


def test_max_queries_enforced(monkeypatch):
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES + 5, 1, monkeypatch=monkeypatch)
    assert st.queries <= config.MAX_QUERIES


def test_max_screened_enforced(monkeypatch):
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES, config.MAX_SCREENED, monkeypatch=monkeypatch)
    assert st.screened <= config.MAX_SCREENED


def test_max_accepted_enforced(monkeypatch):
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES, config.MAX_SCREENED, monkeypatch=monkeypatch)
    assert len(st.accepted) <= config.MAX_ACCEPTED


def test_max_claims_enforced(monkeypatch):
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES, config.MAX_SCREENED, monkeypatch=monkeypatch)
    assert st.claims_made <= config.MAX_CLAIMS


def test_status_is_partial_when_a_limit_is_hit_and_records_next_operation(monkeypatch):
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES, config.MAX_SCREENED, monkeypatch=monkeypatch)
    assert st.status in ("partial", "completed")
    assert st.stop_reason


def test_soft_deadline_stops_research_before_any_hard_limit(monkeypatch):
    # an already-expired soft deadline must stop the loop before the first query
    st = _run_with_n_queries_of_m_records(config.MAX_QUERIES, 3, monkeypatch=monkeypatch, soft_seconds=0.0)
    assert st.queries == 0
    assert st.stop_reason == "limit_or_deadline_before_query"
