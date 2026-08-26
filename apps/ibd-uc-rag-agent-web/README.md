# IBD / UC Evidence Agent (Next.js + model-powered LangGraph)

Research prototype—not medical advice. Evidence and outputs require clinician/human review.

A genuine model-powered RAG agent: nine LLM-powered LangGraph nodes
(planner, query classifier, query reformulator, evidence analyst,
conflict resolver, grounded synthesizer, citation reviewer, safety
critic, QA evaluator) wrapped around deterministic, non-bypassable tools
(BM25, vector retrieval, reciprocal-rank fusion, UC-applicability
filtering, citation existence checks, hard safety rules, request/token
limits). Deployed as a Next.js (TypeScript, App Router) frontend calling
a Python LangGraph agent as a Vercel serverless function, following the
[`procurement-genai-case-study`](https://github.com/janakiramvit/procurement-genai-case-study)
reference architecture.

## Full agent graph (`api/agent_core/graph_v2.py`)

```
receive_query
  -> check_safety_boundaries   [DETERMINISTIC, hard, non-bypassable -- runs
                                 BEFORE any model call so a refused query
                                 never spends a token]
  -> planner                   [LLM: dynamic tool selection + sub-topic ID]
  -> query_classifier          [LLM: intent -- informational only]
  -> query_reformulator        [LLM: recall-widening only, never narrowing]
  -> evidence_retriever         [DETERMINISTIC BM25, planner+reformulator-routed]
  -> vector_retriever            [DETERMINISTIC embeddings retrieval, when configured]
  -> fusion_reranker             [DETERMINISTIC reciprocal rank fusion:
                                 BM25 + vector + planner tool-call results]
  -> source_applicability_checker [DETERMINISTIC UC-eligibility / Crohn's-only
                                 / excluded-claim filtering]
  -> evidence_analyst           [LLM: summarizes verified claims only]
  -> conflict_detector           [DETERMINISTIC structural signal]
  -> conflict_resolver          [LLM: true-contradiction vs. which
                                 dimension differs -- never drops a claim]
  -> gap_detector                [DETERMINISTIC unsupported-topic routing]
  -> evidence_synthesizer       [LLM: the ONLY node whose text becomes the
                                 final answer; citations built independently]
  -> safety_critic               [LLM AND deterministic regex -- combined
                                 verdict, LLM can only be stricter]
  -> citation_verifier           [DETERMINISTIC existence/integrity check]
  -> citation_reviewer          [LLM: semantic-support check, additive]
  -> qa_agent                   [LLM alongside deterministic QA checks]
  -> attach_citations_final
```

Bounded retry: a safety-critic, citation-verifier, or citation-reviewer
failure routes back to `evidence_synthesizer` once, then hard-refuses
(`MAX_SYNTHESIS_ATTEMPTS = 2`).

**Fail-safe by construction, not by convention**: every LLM-powered node
degrades to a deterministic fallback (documented per-node in its module
docstring) on missing credentials, timeout, provider error, or
schema-invalid output -- never by crashing, never by silently proceeding
with unverified output, and never (for `evidence_synthesizer`
specifically, since its output IS the answer) by fabricating a response.

## Deterministic, non-bypassable tools

| Tool | Module |
|---|---|
| BM25 keyword retrieval | `agent_core/retrieval.py` |
| Vector/embedding retrieval | `agent_core/vector_retrieval.py` |
| Reciprocal-rank fusion | `agent_core/fusion.py` |
| UC-applicability / Crohn's-exclusion filtering | `agent_core/evidence_loader.py` (`is_uc_eligible`, `is_crohns_only`) |
| Source/locator lookup | `agent_core/tools.py` |
| Citation existence checks | `agent_core/subagents.py` (`citation_verifier_node`) |
| Hard safety rules | `agent_core/safety_rules.py` (`check_safety_boundaries`) |
| Request/token limits | `agent_core/rate_limit.py` |

An LLM node can only ever **add** an opinion on top of what these have
already decided -- see `tests/test_applicability_bypass_resistance.py`
and `tests/test_llm_safety_critic.py` for the tests proving this holds
even against a manipulated/hallucinating model output.

## Model routing (env vars only, never hard-coded)

| Category | Env vars | Used by | Default (if unset) |
|---|---|---|---|
| `planner` | `PLANNER_PROVIDER`, `PLANNER_MODEL` | planner, query classifier, query reformulator | anthropic / `claude-haiku-4-5` (cheap) |
| `reasoning` | `REASONING_PROVIDER`, `REASONING_MODEL` | evidence analyst, conflict resolver | anthropic / `claude-sonnet-4-5` |
| `synthesis` | `SYNTHESIS_PROVIDER`, `SYNTHESIS_MODEL` | grounded synthesizer | anthropic / `claude-sonnet-4-5` |
| `critic` | `CRITIC_PROVIDER`, `CRITIC_MODEL` | citation reviewer, safety critic, QA evaluator | anthropic / `claude-sonnet-4-5` |

See `.env.example`. Provider must be `openai` or `anthropic`; the
matching `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` must be set for whichever
provider a category resolves to. Vector retrieval separately always uses
`OPENAI_API_KEY` (embeddings) regardless of the routing above.

## Running locally

```bash
npm install
npm run dev        # frontend on http://localhost:3000

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest tests/ -v    # agent test suite
```

## Known limitations

- Rate limiting is a best-effort, in-memory, single-instance token bucket
  -- Vercel serverless functions aren't guaranteed to reuse the same
  process across invocations, so it doesn't enforce a hard global cap
  across all instances.
- The per-request token budget (`agent_core/rate_limit.py`,
  `DEFAULT_MAX_TOKENS_PER_REQUEST = 8000`) is estimated via a
  chars-per-token heuristic, not exact provider tokenization.
- The underlying evidence package (`api/data/ibd-prototype-evidence.json`)
  is preserved exactly as-is and carries the same QA status noted
  previously: real, unpublished-for-clinical-use evidence pending human
  review, not clinically approved.
- MCP HTTP integration is explicitly out of scope for this change (a
  separate, later task).
