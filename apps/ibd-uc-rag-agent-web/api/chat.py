"""POST /api/chat -- Vercel Python serverless function entrypoint.

Wires the Next.js frontend to the full graph_v2 LangGraph pipeline
(planner -> classifier -> BM25 + vector retrieval -> applicability check
-> conflict detection -> gap detection -> safety boundaries -> real-LLM
grounded synthesis -> safety critic -> citation verifier -> QA pass).

Engineering requirements implemented here:
  - rate limiting (best-effort, see agent_core.rate_limit for the honest
    caveat about serverless instance isolation)
  - a request-size cap (cost control) before anything reaches the LLM
  - an overall wall-clock timeout around graph execution, independent of
    the per-call LLM client timeout, so a hung retrieval/tool step can't
    hang the whole request indefinitely
  - error handling that returns a structured JSON error instead of a
    bare 500 with no explanation, and never fabricates a 200 success
"""

import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Vercel's Python runtime does not add this file's own directory to
# sys.path automatically, so the sibling `agent_core` package needs this
# to be importable (same pattern used by the reference architecture).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core.evidence_loader import load_evidence_package  # noqa: E402
from agent_core.graph_v2 import build_graph_v2, run_graph_v2  # noqa: E402
from agent_core.rate_limit import (  # noqa: E402
    DEFAULT_MAX_QUERY_CHARS,
    QueryTooLong,
    RateLimitExceeded,
    check_query_length,
    check_rate_limit,
)
from agent_core.retrieval import build_retriever  # noqa: E402

REQUEST_TIMEOUT_SECONDS = 45  # overall wall-clock budget for one /api/chat request

_package = None
_retriever = None
_graph = None
_executor = ThreadPoolExecutor(max_workers=4)


def _pipeline():
    """Lazily build the evidence package / retriever / compiled graph once
    per warm function instance, not once per request."""
    global _package, _retriever, _graph
    if _graph is None:
        _package = load_evidence_package()
        _retriever = build_retriever(_package)
        _graph = build_graph_v2(_package, _retriever)
    return _graph


def _client_key(handler: "handler") -> str:
    forwarded = handler.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return handler.client_address[0] if handler.client_address else "unknown"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        client_key = _client_key(self)
        try:
            check_rate_limit(client_key)
        except RateLimitExceeded as exc:
            self._send_json(
                429,
                {"error": "rate_limited", "message": str(exc), "retryAfterSeconds": exc.retry_after_seconds},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(body or b"{}")
            query = (payload.get("query") or "").strip()
            topic_filter = payload.get("topicFilter") or None

            if not query:
                self._send_json(400, {"error": "bad_request", "message": "`query` is required."})
                return

            check_query_length(query)

            graph = _pipeline()
            future = _executor.submit(run_graph_v2, graph, query, topic_filter)
            try:
                result = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
            except FutureTimeoutError:
                self._send_json(
                    504,
                    {
                        "error": "timeout",
                        "message": f"The agent pipeline did not complete within {REQUEST_TIMEOUT_SECONDS}s.",
                    },
                )
                return

            self._send_json(200, self._to_response(result))
        except QueryTooLong as exc:
            self._send_json(400, {"error": "query_too_long", "message": str(exc), "maxChars": DEFAULT_MAX_QUERY_CHARS})
        except Exception as exc:  # noqa: BLE001 - top-level handler must never crash without a response
            self._send_json(500, {"error": "internal_error", "message": str(exc), "trace": traceback.format_exc()})

    def do_GET(self):
        self._send_json(200, {"status": "ok"})

    @staticmethod
    def _to_response(result: dict) -> dict:
        return {
            "status": result.get("status"),
            "answer": result.get("answer"),
            "citations": result.get("citations", []),
            "showSymptomCaveat": result.get("show_symptom_caveat", False),
            "plan": result.get("plan"),
            "conflictReport": result.get("conflict_report"),
            "vectorRetrievalStatus": result.get("vector_retrieval_status"),
            "fusionReport": result.get("fusion_report"),
            "llmProvider": result.get("llm_provider"),
            "llmModel": result.get("llm_model"),
            "trace": result.get("trace", []),
            "visitedNodes": result.get("visited_nodes", []),
        }

    def _send_json(self, status: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
