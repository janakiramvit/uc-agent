"""Provider-specific query syntax: each provider builds its own query and date filter; nothing is shared."""

from __future__ import annotations

import datetime as dt

import pytest

from uc_evidence_discovery.providers.base import InvalidQuery, Window
from uc_evidence_discovery.providers.clinicaltrials import ClinicalTrialsProvider, trial_evidence_type
from uc_evidence_discovery.providers.europepmc import EuropePmcProvider
from uc_evidence_discovery.providers.guidelines import build_guideline_providers
from uc_evidence_discovery.providers.pubmed import PubMedProvider, check_translation
from uc_evidence_discovery.providers.registry import build_providers, rotated

W = Window(dt.date(2026, 11, 10), dt.date(2026, 11, 12))


def test_europepmc_uses_its_own_date_syntax_not_pubmed_syntax():
    q = EuropePmcProvider().build_query(W)
    assert "FIRST_IDATE:[2026-11-10 TO 2026-11-12]" in q
    assert "[pub_year]" not in q and "[tiab]" not in q and "[MeSH" not in q
    assert "NOT SRC:PPR" in q                       # preprints excluded


def test_the_old_zero_result_expression_is_rejected_before_it_is_ever_sent():
    with pytest.raises(InvalidQuery):
        EuropePmcProvider._lint('"ulcerative colitis" AND (2021:2026[pub_year])')


@pytest.mark.parametrize("bad", ['("ulcerative colitis" AND FIRST_IDATE:[2026-11-10 TO 2026-11-12]',   # unbalanced (
                                 '"ulcerative colitis AND FIRST_IDATE:[2026-11-10 TO 2026-11-12]',      # unbalanced "
                                 '"ulcerative colitis"[tiab] AND FIRST_IDATE:[2026-11-10 TO 2026-11-12]'])
def test_europepmc_lint_rejects_malformed_or_cross_syntax_queries(bad):
    with pytest.raises(InvalidQuery):
        EuropePmcProvider._lint(bad)


def test_pubmed_uses_field_tags_and_slash_dates():
    p = PubMedProvider()
    assert '"ulcerative colitis"[tiab]' in p.build_query(W) and "[MeSH Terms]" in p.build_query(W)
    assert p._dates(W) == ("2026/11/10", "2026/11/12")        # PubMed date format, not ISO


def test_clinicaltrials_uses_its_own_area_range_syntax():
    q = ClinicalTrialsProvider().build_query(W)
    assert "AREA[LastUpdatePostDate]RANGE[2026-11-10,2026-11-12]" in q
    assert "FIRST_IDATE" not in q and "[tiab]" not in q


def test_no_two_provider_queries_are_the_same_string():
    qs = {p.name: p.build_query(W) for p in build_providers()}
    assert qs["europepmc"] != qs["pubmed"] != qs["clinicaltrials"]
    assert "FIRST_IDATE" not in qs["pubmed"] and "AREA[" not in qs["pubmed"]
    assert "[tiab]" not in qs["europepmc"] and "[tiab]" not in qs["clinicaltrials"]


def test_all_eight_sources_are_configured_and_unique():
    names = [p.name for p in build_providers()]
    assert sorted(names) == sorted(["europepmc", "pubmed", "clinicaltrials", "aga", "acg", "ecco", "nice", "bsg"])
    assert len(set(names)) == 8


def test_rotation_starts_elsewhere_each_day_but_always_covers_every_provider():
    ps = build_providers()
    firsts = {rotated(ps, dt.date(2026, 11, 10) + dt.timedelta(days=i))[0].name for i in range(8)}
    assert len(firsts) == 8
    for i in range(8):
        assert {p.name for p in rotated(ps, dt.date(2026, 11, 10) + dt.timedelta(days=i))} == {p.name for p in ps}


def test_trial_status_maps_to_trial_types_never_to_study_or_guideline():
    assert trial_evidence_type("RECRUITING").value == "ongoing_trial"
    assert trial_evidence_type("ACTIVE_NOT_RECRUITING").value == "ongoing_trial"
    assert trial_evidence_type("COMPLETED").value == "completed_trial_record"


def test_society_provider_queries_use_their_own_journal_filters():
    q = {p.name: p.build_query(W) for p in build_guideline_providers()}
    assert '"Gastroenterology"[ta]' in q["aga"] and '"Am J Gastroenterol"[ta]' in q["acg"]
    assert '"J Crohns Colitis"[ta]' in q["ecco"] and '"Gut"[ta]' in q["bsg"]
    assert "[ta]" not in q["nice"]                      # NICE is not a PubMed journal


def test_pubmed_translation_check_flags_silently_dropped_clauses():
    # NCBI answers garbage with a full-database count and no error; the translation is the only tell
    with pytest.raises(InvalidQuery):
        check_translation('"ulcerative colitis"[All Fields]', {}, {}, expect=("Date - Entry",))
    with pytest.raises(InvalidQuery):
        check_translation("x [Date - Entry]", {"phrasesnotfound": ["foo"]}, {}, expect=())
    with pytest.raises(InvalidQuery):
        check_translation("x [Date - Entry]", {}, {"outputmessages": ["AND", "("]}, expect=())
    # empty lists inside the error/warning dicts are NORMAL and must not trip the check
    check_translation('"ulcerative colitis"[Title/Abstract] [Date - Entry]',
                      {"phrasesnotfound": [], "fieldsnotfound": []}, {"outputmessages": []},
                      expect=("Date - Entry", "ulcerative colitis"))
