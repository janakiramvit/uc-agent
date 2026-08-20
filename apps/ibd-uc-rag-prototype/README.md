# ibd-uc-rag-prototype

A local, non-production prototype that answers questions about **ulcerative
colitis (UC)** using a fixed, human-reviewed evidence package, via a
LangChain retriever wired into an explicit LangGraph state machine, with a
Streamlit UI.

This is an **informational prototype only** -- not a medical device, not a
substitute for professional medical advice, diagnosis, or treatment. All
evidence surfaced by this tool is **pending human clinical review**.

## Honest scope note (read this first)

The UC-eligible evidence set in the current package is **only 5 claims**:

| Claim ID | Topic | Source |
|---|---|---|
| CLM-014 | fibre | Diet, Food, and Nutritional Exposures and IBD... |
| CLM-081 | core_condition_knowledge | ECCO consensus on dietary management... |
| CLM-093 | fruit_vegetables | Food and IBD |
| CLM-094 | fibre | Food and IBD |
| CLM-095 | alcohol | Food and IBD |

All five have `conditionApplicability == "ulcerative_colitis; crohns_disease; ibd_general"`.
Every other topic (biologics, JAK inhibitors, mucosal healing, colonoscopy,
intestinal ultrasound, ESR, CRP, fecal calprotectin, medication questions,
etc.) has **zero** UC-eligible claims and will correctly return:

> "This topic is not currently covered by the reviewed UC evidence set."

There is no ESR claim anywhere in the source package. This tool never
claims ESR coverage.

15 claims in the source package are Crohn's-disease-only
(`conditionApplicability == "crohns_disease"`) and are structurally
excluded from every UC answer. 12 claims are in the package's
`excludedClaimIds` list and are never retrievable at all.

## Architecture

```
data/ibd-prototype-evidence.json   read-only copy of the reviewed evidence package
app/evidence_loader.py             loads JSON, applies UC-substring eligibility filter
                                    + excluded-claim-id filter, builds LangChain Documents
app/retrieval.py                   LangChain BM25Retriever, metadata-filter-before-rank
app/safety_rules.py                keyword/pattern guardrails (diagnosis, flare, meds,
                                    diet plans, symptom/inflammation, Crohn's misapplication)
app/workflow.py                    LangGraph StateGraph implementing the original 8-node workflow
app/subagents.py                   extended LangGraph subagent graph (8 bounded subagents,
                                    retry/repair loop) -- see "Subagent graph" below
app/qa_checks.py                   individually-named, individually-testable QA Agent checks
mcp_server/tools.py                pure, transport-independent MCP tool implementations
mcp_server/server.py               FastMCP wiring exposing exactly 6 read-only tools
memory/session_memory.py           in-memory-only, per-Streamlit-session store
memory/preference_memory.py        small persisted (JSON) non-clinical preference store
memory/guard.py                    hard denylist guard shared by both memory stores
streamlit_app.py                   Streamlit UI entry point (+ Developer/QA panel, preferences,
                                    "Clear my data")
tests/test_prototype.py            original pytest suite (35 tests)
tests/test_mcp_server.py           MCP tool schema + retrieval-correctness tests
tests/test_memory.py               memory isolation, clearing, and clinical-content-guard tests
tests/test_subagents.py            subagent routing, safety critic, citation verifier,
                                    QA agent, and retry/stop tests
```

### Eligibility rule (exact)

A claim is UC-eligible **only if** its `conditionApplicability` string
**contains the substring `"ulcerative_colitis"`**. This is a strict
substring filter, not the broader "ibd_general" rule used in unrelated
prototypes. See `app/evidence_loader.py::is_uc_eligible`.

### LangGraph workflow (8 nodes, `app/workflow.py`)

1. `receive_query` -- normalize raw query + optional topic/disease filter into state.
2. `classify_topic` -- lightweight keyword classifier against the known topic vocabulary; flags known-zero-coverage topics (ESR, biologics, JAK inhibitors, mucosal healing, colonoscopy, intestinal ultrasound, CRP, fecal calprotectin).
3. `retrieve_uc_claims` -- LangChain BM25 retrieval, restricted to the pre-filtered UC-eligible candidate set (filter happens before ranking, not after).
4. `check_source_and_applicability` -- independent, defense-in-depth re-check that every candidate is still UC-eligible and not Crohn's-only/excluded.
5. `check_safety_boundaries` -- guardrail checks; can short-circuit straight to `refuse`, bypassing `compose_answer` entirely.
6. `compose_answer` -- deterministic, template-based composition from `plainLanguageExplanation`/`claimText`; no LLM call by default.
7. `attach_citations` -- maps every claim used to a numbered citation with full metadata.
8. `fallback_if_unsupported` -- if nothing survives, returns exactly `"This topic is not currently covered by the reviewed UC evidence set."`

Graph edges are visible in `build_workflow()`; the safety node uses a
conditional edge (`route_after_safety`) to route to `refuse` or
`compose_answer`, and `attach_citations` uses a conditional edge
(`route_after_citations`) to route to `fallback_if_unsupported` when no
claims survive.

### No model calls by default

Retrieval is local BM25 (`langchain_community.retrievers.BM25Retriever`).
Answer composition is deterministic string templating over the claim's own
`plainLanguageExplanation`/`claimText` fields -- nothing is invented.
`ENABLE_MODEL_CALLS` (see `.env.example`) is off by default and no code
path in this build performs a network/model call regardless of its value.

## Setup

```bash
cd ibd-uc-rag-prototype
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; defaults are already safe
```

## Run the app

```bash
streamlit run streamlit_app.py
```

Then open the printed local URL (default `http://localhost:8501`).

## Run the tests

```bash
pytest tests/ -v
```

105 tests, all passing as of this build (35 original + 70 new). Covers:
UC-only filtering (exact 5-claim set), Crohn's-only exclusion (15 claims),
ESR/unsupported-topic fallback, citation/locator/limitation verbatim
preservation, medication and diagnosis refusals, symptom-vs-inflammation
caveat, determinism with zero model calls, LangGraph node-sequence
assertions for three query classes, Streamlit import + live `streamlit run`
health check, unique claim IDs, source-ID resolution integrity, MCP tool
schemas/retrieval correctness/hard eligibility boundary, memory isolation
and clearing and the clinical-content guard, subagent routing, safety
critic and citation verifier rejection, QA agent structured failure
reporting, and the retry-once-then-stop behavior.

## MCP server

A local, read-only MCP server (`mcp_server/`, built on the `mcp` Python
SDK's `FastMCP`, pinned to `mcp==1.29.0`) exposes exactly six tools over
the same eligibility-filtered view the Streamlit app uses -- it reuses
`app.evidence_loader` / `app.retrieval` directly rather than duplicating
any filtering logic, and has no write/approve/edit/delete capability of
any kind:

- `search_uc_claims(query, topic=None)`
- `get_claim(claim_id)` -- hard boundary: refuses Crohn's-only/excluded
  claim IDs even when asked for directly
- `get_source(source_id)`
- `list_supported_topics()` -- reflects only the current 5-claim reality
- `check_claim_applicability(claim_id)`
- `get_evidence_gaps()` -- dynamically diffs the full topic vocabulary
  against the UC-eligible one, combined with the known-absent categories
  (ESR, CRP, biologics, ...) from `app.safety_rules.KNOWN_UNSUPPORTED_KEYWORDS`

Run it standalone (stdio transport):

```bash
python -m mcp_server.server
```

`tests/test_mcp_server.py` unit-tests the underlying tool functions
directly and also does a full live stdio smoke test of all six tools via
`mcp.client.stdio.stdio_client` + `ClientSession`.

## Memory layers

`memory/` has two clearly separate stores (see `memory/__init__.py`):

- **`SessionMemory`** -- current question, retrieved claim IDs,
  conversation turns, and safety warnings already shown, scoped to one
  Streamlit session (`st.session_state`), in-memory only, never written
  to disk.
- **`UserPreferenceMemory`** -- preferred answer length
  (short/standard/detailed), preferred language tag (stored only, no
  translation implemented), and whether citations are expanded by
  default. Persists across a session restart via
  `memory_store/user_preferences.json` (this project's own directory,
  never `data/` and never the source evidence file).

Both stores run every write through `memory/guard.py::validate_before_store`,
a denylist-pattern guard (same style as `app/safety_rules.py`) that
refuses to store a diagnosis, an inferred disease-activity judgment, a
predicted flare, a medication recommendation, or an unsupported medical
conclusion treated as fact -- see `tests/test_memory.py` for the
guard-rejection tests. `memory.clear_all_memory()` and the Streamlit
"Clear my data" button wipe both stores at once.

## Subagent graph

`app/subagents.py` extends (does not replace) `app/workflow.py`'s
8-node graph with eight bounded, single-responsibility subagents and a
bounded retry/repair loop:

1. **Query Classifier** -- topic + intent (question / diagnosis-seeking /
   medication-change-seeking / flare-prediction-seeking / diet-plan-seeking /
   symptom-inflammation-question), reusing `check_safety_boundaries` as the
   single source of truth for the underlying patterns.
2. **Evidence Retriever** -- thin wrapper around the existing
   `retrieve_uc_claims` node.
3. **Source Applicability Checker** -- extends
   `check_source_and_applicability` with a source-level status check
   (source resolves, not superseded).
4. **Evidence Synthesizer** -- template-based draft from
   `plainLanguageExplanation`/`claimText` (or, on a strict retry,
   `supportingExcerpt` only) -- no invention.
5. **Safety Critic** -- inspects the DRAFTED ANSWER (not the query) for
   diagnosis language, flare prediction, medication-change language,
   individualized diet prescription, causal overstatement, and
   symptom/inflammation confusion.
6. **Citation Verifier** -- checks every citation's claim ID, source URL,
   excerpt, and locator against the underlying data, catching a
   hypothetical fabricated citation.
7. **Gap Detector** -- reuses `mcp_server.tools.compute_evidence_gaps` (one
   source of truth) to route to the fixed fallback message.
8. **QA Agent** -- runs every check in `app/qa_checks.py` as a final pass
   and returns a structured, per-check pass/fail report (`qa_report`).

If the Safety Critic or Citation Verifier fails, the Evidence Synthesizer
is retried once with a stricter constraint; if the retry also fails, the
graph hard-stops to a refusal (never returns the unsafe/unverifiable
draft) -- see `route_after_safety_critic` / `route_after_citation_verifier`
in `app/subagents.py` and `tests/test_subagents.py` for the retry-then-stop
tests. The original `app/workflow.py::build_workflow` graph and its exact
8-node behavior are untouched; the extended graph is a separate,
additional graph (`build_extended_workflow`) used to populate the
Developer/QA panel.

## Developer / QA panel

The Streamlit UI (`streamlit_app.py`) has a collapsed-by-default
`st.expander("Developer / QA panel (advanced)")` showing, for the most
recent query: the extended graph's node/step sequence, each subagent's
decision/output, retrieved claim IDs, source IDs used, the Citation
Verifier result, the Safety Critic result, the Gap Detector result, the
QA Agent's structured report, and the current session memory contents.
It is purely additive -- the primary user-facing answer above it is still
produced by the original, unmodified `graph` (`build_workflow`).

## Safety boundaries enforced

The workflow refuses (routes to a fixed refusal message, never to
`compose_answer`) any query that attempts to:

- get a UC diagnosis or flare confirmation
- predict an individual flare
- get a medication start/stop/change recommendation
- get an individualized/prescriptive diet plan
- have the app confirm or deny that symptoms mean active inflammation
- apply Crohn's-only evidence to a UC question

See `SAMPLE_QUESTIONS.md` for concrete examples of each behavior.

## What this prototype does NOT do

- No production authentication, no deployment configuration.
- No external database -- evidence is a local JSON file.
- No cloud/Azure service integration.
- No paid/model API calls unless `ENABLE_MODEL_CALLS=true` is explicitly
  set (and even then, this build has no implemented call path -- it's a
  documented, gated placeholder only).
- Does not modify the source evidence file at
  `/mnt/user-data/uploads/ibd-research-review/ibd-prototype-evidence.json`
  (a read-only copy lives at `data/ibd-prototype-evidence.json`).
- The MCP server (`mcp_server/`) is read-only -- no write/approve/edit/
  delete tool exists anywhere in this build.
- `UserPreferenceMemory` never stores clinical facts (see "Memory
  layers" above); `SessionMemory` is never written to disk at all.

See `COMPLETION_REPORT_ADDENDUM.md` for the full test results and
confirmation that nothing outside this project directory was modified.
