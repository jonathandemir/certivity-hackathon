"""Stufe 2: Anforderungen aus den gewählten Regelungen.

Baseline B0 (AP1): jeder nummerierte Absatz der base-Version, der „shall" enthält, wird eine Anforderung
(Text = Absatztext, Seite = Startseite, Absatz = Label). Keine Zerlegung in einzelne Pflichten.
AP4: `filters` schaltet den Relevanzfilter entlang der Gliederung zu (certreq/relevance.py); Standard bleibt B0,
bis eine Messung besser ist (AGENTS.md §4).
"""
from __future__ import annotations

import re

from .pdf import parse_pdf
from .regindex import Regulation
from .relevance import relevant
from .submission import Requirement

SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)


def extract_requirements(regs: list[Regulation], spec_text: str = "", filters: tuple[str, ...] = ()) -> list[Requirement]:
    reqs: list[Requirement] = []
    for reg in regs:
        base = reg.base
        for pdf in base.pdfs:
            if not pdf.exists():
                raise SystemExit(f"PDF fehlt: {pdf}. Im Paket python3 tools/fetch_regulations.py ausführen.")
            paras = parse_pdf(pdf)
            keep = relevant(paras, filters, spec_text) if filters else [True] * len(paras)
            for para, ok in zip(paras, keep):
                if ok and SHALL_RE.search(para.text):
                    reqs.append(Requirement(para.text, reg.name, base.label, para.page, para.label))
    return reqs
