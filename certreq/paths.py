"""Feste Pfade. Das Teilnehmerpaket liegt gitignored unter vendor/ (Lizenz: nie ins Repo kopieren)."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = Path(os.environ.get("CERTIVITY_PKG_DIR", REPO_ROOT / "vendor" / "industrial-ai-hackathon"))
INDEX_PATH = PKG_DIR / "regulations" / "index.json"
PDF_DIR = PKG_DIR / "regulations" / "pdf"
CASES_DIR = PKG_DIR / "cases"
TOOLS_DIR = PKG_DIR / "tools"
OUT_DIR = REPO_ROOT / "out"  # gitignored: Ausgaben und Caches


def require_package() -> None:
    if not INDEX_PATH.exists():
        raise SystemExit(f"Teilnehmerpaket fehlt ({INDEX_PATH}). Erst scripts/setup <vorname> ausführen.")
