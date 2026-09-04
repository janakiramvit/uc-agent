"""UC-eligibility checks runnable BEFORE promotion (pure - operate on validated staging
records, not on canonical/view rows, which don't exist until promote).

The app's rule (agent_core/evidence_loader.is_uc_eligible): a claim is UC-eligible iff
its conditionApplicability string CONTAINS "ulcerative_colitis". CLM-083 must never
qualify in the prototype-v1 dataset - its broader baseline-register scope is quarantined
under requires_clinical_applicability_review specifically so it can't promote with UC
applicability inferred or upgraded.
"""

from __future__ import annotations

KNOWN_UC_ELIGIBLE = {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}


def _prototype_claim_outcomes(validated):
    return [o for o in validated["prototype-v1"].outcomes if o.target == "claim_raw"]


def test_clm083_prototype_scope_excludes_ulcerative_colitis(validated):
    o = next(o for o in _prototype_claim_outcomes(validated) if o.natural_key == "CLM-083")
    canon = o.canonical.get("condition_applicability") or []
    assert "ulcerative_colitis" not in canon
    assert canon == ["crohns_disease"]


def test_app_uc_substring_rule_over_prototype_raw_matches_known_five(validated):
    """Reproduces agent_core.evidence_loader.is_uc_eligible's exact substring rule over
    the *_raw verbatim field (what the app actually reads), not the canonical array."""
    eligible = set()
    for o in _prototype_claim_outcomes(validated):
        raw = o.canonical.get("condition_applicability_raw") or ""
        if "ulcerative_colitis" in raw:
            eligible.add(o.natural_key)
    assert eligible == KNOWN_UC_ELIGIBLE
    assert "CLM-083" not in eligible


def test_clm083_baseline_register_broader_scope_is_quarantined_for_review(validated, adapted):
    from pipeline.reconcile import reconcile

    res = reconcile({k: v.outcomes for k, v in validated.items()}, adapted["refs"].records)
    q = [x for x in res.quarantine_recommendations
        if x.entity_ref == "CLM-083" and x.entity_type == "claim"]
    assert q, "CLM-083 must remain quarantined"
    assert any("requires_clinical_applicability_review" in r
              for x in q for r in x.reasons)
    # never silently narrowed or dropped from baseline-register's own staged data
    o = next(o for o in validated["baseline-register"].outcomes
            if o.target == "claim_raw" and o.natural_key == "CLM-083")
    assert o.canonical.get("condition_applicability") == [
        "crohns_disease", "ibd_general", "ulcerative_colitis"]
