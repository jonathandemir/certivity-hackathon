"""AP5: Explosionszeichnung → Produkt, Lage am Fahrzeug, Teile mit Funktion und Technik.

Die Beschreibung wird als Text an die Spezifikation angehängt (mode "on") oder ersetzt sie (mode "only": Fall mit nur
einer Zeichnung, Demo-Pflicht R3). Danach laufen Auswahl (AP2) und Extraktion (AP4) unverändert.
Das Modell soll nur beschreiben, was die Zeichnung zeigt, mit Bildbeleg je Teil; Regelungen nennt es nicht (die
Auswahl ist Aufgabe von AP2, und so bleibt die Stufe auch bei beschrifteten Zeichnungen sauber getrennt).
"""
from __future__ import annotations

from dataclasses import replace

from . import llm
from .case import Case

MODES = ("auto", "off", "on", "only")

SYSTEM = """You are an automotive design engineer reading a technical drawing (for example an exploded view or a patent
figure) of a vehicle component. Describe only what the drawing shows or strongly implies:
- the product and where on the vehicle it is mounted (front, rear, side, interior, ...),
- every distinguishable part or functional unit: its likely name, its function, its technology or material class
  (e.g. LED array, bulb, reflector, transparent lens, retro-reflective prism plate, electronic board, plastic housing,
  metal bracket, sensor, fastener) and the visual evidence for it,
- uncertainties: what cannot be determined from the drawing alone.
Use the specification text, if given, only to name parts consistently; do not invent parts that are not visible.
Do not cite or guess regulations."""

SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["product", "vehicle_location", "parts", "uncertainties"],
    "properties": {
        "product": {"type": "string"},
        "vehicle_location": {"type": "string"},
        "parts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "function", "technology", "evidence"],
            "properties": {"name": {"type": "string"}, "function": {"type": "string"},
                           "technology": {"type": "string"}, "evidence": {"type": "string"}}}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
}


def describe(case: Case, use_spec: bool = True) -> dict:
    """Liest alle Bilder des Falls. use_spec=False: ohne den Spec-Text (reiner Zeichnungsfall)."""
    user = "Describe the drawing(s)."
    if use_spec and case.spec_text.strip():
        user += f"\n\nSpecification text for consistent naming:\n{case.spec_text.strip()}"
    return llm.ask_json(SYSTEM, user, SCHEMA, name="drawing", model=llm.STRONG_MODEL, effort="medium",
                        images=list(case.images))


def render(desc: dict) -> str:
    lines = ["## From the drawing (read automatically)", f"Product: {desc['product']}",
             f"Location on vehicle: {desc['vehicle_location']}", "Parts:"]
    lines += [f"- {p['name']}: {p['function']} ({p['technology']})" for p in desc["parts"]]
    if desc["uncertainties"]:
        lines.append("Uncertain from the drawing: " + "; ".join(desc["uncertainties"]))
    return "\n".join(lines)


def apply(case: Case, mode: str = "auto") -> tuple[Case, dict | None]:
    """Gibt den (ggf. ergänzten) Fall und die Zeichnungsbeschreibung (für .meta.json) zurück.
    auto: mit Spec wie off (E016-a; Zeichnung brachte zusätzlich nichts, E018-a), ohne Spec wie only (E017-a)."""
    if mode not in MODES:
        raise SystemExit(f"Unbekannter Vision-Modus {mode!r}, erlaubt: {MODES}")
    if mode == "auto":
        mode = "off" if case.spec_text.strip() else "only"
    if mode == "off" or not case.images:
        if mode == "only" and not case.images:
            raise SystemExit(f"--vision only, aber keine Zeichnung in {case.folder}")
        return case, None
    desc = describe(case, use_spec=(mode == "on"))
    text = render(desc)
    spec = text if mode == "only" or not case.spec_text.strip() else f"{case.spec_text.rstrip()}\n\n{text}"
    return replace(case, spec_text=spec), desc
