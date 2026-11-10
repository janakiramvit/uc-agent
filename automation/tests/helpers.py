"""Test doubles: a fake guarded-HTTP client that serves recorded fixtures (no network)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from uc_evidence_discovery.apis.http import HttpClientError

FIX = Path(__file__).resolve().parent / "fixtures"


def fixture(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def fixture_json(name: str) -> dict:
    return json.loads(fixture(name))


Route = tuple[Callable[[str, dict], bool], Callable[[str, dict], object]]


class FakeHttp:
    """Routes: (matcher(url, params) -> bool, responder(url, params) -> json-able | str | Exception)."""

    def __init__(self, routes: Optional[list[Route]] = None, default_status: int = 404) -> None:
        self.routes: list[Route] = list(routes or [])
        self.calls: list[tuple[str, dict]] = []
        self.host_intervals: dict[str, float] = {}
        self.default_status = default_status

    def add(self, matcher, responder) -> "FakeHttp":
        self.routes.append((matcher, responder))
        return self

    def set_host_interval(self, host: str, seconds: float) -> None:
        self.host_intervals[host] = seconds

    def _resolve(self, url: str, params: Optional[dict]):
        params = params or {}
        self.calls.append((url, dict(params)))
        for matcher, responder in self.routes:
            if matcher(url, params):
                out = responder(url, params)
                if isinstance(out, Exception):
                    raise out
                return out
        host = url.split("/")[2]
        raise HttpClientError(self.default_status, host)

    def get_json(self, url: str, params: Optional[dict] = None) -> dict:
        out = self._resolve(url, params)
        return json.loads(out) if isinstance(out, str) else out

    def get_text(self, url: str, params: Optional[dict] = None) -> str:
        out = self._resolve(url, params)
        return out if isinstance(out, str) else json.dumps(out)

    def get(self, url: str, params: Optional[dict] = None):                 # pragma: no cover - not used by providers
        raise NotImplementedError


def url_has(*needles: str):
    return lambda url, params: all(n in url for n in needles)


def route_robots(host: str, text: str | None = None, status: int | None = None) -> Route:
    def resp(url, params):
        if status is not None:
            return HttpClientError(status, host)
        return text or ""
    return (lambda url, params: url == f"https://{host}/robots.txt", resp)
