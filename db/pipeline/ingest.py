"""CLI orchestrator.

    python -m pipeline.ingest --step infer          # schema inference (no DB)
    python -m pipeline.ingest --step adapt          # parse workbooks -> in-memory (no DB)
    python -m pipeline.ingest --step migrate        # apply 0001-0005 to DEV Supabase (DB)
    python -m pipeline.ingest --step stage          # write staging.* from the adapters (DB)
    python -m pipeline.ingest --step validate       # crosswalk + quarantine; persists to staging when DB configured
    python -m pipeline.ingest --step reconcile      # writes db/reports/*; persists to staging.reconciliation_result + quarantine.record when DB configured
    python -m pipeline.ingest --step status         # read-only: migrations/schemas/roles/RLS/views/metadata/staging/quarantine/reconciliation counts (DB)
    python -m pipeline.ingest --step promote --confirm-promote   # GATED (DB)
    python -m pipeline.ingest --step gate           # post-promotion checklist (DB)
    python -m pipeline.ingest --step all            # infer..reconcile in OFFLINE PREVIEW mode only, then STOP

``all`` never touches a database, even if DATABASE_URL is configured - it is the offline
preview path. For a real run use the individual steps in order:
migrate -> stage -> validate -> reconcile -> status, then pytest, then (only with explicit
approval) promote --confirm-promote -> gate.

Without ``--confirm-promote`` the ``promote`` step refuses to promote and tells you to
review ``db/reports/SUMMARY.md`` first. Steps that need a database print a clear message
and exit 0 when ``DATABASE_URL`` is absent, or refuse with a sanitized reason when the
target cannot be positively identified as development (nothing is a hard error in
planning mode; connection failures never surface host/user/password).
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


def cmd_validate(args) -> int:
    settings = load_env()
    if not settings.has_db:
        reps = _validate_all(_adapt_all())
        for ds, rep in reps.items():
            print(f"  (offline preview) {ds}: {rep.by_status}")
            for o in rep.quarantined:
                print(f"     QUARANTINE {o.target} {o.natural_key}: {o.errors}")
        return 0
    if not _need_db(settings):
        return 0
    from pipeline import stage
    from pipeline.db import ConnectionFailedError, connect

    try:
        conn = connect(settings)
    except ConnectionFailedError as exc:
        print(f"  REFUSED/FAILED: {exc}")
        return 1
    try:
        batch_id = stage.latest_batch(conn)
        reps = _validate_all(_adapt_all())
        for ds, rep in reps.items():
            summary = stage.persist_validation(conn, batch_id, ds, rep)
            print(f"  {ds}: {rep.by_status}  (staging rows updated={summary['updated']}, "
                 f"quarantined={summary['quarantined']})")
        conn.commit()
    finally:
        conn.close()
    return 0


def cmd_reconcile(args) -> int:
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

    settings = load_env()
    if not settings.has_db:
        return 0
    if not _need_db(settings):
        return 0
    from pipeline import stage
    from pipeline.db import ConnectionFailedError, connect

    try:
        conn = connect(settings)
    except ConnectionFailedError as exc:
        print(f"  REFUSED/FAILED: {exc}")
        return 1
    try:
        batch_id = stage.latest_batch(conn)
        db_summary = stage.persist_reconciliation(conn, batch_id, res)
        conn.commit()
        print(f"  DB: {db_summary}")
    finally:
        conn.close()
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
    from pipeline.db import ConnectionFailedError, MigrationRunner, connect

    try:
        conn = connect(settings)
    except ConnectionFailedError as exc:
        print(f"  REFUSED/FAILED: {exc}")
        return 1
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
    from pipeline import stage
    from pipeline.db import ConnectionFailedError, connect

    try:
        conn = connect(settings)
    except ConnectionFailedError as exc:
        print(f"  REFUSED/FAILED: {exc}")
        return 1
    try:
        adapted = _adapt_all()
        batch_id = stage.new_batch(conn)
        totals: dict[str, int] = {}
        for key, res in adapted.items():
            counts = stage.stage_records(conn, batch_id, res.records)
            label = "baseline-register" if key == "baseline-register" else \
                    "prototype-v1" if key == "prototype-v1" else \
                    ("qa-overlay" if key == "_qa" else "json-reconcile-refs")
            print(f"  {label}: {counts}")
            for k, v in counts.items():
                totals[k] = totals.get(k, 0) + v
        conn.commit()
        print(f"  batch_id={batch_id}  totals={totals}")
    finally:
        conn.close()
    return 0


def cmd_status(_args) -> int:
    settings = load_env()
    if not _need_db(settings):
        return 0
    from pipeline import stage
    from pipeline.db import ConnectionFailedError, MigrationRunner, connect

    try:
        conn = connect(settings)
    except ConnectionFailedError as exc:
        print(f"  REFUSED/FAILED: {exc}")
        return 1
    try:
        print("  -- migrations --")
        for name, state in MigrationRunner(settings).status(conn):
            print(f"    {name}: {state}")

        print("  -- schemas --")
        names = {r[0] for r in conn.execute("SELECT nspname FROM pg_namespace").fetchall()}
        for s in ("canonical", "staging", "quarantine"):
            print(f"    {s}: {'present' if s in names else 'MISSING'}")

        print("  -- roles / grants --")
        role = conn.execute(
            "SELECT rolname FROM pg_roles WHERE rolname='evidence_reader'").fetchone()
        print(f"    evidence_reader role: {'present' if role else 'MISSING'}")
        browser = conn.execute(
            "SELECT count(*) FROM information_schema.role_table_grants "
            "WHERE table_schema IN ('canonical','staging','quarantine') "
            "AND grantee IN ('anon','authenticated')").fetchone()
        print(f"    anon/authenticated grants on canonical/staging/quarantine: {browser[0]} "
             f"(must be 0)")
        reader_views = conn.execute(
            "SELECT count(*) FROM information_schema.role_table_grants "
            "WHERE table_schema='canonical' AND grantee='evidence_reader' "
            "AND table_name LIKE 'v\\_%' ESCAPE '\\'").fetchone()
        print(f"    evidence_reader grants on canonical.v_*: {reader_views[0]}")
        reader_base = conn.execute(
            "SELECT count(*) FROM information_schema.role_table_grants "
            "WHERE table_schema IN ('canonical','staging','quarantine') "
            "AND grantee='evidence_reader' AND table_name NOT LIKE 'v\\_%' ESCAPE '\\'"
        ).fetchone()
        print(f"    evidence_reader grants on non-view objects: {reader_base[0]} (must be 0)")

        print("  -- views --")
        views = {r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.views WHERE table_schema='canonical'"
        ).fetchall()}
        print(f"    {len(views)} views present: {sorted(views)}")

        print("  -- RLS --")
        rls_rows = conn.execute(
            "SELECT n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity "
            "FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname IN ('canonical','staging','quarantine') AND c.relkind='r'"
        ).fetchall()
        not_forced = [f"{n}.{t}" for n, t, en, fo in rls_rows if not (en and fo)]
        print(f"    {len(rls_rows)} base tables checked; not RLS-forced: {not_forced or 'none'}")

        print("  -- metadata seed --")
        (sv,) = conn.execute("SELECT count(*) FROM canonical.schema_version").fetchone()
        (ev,) = conn.execute("SELECT count(*) FROM canonical.enum_value").fetchone()
        (ex,) = conn.execute("SELECT count(*) FROM canonical.enum_crosswalk").fetchone()
        ds_rows = conn.execute(
            "SELECT code, version, status FROM canonical.dataset ORDER BY code").fetchall()
        print(f"    schema_version rows={sv}, enum_value={ev}, enum_crosswalk={ex}")
        print(f"    dataset rows: {ds_rows}")

        print("  -- canonical evidence tables (MUST be 0) --")
        for t in ("source", "claim", "claim_citation", "claim_qa", "excluded_claim",
                 "reconciliation_note", "ingest_provenance"):
            (n,) = conn.execute(f"SELECT count(*) FROM canonical.{t}").fetchone()
            print(f"    canonical.{t}: {n}")

        try:
            batch_id = stage.latest_batch(conn)
            print(f"  -- staging (batch {batch_id}) --")
            counts = stage.read_counts(conn, batch_id)
            print(f"    by dataset/table: {counts.by_target}  (total={counts.total})")
            print(f"    validation status by table: {stage.read_validation_summary(conn, batch_id)}")
            print("    quarantine (step, dataset, entity_type, count, ids):")
            for row in stage.read_quarantine_summary(conn, batch_id):
                print(f"      {row}")
            recon = conn.execute(
                "SELECT comparison, status, count(*) FROM staging.reconciliation_result "
                "WHERE batch_id=%s GROUP BY comparison, status ORDER BY comparison, status",
                (batch_id,)).fetchall()
            print(f"    reconciliation_result tally: {recon}")
        except RuntimeError as exc:
            print(f"  -- staging: {exc}")
    finally:
        conn.rollback()
        conn.close()
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


def cmd_all(_args) -> int:
    """Offline preview only - never touches a database, even if one is configured."""
    cmd_infer(_args)
    cmd_adapt(_args)
    reps = _validate_all(_adapt_all())
    for ds, rep in reps.items():
        print(f"  (offline preview) {ds}: {rep.by_status}")
        for o in rep.quarantined:
            print(f"     QUARANTINE {o.target} {o.natural_key}: {o.errors}")
    adapted = _adapt_all()
    res = reconcile({ds: rep.outcomes for ds, rep in reps.items()}, adapted["_refs"].records)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_full_report(res, REPORTS_DIR / "schema-reconciliation-report.md")
    write_summary(res, REPORTS_DIR / "SUMMARY.md")
    print(f"  wrote {REPORTS_DIR/'schema-reconciliation-report.md'} (gitignored)")
    print(f"  wrote {REPORTS_DIR/'SUMMARY.md'} (committable)")
    print(f"  material mismatches: {len(res.material_mismatches())}")
    print(f"  quarantine recommendations: {len(res.quarantine_recommendations)}")
    print("\n  STOP: 'all' is offline preview only (infer..reconcile, no DB writes even "
         "if DATABASE_URL is set). For a real run: migrate -> stage -> validate -> "
         "reconcile -> status, then --step promote --confirm-promote only with approval.")
    return 0


_STEPS = {
    "infer": cmd_infer, "adapt": cmd_adapt, "validate": cmd_validate,
    "reconcile": cmd_reconcile, "migrate": cmd_migrate, "stage": cmd_stage,
    "status": cmd_status, "promote": cmd_promote, "gate": cmd_gate, "all": cmd_all,
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
