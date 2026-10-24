"""regulations/index.json: welche Regelungen zitiert werden dürfen, ihre Versionen und PDF-Pfade."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import paths


@dataclass(frozen=True)
class Version:
    regulation: str  # exakt wie im Index, z. B. "UN R148"
    role: str  # "base" oder "latest"
    label: str  # version_label, z. B. "1.6.0"
    pdfs: tuple[Path, ...]


@dataclass(frozen=True)
class Regulation:
    name: str
    title: str
    versions: tuple[Version, ...]

    def version(self, role: str = "base") -> Version | None:
        return next((v for v in self.versions if v.role == role), None)

    @property
    def base(self) -> Version:
        v = self.version("base")
        if v is None:
            raise KeyError(f"{self.name} hat keine base-Version")
        return v


def pdf_slug(regulation: str) -> str:
    """Ordnername wie in tools/fetch_regulations.py."""
    return "_".join(regulation.replace("/", " ").split())


@lru_cache(maxsize=None)
def load_index(index_path: Path = paths.INDEX_PATH) -> dict[str, Regulation]:
    paths.require_package()
    entries = json.loads(Path(index_path).read_text(encoding="utf-8"))
    out: dict[str, Regulation] = {}
    for e in entries:
        versions = []
        for v in e.get("versions", []):
            folder = paths.PDF_DIR / pdf_slug(e["regulation"]) / v["role"]
            pdfs = tuple(folder / f["name"] for f in v.get("files", []))
            versions.append(Version(e["regulation"], v["role"], v["version_label"], pdfs))
        out[e["regulation"]] = Regulation(e["regulation"], e.get("title", ""), tuple(versions))
    return out
