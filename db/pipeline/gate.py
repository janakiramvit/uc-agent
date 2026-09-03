"""The pre-production gate checklist. Writes ``db/reports/gate-status.{json,md}``.

Runs post-promotion. Exit code != 0 if any check fails. Nothing here flips a production
switch - it only reports whether flipping one would be safe.

Not executed in the planning/build session.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.adapters.base import now_iso
from pipeline.config import APP_DIR, REPORTS_DIR


@dataclass
class Check:
    key: str
    passed: bool
    detail: str


@dataclass
class GateStatus:
    checks: list[Check] = field(default_factory=list)

    def add(self, key: str, passed: bool, detail: str) -> None:
        self.checks.append(Check(key, passed, detail))

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_json(self) -> dict:
        return {
            "generated_at": now_iso(),
            "status": "pass" if self.ok else "fail",
            "checks": [{"key": c.key, "passed": c.passed, "detail": c.detail}
                       for c in self.checks],
        }


def _app_default_is_file() -> tuple[bool, str]:
    """The app must default to file-based retrieval; the supabase flag must be unset."""
    env_example = (APP_DIR / ".env.example").read_text() if (APP_DIR / ".env.example").is_file() else ""
    backend = APP_DIR / "api" / "agent_core" / "evidence_backend.py"
    src = backend.read_text() if backend.is_file() else ""
    default_file = 'EVIDENCE_BACKEND' in src and '"file"' in src and 'default' in src.lower()
    flag_unset = "EVIDENCE_SUPABASE_ENABLED=" in env_example and \
        "EVIDENCE_SUPABASE_ENABLED=1" not in env_example
    return (default_file and flag_unset,
            f"evidence_backend defaults to file={default_file}; "
            f"EVIDENCE_SUPABASE_ENABLED unset in .env.example={flag_unset}")


def run_gate(conn, *, oracle_path: Path, shadow_check) -> GateStatus:
    gs = GateStatus()
    cs = conn.execute  # shorthand

    # 1. every staged row is validated (no 'pending')
    (pending,) = cs(
        "SELECT count(*) FROM ("
        "  SELECT validation_status FROM staging.source_raw "
        "  UNION ALL SELECT validation_status FROM staging.claim_raw"
        ") s WHERE validation_status = 'pending' OR validation_status IS NULL"
    ).fetchone()
    gs.add("all_staged_rows_validated", pending == 0, f"{pending} rows still pending")

    # 2. referential integrity - no orphan canonical claims
    (orphans,) = cs(
        "SELECT count(*) FROM canonical.claim c LEFT JOIN canonical.source s "
        "ON s.dataset_id = c.dataset_id AND s.source_ref = c.source_ref "
        "WHERE s.id IS NULL"
    ).fetchone()
    gs.add("referential_integrity", orphans == 0, f"{orphans} orphan claims")

    # 3. source & claim IDs stable (no material ID-set drift recorded)
    (iddrift,) = cs(
        "SELECT count(*) FROM canonical.reconciliation_note "
        "WHERE field = '__id_set__' AND material"
    ).fetchone()
    gs.add("id_stability", iddrift == 0, f"{iddrift} ID-set drift notes")

    # 4. citation + locator preserved (no material mismatch on those fields)
    (cit,) = cs(
        "SELECT count(*) FROM canonical.reconciliation_note "
        "WHERE status = 'mismatch' AND material "
        "AND field IN ('authoritative_url','precise_locator','supporting_excerpt','claim_text')"
    ).fetchone()
    gs.add("citation_locator_preserved", cit == 0,
           f"{cit} unresolved material citation/locator/text mismatches")

    # 5. review + applicability preserved
    (rev,) = cs(
        "SELECT count(*) FROM canonical.reconciliation_note "
        "WHERE status = 'mismatch' AND material "
        "AND field IN ('review_status','condition_applicability','disease_context',"
        "'limitations','applicability_limitations','access_licensing_note')"
    ).fetchone()
    gs.add("review_applicability_preserved", rev == 0,
           f"{rev} unresolved material review/applicability mismatches")

    # 6. file-vs-DB shadow parity (delegated)
    shadow_ok, shadow_detail = shadow_check(conn, oracle_path)
    gs.add("shadow_file_vs_db", shadow_ok, shadow_detail)

    # 7. rollback tested - a marker file the rollback test writes
    marker = REPORTS_DIR / ".rollback-tested"
    gs.add("rollback_tested", marker.is_file(),
           "reports/.rollback-tested present" if marker.is_file()
           else "run tests/test_rollback.py")

    # 8. production retrieval still disabled
    ok, detail = _app_default_is_file()
    gs.add("production_retrieval_disabled", ok, detail)

    return gs


def write_reports(gs: GateStatus, out_dir: Path = REPORTS_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gate-status.json").write_text(json.dumps(gs.to_json(), indent=2))
    lines = [f"# Gate status: {'PASS' if gs.ok else 'FAIL'}", "",
             f"_Generated {now_iso()} by `pipeline.gate`._", "",
             "| check | result | detail |", "|---|---|---|"]
    for c in gs.checks:
        lines.append(f"| {c.key} | {'PASS' if c.passed else 'FAIL'} | {c.detail} |")
    (out_dir / "gate-status.md").write_text("\n".join(lines) + "\n")
