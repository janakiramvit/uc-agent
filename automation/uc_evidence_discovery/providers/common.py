"""Shared helpers: error mapping, query lint, evidence-type tagging."""

from __future__ import annotations

import re

import requests

from ..apis.http import DisallowedHost, HttpClientError, HttpRedirect, NetworkDisabled, PdfRefused, ResponseTooLarge
from .base import EvidenceType, InvalidQuery, ProviderUnavailable


def guarded(provider: str, fn, *args, **kwargs):
    """Run an API call, translating transport/API failures into the provider error taxonomy."""
    try:
        return fn(*args, **kwargs)
    except HttpClientError as exc:
        if exc.status == 400:
            raise InvalidQuery(f"{provider}: HTTP 400 (query rejected)") from None
        raise ProviderUnavailable(f"{provider}: HTTP {exc.status}") from None
    except HttpRedirect as exc:
        raise ProviderUnavailable(f"{provider}: unexpected redirect (HTTP {exc.status})") from None
    except ValueError as exc:                                  # API-side explicit rejection / bad JSON
        raise InvalidQuery(f"{provider}: {exc}") from None
    except NetworkDisabled:
        raise
    except (DisallowedHost, PdfRefused) as exc:
        raise ProviderUnavailable(f"{provider}: blocked by client policy ({type(exc).__name__})") from None
    except (requests.RequestException, ResponseTooLarge) as exc:
        raise ProviderUnavailable(f"{provider}: {type(exc).__name__}") from None
    except Exception as exc:                       # malformed payloads (XML/JSON/shape): provider-level failure, not a crash
        raise ProviderUnavailable(f"{provider}: unparseable response ({type(exc).__name__})") from None


_GUIDELINE_TYPES = ("practice guideline", "guideline", "consensus development conference", "consensus statement")
_GUIDELINE_TITLE = re.compile(r"\b(guideline|guidelines|consensus|clinical practice update|recommendations?)\b", re.I)


def classify_publication(record: dict) -> EvidenceType:
    """Published study vs clinical guideline, from the provider's own publication-type tags first."""
    types = [t.lower() for t in record.get("publicationTypes") or []]
    if any(any(g == t or g in t for g in _GUIDELINE_TYPES) for t in types):
        return EvidenceType.CLINICAL_GUIDELINE
    return EvidenceType.PUBLISHED_STUDY


def lint_query_balanced(query: str, provider: str) -> None:
    if query.count("(") != query.count(")"):
        raise InvalidQuery(f"{provider}: unbalanced parentheses in generated query")
    if query.count('"') % 2:
        raise InvalidQuery(f"{provider}: unbalanced quotes in generated query")
