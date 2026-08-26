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

# Per-request token budget across ALL model-powered nodes combined (planner,
# classifier, reformulator, evidence analyst, conflict resolver, synthesizer,
# citation reviewer, safety critic, QA evaluator). Enforced in code BEFORE
# each model call -- the model itself has no way to raise or bypass this
# ceiling, so a single pathological/compound query cannot fan out into an
# unbounded number of expensive calls.
DEFAULT_MAX_TOKENS_PER_REQUEST = 8000
_CHARS_PER_TOKEN_ESTIMATE = 4  # rough, provider-agnostic heuristic; deliberately conservative (over-, not under-, counts)


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


class TokenBudgetExceeded(RuntimeError):
    pass


def estimate_tokens(*texts: str) -> int:
    total_chars = sum(len(t or "") for t in texts)
    return max(1, total_chars // _CHARS_PER_TOKEN_ESTIMATE)


def check_and_consume_token_budget(
    state: dict,
    estimated_tokens: int,
    max_tokens: int = DEFAULT_MAX_TOKENS_PER_REQUEST,
) -> bool:
    """Deterministic, non-bypassable token budget for one request's
    lifetime. Call this BEFORE every model-powered node's invocation;
    returns False (and does NOT consume budget) if the call would exceed
    the ceiling, so the node can degrade to its safe fallback instead of
    ever reaching the model. State-scoped (per-request), not global --
    resets naturally with each new request's initial state dict."""
    used = state.get("_token_budget_used", 0)
    if used + estimated_tokens > max_tokens:
        return False
    state["_token_budget_used"] = used + estimated_tokens
    return True


def remaining_token_budget(state: dict, max_tokens: int = DEFAULT_MAX_TOKENS_PER_REQUEST) -> int:
    return max_tokens - state.get("_token_budget_used", 0)


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
