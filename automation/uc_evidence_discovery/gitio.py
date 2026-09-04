"""All git interaction with the ``automation/uc-evidence-staging`` branch.

Design invariants (enforced here and in tests):

* the runner executes from the trusted ``main`` checkout; this module only ever runs
  ``git`` subprocesses, it never imports anything from ``--state-root``;
* every state read/write happens *inside* the ``--state-root`` worktree;
* only the explicit :data:`config.StatePaths.COMMIT_ALLOWLIST` is ever staged;
* ``main`` is never modified or pushed;
* the worktree is removed from the trusted ``main`` checkout with an explicit target path.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path

from . import config
from .errors import SafeStop, UntrustedStateRoot


def _git(args: list[str], cwd: Path, *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=check,
        capture_output=capture,
        text=True,
    )


# --------------------------------------------------------------------------------------------
# state-root validation
# --------------------------------------------------------------------------------------------
def resolve_state_root(raw: str) -> config.StatePaths:
    """Resolve and *fully validate* ``--state-root``.

    Raises :class:`UntrustedStateRoot` unless the path is an existing git worktree whose
    checked-out branch resolves to ``automation/uc-evidence-staging`` (directly, or via a
    local branch that tracks it), lives outside the trusted-code tree, and is not importable.
    """
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise UntrustedStateRoot(f"--state-root {path} does not exist")

    config.assert_outside_trusted_tree(path)
    config.assert_not_on_sys_path(path)

    try:
        inside = _git(["rev-parse", "--is-inside-work-tree"], cwd=path).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise UntrustedStateRoot(f"--state-root {path} is not a git work tree: {exc}") from exc
    if inside != "true":
        raise UntrustedStateRoot(f"--state-root {path} is not a git work tree")

    # Must be a linked worktree, not the primary checkout. git-dir of a linked worktree lives
    # under <common-dir>/worktrees/<name>; git-common-dir is the primary checkout's real .git.
    common_raw = _git(["rev-parse", "--git-common-dir"], cwd=path).stdout.strip()
    common = Path(common_raw)
    if not common.is_absolute():
        common = (path / common).resolve()
    git_dir = Path(_git(["rev-parse", "--git-dir"], cwd=path).stdout.strip())
    if "worktrees" not in str(git_dir):
        raise UntrustedStateRoot(
            f"--state-root {path} is the primary checkout, not a linked worktree"
        )

    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path).stdout.strip()
    if not _branch_is_staging(path, branch):
        raise UntrustedStateRoot(
            f"--state-root {path} is on {branch!r}, not {config.STAGING_BRANCH!r} "
            "(nor a local branch tracking it)"
        )
    # The primary checkout of *this specific worktree's own repo* -- not config.REPO_ROOT,
    # which would be wrong if the trusted code happens to be imported from elsewhere (e.g. a
    # test sandbox). worktree removal must run from here.
    primary_checkout = common.parent if common.name == ".git" else common
    return config.StatePaths(root=path, primary_checkout=primary_checkout)


def _branch_is_staging(path: Path, branch: str) -> bool:
    if branch == config.STAGING_BRANCH:
        return True
    if branch == "HEAD":  # detached
        # accept only if HEAD == origin/staging
        try:
            head = _git(["rev-parse", "HEAD"], cwd=path).stdout.strip()
            ref = _git(["rev-parse", config.STAGING_REMOTE_REF], cwd=path).stdout.strip()
            return head == ref
        except subprocess.CalledProcessError:
            return False
    try:
        upstream = _git(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], cwd=path
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return False
    return upstream in (f"origin/{config.STAGING_BRANCH}", config.STAGING_BRANCH)


# --------------------------------------------------------------------------------------------
# worktree lifecycle (invoked from the trusted main checkout)
# --------------------------------------------------------------------------------------------
def fetch_staging(repo_root: Path | None = None) -> None:
    repo_root = repo_root or config.REPO_ROOT
    _git(
        [
            "fetch",
            "origin",
            f"+refs/heads/{config.STAGING_BRANCH}:{config.STAGING_REMOTE_REF}",
        ],
        cwd=repo_root,
        check=False,
    )


def add_worktree(target: Path, repo_root: Path | None = None) -> None:
    """``git worktree add <target> <remote staging ref>`` from the main checkout."""
    repo_root = repo_root or config.REPO_ROOT
    proc = _git(
        ["worktree", "add", "--detach", str(target), config.STAGING_REMOTE_REF],
        cwd=repo_root,
        check=False,
    )
    if proc.returncode != 0:
        raise SafeStop(
            f"could not create staging worktree at {target}: {proc.stderr.strip() or proc.stdout.strip()}"
        )


def remove_worktree(target: Path, repo_root: Path | None = None) -> None:
    """Remove a staging worktree using an explicit target path, from the main checkout."""
    repo_root = repo_root or config.REPO_ROOT
    _git(["worktree", "remove", "--force", str(target)], cwd=repo_root, check=False)
    _git(["worktree", "prune"], cwd=repo_root, check=False)


# --------------------------------------------------------------------------------------------
# staging commit / push
# --------------------------------------------------------------------------------------------
def stage_paths(paths: config.StatePaths) -> list[str]:
    """``git add`` the explicit allowlist (``-f`` for the gitignored trio). Returns the list
    of allowlist entries that actually exist and were staged."""
    root = paths.root
    staged: list[str] = []
    for rel in config.StatePaths.COMMIT_ALLOWLIST:
        if _is_denied(rel):
            continue
        if not (root / rel).exists():
            continue
        args = ["add"]
        if rel in config.StatePaths.COMMIT_FORCE_PATHS:
            args.append("-f")
        args.append("--")
        args.append(rel)
        _git(args, cwd=root)
        staged.append(rel)
    return staged


def _is_denied(rel: str) -> bool:
    return any(rel == d or rel.startswith(d) for d in config.StatePaths.COMMIT_DENYLIST_SUBPATHS)


def has_staged_changes(paths: config.StatePaths) -> bool:
    out = _git(["diff", "--cached", "--name-only"], cwd=paths.root).stdout.strip()
    return bool(out)


def commit(paths: config.StatePaths, *, date: str | None = None) -> str | None:
    """Create the single atomic staging commit. Returns the commit sha, or ``None`` if there
    was nothing to commit (no empty commits, ever)."""
    if not has_staged_changes(paths):
        return None
    date = date or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    message = config.COMMIT_MESSAGE_TEMPLATE.format(date=date)
    _git(
        [
            "-c", f"user.name={config.BOT_NAME}",
            "-c", f"user.email={config.BOT_EMAIL}",
            "commit", "--no-verify", "-m", message,
        ],
        cwd=paths.root,
    )
    return _git(["rev-parse", "HEAD"], cwd=paths.root).stdout.strip()


def push(paths: config.StatePaths) -> None:
    """Push the local worktree HEAD to the staging branch only. Never pushes ``main``.

    Credentials are supplied out-of-band by ``actions/checkout`` (http.extraheader); this
    module never writes a token into a remote URL or logs one.
    """
    _git(
        ["push", "origin", f"HEAD:refs/heads/{config.STAGING_BRANCH}"],
        cwd=paths.root,
    )
