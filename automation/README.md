# `automation/` — UC daily evidence-discovery runner (Prompt v1.0.0)

A **deterministic, no-LLM** GitHub Actions job that performs one bounded ulcerative-colitis
evidence-discovery increment per day: discover authoritative public UC evidence, dedupe /
normalize it, extract verbatim candidate excerpts, atomically advance a checkpoint, and stage
results. It never approves evidence, never promotes into the live RAG index, never touches
canonical Supabase tables, the app, or Vercel, and never makes a paid model/API call.

## Trusted code vs. mutable state — the one rule that matters

**Executable code (this whole `automation/` tree) lives only on `main`.** All mutable
evidence / checkpoint / journal / lock state lives on the **`automation/uc-evidence-staging`**
branch. The runner is always invoked from the `main` checkout and is handed that branch as a
**separate `git worktree`** via `--state-root=<path>`:

```
git fetch origin +refs/heads/automation/uc-evidence-staging:refs/remotes/origin/automation/uc-evidence-staging
git worktree add --detach "$RUNNER_TEMP/uc-state" refs/remotes/origin/automation/uc-evidence-staging
python -m uc_evidence_discovery --state-root "$RUNNER_TEMP/uc-state" ...
git worktree remove --force "$RUNNER_TEMP/uc-state"; git worktree prune   # from the main checkout
```

`--state-root` is a **data directory only**. The runner asserts it is a real worktree of
`automation/uc-evidence-staging`, that it is **not** on `sys.path`, and that it does not
overlap the trusted-code tree — then never imports, execs, or loads any Python / configuration
/ executable file from it. All evidence/checkpoint/journal/lock reads and writes go through
`--state-root`; the checkpoint **schema**, rule tables, and every Python module load only from
the `main` checkout.

`main` never receives evidence output, checkpoints, or the sanitized topic map — only the
workflow definition, this runner, its tests, and documentation.

## Timing budget (three numbers, not two)

| Budget | Seconds | What happens at the boundary |
|---|---|---|
| GitHub Actions hard timeout | 600 (`timeout-minutes: 10`) | job is killed |
| Runner finalize deadline | 540 | all of QA / checkpoint save / known-good / journal / redacted artifact / commit / push / lock release / worktree removal must be **done** |
| Research soft deadline | 450 | **no new query and no new record screened** after this point |
| Reserved for upload + cleanup | 60 (600 − 540) | the separate `actions/upload-artifact` step + GitHub runner teardown |

## Hard daily limits

10 discovery queries · 30 records screened · 5 newly accepted sources · 20 candidate
claims/excerpts · bounded retries with exponential backoff · per-host rate limiting · a
response-size ceiling. Hitting any limit stops research, keeps a valid continuation
checkpoint, still finishes QA/finalization, and exits `0` with a `partial` status recording the
exact next operation.

## Dispositions

Every screened record gets exactly one of `accepted` / `deferred` / `rejected` / `duplicate`,
each with a non-empty `reason`. `deferred` counts toward the 30-screened limit but not toward
the 5-accepted limit; `duplicate` counts in API-processing metrics only.

## Lock protocol

`<state-root>/state/run.lock` is advisory, never committed, and stale after 20 minutes. A
stale lock is reclaimed **only** after the GitHub Actions API (`actions: read`) confirms its
run is no longer active; if that cannot be determined, the lock is treated as held. The lock is
released in a `finally` block on both success and handled failure.

## Checkpoint

`<state-root>/knowledge/uc-evidence-expansion/state/checkpoint.json` is the sole source of
truth, schema-validated against `checkpoint.schema-v1.1.0.json` (a backward-compatible
superset of `checkpoint.schema.json` — see `state/SCHEMA-MIGRATION-v1.0.0-to-v1.1.0.md`). On
validation failure the runner falls back to
`state/checkpoint.json.known-good` (the one real known-good file); if both are invalid it
raises a safe stop and does **no research**. Prompt-supplied resume hints (topic/search/cursor
/ next ids) are compared against the checkpoint only to report a difference — the checkpoint
always wins. Every write is atomic (temp file + `os.replace`); the known-good copy is only
updated after the primary re-validates.

## What lands where

| Branch | Contents |
|---|---|
| `main` | `.github/workflows/uc-daily-evidence-discovery.yml`, this `automation/` tree (runner + tools + tests + docs), the checkpoint schema + migration doc |
| `automation/uc-evidence-staging` | `knowledge/uc-evidence-expansion/{sources,candidate-claims,question-coverage-map,ingestion-manifest,licensing-access-register,qa-results}.json`, the reports, `reviewer-workbook.xlsx`, `topic-priority-map.json`, `state/checkpoint.json` (+ known-good), `journal/run-journal.ndjson` |

The commit/push step stages an **explicit filename allowlist** (`config.StatePaths.
COMMIT_ALLOWLIST`) — never a broad `git add -A`. `state/run.lock`, `retrieval-cache/`,
`source-files/`, `.venv`, `.env*`, and the raw `uc_39_question_tree.json` are never staged. An
unchanged tree produces **no commit** (never an empty one).

## Reddit boundary

The runner never requests a Reddit host (enforced by `config.DENY_HOST_SUBSTRINGS` +
`apis.http.host_allowed`). It reads topic-prioritization hints only from
`topic-priority-map.json` — a sanitized derivative of the local, uncommitted
`uc_39_question_tree.json` built by `tools/build_topic_priority_map.py`, which reads only a
fixed allowlist of per-node fields (id, parent, normalized question, topic label, urgency
band, recurrence band, evidence-coverage label) and drops every Reddit URL, username, post
body, or narrative field without inspecting its content. See that tool's docstring for the
exact abort conditions.

## Running locally

```bash
python3 -m venv automation/.venv
automation/.venv/bin/pip install -r automation/requirements.txt
automation/.venv/bin/python -m pytest automation/tests -q

# rebuild the sanitized topic map (only if uc_39_question_tree.json exists locally)
automation/.venv/bin/python automation/tools/build_topic_priority_map.py --check

# offline dry run against a throwaway worktree (no network, no commit)
git worktree add --detach /tmp/uc-state-sandbox automation/uc-evidence-staging
automation/.venv/bin/python -m uc_evidence_discovery \
  --state-root /tmp/uc-state-sandbox --dry-run --no-network --soft-deadline-seconds 5
git worktree remove --force /tmp/uc-state-sandbox
```

## Reading the redacted artifact

`automation/artifact/redacted-run-<runId>.{json,md}` — run id/timestamps, safe query labels,
aggregate counts, accepted source ids + titles + DOI/PMID/PMCID/NCT + canonical URLs, QA
pass/fail totals, disposition-reason categories, checkpoint-validation status, and the next
topic id. It never contains an abstract, excerpt, claim text, raw API response, or secret —
`artifact.py` asserts this before writing.

## Estimated Actions usage

One run per day, capped at 10 minutes ⇒ ≤ ~300 minutes/month (well under the free tier for a
public repository, and a small fraction of most private-repo allowances).

## Known limitations

- Deterministic keyword/metadata screening will miss evidence a clinician's reading would
  catch, and will flag some clearly-fine records `requires_human_review` — that is the
  intended conservative bias, not a bug.
- No full text is ever archived in this version; every accepted source is `link_only`, even
  when an open licence is later detected (recorded, but the runner does not fetch files).
- ClinicalTrials.gov / PubMed / Europe PMC availability and rate limits vary; a quiet day is
  expected and acceptable ("lower daily yield is acceptable").
