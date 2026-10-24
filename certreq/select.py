"""Stufe 1: Welche Regelungen gelten für das Bauteil?

mode="b0" (AP1, Referenz E001): Wortüberlappung zwischen Spezifikation und Regelungstitel. Bewusst naiv.
mode="llm" (AP2): Das LLM (llm.STRONG_MODEL) bekommt die Spezifikation und von allen Regelungen des Index einen
Steckbrief (Titel, Einleitung, Geltungsbereich aus der base-PDF) und wählt nach allgemeinen Prinzipien der
Typgenehmigung: Bauteil selbst, Anbau am Fahrzeug, querschnittliche Regelungen wegen Technik/Lage/Verkehrsteilnehmern,
konsolidierte statt ersetzter Regelungen (die PDFs sagen das selbst, z. B. R148 „combines … Nos. 4, 6, 7, 23 …"),
Fahrzeugklasse beachten. Keine fallspezifischen Regeln, damit es auch für den Held-out (Frontstoßfänger) trägt.
mode="llm2" (AP2b): wie llm, aber das Modell gibt je Regelung zusätzlich an, ob der Auslöser in der Spec steht
(`stated_in_spec`) und wo die Anforderungen liegen (`requirement_locus`: component / installation / vehicle-only).
Der Code verwirft Annahmen („if the radar is used for AEBS …") und reine Fahrzeugebene (Crash der Insassen,
Cybersecurity-Management …). Anlass: Robustheitsprüfung am synthetischen Stoßfänger (LEARNINGS).
`forced` gibt die Auswahl explizit vor (Demo, Diagnose). `explain` (Liste) bekommt je Regelung Rolle und Begründung.
"""
from __future__ import annotations

import re
from functools import lru_cache

from . import llm
from .case import Case
from .regindex import Regulation, load_index

STOP = {
    "with", "from", "this", "that", "their", "into", "under", "other", "than", "devices", "device", "systems",
    "system", "vehicle", "vehicles", "approval", "regard", "respect", "category", "categories", "type", "types",
    "unit", "units", "and", "the", "for", "of", "on", "in", "to", "or", "by", "as", "at", "an", "a", "is", "are",
    "single", "module", "multiple", "combining", "confirm", "actual", "representative", "values", "typical",
    "material", "materials", "main", "parts", "product", "function", "apply", "across", "referenced",
}
MODES = ("b0", "llm", "llm2")
BRIEF_PAGES = 6
INTRO_CHARS = 500
SCOPE_CHARS = 800

SYSTEM = """You are a type-approval (homologation) engineer for UNECE vehicle regulations.
Input: the specification of a vehicle component and a catalogue of UN Regulations (title, introduction, scope).
Select every regulation that contains engineering requirements this component or its integration on the vehicle
must fulfil. Principles:
1. Component approval: regulations whose scope covers the component itself or any device or function it contains.
2. Installation: regulations that govern how such devices are installed on vehicles of the given category.
3. Cross-cutting: regulations that apply because of the component's technology (for example electrical or
   electronic parts), its materials, its position on the vehicle or its interaction with other road users.
4. Consolidation: if a regulation states that it combines or replaces older regulations that are also in the
   catalogue, select the consolidated regulation and not the older ones.
5. Vehicle category: skip regulations that only cover other vehicle categories than the one in the specification.
6. A missed relevant regulation costs more than an extra marginal one, but do not add regulations "to be safe" when
   the component clearly falls outside their scope.
For each selected regulation give its role and a one-sentence reason grounded in the specification. Also list up to
five regulations you considered but rejected, with the reason."""


SYSTEM2 = SYSTEM + """
For each selected regulation also state:
- trigger: the feature of the specification that makes it apply (quote or close paraphrase),
- stated_in_spec: false if it only applies under an assumption the specification does not state
  (for example "if the radar is used for emergency braking" or "if standardised light sources are used"),
- requirement_locus: "component" if the regulation sets requirements that the component's design, marking or
  performance must meet, including vehicle tests whose result depends on this component (for example impact tests of
  the structure it forms); "installation" if it governs how the component or its devices are mounted, positioned or
  connected on the vehicle; "vehicle-only" if its requirements concern other vehicle systems, the vehicle as a whole
  independently of this component, or the manufacturer's organisation and processes."""


def _stems(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower().replace("-", " "))
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if len(w) >= 3 and w not in STOP}


def _select_b0(case: Case, index: dict[str, Regulation]) -> list[Regulation]:
    spec = _stems(case.spec_text)
    scored = [(len(spec & _stems(reg.title)), reg) for reg in index.values()]
    return [reg for score, reg in sorted(scored, key=lambda t: (-t[0], t[1].name)) if score >= 1]


@lru_cache(maxsize=None)
def brief(name: str) -> str:
    """Steckbrief einer Regelung: Titel, Einleitung und Geltungsbereich aus den ersten Seiten der base-PDF."""
    import pymupdf

    reg = load_index()[name]
    lines: list[str] = []
    with pymupdf.open(str(reg.base.pdfs[0])) as doc:
        for page in list(doc)[:BRIEF_PAGES]:
            lines += page.get_text().splitlines()
    # Kopfzeile und Certivity-Hinweis („… rendered by Certivity …", „Role in the hackathon: …") entfernen
    skip = re.compile(r"^UN .+(version \S+ \| page|\(version \S+\)$)|rendered by Certivity|^the bottom of every page|"
                      r"^Role in the hackathon")
    body = re.sub(r"\s+", " ", " ".join(ln for ln in lines if not skip.search(ln.strip())))
    intro = body[:INTRO_CHARS]
    m = re.search(r"\b(SCOPE|Scope)\b|\bapplies to\b", body)
    scope = body[m.start(): m.start() + SCOPE_CHARS] if m and m.start() >= INTRO_CHARS else ""
    combined = re.search(r"[^.]*\b(combines|replaces|supersedes)\b[^.]*\.", body[:6000])
    parts = [f"Title: {reg.title}", f"Start: {intro}"]
    if scope:
        parts.append(f"Scope: {scope}")
    if combined and combined.group(0) not in intro + scope:
        parts.append(f"Note: {combined.group(0).strip()}")
    return "\n".join(parts)


def _select_llm(case: Case, index: dict[str, Regulation], explain: list | None, strict: bool = False) -> list[Regulation]:
    names = sorted(index)
    catalogue = "\n\n".join(f"### {n}\n{brief(n)}" for n in names)
    user = f"Component specification:\n{case.spec_text.strip()}\n\nCatalogue of UN Regulations:\n\n{catalogue}"
    reg_enum = {"type": "string", "enum": names}
    item = {"regulation": reg_enum, "role": {"type": "string", "enum": ["component", "installation", "cross-cutting"]},
            "reason": {"type": "string"}}
    if strict:
        item |= {"trigger": {"type": "string"}, "stated_in_spec": {"type": "boolean"},
                 "requirement_locus": {"type": "string", "enum": ["component", "installation", "vehicle-only"]}}
    schema = {"type": "object", "additionalProperties": False, "required": ["selected", "rejected"], "properties": {
        "selected": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                "required": list(item), "properties": item}},
        "rejected": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                                "required": ["regulation", "reason"],
                                                "properties": {"regulation": reg_enum, "reason": {"type": "string"}}}}}}
    ans = llm.ask_json(SYSTEM2 if strict else SYSTEM, user, schema, name="selection", model=llm.STRONG_MODEL, effort="high")
    chosen, seen, dropped = [], set(), []
    for item in ans["selected"]:
        if strict and (not item["stated_in_spec"] or item["requirement_locus"] == "vehicle-only"):
            why = "Annahme, nicht in der Spec" if not item["stated_in_spec"] else "nur Fahrzeugebene"
            dropped.append({"regulation": item["regulation"], "role": "rejected",
                            "reason": f"verworfen ({why}): {item['reason']}"})
            continue
        if item["regulation"] in index and item["regulation"] not in seen:
            seen.add(item["regulation"])
            chosen.append(index[item["regulation"]])
            if explain is not None:
                explain.append({"regulation": item["regulation"], "role": item["role"], "reason": item["reason"]})
    if explain is not None:
        explain += dropped + [{"regulation": r["regulation"], "role": "rejected", "reason": r["reason"]}
                              for r in ans["rejected"]]
    return chosen


def select_regulations(case: Case, forced: list[str] | None = None, mode: str = "b0",
                       explain: list | None = None) -> list[Regulation]:
    index = load_index()
    if forced:
        unknown = [r for r in forced if r not in index]
        if unknown:
            raise SystemExit(f"Nicht im Index: {unknown}. Erlaubt: {sorted(index)}")
        return [index[r] for r in forced]
    if mode in ("llm", "llm2"):
        return _select_llm(case, index, explain, strict=mode == "llm2")
    if mode != "b0":
        raise SystemExit(f"Unbekannter Auswahlmodus {mode!r}, erlaubt: {MODES}")
    return _select_b0(case, index)
