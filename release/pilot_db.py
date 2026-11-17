"""Dev-Supabase side of the pilot release: staging load, promotion preview, gated promotion to canonical.

    python -m release.pilot_db stage                      # load the reconciled inventory into dev STAGING (+ quarantine); idempotent
    python -m release.pilot_db preview                    # exact promotion preview from the recorded owner decisions (no writes)
    python -m release.pilot_db promote --confirm-promote  # promote ONLY owner-approved claims to canonical.pilot-additions (dev)

Writes only to staging.*, quarantine.record and (promote) the 'pilot-additions' dataset in canonical.*. Never touches prototype-v1,
never approves anything as clinically reviewed, never runs a destructive migration.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from release import inventory as inv
from release import review

REPO = inv.REPO
if str(REPO / "db") not in sys.path:
    sys.path.insert(0, str(REPO / "db"))      # the dev-DB pipeline package (promote SQL, connection guard)
DECISIONS = REPO / "release" / "config" / "owner-decisions.json"
STAGING_DATASET = "uc-evidence-expansion"
ANNOTATION_DATASET = "pilot-release-2026-11-17"
QUARANTINE_STEP = "release_review"
HARD_EXCLUDE = ("incomplete_or_unverifiable", "conflicting", "crohns_only")
PILOT_DATASET = "pilot-additions"
PILOT_VERSION = "1.0.0"
REVIEW_STATUS_RAW = "owner_reviewed_for_pilot"      # never 'approved' / clinician-approved

_EVIDENCE_LEVEL = {"Clinical practice guideline": "clinical guideline", "Consensus statement": "consensus statement",
                   "Randomized open-label trial": "randomized controlled trial"}
_SOURCE_TYPE = {"clinical_guideline": ("guideline", "guideline"), "published_study": ("randomized_trial", "randomized controlled trial")}
_CONFIDENCE = {"CLM-701": "low", "CLM-702": "low"}      # others: moderate (GRADE-based guideline / systematic review + Delphi)


# ------------------------------------------------------------------ pure builders
def build_all() -> dict:
    b = review.build()
    review.enrich(b)
    return b


def decisions() -> dict:
    return json.loads(DECISIONS.read_text())


def approved_claim_ids(dec: dict, proposed_ids: "set[str] | None" = None) -> list[str]:
    bad = {k: v for k, v in dec["proposed"].items() if v not in ("approve", "defer")}
    if bad:
        raise ValueError(f"owner decisions must be 'approve' or 'defer': {bad}")
    ids = sorted(k for k, v in dec["proposed"].items() if v == "approve")
    if proposed_ids is not None and set(ids) - proposed_ids:
        raise ValueError(f"cannot approve claims that were never proposed: {sorted(set(ids) - proposed_ids)}")
    return ids


def source_row(src_raw: dict, claim_rows: list[dict]) -> dict:
    cond = "ulcerative_colitis" if any(r["applicability"].startswith("ulcerative") for r in claim_rows) else \
        (src_raw.get("ucApplicability") or "ibd_general")
    year = (src_raw.get("publicationDate") or "")[:4]
    st_raw = "guideline" if src_raw.get("evidenceType") == "clinical_guideline" or "guideline" in (src_raw.get("sourceType") or "").lower() \
        or "consensus" in (src_raw.get("sourceType") or "").lower() else "randomized controlled trial"
    return {"source_ref": src_raw["sourceId"], "title": src_raw["title"],
            "source_type": "guideline" if st_raw == "guideline" else "randomized_trial", "source_type_raw": st_raw,
            "status": None, "authors": src_raw.get("authors"), "journal": src_raw.get("journalOrPublisher"),
            "pub_year": int(year) if year.isdigit() else None, "authoritative_url": src_raw.get("canonicalUrl"),
            "canonical_url": src_raw.get("canonicalUrl"), "pmid": src_raw.get("pubmedId") or None,
            "pmcid": src_raw.get("pmcId") or None, "doi": src_raw.get("doi") or None,
            "full_text_verification": "abstract_only_verified_verbatim_2026-11-17",
            "condition_applicability": [t.strip() for t in cond.split(";") if t.strip()],
            "condition_applicability_raw": cond, "disease_context": None,
            "disease_context_raw": "; ".join(src_raw.get("diseaseContext") or []) or None,
            "main_relevant_finding": None, "evidence_limitations": src_raw.get("limitations"),
            "access_licensing_note": "public abstract/metadata only; no full text or PDF stored",
            "region_applicability_note": (src_raw.get("regionalApplicability") or {}).get("assessment") if isinstance(src_raw.get("regionalApplicability"), dict) else None,
            "regional_assessment": "Canada/US applicability not assessed; owner-reviewed for a technical research pilot only",
            "review_status": None, "review_status_raw": REVIEW_STATUS_RAW}


def claim_row(row: dict, raw_claim: dict | None) -> dict:
    cond_raw = "ulcerative_colitis; ibd_general" if row["claimId"] == "CLM-126" else "ulcerative_colitis"
    disease = (raw_claim or {}).get("diseaseContext") or []
    outcome = "biomarkers" if row["claimId"] in ("CLM-115", "CLM-116", "CLM-117", "CLM-118", "CLM-121") else (
        "evidence_uncertainty" if row["claimId"] == "CLM-120" else (
            "surgery" if row["claimId"] == "CLM-702" else (
                "nutritional_status" if row["claimId"] == "CLM-701" else "disease_activity")))
    level = _EVIDENCE_LEVEL.get(row["design"], "other")
    return {"claim_ref": row["claimId"], "source_ref": row["sourceId"], "split_from_ref": None,
            "source_title": row["sourceTitle"], "topic": None,
            "condition_applicability": [t.strip() for t in cond_raw.split(";")], "condition_applicability_raw": cond_raw,
            "disease_context": None, "disease_context_raw": "; ".join(disease) if disease else "general_or_unspecified",
            "claim_text": row["patient"], "original_claim_text": row["claimText"],
            "qa_proposed_claim_text": None, "supporting_excerpt": row["excerpt"], "exact_authoritative_passage": None,
            "precise_locator": row["locator"], "authoritative_url": row["citationUrl"],
            "evidence_status": "ready_for_human_review", "final_qa_eligibility": None, "approved_export_eligibility": None,
            "verification_status": "verbatim_in_public_abstract_2026-11-17; full text not read",
            "remediation_note": None, "limitations": row["limitations"],
            "applicability_limitations": (row.get("population") or "") + " | " + row["strength"],
            "plain_language_explanation": row["patient"], "outcome_type": outcome, "outcome_type_raw": outcome,
            "study_type": row["design"], "evidence_level": {"clinical guideline": "formal_guideline",
                                                            "consensus statement": "consensus_statement",
                                                            "randomized controlled trial": "randomized_trial"}.get(level, "other"),
            "evidence_level_raw": level, "confidence": _CONFIDENCE.get(row["claimId"], "moderate"),
            "confidence_raw": _CONFIDENCE.get(row["claimId"], "moderate"), "review_status": None,
            "review_status_raw": REVIEW_STATUS_RAW, "prototype_eligibility_status": "prototype_eligible_with_limitation",
            "prototype_eligibility_status_raw": "prototype_eligible_with_limitation"}


def promotion_preview(b: dict, dec: dict) -> dict:
    rows = {r["claimId"]: r for r in b["claim_rows"] if r["origin"] == "staging" and r["recommendation"] == "proposed_include"}
    ids = approved_claim_ids(dec, set(rows))
    raws = {c["claimId"]: c for c in json.loads((inv.FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    srcs = {s["sourceId"]: s for s in json.loads((inv.FROZEN / "staging-sources.json").read_text())["sources"]}
    claims = [claim_row(rows[i], raws.get(i)) for i in ids]
    sids = sorted({c["source_ref"] for c in claims})
    sources = [source_row(srcs[s], [r for r in rows.values() if r["sourceId"] == s and r["claimId"] in ids]) for s in sids]
    deferred_ids = sorted(r["claimId"] for r in b["claim_rows"]
                          if r["origin"] == "staging" and r["claimId"] not in ids and r["category"] != "duplicate")
    meta = {"package_version": "pilot-additions-1.0.0", "created_at": "2026-11-17",
            "intended_use": "Technical research pilot only. Owner-reviewed (owner_reviewed_for_pilot); NOT clinician-approved.",
            "limitations": ["Abstract-level verification only; full texts were not read.",
                            "Owner review for a technical research pilot is not clinical approval.",
                            "Guideline statements may not reflect Canadian/US practice; discuss care decisions with your clinician."]}
    return {"dataset": PILOT_DATASET, "version": PILOT_VERSION, "sources": sources, "claims": claims,
            "excludedClaimRefs": deferred_ids, "packageMeta": meta,
            "summary": {"sources": len(sources), "claims": len(claims), "approvedIds": ids, "excludedCount": len(deferred_ids)}}


# ------------------------------------------------------------------ DB (thin)
def _connect():
    sys.path.insert(0, str(REPO / "db"))
    from pipeline.config import load_env
    from pipeline.db import connect
    return connect(load_env())


def stage_plan_rows(b: dict) -> dict:
    """What `stage` writes: staging rows for every staging-origin source/claim, annotations for every non-duplicate claim,
    quarantine rows for hard-excluded categories."""
    rows = [r for r in b["claim_rows"] if r["category"] != "duplicate"]
    quarantine = [r for r in rows if r["category"] in HARD_EXCLUDE]
    return {"annotations": rows, "quarantine": quarantine}


def stage(conn, b: dict, *, apply: bool) -> dict:
    from phase2.staging import _upsert, latest_batch
    batch = latest_batch(conn)
    raws = {c["claimId"]: c for c in json.loads((inv.FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    srcs = json.loads((inv.FROZEN / "staging-sources.json").read_text())["sources"]
    authored = {a["claimId"]: a for a in b["curation"]["authored_claims"]}
    summary = {"batch": batch, "applied": apply, "sourcesUpserted": len(srcs)}
    claims_in = [r for r in b["claim_rows"] if r["origin"] == "staging"]
    summary["claimsUpserted"] = len(claims_in)
    plan = stage_plan_rows(b)
    summary["annotations"] = len(plan["annotations"])
    already = {(d, k) for d, k in conn.execute("SELECT dataset_code, natural_key FROM quarantine.record WHERE batch_id=%s "
                                               "AND source_step<>%s", (batch, QUARANTINE_STEP)).fetchall()}
    fresh_q = [r for r in plan["quarantine"] if (_dataset(r), r["claimId"]) not in already]
    summary["quarantined"] = len(fresh_q)
    if not apply:
        return summary
    prov = {"adapter": "pilot_release", "adapter_version": "1", "cutoff": "9c7cd28", "inputs": "release/frozen"}
    for s in srcs:
        _upsert(conn, "source_raw", batch, STAGING_DATASET, s["sourceId"], {"source_ref": s["sourceId"], "title": s["title"],
                "evidence_type": s.get("evidenceType", "published_study")}, prov, s, status="valid_with_flags",
                flags=["pending_owner_review"], canonical={})
    for r in claims_in:
        raw = raws.get(r["claimId"]) or authored.get(r["claimId"], {})
        status = "quarantine" if r["category"] in HARD_EXCLUDE else "valid_with_flags"
        flag = ("proposed_for_pilot" if r["recommendation"] == "proposed_include" else f"deferred_for_pilot:{r['category']}")
        _upsert(conn, "claim_raw", batch, STAGING_DATASET, r["claimId"],
                {"claim_ref": r["claimId"], "source_ref": r["sourceId"], "claim_text": r["claimText"],
                 "supporting_excerpt": r["excerpt"], "precise_locator": r["locator"], "authoritative_url": r["citationUrl"],
                 "condition_applicability": [t.strip() for t in r["applicability"].split(";") if t.strip()]},
                {**prov, "authored": bool(r.get("authored"))}, raw, status=status,
                errors=[r["reason"]] if status == "quarantine" else [], flags=[flag], canonical={})
    for r in plan["annotations"]:
        _upsert(conn, "claim_qa_raw", batch, ANNOTATION_DATASET, r["uid"],
                {"category": r["category"], "recommendation": r["recommendation"], "reason": r["reason"],
                 "owner_reviewed": False, "approved": False}, prov, {})
    conn.execute("DELETE FROM quarantine.record WHERE batch_id=%s AND source_step=%s", (batch, QUARANTINE_STEP))
    for r in fresh_q:
        conn.execute("INSERT INTO quarantine.record (batch_id, dataset_code, entity_type, natural_key, raw, reasons, source_step) "
                     "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                     (batch, _dataset(r), "claim", r["claimId"], json.dumps({"category": r["category"]}), [r["reason"]],
                      QUARANTINE_STEP))
    return summary


def _dataset(r: dict) -> str:
    return {"production": "prototype-v1", "baseline-register": "baseline-register", "staging": STAGING_DATASET}[r["origin"]]


_INSERT_DATASET = ("INSERT INTO canonical.dataset (code, version, source_description, ingested_at, status, package_meta) "
                   "VALUES (%s,%s,%s, now(), 'promoted', %s) RETURNING dataset_id")


def promote(conn, preview: dict, *, confirm: bool) -> dict:
    if not confirm:
        raise RuntimeError("promotion requires --confirm-promote")
    from pipeline.promote import _INSERT_CLAIM, _INSERT_SOURCE
    (exists,) = conn.execute("SELECT count(*) FROM canonical.dataset WHERE code=%s", (preview["dataset"],)).fetchone()
    if exists:
        raise RuntimeError(f"dataset {preview['dataset']} already exists in canonical; refusing to promote twice")
    (did,) = conn.execute(_INSERT_DATASET, (preview["dataset"], preview["version"],
                          "owner-reviewed pilot additions (not clinician-approved)", json.dumps(preview["packageMeta"]))).fetchone()
    for i, text in enumerate(preview["packageMeta"]["limitations"], 1):
        conn.execute("INSERT INTO canonical.dataset_limitation (dataset_id, ordinal, text) VALUES (%s,%s,%s)", (did, i, text))
    for s in preview["sources"]:
        conn.execute(_INSERT_SOURCE, {**s, "dataset_id": did})
    for c in preview["claims"]:
        conn.execute(_INSERT_CLAIM, {**c, "dataset_id": did})
    conn.execute("INSERT INTO canonical.claim_citation (claim_id, dataset_id, citation_url, exact_locator, supporting_excerpt, "
                 "authoritative_passage) SELECT id, dataset_id, authoritative_url, precise_locator, supporting_excerpt, "
                 "exact_authoritative_passage FROM canonical.claim WHERE dataset_id=%s", (did,))
    for ref in preview["excludedClaimRefs"]:
        conn.execute("INSERT INTO canonical.excluded_claim (dataset_id, claim_ref, result, reason, origin) VALUES (%s,%s,%s,%s,%s)",
                     (did, ref, "deferred_for_pilot", "not approved in the 2026-11-17 owner review", "pilot-release"))
    return {"dataset_id": did, **preview["summary"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("stage", "plan", "preview", "promote"))
    ap.add_argument("--confirm-promote", action="store_true")
    a = ap.parse_args()
    b = build_all()
    if a.cmd == "preview":
        print(json.dumps(promotion_preview(b, decisions()), indent=2, ensure_ascii=False, default=str))
        return
    conn = _connect()
    try:
        if a.cmd in ("stage", "plan"):
            out = stage(conn, b, apply=a.cmd == "stage")
        else:
            out = promote(conn, promotion_preview(b, decisions()), confirm=a.confirm_promote)
        conn.commit() if (a.cmd in ("stage", "promote")) else conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
