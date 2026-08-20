import pytest

from agent_core.rate_limit import (
    QueryTooLong,
    RateLimitExceeded,
    check_query_length,
    check_rate_limit,
    reset_rate_limits,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_rate_limits()
    yield
    reset_rate_limits()


def test_requests_within_limit_pass():
    for _ in range(5):
        check_rate_limit("client-a", max_requests=5, window_seconds=60, now=1000.0)


def test_exceeding_limit_raises():
    for i in range(5):
        check_rate_limit("client-b", max_requests=5, window_seconds=60, now=1000.0 + i)
    with pytest.raises(RateLimitExceeded):
        check_rate_limit("client-b", max_requests=5, window_seconds=60, now=1000.0)


def test_limit_resets_after_window_elapses():
    for i in range(5):
        check_rate_limit("client-c", max_requests=5, window_seconds=60, now=1000.0 + i)
    # 61 seconds later, the earliest requests have aged out of the window.
    check_rate_limit("client-c", max_requests=5, window_seconds=60, now=1065.0)


def test_clients_are_isolated():
    for i in range(5):
        check_rate_limit("client-d", max_requests=5, window_seconds=60, now=1000.0 + i)
    # A different client key must not be affected by client-d's usage.
    check_rate_limit("client-e", max_requests=5, window_seconds=60, now=1000.0)


def test_query_length_cap():
    check_query_length("short question")
    with pytest.raises(QueryTooLong):
        check_query_length("x" * 2001)
