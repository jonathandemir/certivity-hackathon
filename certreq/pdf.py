"""Regulierungs-PDF → nummerierte Absätze mit Seite.

Die PDFs sind von Certivity gerendert: Kopfzeile „UN R148, version 1.6.0 | page 14 of 48", jeder Absatz beginnt
mit seiner Nummer („4.8.1.7. Text"). Absatzlabels folgen der Schreibweise der Referenz: „4.8.1.7",
„Annex 9 3.1", „Annex 4 Part 1 1.2". Appendices werden als „Annex 4 Appendix 1 2.1" gelabelt (Format der Referenz
dafür unbekannt; Seite zählt ohnehin, wenn das Label nicht passt).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

HEADER_RE = re.compile(r"^UN .+, version \S+ \| page \d+ of \d+$")
# Absatzbeginn: Nummer mit abschließendem Punkt, dann Text. Abbildungsnummern ("16") und Messwerte ("13.5 V") fallen raus.
PARA_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,7})\.\s+(\S.*)$")
# Anhang-Überschrift: "Annex 10 Method(s) ...", "Annex 4 - Appendix 1", "Annex 2A Information ...", "Annex 3"
ANNEX_RE = re.compile(r"^Annex\s+(\d{1,2})([A-Z]?)(?:\s*[-–]\s*Appendix\s+(\d{1,2}))?(?:\s+[A-Z(\"].*)?$")
PART_RE = re.compile(r"^Part\s+(\d{1,2})\s*[-–:]\s*\S")


@dataclass
class Paragraph:
    label: str  # wie in der Referenz, z. B. "4.8.1.7" oder "Annex 9 3.1"
    number: str  # nur die Nummer, z. B. "3.1"
    page: int  # Startseite, 1-basiert
    end_page: int
    text: str

    @property
    def in_annex(self) -> bool:
        return self.label.startswith("Annex ")


def _context_label(annex: str | None, appendix: str | None, part: str | None) -> str:
    if annex is None:
        return ""
    label = f"Annex {annex}"
    if appendix:
        label += f" Appendix {appendix}"
    if part:
        label += f" Part {part}"
    return label + " "


def _is_next_annex(m: re.Match, annex_no: int, annex: str | None) -> bool:
    """Anhänge kommen der Reihe nach. Tabellenzellen wie „Annex 10 (values in" oder ein einzelnes „Annex 5"
    mitten im Haupttext würden sonst den Kontext kapern (gesehen in UN R150 S. 5 und 14)."""
    num, letter, appendix = int(m.group(1)), m.group(2), m.group(3)
    if annex_no < num <= annex_no + 2:  # nächster Anhang, ein reservierter darf fehlen
        return True
    return num == annex_no and bool(appendix or (letter and f"{num}{letter}" != annex))


@lru_cache(maxsize=None)
def parse_pdf(path: str | Path) -> tuple[Paragraph, ...]:
    import pymupdf  # erst hier importiert, damit der Rest ohne PyMuPDF testbar bleibt

    paras: list[Paragraph] = []
    annex = appendix = part = None
    annex_no = 0
    cur: Paragraph | None = None
    with pymupdf.open(str(path)) as doc:
        for pno, page in enumerate(doc, start=1):
            for raw in page.get_text().splitlines():
                line = raw.strip()
                if not line or HEADER_RE.match(line):
                    continue
                m = ANNEX_RE.match(line)
                if m and _is_next_annex(m, annex_no, annex):
                    annex_no = int(m.group(1))
                    annex, appendix, part = m.group(1) + m.group(2), m.group(3), None
                    cur = None
                    continue
                m = PART_RE.match(line)
                if m and annex is not None:
                    part, cur = m.group(1), None
                    continue
                m = PARA_RE.match(line)
                if m:
                    number = m.group(1)
                    cur = Paragraph(_context_label(annex, appendix, part) + number, number, pno, pno, m.group(2))
                    paras.append(cur)
                elif cur is not None:
                    cur.text += " " + line
                    cur.end_page = pno
    return tuple(paras)
