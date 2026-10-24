"""Git-Stand eines Laufs, aus git gelesen (nie erfunden): <branch>@<kurzhash>, sauber, gepusht."""
from __future__ import annotations

import subprocess

from .paths import REPO_ROOT


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()


def git_state() -> dict:
    branch = _git("symbolic-ref", "--short", "-q", "HEAD") or "detached"
    dirty = _git("status", "--porcelain").splitlines()
    return {
        "commit": f"{branch}@{_git('rev-parse', '--short', 'HEAD')}",
        "full_hash": _git("rev-parse", "HEAD"),
        "clean": not dirty,
        "pushed": bool(_git("branch", "-r", "--contains", "HEAD")),
        "dirty_files": dirty[:20],
    }
