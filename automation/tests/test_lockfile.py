from __future__ import annotations

import datetime as _dt

import pytest

from uc_evidence_discovery import lockfile
from uc_evidence_discovery.errors import LockHeld


def _info(run_id="uc-exp-000000000001"):
    return lockfile.LockInfo.new(run_id=run_id, run_url="https://x/runs/1", commit="deadbeef")


def test_acquire_then_release(tmp_path):
    lock = tmp_path / "run.lock"
    info = _info()
    lockfile.acquire(lock, info)
    assert lock.exists()
    lockfile.release(lock, info.runId)
    assert lockfile.read(lock)["status"] == "released"


def test_fresh_lock_is_not_reclaimed(tmp_path):
    lock = tmp_path / "run.lock"
    lockfile.acquire(lock, _info("uc-exp-aaaaaaaaaaaa"))
    with pytest.raises(LockHeld):
        lockfile.acquire(lock, _info("uc-exp-bbbbbbbbbbbb"), is_run_active=lambda _r: False)


def test_stale_lock_reclaimed_only_when_run_confirmed_inactive(tmp_path):
    lock = tmp_path / "run.lock"
    lockfile.acquire(lock, _info("uc-exp-aaaaaaaaaaaa"))
    stale_now = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=lockfile.STALE_AFTER_SECONDS + 5)

    with pytest.raises(LockHeld):
        lockfile.acquire(lock, _info("uc-exp-bbbbbbbbbbbb"), is_run_active=lambda _r: None, now=stale_now)
    with pytest.raises(LockHeld):
        lockfile.acquire(lock, _info("uc-exp-bbbbbbbbbbbb"), is_run_active=lambda _r: True, now=stale_now)

    lockfile.acquire(lock, _info("uc-exp-cccccccccccc"), is_run_active=lambda _r: False, now=stale_now)
    assert lockfile.read(lock)["runId"] == "uc-exp-cccccccccccc"


def test_active_but_stale_by_age_alone_is_not_reclaimed_without_confirmation(tmp_path):
    lock = tmp_path / "run.lock"
    lockfile.acquire(lock, _info("uc-exp-aaaaaaaaaaaa"))
    stale_now = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=lockfile.STALE_AFTER_SECONDS + 5)
    with pytest.raises(LockHeld):
        lockfile.acquire(lock, _info("uc-exp-dddddddddddd"),
                         is_run_active=lambda _r: True, now=stale_now)


def test_release_is_a_noop_for_a_lock_we_do_not_own(tmp_path):
    lock = tmp_path / "run.lock"
    lockfile.acquire(lock, _info("uc-exp-aaaaaaaaaaaa"))
    lockfile.release(lock, "uc-exp-bbbbbbbbbbbb")  # not our lock
    assert lockfile.read(lock)["runId"] == "uc-exp-aaaaaaaaaaaa"
    assert lockfile.read(lock).get("status") != "released"


def test_release_after_error_still_marks_released(tmp_path):
    lock = tmp_path / "run.lock"
    info = _info()
    lockfile.acquire(lock, info)
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        lockfile.release(lock, info.runId)
    assert lockfile.read(lock)["status"] == "released"
