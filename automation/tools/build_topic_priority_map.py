#!/usr/bin/env python3
"""One-shot sanitizer: ``uc_39_question_tree.json`` (Reddit-derived, local-only) →
``knowledge/uc-evidence-expansion/topic-priority-map.json`` (committable, Reddit-free).

**Allowlist-by-construction, not a content filter on the source file:**

1. For every node, read *only* the explicitly permitted input fields. Every other field —
   ``supporting_public_urls``, ``paraphrased_demand_rationale``, ``likely_evidence_gap``,
   ``sampling_limitations``, ``user_goal``, ``username``, ``profile_url``, etc. — is ignored
   and dropped, never inspected.
2. Normalise the permitted values into the strict output record.
3. Validate + content-scan **only the resulting output values**.
4. Emit the derivative on success. Abort (no file written) **only** if a permitted *output*
   value is itself polluted (contains a URL / reddit / handle / narrative-length text) or the
   output violates its schema — never merely because a *discarded* input field contained a
   Reddit URL.

The daily runner reads only this derivative for topic prioritisation; it never reads the raw
question-tree file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE = REPO_ROOT / "uc_39_question_tree.json"
DEFAULT_OUTPUT = REPO_ROOT / "knowledge" / "uc-evidence-expansion" / "topic-priority-map.json"

# Step 1: the only input fields this tool ever reads.
_PERMITTED_INPUT_FIELDS = (
    "question_id", "parent_question_id", "normalized_question", "topic",
    "urgency_clinical_risk", "recurrence_band", "current_evidence_package_coverage",
)

_PROHIBITED_OUTPUT_RE = re.compile(
    r"(?i)https?://|www\.|reddit|redd\.it|(?<![A-Za-z])u/[A-Za-z0-9_-]+|/user/[A-Za-z0-9_-]+"
)
_MAX_QUESTION_LEN = 300  # keeps this a "normalized question", not a narrative dump


def _clean_str(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def sanitize_node(node: dict) -> dict:
    """Step 1+2: copy only permitted fields into the strict output shape."""
    return {
        "nodeId": _clean_str(node.get("question_id")),
        "parentId": _clean_str(node.get("parent_question_id")) or None,
        "normalizedQuestion": _clean_str(node.get("normalized_question")),
        "topicId": _clean_str(node.get("topic")),
        "priorityBand": _clean_str(node.get("urgency_clinical_risk")) or "unknown",
        "recurrenceBand": _clean_str(node.get("recurrence_band")) or "unknown",
        "evidenceCoverage": _clean_str(node.get("current_evidence_package_coverage")) or "unknown",
    }


def validate_output_record(rec: dict) -> list[str]:
    """Step 3: scan and schema-check only the sanitized OUTPUT values."""
    errors = []
    required = ("nodeId", "normalizedQuestion", "topicId", "priorityBand", "recurrenceBand", "evidenceCoverage")
    for key in required:
        if not rec.get(key):
            errors.append(f"{rec.get('nodeId','?')}: missing required output field {key!r}")
    if rec.get("normalizedQuestion") and len(rec["normalizedQuestion"]) > _MAX_QUESTION_LEN:
        errors.append(f"{rec['nodeId']}: normalizedQuestion exceeds {_MAX_QUESTION_LEN} chars")
    for key, val in rec.items():
        if not isinstance(val, str):
            continue
        if _PROHIBITED_OUTPUT_RE.search(val):
            errors.append(f"{rec.get('nodeId','?')}: output field {key!r} contains prohibited content")
    return errors


def build(source_path: Path = DEFAULT_SOURCE) -> dict:
    raw = json.loads(source_path.read_text(encoding="utf-8"))
    nodes = raw.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("uc_39_question_tree.json: 'nodes' is not a list")

    records = []
    all_errors: list[str] = []
    for node in nodes:
        rec = sanitize_node(node)
        all_errors.extend(validate_output_record(rec))
        records.append(rec)

    if all_errors:
        raise ValueError("sanitizer output failed validation:\n" + "\n".join(all_errors))

    return {
        "schemaVersion": "uc-evidence-expansion-topic-priority-map-1.0.0",
        "derivedFrom": "uc_39_question_tree.json (local only; not committed)",
        "note": (
            "Sanitized derivative. Contains only node ids, parent relationships, normalized "
            "questions, topic labels, priority/recurrence bands, and evidence-coverage labels. "
            "No URLs, usernames, profile links, post text, or personal narratives."
        ),
        "nodes": records,
    }


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--check", action="store_true", help="build and validate; do not write the file")
    args = p.parse_args(argv)

    if not args.source.exists():
        print(f"[topic-map] source not found: {args.source} (nothing to do)", file=sys.stderr)
        return 0  # not an error: local-only Reddit file may legitimately be absent

    try:
        doc = build(args.source)
    except ValueError as exc:
        print(f"[topic-map] ABORT: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"[topic-map] OK: {len(doc['nodes'])} nodes sanitized (not written; --check)")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[topic-map] wrote {args.output} ({len(doc['nodes'])} nodes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
