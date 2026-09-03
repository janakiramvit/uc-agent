"""Generate ``supabase/migrations/0004_seed_metadata.sql`` from ``pipeline.enums``.

Keeps the committed seed SQL in lock-step with the Python single-source-of-truth.
``tests/test_enums.py`` runs this and asserts the committed file is byte-identical.

    python -m pipeline.gen_seed_sql            # rewrite the file
    python -m pipeline.gen_seed_sql --check    # exit 1 if the file is stale
"""

from __future__ import annotations

import sys
from pathlib import Path

from pipeline.config import MIGRATIONS_DIR
from pipeline.enums import CANONICAL_ENUMS, emit_seed_rows

TARGET = MIGRATIONS_DIR / "0004_seed_metadata.sql"

_DATASET_ROWS = [
    ("baseline-register", "1.0.0",
     "ibd-evidence-review-final-remediation.xlsx (Sources+Claims register)"),
    ("prototype-v1", "1.0.0",
     "ibd-prototype-evidence-review.xlsx (existing 49/20 prototype cut)"),
]


def _q(s) -> str:
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def render() -> str:
    rows = emit_seed_rows()
    vals = [r for r in rows if r["table"] == "enum_value"]
    xw = [r for r in rows if r["table"] == "enum_crosswalk"]
    out: list[str] = [
        "-- 0004_seed_metadata.sql  (Prompt v1.0.0)",
        "-- Reversible: see 0004_seed_metadata.down.sql",
        "-- METADATA ONLY. No source/claim rows. Generated from pipeline/enums.py by",
        "-- pipeline/gen_seed_sql.py - tests/test_enums.py asserts this file matches enums.py.",
        "",
        "INSERT INTO canonical.schema_version(version, description) VALUES",
        "  ('1.0.0', 'Schema-compatibility gate: baseline-register + prototype-v1 datasets')",
        "ON CONFLICT (version) DO NOTHING;",
        "",
        "INSERT INTO canonical.enum_domain(dimension, description) VALUES",
        ",\n".join(f"  ({_q(d)}, {_q('canonical vocabulary for ' + d)})"
                   for d in sorted(CANONICAL_ENUMS)),
        "ON CONFLICT (dimension) DO NOTHING;",
        "",
        "INSERT INTO canonical.enum_value(dimension, value, ordinal) VALUES",
        ",\n".join(f"  ({_q(r['dimension'])}, {_q(r['value'])}, {r['ordinal']})"
                   for r in vals),
        "ON CONFLICT (dimension, value) DO NOTHING;",
        "",
        "INSERT INTO canonical.enum_crosswalk(dimension, input_format, input_value, "
        "canonical_value, note) VALUES",
        ",\n".join(
            f"  ({_q(r['dimension'])}, {_q(r['input_format'])}, {_q(r['input_value'])}, "
            f"{_q(r['canonical_value'])}, {_q(r['note'])})"
            for r in xw
        ),
        "ON CONFLICT (dimension, input_format, input_value) DO NOTHING;",
        "",
        "-- Version-aware dataset identity rows (metadata; not evidence).",
        "INSERT INTO canonical.dataset(code, version, source_description, status) VALUES",
        ",\n".join(f"  ({_q(c)}, {_q(v)}, {_q(desc)}, 'staged')"
                   for c, v, desc in _DATASET_ROWS),
        "ON CONFLICT (code, version) DO NOTHING;",
        "",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    sql = render()
    if "--check" in argv:
        current = TARGET.read_text() if TARGET.exists() else ""
        if current != sql:
            print(f"STALE: {TARGET} does not match pipeline.enums. Run: python -m pipeline.gen_seed_sql")
            return 1
        print("ok: 0004_seed_metadata.sql is in sync with pipeline.enums")
        return 0
    TARGET.write_text(sql)
    print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
