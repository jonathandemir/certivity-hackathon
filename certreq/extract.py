"""Stufe 2: Anforderungen aus den gewählten Regelungen.

Baseline B0 (AP1): jeder nummerierte Absatz der base-Version, der „shall" enthält, wird eine Anforderung
(Text = Absatztext, Seite = Startseite, Absatz = Label). Keine Relevanzfilterung, keine Zerlegung in einzelne
Pflichten; AP4 ersetzt diese Funktion.
"""
from __future__ import annotations

import re

from .pdf import parse_pdf
from .regindex import Regulation
from .submission import Requirement

SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)


def extract_requirements(regs: list[Regulation]) -> list[Requirement]:
    reqs: list[Requirement] = []
    for reg in regs:
        base = reg.base
        for pdf in base.pdfs:
            if not pdf.exists():
                raise SystemExit(f"PDF fehlt: {pdf}. Im Paket python3 tools/fetch_regulations.py ausführen.")
            for para in parse_pdf(pdf):
                if SHALL_RE.search(para.text):
                    reqs.append(Requirement(para.text, reg.name, base.label, para.page, para.label))
    return reqs
