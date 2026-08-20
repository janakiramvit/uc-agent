import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from app.evidence_loader import load_evidence_package
from app.retrieval import build_retriever
from app.workflow import build_workflow


@pytest.fixture(scope="session")
def package():
    return load_evidence_package()


@pytest.fixture(scope="session")
def retriever(package):
    return build_retriever(package)


@pytest.fixture(scope="session")
def graph(package, retriever):
    return build_workflow(package, retriever)
