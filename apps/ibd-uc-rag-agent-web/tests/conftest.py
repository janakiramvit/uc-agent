import sys
from pathlib import Path

# Mirror api/chat.py's own import setup: agent_core lives inside api/, and
# Vercel's Python runtime (and pytest here) need that directory on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

import pytest  # noqa: E402

from agent_core.evidence_loader import load_evidence_package  # noqa: E402
from agent_core.graph_v2 import build_graph_v2  # noqa: E402
from agent_core.retrieval import build_retriever  # noqa: E402


@pytest.fixture(scope="session")
def package():
    return load_evidence_package()


@pytest.fixture(scope="session")
def retriever(package):
    return build_retriever(package)


@pytest.fixture(scope="session")
def graph(package, retriever):
    return build_graph_v2(package, retriever)
