from __future__ import annotations

import datetime as dt

from uc_evidence_discovery import config
from uc_evidence_discovery.window import plan_window

D = dt.date


def test_first_run_starts_on_the_discovery_start_date_with_no_backfill():
    p = plan_window(None, D(2026, 11, 10))
    assert p.first_run and p.window.start == D(2026, 11, 10) and p.window.end == D(2026, 11, 10)


def test_nothing_earlier_than_the_start_date_is_ever_searched_even_if_state_is_older():
    p = plan_window("2026-01-01", D(2026, 11, 12))
    assert p.window.start >= D(2026, 11, 10)


def test_before_the_start_date_nothing_is_searched():
    p = plan_window(None, D(2026, 11, 9))
    assert p.window.days <= 0


def test_normal_next_day_overlaps_one_day_and_reports_no_missed_run():
    p = plan_window("2026-11-10", D(2026, 11, 11))
    assert p.window.start == D(2026, 11, 10) and p.window.end == D(2026, 11, 11)
    assert p.missed_dates == [] and not p.catch_up


def test_missed_days_are_listed_and_covered_from_the_last_successful_cutoff():
    p = plan_window("2026-11-10", D(2026, 11, 14))
    assert p.missed_dates == ["2026-11-11", "2026-11-12", "2026-11-13"]
    assert p.catch_up and p.window.start == D(2026, 11, 10) and p.window.end == D(2026, 11, 14)
    assert "catching up 3 missed day(s)" in p.describe()


def test_a_long_gap_is_sliced_and_continues_next_run_without_dropping_days():
    p = plan_window("2026-11-10", D(2027, 2, 1))
    assert p.sliced and p.window.days == config.MAX_CATCHUP_DAYS
    # the next run starts from the end of this slice
    q = plan_window(p.window.end.isoformat(), D(2027, 2, 2))
    assert q.window.start <= p.window.end
