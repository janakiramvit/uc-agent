"""Local, read-only MCP server package for the UC RAG prototype.

Exposes exactly six read-only tools over the same eligibility-filtered
view used by the Streamlit app (``app.evidence_loader`` /
``app.retrieval``). No tool in this package writes, approves, edits, or
deletes anything -- see ``mcp_server/tools.py`` for the underlying
functions and ``mcp_server/server.py`` for the FastMCP wiring.
"""
