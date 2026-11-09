"""Reproducible inputs for the Phase-2 inventory.

    python -m phase2.inputs           # (re)generate the committed derived inputs from local sources
    python -m phase2.inputs --verify  # check committed hashes against whatever sources are present

Committed here: a *minimal* question tree (ids, hierarchy, question text, urgency, the tree's prior
coverage annotation - none of the Reddit URLs/engagement data) and a manifest of the 63 zero-claim daily
runs (per-run counters + sha256 of each redacted report). The redacted run reports themselves and the
full 250 KB question tree are NOT committed; their sha256 are recorded so provenance stays checkable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

from phase2 import paths

INPUTS_DIR = paths.REPO / "phase2" / "inputs"
MIN_TREE = INPUTS_DIR / "question-tree.min.json"
DAILY_MANIFEST = INPUTS_DIR / "daily-discovery-manifest.json"
INPUTS_INDEX = INPUTS_DIR / "INPUTS.json"
FULL_TREE = paths.REPO / "uc_39_question_tree.json"

TREE_FIELDS = ("question_id", "level", "parent_question_id", "normalized_question", "topic", "subtopic",
               "urgency_clinical_risk", "current_evidence_package_coverage", "likely_evidence_gap")


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_min_tree() -> dict:
    full = json.loads(FULL_TREE.read_text())
    return {
        "schema": "phase2-question-tree-min/1",
        "derived_from": {"file": "uc_39_question_tree.json", "sha256": sha256(FULL_TREE),
                         "title": full["title"], "created_at": full["created_at"]},
        "note": "Question tree is evidence of patient DEMAND only. `current_evidence_package_coverage` is the "
                "tree's own prior annotation; the Phase-2 evaluation does NOT use it (see MAPPING-DECISION.md).",
        "nodes": [{k: n.get(k) for k in TREE_FIELDS} for n in full["nodes"]],
    }


def build_daily_manifest() -> dict:
    runs = []
    for f in sorted(paths.DAILY_ARTIFACT_DIR.glob("redacted-run-*.json")):
        d = json.loads(f.read_text())
        runs.append({"run_id": d["runId"], "file": f.name, "sha256": sha256(f), "status": d["status"],
                     "started_at": d.get("startedAt"), "counters": d["counters"],
                     "accepted_sources": len(d.get("acceptedSources", [])), "next_topic_id": d.get("nextTopicId")})
    totals = {k: sum(r["counters"].get(k, 0) for r in runs)
              for k in ("queriesConsumed", "recordsScreened", "sourcesAccepted", "claimsExtracted", "pdfsDownloaded")}
    statuses: dict[str, int] = {}
    for r in runs:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    return {"schema": "phase2-daily-discovery-manifest/1", "run_count": len(runs), "by_status": statuses,
            "totals": totals, "zero_claim_runs": sum(1 for r in runs if r["counters"].get("claimsExtracted", 0) == 0),
            "runs": runs}


def source_hashes() -> dict:
    files = {
        "production_package": paths.PRODUCTION_JSON, "baseline_register": paths.BASELINE_REGISTER_XLSX,
        "expansion_claims": paths.EXPANSION_CLAIMS, "expansion_sources": paths.EXPANSION_SOURCES,
        "topic_question_map": paths.TOPIC_QUESTION_MAP,
    }
    out = {k: {"path": str(v.relative_to(paths.REPO)), "sha256": sha256(v)} for k, v in files.items() if v.exists()}
    out["full_question_tree"] = {"path": "uc_39_question_tree.json (not committed)", "sha256": sha256(FULL_TREE)}
    return out


def write() -> None:
    INPUTS_DIR.mkdir(exist_ok=True)
    for path, obj in ((MIN_TREE, build_min_tree()), (DAILY_MANIFEST, build_daily_manifest()),
                      (INPUTS_INDEX, {"schema": "phase2-inputs-index/1", "sources": source_hashes()})):
        path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print("wrote", path.relative_to(paths.REPO))


def verify() -> list[str]:
    problems = []
    idx = json.loads(INPUTS_INDEX.read_text())["sources"]
    for name, meta in idx.items():
        p = paths.REPO / meta["path"].split(" (")[0]
        if p.exists() and sha256(p) != meta["sha256"]:
            problems.append(f"{name}: sha256 differs from committed index")
    man = json.loads(DAILY_MANIFEST.read_text())
    for r in man["runs"]:
        p = paths.DAILY_ARTIFACT_DIR / r["file"]
        if p.exists() and sha256(p) != r["sha256"]:
            problems.append(f"daily run {r['run_id']}: sha256 differs")
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        probs = verify()
        print("\n".join(probs) or "inputs verified")
        sys.exit(1 if probs else 0)
    write()
