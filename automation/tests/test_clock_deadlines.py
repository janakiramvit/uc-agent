from __future__ import annotations

import time

from uc_evidence_discovery import config
from uc_evidence_discovery.clock import Deadline


def test_defaults_match_configured_budget():
    d = Deadline()
    assert d.soft_seconds == 450 == config.SOFT_DEADLINE_SECONDS
    assert d.finalize_seconds == 540 == config.FINALIZE_DEADLINE_SECONDS
    assert config.HARD_TIMEOUT_SECONDS - config.FINALIZE_DEADLINE_SECONDS == 60
    assert config.UPLOAD_CLEANUP_RESERVE_SECONDS == 60


def test_soft_expires_before_finalize():
    d = Deadline(soft_seconds=0.05, finalize_seconds=0.2)
    assert not d.soft_expired()
    time.sleep(0.08)
    assert d.soft_expired()
    assert not d.finalize_expired()
    time.sleep(0.2)
    assert d.finalize_expired()


def test_may_start_new_work_is_false_once_soft_expired():
    d = Deadline(soft_seconds=0.02, finalize_seconds=1.0)
    assert d.may_start_new_work()
    time.sleep(0.05)
    assert not d.may_start_new_work()


def test_remaining_never_negative():
    d = Deadline(soft_seconds=0.01, finalize_seconds=0.01)
    time.sleep(0.05)
    assert d.remaining_soft() == 0.0
    assert d.remaining_finalize() == 0.0
