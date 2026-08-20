# Completion report -- ibd-uc-rag-prototype

## What was built

A local, non-production prototype at `/home/claude/ibd-uc-rag-prototype`
that answers ulcerative-colitis-only questions from a fixed, reviewed
evidence package, using:

- **LangChain** -- each UC-eligible claim wrapped as a `Document` with all
  original claim fields preserved as metadata (`app/evidence_loader.py`);
  a `BM25Retriever`-based retrieval layer with metadata filtering applied
  before ranking (`app/retrieval.py`).
- **LangGraph** -- an explicit `StateGraph` implementing the required
  8-node workflow (`receive_query` -> `classify_topic` ->
  `retrieve_uc_claims` -> `check_source_and_applicability` ->
  `check_safety_boundaries` -> [conditional: `refuse` or `compose_answer`]
  -> `attach_citations` -> [conditional: `fallback_if_unsupported` or end])
  (`app/workflow.py`).
- **Streamlit** -- local UI with question input, topic filter, a
  locked/disabled disease filter fixed to "ulcerative_colitis", answer
  panel, per-claim citation cards, limitations/safety panel, distinct
  "no sufficient evidence" state styling, and a persistent
  informational-prototype-only banner plus pending-human-review notice
  (`streamlit_app.py`).
- **Safety rules module** (`app/safety_rules.py`) -- keyword/pattern-based
  guardrails for diagnosis requests, flare prediction, medication changes,
  individualized diet plans, symptom-vs-inflammation equivalence claims,
  and Crohn's-to-UC evidence misapplication.
- **pytest suite** (`tests/test_prototype.py`, 35 tests) covering every
  item in the spec's test list.

No LLM/model provider call is implemented in this build. `ENABLE_MODEL_CALLS`
and `MODEL_PROVIDER` are documented in `.env.example`, default to
disabled, and no code path performs a network or model call regardless of
their value -- retrieval and answer composition are fully deterministic,
local BM25 + template-based text assembly.

## Evidence filtering result (verified against the live data)

- **5** UC-eligible claims (substring filter on `conditionApplicability`
  containing `"ulcerative_colitis"`): CLM-014 (fibre), CLM-081
  (core_condition_knowledge), CLM-093 (fruit_vegetables), CLM-094 (fibre),
  CLM-095 (alcohol).
- **15** Crohn's-only claims (`conditionApplicability == "crohns_disease"`),
  structurally excluded from all UC answers.
- **12** claims in `excludedClaimIds`, confirmed absent from the loaded
  claim set.
- **No ESR claim** exists anywhere in the source package; ESR questions
  always return the fixed unsupported-topic message.

## Test results

```
35 passed in 1.97s
```

Command used: `pytest tests/ -v` (from the project's `venv`).

Coverage includes (matching the spec's 15-item list): UC-only filtering
with the exact 5-claim assertion; Crohn's-only exclusion (15-claim count
and non-retrievability, including an adversarial "apply Crohn's evidence
to UC" prompt); ESR fallback exact-string match; citation/source
preservation against the original claim records; exact-locator verbatim
preservation; limitations/applicabilityLimitations verbatim preservation;
unsupported-topic fallback for biologics/JAK inhibitors/mucosal
healing/colonoscopy/intestinal ultrasound/ESR/CRP/fecal calprotectin;
medication-change refusal; diagnosis refusal; symptom-vs-inflammation
caveat presence and non-confirmation; determinism across repeated runs
with `requests.get`/`requests.post` monkeypatched to raise if called;
LangGraph node-sequence assertions for a normal answerable query, an
unsupported-topic query, and a safety-boundary query (confirmed
`compose_answer` is never visited in the refusal case); Streamlit module
import and a live `streamlit run` + HTTP health check; unique claim IDs
(both loaded set and raw file); and source-ID resolution for every claim.

## Streamlit launch verification

Launched manually outside the test suite as well:

```
streamlit run streamlit_app.py --server.headless true --server.port 8512 &
curl -o /dev/null -w "%{http_code}" http://localhost:8512   # -> 200
kill <pid>   # clean shutdown, no errors in log
```

The `test_streamlit_run_starts_cleanly` pytest test performs an equivalent
check automatically (subprocess launch, poll for HTTP 200, then
terminate).

## Deviations from spec, and why

- The optional model-assisted composition path (`ENABLE_MODEL_CALLS=true`)
  is documented and gated but **not implemented** -- the spec requires it
  be "strictly optional... OFF by default" and that the app "run and
  answer correctly with zero model calls," which this build satisfies. No
  actual call code exists to invoke, by design, since implementing an
  unused paid-call path would add risk without being exercised or
  requested for use.
- No other functional deviations. The eligibility rule is the exact
  substring filter specified (not the broader `ibd_general` rule from
  other prototypes); all 5 claims and 15 Crohn's-only claims were
  independently re-verified against the live evidence file during this
  build and match the numbers given in the task.

## Confirmation: no source data or other repository modified

- The original evidence file at
  `/mnt/user-data/uploads/ibd-research-review/ibd-prototype-evidence.json`
  was only read, never written. It remains at its original path,
  unmodified, with its original read-only permissions.
- This project's own copy lives at
  `/home/claude/ibd-uc-rag-prototype/data/ibd-prototype-evidence.json` and
  is the only file this prototype reads at runtime.
- No path containing `cheatmeal-recovery` was inspected, referenced, or
  depended on anywhere in this build.
- No other repository, project, or application on this machine was
  touched. All new files live exclusively under
  `/home/claude/ibd-uc-rag-prototype/`.

## Known limitations (restated, not overstated)

- The UC-eligible evidence set is currently only **5 claims**, spanning 4
  topics (fibre, core_condition_knowledge, fruit_vegetables, alcohol).
  Almost every other nutrition/lifestyle/biomarker/procedure topic a real
  user might ask about has zero coverage and will correctly return the
  fixed unsupported-topic fallback rather than any fabricated answer.
- There is no ESR (or CRP, or fecal calprotectin) claim in the source
  package at all -- this is a data gap in the underlying evidence review,
  not a retrieval bug, and the tool never implies otherwise.
- Topic classification is a simple keyword/substring classifier, not a
  learned model; it is intentionally conservative and simple per the
  spec's "keyword classifier is fine and should be the default."
- Safety-boundary detection is pattern/keyword based. It is deliberately
  tuned to over-refuse rather than under-refuse (e.g. the Crohn's-to-UC
  misapplication check uses a broad "mentions Crohn's + mentions UC +
  uses an apply/use/treat verb" heuristic) to keep the safer failure mode.
