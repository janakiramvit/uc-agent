"""Staging -> canonical promotion. GATED.

Refuses unless ``confirm=True`` (the ingest CLI passes it only for
``--step promote --confirm-promote``). One transaction per dataset. DB constraints
enforce referential integrity; anything that fails validation or carries a material
reconciliation mismatch is written to ``quarantine.record`` and NOT promoted.

Not executed in the planning/build session - no ``DATABASE_URL``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pipeline.reconcile import ReconResult
from pipeline.validate import Outcome, ValidationReport


class PromotionNotConfirmed(RuntimeError):
    pass


@dataclass
class PromotionPlan:
    dataset: str
    dataset_version: str
    promote_sources: list[Outcome]
    promote_claims: list[Outcome]
    promote_excluded: list[Outcome]
    promote_qa: list[Outcome]
    quarantine: list[dict]          # {entity_type, natural_key, reasons, raw}

    def summary(self) -> dict:
        return {
            "dataset": self.dataset,
            "sources": len(self.promote_sources),
            "claims": len(self.promote_claims),
            "excluded": len(self.promote_excluded),
            "qa": len(self.promote_qa),
            "quarantine": len(self.quarantine),
        }


def build_plan(report: ValidationReport, recon: ReconResult, *, dataset_version="1.0.0"
               ) -> PromotionPlan:
    """Pure: decide what would be promoted vs quarantined. No DB."""
    mismatch_refs = {
        (q.dataset, q.entity_type, q.entity_ref)
        for q in recon.quarantine_recommendations
        if q.dataset == report.dataset
    }
    q: list[dict] = []
    promote = {"source_raw": [], "claim_raw": [], "excluded_raw": [], "claim_qa_raw": []}
    for o in report.outcomes:
        if o.target not in promote:
            continue
        et = "source" if o.target == "source_raw" else (
            "claim" if o.target in ("claim_raw", "claim_qa_raw") else "excluded")
        blocked = o.status == "quarantine"
        reasons = list(o.errors)
        if (report.dataset, et, o.natural_key) in mismatch_refs and o.target in (
                "source_raw", "claim_raw"):
            blocked = True
            reasons.append("material reconciliation mismatch (see reconciliation_result)")
        if blocked:
            q.append({"entity_type": et, "natural_key": o.natural_key,
                      "reasons": reasons or ["quarantined"], "raw": o.canonical})
        else:
            promote[o.target].append(o)
    return PromotionPlan(
        dataset=report.dataset, dataset_version=dataset_version,
        promote_sources=promote["source_raw"], promote_claims=promote["claim_raw"],
        promote_excluded=promote["excluded_raw"], promote_qa=promote["claim_qa_raw"],
        quarantine=q,
    )


# ------------------------------------------------------------------ DB write (gated)

_INSERT_SOURCE = """
INSERT INTO canonical.source (dataset_id, source_ref, title, source_type, source_type_raw,
    status, authors, journal, pub_year, authoritative_url, canonical_url, pmid, pmcid, doi,
    full_text_verification, condition_applicability, condition_applicability_raw,
    disease_context, disease_context_raw, main_relevant_finding, evidence_limitations,
    access_licensing_note, region_applicability_note, regional_assessment,
    review_status, review_status_raw)
VALUES (%(dataset_id)s, %(source_ref)s, %(title)s, %(source_type)s, %(source_type_raw)s,
    %(status)s, %(authors)s, %(journal)s, %(pub_year)s, %(authoritative_url)s,
    %(canonical_url)s, %(pmid)s, %(pmcid)s, %(doi)s, %(full_text_verification)s,
    %(condition_applicability)s, %(condition_applicability_raw)s, %(disease_context)s,
    %(disease_context_raw)s, %(main_relevant_finding)s, %(evidence_limitations)s,
    %(access_licensing_note)s, %(region_applicability_note)s, %(regional_assessment)s,
    %(review_status)s, %(review_status_raw)s)
RETURNING id
"""

_INSERT_CLAIM = """
INSERT INTO canonical.claim (dataset_id, claim_ref, source_ref, split_from_ref,
    source_title, topic, condition_applicability, condition_applicability_raw,
    disease_context, disease_context_raw, claim_text, original_claim_text,
    qa_proposed_claim_text, supporting_excerpt, exact_authoritative_passage,
    precise_locator, authoritative_url, evidence_status, final_qa_eligibility,
    approved_export_eligibility, verification_status, remediation_note, limitations,
    applicability_limitations, plain_language_explanation, outcome_type, outcome_type_raw,
    study_type, evidence_level, evidence_level_raw, confidence, confidence_raw,
    review_status, review_status_raw, prototype_eligibility_status,
    prototype_eligibility_status_raw)
VALUES (%(dataset_id)s, %(claim_ref)s, %(source_ref)s, %(split_from_ref)s,
    %(source_title)s, %(topic)s, %(condition_applicability)s, %(condition_applicability_raw)s,
    %(disease_context)s, %(disease_context_raw)s, %(claim_text)s, %(original_claim_text)s,
    %(qa_proposed_claim_text)s, %(supporting_excerpt)s, %(exact_authoritative_passage)s,
    %(precise_locator)s, %(authoritative_url)s, %(evidence_status)s, %(final_qa_eligibility)s,
    %(approved_export_eligibility)s, %(verification_status)s, %(remediation_note)s,
    %(limitations)s, %(applicability_limitations)s, %(plain_language_explanation)s,
    %(outcome_type)s, %(outcome_type_raw)s, %(study_type)s, %(evidence_level)s,
    %(evidence_level_raw)s, %(confidence)s, %(confidence_raw)s, %(review_status)s,
    %(review_status_raw)s, %(prototype_eligibility_status)s,
    %(prototype_eligibility_status_raw)s)
RETURNING id
"""


_SOURCE_KEYS = (
    "source_ref", "title", "source_type", "source_type_raw", "status", "authors",
    "journal", "pub_year", "authoritative_url", "canonical_url", "pmid", "pmcid", "doi",
    "full_text_verification", "condition_applicability", "condition_applicability_raw",
    "disease_context", "disease_context_raw", "main_relevant_finding",
    "evidence_limitations", "access_licensing_note", "region_applicability_note",
    "regional_assessment", "review_status", "review_status_raw",
)
_CLAIM_KEYS = (
    "claim_ref", "source_ref", "split_from_ref", "source_title", "topic",
    "condition_applicability", "condition_applicability_raw", "disease_context",
    "disease_context_raw", "claim_text", "original_claim_text", "qa_proposed_claim_text",
    "supporting_excerpt", "exact_authoritative_passage", "precise_locator",
    "authoritative_url", "evidence_status", "final_qa_eligibility",
    "approved_export_eligibility", "verification_status", "remediation_note",
    "limitations", "applicability_limitations", "plain_language_explanation",
    "outcome_type", "outcome_type_raw", "study_type", "evidence_level",
    "evidence_level_raw", "confidence", "confidence_raw", "review_status",
    "review_status_raw", "prototype_eligibility_status",
    "prototype_eligibility_status_raw",
)


def _row(canonical: dict, keys: tuple[str, ...], dataset_id: int) -> dict:
    out = {k: canonical.get(k) for k in keys}
    out["dataset_id"] = dataset_id
    return out


def promote(conn, plans: list[PromotionPlan], recon: ReconResult, batch_id: str, *,
            confirm: bool = False) -> dict:
    if not confirm:
        raise PromotionNotConfirmed(
            "promote() requires confirm=True (ingest: --step promote --confirm-promote)"
        )
    results: dict = {}
    src_keys, clm_keys = _SOURCE_KEYS, _CLAIM_KEYS

    for plan in plans:
        with conn.transaction():
            (dataset_id,) = conn.execute(
                "SELECT dataset_id FROM canonical.dataset WHERE code=%s AND version=%s",
                (plan.dataset, plan.dataset_version),
            ).fetchone()
            for o in plan.promote_sources:
                conn.execute(_INSERT_SOURCE, _row(o.canonical, src_keys, dataset_id))
            for o in plan.promote_claims:
                (cid,) = conn.execute(_INSERT_CLAIM,
                                      _row(o.canonical, clm_keys, dataset_id)).fetchone()
                conn.execute(
                    "INSERT INTO canonical.claim_citation "
                    "(claim_id, dataset_id, citation_url, exact_locator, supporting_excerpt, "
                    " authoritative_passage) VALUES (%s,%s,%s,%s,%s,%s)",
                    (cid, dataset_id, o.canonical.get("authoritative_url"),
                     o.canonical.get("precise_locator"),
                     o.canonical.get("supporting_excerpt"),
                     o.canonical.get("exact_authoritative_passage")),
                )
            for o in plan.promote_excluded:
                conn.execute(
                    "INSERT INTO canonical.excluded_claim "
                    "(dataset_id, claim_ref, result, reason, origin) VALUES (%s,%s,%s,%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (dataset_id, o.natural_key, o.canonical.get("result"),
                     o.canonical.get("reason"), o.canonical.get("origin_sheet")),
                )
            for o in plan.promote_qa:
                f = o.canonical
                conn.execute(
                    "INSERT INTO canonical.claim_qa "
                    "(dataset_id, claim_ref, qa_dimension, qa_outcome, qa_note, findings) "
                    "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (dataset_id, f.get("claim_ref"), f.get("qa_dimension"),
                     f.get("qa_outcome"), f.get("qa_note"),
                     json.dumps(f.get("findings") or {})),
                )
            for qr in plan.quarantine:
                conn.execute(
                    "INSERT INTO quarantine.record "
                    "(batch_id, dataset_code, entity_type, natural_key, raw, reasons, source_step) "
                    "VALUES (%s,%s,%s,%s,%s,%s,'promote')",
                    (batch_id, plan.dataset, qr["entity_type"], qr["natural_key"],
                     json.dumps(qr["raw"], default=str), qr["reasons"]),
                )
            # snapshot the approved reconciliation into canonical
            for r in recon.rows:
                if r.comparison == "A" and r.status == "match":
                    continue  # keep the note table focused on findings
                conn.execute(
                    "INSERT INTO canonical.reconciliation_note "
                    "(dataset_id, comparison, entity_type, entity_ref, field, status, "
                    " material, left_label, right_label, detail) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (dataset_id, r.comparison, r.entity_type, r.entity_ref, r.field,
                     r.status, r.material, r.left, r.right, None),
                )
            conn.execute(
                "UPDATE canonical.dataset SET status='promoted', ingested_at=now(), "
                "load_batch_id=%s WHERE dataset_id=%s", (batch_id, dataset_id))
        results[plan.dataset] = plan.summary()
    return results
