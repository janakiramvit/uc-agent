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


def test_cross_dataset_flags_known_divergences(validated, adapted):
    res = _run(validated, adapted)
    mm = {(r.entity_ref, r.field) for r in res.material_mismatches()}
    assert ("CLM-083", "condition_applicability") in mm      # ECCO CLM-083 narrowing
    assert ("CLM-097", "authoritative_url") in mm            # ESPEN PDF vs PubMed URL
    assert ("SRC-026", "authoritative_url") in mm
    q = {(x.dataset, x.entity_ref) for x in res.quarantine_recommendations}
    assert ("baseline-register", "CLM-083") in q and ("prototype-v1", "CLM-083") in q


def test_summary_is_redacted(validated, adapted, tmp_path):
    res = _run(validated, adapted)
    out = tmp_path / "SUMMARY.md"
    write_summary(res, out)
    text = out.read_text()
    # no evidence text / URLs / connection strings leak into the committable summary
    for needle in ("http://", "https://", "espen.org", "Statement 1:", "postgres://"):
        assert needle not in text, needle
    assert "material mismatches" in text
