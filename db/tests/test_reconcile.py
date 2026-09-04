"""Reconciliation surfaces the real divergences and redacts the committable summary."""

from __future__ import annotations

from pipeline.reconcile import reconcile, write_summary


def _run(validated, adapted):
    return reconcile({k: v.outcomes for k, v in validated.items()},
                     adapted["refs"].records)


def test_prototype_workbook_matches_json_oracle(validated, adapted):
    res = _run(validated, adapted)
    a = [r for r in res.rows if r.comparison == "A"]
    assert a, "comparison A produced no rows"
    assert [r for r in a if r.status == "mismatch"] == []          # same-origin parity
    ids = res.id_stability["A:claim"]
    assert len(ids["both"]) == 49 and not ids["prototype_workbook_only"]


def test_url_differences_released_as_expected_versioned_difference(validated, adapted):
    """SRC-026 + CLM-097..100: prototype-v1's authoritative_url == baseline-register's
    OWN documented source.canonical_url for that source - a provenance-backed release,
    not a guess. Neither original URL is altered; both remain in left_value/right_value."""
    res = _run(validated, adapted)
    released = {(r.entity_type, r.entity_ref): r for r in res.rows
               if r.comparison == "C" and r.field == "authoritative_url"
               and r.classification == "expected_versioned_difference"}
    expected = {("source", "SRC-026"), ("claim", "CLM-097"), ("claim", "CLM-098"),
               ("claim", "CLM-099"), ("claim", "CLM-100")}
    assert set(released) == expected
    for key, row in released.items():
        assert row.material is False
        assert row.status == "mismatch"                 # still reported as a difference
        assert row.left_value and row.right_value        # both originals preserved
        assert row.left_value != row.right_value          # genuinely different strings
    mm = {(r.entity_type, r.entity_ref) for r in res.material_mismatches()}
    assert not (mm & expected), "released URL entities must not remain material"


def test_excerpt_differences_stay_quarantined_when_substantively_different(validated, adapted):
    """CLM-081/083/085: after isolating ONLY the documented 'Statement N:' label, the
    remaining text still differs (paraphrase / different passage / an unrelated
    trailing evidence-grade annotation on CLM-081) - rule 4's release condition is NOT
    met, so all three stay quarantined, unclassified (no invented extra normalization)."""
    res = _run(validated, adapted)
    mm = {(r.entity_ref, r.field): r for r in res.material_mismatches()}
    for cid in ("CLM-081", "CLM-083", "CLM-085"):
        row = mm[(cid, "supporting_excerpt")]
        assert row.classification is None
        assert row.left_value and row.right_value        # both originals preserved


def test_clm083_applicability_flagged_for_review_not_released(validated, adapted):
    res = _run(validated, adapted)
    row = next(r for r in res.material_mismatches()
              if r.entity_ref == "CLM-083" and r.field == "condition_applicability")
    assert row.classification == "requires_clinical_applicability_review"
    assert row.material is True                          # NOT released
    assert row.left_value == ["crohns_disease", "ibd_general", "ulcerative_colitis"]
    assert row.right_value == ["crohns_disease"]           # prototype's corrected scope, untouched


def test_quarantine_now_six_entities_not_sixteen(validated, adapted):
    res = _run(validated, adapted)
    q = {(x.dataset, x.entity_type, x.entity_ref) for x in res.quarantine_recommendations}
    assert len(q) == 6
    remaining_refs = {ref for (_ds, _et, ref) in q}
    assert remaining_refs == {"CLM-081", "CLM-083", "CLM-085"}
    released_refs = {"CLM-097", "CLM-098", "CLM-099", "CLM-100", "SRC-026"}
    assert not (remaining_refs & released_refs)


def test_classification_is_a_generic_rule_not_an_id_allowlist():
    """Prove the URL classifier fires from provenance alone - synthesize a claim whose
    ref isn't in the known set and confirm it still releases when the same documented
    condition (prototype url == register's own canonical_url) holds, and still stays
    material when it doesn't."""
    from pipeline.reconcile import ReconRow, _make_c_classifier

    base_sources = {"SRC-999": {"canonical_url": "https://pubmed.example/999"}}
    base_claims = {"CLM-999": {"source_ref": "SRC-999"}}
    classify = _make_c_classifier(base_sources=base_sources, base_claims=base_claims)

    released = ReconRow("C", "baseline-register", "prototype-v1", "claim", "CLM-999",
                        "authoritative_url", "mismatch", material=True,
                        left_value="https://publisher.example/pdf",
                        right_value="https://pubmed.example/999")
    classify(released)
    assert released.material is False
    assert released.classification == "expected_versioned_difference"

    not_released = ReconRow("C", "baseline-register", "prototype-v1", "claim", "CLM-999",
                            "authoritative_url", "mismatch", material=True,
                            left_value="https://publisher.example/pdf",
                            right_value="https://somewhere-else.example/x")
    classify(not_released)
    assert not_released.material is True                 # unrelated URL -> not released
    assert not_released.classification is None


def test_summary_is_redacted(validated, adapted, tmp_path):
    res = _run(validated, adapted)
    out = tmp_path / "SUMMARY.md"
    write_summary(res, out)
    text = out.read_text()
    # no evidence text / URLs / connection strings leak into the committable summary
    for needle in ("http://", "https://", "espen.org", "Statement 1:", "postgres://"):
        assert needle not in text, needle
    assert "material mismatches" in text
