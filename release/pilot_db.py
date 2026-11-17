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


def _prod_source_row(s: dict, source_type_raw: str) -> dict:
    """Copy of a live production source into the pilot dataset (claims reference (dataset, source_ref))."""
    cond = s.get("conditionApplicability") or "ibd_general"
    return {"source_ref": s["sourceId"], "title": s["sourceTitle"],
            "source_type": "guideline" if source_type_raw == "guideline" else "patient_information",
            "source_type_raw": source_type_raw, "status": None, "authors": None, "journal": None,
            "pub_year": s.get("publicationYear"), "authoritative_url": s.get("sourceUrl"), "canonical_url": s.get("sourceUrl"),
            "pmid": None, "pmcid": None, "doi": None, "full_text_verification": "as recorded for prototype-v1",
            "condition_applicability": [t.strip() for t in cond.split(";") if t.strip()], "condition_applicability_raw": cond,
            "disease_context": None, "disease_context_raw": s.get("diseaseContext"), "main_relevant_finding": None,
            "evidence_limitations": s.get("evidenceLimitations"), "access_licensing_note": "public page/abstract only",
            "region_applicability_note": s.get("canadaUsApplicability"), "regional_assessment": s.get("regionalAssessment"),
            "review_status": None, "review_status_raw": REVIEW_STATUS_RAW}


def reissued_claim_row(item: dict, prod_source: dict) -> dict:
    return {"claim_ref": item["claimId"], "source_ref": item["sourceId"], "split_from_ref": item["replaces"],
            "source_title": prod_source["sourceTitle"], "topic": None,
            "condition_applicability": ["ibd_general", "ulcerative_colitis"],
            "condition_applicability_raw": "ibd_general; ulcerative_colitis", "disease_context": None,
            "disease_context_raw": "general_or_unspecified", "claim_text": item["claimText"],
            "original_claim_text": item["supportingExcerpt"], "qa_proposed_claim_text": None,
            "supporting_excerpt": item["supportingExcerpt"], "exact_authoritative_passage": None,
            "precise_locator": f"Re-issue of live claim {item['replaces']} (same verbatim excerpt and source locator)",
            "authoritative_url": prod_source["sourceUrl"], "evidence_status": "ready_for_human_review",
            "final_qa_eligibility": None, "approved_export_eligibility": None,
            "verification_status": f"verbatim excerpt carried over from live claim {item['replaces']}", "remediation_note": None,
            "limitations": item["limitations"], "applicability_limitations": "IBD-wide statement; UC is covered at source level only",
            "plain_language_explanation": item["claimText"], "outcome_type": "evidence_uncertainty" if item["claimId"] == "CLM-706" else "general_patient_education",
            "outcome_type_raw": "evidence_uncertainty" if item["claimId"] == "CLM-706" else "general_patient_education",
            "study_type": item["evidenceLevel"], "evidence_level": "consensus_statement" if item["claimId"] == "CLM-705" else "official_patient_information",
            "evidence_level_raw": item["evidenceLevel"], "confidence": item["confidence"], "confidence_raw": item["confidence"],
            "review_status": None, "review_status_raw": REVIEW_STATUS_RAW,
            "prototype_eligibility_status": "prototype_eligible_with_limitation",
            "prototype_eligibility_status_raw": "prototype_eligible_with_limitation"}


def promotion_preview(b: dict, dec: dict) -> dict:
    rows = {r["claimId"]: r for r in b["claim_rows"] if r["origin"] == "staging" and r["recommendation"] == "proposed_include"}
    ids = approved_claim_ids(dec, set(rows))
    raws = {c["claimId"]: c for c in json.loads((inv.FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    srcs = {s["sourceId"]: s for s in json.loads((inv.FROZEN / "staging-sources.json").read_text())["sources"]}
    prod = {s["sourceId"]: s for s in json.loads(inv.PRODUCTION_JSON.read_text())["sources"]}
    live = dec.get("live", {})
    bad = {k: v for k, v in live.items() if v not in ("keep", "keep_relabelled", "retire")}
    if bad or set(live) - {"CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"}:
        raise ValueError(f"invalid live-claim decisions: {live}")
    reissue = [i for i in b["curation"].get("reissued_live", []) if live.get(i["replaces"]) == "keep_relabelled"]
    claims = [claim_row(rows[i], raws.get(i)) for i in ids] + [reissued_claim_row(i, prod[i["sourceId"]]) for i in reissue]
    sids = sorted({c["source_ref"] for c in claims if c["source_ref"] in srcs})
    sources = [source_row(srcs[s], [r for r in rows.values() if r["sourceId"] == s and r["claimId"] in ids]) for s in sids]
    sources += [_prod_source_row(prod[i["sourceId"]], i["sourceType"]) for i in reissue]
    retired = sorted(k for k, v in live.items() if v == "retire")
    replaced = sorted(i["replaces"] for i in reissue)
    deferred_ids = sorted(r["claimId"] for r in b["claim_rows"]
                          if r["origin"] == "staging" and r["claimId"] not in ids and r["category"] != "duplicate"
                          and r["recommendation"] != "review_candidate")
    meta = {"package_version": "pilot-additions-1.0.0", "created_at": "2026-11-17",
            "intended_use": "Technical research pilot only. Owner-reviewed (owner_reviewed_for_pilot); NOT clinician-approved.",
            "limitations": ["Abstract-level verification only; full texts were not read.",
                            "Owner review for a technical research pilot is not clinical approval.",
                            "Guideline statements may not reflect Canadian/US practice; discuss care decisions with your clinician."]}
    return {"dataset": PILOT_DATASET, "version": PILOT_VERSION, "sources": sources, "claims": claims,
            "excludedClaimRefs": deferred_ids, "retiredLiveClaimRefs": retired, "replacedLiveClaimRefs": replaced,
            "packageMeta": meta,
            "summary": {"sources": len(sources), "claims": len(claims), "approvedIds": ids,
                        "reissuedLive": [i["claimId"] for i in reissue], "retiredLive": retired, "replacedLive": replaced,
                        "excludedCount": len(deferred_ids)}}


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
    extra_src = [{"sourceId": a["sourceId"], "title": a["title"], "evidenceType": a["evidenceType"], "doi": a["doi"],
                  "pubmedId": a["pmid"], "canonicalUrl": a["url"], "publicationDate": a["year"], "authoredForRelease": True}
                 for a in b["curation"].get("authored_sources", [])]
    srcs = srcs + extra_src
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
                 "owner_decision": r.get("ownerDecision"),
                 "owner_reviewed": r.get("ownerDecision") is not None,
                 "review_status_raw": REVIEW_STATUS_RAW if r.get("ownerDecision") else None,
                 "approved": False}, prov, {})
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
    # live claims leave patient retrieval through the pilot view only; prototype-v1 rows are never modified or deleted
    for ref in preview["retiredLiveClaimRefs"]:
        conn.execute("INSERT INTO canonical.excluded_claim (dataset_id, claim_ref, result, reason, origin) VALUES (%s,%s,%s,%s,%s)",
                     (did, ref, "retired_from_patient_retrieval", "owner decision 2026-11-17; preserved in prototype-v1", "owner-retired-live"))
    for ref in preview["replacedLiveClaimRefs"]:
        conn.execute("INSERT INTO canonical.excluded_claim (dataset_id, claim_ref, result, reason, origin) VALUES (%s,%s,%s,%s,%s)",
                     (did, ref, "replaced_by_relabelled_claim", "owner kept it with clearer labelling; re-issued under a new ID; original preserved", "owner-relabelled-live"))
    return {"dataset_id": did, **preview["summary"]}


def write_preview(b: dict, dec: dict) -> list[Path]:
    """Exact promotion preview (machine + human readable). Writes files only; touches no database."""
    pv = promotion_preview(b, dec)
    out = REPO / "release" / "output"
    (out / "promotion-preview.json").write_text(json.dumps(pv, indent=2, ensure_ascii=False, default=str) + "\n")
    cand = [r for r in b["claim_rows"] if r["recommendation"] == "review_candidate"]
    L = ["# Exact promotion preview - pilot-additions 1.0.0 (dev canonical)", "",
         "Nothing below has been promoted. Records would be written as `owner_reviewed_for_pilot` (never clinician-approved).", "",
         f"- **Promote ({len(pv['claims'])} claims, {len(pv['sources'])} sources):** " + ", ".join(c["claim_ref"] for c in pv["claims"]),
         f"- **Retire live claims from patient retrieval (preserved in prototype-v1):** {', '.join(pv['retiredLiveClaimRefs'])}",
         f"- **Replace live claims with relabelled re-issues:** {', '.join(f'{a}->{c}' for a, c in zip(pv['replacedLiveClaimRefs'], [i for i in pv['summary']['reissuedLive']]))}",
         f"- **Excluded (deferred, never promoted):** {len(pv['excludedClaimRefs'])} staged claims, including owner deferrals CLM-126 and CLM-702",
         "- **Not promoted, returned for review:** " + ", ".join(r["claimId"] for r in cand), ""]
    for c in pv["claims"]:
        L += [f"## {c['claim_ref']} ({c['source_ref']})", "", f"**Patient-facing claim:** {c['claim_text']}", "",
              f"**Exact excerpt:** \"{c['supporting_excerpt']}\"", "",
              f"**Applicability:** {c['condition_applicability_raw']} | **Evidence:** {c['evidence_level_raw']} | **Confidence:** {c['confidence_raw']} | "
              f"**Review status:** {c['review_status_raw']}", "", f"**Limitations:** {c['limitations']}", "",
              f"**Citation:** {c['authoritative_url']}", ""]
    L += ["## Candidate returned for review (not in this preview)", ""]
    for r in cand:
        L += [f"### {r['claimId']} ({r['sourceId']}): {r['sourceTitle']} ({r['sourceYear']})", "", f"**Proposed claim:** {r['patient']}", "",
              f"**Exact excerpt:** \"{r['excerpt']}\"", "", f"**Limitations:** {r['limitations']}", "", f"**Citation:** {r['citationUrl']}", ""]
    (out / "PROMOTION-PREVIEW.md").write_text("\n".join(L) + "\n")
    return [out / "promotion-preview.json", out / "PROMOTION-PREVIEW.md"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("stage", "plan", "preview", "promote"))
    ap.add_argument("--confirm-promote", action="store_true")
    a = ap.parse_args()
    b = build_all()
    if a.cmd == "preview":
        for p in write_preview(b, decisions()):
            print("wrote", p.relative_to(REPO))
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
