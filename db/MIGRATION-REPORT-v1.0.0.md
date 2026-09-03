# Migration report — Prompt v1.0.0 (living)

Redacted, committable. Full detail (with evidence values) is in the gitignored
`db/reports/schema-reconciliation-report.md`.

## Status: BUILT, NOT PROMOTED

| step | state |
|---|---|
| `db/` package + reversible migrations `0001`–`0005` + `.down.sql` | **authored** |
| `schema_infer` (no DB) | **run** → `db/schema/inferred/*` (gitignored) |
| adapters (register / QA overlay / prototype / JSON reconcile) | **run** offline against the real files |
| `validate` (no DB) | **run** |
| `reconcile` (no DB) | **run** → `db/reports/SUMMARY.md` (committed) + full report (gitignored) |
| pre-promotion tests `pytest db/tests -m "not post_promotion"` | **run** — 29 passed, 30 skipped (post_promotion) |
| app: `evidence_backend.py` + `supabase_evidence_source.py` + flag test + `.env.example` | **authored**; flag logic verified standalone |
| `migrate` / `stage` / `promote` / `gate` (need dev Supabase `DATABASE_URL`) | **NOT run** |
| canonical evidence tables | **0 rows** (nothing migrated yet) |
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
- **C** (register vs prototype, shared IDs): **9 material mismatches** → **16 quarantine
  recommendations** (8 per dataset). Entities: `CLM-081/083/085` supporting_excerpt;
  `CLM-083` condition_applicability (ECCO narrowing to crohns-only — the prototype's
  `CLM-083 Correction` sheet); `CLM-097/098/099/100` + `SRC-026` authoritative_url (ESPEN
  PDF URL in the register vs PubMed URL in the prototype/candidate).

Per correction #7 these are **reported and recommended for quarantine — not normalized**.
They need a human decision at the pre-promotion review.

## Next session (on explicit instruction)

1. `pip install -r db/requirements.txt` into `db/.venv` (done this session).
2. Put a **dev** Supabase `DATABASE_URL` + `PROD_HOST_DENYLIST` in `db/.env`.
3. `python -m pipeline.ingest --step migrate` → applies `0001`–`0005` (metadata-only seed).
4. `--step stage`, `--step validate`, `--step reconcile`.
5. **STOP.** Review `db/reports/SUMMARY.md` + `quarantine.record`; resolve the 9 material
   findings; get explicit approval.
6. `--step promote --confirm-promote`, `--step gate`, full `pytest db/tests`.

Production retrieval / Vercel cutover remain a separate decision after the gate passes.
