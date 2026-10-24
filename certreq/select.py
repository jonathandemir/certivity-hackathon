"""Stufe 1: Welche Regelungen gelten für das Bauteil?

Baseline B0 (AP1): Wortüberlappung zwischen Spezifikation und Regelungstitel. Bewusst naiv, damit es eine
gemessene Referenz gibt; AP2 ersetzt diese Funktion. `forced` erlaubt, die Auswahl explizit vorzugeben
(Demo, Diagnose).
"""
from __future__ import annotations

import re

from .case import Case
from .regindex import Regulation, load_index

STOP = {
    "with", "from", "this", "that", "their", "into", "under", "other", "than", "devices", "device", "systems",
    "system", "vehicle", "vehicles", "approval", "regard", "respect", "category", "categories", "type", "types",
    "unit", "units", "and", "the", "for", "of", "on", "in", "to", "or", "by", "as", "at", "an", "a", "is", "are",
    "single", "module", "multiple", "combining", "confirm", "actual", "representative", "values", "typical",
    "material", "materials", "main", "parts", "product", "function", "apply", "across", "referenced",
}


def _stems(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower().replace("-", " "))
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if len(w) >= 3 and w not in STOP}


def select_regulations(case: Case, forced: list[str] | None = None) -> list[Regulation]:
    index = load_index()
    if forced:
        unknown = [r for r in forced if r not in index]
        if unknown:
            raise SystemExit(f"Nicht im Index: {unknown}. Erlaubt: {sorted(index)}")
        return [index[r] for r in forced]
    spec = _stems(case.spec_text)
    scored = [(len(spec & _stems(reg.title)), reg) for reg in index.values()]
    return [reg for score, reg in sorted(scored, key=lambda t: (-t[0], t[1].name)) if score >= 1]
