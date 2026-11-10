"""The configured providers, and the rotation order.

Every run attempts EVERY provider, independently. The starting provider rotates with the day of the year so that, if
the 450 s soft deadline ever bites, the same provider is not always the one starved."""

from __future__ import annotations

import datetime as _dt

from .base import Provider
from .clinicaltrials import ClinicalTrialsProvider
from .europepmc import EuropePmcProvider
from .guidelines import build_guideline_providers
from .pubmed import PubMedProvider


def build_providers() -> list[Provider]:
    return [EuropePmcProvider(), PubMedProvider(), ClinicalTrialsProvider(), *build_guideline_providers()]


def rotated(providers: list[Provider], today: _dt.date) -> list[Provider]:
    if not providers:
        return []
    k = today.timetuple().tm_yday % len(providers)
    return providers[k:] + providers[:k]
