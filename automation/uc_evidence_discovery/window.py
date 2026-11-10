"""Search-window computation: start from the last successful cutoff, floor at the configured start
date, never skip a date silently, never backfill before the floor."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from . import config
from .providers.base import Window


@dataclass
class WindowPlan:
    window: Window
    first_run: bool
    last_cutoff: str | None
    missed_dates: list[str] = field(default_factory=list)   # dates with no successful run
    catch_up: bool = False
    sliced: bool = False                                     # gap longer than MAX_CATCHUP_DAYS
    floored: bool = False                                    # window start raised to EARLIEST_DISCOVERY_DATE

    def describe(self) -> str:
        s, e = self.window.iso()
        bits = [f"{s} .. {e}"]
        if self.first_run:
            bits.append("first run (no backfill before the discovery start date)")
        if self.catch_up:
            bits.append(f"catching up {len(self.missed_dates)} missed day(s)")
        if self.sliced:
            bits.append("gap longer than the catch-up slice; continues next run")
        return "; ".join(bits)


def _d(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s[:10])


def plan_window(last_cutoff: str | None, today: _dt.date, *,
                floor: str = config.EARLIEST_DISCOVERY_DATE,
                overlap_days: int = config.WINDOW_OVERLAP_DAYS,
                max_days: int = config.MAX_CATCHUP_DAYS) -> WindowPlan:
    floor_d = _d(floor)
    if today < floor_d:
        # discovery has not started yet: an empty, explicit window - nothing is searched
        return WindowPlan(Window(floor_d, floor_d - _dt.timedelta(days=1)), first_run=True, last_cutoff=None)

    if not last_cutoff:
        return WindowPlan(Window(floor_d, today), first_run=True, last_cutoff=None)

    last = _d(last_cutoff)
    start = max(floor_d, last - _dt.timedelta(days=overlap_days))
    # every calendar day after the last covered day, up to yesterday, was not covered by any run
    missed = [(last + _dt.timedelta(days=i)).isoformat() for i in range(1, (today - last).days)]
    end = today
    sliced = False
    if (end - start).days + 1 > max_days:
        end = start + _dt.timedelta(days=max_days - 1)
        sliced = True
    return WindowPlan(Window(start, end), first_run=False, last_cutoff=last_cutoff, missed_dates=missed,
                      catch_up=bool(missed), sliced=sliced, floored=start == floor_d and last < floor_d)
