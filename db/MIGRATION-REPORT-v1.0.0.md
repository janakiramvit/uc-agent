# Migration report — Prompt v1.0.0 (living)

Redacted, committable. Full detail (with evidence values) is in the gitignored
`db/reports/schema-reconciliation-report.md`.

## Status: BUILT, MIGRATED TO DEV (0001–0006), NOT PROMOTED

_Refreshed 2026-10-23 to match commit `4b14fb8` (2026-09-04). The table and sections below were
written on 2026-09-03 before the dev run; where they conflict, this block wins._

- Migrations `0001`–`0006` applied to dev (`0006` locks down `canonical.schema_migration`; 22/22 base tables RLS-forced).
- `stage`, `validate`, `reconcile` run and persisted. Comparison C was reassessed as two intentionally versioned datasets: at `4b14fb8` quarantine was 6 records (CLM-081, CLM-083, CLM-085 in both datasets), down from 16; CLM-097–100 and SRC-026 released as `expected_versioned_difference`.
- Commit `d4a472b` judges each dataset independently (baseline checked against its own QA overlay, prototype-v1 against its own oracle): with the QA overlay the recommendation is **1 record — baseline-register CLM-083** (clinical applicability review); without QA, 3 baseline-register only. **The dev DB still holds the older 6 `quarantine.record` rows until `--step reconcile` is re-run.**
- Canonical evidence tables remain **0 rows**; `promote`/`gate` not run.
- Last recorded tests: `pytest db/tests` 50 passed, 35 skipped (post_promotion, gated).

| step | state |
|---|---|
| `db/` package + reversible migrations `0001`–`0006` + `.down.sql` | **authored** |
| `schema_infer` (no DB) | **run** → `db/schema/inferred/*` (gitignored) |
| adapters (register / QA overlay / prototype / JSON reconcile) | **run** offline against the real files |
| `validate` (no DB) | **run** |
| `reconcile` (no DB) | **run** → `db/reports/SUMMARY.md` (committed) + full report (gitignored) |
| pre-promotion tests `pytest db/tests -m "not post_promotion"` | **run** — 29 passed, 30 skipped (post_promotion) |
| app: `evidence_backend.py` + `supabase_evidence_source.py` + flag test + `.env.example` | **authored**; flag logic verified standalone |
| `migrate` (0001–0006) / `stage` / `validate` / `reconcile` on dev | **run** (2026-09-04) |
| `promote` / `gate` | **NOT run** |
| canonical evidence tables | **0 rows** (nothing promoted) |
| Supabase-backed production retrieval / Vercel | **untouched** — `EVIDENCE_BACKEND=file`, flag unset |

## Datasets (planned)

| dataset | load source | staged counts (adapter output) |
|---|---|---|
| `baseline-register@1.0.0` | `ibd-evidence-review-final-remediation.xlsx` | 26 sources, 61 claims, 41 excluded rows |
| `prototype-v1@1.0.0` | `ibd-prototype-evidence-review.xlsx` | 20 sources, 49 claims, 12 excluded (== `excludedClaimIds`) |

QA overlay (`…-qa.xlsx`): 133 `claim_qa` rows across 4 dimensions. Never populates source/claim.

## Validation (offline, both datasets)

- **0 quarantined** by validation.
- `baseline-register`: 137 valid, 22 valid-with-flags — 17 sources `source_type` pending
  (`review`/`study` free-text), 1 source `disease_context` pending (`stricturing_disease`),
  5 claims (CLM-096..100) `condition_applicability` empty → flagged `applicability_missing`
  (canonical NULL, **not inferred**; matches QA F-001).
- `prototype-v1`: 88 valid, 24 valid-with-flags — 14 sources `source_type` pending,
  1 source `disease_context` pending, 9 claims `evidence_level` pending
  (`guideline/consensus` ×5, `review` ×3, `EL5` ×1 — canonical NULL, `evidence_level_raw`
  preserved).

## Reconciliation (offline) — schema deltas found

Field-name-level (see `db/schema/input-schemas.md`): claim-text column differs 3 ways;
register has no per-claim evidence-strength columns; `conditionApplicability` is a string
in the workbooks/prototype-JSON but a list in `candidate-claims.json`; evidence-level
vocabularies diverge (`meta-analysis` vs `meta_analysis`, plus `EL5`, `guideline/consensus`,
`review`).

Comparisons:
- **A** (prototype workbook vs `ibd-prototype-evidence.json`): 826 rows, **0 material
  mismatches** — full parity (needed for the shadow test).
- **B** (register vs `candidate-claims.json`): pre-remediation reference; text/strength
  differences expected; **0 material** on the stability set (IDs / citation URL /
  applicability / review status).
- **C** (register vs prototype, shared IDs): **9 mismatches (4 material after classification)** → **6 quarantine
  records** at `4b14fb8` (was 16); **1** after `d4a472b` (baseline-register CLM-083). Entities: `CLM-081/083/085` supporting_excerpt;
  `CLM-083` condition_applicability (ECCO narrowing to crohns-only — the prototype's
  `CLM-083 Correction` sheet); `CLM-097/098/099/100` + `SRC-026` authoritative_url (ESPEN
  PDF URL in the register vs PubMed URL in the prototype/candidate).

Per correction #7 these are **reported and recommended for quarantine — not normalized**.
They need a human decision at the pre-promotion review.

## Next session (on explicit instruction)

1. `pip install -r db/requirements.txt` into `db/.venv` (done this session).
2. Put a **dev** Supabase `DATABASE_URL` + `PROD_HOST_DENYLIST` in `db/.env`.
3. `python -m pipeline.ingest --step migrate` → applies `0001`–`0006` (metadata-only seed) — **done on dev**.
4. `--step stage`, `--step validate`, `--step reconcile`.
5. **STOP.** Review `db/reports/SUMMARY.md` + `quarantine.record`; resolve the remaining material
   findings; get explicit approval.
6. `--step promote --confirm-promote`, `--step gate`, full `pytest db/tests`.

Production retrieval / Vercel cutover remain a separate decision after the gate passes.
