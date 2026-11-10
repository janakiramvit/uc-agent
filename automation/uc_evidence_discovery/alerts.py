"""Explicit errors and alerts. Alerts are data first (stored, reported, annotated in GitHub Actions)."""

from __future__ import annotations

import re
from dataclasses import dataclass

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"


_CTRL = re.compile(r"[\x00-\x1f\x7f]+")
MAX_MESSAGE = 300


def sanitize(text: str) -> str:
    """Alert text can embed remote error strings: strip control characters/newlines (no second ``::`` workflow
    command, no markdown injection into the report) and bound the length."""
    return _CTRL.sub(" ", str(text)).replace("::", ": :").strip()[:MAX_MESSAGE]


@dataclass(frozen=True)
class Alert:
    level: str          # ERROR | WARNING | INFO
    code: str           # PROVIDER_FAILURE | INVALID_QUERY | UNEXPECTED_ZERO | REPEATED_UNEXPECTED_ZERO | ACCESS_LIMITED ...
    provider: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", sanitize(self.message))

    def to_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "provider": self.provider, "message": self.message}

    def github_annotation(self) -> str:
        kind = {"ERROR": "error", "WARNING": "warning"}.get(self.level, "notice")
        # message is composed by this package from provider names/counts only - never response bodies
        msg = self.message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        return f"::{kind} title=UC discovery {self.code} ({self.provider})::{msg}"


def has_errors(alerts: list[Alert]) -> bool:
    return any(a.level == ERROR for a in alerts)
