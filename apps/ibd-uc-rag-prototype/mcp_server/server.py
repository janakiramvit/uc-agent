"""Local MCP server exposing exactly six read-only tools over the UC
evidence set.

Run standalone (stdio transport) with:

    python -m mcp_server.server

Tools exposed (and no others):
    - search_uc_claims(query, topic=None)
    - get_claim(claim_id)
    - get_source(source_id)
    - list_supported_topics()
    - check_claim_applicability(claim_id)
    - get_evidence_gaps()

This server has no write/approve/edit/delete capability of any kind. It
reuses ``app.evidence_loader`` / ``app.retrieval`` directly -- it does not
duplicate any filtering or retrieval logic.
"""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from app.evidence_loader import load_evidence_package
from app.retrieval import build_retriever
from mcp_server.tools import MCPToolContext
from mcp_server.tools import check_claim_applicability as _check_claim_applicability
from mcp_server.tools import get_claim as _get_claim
from mcp_server.tools import get_evidence_gaps as _get_evidence_gaps
from mcp_server.tools import get_source as _get_source
from mcp_server.tools import list_supported_topics as _list_supported_topics
from mcp_server.tools import search_uc_claims as _search_uc_claims

mcp = FastMCP("ibd-uc-evidence")

_ctx: MCPToolContext | None = None


def get_context() -> MCPToolContext:
    """Lazily build (and cache) the shared package/retriever context."""
    global _ctx
    if _ctx is None:
        package = load_evidence_package()
        retriever = build_retriever(package)
        _ctx = MCPToolContext(package=package, retriever=retriever)
    return _ctx


@mcp.tool()
def search_uc_claims(query: str, topic: Optional[str] = None) -> dict[str, Any]:
    """Search UC-eligible claims (read-only) matching a query, optionally
    restricted to a topic. Never returns Crohn's-only or excluded claims."""
    return _search_uc_claims(get_context(), query, topic)


@mcp.tool()
def get_claim(claim_id: str) -> dict[str, Any]:
    """Return one claim's full fields if and only if it is UC-eligible.
    Refuses Crohn's-only and excluded claim IDs, even when asked directly."""
    return _get_claim(get_context(), claim_id)


@mcp.tool()
def get_source(source_id: str) -> dict[str, Any]:
    """Return source metadata for a given sourceId."""
    return _get_source(get_context(), source_id)


@mcp.tool()
def list_supported_topics() -> dict[str, Any]:
    """List the topic vocabulary that actually has UC-eligible claims today."""
    return _list_supported_topics(get_context())


@mcp.tool()
def check_claim_applicability(claim_id: str) -> dict[str, Any]:
    """Return whether a claim is UC-eligible, Crohn's-only, or excluded, with reason."""
    return _check_claim_applicability(get_context(), claim_id)


@mcp.tool()
def get_evidence_gaps() -> dict[str, Any]:
    """Return the known unsupported topics (zero UC-eligible claims)."""
    return _get_evidence_gaps(get_context())


if __name__ == "__main__":
    mcp.run()
