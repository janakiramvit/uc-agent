# `db/` — schema-compatibility gate & Supabase migration (Prompt v1.0.0)

Migrates the baseline IBD/UC evidence into a **greenfield Supabase/Postgres** canonical
store behind a strict gate. Two versioned datasets, one canonical schema:

| dataset | load source | role |
|---|---|---|
| `baseline-register@1.0.0` | `ibd-evidence-review-final-remediation.xlsx` (Sources + Claims) | authoritative register |
| `prototype-v1@1.0.0` | `ibd-prototype-evidence-review.xlsx` | reproduce + shadow-test the existing 49/20 cut |

`ibd-evidence-review-final-remediation-qa.xlsx` is a **QA overlay only** (never populates
`source`/`claim`). `ibd-prototype-evidence.json` is the **shadow-test oracle**. All other
JSON in `knowledge/ibd-research-review/` is read-only reconciliation reference.
`knowledge/uc-evidence-expansion/` is **Phase 2** — not imported (see `PHASE-2-INPUT.md`).

## Pipeline

```
raw workbook ─▶ adapter ─▶ staging.* ─▶ validate ─▶ reconcile ─▶ [approval] ─▶ promote ─▶ canonical.* ─▶ v_* views ─▶ app
                                           │            │                                    ▲
                                           └─ quarantine.record ◀── material mismatch ───────┘
```

Run order:

```bash
python3 -m venv db/.venv && db/.venv/bin/pip install -r db/requirements.txt

# no DB needed:
db/.venv/bin/python -m pipeline.ingest --step infer       # db/schema/inferred/*  (gitignored)
db/.venv/bin/python -m pipeline.ingest --step reconcile   # db/reports/SUMMARY.md (+ full report, gitignored)
db/.venv/bin/python -m pytest db/tests -m "not post_promotion"

# needs a DEV Supabase DATABASE_URL + DB_ENVIRONMENT=development + EXPECTED_DEV_HOST in db/.env:
db/.venv/bin/python -m pipeline.ingest --step migrate     # applies 0001–0005 (metadata-only seed)
db/.venv/bin/python -m pipeline.ingest --step stage       # writes staging.* from the adapters
db/.venv/bin/python -m pipeline.ingest --step validate    # crosswalk + quarantine; persists to staging
db/.venv/bin/python -m pipeline.ingest --step reconcile   # persists to staging.reconciliation_result + quarantine.record
db/.venv/bin/python -m pipeline.ingest --step status      # read-only: migrations/roles/RLS/views/metadata/staging/quarantine counts
#  ── STOP. Review db/reports/SUMMARY.md + quarantine.record. Get explicit approval. ──
db/.venv/bin/python -m pipeline.ingest --step promote --confirm-promote
db/.venv/bin/python -m pipeline.ingest --step gate
db/.venv/bin/python -m pytest db/tests                    # full suite incl. post_promotion
```

`--step all` is an **offline preview only** (`infer → adapt → validate → reconcile` in
memory) - it never writes to a database, even when one is configured.

## Safety boundaries (v1.0.0)

- **No promotion** into canonical evidence tables without explicit approval of the
  reconciliation review. Migrations seed metadata only (`schema_version`, enums, `dataset`
  identity); `source`/`claim`/… stay 0 rows.
- **No production retrieval switch.** The app keeps `EVIDENCE_BACKEND=file`;
  `agent_core/supabase_evidence_source.py` is import-dormant. No Vercel change.
- **No secrets outward.** `db/.env` is gitignored; DSNs are redacted in logs; `db/reports/**`
  is gitignored except the redacted `SUMMARY.md`.
- Missing clinical / applicability / evidence-strength / licensing / review values stay
  `NULL` — never inferred. Material reconciliation mismatch ⇒ `quarantine.record`, not
  normalization.

## Rollback

Every `NNNN_x.sql` has a paired `NNNN_x.down.sql`. To reverse:

```bash
db/.venv/bin/python -c "from pipeline.config import load_env; from pipeline.db import *; \
  s=load_env(); c=connect(s); r=MigrationRunner(s); \
  [r.rollback_last(c) for _ in range(5)]; c.commit()"
```

`db/scripts/dev_teardown.py` is a destructive last resort — dev-only, refuses without
`--i-understand-dev-only` + a retyped DB name, and refuses hosts in `PROD_HOST_DENYLIST`.
It is **not** the routine rollback path.

## Access model

- `evidence_reader` — server-only `NOLOGIN` role; `SELECT` on `canonical.v_*` views only.
  The Next.js API connects as a login role that has been `GRANT evidence_reader`.
- `anon` / `authenticated` (Supabase browser roles) — no privileges on
  `canonical` / `staging` / `quarantine`. RLS is `ENABLE`d + `FORCE`d on every base table.
