"use client";

import { useState } from "react";
import type { ChatErrorResponse, ChatResponse } from "./types";

const STATUS_STYLES: Record<string, string> = {
  answered: "border-green-300 bg-green-50 text-green-900",
  unsupported: "border-amber-300 bg-amber-50 text-amber-900",
  refused: "border-red-300 bg-red-50 text-red-900",
  llm_unavailable: "border-slate-300 bg-slate-100 text-slate-900",
  error: "border-red-300 bg-red-50 text-red-900",
};

const SUGGESTED_QUESTIONS = [
  "Is fibre good or bad for my ulcerative colitis?",
  "How much fibre should I actually be eating with UC?",
  "Should I eat fruit and vegetables if I have ulcerative colitis?",
  "Is it safe to drink alcohol with ulcerative colitis?",
  "What general diet advice is there for someone with IBD?",
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<ChatErrorResponse | null>(null);
  const [showTrace, setShowTrace] = useState(false);

  async function handleAsk(overrideQuery?: string) {
    const q = overrideQuery ?? query;
    if (!q.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data as ChatErrorResponse);
      } else {
        setResult(data as ChatResponse);
      }
    } catch {
      setError({ error: "network_error", message: "Could not reach the agent API." });
    } finally {
      setLoading(false);
    }
  }

  function askSuggested(q: string) {
    setQuery(q);
    handleAsk(q);
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-10">
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <strong>Informational prototype only</strong> — not a medical device, not a substitute for
        professional medical advice, diagnosis, or treatment. All evidence in this tool is{" "}
        <strong>pending human clinical review</strong> and has not been clinically approved.
        UC-only evidence set (5 claims). Does not diagnose, predict flares, recommend medication
        changes, or generate individualized diet plans.
      </div>

      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Ulcerative Colitis Evidence Agent</h1>
      </header>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          className="flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-neutral-500 focus:outline-none"
          placeholder="e.g. What does the evidence say about fibre in ulcerative colitis?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleAsk();
          }}
        />
        <button
          onClick={() => handleAsk()}
          disabled={loading || !query.trim()}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </div>

      <section aria-label="Suggested questions">
        <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
          Suggested questions
        </h2>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => askSuggested(q)}
              disabled={loading}
              className="rounded-full border border-neutral-300 px-3 py-1.5 text-xs text-neutral-700 hover:border-neutral-500 hover:bg-neutral-50 disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900">
          <strong className="block">{error.error}</strong>
          {error.message}
          {typeof error.retryAfterSeconds === "number" && (
            <span> Retry after ~{Math.ceil(error.retryAfterSeconds)}s.</span>
          )}
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-4">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Answer</h2>
            <div className={`whitespace-pre-wrap rounded-lg border px-4 py-3 text-sm ${STATUS_STYLES[result.status] ?? "border-neutral-300 bg-neutral-50"}`}>
              {result.answer}
            </div>
            {result.showSymptomCaveat && (
              <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
                Note: symptoms and measurable intestinal inflammation do not always move together in
                ulcerative colitis. This information does not confirm or rule out active inflammation.
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold">Evidence / Citations</h2>
            {result.citations.length === 0 ? (
              <p className="text-sm text-neutral-500">
                No sufficient evidence was retrieved for this query from the reviewed UC evidence set.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {result.citations.map((c) => (
                  <details key={c.number} className="rounded-lg border border-neutral-200 px-4 py-3 text-sm">
                    <summary className="cursor-pointer font-medium">
                      [{c.number}] {c.sourceTitle}
                    </summary>
                    <div className="mt-2 flex flex-col gap-1 text-neutral-700">
                      <div>
                        Claim ID: <code>{c.claimId}</code> · Evidence level: {c.evidenceLevel} · Confidence:{" "}
                        {c.confidence}
                      </div>
                      <div>
                        <strong>Claim:</strong> {c.claimText}
                      </div>
                      <div>
                        <strong>Supporting excerpt:</strong> {c.supportingExcerpt}
                      </div>
                      <div>
                        <strong>Exact locator:</strong> {c.exactLocator}
                      </div>
                      <div>
                        <strong>Source URL:</strong>{" "}
                        <a className="text-blue-700 underline" href={c.sourceUrl} target="_blank" rel="noreferrer">
                          {c.sourceUrl}
                        </a>
                      </div>
                      <div>
                        <strong>Limitations:</strong> {c.limitations}
                      </div>
                      <div>
                        <strong>Applicability limitations:</strong> {c.applicabilityLimitations}
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            )}
          </section>

          {result.conflictReport?.has_conflicts && (
            <section>
              <h2 className="mb-2 text-lg font-semibold">Conflict detector</h2>
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {result.conflictReport.conflicts.map((c, i) => (
                  <div key={i} className="mb-1">
                    <strong>{c.topic}:</strong> {c.reason} ({c.claimIds.join(", ")})
                  </div>
                ))}
              </div>
            </section>
          )}

          <section>
            <button
              className="w-fit text-sm font-medium text-neutral-600 underline"
              onClick={() => setShowTrace((v) => !v)}
            >
              {showTrace ? "Hide" : "Show"} developer / agent-trace panel
            </button>
            {showTrace && (
              <div className="mt-2 flex flex-col gap-2 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3 text-xs">
                <div>
                  <strong>Node sequence:</strong> {result.visitedNodes.join(" → ")}
                </div>
                <div>
                  <strong>LLM provider / model:</strong> {result.llmProvider ?? "—"} / {result.llmModel ?? "—"}
                </div>
                <div>
                  <strong>Vector retrieval status:</strong> {result.vectorRetrievalStatus ?? "—"}
                </div>
                {result.fusionReport && (
                  <div>
                    <strong>Fusion (RRF):</strong> vector used={String(result.fusionReport.vector_used)}; BM25=
                    {result.fusionReport.bm25_ids.join(", ") || "(none)"}; vector=
                    {result.fusionReport.vector_ids.join(", ") || "(none)"}; fused=
                    {result.fusionReport.fused_ids.join(", ") || "(none)"}
                  </div>
                )}
                {result.plan && (
                  <div>
                    <strong>Plan:</strong> topics={result.plan.identified_topics.join(", ") || "(none)"}; steps=
                    {result.plan.steps.join(" → ")}
                  </div>
                )}
                <div>
                  <strong>Trace:</strong>
                  <pre className="mt-1 max-h-64 overflow-auto rounded bg-white p-2">
                    {JSON.stringify(result.trace, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      <footer className="mt-auto flex flex-col gap-2 border-t border-neutral-200 pt-4 text-xs text-neutral-500">
        <p className="font-medium text-neutral-700">
          Research prototype—not medical advice. Evidence and outputs require clinician/human review.
          Not for clinical use.
        </p>
        <p>
          Hybrid RAG agent — LangGraph planner and tool orchestration, BM25 keyword retrieval fused
          with vector/embedding retrieval via reciprocal rank fusion, source/applicability validation,
          conflict and evidence-gap detection, grounded LLM synthesis, citation and locator
          verification, and a final safety/QA pass.
        </p>
      </footer>
    </main>
  );
}
