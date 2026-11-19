"use client";

import { useEffect, useState } from "react";
import type { ChatErrorResponse, ChatResponse, EvidenceProvenance, SourceCounts } from "./types";

// Source counts are always split by kind. There is no single "papers" number: a guideline, a study and a trial
// registry record are not the same thing, and trial records are never used as efficacy evidence.
function describeSources(c: SourceCounts): string {
  const parts = [
    c.guidelines ? `${c.guidelines} guideline${c.guidelines === 1 ? "" : "s"}` : null,
    c.studies ? `${c.studies} stud${c.studies === 1 ? "y" : "ies"}` : null,
    `${c.trialRecords} trial record${c.trialRecords === 1 ? "" : "s"}`,
    c.patientInformation ? `${c.patientInformation} patient-information page${c.patientInformation === 1 ? "" : "s"}` : null,
  ].filter(Boolean);
  return parts.join(", ");
}

const STATUS_STYLES: Record<string, string> = {
  answered: "border-teal-600/40 bg-white text-[#1b1b5e]",
  unsupported: "border-amber-400 bg-amber-50 text-amber-950",
  refused: "border-red-400 bg-red-50 text-red-950",
  llm_unavailable: "border-slate-300 bg-slate-100 text-slate-900",
  error: "border-red-400 bg-red-50 text-red-950",
};

// Current pilot size; replaced by the live count from /api/chat as soon as it loads.
const FALLBACK_SOURCE_COUNT = 22;

const SUGGESTED_QUESTIONS = [
  "What does fecal calprotectin tell me?",
  "How are biomarkers used to monitor UC?",
  "When might my clinician consider endoscopy?",
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<ChatErrorResponse | null>(null);
  const [showTrace, setShowTrace] = useState(false);
  const [evidence, setEvidence] = useState<EvidenceProvenance | null>(null);

  useEffect(() => {
    fetch("/api/chat")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setEvidence(d?.evidence ?? null))
      .catch(() => setEvidence(null));
  }, []);

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

  const sourceCount = evidence?.sourceCount ?? FALLBACK_SOURCE_COUNT;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-10 px-5 pb-8 pt-16 sm:px-8 sm:pt-24 lg:pt-32">
      <header className="flex flex-col gap-4">
        <h1 className="text-4xl font-extrabold tracking-tight text-[#1b1b5e] sm:text-6xl">
          Ulcerative Colitis Agent
        </h1>
        <p className="max-w-4xl text-base leading-relaxed text-[#1b1b5e] sm:text-lg">
          Evidence, not hearsay. Built on {sourceCount} medical sources spanning research papers, clinical
          guidelines, and patient guidance—including sources from the American Gastroenterological
          Association and Crohn’s &amp; Colitis UK.
        </p>
      </header>

      <form
        className="flex flex-col gap-3 sm:flex-row"
        onSubmit={(e) => {
          e.preventDefault();
          handleAsk();
        }}
      >
        <label htmlFor="question" className="sr-only">
          Ask a question about ulcerative colitis
        </label>
        <input
          id="question"
          type="text"
          className="min-h-14 flex-1 rounded-xl border-2 border-teal-600 bg-white px-5 text-lg text-[#1b1b5e] placeholder:text-[#4b4f86] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30"
          placeholder="Ask a question about ulcerative colitis…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="min-h-14 rounded-xl bg-teal-700 px-10 text-xl font-bold text-white hover:bg-teal-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/40 disabled:opacity-50"
        >
          {loading ? "Asking…" : "Ask"}
        </button>
      </form>

      <section aria-labelledby="try-asking">
        <h2 id="try-asking" className="mb-4 text-2xl font-extrabold text-[#1b1b5e]">
          Try asking
        </h2>
        <ul className="flex flex-col items-start gap-3">
          {SUGGESTED_QUESTIONS.map((q) => (
            <li key={q} className="max-w-full">
              <button
                type="button"
                onClick={() => askSuggested(q)}
                disabled={loading}
                className="max-w-full rounded-full border-2 border-teal-600 px-6 py-3 text-left text-lg text-[#1b1b5e] hover:bg-teal-600/10 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30 disabled:opacity-50"
              >
                {q}
              </button>
            </li>
          ))}
        </ul>
      </section>

      {error && (
        <div className="rounded-xl border border-red-400 bg-red-50 px-4 py-3 text-sm text-red-950" role="alert">
          <strong className="block">{error.error}</strong>
          {error.message}
          {typeof error.retryAfterSeconds === "number" && (
            <span> Retry after ~{Math.ceil(error.retryAfterSeconds)}s.</span>
          )}
        </div>
      )}

      {result && (
        <div className="flex flex-col gap-4" aria-live="polite">
          <section>
            <h2 className="mb-2 text-xl font-extrabold text-[#1b1b5e]">Answer</h2>
            <div className={`whitespace-pre-wrap rounded-xl border px-5 py-4 text-base leading-relaxed ${STATUS_STYLES[result.status] ?? "border-neutral-300 bg-neutral-50"}`}>
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
            <h2 className="mb-2 text-xl font-extrabold text-[#1b1b5e]">Evidence / Citations</h2>
            {result.answerSources && result.answerSources.total > 0 && (
              <p data-testid="answer-sources" className="mb-2 text-xs text-[#3d4170]">
                This answer draws on {result.answerSources.total} unique reviewed source
                {result.answerSources.total === 1 ? "" : "s"} ({describeSources(result.answerSources)}).
              </p>
            )}
            {result.citations.length === 0 ? (
              <p className="text-sm text-[#3d4170]">
                No sufficient evidence was retrieved for this query from the reviewed UC evidence set.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {result.citations.map((c) => (
                  <details key={c.number} className="rounded-xl border border-teal-600/40 bg-white px-4 py-3 text-sm text-[#1b1b5e]">
                    <summary className="cursor-pointer font-medium">
                      [{c.number}] {c.sourceTitle}
                    </summary>
                    <div className="mt-2 flex flex-col gap-1 text-[#1b1b5e]">
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
              <h2 className="mb-2 text-xl font-extrabold text-[#1b1b5e]">Conflict detector</h2>
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
              className="w-fit text-sm font-medium text-[#3d4170] underline"
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

      <footer className="mt-auto pt-16">
        <p className="text-sm text-[#437d73]">Research pilot—not medical advice.</p>
      </footer>
    </main>
  );
}
