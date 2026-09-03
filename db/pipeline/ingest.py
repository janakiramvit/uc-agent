"""CLI orchestrator.

    python -m pipeline.ingest --step infer          # schema inference (no DB)
    python -m pipeline.ingest --step adapt          # parse workbooks -> in-memory (no DB)
    python -m pipeline.ingest --step validate       # + enum crosswalk / quarantine calc
    python -m pipeline.ingest --step reconcile      # + write db/reports/*  (no DB needed)
    python -m pipeline.ingest --step migrate        # apply 0001-0005 to DEV Supabase (DB)
    python -m pipeline.ingest --step stage          # write staging.* (DB)
    python -m pipeline.ingest --step promote --confirm-promote   # GATED (DB)
    python -m pipeline.ingest --step gate           # post-promotion checklist (DB)
    python -m pipeline.ingest --step all            # infer..reconcile, then STOP

Without ``--confirm-promote`` the ``promote`` and ``all`` steps refuse to promote and
stop after ``reconcile``. Steps that need a database print a clear message and exit 0
when ``DATABASE_URL`` is absent (nothing is a hard error in planning mode).
"""

from __future__ import annotations

import argparse
import sys

from pipeline import schema_infer
from pipeline.adapters import (
    json_reconcile,
    prototype_workbook,
    qa_workbook,
    register_workbook,
)
from pipeline.config import REPORTS_DIR, input_registry, load_env
from pipeline.reconcile import reconcile, write_full_report, write_summary
from pipeline.validate import validate_dataset

_LOAD = {
    "baseline-register": (register_workbook, "register_workbook"),
    "prototype-v1": (prototype_workbook, "prototype_workbook"),
}


def _adapt_all():
    reg = input_registry()
    results = {}
    for ds, (mod, key) in _LOAD.items():
        results[ds] = mod.load(reg[key].path)
    results["_qa"] = qa_workbook.load(reg["qa_workbook"].path)
    ref_paths = {k: v.path for k, v in reg.items() if v.role in ("reconcile", "oracle")}
    results["_refs"] = json_reconcile.load(ref_paths)
    return results


def _validate_all(adapted):
    reports = {}
    for ds, (_mod, fmt) in _LOAD.items():
        reports[ds] = validate_dataset(adapted[ds].records, dataset=ds, input_format=fmt)
    return reports


def cmd_infer(_args) -> int:
    schema_infer.run()
    return 0


def cmd_adapt(_args) -> int:
    for ds, res in _adapt_all().items():
        print(f"  {ds}: {res.counts() if hasattr(res, 'counts') else res}")
    return 0


def cmd_validate(_args) -> int:
    reps = _validate_all(_adapt_all())
    for ds, rep in reps.items():
        print(f"  {ds}: {rep.by_status}")
        for o in rep.quarantined:
            print(f"     QUARANTINE {o.target} {o.natural_key}: {o.errors}")
    return 0


def cmd_reconcile(_args) -> int:
    adapted = _adapt_all()
    reports = _validate_all(adapted)
    res = reconcile({ds: rep.outcomes for ds, rep in reports.items()},
                    adapted["_refs"].records)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_full_report(res, REPORTS_DIR / "schema-reconciliation-report.md")
    write_summary(res, REPORTS_DIR / "SUMMARY.md")
    print(f"  wrote {REPORTS_DIR/'schema-reconciliation-report.md'} (gitignored)")
    print(f"  wrote {REPORTS_DIR/'SUMMARY.md'} (committable)")
    print(f"  material mismatches: {len(res.material_mismatches())}")
    print(f"  quarantine recommendations: {len(res.quarantine_recommendations)}")
    return 0


def _need_db(settings) -> bool:
    if not settings.has_db:
        print("  DATABASE_URL not set - this step needs a dev Supabase connection in db/.env.")
        print("  Nothing changed. (planning mode)")
        return False
    from pipeline.db import RefusedProdError, require_dev_target

    try:
        ident = require_dev_target(settings)
    except RefusedProdError as exc:
        print(f"  REFUSED: {exc}")
        print("  Nothing changed.")
        return False
    print(f"  dev target confirmed: {ident}")
    return True


def cmd_migrate(_args) -> int:
    settings = load_env()
    if not _need_db(settings):
        return 0
    from pipeline.db import MigrationRunner, connect

    conn = connect(settings)
    try:
        runner = MigrationRunner(settings)
        for name, state in runner.status(conn):
            print(f"    {name}: {state}")
        applied = runner.apply(conn)
        conn.commit()
        print(f"  applied {len(applied)} migration(s)")
    finally:
        conn.close()
    return 0


def cmd_stage(_args) -> int:
    settings = load_env()
    if not _need_db(settings):
        return 0
    print("  stage: writes staging.* from the adapters. Implemented for the DB session.")
    return 0


def cmd_promote(args) -> int:
    if not args.confirm_promote:
        print("  REFUSED: promotion requires --confirm-promote AND prior user approval.")
        print("  Run --step reconcile, review db/reports/SUMMARY.md, then re-run with the flag.")
        return 2
    settings = load_env()
    if not _need_db(settings):
        return 0
    print("  promote: gated DB write. Implemented for the DB session.")
    return 0


def cmd_gate(_args) -> int:
    settings = load_env()
    if not _need_db(settings):
        return 0
    print("  gate: post-promotion checklist. Implemented for the DB session.")
    return 0


def cmd_all(args) -> int:
    for step in (cmd_infer, cmd_adapt, cmd_validate, cmd_reconcile):
        step(args)
    print("\n  STOP: 'all' runs through reconcile only. Promotion needs explicit approval")
    print("  and --step promote --confirm-promote.")
    return 0


_STEPS = {
    "infer": cmd_infer, "adapt": cmd_adapt, "validate": cmd_validate,
    "reconcile": cmd_reconcile, "migrate": cmd_migrate, "stage": cmd_stage,
    "promote": cmd_promote, "gate": cmd_gate, "all": cmd_all,
}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="pipeline.ingest")
    p.add_argument("--step", required=True, choices=sorted(_STEPS))
    p.add_argument("--confirm-promote", action="store_true",
                   help="required (with prior approval) for --step promote / all")
    args = p.parse_args(argv)
    print(f"# pipeline.ingest --step {args.step}")
    return _STEPS[args.step](args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
