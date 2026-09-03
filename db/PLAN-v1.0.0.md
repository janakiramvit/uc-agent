# Plan — Schema-compatibility gate & greenfield Supabase migration (Prompt v1.0.0)

> **Status: APPROVED WITH CORRECTIONS — NOT EXECUTED.** No migrations, no staging, no
> Supabase change in the session that produced this file. That session only: folded in the
> 7 approval corrections, wrote this plan + the checkpoint into the repo, committed the safe
> planning files. Resume only on the user's explicit instruction.

## Context

The IBD/UC RAG app (`apps/ibd-uc-rag-agent-web`) today retrieves evidence from a single
read-only file: `api/data/ibd-prototype-evidence.json` (49 claims / 20 sources). We are
standing up a **greenfield Supabase/Postgres** canonical store so retrieval can eventually
be database-backed — but only behind a strict migration gate.

The baseline evidence lives in `knowledge/ibd-research-review/` and is **not one schema**.
Exploration confirmed at least three incompatible shapes that must be reconciled, never
blindly merged:

| Input | Role in v1.0.0 | Shape highlights |
|---|---|---|
| `ibd-evidence-review-final-remediation.xlsx` — `Sources` (SRC-001..026, 25 cols), `Claims` (CLM-005..100, 24 cols) + 6 audit sheets | **The authoritative baseline source/claim register.** Sole load source for `staging.source_raw` / `staging.claim_raw` of dataset `baseline-register` | remediation-tracking schema: `Original claim` / `QA proposed claim` / `Final remediated claim` columns; **no per-claim `evidenceLevel`**; `Condition applicability` is a `"a; b; c"` string list |
| `ibd-evidence-review-final-remediation-qa.xlsx` — 8 QA sheets (`Source and Locator QA` 61 rows, `Safety Boundary QA` 61 rows, `Corrected Claim QA` 10, `CLM-092 Exclusion QA`, 4 reconciliation sheets) | **QA / reconciliation overlay ONLY** for `baseline-register`. Never populates `source` or `claim`. Feeds `staging.claim_qa_raw` + `staging.reconciliation_result`. The QA workbook alone is not a complete load source and is not treated as one. | per-claim QA-observed `outcomeType` / `studyType` / `confidence` + PASS/FAIL QA outcomes (kept only in the QA overlay, never merged into `claim`); `QA Summary` F-001 flags 17 ready-tagged claims with row-level metadata defects |
| `ibd-prototype-evidence-review.xlsx` + `ibd-prototype-evidence.json` (49/20/12) | **Reproduce + shadow-test only** the existing 49-claim / 20-source prototype dataset and the 5-claim UC retrieval behaviour. Workbook loads `staging.*` for dataset `prototype-v1`; JSON is the shadow-test oracle. Not a new evidence corpus. | retrieval schema: `claimText`, `exactLocator`, `evidenceLevel` (free-text vocab: `clinical guideline`, `EL5`, `guideline/consensus`…), `confidence`, `conditionApplicability` string |
| Other JSON in `knowledge/ibd-research-review/` — `extracted-claims/candidate-claims.json` (95, `models.py` schema), `prototype-evidence-exclusions.json`, `prototype-evidence-summary.json`, `run-summary-*.json`, `archive/removed-claims/removed-and-replaced-claims.json`, `prototype_work/prototype-data.json` | **READ-ONLY reconciliation reference** (never loaded) | list-typed enums, `claim` vs `claimText`, extraction metadata |

`knowledge/uc-evidence-expansion/` (the incremental package) is **explicitly deferred** to
Phase 2 and must not be imported under Prompt v1.0.0. Recorded in `db/PHASE-2-INPUT.md`.

Environment constraints found: Python 3.13, **no** `openpyxl` / `pydantic` / `psycopg` /
`supabase` CLI / `psql` installed, no Docker assumed. Repo is git `main`. `.gitignore`
already ignores `.env` / `.env.*` at any depth and `data/*.db`.

### Decisions locked with the user
1. **Row scope:** two versioned datasets under one canonical schema — `baseline-register`
   (v1.0.0, full ~61 claims / ~26 sources, from the remediation register workbook) and
   `prototype-v1` (the existing 49/20 cut, loaded *solely* to reproduce and shadow-test
   current behaviour).
2. **Source of record:** the two register/prototype workbooks load; all JSON (and the QA
   workbook) reconcile / shadow-test read-only.
3. **DB delivery (next session only):** in a later session, and *only* after the user's
   explicit instruction, the user supplies a **dev Supabase** `DATABASE_URL` in gitignored
   `db/.env`; then migrations → `adapt → stage → validate → reconcile` run against that dev
   DB, then **STOP before any promotion into canonical evidence tables** and request
   approval. Reconciliation output goes to `staging` / report files — **never into canonical
   tables before promotion**. None of this runs in the current session.
4. **App reach:** dormant Supabase adapter behind `EVIDENCE_BACKEND` flag (default `file`)
   + file-vs-DB shadow tests + tested rollback. `evidence_loader.py` behaviour unchanged.
   **No Supabase-backed production retrieval, no Vercel change.**

## Approval corrections (binding, 2026-09-02)

1. **Version-aware dataset identity.** `canonical.dataset` uses `UNIQUE(code, version)` —
   never `code UNIQUE` — so `baseline-register` v1.0.0 and a future v1.1.0 coexist.
2. **No `DROP SCHEMA … CASCADE` as routine rollback on hosted Supabase.** Every
   `NNNN_x.sql` ships a paired `NNNN_x.down.sql` (reversible). A destructive teardown
   exists only as `db/scripts/dev_teardown.py`, dev-only, refusing to run unless
   `--i-understand-dev-only` is passed *and* the operator retypes the target database
   name, and refusing any host that looks like prod (name allowlist in `db/.env`).
3. **Precise roles + RLS.** Browser-facing Supabase roles (`anon`, `authenticated`) get
   **no** access to `staging.*`, `quarantine.*`, `canonical` base tables, `canonical.claim_qa`,
   or Storage. RLS is ON for every base table with no permissive policy for those roles.
   A dedicated server-only role `evidence_reader` (used by the Next.js API via a
   server-side connection string, never shipped to the client) holds `SELECT` on the
   approved `canonical.v_*` views **only**. `REVOKE ALL … FROM PUBLIC` on every new schema
   and object. Delivered as migration `0005_roles_and_rls.sql` (+ `.down.sql`).
4. **No secret / evidence / error leakage outward.** `DATABASE_URL`, Supabase service-role
   keys, raw workbook contents, and DB/connection error text never reach the browser,
   app-visible logs, committed files, or generated artifacts. Pipeline logs redact the DSN
   and never print clinical text at INFO. `db/reports/**` is **gitignored** (it contains
   workbook-derived evidence text); the only committable report is a redacted
   `db/reports/SUMMARY.md` — counts, pass/fail, per-field mismatch tallies, zero evidence
   text, zero secrets. Nothing evidence-bearing is ever returned to the browser.
5. **Canonical evidence tables stay empty at the migrate checkpoint.** Migration may seed
   only metadata: `schema_version`, `enum_domain`/`enum_value`/`enum_crosswalk`, and
   `dataset` identity rows. `source`, `claim`, `claim_citation`, `claim_qa`,
   `excluded_claim`, `reconciliation_note`, `ingest_provenance` remain 0 rows until an
   approved promotion.
6. **Storage & embeddings are out of Phase 1.** Supabase Storage for source PDFs/XML
   (`knowledge/ibd-research-review/sources/`, `extracted-text/`) and pgvector embeddings
   for canonical claims are documented in `db/LATER-PHASES.md` as Phase 3+, not built now.
   `apps/ibd-uc-rag-agent-web/api/agent_core/vector_retrieval.py` is untouched.
7. **Material mismatch ⇒ quarantine, not normalization.** If reconciliation finds any
   material difference in `claim_ref`/`source_ref` IDs, claim text, citation URL,
   locator, condition/disease applicability, limitations, licensing, or review status
   (between register workbook and JSON reference, or between datasets for a shared ID),
   the affected record is written to `quarantine.record` with an explicit reason and
   reported — it is **never** silently coerced. Non-material differences (whitespace /
   case in non-clinical technical fields) may be noted without quarantine.

## Guiding rules (from the prompt, enforced in code)
- Independent schema inference per input, documented, before any import.
- One **versioned** canonical schema (`schema_version = '1.0.0'`).
- A **separate validated adapter per input format**.
- `raw → staging → validate → (approval) → promote → canonical`; app reads **only canonical views**.
- **Quarantine** incompatible records with explicit reasons — never silent-drop, never invent.
- Missing **clinical / applicability / evidence-strength / licensing / review** values stay
  `NULL` / `unknown` / `pending` — never inferred. Only **non-clinical technical** values may
  take documented safe defaults (guarded in code — attempting to default a clinical field raises).
- **Pre-promotion reconciliation results are stored only in `staging.reconciliation_result`
  and generated report files** (`db/reports/…`). `canonical.reconciliation_note` stays empty
  until `promote` snapshots the approved reconciliation into it.
- Field-by-field schema reconciliation report generated before the approval gate.
- Canonical promotion, Supabase-backed production retrieval, and any Vercel cutover do NOT
  happen in this session — they wait for explicit approval after every gate passes
  (validation, referential integrity, ID stability, citation/locator preservation,
  review/applicability preservation, shadow tests, rollback test).

---

## Deliverables

### 1. `db/` — new top-level package

```
db/
  README.md                     architecture, run order, reversible-migration rollback runbook
  requirements.txt              openpyxl, psycopg[binary]>=3.1, python-dotenv, pytest
  .env.example                  DATABASE_URL=, PROMPT_VERSION=1.0.0, PROD_HOST_DENYLIST=
  .gitignore                    .env, .venv/, reports/** (except reports/SUMMARY.md), schema/inferred/**
  PHASE-2-INPUT.md              records knowledge/uc-evidence-expansion/ as deferred Phase-2 input + its known schema family
  LATER-PHASES.md               Phase 3+: Supabase Storage for source PDFs/XML; pgvector embeddings for claims (NOT built in v1.0.0)
  PLAN-v1.0.0.md                the approved revised plan (this file)
  CHECKPOINT-v1.0.0.md          durable continuation checkpoint (resume state)
  scripts/
    dev_teardown.py             DESTRUCTIVE, dev-only. Refuses without --i-understand-dev-only + retyped DB name;
                                refuses hosts matching PROD_HOST_DENYLIST. Not the routine rollback path.
  schema/
    canonical-schema-v1.0.0.md  the versioned canonical schema, field by field, with null-policy per field
    input-schemas.md            the 3+ inferred input schemas + comparison table (fields / types / enums / IDs / relationships / required)
    enumerations.md             canonical enum vocab + crosswalk from each input vocab, with unmapped values called out
    inferred/                   machine output of schema_infer.py (*.json, one per input)
  supabase/migrations/          every NNNN_x.sql has a paired NNNN_x.down.sql (reversible; no DROP SCHEMA CASCADE)
    0001_canonical_schema.sql   schemas canonical/staging/quarantine; schema_version; dataset (UNIQUE(code,version));
                                source; claim; claim_citation; claim_qa; excluded_claim; reconciliation_note;
                                ingest_provenance; enum lookup tables + enum_crosswalk; all FK / CHECK / UNIQUE.
                                REVOKE ALL ON SCHEMA/TABLES FROM PUBLIC.
    0002_staging.sql            staging.* permissive mirrors (source_raw / claim_raw / claim_qa_raw /
                                excluded_raw / reconcile_raw) + staging.reconciliation_result
                                (field-by-field pre-promotion output) + ingest_batch; each row carries
                                src_file/sheet/row, raw jsonb, validation_status, validation_errors jsonb.
                                quarantine.record. REVOKE ALL FROM PUBLIC.
    0003_canonical_views.sql    canonical.v_dataset / v_source / v_claim / v_claim_qa /
                                v_prototype_source / v_prototype_claim / v_prototype_excluded_claim_id /
                                v_prototype_limitation / v_uc_eligible_claim / v_schema_reconciliation.
                                Created empty at migrate time (base tables unpopulated until promotion).
    0004_seed_metadata.sql      seed ONLY metadata: schema_version='1.0.0'; enum_domain/value/crosswalk from
                                schema_infer output; dataset identity rows (baseline-register@1.0.0, prototype-v1).
                                No source/claim rows.
    0005_roles_and_rls.sql      create server-only role evidence_reader; GRANT SELECT on canonical.v_* to it ONLY;
                                enable RLS on all canonical/staging/quarantine base tables with NO policy for
                                anon/authenticated; REVOKE ALL … FROM anon, authenticated, PUBLIC on schemas,
                                base tables, claim_qa, and staging/quarantine.
  pipeline/
    __init__.py
    config.py                   .env load; input-file registry; PROMPT_VERSION / CANONICAL_SCHEMA_VERSION = 1.0.0
    db.py                       psycopg3 connect; run_migrations() tracked in canonical.schema_migration; tx helpers
    schema_infer.py             infer + write schema/inferred/*.{json,md} for every input (fields, types, observed
                                enum domains, required/optional, ID regex, cross-refs). Runs first, no DB needed.
    adapters/
      base.py                   AdapterRecord / AdapterResult; SAFE_DEFAULTS registry (non-clinical only);
                                CLINICAL_FIELDS guard -> raises if a clinical/evidence-strength/applicability/
                                licensing/review field is defaulted
      register_workbook.py      openpyxl parse of ibd-evidence-review-final-remediation.xlsx ->
                                staging.source_raw + staging.claim_raw + staging.excluded_raw (audit sheets);
                                "a; b" -> text[]; provenance per sheet+row
      qa_workbook.py            parse ...-qa.xlsx -> staging.claim_qa_raw (per-dimension rows) +
                                staging.reconcile_raw (Active Claim Reconciliation / Report Reconciliation /
                                Workbook Integrity counts)
      prototype_workbook.py     parse ibd-prototype-evidence-review.xlsx -> staging.source_raw + staging.claim_raw +
                                staging.excluded_raw for dataset prototype-v1
      json_reconcile.py         load ALL knowledge/ibd-research-review/*.json + the QA workbook read-only
                                into an index; writes ONLY staging.reconcile_raw (never canonical)
    validate.py                 staging validation: required-key presence (clinical keys must be PRESENT-as-null,
                                not missing); enum membership via enum_crosswalk (unknown -> quarantine w/ reason);
                                ID regex (^CLM-\d+$ / ^SRC-\d+$); FK resolvability within same dataset;
                                citation/locator non-empty for non-excluded claims; clinical-invention guard.
                                Writes validation_status + validation_errors per staging row.
    promote.py                  **gated on --confirm-promote + approval marker.** One tx per dataset:
                                validated staging -> canonical.*; DB constraints enforce referential integrity;
                                failures -> quarantine.record(reasons[]); dataset-level invariants (counts vs
                                reconcile_raw expected) must hold or the tx aborts. Final step snapshots the
                                approved staging.reconciliation_result into canonical.reconciliation_note.
    reconcile.py                field-by-field: for each (entity, natural key, field) in workbook and/or JSON ->
                                match | mismatch | workbook_only | json_only | null_preserved; assert
                                claim_ref/source_ref set-stability workbook<->json; citation/locator byte-equality
                                (URL, exactLocator, supportingExcerpt); review_status + applicability preserved.
                                **Any MATERIAL mismatch (IDs, claim text, citation, locator, applicability,
                                limitations, licensing, review status) => write the record to quarantine.record
                                with reason; never coerce.** Writes staging.reconciliation_result +
                                db/reports/schema-reconciliation-report.md (gitignored) + redacted
                                db/reports/SUMMARY.md. NEVER canonical before promotion.
    gate.py                     runs the full prompt checklist; writes db/reports/gate-status.{json,md} (gitignored);
                                non-zero exit on any failure; asserts app flag default still = file, RLS on,
                                anon/authenticated denied. Post-promotion step (deferred with promotion).
    ingest.py                   CLI: python -m pipeline.ingest --step {migrate,infer,adapt,stage,validate,
                                reconcile,promote,gate,all}. Without --confirm-promote it refuses `promote`/`all`
                                and stops after `reconcile`.
  reports/                      generated & GITIGNORED (evidence text): schema-reconciliation-report.md,
                                gate-status.{json,md}. Only reports/SUMMARY.md (redacted aggregates) is committable.
  tests/
    conftest.py                 DATABASE_URL fixture; disposable test schemas; teardown; `post_promotion` marker
    # --- run NOW (pre-promotion) ---
    test_schema_infer.py        inferred schemas are NON-identical; expected field/enum deltas present
    test_adapters.py            row counts (26 src / 61 claim / 61 QA / 49 proto claim / 20 proto src / 12 excl);
                                "a; b" -> array; provenance populated; no clinical field defaulted
    test_validation.py          good rows pass; synthetic bad-enum / bad-ID / missing-citation / dangling-ref each
                                quarantined with correct reason; missing clinical value stays NULL (not quarantined)
    test_staging_referential_integrity.py   every staging claim.source_ref resolves within its dataset;
                                dataset isolation holds at staging level
    test_id_citation_locator_stability.py   ID sets stable workbook<->json; citation URL/locator/excerpt preserved
                                byte-for-byte; review_status + applicability_limitations preserved (over staging + reconcile)
    test_migration_objects.py   after migrate: canonical/staging/quarantine schemas + all tables + all v_* views exist
                                (empty); enum lookup + crosswalk seeded; schema_version = '1.0.0'
    test_views_permissions.py   evidence_reader: SELECT on canonical.v_* granted; DENIED on staging.* / quarantine.* /
                                base tables; anon/authenticated denied everywhere sensitive
    test_evidence_backend_flag.py  (app tree) default backend = file; supabase without enable flag raises; file path intact
    # --- DEFERRED: @pytest.mark.post_promotion (need canonical rows) ---
    test_promoted_referential_integrity.py   DB-enforced: no orphan canonical.claim; FK + dataset isolation
    test_shadow_file_vs_db.py    v_prototype_claim/source/excluded/limitation reproduce ibd-prototype-evidence.json
                                exactly (order-insensitive deep compare); v_uc_eligible_claim = same 5 claim IDs the
                                app's rule yields from the file
    test_rollback.py            drop-canonical / backend-revert fallback: app still loads from JSON unchanged;
                                rollback runbook steps asserted
    test_reconciliation_snapshot.py   canonical.reconciliation_note matches the approved staging snapshot; 0 mismatch
                                rows on ID / citation / locator / review / applicability
```

### 2. App — dormant DB backend (no behaviour change)

- `apps/ibd-uc-rag-agent-web/api/agent_core/evidence_backend.py` **(new)** —
  `get_evidence_backend()` reads `EVIDENCE_BACKEND` (default `"file"`). `"supabase"` raises
  `SupabaseBackendNotEnabled` unless `EVIDENCE_SUPABASE_ENABLED=1` (unset by default).
  Dormant by construction; the migration gate must pass before anyone sets that env var
  (documented, not file-coupled — no gitignored report is on the import path).
- `apps/ibd-uc-rag-agent-web/api/agent_core/supabase_evidence_source.py` **(new)** —
  `load_evidence_package_from_db(conn)` builds the existing `EvidencePackage` dataclass
  (from `evidence_loader.py`) out of `canonical.v_prototype_*` views, using a **server-side**
  connection as `evidence_reader`. Imported lazily; unused by default. Never runs in the browser.
- `apps/ibd-uc-rag-agent-web/api/agent_core/evidence_loader.py` — **unchanged** (decision 4).
- `apps/ibd-uc-rag-agent-web/.env.example` — add `EVIDENCE_BACKEND=file`,
  `EVIDENCE_SUPABASE_ENABLED=`, `EVIDENCE_SUPABASE_DB_URL=` (server-side only; comment:
  never expose to the client bundle / `NEXT_PUBLIC_*`; production retrieval stays file-based
  until the migration gate passes).
- `apps/ibd-uc-rag-agent-web/tests/test_evidence_backend_flag.py` **(new)** — default is
  `file`; selecting `supabase` without the enable flag raises; file path unaffected.

### 3. Reports
- `db/reports/schema-reconciliation-report.md` — full field-by-field, per dataset, contains
  workbook-derived evidence text ⇒ **GITIGNORED**, local only. Generated at the `reconcile` step (on resume).
- `db/reports/gate-status.{json,md}` — gate result ⇒ **GITIGNORED**. Generated at the
  post-approval promotion step.
- `db/reports/SUMMARY.md` — **committable, redacted**: row counts, per-field match/mismatch
  tallies, quarantine counts by reason, pass/fail booleans. No evidence text, no secrets, no DSNs.
- `db/MIGRATION-REPORT-v1.0.0.md` — **committable, redacted** living report: what ran, counts,
  quarantine counts, schema-delta list (field names only), "canonical evidence tables = 0 rows —
  promotion pending approval"; updated post-promotion with gate results + "Supabase production
  retrieval NOT enabled, Vercel unchanged".

---

## Canonical schema v1.0.0 (essentials)

- `canonical.schema_version(version PK, applied_at, description)` — seeded `'1.0.0'`.
- `canonical.dataset(dataset_id PK, code, version, source_description, ingest_batch_id,
  ingested_at, status, UNIQUE(code, version))` — rows: `baseline-register`@`1.0.0`,
  `prototype-v1`@`1.0.0`. **Never `code UNIQUE`** — future versions must coexist.
- `canonical.source(id PK, dataset_id FK, source_ref, title, type, status, authors, journal,
  pub_year, authoritative_url, canonical_url, pmid, pmcid, doi, full_text_verification,
  condition_applicability text[], disease_context text[], main_relevant_finding,
  evidence_limitations, access_licensing_note, region_applicability_note, regional_assessment,
  review_status, UNIQUE(dataset_id, source_ref))`.
- `canonical.claim(id PK, dataset_id FK, claim_ref, source_ref, split_from_ref NULL, topic,
  condition_applicability text[], disease_context text[], claim_text, original_claim_text NULL,
  supporting_excerpt, exact_authoritative_passage NULL, precise_locator, authoritative_url,
  evidence_status NULL, final_qa_eligibility NULL, approved_export_eligibility NULL,
  verification_status NULL, remediation_note NULL, limitations NULL, applicability_limitations NULL,
  plain_language_explanation NULL, outcome_type NULL, study_type NULL, evidence_level NULL,
  confidence NULL, review_status, prototype_eligibility_status NULL,
  FK(dataset_id, source_ref) -> source(dataset_id, source_ref), UNIQUE(dataset_id, claim_ref))`
  — every clinical / evidence-strength / applicability / review column is `NULL`-able and left
  `NULL` when the input doesn't carry it.
- `canonical.claim_citation(claim_id FK 1:1, dataset_id, citation_url, exact_locator,
  supporting_excerpt, authoritative_passage NULL)` — the preserve-verbatim fields as their own
  testable table.
- `canonical.claim_qa(dataset_id, claim_ref, qa_dimension, qa_outcome, qa_note, findings jsonb,
  UNIQUE(dataset_id, claim_ref, qa_dimension))` — QA-workbook overlay; never feeds `claim`.
- `canonical.excluded_claim(dataset_id, claim_ref, result, reason, PK(dataset_id, claim_ref))`.
- `canonical.reconciliation_note(dataset_id, entity_type, entity_ref, field, workbook_value,
  json_value, status, detail, snapshot_at)` — **stays empty until an approved promotion**;
  populated only by `promote` from the approved `staging.reconciliation_result`.
- `canonical.ingest_provenance(table_name, row_id, dataset_id, src_file, src_sheet, src_row,
  adapter, adapter_version, transform, ingested_at)`.
- Enums as **lookup tables + FK** (not free CHECK): `canonical.enum_domain`, `canonical.enum_value`,
  `canonical.enum_crosswalk(dimension, input_format, input_value, canonical_value, note)`.
  Unknown input enum value ⇒ no crosswalk row ⇒ validation quarantines it.
- **Access model:** RLS ON for every base/staging/quarantine table; `anon`/`authenticated`
  have no policy and no grants. Server-only role `evidence_reader` has `SELECT` on
  `canonical.v_*` views only. `PUBLIC` revoked everywhere. The Next.js API reaches the DB
  through a server-side connection as `evidence_reader`; the browser never holds a DB URL.

---

## Execution order — ON RESUME ONLY (nothing below runs today)

Today: corrections folded in, checkpoint + plan written to `db/`, safe planning files
committed. Everything below waits for the user's explicit "go".

1. `pip install -r db/requirements.txt` into `db/.venv`.
2. `python -m pipeline.schema_infer` → write `db/schema/inferred/*` (gitignored) + draft
   `db/schema/input-schemas.md` / `enumerations.md`. (no DB)
3. User puts the dev Supabase connection string in `db/.env` (`DATABASE_URL=…`, gitignored)
   and lists prod hostnames in `PROD_HOST_DENYLIST`.
4. `python -m pipeline.ingest --step migrate` → apply `0001`–`0005` (each with its `.down.sql`
   available) to the dev Supabase DB: schemas + empty base tables + views + RLS + roles +
   **metadata-only seed** (`schema_version`, enums, `dataset` identity). Evidence tables = 0 rows.
5. `--step adapt` + `--step stage` → register + prototype workbook adapters, QA overlay
   adapter, JSON reconcile adapter populate `staging.*` + provenance.
6. `--step validate` → per-row `validation_status`; unmapped enums / bad IDs / dangling refs
   flagged as quarantine candidates (not promoted).
7. `--step reconcile` → `staging.reconciliation_result`; **material mismatches → `quarantine.record`**;
   `db/reports/schema-reconciliation-report.md` (gitignored) + redacted `db/reports/SUMMARY.md`.
8. **Run every pre-promotion test:** `pytest db/tests -m "not post_promotion" -q` +
   `pytest apps/ibd-uc-rag-agent-web/tests -q`.
9. **STOP.** Present staging counts, validation summary, quarantine list, reconciliation
   SUMMARY, test results. Wait for explicit approval.
10. **Only after approval:** `--step promote --confirm-promote` → canonical tables +
    `reconciliation_note` snapshot; `--step gate`; full `pytest db/tests -q`. Production
    retrieval / Vercel untouched pending a separate decision.

## Verification

**On resume, pre-promotion:**
- `pytest db/tests -m "not post_promotion" -q` — schema-infer deltas, adapters, validation,
  staging referential integrity, ID/citation/locator stability, migration objects exist,
  RLS on + `anon`/`authenticated` denied on staging/quarantine/base/claim_qa, `evidence_reader`
  can read `canonical.v_*` and nothing else.
- `pytest apps/ibd-uc-rag-agent-web/tests -q` — existing suite still green + new
  `test_evidence_backend_flag.py`.
- Inspect `db/reports/SUMMARY.md`, `staging.reconciliation_result`, `quarantine.record`.
- Confirm `canonical` evidence tables empty (`SELECT count(*)` = 0 for source/claim/…);
  only `schema_version` / enum / `dataset` metadata populated.
- Grep the client bundle / `NEXT_PUBLIC_*` for any DB URL or key — must be absent.

**Deferred to post-approval promotion:**
- `pytest db/tests -q` full run (adds `post_promotion`): DB-enforced referential integrity,
  file-vs-DB shadow parity on `v_prototype_*`, `v_uc_eligible_claim` = the same 5 claim IDs,
  reconciliation snapshot, rollback drill (reversible `.down.sql`, not `DROP SCHEMA`).
- `python -m pipeline.gate` exits 0; `db/reports/gate-status.json` all `pass`; asserts
  `EVIDENCE_BACKEND` default `file` and `EVIDENCE_SUPABASE_ENABLED` unset.

## In scope for v1.0.0 (build on resume)
- The full `db/` package: reversible migrations, the 3 load/overlay adapters + JSON reconcile,
  validation, reconcile, gate, pre-promotion pipeline steps, redacted reports.
- Applying reversible migrations to and staging into the **hosted dev Supabase DB** — *on
  resume, on the user's go*, not today.
- Dormant app backend + `EVIDENCE_BACKEND` flag + RLS/roles + pre-promotion tests.

## Today only
- Fold the 7 corrections into this plan.
- Write `db/PLAN-v1.0.0.md` (this plan) + `db/CHECKPOINT-v1.0.0.md` into the repo.
- Branch off `main`; commit **only** those two markdown files; report paths + commit ID.
- No pip install, no migration, no DB connection, no staging, no `.env`, no credentials committed.

## Out of scope for v1.0.0 (until explicit approval after gates pass)
- **Promotion into canonical evidence tables.**
- Enabling Supabase-backed **production** retrieval / flipping any default / any **Vercel** change.
- Importing `knowledge/uc-evidence-expansion/` (Phase 2 — `db/PHASE-2-INPUT.md`).
- **Supabase Storage for source PDFs/XML, and pgvector embeddings** (Phase 3+ — `db/LATER-PHASES.md`).
- Refactoring `evidence_loader.py`, `vector_retrieval.py`, or the retrieval graph.
