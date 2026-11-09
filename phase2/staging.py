"""Reconcile the Phase-2 inventory with dev Supabase *staging* and load the non-production records.

Writes ONLY to ``staging.*`` and ``quarantine.record`` in the dev project. Never touches ``canonical.*``,
never approves, promotes or embeds anything, and never re-inserts prototype-v1 / baseline-register rows that
staging already holds (they are reconciled, not duplicated).

    python -m phase2.staging --plan      # read-only: reconcile with staging, show what would be written
    python -m phase2.staging --apply     # perform the load (idempotent)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from phase2 import paths
from phase2.loaders import Record, load_all

DB_DIR = paths.REPO / "db"
NON_USABLE = ("incomplete", "conflicting", "crohns_only", "unverifiable")
ANNOTATION_DATASET = "phase2-inventory"       # dataset_code of the classification/provenance rows
QUARANTINE_STEP = "phase2_inventory"          # quarantine.record.source_step owned by this module
ADAPTER = "phase2_inventory"
EXPANSION_FILES = {"claims": paths.EXPANSION_CLAIMS, "sources": paths.EXPANSION_SOURCES}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _n(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


# ------------------------------------------------------------------ pure planning
def staging_claim_fields(row: dict, raw_claim: dict) -> dict:
    """Staging `fields` for an expansion claim, using the same field names the db adapters use."""
    return {
        "claim_ref": row["claim_id"], "source_ref": row["source_id"], "claim_text": row["claim_text"],
        "supporting_excerpt": row["supporting_excerpt"], "precise_locator": row["locator"],
        "authoritative_url": row["source_url"], "condition_applicability": row["uc_applicability"],
        "disease_context": row["disease_context"], "evidence_status": row["evidence_status"],
        "review_status": row["review_status"], "limitations": row["limitations"],
        "confidence": raw_claim.get("confidence"), "evidence_level": raw_claim.get("evidenceStrength"),
        "outcome_type": raw_claim.get("outcome"), "study_design": raw_claim.get("studyDesign"),
        "mapped_question_ids": row["mapped_question_ids"],
        "regional_applicability_note": raw_claim.get("regionalApplicabilityNote"),
    }


def staging_source_fields(s: dict) -> dict:
    return {
        "source_ref": s["sourceId"], "title": s.get("title"), "source_type": s.get("sourceType"),
        "authors": s.get("authors"), "journal": s.get("journalOrPublisher"), "publication_date": s.get("publicationDate"),
        "authoritative_url": s.get("canonicalUrl") or s.get("alternateUrl"), "doi": s.get("doi"),
        "pmid": s.get("pubmedId"), "study_design": s.get("studyDesign"), "evidence_limitations": s.get("limitations"),
        "region_applicability_note": s.get("regionalApplicability"), "full_text_status": s.get("fullTextStatus"),
        "review_status": s.get("humanReviewStatus"),
    }


def nonproduction_rows(result: dict) -> list[dict]:
    return [r for r in result["claims"] if r["originating_dataset"] != paths.DS_PRODUCTION and not r["in_production"]]


def validation_status_for(row: dict) -> str:
    return "quarantine" if row["status"] in NON_USABLE else "valid_with_flags"


def compare_to_staging(records: list[Record], existing: dict) -> dict:
    """Reconcile loaded records (prototype-v1 / baseline-register) against what staging already holds.

    ``existing`` maps (dataset_code, natural_key) -> staged claim ``fields``. Reports present / missing /
    content-mismatched. Pure; never proposes an insert for a dataset staging already owns.
    """
    out = {}
    for ds in (paths.DS_PRODUCTION, paths.DS_BASELINE):
        recs = [r for r in records if r.dataset == ds]
        present, missing, mismatched = 0, [], []
        for r in recs:
            f = existing.get((ds, r.claim_id))
            if f is None:
                missing.append(r.claim_id)
                continue
            present += 1
            diffs = []
            if _n(f.get("claim_text")) != _n(r.claim_text):
                diffs.append("claim_text")
            if _n(f.get("supporting_excerpt")) != _n(r.excerpt):
                diffs.append("supporting_excerpt")
            if _n(f.get("precise_locator")) != _n(r.locator):
                diffs.append("precise_locator")
            if _n(f.get("authoritative_url")) != _n(r.source_url):
                diffs.append("authoritative_url")
            sa = {t.lower() for t in (f.get("condition_applicability") or [])}
            if sa != {t.lower() for t in r.uc_applicability}:
                diffs.append("condition_applicability")
            if diffs:
                mismatched.append({"claim_id": r.claim_id, "fields": diffs})
        out[ds] = {"in_inventory": len(recs), "present_in_staging": present, "missing_from_staging": missing,
                   "content_mismatches": mismatched}
    return out


# ------------------------------------------------------------------ DB I/O (thin)
def _connect():
    sys.path.insert(0, str(DB_DIR))
    from pipeline.config import load_env
    from pipeline.db import connect

    return connect(load_env())


def latest_batch(conn) -> str:
    row = conn.execute("SELECT batch_id FROM staging.ingest_batch ORDER BY started_at DESC LIMIT 1").fetchone()
    if not row:
        raise RuntimeError("no staging.ingest_batch - run the db pipeline --step stage first")
    return str(row[0])


def fetch_existing_claim_fields(conn, batch_id: str) -> dict:
    rows = conn.execute("SELECT dataset_code, natural_key, fields FROM staging.claim_raw WHERE batch_id=%s",
                        (batch_id,)).fetchall()
    return {(d, k): f for d, k, f in rows}


def fetch_existing_keys(conn, batch_id: str, table: str, dataset: str) -> set[str]:
    rows = conn.execute(f"SELECT natural_key FROM staging.{table} WHERE batch_id=%s AND dataset_code=%s",
                        (batch_id, dataset)).fetchall()
    return {r[0] for r in rows}


def _upsert(conn, table, batch_id, dataset, key, fields, provenance, raw, status="pending",
            errors=None, flags=None, canonical=None) -> None:
    conn.execute(
        f"INSERT INTO staging.{table} (batch_id, dataset_code, natural_key, fields, provenance, raw, "
        "validation_status, validation_errors, validation_flags, canonical) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (batch_id, dataset_code, natural_key) DO UPDATE SET fields=EXCLUDED.fields, "
        "provenance=EXCLUDED.provenance, raw=EXCLUDED.raw, validation_status=EXCLUDED.validation_status, "
        "validation_errors=EXCLUDED.validation_errors, validation_flags=EXCLUDED.validation_flags, "
        "canonical=EXCLUDED.canonical",
        (batch_id, dataset, key, json.dumps(fields, default=str), json.dumps(provenance, default=str),
         json.dumps(raw, default=str), status, json.dumps(errors or []), json.dumps(flags or []),
         json.dumps(canonical or {}, default=str)))


def load(conn, batch_id: str, result: dict, records: list[Record], *, apply: bool) -> dict:
    """Plan (apply=False) or perform (apply=True) the Phase-2 staging load. Idempotent."""
    claims_raw = {c["claimId"]: c for c in json.loads(paths.EXPANSION_CLAIMS.read_text())["claims"]}
    sources_raw = {s["sourceId"]: s for s in json.loads(paths.EXPANSION_SOURCES.read_text())["sources"]}
    manifest_sha = hashlib.sha256(json.dumps(
        {k: result[k] for k in ("schema", "counts", "claims")}, sort_keys=True, default=str).encode()).hexdigest()
    prov_base = {"adapter": ADAPTER, "adapter_version": "1", "manifest_schema": result["schema"],
                 "inventory_sha256": manifest_sha}

    summary: dict = {"batch_id": batch_id, "applied": apply, "datasets_already_in_staging":
                     compare_to_staging(records, fetch_existing_claim_fields(conn, batch_id))}

    nonprod = nonproduction_rows(result)
    exp_rows = [r for r in nonprod if r["originating_dataset"] == paths.DS_EXPANSION]

    # ---- expansion sources + claims -> source_raw / claim_raw
    ds = paths.DS_EXPANSION
    have_src = fetch_existing_keys(conn, batch_id, "source_raw", ds)
    have_clm = fetch_existing_keys(conn, batch_id, "claim_raw", ds)
    src_ids = sorted(sources_raw)            # every possessed source, incl. ones with no candidate claim
    claimless = set(src_ids) - {r["source_id"] for r in exp_rows}
    summary["expansion_sources"] = {"to_insert": [s for s in src_ids if s not in have_src],
                                    "already_present": [s for s in src_ids if s in have_src]}
    summary["expansion_claims"] = {"to_insert": [r["claim_id"] for r in exp_rows if r["claim_id"] not in have_clm],
                                   "already_present": [r["claim_id"] for r in exp_rows if r["claim_id"] in have_clm]}
    if apply:
        for sid in src_ids:
            fields = staging_source_fields(sources_raw[sid])
            _upsert(conn, "source_raw", batch_id, ds, sid, fields,
                    {**prov_base, "src_file": str(paths.EXPANSION_SOURCES.relative_to(paths.REPO)),
                     "src_sha256": _sha(paths.EXPANSION_SOURCES)}, sources_raw[sid],
                    status="valid_with_flags",
                    flags=["pending_owner_review", *(["no_candidate_claims"] if sid in claimless else [])],
                    canonical=fields)
        for r in exp_rows:
            fields = staging_claim_fields(r, claims_raw[r["claim_id"]])
            _upsert(conn, "claim_raw", batch_id, ds, r["claim_id"], fields,
                    {**prov_base, "src_file": str(paths.EXPANSION_CLAIMS.relative_to(paths.REPO)),
                     "src_sha256": _sha(paths.EXPANSION_CLAIMS)}, claims_raw[r["claim_id"]],
                    status=validation_status_for(r),
                    errors=r["status_reasons"] if r["status"] in NON_USABLE else [],
                    flags=[f"phase2:status={r['status']}", "pending_owner_review", *r["review_flags"]],
                    canonical=fields)

    # ---- classification + provenance annotations for EVERY non-production record -> claim_qa_raw
    have_ann = fetch_existing_keys(conn, batch_id, "claim_qa_raw", ANNOTATION_DATASET)
    summary["annotations"] = {"to_insert": sum(1 for r in nonprod if r["record_id"] not in have_ann),
                              "already_present": sum(1 for r in nonprod if r["record_id"] in have_ann)}
    if apply:
        for r in nonprod:
            fields = {k: r[k] for k in ("claim_id", "originating_dataset", "status", "status_reasons",
                                        "applicability_class", "uc_applicability", "mapped_question_ids",
                                        "mapping_basis", "content_hash", "also_present_in", "variant_of",
                                        "review_flags", "in_production")}
            fields["owner_review_required"] = r["status"] == "usable"
            fields["approved"] = False
            _upsert(conn, "claim_qa_raw", batch_id, ANNOTATION_DATASET, r["record_id"], fields,
                    {**prov_base, "src_dataset": r["originating_dataset"]}, {})

    # ---- quarantine non-usable, non-production records (skip entities another step already quarantined)
    already = {(d, k) for d, k in conn.execute(
        "SELECT dataset_code, natural_key FROM quarantine.record WHERE batch_id=%s AND source_step<>%s",
        (batch_id, QUARANTINE_STEP)).fetchall()}
    to_q = [r for r in nonprod if r["status"] in NON_USABLE]
    fresh = [r for r in to_q if (r["originating_dataset"], r["claim_id"]) not in already]
    summary["quarantine"] = {
        "non_usable_nonproduction": len(to_q),
        "to_quarantine": [f'{r["record_id"]} ({r["status"]})' for r in fresh],
        "already_quarantined_by_other_step": [r["record_id"] for r in to_q
                                              if (r["originating_dataset"], r["claim_id"]) in already],
    }
    if apply:
        conn.execute("DELETE FROM quarantine.record WHERE batch_id=%s AND source_step=%s",
                     (batch_id, QUARANTINE_STEP))
        for r in fresh:
            conn.execute(
                "INSERT INTO quarantine.record (batch_id, dataset_code, entity_type, natural_key, raw, reasons, "
                "source_step) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (batch_id, r["originating_dataset"], "claim", r["claim_id"],
                 json.dumps({k: r[k] for k in ("claim_id", "status", "source_id", "applicability_class",
                                               "content_hash")}),
                 list(r["status_reasons"]) or ["unspecified"], QUARANTINE_STEP))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    from phase2.build import build

    records, summaries = load_all()
    result = build(records=list(records), summaries=summaries)
    conn = _connect()
    try:
        batch = latest_batch(conn)
        summary = load(conn, batch, result, records, apply=args.apply)
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
