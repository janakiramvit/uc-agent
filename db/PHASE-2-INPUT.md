# Phase 2 input (DEFERRED — not imported under Prompt v1.0.0)

`knowledge/uc-evidence-expansion/` is the **incremental evidence package**. It is
available but explicitly deferred. The v1.0.0 pipeline never opens it
(`pipeline.config.PHASE_2_DIR` is defined but unused by any adapter).

## Known schema family (for the future adapter)

| file | container | shape |
|---|---|---|
| `candidate-claims.json` | `{schemaVersion, runId, generatedAt, claimsExtractedThisRun, extractionRules, claims[]}` | claim objects — expect **list-typed** `conditionApplicability` / `diseaseContext`, `claim` (not `claimText`), extraction metadata |
| `sources.json` | `{schemaVersion, runId, generatedAt, idReservationNote, sourcesAcceptedThisRun, sources[]}` | source objects; note the ID-reservation scheme |
| `licensing-access-register.json` | `{schemaVersion, runId, generatedAt, policyNotes, entries[]}` | licensing / access status per source — a **licensing** dimension not present in the baseline |
| `question-coverage-map.json`, `ingestion-manifest.json`, `qa-results.json` | objects | run metadata / QA |
| `reviewer-workbook.xlsx` | xlsx | reviewer workbook (a 4th workbook schema) |
| `state/checkpoint.schema.json` | JSON-Schema | the run's checkpoint contract |

## What Phase 2 will need

1. A **separate validated adapter** (`pipeline/adapters/expansion_*`) — do **not** reuse the
   baseline adapters; the schema differs (list enums, licensing register, reviewer workbook).
2. A new dataset row, e.g. `uc-evidence-expansion@1.0.0`, under the **same** canonical
   schema — `UNIQUE(code, version)` already allows it to coexist with the baseline.
3. Its own reconciliation pass and quarantine handling; incremental IDs must not collide
   with reserved baseline IDs (see `idReservationNote`).
4. A `licensing` enum domain + crosswalk, and population of
   `source.access_licensing_note` from `licensing-access-register.json`.

Nothing above is built yet.
