"""Ein Fall = ein Ordner unter cases/ mit Spezifikation (Markdown/Text) und/oder Explosionszeichnung (Bild)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

TEXT_SUFFIXES = {".md", ".txt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
IGNORED = {"expected.json"}  # die Antwort des Worked Example darf nie in die Pipeline fließen


@dataclass
class Case:
    case_id: str
    folder: Path
    spec_text: str = ""
    images: list[Path] = field(default_factory=list)


def load_case(folder: str | Path) -> Case:
    folder = Path(folder)
    if not folder.is_dir():
        raise SystemExit(f"Fall-Ordner nicht gefunden: {folder}")
    texts, images = [], []
    for p in sorted(folder.iterdir()):
        if p.name in IGNORED or not p.is_file():
            continue
        if p.suffix.lower() in TEXT_SUFFIXES:
            texts.append(p.read_text(encoding="utf-8"))
        elif p.suffix.lower() in IMAGE_SUFFIXES:
            images.append(p)
    if not texts and not images:
        raise SystemExit(f"Weder Spezifikation noch Zeichnung in {folder}")
    return Case(case_id=folder.name, folder=folder, spec_text="\n\n".join(texts), images=images)
