"""Deterministic, no-LLM daily UC evidence-discovery runner (Prompt v1.0.0).

This package is *trusted executable code*. It is always loaded and executed from the
repository's ``main`` checkout. Mutable evidence / checkpoint / journal / lock state lives on
the ``automation/uc-evidence-staging`` branch, which is materialised as a **separate git
worktree** and handed to the runner as ``--state-root``. The runner never adds ``--state-root``
to ``sys.path`` and never imports, execs or loads Python / configuration / executable files
from it.
"""

__all__ = ["__version__", "PROMPT_VERSION"]

__version__ = "1.0.0"
PROMPT_VERSION = "uc-daily-evidence-discovery-v1.0.0"
