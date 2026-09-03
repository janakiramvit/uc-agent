# CHECKPOINT — Schema-compatibility gate & greenfield Supabase migration

**Resume file.** Read this first next session. Do **not** repeat completed work or
expand scope. Wait for the user's explicit "proceed" before running migrations, staging,
Supabase changes, promotion, or any production action.

> **Update 2026-09-03 (build session):** the entire `db/` package + the dormant app
> backend are now BUILT and the offline pipeline (`infer → adapt → validate → reconcile`)
> + pre-promotion tests (`29 passed, 30 skipped`) have run. `db/.venv` is created and deps
> installed. Nothing touched a database. See `db/MIGRATION-REPORT-v1.0.0.md` for results
> (incl. 9 material reconciliation findings awaiting a human decision). **Next real step:
> put a dev Supabase `DATABASE_URL` + `PROD_HOST_DENYLIST` in `db/.env`, then
> `python -m pipeline.ingest --step migrate`.**

---

## 1. Prompt & schema version

- Prompt version: **v1.0.0**
- Canonical schema version: **v1.0.0** (`canonical.schema_version = '1.0.0'`)
- Full approved plan: [`db/PLAN-v1.0.0.md`](./PLAN-v1.0.0.md)
- Checkpoint written: 2026-09-02 ~22:00 local

## 2. Completed planning decisions (do not re-litigate)

1. **Row scope:** two versioned datasets under one canonical schema —
   `baseline-register`@`1.0.0` (full register, ~61 claims / ~26 sources) and
   `prototype-v1`@`1.0.0` (existing 49-claim / 20-source cut, loaded solely to reproduce
   and shadow-test current behaviour).
2. **Source of record:** the two register/prototype **workbooks load**; all JSON and the QA
   workbook are **read-only reconciliation / shadow-test oracles**.
3. **QA workbook is an overlay only.** `ibd-evidence-review-final-remediation-qa.xlsx` never
   populates `canonical.source` or `canonical.claim`; it feeds `staging.claim_qa_raw` +
   `staging.reconciliation_result` only.
4. **DB delivery:** dev Supabase only. Migrations → adapt → stage → validate → reconcile run
   **next session, after explicit user instruction**. Then STOP before promotion.
5. **App reach:** dormant Supabase adapter behind `EVIDENCE_BACKEND` env flag (default
   `file`). `evidence_loader.py`, `vector_retrieval.py`, and the retrieval graph are
   untouched. No production retrieval switch, no Vercel change.
6. **7 binding approval corrections** (see `PLAN-v1.0.0.md` → "Approval corrections"):
   `UNIQUE(code, version)` on `dataset`; reversible `.down.sql` per migration (no
   `DROP SCHEMA CASCADE` as routine rollback); precise roles + RLS (`evidence_reader`
   server-only role, `anon`/`authenticated` denied on staging/quarantine/base/`claim_qa`/
   Storage); no secret/evidence/error leakage outward (`db/reports/**` gitignored except a
   redacted `SUMMARY.md`); canonical evidence tables empty at migrate checkpoint
   (metadata-only seed); Storage + pgvector embeddings deferred to Phase 3+; material
   reconciliation mismatch ⇒ quarantine + report, never silent normalization.
7. **Environment facts:** Python 3.13; `openpyxl` / `pydantic` / `psycopg` / `supabase` CLI
   / `psql` **not installed**; no Docker assumed. Repo is git, on `main`.

## 3. Exact next operation (when the user says "proceed")

> Start of the build session. Nothing below has been done yet.

1. Create the `db/` package skeleton per `PLAN-v1.0.0.md` → Deliverables §1 (files listed in
   §5 of this checkpoint).
2. `python3 -m venv db/.venv && db/.venv/bin/pip install -r db/requirements.txt`
   (`requirements.txt`: `openpyxl`, `psycopg[binary]>=3.1`, `python-dotenv`, `pytest`).
3. Implement + run `python -m pipeline.schema_infer` (no DB) → `db/schema/inferred/*` +
   draft `db/schema/input-schemas.md` / `enumerations.md`.
4. **Pause. Ask the user for the dev Supabase `DATABASE_URL`** (they place it in `db/.env`,
   which is gitignored — do not create or read `.env` yourself beyond what the pipeline
   loader needs at runtime) and for `PROD_HOST_DENYLIST` values.

The first commit of the build session should be the `db/` skeleton + `schema_infer` output
draft, before any DB connection.

## 4. Required input paths

| Purpose | Path | Notes |
|---|---|---|
| Baseline register — **LOAD** source (`baseline-register`) | `/Users/janakirampulipati/ibd-research-review/ibd-evidence-review-final-remediation.xlsx` | `Sources` sheet SRC-001..026 (25 cols); `Claims` sheet CLM-005..100 (24 cols); + audit sheets: `Locator Corrections`, `CLM-097 Remediation`, `Unresolved Claims`, `Removed or Replaced Claims`, `Validation Summary`, `Final Remediation Summary`. Byte-identical mirror also at `knowledge/ibd-research-review/ibd-evidence-review-final-remediation.xlsx` (md5 `f6f0ddc8…` is the `-qa` file; register file differs). A parseable `*.inspect.ndjson` sits beside each `.xlsx`. |
| Baseline QA — **OVERLAY only** | `/Users/janakirampulipati/ibd-research-review/ibd-evidence-review-final-remediation-qa.xlsx` | 8 sheets: `Corrected Claim QA` (10), `CLM-092 Exclusion QA`, `Active Claim Reconciliation`, `Source and Locator QA` (61), `Safety Boundary QA` (61), `Workbook Integrity`, `Report Reconciliation`, `QA Summary`. md5 `f6f0ddc857ebe18ceffe93134051bb2a` (identical to the copy in `knowledge/ibd-research-review/`). |
| Prototype cut — **LOAD** source (`prototype-v1`) | `knowledge/ibd-research-review/ibd-prototype-evidence-review.xlsx` | Sheets: `Included Sources` (20), `Included Claims` (49), `Included With Limitations` (7), `Excluded Claims` (12), `CLM-083 Correction`, `CLM-096-100 Metadata`, `Prototype Coverage`, `Prototype Summary`. |
| Prototype cut — shadow-test **oracle** | `knowledge/ibd-research-review/ibd-prototype-evidence.json` | 49 claims / 20 sources / 12 `excludedClaimIds` / 5 top-level `limitations`. Byte-identical to `apps/ibd-uc-rag-agent-web/api/data/ibd-prototype-evidence.json` (the file the app reads today). 5 UC-eligible claim IDs: **CLM-014, CLM-081, CLM-093, CLM-094, CLM-095**. |
| Read-only reconciliation references | `knowledge/ibd-research-review/extracted-claims/candidate-claims.json` (95, `models.py` schema), `.../prototype-evidence-exclusions.json`, `.../prototype-evidence-summary.json`, `.../run-summary-*.json`, `.../archive/removed-claims/removed-and-replaced-claims.json`, `.../prototype_work/prototype-data.json` | Never loaded into staging/canonical. |
| Authoring schema reference (enum vocab) | `knowledge/ibd-research-review/scripts/models.py` | Pydantic `SourceRecord` / `ClaimRecord` + `Condition` / `DiseaseContext` / `OutcomeType` / `EvidenceLevel` literals. Use as the canonical enum starting vocab; crosswalk everything else. |
| App consumer (retrieval today) | `apps/ibd-uc-rag-agent-web/api/agent_core/evidence_loader.py`, `retrieval.py`, `vector_retrieval.py`, `tools.py` | `EvidencePackage` dataclass + UC substring rule (`"ulcerative_colitis" in conditionApplicability`). |
| **Phase 2 — DEFERRED, do not import** | `knowledge/uc-evidence-expansion/` | `candidate-claims.json` / `sources.json` / `licensing-access-register.json` all `{schemaVersion,runId,generatedAt,…}` wrappers; `state/checkpoint.schema.json` is JSON-Schema. Record in `db/PHASE-2-INPUT.md`. |

### Known schema-drift highlights (fuel for the reconciliation report)
- `conditionApplicability` / `diseaseContext`: **`"a; b; c"` string** in register + prototype
  workbooks and `ibd-prototype-evidence.json`; **list** in `candidate-claims.json` / `models.py`.
- Claim text column: `claim` (`models.py` / `candidate-claims.json`) vs `claimText`
  (prototype workbook + app) vs `Final remediated claim` / `Original claim` / `QA proposed
  claim` (register workbook).
- `evidenceLevel`: **absent per-claim in the register workbook**; free-text vocab in the
  prototype workbook (`clinical guideline`, `EL5`, `guideline/consensus`, `guideline`);
  `models.py` literal set is different again. → stays `NULL` in `canonical.claim` when the
  load source doesn't carry it; QA-observed values live only in `claim_qa`.
- `outcomeType` free values seen not in `models.py`: `obstruction_risk`,
  `perioperative_nutrition_management`.
- Scope: register = 61 active claims (CLM-005..100), 26 sources (SRC-001..026); prototype =
  49 claims / 20 sources / 12 excluded. Prototype IDs are a subset of register IDs (verify
  on resume — this is a reconciliation assertion, not an assumption).
- Baseline QA overall status: `NOT_READY_FOR_HUMAN_APPROVAL`, `humanApprovalsGranted: 0`;
  `QA Summary` F-001 flags 17 ready-tagged claims with row-level metadata defects; failed
  claim `CLM-083`; `CLM-092` correctly excluded.

## 5. Files to create / modify (build session)

**Create — `db/` package** (full tree + per-file intent in `PLAN-v1.0.0.md` → Deliverables §1):
- `db/README.md`, `db/requirements.txt`, `db/.env.example`, `db/.gitignore`,
  `db/PHASE-2-INPUT.md`, `db/LATER-PHASES.md`, `db/MIGRATION-REPORT-v1.0.0.md`
- `db/scripts/dev_teardown.py`
- `db/schema/canonical-schema-v1.0.0.md`, `db/schema/input-schemas.md`,
  `db/schema/enumerations.md`, `db/schema/inferred/` (generated, gitignored)
- `db/supabase/migrations/0001_canonical_schema.sql` (+ `.down.sql`) … through
  `0005_roles_and_rls.sql` (+ `.down.sql`)
- `db/pipeline/__init__.py`, `config.py`, `db.py`, `schema_infer.py`,
  `adapters/{base,register_workbook,qa_workbook,prototype_workbook,json_reconcile}.py`,
  `validate.py`, `promote.py`, `reconcile.py`, `gate.py`, `ingest.py`
- `db/tests/conftest.py` + the pre-promotion tests + `@pytest.mark.post_promotion` tests
- `db/reports/` (generated; only `SUMMARY.md` committable)

**Create — app (dormant, no behaviour change):**
- `apps/ibd-uc-rag-agent-web/api/agent_core/evidence_backend.py`
- `apps/ibd-uc-rag-agent-web/api/agent_core/supabase_evidence_source.py`
- `apps/ibd-uc-rag-agent-web/tests/test_evidence_backend_flag.py`

**Modify — app:**
- `apps/ibd-uc-rag-agent-web/.env.example` — add `EVIDENCE_BACKEND=file`,
  `EVIDENCE_SUPABASE_ENABLED=`, `EVIDENCE_SUPABASE_DB_URL=` (server-side only; never
  `NEXT_PUBLIC_*`).

**Do NOT modify:** `evidence_loader.py`, `retrieval.py`, `vector_retrieval.py`, `tools.py`,
`graph_v2.py`, any evidence JSON/xlsx, `knowledge/**`, `vercel.json`, `next.config.ts`.

**Possibly modify — root `.gitignore`:** add `db/.env`, `db/.venv/`, `db/reports/` (except
`db/reports/SUMMARY.md`), `db/schema/inferred/`. (Root `.gitignore` already ignores `.env`,
`.env.*`, `.venv/`.)

## 6. Supabase setup & credential requirements

- **Target:** a **dev** Supabase project only. Not prod. Not the Vercel-linked environment.
- **User provides** (build session, in `db/.env`, gitignored — assistant never commits it,
  never echoes it, never writes it to a report/artifact):
  - `DATABASE_URL` — a direct Postgres connection string (session pooler / port 5432) with
    privileges to `CREATE SCHEMA`, `CREATE ROLE`, and enable RLS.
  - `PROD_HOST_DENYLIST` — comma-separated hostnames the teardown/migrator must refuse.
- **Assistant creates via migrations:** schemas `canonical` / `staging` / `quarantine`;
  role `evidence_reader` (NOLOGIN or scoped login as the user prefers — decide on resume);
  RLS enabled on all base tables; `REVOKE ALL … FROM PUBLIC, anon, authenticated`.
- **Never:** service-role key handling, `supabase login`, Storage buckets, dashboard
  changes, or anything touching the production project.
- **Connection errors / DSNs** are redacted in all logs and reports.

## 7. Unexecuted migration stages (all pending)

| Stage | Command (build session) | State |
|---|---|---|
| `migrate` | `python -m pipeline.ingest --step migrate` | **not run** — applies `0001`–`0005` to dev Supabase; seeds metadata only (`schema_version`, enums, `dataset` identity); evidence tables stay 0 rows |
| `adapt` + `stage` | `--step adapt` / `--step stage` | **not run** — 3 workbook adapters + JSON reconcile → `staging.*` |
| `validate` | `--step validate` | **not run** — per-row `validation_status`; quarantine candidates |
| `reconcile` | `--step reconcile` | **not run** — `staging.reconciliation_result` + gitignored report + redacted `SUMMARY.md`; material mismatch ⇒ `quarantine.record` |
| **PROMOTE** | `--step promote --confirm-promote` | **not run — BLOCKED pending explicit user approval after review** |
| `gate` | `--step gate` | **not run** — post-promotion |

## 8. Safety & promotion boundaries (hard stops)

- **No promotion** into `canonical.source` / `claim` / `claim_citation` / `claim_qa` /
  `excluded_claim` / `reconciliation_note` / `ingest_provenance` without explicit user
  approval of the reconciliation review.
- Canonical evidence tables must read `count(*) = 0` at the migrate checkpoint; only
  `schema_version` + enum tables + `dataset` identity rows may be populated.
- **No production retrieval switch:** `EVIDENCE_BACKEND` stays `file`;
  `EVIDENCE_SUPABASE_ENABLED` stays unset. `supabase_evidence_source.py` is import-dormant.
- **No Vercel / production config / deployment changes.**
- **No edits to evidence files** (`knowledge/**`, `api/data/**`, any `.xlsx` / evidence JSON).
- **No `uc-evidence-expansion` import** (Phase 2).
- **No secrets committed or echoed**; `db/reports/**` gitignored except redacted `SUMMARY.md`.
- Rollback path = reversible `.down.sql` per migration; `dev_teardown.py` is guarded,
  dev-only, and not the routine path.
- Missing clinical / applicability / evidence-strength / licensing / review values stay
  `NULL` / `unknown` / `pending` — never inferred.

## 9. Tests still to run (none run yet)

**Pre-promotion (run in build session, before asking for promotion approval):**
- `pytest db/tests -m "not post_promotion" -q` — `test_schema_infer`, `test_adapters`,
  `test_validation`, `test_staging_referential_integrity`,
  `test_id_citation_locator_stability`, `test_migration_objects`, `test_views_permissions`.
- `pytest apps/ibd-uc-rag-agent-web/tests -q` — existing suite must stay green + new
  `test_evidence_backend_flag.py`.

**Post-promotion (deferred, `@pytest.mark.post_promotion`):**
- `test_promoted_referential_integrity`, `test_shadow_file_vs_db` (must reproduce
  `ibd-prototype-evidence.json` exactly; `v_uc_eligible_claim` must equal the 5 IDs in §4),
  `test_rollback`, `test_reconciliation_snapshot`.
- `python -m pipeline.gate` → `db/reports/gate-status.json` all `pass`.

## 10. Git branch, commit & working-tree status (at checkpoint time)

- **Branch:** `main` at checkpoint creation; tonight's commit lands on a new branch
  `evidence-db-migration-v1.0.0` (created off `main`).
- **Base commit:** `8445089aa8e31abe7a307c6c94e72d991e211887` ("Finish the full model-powered
  RAG agent").
- **Committed tonight (this branch, planning only):** `db/PLAN-v1.0.0.md`,
  `db/CHECKPOINT-v1.0.0.md`. (Commit ID recorded in the assistant's report message and
  appended here on resume if needed.)
- **Left uncommitted / untracked (pre-existing, NOT ours, do not touch):**
  `M .gitignore`; `?? .uc_reddit_work/`; `?? UC-REDDIT-DEMAND-REPORT.md`;
  `?? knowledge/uc-evidence-expansion/`; `?? uc_39_question_tree.json`;
  `?? uc_39_question_tree.xlsx`; `?? uc_39_question_tree.xlsx.inspect.ndjson`.
- No `.env` created. No dependencies installed. No DB connection made.

## 11. Blockers & unresolved decisions (resolve on resume, before/at the noted step)

1. **Dev Supabase `DATABASE_URL` + `PROD_HOST_DENYLIST`** — needed before `--step migrate`.
   User to provide in `db/.env`.
2. **`evidence_reader` login vs NOLOGIN** — if the Next.js API connects directly, it needs a
   login role + its own secret; if it goes through PostgREST/Supabase client it does not.
   Decide when wiring `supabase_evidence_source.py`. Default assumption: separate login role,
   server-side secret, never in the client bundle.
3. **`dataset` identity rows as "metadata"** — plan treats seeding `baseline-register@1.0.0`
   and `prototype-v1@1.0.0` rows in `0004_seed_metadata.sql` as allowed metadata (no
   source/claim rows). Confirm acceptable, or defer dataset rows to promotion.
4. **Prototype-ID ⊆ register-ID assumption** — must be *verified* by reconciliation, not
   assumed; if any `prototype-v1` claim/source ref is absent from the register, that record
   is quarantined (correction 7) and surfaced for a decision.
5. **`ingest_provenance` in `canonical` vs `staging`** — plan puts the authoritative
   provenance table in `canonical` (populated at promotion) with staging rows carrying
   `src_file/sheet/row`. Confirm no pre-promotion need for a queryable canonical provenance.
6. **Register audit sheets → where** — `Removed or Replaced Claims` / `Unresolved Claims`
   feed `staging.excluded_raw` + reconciliation; confirm they do not need their own canonical
   table in v1.0.0.
7. **openpyxl vs `.inspect.ndjson`** — plan uses real `openpyxl` parsing of the `.xlsx`
   (decision: "workbooks load"). The `.inspect.ndjson` beside each file is a fallback / a
   cross-check for the adapter tests.

---

### Resume procedure

1. Read `db/CHECKPOINT-v1.0.0.md` (this file) and `db/PLAN-v1.0.0.md`.
2. Confirm with the user which step to start at (default: §3 step 1 — build the `db/`
   skeleton + `schema_infer`).
3. Do **not** connect to Supabase, stage, validate, reconcile, promote, run tests, or touch
   the app/Vercel/evidence files until the user explicitly says to.
