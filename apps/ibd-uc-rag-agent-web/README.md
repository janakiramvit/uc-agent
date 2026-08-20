# IBD / UC Evidence Agent (Next.js + LangGraph)

Research prototype—not medical advice. Evidence and outputs require clinician/human review.

Production-grade rebuild of the original Streamlit prototype
(`apps/ibd-uc-rag-prototype/`), following the architecture pattern of
[`procurement-genai-case-study`](https://github.com/janakiramvit/procurement-genai-case-study):
a Next.js (TypeScript, App Router) frontend calling a Python LangGraph
agent deployed as a Vercel Python serverless function.

## Architecture

```
app/                Next.js frontend (chat UI, citations, agent-trace panel)
api/chat.py          Vercel Python serverless entrypoint (rate limiting,
                      timeout handling, error handling)
api/agent_core/       LangGraph agent (StateGraph), extended from the
                      original prototype's tested nodes:
  evidence_loader.py    load + index the evidence package (unchanged)
  retrieval.py           BM25 retriever (unchanged)
  vector_retrieval.py    NEW: OpenAI-embeddings vector retrieval
  planner.py              NEW: query decomposition / planning
  conflict_detector.py    NEW: cross-source conflict detection
  safety_rules.py        query-level safety boundaries (unchanged)
  llm_synthesizer.py      NEW: real LLM-backed grounded synthesis
  subagents.py            safety critic, citation verifier, gap detector,
                          QA agent (unchanged, reused as-is)
  graph_v2.py              NEW: composes all of the above into one
                          StateGraph
  tools.py                6 read-only evidence tools (search/get-claim/
                          get-source/list-topics/check-applicability/
                          evidence-gaps) -- tool-augmented RAG layer
  rate_limit.py           NEW: best-effort request rate limiting + cost caps
api/data/                exact, unmodified copy of the reviewed evidence
                      package (md5-identical to the Streamlit app's copy)
tests/                new pytest suite: planning, tool invocation,
                      unsupported-query handling, citation grounding,
                      safety filters, conflict detection, rate limiting,
                      and an HTTP-level test of api/chat.py itself
```

## Agent graph (graph_v2)

```
receive_query -> planner -> query_classifier -> evidence_retriever (BM25)
  -> vector_retriever (embeddings, if OPENAI_API_KEY set)
  -> source_applicability_checker -> conflict_detector -> gap_detector
  -> check_safety_boundaries -> evidence_synthesizer (REAL LLM call)
  -> safety_critic -> citation_verifier -> qa_agent -> attach_citations_final
```

with bounded retry (1 retry, then hard refuse) on safety-critic or
citation-verifier failure, exactly mirroring the original prototype's
retry policy.

**Grounding is enforced by construction, not by trusting the model**:
citations are built directly from the retrieved/verified evidence
claims, never parsed out of the LLM's free text. The LLM can only
contribute prose; the citation_verifier node independently re-checks
every citation against the real evidence package regardless.

## Environment variables

See `.env.example`. Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to enable
the real LLM synthesis step. With neither set, the pipeline still runs
end-to-end and returns an explicit `"llm_unavailable"` status rather than
a fabricated answer.

## Running locally

```bash
npm install
npm run dev        # frontend on http://localhost:3000

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pytest tests/ -v    # agent test suite
```

The Python API function (`api/chat.py`) is designed to run under Vercel's
Python runtime; `vercel dev` runs both the Next.js frontend and the
Python function together locally.

## Known limitations

- Vector retrieval and LLM synthesis both require a real provider API
  key (`OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`) set as an environment
  variable. Neither is hard-coded, and neither is faked when absent.
- Rate limiting is a best-effort, in-memory, single-instance token
  bucket -- Vercel serverless functions are not guaranteed to reuse the
  same process across invocations, so this does not enforce a hard global
  cap across all instances. A production deployment would back this with
  a shared store (e.g. Upstash Redis).
- The underlying evidence package (`api/data/ibd-prototype-evidence.json`)
  is preserved exactly as-is from the Streamlit prototype and carries the
  same QA status noted there: it is real, unpublished-for-clinical-use
  evidence pending human review, not clinically approved.
