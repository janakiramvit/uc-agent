"""Explicit errors and alerts. Alerts are data first (stored, reported, annotated in GitHub Actions)."""

from __future__ import annotations

from dataclasses import dataclass

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"


@dataclass(frozen=True)
class Alert:
    level: str          # ERROR | WARNING | INFO
    code: str           # PROVIDER_FAILURE | INVALID_QUERY | UNEXPECTED_ZERO | REPEATED_UNEXPECTED_ZERO | ACCESS_LIMITED ...
    provider: str
    message: str

    def to_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "provider": self.provider, "message": self.message}

    def github_annotation(self) -> str:
        kind = {"ERROR": "error", "WARNING": "warning"}.get(self.level, "notice")
        # message is composed by this package from provider names/counts only - never response bodies
        return f"::{kind} title=UC discovery {self.code} ({self.provider})::{self.message}"


def has_errors(alerts: list[Alert]) -> bool:
    return any(a.level == ERROR for a in alerts)
