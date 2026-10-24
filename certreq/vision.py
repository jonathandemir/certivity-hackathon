"""AP5: Explosionszeichnung → Produkt, Lage am Fahrzeug, Teile mit Funktion und Technik.

Die Beschreibung wird als Text an die Spezifikation angehängt (mode "on") oder ersetzt sie (mode "only": Fall mit nur
einer Zeichnung, Demo-Pflicht R3). Danach laufen Auswahl (AP2) und Extraktion (AP4) unverändert.
Das Modell soll nur beschreiben, was die Zeichnung zeigt, mit Bildbeleg je Teil; Regelungen nennt es nicht (die
Auswahl ist Aufgabe von AP2, und so bleibt die Stufe auch bei beschrifteten Zeichnungen sauber getrennt).
"""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

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


# Schalter --infer-category (E043-a): Ohne Spec steht die Fahrzeugklasse nirgends; --select llm2 verwirft dann die
# Anbau-Regelung als Annahme (E042-a: R48 fehlt, 56 von 190 Gold-Anforderungen). Das Modell soll die Klasse aus Produktart
# und Bauform ableiten und als Ableitung kennzeichnen.
CATEGORY_RULE = """
- the vehicle category this component is most likely made for (UNECE categories such as L3 motorcycle, M1 passenger
  car, N1 light commercial vehicle, N3 heavy truck, O trailer), inferred from the product type, size and design shown;
  give the category code and name and a short reason, and say that it is inferred."""


def describe(case: Case, use_spec: bool = True, infer_category: bool = False) -> dict:
    """Liest alle Bilder des Falls. use_spec=False: ohne den Spec-Text (reiner Zeichnungsfall).
    infer_category: zusätzlich die wahrscheinliche Fahrzeugklasse (Feld vehicle_category)."""
    user = "Describe the drawing(s)."
    if use_spec and case.spec_text.strip():
        user += f"\n\nSpecification text for consistent naming:\n{case.spec_text.strip()}"
    system, schema = SYSTEM, SCHEMA
    if infer_category:
        system = SYSTEM.replace("\n- uncertainties:", CATEGORY_RULE + "\n- uncertainties:")
        schema = {**SCHEMA, "required": SCHEMA["required"] + ["vehicle_category"],
                  "properties": {**SCHEMA["properties"], "vehicle_category": {"type": "string"}}}
    return llm.ask_json(system, user, schema, name="drawing", model=llm.STRONG_MODEL, effort="medium",
                        images=list(case.images))


def render(desc: dict) -> str:
    lines = ["## From the drawing (read automatically)", f"Product: {desc['product']}",
             f"Location on vehicle: {desc['vehicle_location']}"]
    if desc.get("vehicle_category"):
        lines.append(f"Vehicle category (inferred from the drawing): {desc['vehicle_category']}")
    lines.append("Parts:")
    lines += [f"- {p['name']}: {p['function']} ({p['technology']})" for p in desc["parts"]]
    if desc["uncertainties"]:
        lines.append("Uncertain from the drawing: " + "; ".join(desc["uncertainties"]))
    return "\n".join(lines)


REGIONS_SYSTEM = """You locate the parts of a technical drawing (exploded view or patent figure) of a vehicle component.
Return every distinguishable part or functional unit that is drawn. Use callout labels and their leader lines (the dot
at the end of a leader line marks the part) where present. For each part give:
- label: its name as written in the drawing, otherwise a short descriptive name,
- note: the callout text that belongs to the label (verbatim, without the label), or "" if there is none,
- box: the bounding box of the drawn part itself, not of its label text, as x0, y0, x1, y1 in thousandths of the image
  width and height (0 = left or top edge, 1000 = right or bottom edge), tight around the part's outline,
- spec_parts: the listed specification parts that this drawn part implements or belongs to (may be empty).
Only return parts you can see; do not invent parts and do not cite regulations."""


def spec_parts(spec_text: str) -> list[str]:
    """Bauteile aus dem Abschnitt „Main Parts" der Spec, gleiche Regel wie demo/prepare.parse_spec (gleiche Namen)."""
    cur, out = None, []
    for line in spec_text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip().lower()
        elif cur and "main part" in cur and re.match(r"^\s*[-*]\s+\S", line):
            out.append(re.sub(r"^\s*[-*]\s*", "", line).strip())
    return out


def _image_size(path: Path) -> tuple[int, int]:
    import pymupdf
    pm = pymupdf.Pixmap(str(path))
    return pm.width, pm.height


def regions(case: Case) -> dict | None:
    """Bildregion je gezeichnetem Teil (Pixel der ersten Zeichnung) und Zuordnung zu den Bauteilen der Spec.
    Ändert die Pipeline nicht: nur für die Demo (Teile der Zeichnung ↔ Spec-Bauteile) und für die Prüfung von Hand."""
    if not case.images:
        return None
    img = case.images[0]
    width, height = _image_size(img)
    names = spec_parts(case.spec_text)
    coord = {"type": "integer"}
    box = {"type": "object", "additionalProperties": False, "required": ["x0", "y0", "x1", "y1"],
           "properties": {k: coord for k in ("x0", "y0", "x1", "y1")}}
    spec_item = {"type": "string", "enum": names} if names else {"type": "string"}
    schema = {"type": "object", "additionalProperties": False, "required": ["parts"], "properties": {"parts": {
        "type": "array", "items": {"type": "object", "additionalProperties": False,
                                   "required": ["label", "note", "box", "spec_parts"],
                                   "properties": {"label": {"type": "string"}, "note": {"type": "string"}, "box": box,
                                                  "spec_parts": {"type": "array", "items": spec_item}}}}}}
    user = "Locate the parts in the drawing."
    if names:
        user += "\n\nSpecification parts:\n" + "\n".join(f"- {n}" for n in names)
    ans = llm.ask_json(REGIONS_SYSTEM, user, schema, name="regions", model=llm.STRONG_MODEL, effort="medium",
                       images=[img])
    parts = []
    for p in ans["parts"]:
        b = p["box"]
        xs = sorted(min(1000, max(0, v)) for v in (b["x0"], b["x1"]))
        ys = sorted(min(1000, max(0, v)) for v in (b["y0"], b["y1"]))
        parts.append({"label": p["label"], "note": p["note"],
                      "bbox": [round(xs[0] * width / 1000), round(ys[0] * height / 1000),
                               round(xs[1] * width / 1000), round(ys[1] * height / 1000)],
                      "spec_parts": [s for s in p["spec_parts"] if not names or s in names]})
    return {"image": img.name, "width": width, "height": height, "unit": "px, Ursprung oben links",
            "model": llm.model_name(llm.STRONG_MODEL), "spec_parts": names, "parts": parts}


def draw_regions(case: Case, reg: dict, out: Path) -> Path:
    """Zeichnet die Regionen zur Kontrolle von Hand ins Bild (PNG)."""
    import pymupdf
    img = next(p for p in case.images if p.name == reg["image"])
    doc = pymupdf.open()
    page = doc.new_page(width=reg["width"], height=reg["height"])
    page.insert_image(page.rect, filename=str(img))
    for i, p in enumerate(reg["parts"], start=1):
        r = pymupdf.Rect(*p["bbox"])
        page.draw_rect(r, color=(0.85, 0.1, 0.1), width=5)
        page.insert_text((r.x0 + 6, r.y0 + 34), f"{i} {p['label']}", fontsize=30, color=(0.85, 0.1, 0.1))
    page.get_pixmap().save(str(out))
    return out


def apply(case: Case, mode: str = "auto", infer_category: bool = False) -> tuple[Case, dict | None]:
    """Gibt den (ggf. ergänzten) Fall und die Zeichnungsbeschreibung (für .meta.json) zurück.
    auto: mit Spec wie off (Zeichnung brachte zusätzlich nichts: E018-a, mit der neuen beschrifteten Zeichnung E041-a),
    ohne Spec wie only (E042-a 0.608; mit infer_category E043-a 0.691, CLI-Standard)."""
    if mode not in MODES:
        raise SystemExit(f"Unbekannter Vision-Modus {mode!r}, erlaubt: {MODES}")
    if mode == "auto":
        mode = "off" if case.spec_text.strip() else "only"
    if mode == "off" or not case.images:
        if mode == "only" and not case.images:
            raise SystemExit(f"--vision only, aber keine Zeichnung in {case.folder}")
        return case, None
    desc = describe(case, use_spec=(mode == "on"), infer_category=infer_category and mode == "only")
    text = render(desc)
    spec = text if mode == "only" or not case.spec_text.strip() else f"{case.spec_text.rstrip()}\n\n{text}"
    return replace(case, spec_text=spec), desc


def main(argv: list[str] | None = None) -> int:
    """    .venv/bin/python -m certreq.vision regions <fall-ordner> [--out regionen.json] [--draw kontrolle.png]"""
    import argparse
    import json
    import sys

    from .case import load_case
    ap = argparse.ArgumentParser(prog="python -m certreq.vision", description="Zeichnung: Bildregionen je Teil")
    ap.add_argument("cmd", choices=["regions"])
    ap.add_argument("case")
    ap.add_argument("--out", help="JSON-Datei (Standard: nur Ausgabe)")
    ap.add_argument("--draw", help="PNG mit eingezeichneten Regionen zur Kontrolle")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])
    case = load_case(args.case)
    reg = regions(case)
    if reg is None:
        raise SystemExit(f"Keine Zeichnung in {case.folder}")
    text = json.dumps(reg, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    for i, p in enumerate(reg["parts"], start=1):
        print(f"{i:2} {p['label']:28} {p['bbox']}  → {', '.join(p['spec_parts']) or '–'}")
    if args.draw:
        print(f"Kontrollbild: {draw_regions(case, reg, Path(args.draw))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
