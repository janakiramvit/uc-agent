# Completion report addendum -- MCP server, memory layers, subagent graph, QA agent, dev panel

This addendum covers the second phase of work, extending the original
prototype documented in `COMPLETION_REPORT.md`. Nothing in the original
build was removed or behaviorally changed; all 35 original tests still
pass unmodified.

## What was added

1. **Local MCP server** (`mcp_server/`) -- `mcp_server/tools.py` holds
   pure, transport-independent implementations of the six required
   tools (`search_uc_claims`, `get_claim`, `get_source`,
   `list_supported_topics`, `check_claim_applicability`,
   `get_evidence_gaps`); `mcp_server/server.py` wires them into a
   `FastMCP` server (`mcp==1.29.0`) with no write/approve/edit/delete
   tool of any kind. All six tools reuse `app.evidence_loader` /
   `app.retrieval` directly.

2. **Memory layers** (`memory/`) -- `SessionMemory` (in-memory only,
   backed by `st.session_state`) and `UserPreferenceMemory` (persisted
   JSON under `memory_store/`), both routed through a shared
   `memory/guard.py::validate_before_store` denylist guard that refuses
   diagnosis/flare-prediction/medication-change/unsupported-conclusion
   content. `memory.clear_all_memory()` wipes both stores; wired to a
   "Clear my data" button in the Streamlit sidebar.

3. **LangGraph subagents** (`app/subagents.py`) -- eight bounded,
   single-responsibility nodes (Query Classifier, Evidence Retriever,
   Source Applicability Checker, Evidence Synthesizer, Safety Critic,
   Citation Verifier, Gap Detector, QA Agent) assembled into a new,
   separate compiled graph (`build_extended_workflow`) with a bounded
   one-retry-then-stop repair loop when the Safety Critic or Citation
   Verifier rejects a draft. The original `app/workflow.py::build_workflow`
   graph is untouched.

4. **QA Agent checks** (`app/qa_checks.py`) -- 15 individually named,
   individually testable check functions, aggregated by
   `run_all_qa_checks` into a structured per-check pass/fail report
   (never just one overall boolean).

5. **UI additions** (`streamlit_app.py`) -- a collapsed-by-default
   "Developer / QA panel" expander (node sequence, subagent trace,
   retrieved claim/source IDs, citation verifier / safety critic / gap
   detector / QA agent results, session memory contents), sidebar
   preference controls (answer length, citations-expanded-by-default)
   wired to `UserPreferenceMemory`, and a "Clear my data" button. The
   primary user-facing answer flow is unchanged -- it still calls the
   original `run_query(graph, ...)`; the extended graph runs in parallel
   purely to populate the dev panel.

6. **Tests** -- `tests/test_mcp_server.py`, `tests/test_memory.py`,
   `tests/test_subagents.py` (70 new tests), alongside the untouched
   `tests/test_prototype.py` (35 tests).

## Full test results

```
pytest tests/ -v
...
105 passed in ~2.9s
```

Breakdown: 35 original (unmodified) + 70 new = 105, all passing.
`tests/test_prototype.py::test_streamlit_run_starts_cleanly` (part of
the original 35) performs a live `streamlit run` + HTTP 200 health
check as part of the suite; this was also re-verified manually outside
pytest:

```
streamlit run streamlit_app.py --server.headless true --server.port 8513 &
curl -o /dev/null -w "%{http_code}" http://localhost:8513   # -> 200
kill <pid>
```

The MCP server was also smoke-tested live end-to-end (not just via unit
tests of the underlying functions) using the `mcp` SDK's stdio client:

```python
async with stdio_client(StdioServerParameters(command="python", args=["-m", "mcp_server.server"])) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # all six tools called successfully over real stdio transport
```

All six tools returned successfully (`isError=False`), including a
`get_claim("CLM-081")` call confirming a real UC-eligible claim is
returned with every verbatim field intact.

## Confirmation: no unintended modifications outside the project directory

- `/mnt/user-data/uploads/ibd-research-review/ibd-prototype-evidence.json`
  -- md5 checksum verified identical before and after this work
  (`25166de97aa7cb8b6318276efc6e8df1`); only ever read, never written.
- This project's own evidence copy at
  `/home/claude/ibd-uc-rag-prototype/data/ibd-prototype-evidence.json`
  -- also unmodified (same checksum), copy-on-read only, as instructed.
- No path containing `cheatmeal-recovery` exists anywhere on the
  filesystem (`find / -iname "*cheatmeal-recovery*"` returned nothing).
- All new files live exclusively under
  `/home/claude/ibd-uc-rag-prototype/` (`mcp_server/`, `memory/`,
  `memory_store/`, new files in `app/` and `tests/`, edits to
  `streamlit_app.py`, `requirements.txt`, `README.md`).
- No other repository, project, or application on this machine was
  touched.

## Deviations from spec, and why

- **MCP SDK version pin.** The environment's pre-installed `mcp` package
  resolved to `2.0.0`, whose `mcp.server` module does not expose
  `mcp.server.fastmcp` (a different, non-FastMCP server API). Installed
  `mcp==1.29.0` instead (the last 1.x release, still current per
  `modelcontextprotocol.io`) into the project's `venv`, which does
  provide `FastMCP` and is what `mcp_server/server.py` uses. Pinned in
  `requirements.txt`.
- **`get_evidence_gaps` composition.** The spec names ESR/CRP/biologics/
  JAK-inhibitors/etc. as topics that should appear in the gap list, but
  none of those terms ever appear as a `topic` value anywhere in the
  49-claim source data (verified directly) -- they only exist as
  keywords in `app.safety_rules.KNOWN_UNSUPPORTED_KEYWORDS`. So
  `get_evidence_gaps` combines two computed sources: (a) a genuine
  dynamic diff of the full-vs-UC-eligible topic vocabulary (currently 10
  nutrition/lifestyle topics), and (b) the existing
  `KNOWN_UNSUPPORTED_KEYWORDS` list (reused, not duplicated) for the
  categories that are absent from the topic vocabulary entirely. This
  keeps a single source of truth for the keyword list while still
  satisfying "compute this dynamically" for the part of the gap set that
  is actually present in the claim data.
- **Extended graph is additive, not a replacement.** `app/workflow.py`'s
  `build_workflow` and its exact 8-node behavior were left byte-for-byte
  compatible with the original 35 tests (which assert exact
  `visited_nodes` sequences). The new 8-subagent, retry-capable graph
  lives in `app/subagents.py` as a second, separate compiled graph
  (`build_extended_workflow`) rather than mutating the original one in
  place, so both can be independently tested and the original test suite
  needed zero changes.
- **Test-only hooks in the synthesizer.** Because the real 5-claim UC
  evidence set is safe by construction, the Safety Critic and Citation
  Verifier never organically fail against it. To make the retry/repair
  loop and rejection paths genuinely exercised (not just asserted via
  hand-called functions), `evidence_synthesizer_node` accepts two
  test-only state keys (`_test_force_bad_draft_attempts`,
  `_test_inject_fake_citation[_attempts]`) that are absent from every
  real request path and documented inline as test-only.

## Known limitations (restated, not overstated)

- Still only **5 UC-eligible claims** in the underlying evidence
  package (CLM-014, CLM-081, CLM-093, CLM-094, CLM-095). None of this
  phase's work changes that -- it adds infrastructure (MCP access,
  memory, a more explicit/defensible subagent pipeline, QA reporting,
  and visibility into all of it) around the same underlying evidence
  coverage, not new evidence.
- The MCP server, memory layers, and subagent graph are all local,
  single-process, and read-only/no-model-call by design, matching the
  rest of the prototype's "informational prototype only" scope.
- `UserPreferenceMemory`'s language field stores a tag only; no
  translation is implemented, matching the spec.
