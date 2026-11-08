"""Map already-possessed usable evidence onto the 39 patient questions. No research, no gap filling.

Leaf (level-3) status, per scope:
    covered      >=1 usable claim that is UC-specific is mapped to the question
    partial      mapped claims exist but none is a usable UC-specific one (only IBD-general usable claims,
                 or only incomplete / conflicting / unverifiable ones)
    not_covered  no mapped claim at all, or only Crohn's-only claims

Non-leaf (level-1/2) status is rolled up from its children (all covered -> covered, none covered and none
partial -> not_covered, otherwise partial); a claim mapped directly to a non-leaf lifts not_covered to partial.

Scopes:
    production_servable   claims actually in the production package (prototype-v1) that are usable and UC-specific
    all_possessed         every retained record from any dataset (production, baseline register, Phase-2 candidates)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from phase2 import paths
from phase2.classify import applicability_class
from phase2.loaders import Record

SCOPES = ("production_servable", "all_possessed")


def load_questions(path: Path = paths.QUESTION_TREE) -> list[dict]:
    nodes = json.loads(path.read_text())["nodes"]
    return [{
        "question_id": n["question_id"], "level": n["level"],
        "parent_question_id": n.get("parent_question_id") or None,
        "question": n["normalized_question"], "urgency_clinical_risk": n.get("urgency_clinical_risk"),
        "prior_tree_coverage": n.get("current_evidence_package_coverage"),
    } for n in nodes]


def assign_question_ids(records: list[Record], rules_path: Path = paths.TOPIC_QUESTION_MAP) -> None:
    cfg = json.loads(rules_path.read_text())
    rules, overrides = cfg["topic_rules"], cfg["claim_overrides"]
    for r in records:
        if r.native_question_ids:
            r.mapped_question_ids, r.mapping_basis = list(r.native_question_ids), "source_provided"
        elif r.claim_id in overrides and r.dataset in (paths.DS_PRODUCTION, paths.DS_BASELINE):
            r.mapped_question_ids, r.mapping_basis = list(overrides[r.claim_id]), "claim_override"
        elif r.topic and r.topic in rules:
            r.mapped_question_ids, r.mapping_basis = list(rules[r.topic]), "topic_rule"
        else:
            r.mapped_question_ids, r.mapping_basis = [], "unmapped"


def _in_scope(row: dict, scope: str) -> bool:
    if scope == "production_servable":
        return row["in_production"]
    return True


def _leaf_status(rows: list[dict]) -> str:
    rows = [r for r in rows if r["applicability_class"] != "crohns_only"]
    if not rows:
        return "not_covered"
    if any(r["status"] == "usable" and r["applicability_class"] == "uc_specific" for r in rows):
        return "covered"
    return "partial"


def compute_coverage(questions: list[dict], manifest_rows: list[dict]) -> dict:
    children = defaultdict(list)
    for q in questions:
        if q["parent_question_id"]:
            children[q["parent_question_id"]].append(q["question_id"])

    result: dict = {"scopes": {}, "questions": {}}
    for scope in SCOPES:
        direct: dict[str, list[dict]] = defaultdict(list)
        for row in manifest_rows:
            if not _in_scope(row, scope):
                continue
            for qid in row["mapped_question_ids"]:
                direct[qid].append(row)

        status: dict[str, str] = {}

        def resolve(qid: str) -> str:
            if qid in status:
                return status[qid]
            kids = children.get(qid, [])
            if not kids:
                s = _leaf_status(direct.get(qid, []))
            else:
                ks = [resolve(k) for k in kids]
                if all(k == "covered" for k in ks):
                    s = "covered"
                elif all(k == "not_covered" for k in ks):
                    s = "partial" if _leaf_status(direct.get(qid, [])) != "not_covered" else "not_covered"
                else:
                    s = "partial"
            status[qid] = s
            return s

        for q in questions:
            resolve(q["question_id"])
            entry = result["questions"].setdefault(q["question_id"], {**q, "scopes": {}})
            entry["scopes"][scope] = {
                "status": status[q["question_id"]],
                "direct_claims": sorted({r["claim_id"] for r in direct.get(q["question_id"], [])
                                         if r["applicability_class"] != "crohns_only"}),
                "crohns_only_not_counted": sorted({r["claim_id"] for r in direct.get(q["question_id"], [])
                                                   if r["applicability_class"] == "crohns_only"}),
            }

        def tally(level: int | None) -> dict:
            qs = [q for q in questions if level is None or q["level"] == level]
            t = {"covered": 0, "partial": 0, "not_covered": 0}
            for q in qs:
                t[status[q["question_id"]]] += 1
            t["total"] = len(qs)
            return t

        result["scopes"][scope] = {"all_39": tally(None), "leaf_level_3": tally(3),
                                   "level_2": tally(2), "level_1": tally(1)}
    return result
