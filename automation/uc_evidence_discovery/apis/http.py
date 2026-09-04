"""Guarded HTTP: allowlist, timeouts, bounded retries + exponential backoff, per-host rate
limiting, response-size ceiling. Also the single choke-point that makes ``--no-network``
provable (no session is even constructed)."""

from __future__ import annotations

import random
import time
from typing import Optional
from urllib.parse import urlparse

import requests

from .. import config


class NetworkDisabled(RuntimeError):
    """Raised if a request is attempted while running with ``--no-network``."""


class DisallowedHost(RuntimeError):
    pass


class ResponseTooLarge(RuntimeError):
    pass


def host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if any(bad in host for bad in config.DENY_HOST_SUBSTRINGS):
        return False
    return host in config.API_HOST_ALLOWLIST


class Http:
    def __init__(
        self,
        *,
        enabled: bool = True,
        session: Optional["requests.Session"] = None,
        timeout: float = 20.0,
        retries: int = config.MAX_RETRIES_PER_SERVICE,
        backoff_base: float = config.BACKOFF_BASE_SECONDS,
        min_interval: float = config.PER_HOST_MIN_INTERVAL_SECONDS,
        max_bytes: int = config.MAX_RESPONSE_BYTES,
        sleep=time.sleep,
    ) -> None:
        self.enabled = enabled
        self.timeout = timeout
        self.retries = retries
        self.backoff_base = backoff_base
        self.min_interval = min_interval
        self.max_bytes = max_bytes
        self._sleep = sleep
        self._last_hit: dict[str, float] = {}
        self._session = session
        if enabled and self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": config.USER_AGENT})
        self.request_log: list[str] = []   # host+path only; never query values

    # ----------------------------------------------------------------------------------
    def _rate_limit(self, host: str) -> None:
        last = self._last_hit.get(host)
        if last is not None:
            wait = self.min_interval - (time.monotonic() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_hit[host] = time.monotonic()

    def get(self, url: str, params: Optional[dict] = None) -> "requests.Response":
        if not self.enabled:
            raise NetworkDisabled(f"--no-network: refusing GET {urlparse(url).hostname}")
        if not host_allowed(url):
            raise DisallowedHost(url)
        host = (urlparse(url).hostname or "").lower()
        self.request_log.append(f"{host}{urlparse(url).path}")

        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            self._rate_limit(host)
            try:
                resp = self._session.get(
                    url, params=params, timeout=self.timeout, stream=True, allow_redirects=False
                )
                if resp.status_code in (429, 500, 502, 503, 504):
                    last_exc = requests.HTTPError(f"{resp.status_code} for {host}")
                    self._backoff(attempt)
                    continue
                if 300 <= resp.status_code < 400:
                    loc = resp.headers.get("Location", "")
                    if not host_allowed(loc):
                        raise DisallowedHost(f"redirect to disallowed host: {loc}")
                resp.raise_for_status()
                self._enforce_size(resp)
                return resp
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
                last_exc = exc
                self._backoff(attempt)
        raise last_exc if last_exc else RuntimeError("unreachable")

    def get_json(self, url: str, params: Optional[dict] = None) -> dict:
        return self.get(url, params).json()

    def get_text(self, url: str, params: Optional[dict] = None) -> str:
        resp = self.get(url, params)
        return resp.text

    # ----------------------------------------------------------------------------------
    def _backoff(self, attempt: int) -> None:
        delay = self.backoff_base * (2 ** attempt) + random.uniform(0, 0.4)
        self._sleep(min(delay, 15.0))

    def _enforce_size(self, resp: "requests.Response") -> None:
        declared = resp.headers.get("Content-Length")
        if declared and int(declared) > self.max_bytes:
            raise ResponseTooLarge(f"{declared} bytes > {self.max_bytes}")
        body = bytearray()
        for chunk in resp.iter_content(8192):
            body.extend(chunk)
            if len(body) > self.max_bytes:
                raise ResponseTooLarge(f"stream exceeded {self.max_bytes} bytes")
        resp._content = bytes(body)      # noqa: SLF001 - make .json()/.text work post-stream
        resp._content_consumed = True    # noqa: SLF001
