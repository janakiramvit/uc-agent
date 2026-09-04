# UC Evidence Expansion — staged package

Incremental, human-in-the-loop ulcerative-colitis (UC) evidence-preparation package. **Nothing here is clinically
approved.** All new sources and claims are `pending_clinical_review`. This package does **not** feed the production
app, deployment, Vercel config, or the production RAG / vector index. Every manual increment (below) is started by
hand; a separate, deterministic, no-LLM **daily GitHub Action** (`.github/workflows/uc-daily-evidence-discovery.yml`,
code in `automation/`) additionally runs one bounded increment per day and stages its results here — see "Automated
daily runner" below. Neither path ever approves evidence or promotes anything into the live app.

## Layout

| Path | What it is | In Git? |
|---|---|---|
| `sources.json` | Accepted sources this + prior expansion runs (metadata, licensing, regional applicability, dedup, blank review fields) | yes |
| `candidate-claims.json` | Verbatim-supported candidate claims, each with exact excerpt + locator, mapped to Reddit question nodes | yes |
| `question-coverage-map.json` | Coverage of the `uc_39_question_tree.json` demand nodes; topics selected/deferred; next recommended topic | yes |
| `ingestion-manifest.json` | What was ingested, what is `link_only`, retrieval-cache checksums; `targetIndex = NONE` | yes |
| `licensing-access-register.json` | Per-source licence / full-text / PDF / archival / redistribution status | yes |
| `qa-results.json` | Automated QA checks (not clinical approval) | yes |
| `reviewer-workbook.xlsx` | 9-sheet reviewer workbook (see below) | yes |
| `EVIDENCE-GAPS.md` · `QA-REPORT.md` · `RUN-REPORT.md` · `STORAGE-RECOMMENDATION.md` | Narrative reports | yes |
| `state/checkpoint.schema.json` | Versioned checkpoint JSON schema (draft-07) | yes |
| `state/checkpoint.json` · `state/checkpoint.json.known-good` · `state/run.lock` | Mutable run state + advisory lock | **no (git-ignored)** |
| `journal/run-journal.ndjson` | Append-only run journal | **no (git-ignored)** |
| `retrieval-cache/*.json` | Raw Europe PMC / NCBI API responses used for extraction provenance | **no (git-ignored)** |
| `source-files/<source-id>/<sha256>.<ext>` | Immutable licensed source documents + provenance manifests | **no (git-ignored)** — empty this run |

The checkpoint **schema** is version-controlled; the mutable checkpoint, lock, journal, retrieval cache, and
downloaded source files are not (privacy / mutable-state, consistent with the existing
`knowledge/ibd-research-review/` convention).

## Reviewer workbook sheets

`Run Summary` · `Sources` · `Candidate Claims` · `Question Coverage` · `Conflicts` · `Evidence Gaps` ·
`Licensing and Access` · `QA Results` · `Method and Limitations`.
Every approval / reviewer / decision / signature / review-date field is intentionally blank.

## Running the next increment (manual only)

1. Acquire the advisory lock (`state/run.lock`); refuse to start if another run holds it.
2. Read + validate `state/checkpoint.json` against `state/checkpoint.schema.json`; on corruption, recover from
   `state/checkpoint.json.known-good` + `journal/run-journal.ndjson`.
3. Follow `checkpoint.nextRecommendedOperation` — currently: **topic `T-UCX-03` (acute severe UC), search
   `S-UCX-03-a`, cursor `0`, first new IDs `SRC-035` / `CLM-128`**.
4. Skip every identifier already in `checkpoint.processedSourceIdentifiers` (DOI / PubMed ID / URL / checksum /
   normalized title).
5. Reset only the new run's counters; stop at the first limit; write the checkpoint atomically after every
   processed result page or source; append to the journal; release the lock.

## Automated daily runner (additive)

`.github/workflows/uc-daily-evidence-discovery.yml` on `main` runs
`automation/uc_evidence_discovery/` once a day (`workflow_dispatch` also available). It is
deterministic and makes no LLM/paid-API call. It executes only from the `main` checkout; all
evidence/checkpoint state it reads and writes lives on `automation/uc-evidence-staging` — this
package's files as they appear *there*, not on `main`. It reads patient-topic priorities only
from `topic-priority-map.json` (a sanitized derivative of `uc_39_question_tree.json` with no
URLs, usernames, or narrative text), never the raw Reddit-derived file. See
`automation/README.md` for the full design, and `state/SCHEMA-MIGRATION-v1.0.0-to-v1.1.0.md`
for the (backward-compatible) checkpoint schema it validates against.

## Hard rules for every run

- Reddit (`uc_39_question_tree.json`) is **patient-demand evidence only**, never a medical source.
- Do not convert Crohn's-only or IBD-general findings into UC-specific claims; keep `ibd_general` labelled.
- Do not bypass paywalls, auth, robots rules, or rate limits. Do not assume a reachable PDF is redistributable.
- Do not mark anything `approved`; leave all human-review / clinical-review fields blank.
- Do not promote anything to the production app or vector index. Do not build a scheduler or modify the deployment.

## ID reservations

`SRC-001…SRC-032` and `CLM-001…CLM-114` are reserved by prior packages under `knowledge/ibd-research-review/`
(SRC-001…026 persisted; SRC-027…032 / CLM-101…114 planned-only in `scripts/extend_uc_evidence.py`, never
materialized). This run added `SRC-033`, `SRC-034`, `CLM-115…127`, and adopted the planned canonical id `SRC-028`
for the AGA UC biomarkers guideline (documented in `sources.json`).
