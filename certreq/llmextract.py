"""AP4: Das LLM liest Kandidat-Absätze (mit Gliederungspfad) und formuliert die Pflichten für das Bauteil.

Ein Aufruf je Batch (aufeinanderfolgende Absätze einer Regelung, ≤ BATCH_PARAS Absätze bzw. ≤ BATCH_CHARS Zeichen),
parallel über llm.ask_many, Antworten im Cache (out/cache/llm/). Antwort je Absatz: Liste von Anforderungen als
eigenständige shall-Sätze, eine Pflicht je Satz; leer = gilt nicht für dieses Bauteil oder keine Pflicht.
Fehlt ein Absatz in der Antwort, bleibt sein Rohtext (kein stiller Recall-Verlust); `stats` zählt das.

Das Beispiel im Prompt ist selbst geschrieben (andere Regelung), nicht aus dem Dev-Gold, damit die Dev-Messung ehrlich bleibt.
"""
from __future__ import annotations

from .pdf import Paragraph
from .regindex import Regulation
from .submission import Requirement

BATCH_PARAS = 12
BATCH_CHARS = 9000
MAX_PARA_CHARS = 3000

SYSTEM = """You are a vehicle homologation engineer. You receive the specification of one vehicle component and a batch \
of numbered paragraphs from one UN Regulation, each with its section path. For every paragraph, list the engineering \
requirements it imposes on THIS component: obligations its designers and manufacturer must implement or verify \
(design, construction, materials, markings, photometric/electrical/mechanical performance, installation of this \
component on the vehicle, test conditions it must withstand).

Return an empty list for a paragraph when it
- is a definition, scope statement, explanatory note or pure cross-reference without its own obligation;
- is administrative: application, approval procedure, documents, communication, duties of authorities or technical services;
- only concerns other device types, functions or vehicle categories than this component;
- only describes test equipment or the test laboratory's procedure without a requirement the component must meet.

Writing rules:
- Keep the scope exactly as the regulation states it: if the text says "lamps", "all light-signalling devices", \
"every retro-reflector" or "devices marked TOP", the requirement says that too. Never narrow it to the component \
("the rear lamp ...") and never add the component's name where the regulation does not use it. The component only \
decides WHETHER a paragraph applies, not how its requirement is worded.
- Split only where the regulation itself separates obligations: lettered or numbered items (a), (b), (c); separate \
sentences; independent limits for different quantities or directions (e.g. horizontal angle vs. vertical angle). \
Keep coordinated properties of one clause together ("shall be clearly legible and indelible" is ONE requirement), \
keep a minimum/maximum range of the same quantity together, and keep an exception with the rule it modifies.
- Each requirement is a self-contained sentence with "shall" (permissions: "may" or "shall be permitted to", as in \
the text). Replace "it"/"they" by the regulation's own subject from the context. Keep conditions ("where ...", "if \
...", "except ..."), values, units and paragraph references exactly as written. Stay close to the regulation's \
wording; never invent values and never add content from referenced paragraphs or other regulations.
- Do not repeat a requirement that another paragraph of the batch states.

Example (illustrative, UN R46 mirrors, component = exterior mirror): paragraph "6.1.2.1. The mirror shall be \
adjustable from the driver's seat and its reflecting surface shall not be less than 100 cm²." yields ["The mirror shall \
be adjustable from the driver's seat.", "The reflecting surface of the mirror shall not be less than 100 cm²."]; \
paragraph "6.1.1. All mirrors shall be adjustable and firmly fixed." yields ["All mirrors shall be adjustable and \
firmly fixed."]; paragraph "2.3. 'Class' means ..." yields [].

Answer as JSON matching the schema: one entry per paragraph ref, in order; "note" gives the reason in a few words \
when "requirements" is empty, otherwise "".
"""

SCHEMA = {
    "type": "object",
    "properties": {"paragraphs": {"type": "array", "items": {
        "type": "object",
        "properties": {"ref": {"type": "integer"}, "requirements": {"type": "array", "items": {"type": "string"}},
                       "note": {"type": "string"}},
        "required": ["ref", "requirements", "note"], "additionalProperties": False}}},
    "required": ["paragraphs"], "additionalProperties": False,
}


def _batches(cands: list[tuple[Regulation, Paragraph]]) -> list[list[tuple[Regulation, Paragraph]]]:
    out: list[list[tuple[Regulation, Paragraph]]] = []
    cur: list[tuple[Regulation, Paragraph]] = []
    size = 0
    for reg, p in cands:
        n = min(len(p.text), MAX_PARA_CHARS)
        if cur and (cur[0][0].name != reg.name or len(cur) >= BATCH_PARAS or size + n > BATCH_CHARS):
            out.append(cur)
            cur, size = [], 0
        cur.append((reg, p))
        size += n
    if cur:
        out.append(cur)
    return out


def _user_prompt(spec_text: str, batch: list[tuple[Regulation, Paragraph]]) -> str:
    reg = batch[0][0]
    lines = [f"COMPONENT SPECIFICATION:\n{spec_text.strip()}\n", f"REGULATION: {reg.name} ({reg.title}), version {reg.base.label}\n",
             "PARAGRAPHS:"]
    for i, (_, p) in enumerate(batch, start=1):
        path = " > ".join(p.headings) or "-"
        text = p.text if len(p.text) <= MAX_PARA_CHARS else p.text[:MAX_PARA_CHARS] + " [...]"
        lines.append(f"[{i}] paragraph {p.label} | section: {path} | page {p.page}\n{text}\n")
    return "\n".join(lines)


def llm_requirements(cands: list[tuple[Regulation, Paragraph]], spec_text: str, workers: int = 8,
                     stats: dict | None = None) -> list[Requirement]:
    from .llm import ask_many  # erst hier: Tests und B0-Läufe brauchen weder openai noch Key

    batches = _batches(cands)
    answers = ask_many([dict(system=SYSTEM, user=_user_prompt(spec_text, b), schema=SCHEMA, name="requirements")
                        for b in batches], workers=workers)
    stats = stats if stats is not None else {}
    stats.update(batches=len(batches), paragraphs=len(cands), kept=0, dropped=0, missing=0)
    reqs: list[Requirement] = []
    for batch, answer in zip(batches, answers):
        by_ref = {e["ref"]: e for e in answer.get("paragraphs", []) if isinstance(e, dict)}
        for i, (reg, p) in enumerate(batch, start=1):
            entry = by_ref.get(i)
            if entry is None:
                stats["missing"] += 1
                texts = [p.text]
            else:
                texts = [t.strip() for t in entry.get("requirements", []) if t and t.strip()]
            stats["kept" if texts else "dropped"] += 1
            reqs.extend(Requirement(t, reg.name, reg.base.label, p.page, p.label) for t in texts)
    return reqs
