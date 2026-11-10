"""robots.txt policy (RFC 9309 semantics). Automated access to a site's content is attempted ONLY when its robots.txt permits it.

    200            parse; our user-agent group (else ``*``); longest matching rule wins, Allow beats Disallow on a tie;
                   ``*`` and ``$`` wildcards honoured; Crawl-delay honoured (and a delay above our budget = not permitted)
    404 / 410      no robots file -> no restriction
    401 / 403      the site refuses automated clients -> NOT permitted (ECCO answers 403)
    3xx            redirects are never followed -> unusable -> NOT permitted
    other 4xx      NOT permitted;   5xx / network -> cannot tell -> ProviderUnavailable (never assume permission)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .. import config
from ..apis.http import Http, HttpClientError, HttpRedirect
from .base import AccessLimited, ProviderUnavailable

UA_TOKEN = "uc-agent-evidence-discovery"


@dataclass
class _Rules:
    rules: list[tuple[bool, str]] = field(default_factory=list)      # (allow?, pattern)
    crawl_delay: float | None = None


def _pattern_regex(pattern: str) -> re.Pattern:
    anchored = pattern.endswith("$")
    body = re.escape(pattern[:-1] if anchored else pattern).replace(r"\*", ".*")
    return re.compile("^" + body + ("$" if anchored else ""))


def parse_robots(text: str) -> _Rules:
    groups: list[tuple[list[str], _Rules]] = []
    agents: list[str] = []
    cur: _Rules | None = None
    last_was_agent = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            if not last_was_agent:
                agents, cur = [], _Rules()
                groups.append((agents, cur))
            agents.append(val.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if cur is None:
            continue
        if key in ("allow", "disallow"):
            if val or key == "allow":                               # an empty Disallow allows everything: no rule
                cur.rules.append((key == "allow", val))
        elif key == "crawl-delay":
            try:
                cur.crawl_delay = float(val)
            except ValueError:
                pass
    token = UA_TOKEN.lower()
    specific = [r for ags, r in groups if any(a == token for a in ags)]
    star = [r for ags, r in groups if "*" in ags]
    chosen = specific or star
    merged = _Rules()
    for r in chosen:
        merged.rules.extend(r.rules)
        if r.crawl_delay is not None:
            merged.crawl_delay = r.crawl_delay
    return merged


def allowed(rules: _Rules, path_and_query: str) -> bool:
    best_len, best_allow = -1, True
    for allow, pattern in rules.rules:
        if not pattern:
            continue
        if _pattern_regex(pattern).match(path_and_query):
            n = len(pattern)
            if n > best_len or (n == best_len and allow):
                best_len, best_allow = n, allow
    return best_allow


class RobotsPolicy:
    def __init__(self, http: Http) -> None:
        self.http = http
        self._cache: dict[str, _Rules | str] = {}        # host -> rules | "allow" | "deny:<why>"

    def _load(self, host: str) -> _Rules | str:
        if host in self._cache:
            return self._cache[host]
        try:
            text = self.http.get_text(f"https://{host}/robots.txt")
        except HttpRedirect as exc:
            self._cache[host] = f"deny:robots.txt redirected (HTTP {exc.status}); redirects are not followed"
            return self._cache[host]
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
        rules = parse_robots(text)
        if rules.crawl_delay is not None:
            if rules.crawl_delay > config.MAX_ROBOTS_CRAWL_DELAY:
                self._cache[host] = (f"deny:robots.txt Crawl-delay {rules.crawl_delay:g}s exceeds our "
                                     f"{config.MAX_ROBOTS_CRAWL_DELAY:g}s budget")
                return self._cache[host]
            self.http.set_host_interval(host, rules.crawl_delay)
        self._cache[host] = rules
        return rules

    def require(self, url: str) -> None:
        """Raise AccessLimited unless automated fetching of ``url`` is permitted."""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        policy = self._load(host)
        if policy == "allow":
            return
        if isinstance(policy, str):
            raise AccessLimited(f"{host}: {policy.split(':', 1)[1]}")
        target = (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")
        if not allowed(policy, target):
            raise AccessLimited(f"{host}: robots.txt disallows automated access to {parsed.path or '/'}")
