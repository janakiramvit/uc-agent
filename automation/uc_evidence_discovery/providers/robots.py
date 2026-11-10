"""robots.txt policy. Automated access to a site's content is attempted ONLY when its robots.txt permits it.

Interpretation is deliberately conservative (RFC 9309 would let a crawler proceed on some 4xx):
    200            parse; honour Disallow and Crawl-delay for our user-agent token
    404 / 410      no robots file -> no restriction
    401 / 403      the site refuses automated clients -> treated as NOT permitted (ECCO answers 403)
    5xx / network  cannot tell -> ProviderUnavailable (retry next run), never assume permission
"""

from __future__ import annotations

from urllib import robotparser
from urllib.parse import urlparse

from .. import config
from ..apis.http import Http, HttpClientError
from .base import AccessLimited, ProviderUnavailable

UA_TOKEN = "uc-agent-evidence-discovery"


class RobotsPolicy:
    def __init__(self, http: Http) -> None:
        self.http = http
        self._cache: dict[str, robotparser.RobotFileParser | str] = {}   # host -> parser | "deny:<why>" | "allow"

    def _load(self, host: str) -> robotparser.RobotFileParser | str:
        if host in self._cache:
            return self._cache[host]
        url = f"https://{host}/robots.txt"
        try:
            text = self.http.get_text(url)
        except HttpClientError as exc:
            if exc.status in (404, 410):
                self._cache[host] = "allow"
            elif exc.status in (401, 403):
                self._cache[host] = f"deny:robots.txt returned HTTP {exc.status} (site refuses automated clients)"
            else:
                self._cache[host] = f"deny:robots.txt returned HTTP {exc.status}"
            return self._cache[host]
        except Exception as exc:                                    # network / 5xx after retries
            raise ProviderUnavailable(f"robots.txt for {host} unreachable ({type(exc).__name__})") from None
        rp = robotparser.RobotFileParser()
        rp.parse(text.splitlines())
        delay = rp.crawl_delay(UA_TOKEN)
        if delay:
            self.http.set_host_interval(host, float(delay))
        self._cache[host] = rp
        return rp

    def require(self, url: str) -> None:
        """Raise AccessLimited unless automated fetching of ``url`` is permitted."""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        policy = self._load(host)
        if policy == "allow":
            return
        if isinstance(policy, str):
            raise AccessLimited(f"{host}: {policy.split(':', 1)[1]}")
        if not policy.can_fetch(UA_TOKEN, url):
            raise AccessLimited(f"{host}: robots.txt disallows automated access to {parsed.path or '/'}")
