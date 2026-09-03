"""Adapters parse the real workbooks into the expected staging records."""

from __future__ import annotations

import pytest

from pipeline.adapters.base import CLINICAL_FIELDS, ClinicalFieldDefaultError, apply_safe_default


def test_register_workbook_counts(adapted):
    c = adapted["baseline-register"].counts()
    assert c["source_raw"] == 26
    assert c["claim_raw"] == 61
    assert c["excluded_raw"] == 41          # 40 removed/replaced + CLM-092 unresolved
    assert c["reconcile_raw"] >= 20
    refs = {r.natural_key for r in adapted["baseline-register"].records
            if r.target == "claim_raw"}
    assert "CLM-005" in refs and "CLM-100" in refs and len(refs) == 61


def test_prototype_workbook_counts_match_json(adapted, registry):
    import json
    c = adapted["prototype-v1"].counts()
    assert c["source_raw"] == 20
    assert c["claim_raw"] == 49
    assert c["excluded_raw"] == 12
    excl = sorted(r.natural_key for r in adapted["prototype-v1"].records
                  if r.target == "excluded_raw")
    oracle = json.loads(registry["prototype_json"].path.read_text())
    assert excl == sorted(oracle["excludedClaimIds"])


def test_qa_workbook_is_overlay_only(adapted):
    recs = adapted["qa"].records
    assert not any(r.target in ("source_raw", "claim_raw") for r in recs)
    dims = {r.fields["qa_dimension"] for r in recs if r.target == "claim_qa_raw"}
    assert dims == {"corrected_claim", "source_and_locator", "safety_boundary", "exclusion"}
    assert sum(1 for r in recs if r.target == "claim_qa_raw") == 133


def test_multivalue_split_and_provenance(adapted):
    clm = next(r for r in adapted["baseline-register"].records
              if r.natural_key == "CLM-081" and r.target == "claim_raw")
    assert isinstance(clm.fields["condition_applicability"], list)
    assert set(clm.fields["condition_applicability"]) == {
        "ulcerative_colitis", "crohns_disease", "ibd_general"}
    assert clm.provenance["src_sheet"] == "Claims"
    assert clm.provenance["src_row"] > 3
    # provenance stores the file name only, never a local absolute path
    assert "/" not in clm.provenance["src_file"]


def test_no_adapter_warnings(adapted):
    for key in ("baseline-register", "prototype-v1", "qa"):
        assert adapted[key].warnings == [], adapted[key].warnings


def test_safe_default_guard_rejects_clinical_fields():
    assert apply_safe_default("adapter_version", None) == "1.0.0"
    for f in list(CLINICAL_FIELDS)[:5]:
        with pytest.raises(ClinicalFieldDefaultError):
            apply_safe_default(f, None)
