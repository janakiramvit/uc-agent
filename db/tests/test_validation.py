"""Validation policy: fatal vs pending vs clean, and never inventing clinical values."""

from __future__ import annotations

from pipeline.adapters.base import StagingRecord
from pipeline.validate import validate_dataset


def _wrap(records):
    return validate_dataset(records, dataset="t", input_format="prototype_workbook")


def _claim(natural_key="CLM-900", **fields):
    base = dict(source_ref="SRC-900", claim_text="x" * 40,
               supporting_excerpt="y" * 40, precise_locator="p 1",
               condition_applicability=["ulcerative_colitis"], disease_context=["remission"])
    base.update(fields)
    return StagingRecord(target="claim_raw", dataset="t", natural_key=natural_key,
                         fields=base)


SRC = StagingRecord(target="source_raw", dataset="t", natural_key="SRC-900",
                    fields=dict(title="t", source_type="guideline",
                                condition_applicability=["ibd_general"]))


def test_clean_claim_is_valid():
    rep = _wrap([SRC, _claim()])
    o = next(o for o in rep.outcomes if o.target == "claim_raw")
    assert o.status == "valid"
    assert o.canonical["condition_applicability"] == ["ulcerative_colitis"]


def test_bad_id_quarantined():
    rep = _wrap([SRC, _claim(natural_key="CLAIM_1")])
    o = next(o for o in rep.outcomes if o.target == "claim_raw")
    assert o.status == "quarantine"
    assert any("does not match" in e for e in o.errors)


def test_missing_locator_quarantined():
    rep = _wrap([SRC, _claim(precise_locator="")])
    o = next(o for o in rep.outcomes if o.natural_key == "CLM-900")
    assert o.status == "quarantine"
    assert any("precise_locator" in e for e in o.errors)


def test_dangling_source_ref_quarantined():
    rep = _wrap([SRC, _claim(source_ref="SRC-404")])
    o = next(o for o in rep.outcomes if o.natural_key == "CLM-900")
    assert o.status == "quarantine"
    assert any("does not resolve" in e for e in o.errors)


def test_unmapped_condition_is_fatal():
    rep = _wrap([SRC, _claim(condition_applicability=["martian_colitis"])])
    o = next(o for o in rep.outcomes if o.natural_key == "CLM-900")
    assert o.status == "quarantine"
    assert o.canonical["condition_applicability"] is None
    assert o.canonical["condition_applicability_raw"] == ["martian_colitis"]


def test_unmapped_evidence_level_is_pending_not_fatal():
    rep = _wrap([SRC, _claim(evidence_level="EL5")])
    o = next(o for o in rep.outcomes if o.natural_key == "CLM-900")
    assert o.status == "valid_with_flags"
    assert o.canonical["evidence_level"] is None                 # not inferred
    assert o.canonical["evidence_level_raw"] == "EL5"            # verbatim preserved
    assert any("pending_human_classification:evidence_level" in f for f in o.flags)


def test_real_datasets_have_zero_quarantine(validated):
    for ds, rep in validated.items():
        assert rep.quarantined == [], (ds, [o.errors for o in rep.quarantined])


def test_metadata_incomplete_claims_flagged_not_dropped(validated):
    base = validated["baseline-register"]
    for ref in ("CLM-096", "CLM-100"):
        o = next(o for o in base.outcomes if o.natural_key == ref and o.target == "claim_raw")
        assert o.status == "valid_with_flags"
        assert o.canonical["condition_applicability"] is None
        assert any("applicability_missing_or_pending" in f for f in o.flags)
