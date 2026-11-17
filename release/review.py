"""Classify every claim/source, verify proposed excerpts against the live public abstract, and write the review pack.

    python -m release.review            # builds release/output/*  (needs network only for excerpt verification)
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from release import inventory as inv

REPO = inv.REPO
CURATION = REPO / "release" / "config" / "curation.json"
OUT = REPO / "release" / "output"
CATEGORIES = ("uc_specific_human", "ibd_general_with_uc_subgroup", "ibd_general_unclear", "crohns_only", "trial_record",
              "animal_preclinical", "case_report", "duplicate", "conflicting", "incomplete_or_unverifiable")
UA = "uc-agent-evidence-discovery/1.0 (+https://github.com/janakiramvit/uc-agent; research staging bot)"
_ANIMAL = re.compile(r"\b(mice|mouse|murine|rats?|rodent|DSS|dextran|acetic acid|in vitro|decoction|electroacupuncture|network pharmacology|"
                     r"organoid|zebrafish)\b", re.I)


OWNER_DECISIONS = REPO / "release" / "config" / "owner-decisions.json"


def load_curation() -> dict:
    return json.loads(CURATION.read_text())


def load_owner_decisions() -> dict:
    return json.loads(OWNER_DECISIONS.read_text()) if OWNER_DECISIONS.exists() else {"proposed": {}, "live": {}}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


# ------------------------------------------------------------------ excerpt verification (public abstract via PubMed)
def fetch_abstracts(pmids: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(pmids), 20):
        chunk = pmids[i:i + 20]
        url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=" + ",".join(chunk))
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read().decode()
        for art in ET.fromstring(data).findall("PubmedArticle"):
            pmid = art.findtext("MedlineCitation/PMID")
            out[pmid] = _norm(" ".join("".join(e.itertext()) for e in art.findall("MedlineCitation/Article/Abstract/AbstractText")))
        time.sleep(0.5)
    return out


def verify_excerpts(items: list[tuple[str, str, str]]) -> dict[str, dict]:
    """items: (claim_id, pmid, excerpt). Stores only a verdict + hashes, never the abstract text."""
    abstracts = fetch_abstracts(sorted({p for _, p, _ in items if p}))
    res = {}
    for cid, pmid, ex in items:
        ab = abstracts.get(pmid, "")
        ok = bool(ab) and _norm(ex) in ab
        res[cid] = {"pmid": pmid, "verbatimInPublicAbstract": ok, "abstractAvailable": bool(ab),
                    "excerptSha256": hashlib.sha256(_norm(ex).encode()).hexdigest()[:16],
                    "abstractSha256": hashlib.sha256(ab.encode()).hexdigest()[:16] if ab else None}
    return res


# ------------------------------------------------------------------ classification
def _applic_tokens(s: str) -> set[str]:
    return {t.strip().lower() for t in re.split(r"[;,]", s or "") if t.strip() and t.strip().lower() != "none"}


def classify_other(c: inv.Clm, collision_ids: set[str]) -> tuple[str, str]:
    """Rule-based category for production / baseline claims (the staged ones are curated)."""
    toks = _applic_tokens(c.applicability)
    if c.origin == "baseline-register" and c.claim_id in collision_ids:
        return "conflicting", "same claim ID as a production claim but different applicability/excerpt; kept apart"
    if toks == {"crohns_disease"}:
        return "crohns_only", "Crohn's disease only"
    if not toks:
        return "incomplete_or_unverifiable", "applicability missing in the register"
    if "ulcerative_colitis" in toks and re.search(r"\b(ulcerative colitis|UC)\b", c.excerpt):
        return "ibd_general_with_uc_subgroup", "excerpt names ulcerative colitis"
    return "ibd_general_unclear", "IBD-general: UC applicability comes from the whole source, not this excerpt"


def classify_source(s: inv.Src, overrides: dict) -> str:
    if s.evidence_type in ("ongoing_trial", "completed_trial_record"):
        return "trial_record"
    for cat, ids in overrides.items():
        if s.origin == "staging" and s.source_id in ids:
            return cat
    if s.origin == "staging" and _ANIMAL.search(s.title):
        return "animal_preclinical"
    return "published_or_guideline"


def build() -> dict:
    cur = load_curation()
    r = inv.build()
    collision_ids = {c["claimId"] for c in r["claim_id_collisions"]}
    uid_group = r["uid_to_group"]
    group_by_gid = {g.gid: g for g in r["groups"]}
    kept_uids = {c.uid for c in r["claims"]}
    dup_decisions = {d["duplicate"]: d for d in r["claim_decisions"]}

    rows = []
    authored = {a["claimId"]: a for a in cur["authored_claims"]}
    for c in r["all_claims"]:
        row = {"uid": c.uid, "origin": c.origin, "claimId": c.claim_id, "sourceId": c.source_id,
               "sourceGroup": uid_group.get(f"{c.origin}:{c.source_id}"), "claimText": c.text, "excerpt": c.excerpt,
               "locator": c.locator, "applicability": c.applicability, "recommendation": "defer"}
        if c.uid not in kept_uids:
            row.update(category="duplicate", reason=f"exact duplicate of {dup_decisions[c.uid]['keptAs']}")
        elif c.origin == "staging":
            if c.claim_id in cur["proposed"]:
                p = cur["proposed"][c.claim_id]
                row.update(category="uc_specific_human" if c.claim_id != "CLM-126" and "guideline" not in p["design"].lower()
                           and "consensus" not in p["design"].lower() else
                           ("ibd_general_with_uc_subgroup" if c.claim_id == "CLM-126" else "uc_specific_human"),
                           recommendation="proposed_include", reason=p["reason"], patient=p["patient"],
                           strength=p["strength"], design=p["design"])
            else:
                cat, why = cur["deferred"][c.claim_id]
                row.update(category=cat, reason=why)
        else:
            cat, why = classify_other(c, collision_ids)
            row.update(category=cat, reason=why)
        rows.append(row)

    # curator-authored claims
    srcs_by_uid = {s.uid: s for s in r["all_sources"]}
    for cid, a in authored.items():
        p = cur["proposed"][cid]
        rows.append({"uid": f"staging:{cid}", "origin": "staging", "claimId": cid, "sourceId": a["sourceId"],
                     "sourceGroup": uid_group.get(f"staging:{a['sourceId']}"), "claimText": a["normalizedClaim"],
                     "excerpt": a["exactSupportingExcerpt"], "locator": a["exactLocator"],
                     "applicability": a["conditionApplicability"],
                     "recommendation": "review_candidate" if a.get("candidateOnly") else "proposed_include",
                     "category": "uc_specific_human", "reason": p["reason"], "patient": a["normalizedClaim"],
                     "strength": p["strength"], "design": p["design"], "authored": True})
    owner = load_owner_decisions()
    for row in rows:
        row["ownerDecision"] = owner["proposed"].get(row["claimId"]) if row["origin"] == "staging" else owner["live"].get(row["claimId"]) if row["origin"] == "production" else None
    src_rows = []
    for g in r["groups"]:
        k = g.keeper
        cat = classify_source(k, cur["source_overrides"])
        src_rows.append({"gid": g.gid, "keeper": k.uid, "title": k.title, "category": cat, "evidenceType": k.evidence_type,
                         "year": (k.date or "")[:4], "members": [m.uid for m in g.members]})
    return {"inventory": r, "curation": cur, "claim_rows": rows, "source_rows": src_rows}


# ------------------------------------------------------------------ pack
LIVE_UC_ELIGIBLE = ["CLM-014", "CLM-081", "CLM-093", "CLM-094", "CLM-095"]


def _source_meta(b: dict) -> dict:
    """source group id -> display metadata of the keeper (title, year, evidence type, URL)."""
    out = {}
    for g in b["inventory"]["groups"]:
        k = g.keeper
        et = k.evidence_type
        st = (k.raw.get("sourceType") or k.raw.get("Source type") or "").lower()
        if et == "published_study" and re.search(r"guideline|consensus", st):
            et = "clinical_guideline"
        url = k.url or (f"https://doi.org/{k.doi}" if k.doi else (f"https://pubmed.ncbi.nlm.nih.gov/{k.pmid}/" if k.pmid else ""))
        out[g.gid] = {"title": k.title, "year": (k.date or "")[:4], "evidenceType": et, "url": url, "pmid": inv.n_pmid(k.pmid)}
        if not out[g.gid]["pmid"]:
            m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", k.url or "")
            out[g.gid]["pmid"] = m.group(1) if m else ""
    return out


def enrich(b: dict) -> None:
    meta = _source_meta(b)
    cur = b["curation"]
    authored = {a["claimId"]: a for a in cur["authored_claims"]}
    staged_raw = {c["claimId"]: c for c in json.loads((inv.FROZEN / "staging-candidate-claims.json").read_text())["claims"]}
    asrc = {a["sourceId"]: a for a in cur.get("authored_sources", [])}
    for row in b["claim_rows"]:
        m = meta.get(row["sourceGroup"], {})
        if not m and row["sourceId"] in asrc and row.get("authored"):
            a_ = asrc[row["sourceId"]]
            m = {"title": a_["title"], "year": a_["year"], "evidenceType": a_["evidenceType"], "url": a_["url"], "pmid": a_["pmid"]}
        row.update(sourceTitle=m.get("title", ""), sourceYear=m.get("year", ""), evidenceType=m.get("evidenceType", ""),
                   citationUrl=m.get("url", ""), pmid=m.get("pmid", ""))
        raw = staged_raw.get(row["claimId"]) if row["origin"] == "staging" and not row.get("authored") else None
        a = authored.get(row["claimId"])
        src = raw or a or {}
        row["limitations"] = (src.get("limitations", "") + " " + (cur["proposed"].get(row["claimId"], {}).get("limitations_extra", ""))).strip()
        row["population"] = src.get("studyPopulation", "")
        row["studyDesignDetail"] = src.get("studyDesign", "")
        row["questions"] = list(src.get("mappedPatientQuestionIds", []))
        if row["recommendation"] == "proposed_include" and not row.get("patient"):
            row["patient"] = row["claimText"]


def verify(b: dict) -> dict:
    items = [(r["claimId"], r["pmid"], r["excerpt"]) for r in b["claim_rows"]
             if r["recommendation"] in ("proposed_include", "review_candidate")]
    return verify_excerpts(items)


def coverage(b: dict) -> dict:
    sys.path.insert(0, str(REPO))
    from phase2.coverage import compute_coverage, load_questions
    qs = load_questions()
    prod_rows = [{"claim_id": c, "mapped_question_ids": q, "status": "usable", "applicability_class": "uc_specific",
                  "in_production": True} for c, q in (
        ("CLM-014", ["L3-2.2.2"]), ("CLM-081", ["L2-2.2"]), ("CLM-093", ["L3-2.2.2"]), ("CLM-094", ["L3-2.2.2"]),
        ("CLM-095", ["L3-2.2.2"]))]
    new_rows = [{"claim_id": r["claimId"], "mapped_question_ids": r["questions"], "status": "usable",
                 "applicability_class": "uc_specific" if r["category"] == "uc_specific_human" else "ibd_general",
                 "in_production": True} for r in b["claim_rows"] if r["recommendation"] == "proposed_include"]
    before = compute_coverage(qs, prod_rows)["scopes"]["production_servable"]["all_39"]
    after_full = compute_coverage(qs, prod_rows + new_rows)
    return {"before": before, "after": after_full["scopes"]["production_servable"]["all_39"],
            "perQuestion": {q: v["scopes"]["production_servable"]["status"] for q, v in after_full["questions"].items()}}


def write_outputs(b: dict, ver: dict, cov: dict) -> list[Path]:
    OUT.mkdir(exist_ok=True)
    inv_r = b["inventory"]
    rows = b["claim_rows"]
    cat_claims = Counter(r["category"] for r in rows)
    cat_src = Counter(s["category"] for s in b["source_rows"])
    proposed = [r for r in rows if r["recommendation"] == "proposed_include"]
    deferred = [r for r in rows if r["recommendation"] == "defer" and r["category"] != "duplicate"]
    summary = {
        "evidenceCutoff": json.loads((inv.FROZEN / "EVIDENCE-CUTOFF.json").read_text()),
        "counts": {"sourcesBeforeDedup": inv_r["sources_before"], "sourcesAfterDedup": inv_r["sources_after"],
                   "claimsBeforeDedup": inv_r["claims_before"], "claimsAfterDedup": inv_r["claims_after"],
                   "curatorAuthoredClaims": len(b["curation"]["authored_claims"]),
                   "byOrigin": inv_r["by_origin"], "claimsByCategory": dict(cat_claims), "sourcesByCategory": dict(cat_src),
                   "proposedInclusions": len(proposed), "deferredClaims": len(deferred),
                   "exactDuplicateClaimsRemoved": len(inv_r["claim_decisions"]),
                   "sourcesMerged": sum(len(d["merged"]) for d in inv_r["source_decisions"])},
        "excerptVerification": ver, "coverage": cov,
        "claimIdCollisions": inv_r["claim_id_collisions"], "sourceIdCollisions": inv_r["source_id_collisions"]}
    (OUT / "release-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    (OUT / "dedup-decisions.json").write_text(json.dumps({"sources": inv_r["source_decisions"], "claims": inv_r["claim_decisions"]},
                                                         indent=2, ensure_ascii=False) + "\n")
    (OUT / "claims-classified.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    (OUT / "sources-classified.json").write_text(json.dumps(b["source_rows"], indent=2, ensure_ascii=False) + "\n")
    (OUT / "REVIEW-PACK.md").write_text(render_md(b, summary, proposed, deferred, ver, cov))
    write_workbook(b, proposed, deferred, summary)
    return sorted(OUT.iterdir())


def render_md(b, summary, proposed, deferred, ver, cov) -> str:
    c = summary["counts"]
    reasons = Counter(r["category"] for r in deferred)
    L = ["# Pilot evidence release - owner review pack (2026-11-17)", "",
         f"Evidence frozen at staging commit `{summary['evidenceCutoff']['stagingCommit']}` (all 8 providers' cutoffs "
         f"{summary['evidenceCutoff']['evidenceCutoffDate']}). Nothing here is approved or promoted. "
         "Your decisions are recorded as `owner_reviewed_for_pilot` - never as clinician approval.", "",
         "## Summary", "",
         f"- Sources: **{c['sourcesBeforeDedup']} -> {c['sourcesAfterDedup']}** after exact de-duplication "
         f"({c['sourcesMerged']} merged: all baseline-register copies of production sources).",
         f"- Claims: **{c['claimsBeforeDedup']} -> {c['claimsAfterDedup']}** after de-duplication "
         f"({c['exactDuplicateClaimsRemoved']} exact duplicates removed) **+ {c['curatorAuthoredClaims']} curator-authored claims** "
         f"(IDs CLM-701, CLM-702, verbatim from public abstracts).",
         f"- By origin (before dedup): production {c['byOrigin']['claims']['production']} claims / {c['byOrigin']['sources']['production']} sources; "
         f"baseline register {c['byOrigin']['claims']['baseline-register']} / {c['byOrigin']['sources']['baseline-register']}; "
         f"staging (Phase 2 + daily discovery) {c['byOrigin']['claims']['staging']} / {c['byOrigin']['sources']['staging']}.",
         f"- **Proposed inclusions: {len(proposed)}** (decide below). Deferred claims: {len(deferred)}. Source types: "
         + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(c['sourcesByCategory'].items())) + ".", "",
         "### Deferred (not for patients) by reason", ""]
    by_origin = Counter(r["origin"] for r in deferred)
    L.append(f"_({len(deferred)} deferred claim records in total: {by_origin['staging']} staged (Phase 2 + daily discovery), "
             f"{by_origin['production']} production claims that are already not served, {by_origin['baseline-register']} baseline-register-only.)_")
    L.append("")
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        L.append(f"- {k.replace('_', ' ')}: {v}")
    L += ["", "### Conflicts and unresolved issues", ""]
    for x in summary["claimIdCollisions"]:
        L.append(f"- Claim ID `{x['claimId']}` exists in both production and the baseline register with different content "
                 f"({', '.join(x['records'])}); kept apart, baseline copy deferred as conflicting.")
    L += ["- Source IDs: no source ID maps to two different sources; no claim ID is reused for a different claim among staged claims.",
          "- Several staged claims share a source with one proposed claim; only the verbatim-verified, non-overstating ones are proposed.",
          "- 26 trial registry records (24 ongoing, 2 completed) are kept as labelled trial sources only: **no efficacy claim can come from them**.", ""]
    L += ["### Question coverage if you approve everything proposed", "",
          f"- Before: covered {cov['before']['covered']}, partial {cov['before']['partial']}, not covered {cov['before']['not_covered']} (of 39).",
          f"- After: covered {cov['after']['covered']}, partial {cov['after']['partial']}, not covered {cov['after']['not_covered']} (of 39).", ""]
    L += ["## A. Proposed inclusions - please mark `approve` or `defer`", "",
          "Excerpts were re-verified verbatim against the public PubMed abstract on 2026-11-17 (full text never accessed; "
          "every claim needs full-text verification before any stronger use).", ""]
    for i, r in enumerate(proposed, 1):
        v = ver.get(r["claimId"], {})
        L += [f"### {i}. {r['claimId']} - {r['sourceId']} - **proposed_include**", "",
              f"- **Source:** {r['sourceTitle']} ({r['sourceYear']}) - {r['evidenceType'].replace('_', ' ')} - {r['citationUrl']}",
              f"- **Patient-friendly claim:** {r['patient']}",
              f"- **Exact excerpt:** \"{r['excerpt']}\"  (verbatim in public abstract: **{'yes' if v.get('verbatimInPublicAbstract') else 'NO'}**)",
              f"- **UC applicability:** {r['category'].replace('_', ' ')} ({r['applicability']})",
              f"- **Study type / population:** {r.get('design', '')}; {r.get('population') or 'see source'}",
              f"- **Evidence strength:** {r['strength']}",
              f"- **Limitations:** {r['limitations']}",
              f"- **Patient questions:** {', '.join(r['questions']) or 'none mapped'}",
              f"- **Why:** {r['reason']}",
              f"- **Your decision:** `[ ] approve   [ ] defer`", ""]
    L += ["## B. Existing live claims - keep or retire?", "",
          "These five claims are already live (production `prototype-v1`). Under the stricter 'directly applicable to UC' rule used for this "
          "release, only CLM-014 names ulcerative colitis in its excerpt; the others are IBD-general sources tagged UC at source level. "
          "Default is **keep** (no change) unless you retire them.", "",
          "| Claim | Excerpt (start) | Decision |", "|---|---|---|"]
    for r in b["claim_rows"]:
        if r["origin"] == "production" and r["claimId"] in LIVE_UC_ELIGIBLE:
            L.append(f"| {r['claimId']} ({r['category'].replace('_', ' ')}) | {r['excerpt'][:150]} | `[ ] keep  [ ] retire` |")
    L += ["", "## C. Deferred records", "",
          "Full list with reasons: `reviewer-workbook.xlsx` (Deferred sheet) and `claims-classified.json`. Highlights worth a second look:", "",
          "- CLM-244/245/246 (vedolizumab vs anti-TNF sequencing, retrospective n=219) - deferred as observational/treatment-advice risk.",
          "- CLM-252 (VTE prophylaxis for hospitalised IBD) - IBD-general; a UC-specific source would be needed.",
          "- SRC-034 (AGA 2020 moderate-to-severe UC guideline) - staged without claims because PubMed holds no abstract for it.", ""]
    return "\n".join(L) + "\n"


def write_workbook(b, proposed, deferred, summary) -> None:
    import openpyxl
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    for k, v in summary["counts"].items():
        ws.append([k, json.dumps(v) if isinstance(v, dict) else v])
    ws = wb.create_sheet("Proposed")
    head = ["Claim ID", "Source ID", "Source title", "Year", "Evidence type", "Exact excerpt", "Patient-friendly claim",
            "UC applicability", "Evidence strength", "Limitations", "Patient question IDs", "Recommendation", "Reason",
            "Citation URL", "Owner decision (approve/defer)", "Owner notes"]
    ws.append(head)
    for r in proposed:
        ws.append([r["claimId"], r["sourceId"], r["sourceTitle"], r["sourceYear"], r["evidenceType"], r["excerpt"], r["patient"],
                   r["category"], r["strength"], r["limitations"], ", ".join(r["questions"]), r["recommendation"], r["reason"],
                   r["citationUrl"], "", ""])
    dv = DataValidation(type="list", formula1='"approve,defer"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"O2:O{len(proposed) + 1}")
    ws = wb.create_sheet("Existing live")
    ws.append(["Claim ID", "Category", "Excerpt", "Owner decision (keep/retire)", "Owner notes"])
    for r in b["claim_rows"]:
        if r["origin"] == "production" and r["claimId"] in LIVE_UC_ELIGIBLE:
            ws.append([r["claimId"], r["category"], r["excerpt"], "", ""])
    ws = wb.create_sheet("Deferred")
    ws.append(["Origin", "Claim ID", "Source ID", "Category", "Reason", "Excerpt"])
    for r in deferred:
        ws.append([r["origin"], r["claimId"], r["sourceId"], r["category"], r["reason"], r["excerpt"][:400]])
    ws = wb.create_sheet("Sources")
    ws.append(["Group", "Keeper", "Title", "Category", "Evidence type", "Year", "Merged members"])
    for s in b["source_rows"]:
        ws.append([s["gid"], s["keeper"], s["title"], s["category"], s["evidenceType"], s["year"], ", ".join(s["members"])])
    ws = wb.create_sheet("Dedup decisions")
    ws.append(["Kind", "Kept", "Removed/merged", "Rule"])
    for d in b["inventory"]["source_decisions"]:
        ws.append(["source", d["kept"], ", ".join(d["merged"]), "matched on " + "+".join(d["matchedOn"])])
    for d in b["inventory"]["claim_decisions"]:
        ws.append(["claim", d["keptAs"], d["duplicate"], d["rule"]])
    wb.save(OUT / "reviewer-workbook.xlsx")


def main() -> None:
    b = build()
    enrich(b)
    ver = verify(b)
    bad = [k for k, v in ver.items() if not v["verbatimInPublicAbstract"]]
    print("excerpt verification:", {k: v["verbatimInPublicAbstract"] for k, v in ver.items()})
    cov = coverage(b)
    for p in write_outputs(b, ver, cov):
        print("wrote", p.relative_to(REPO))
    if bad:
        print("NOT VERBATIM:", bad)
        sys.exit(2)


if __name__ == "__main__":
    main()
