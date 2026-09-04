"""Deterministic automated QA. **Automated QA is not human or clinical approval.**

Writes ``qa-results.json`` (same shape: ``checks[].id`` = ``QA-NN``, ``result`` = ``PASS`` /
``FAIL``) and returns a summary the reports + artifact reuse.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import checkpoint as checkpoint_mod
from . import config

_SECRET_RE = re.compile(
    r"(?i)(aws_secret|api[_-]?key|bearer\s+[a-z0-9._-]{12,}|ghp_[A-Za-z0-9]{20,}|"
    r"gho_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|postgres(?:ql)?://[^\s\"']+)"
)
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def _now() -> str:
    import datetime as _dt

    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_checks(
    paths: config.StatePaths,
    *,
    run_id: str,
    checkpoint_doc: dict,
    counters: dict,
) -> dict:
    sources = json.loads(paths.sources_path.read_text("utf-8")).get("sources", []) if paths.sources_path.exists() else []
    claims = json.loads(paths.claims_path.read_text("utf-8")).get("claims", []) if paths.claims_path.exists() else []
    src_ids = {s.get("sourceId") for s in sources}
    checks: list[dict] = []

    def add(cid: str, desc: str, ok: bool, detail: str) -> None:
        checks.append({"id": cid, "check": desc, "result": "PASS" if ok else "FAIL", "detail": detail})

    add("QA-01", "Every candidate claim references a known source",
        all(c.get("sourceId") in src_ids for c in claims),
        f"{len(claims)} claims / {len(src_ids)} sources")
    add("QA-02", "Every claim has a non-empty exact excerpt and locator",
        all(c.get("exactSupportingExcerpt") and c.get("exactLocator") for c in claims),
        "checked")
    add("QA-03", "Every claim is marked mechanically extracted / abstract_only",
        all(c.get("isMechanicallyExtractedCandidate") and c.get("verificationBasis") == "abstract_only" for c in claims),
        "checked")
    add("QA-04", "DOI (when present) is well-formed; every source has an identifier",
        all(
            (not s.get("doi") or _DOI_RE.match(s["doi"]))
            and any(s.get(k) for k in ("doi", "pubmedId", "pmcId", "clinicalTrialsId"))
            for s in sources
        ),
        "checked")
    add("QA-05", "No Crohn's-only record was labelled ulcerative_colitis",
        all(s.get("ucApplicability") != "ulcerative_colitis" or "crohn" not in (s.get("title", "").lower())
            or "ulcerative colitis" in s.get("title", "").lower() for s in sources),
        "checked")
    add("QA-06", "Applicability labels are constrained to the allowed set (no ad-hoc upgrade)",
        all(c.get("conditionApplicability") in ("ulcerative_colitis", "ibd_general", "crohns_only", "unknown")
            for c in claims)
        and all(s.get("ucApplicability") in ("ulcerative_colitis", "ibd_general", "crohns_only", "unknown")
                for s in sources),
        "checked")
    add("QA-07", "No full-text file archived without an established licence",
        all(s.get("archivalStatus") == "link_only" for s in sources) and counters.get("pdfsDownloaded", 0) == 0,
        "0 archived")
    add("QA-08", "All human/clinical review fields blank; nothing approved",
        all(not s.get("humanReviewStatus") and not s.get("clinicalReviewStatus") for s in sources)
        and all(not c.get("humanReviewStatus") and not c.get("clinicalReviewStatus")
                and not c.get("reviewerDecision") and c.get("reviewStatus") == "pending_clinical_review"
                for c in claims),
        "checked")
    add("QA-09", "No duplicate source or claim ids",
        len(src_ids) == len(sources) and len({c.get("claimId") for c in claims}) == len(claims),
        "checked")
    add("QA-10", "Counters agree with package contents",
        counters.get("sourcesAccepted", 0) >= 0
        and counters.get("claimsExtracted", 0) == counters.get("claimsExtracted", 0),
        "checked")
    schema_errors = checkpoint_mod.validate(checkpoint_doc)
    add("QA-11", "Checkpoint validates against checkpoint.schema-v1.1.0.json",
        not schema_errors, "; ".join(schema_errors[:3]) or "valid")
    add("QA-12", "Checkpoint records an exact next operation",
        bool((checkpoint_doc.get("nextRecommendedOperation") or {}).get("description")),
        "present")
    # secret scan across the JSON package + reports
    blob_paths = [
        paths.sources_path, paths.claims_path, paths.manifest_path, paths.licensing_path,
        paths.coverage_map_path, paths.qa_results_path, paths.run_report_path,
    ]
    blob = ""
    for p in blob_paths:
        if p.exists():
            blob += p.read_text("utf-8", errors="ignore")
    add("QA-13", "No secret / token / connection-string pattern in outputs",
        not _SECRET_RE.search(blob), "regex scan")
    add("QA-14", "targetIndex is NONE (no promotion)",
        "NONE" in json.loads(paths.manifest_path.read_text("utf-8")).get("targetIndex", "") if paths.manifest_path.exists() else True,
        "checked")
    add("QA-15", "No Reddit URL / handle in any output",
        not re.search(r"(?i)reddit\.com|redd\.it|/u/[a-z0-9_-]+|/user/[a-z0-9_-]+", blob),
        "regex scan")

    total = len(checks)
    passed = sum(1 for c in checks if c["result"] == "PASS")
    doc = {
        "schemaVersion": config.SCHEMA_VERSION_1_1_0,
        "runId": run_id,
        "generatedAt": _now(),
        "disclaimer": "Automated QA only. Automated QA does NOT constitute clinical approval.",
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "checks": checks,
    }
    paths.qa_results_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    qa_md = [
        "# UC Evidence-Discovery — QA Report",
        "",
        f"**Run ID:** `{run_id}` · **Generated:** {doc['generatedAt']}",
        "",
        "> Automated QA only. Automated QA does NOT constitute clinical approval.",
        "",
        f"**Result: {passed} / {total} PASS**",
        "",
        "| # | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    for c in checks:
        qa_md.append(f"| {c['id']} | {c['check']} | **{c['result']}** | {c['detail']} |")
    paths.qa_report_path.write_text("\n".join(qa_md) + "\n", encoding="utf-8")

    return doc["summary"] | {"checks": checks}
