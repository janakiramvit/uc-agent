"""Enum single-source-of-truth: seed SQL stays in lock-step with pipeline.enums."""

from __future__ import annotations

from pipeline import gen_seed_sql
from pipeline.enums import CANONICAL_ENUMS, crosswalk, split_multi


def test_seed_sql_matches_enums_module():
    assert gen_seed_sql.main(["--check"]) == 0, \
        "0004_seed_metadata.sql is stale - run: python -m pipeline.gen_seed_sql"


def test_split_multi():
    assert split_multi("a; b; c") == ["a", "b", "c"]
    assert split_multi("a | b") == ["a", "b"]
    assert split_multi("") == [] and split_multi(None) == []


def test_crosswalk_exact_and_mapped_and_unmapped():
    assert crosswalk("condition", "prototype_workbook", "ulcerative_colitis").mapped
    r = crosswalk("evidence_level", "prototype_workbook", "meta-analysis")
    assert r.matched and r.mapped and r.canonical_value == "meta_analysis"
    r = crosswalk("evidence_level", "prototype_workbook", "EL5")
    assert r.matched and not r.mapped and r.canonical_value is None      # pending
    r = crosswalk("condition", "prototype_workbook", "martian_colitis")
    assert not r.matched and not r.mapped                                # unmapped


def test_every_canonical_value_has_a_home():
    for dim, values in CANONICAL_ENUMS.items():
        assert len(values) == len(set(values))
        for v in values:
            assert crosswalk(dim, "models_py", v).canonical_value == v
