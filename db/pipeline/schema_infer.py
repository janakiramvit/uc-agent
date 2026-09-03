"""Step 1 of the gate: infer and document each input schema **independently**.

For every input file we record: the field list, observed value types, null-rate,
observed enum-ish domains (small distinct string sets), inferred ID patterns, and
cross-file reference columns. Output:

    db/schema/inferred/<key>.json     - machine form (gitignored: may echo values)
    db/schema/inferred/<key>.md       - human form
    db/schema/inferred/_comparison.md - side-by-side field/type/enum/ID/relationship table

No database is touched. Run: ``python -m pipeline.schema_infer``
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.adapters.base import iter_table, now_iso
from pipeline.config import SCHEMA_INFERRED_DIR, input_registry

ID_RE = re.compile(r"^(?P<prefix>[A-Z]{2,4})-(?P<num>\d{1,4})(?P<suffix>[A-Za-z0-9-]*)$")
_ENUM_MAX_DISTINCT = 25
_ENUM_MAX_LEN = 60


@dataclass
class FieldProfile:
    name: str
    present: int = 0
    null: int = 0
    types: Counter = field(default_factory=Counter)
    distinct: set = field(default_factory=set)
    max_len: int = 0
    looks_like_id: bool = False
    looks_multivalue: bool = False
    id_prefixes: Counter = field(default_factory=Counter)

    def observe(self, value: Any) -> None:
        self.present += 1
        if value is None or value == "":
            self.null += 1
            return
        self.types[type(value).__name__] += 1
        s = str(value)
        self.max_len = max(self.max_len, len(s))
        if len(self.distinct) <= _ENUM_MAX_DISTINCT and len(s) <= _ENUM_MAX_LEN:
            self.distinct.add(s)
        if ";" in s or " | " in s:
            self.looks_multivalue = True
        for tok in re.split(r"[;|]", s):
            m = ID_RE.match(tok.strip())
            if m:
                self.looks_like_id = True
                self.id_prefixes[m.group("prefix")] += 1

    def to_dict(self) -> dict:
        rows = self.present or 1
        enum_domain = (
            sorted(self.distinct)
            if 0 < len(self.distinct) <= _ENUM_MAX_DISTINCT
            and self.max_len <= _ENUM_MAX_LEN
            else None
        )
        return {
            "name": self.name,
            "rows_present": self.present,
            "null_rate": round(self.null / rows, 3),
            "types": dict(self.types),
            "max_len": self.max_len,
            "looks_like_id": self.looks_like_id,
            "id_prefixes": dict(self.id_prefixes) or None,
            "looks_multivalue": self.looks_multivalue,
            "enum_domain": enum_domain,
            "required": self.null == 0 and self.present > 0,
        }


def _profile_rows(rows: list[dict]) -> dict[str, dict]:
    profs: dict[str, FieldProfile] = {}
    for row in rows:
        for k, v in row.items():
            profs.setdefault(k, FieldProfile(k)).observe(v)
    return {k: p.to_dict() for k, p in profs.items()}


def _xlsx_sheets(path: Path) -> dict[str, list[dict]]:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    names = list(wb.sheetnames)
    wb.close()
    out: dict[str, list[dict]] = {}
    for name in names:
        out[name] = [row for _, row in iter_table(path, name)]
    return out


def _json_shape(path: Path) -> dict:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return {"container": "array", "len": len(data),
                "record_fields": _profile_rows([r for r in data if isinstance(r, dict)])}
    shape: dict[str, Any] = {"container": "object", "top_level_keys": list(data.keys())}
    for k, v in data.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            shape[f"{k}[]"] = {"len": len(v), "record_fields": _profile_rows(v)}
    return shape


def infer_one(key: str, path: Path) -> dict:
    doc: dict[str, Any] = {"key": key, "file": path.name, "inferred_at": now_iso()}
    if path.suffix == ".xlsx":
        doc["kind"] = "xlsx"
        sheets = _xlsx_sheets(path)
        doc["sheets"] = {
            name: {"row_count": len(rows), "fields": _profile_rows(rows)}
            for name, rows in sheets.items()
        }
    elif path.suffix == ".json":
        doc["kind"] = "json"
        doc["shape"] = _json_shape(path)
    return doc


def _primary_fields(doc: dict) -> dict[str, dict]:
    """Best-effort 'the claim/source record' field set for the comparison table."""
    if doc.get("kind") == "json":
        shape = doc["shape"]
        if shape.get("container") == "array":
            return shape["record_fields"]
        for k in ("claims[]", "sources[]"):
            if k in shape:
                return shape[k]["record_fields"]
        return {}
    for cand in ("Claims", "Included Claims", "Source and Locator QA", "Corrected Claim QA"):
        if cand in doc.get("sheets", {}):
            return doc["sheets"][cand]["fields"]
    # first sheet
    first = next(iter(doc.get("sheets", {}).values()), {})
    return first.get("fields", {})


def write_comparison(docs: dict[str, dict], out: Path) -> None:
    lines = ["# Inferred input schemas - comparison", "",
             f"_Generated {now_iso()} by `pipeline.schema_infer`. Do not edit._", "",
             "One row per **canonical-ish concept**; cells show the raw field name / "
             "observed type / whether multi-valued, per input. Blank = not present.", ""]
    concept_keys = {
        "claim id": ("claimId", "Claim ID"),
        "source id": ("sourceId", "Source ID"),
        "claim text": ("claim", "claimText", "Final remediated claim", "Final claim"),
        "supporting excerpt": ("supportingExcerpt", "Preserved supporting excerpt",
                               "Supporting excerpt"),
        "locator": ("exactLocator", "Precise locator", "Exact locator", "pageNumber"),
        "citation url": ("sourceUrl", "Authoritative source URL"),
        "condition applicability": ("conditionApplicability", "Condition applicability"),
        "disease context": ("diseaseContext", "Disease context"),
        "outcome type": ("outcomeType", "Outcome type"),
        "evidence level": ("evidenceLevel", "Evidence level"),
        "confidence": ("confidence", "Confidence"),
        "limitations": ("limitations", "Limitations"),
        "applicability limitations": ("applicabilityLimitations",),
        "review status": ("reviewStatus", "Review status"),
    }
    keys = list(docs)
    lines.append("| concept | " + " | ".join(keys) + " |")
    lines.append("|" + "---|" * (len(keys) + 1))
    prim = {k: _primary_fields(d) for k, d in docs.items()}
    for concept, aliases in concept_keys.items():
        cells = []
        for k in keys:
            fields = prim[k]
            hit = next((a for a in aliases if a in fields), None)
            if hit is None:
                cells.append("")
                continue
            fp = fields[hit]
            t = "/".join(fp["types"]) or "-"
            mv = " (multi)" if fp["looks_multivalue"] else ""
            req = " *req*" if fp["required"] else ""
            cells.append(f"`{hit}` {t}{mv}{req}")
        lines.append(f"| {concept} | " + " | ".join(cells) + " |")

    lines += ["", "## Enum-ish domains observed (per input, per concept)", ""]
    for concept, aliases in concept_keys.items():
        dom_lines = []
        for k in keys:
            fields = prim[k]
            hit = next((a for a in aliases if a in fields), None)
            if hit and fields[hit].get("enum_domain"):
                dom_lines.append(f"  - **{k}** `{hit}`: {fields[hit]['enum_domain']}")
        if dom_lines:
            lines.append(f"- {concept}:")
            lines.extend(dom_lines)
    lines += ["", "## ID patterns", ""]
    for k, d in docs.items():
        prefixes: Counter = Counter()
        for fp in _primary_fields(d).values():
            prefixes.update(fp.get("id_prefixes") or {})
        lines.append(f"- **{k}**: {dict(prefixes) or 'none detected'}")
    out.write_text("\n".join(lines) + "\n")


def write_markdown(doc: dict, out: Path) -> None:
    lines = [f"# Inferred schema - {doc['key']} (`{doc['file']}`)", "",
             f"_Generated {doc['inferred_at']}. Independent inference - not reconciled._", ""]
    if doc["kind"] == "xlsx":
        for sheet, sd in doc["sheets"].items():
            lines.append(f"## sheet `{sheet}` - {sd['row_count']} data rows")
            lines.append("")
            lines.append("| field | types | null% | max len | id? | multi? | required | enum domain |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for name, fp in sd["fields"].items():
                dom = fp["enum_domain"]
                dom_s = ", ".join(dom) if dom else ""
                if len(dom_s) > 90:
                    dom_s = dom_s[:87] + "..."
                lines.append(
                    f"| {name} | {'/'.join(fp['types']) or '-'} | {fp['null_rate']*100:.0f}% "
                    f"| {fp['max_len']} | {'Y' if fp['looks_like_id'] else ''} "
                    f"| {'Y' if fp['looks_multivalue'] else ''} "
                    f"| {'Y' if fp['required'] else ''} | {dom_s} |"
                )
            lines.append("")
    else:
        lines.append("```json")
        lines.append(json.dumps(doc["shape"], indent=2, default=list)[:8000])
        lines.append("```")
    out.write_text("\n".join(lines) + "\n")


def run(out_dir: Path | None = None) -> dict[str, dict]:
    out_dir = out_dir or SCHEMA_INFERRED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    reg = input_registry()
    docs: dict[str, dict] = {}
    for key, item in reg.items():
        if not item.path.is_file():
            print(f"  SKIP {key}: missing {item.path}")
            continue
        doc = infer_one(key, item.path)
        docs[key] = doc
        (out_dir / f"{key}.json").write_text(json.dumps(doc, indent=2, default=list))
        write_markdown(doc, out_dir / f"{key}.md")
        print(f"  inferred {key} ({doc['kind']}) -> {key}.json / {key}.md")
    write_comparison(docs, out_dir / "_comparison.md")
    print(f"  wrote {out_dir / '_comparison.md'}")
    return docs


if __name__ == "__main__":  # pragma: no cover
    run()
