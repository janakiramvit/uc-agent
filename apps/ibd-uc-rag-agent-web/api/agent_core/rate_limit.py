"""Best-effort request rate limiting and cost control for the /api/chat
Vercel Python function.

Honest limitation: Vercel serverless Python functions are not guaranteed
to reuse the same process/memory between invocations (cold starts spin up
fresh instances, and traffic can be spread across multiple warm
instances). This in-memory token bucket is therefore a best-effort,
single-instance limiter -- it will meaningfully throttle bursts on a warm
instance but is NOT a substitute for a shared store (e.g. Upstash Redis)
in a real multi-instance production deployment. That tradeoff is called
out explicitly in the deployment report rather than presented as a
guarantee it cannot make.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

DEFAULT_MAX_REQUESTS_PER_WINDOW = 10
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_QUERY_CHARS = 2000  # cost control: reject absurdly long inputs before they hit the LLM


@dataclass
class _Bucket:
    timestamps: list[float] = field(default_factory=list)


_buckets: dict[str, _Bucket] = {}


class RateLimitExceeded(RuntimeError):
    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded; retry after {retry_after_seconds:.0f}s")


class QueryTooLong(RuntimeError):
    pass


def check_rate_limit(
    client_key: str,
    max_requests: int = DEFAULT_MAX_REQUESTS_PER_WINDOW,
    window_seconds: float = DEFAULT_WINDOW_SECONDS,
    now: float | None = None,
) -> None:
    """Raises ``RateLimitExceeded`` if ``client_key`` has made too many
    requests within the trailing window. Otherwise records this request."""
    now = time.time() if now is None else now
    bucket = _buckets.setdefault(client_key, _Bucket())
    cutoff = now - window_seconds
    bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]

    if len(bucket.timestamps) >= max_requests:
        oldest = min(bucket.timestamps)
        retry_after = window_seconds - (now - oldest)
        raise RateLimitExceeded(max(retry_after, 1.0))

    bucket.timestamps.append(now)


def check_query_length(query: str, max_chars: int = DEFAULT_MAX_QUERY_CHARS) -> None:
    if len(query or "") > max_chars:
        raise QueryTooLong(f"Query exceeds the {max_chars}-character cap for this prototype.")


def reset_rate_limits() -> None:
    """Test-only helper to clear all buckets between test cases."""
    _buckets.clear()
