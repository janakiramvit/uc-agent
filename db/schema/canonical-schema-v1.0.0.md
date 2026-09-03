# Canonical schema v1.0.0

Authoritative DDL: `db/supabase/migrations/0001_canonical_schema.sql` (+ `0002` staging,
`0003` views, `0004` metadata seed, `0005` roles/RLS). This file is the readable map.

`schema_version = '1.0.0'`. Schemas: `canonical` (app-facing via views only), `staging`,
`quarantine`.

## Null policy (per the prompt)

| column class | when the input lacks it | example columns |
|---|---|---|
| clinical / applicability / evidence-strength / licensing / review | **stays `NULL`** — never inferred, never defaulted | `condition_applicability`, `disease_context`, `evidence_level`, `confidence`, `limitations`, `applicability_limitations`, `access_licensing_note`, `review_status`, `evidence_status` |
| non-clinical technical | documented safe default OK | `ingested_at`, `adapter_version`, `load_batch_id` |

Every enum-ish column is stored twice: `<col>` = crosswalked canonical value (NULL if
unmapped/pending) and `<col>_raw` = the verbatim input string (always preserved).

## Tables (`canonical`)

| table | key | notes |
|---|---|---|
| `schema_version` | `version` | seeded `1.0.0` |
| `enum_domain` / `enum_value` / `enum_crosswalk` | — | controlled vocab + per-input crosswalk; seeded from `pipeline.enums` |
| `dataset` | `dataset_id`; **`UNIQUE(code, version)`** | `baseline-register@1.0.0`, `prototype-v1@1.0.0`; `status` ∈ staged/promoted/superseded; `package_meta jsonb` |
| `dataset_limitation` | `(dataset_id, ordinal)` | the prototype package's 5 top-level limitation strings |
| `source` | `id`; `UNIQUE(dataset_id, source_ref)` | 25+ descriptive columns; `condition_applicability text[]`, `*_raw` alongside |
| `claim` | `id`; `UNIQUE(dataset_id, claim_ref)`; `FK(dataset_id, source_ref) → source` | `claim_text`/`supporting_excerpt`/`precise_locator` `NOT NULL`; everything clinical NULL-able; carries `original_claim_text`, `qa_proposed_claim_text`, `remediation_note` from the register |
| `claim_citation` | `claim_id` (1:1, `ON DELETE CASCADE`) | the preserve-verbatim fields (`citation_url`, `exact_locator`, `supporting_excerpt`, `authoritative_passage`) as their own testable table |
| `claim_qa` | `UNIQUE(dataset_id, claim_ref, qa_dimension)` | QA-workbook overlay; **no FK to `claim`** (can reference non-promoted claims like CLM-092); QA-observed metadata stays in `findings jsonb`, never merged into `claim` |
| `excluded_claim` | `(dataset_id, claim_ref)` | from the register audit sheets + prototype "Excluded Claims" |
| `reconciliation_note` | `id` | **empty until an approved promotion**; then a snapshot of the findings from `staging.reconciliation_result` |
| `ingest_provenance` | `id` | `(table_name, row_pk)` → src file/sheet/row, adapter, transform |

## Views (`canonical.v_*`) — the ONLY app-facing objects

`v_dataset`, `v_source`, `v_claim` (claim ⋈ claim_citation), `v_claim_qa`,
`v_schema_reconciliation`, and the shadow-shape set:

- `v_prototype_claim` / `v_prototype_source` — emit `claim_json` / `source_json jsonb`
  built from the **`*_raw`** columns, so each object is byte-identical to a record in
  `ibd-prototype-evidence.json`.
- `v_prototype_excluded_claim_id`, `v_prototype_limitation`.
- `v_uc_eligible_claim` — `v_prototype_claim` where `conditionApplicability ILIKE
  '%ulcerative_colitis%'` (the app's exact rule → the 5 IDs CLM-014/081/093/094/095).

## Staging & quarantine

`staging.{source,claim,claim_qa,excluded,reconcile}_raw` — one permissive shape:
`fields`/`provenance`/`raw`/`canonical jsonb`, `validation_status`, `validation_errors`,
`validation_flags`. `staging.reconciliation_result` holds the pre-promotion field-by-field
output. `staging.ingest_batch` groups a run. `quarantine.record(reasons text[], source_step)`.

## Access

RLS `ENABLE` + `FORCE` on every base table (no policy ⇒ deny). `evidence_reader`
(`NOLOGIN`, server-only) has `SELECT` on the `v_*` views and nothing else. `anon` /
`authenticated` have every privilege revoked on all three schemas.
