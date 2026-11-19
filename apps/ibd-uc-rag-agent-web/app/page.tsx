"use client";

import { useEffect, useRef, useState } from "react";
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
  answered: "border-transparent bg-white text-[#1b1b5e]",
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

type Message =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "agent"; response: ChatResponse }
  | { id: number; role: "error"; error: ChatErrorResponse };

function AgentCard({ response }: { response: ChatResponse }) {
  const [showTrace, setShowTrace] = useState(false);
  return (
    <div
      className={`max-w-[min(100%,46rem)] rounded-2xl border px-5 py-4 text-base leading-relaxed shadow-sm sm:text-lg ${STATUS_STYLES[response.status] ?? "border-neutral-300 bg-white"}`}
    >
      <div className="whitespace-pre-wrap">{response.answer}</div>

      {response.showSymptomCaveat && (
        <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          Note: symptoms and measurable intestinal inflammation do not always move together in ulcerative colitis.
          This information does not confirm or rule out active inflammation.
        </div>
      )}

      {response.conflictReport?.has_conflicts && (
        <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {response.conflictReport.conflicts.map((c, i) => (
            <div key={i} className="mb-1">
              <strong>{c.topic}:</strong> {c.reason} ({c.claimIds.join(", ")})
            </div>
          ))}
        </div>
      )}

      {response.citations.length > 0 && (
        <div className="mt-4 border-t border-[#1b1b5e]/15 pt-3 text-sm">
          {response.answerSources && response.answerSources.total > 0 && (
            <p data-testid="answer-sources" className="mb-2 text-[#3d4170]">
              This answer draws on {response.answerSources.total} unique reviewed source
              {response.answerSources.total === 1 ? "" : "s"} ({describeSources(response.answerSources)}).
            </p>
          )}
          <details className="group">
            <summary className="w-fit cursor-pointer list-none rounded-full border-2 border-teal-600 px-4 py-1.5 font-semibold text-teal-800 hover:bg-teal-600/10 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30">
              View evidence ({response.citations.length})
            </summary>
            <div className="mt-3 flex flex-col gap-3">
              {response.citations.map((c) => (
                <div key={c.number} className="rounded-xl border border-teal-600/30 px-4 py-3 text-[#1b1b5e]">
                  <div className="font-semibold">
                    [{c.number}] {c.sourceTitle}
                  </div>
                  <div className="mt-2 flex flex-col gap-1">
                    <div>
                      Claim ID: <code>{c.claimId}</code> · Evidence level: {c.evidenceLevel} · Confidence: {c.confidence}
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
                      <a className="break-all text-blue-800 underline" href={c.sourceUrl} target="_blank" rel="noreferrer">
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
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      <div className="mt-3">
        <button
          type="button"
          className="text-xs text-[#3d4170] underline"
          onClick={() => setShowTrace((v) => !v)}
          aria-expanded={showTrace}
        >
          {showTrace ? "Hide" : "Show"} developer / agent-trace panel
        </button>
        {showTrace && (
          <div className="mt-2 flex flex-col gap-2 rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-xs text-[#1b1b5e]">
            <div>
              <strong>Node sequence:</strong> {response.visitedNodes.join(" → ")}
            </div>
            <div>
              <strong>LLM provider / model:</strong> {response.llmProvider ?? "—"} / {response.llmModel ?? "—"}
            </div>
            <div>
              <strong>Vector retrieval status:</strong> {response.vectorRetrievalStatus ?? "—"}
            </div>
            {response.fusionReport && (
              <div>
                <strong>Fusion (RRF):</strong> vector used={String(response.fusionReport.vector_used)}; BM25=
                {response.fusionReport.bm25_ids.join(", ") || "(none)"}; vector=
                {response.fusionReport.vector_ids.join(", ") || "(none)"}; fused=
                {response.fusionReport.fused_ids.join(", ") || "(none)"}
              </div>
            )}
            {response.plan && (
              <div>
                <strong>Plan:</strong> topics={response.plan.identified_topics.join(", ") || "(none)"}; steps=
                {response.plan.steps.join(" → ")}
              </div>
            )}
            <div>
              <strong>Trace:</strong>
              <pre className="mt-1 max-h-64 overflow-auto rounded bg-white p-2">
                {JSON.stringify(response.trace, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [evidence, setEvidence] = useState<EvidenceProvenance | null>(null);
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/chat")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setEvidence(d?.evidence ?? null))
      .catch(() => setEvidence(null));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages, loading]);

  async function handleAsk(overrideQuery?: string) {
    const q = (overrideQuery ?? query).trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { id: nextId.current++, role: "user", text: q }]);
    setQuery("");
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      const data = await res.json();
      const msg: Message = res.ok
        ? { id: nextId.current++, role: "agent", response: data as ChatResponse }
        : { id: nextId.current++, role: "error", error: data as ChatErrorResponse };
      setMessages((m) => [...m, msg]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: nextId.current++,
          role: "error",
          error: { error: "network_error", message: "Could not reach the agent API." },
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const sourceCount = evidence?.sourceCount ?? FALLBACK_SOURCE_COUNT;
  const started = messages.length > 0;

  return (
    <main className="mx-auto flex h-dvh min-h-[40rem] w-full max-w-6xl flex-col gap-3 px-4 pb-3 pt-5 sm:gap-4 sm:px-8 sm:pt-6">
      <header className="border-b border-teal-600/30 pb-3">
        <h1 className="text-3xl font-extrabold tracking-tight text-[#1b1b5e] sm:text-4xl">Ulcerative Colitis Agent</h1>
        <p className="mt-1 max-w-4xl text-sm leading-snug text-[#1b1b5e] sm:text-base">
          Evidence, not hearsay. Built on {sourceCount} medical sources spanning research papers, clinical
          guidelines, and patient guidance—including sources from the American Gastroenterological Association and
          Crohn’s &amp; Colitis UK.
        </p>
      </header>

      <section
        aria-label="Conversation"
        aria-live="polite"
        className="min-h-0 flex-1 overflow-y-auto rounded-3xl bg-[#e2f2e9] p-4 sm:p-6"
      >
        <div className="flex flex-col gap-5">
          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.id} className="flex justify-end">
                <p className="max-w-[min(100%,32rem)] rounded-2xl bg-teal-700 px-5 py-3 text-base font-semibold text-white sm:text-lg">
                  {m.text}
                </p>
              </div>
            ) : m.role === "agent" ? (
              <div key={m.id} className="flex justify-start">
                <AgentCard response={m.response} />
              </div>
            ) : (
              <div key={m.id} className="flex justify-start">
                <div
                  role="alert"
                  className="max-w-[min(100%,46rem)] rounded-2xl border border-red-400 bg-red-50 px-5 py-4 text-base text-red-950"
                >
                  <strong className="block">{m.error.error}</strong>
                  {m.error.message}
                  {typeof m.error.retryAfterSeconds === "number" && (
                    <span> Retry after ~{Math.ceil(m.error.retryAfterSeconds)}s.</span>
                  )}
                </div>
              </div>
            ),
          )}
          {loading && (
            <div className="flex justify-start">
              <p className="rounded-2xl bg-white px-5 py-3 text-base text-[#3d4170]" role="status">
                Asking…
              </p>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </section>

      <section aria-labelledby="try-asking">
        <h2 id="try-asking" className="mb-2 text-lg font-extrabold text-[#1b1b5e] sm:text-xl">
          {started ? "Try another question" : "Try asking"}
        </h2>
        <ul className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <li key={q} className="max-w-full">
              <button
                type="button"
                onClick={() => handleAsk(q)}
                disabled={loading}
                className="max-w-full rounded-full border-2 border-teal-600 px-4 py-2 text-left text-sm text-[#1b1b5e] hover:bg-teal-600/10 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30 disabled:opacity-50 sm:text-base"
              >
                {q}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <form
        className="flex gap-3"
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
          className="min-h-12 min-w-0 flex-1 rounded-xl border-2 border-teal-600 bg-white px-4 text-base text-[#1b1b5e] placeholder:text-[#4b4f86] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30 sm:min-h-14 sm:text-lg"
          placeholder="Ask a question about ulcerative colitis…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="min-h-12 rounded-xl bg-teal-700 px-6 text-lg font-bold text-white hover:bg-teal-800 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/40 disabled:opacity-50 sm:min-h-14 sm:px-10 sm:text-xl"
        >
          Send
        </button>
      </form>

      <footer className="text-center">
        <p className="text-xs text-[#437d73]">Research pilot—not medical advice.</p>
      </footer>
    </main>
  );
}
