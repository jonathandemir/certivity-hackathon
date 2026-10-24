"""AP4: Das LLM liest Kandidat-Absätze (mit Gliederungspfad) und formuliert die Pflichten für das Bauteil.

Ein Aufruf je Batch (aufeinanderfolgende Absätze einer Regelung, ≤ BATCH_PARAS Absätze bzw. ≤ BATCH_CHARS Zeichen),
parallel über llm.ask_many, Antworten im Cache (out/cache/llm/). Antwort je Absatz: Liste von Anforderungen als
eigenständige shall-Sätze, eine Pflicht je Satz; leer = gilt nicht für dieses Bauteil oder keine Pflicht.
Fehlt ein Absatz in der Antwort, bleibt sein Rohtext (kein stiller Recall-Verlust); `stats` zählt das.

Das Beispiel im Prompt ist selbst geschrieben (andere Regelung), nicht aus dem Dev-Gold, damit die Dev-Messung ehrlich bleibt.

Zusatzregeln (RULES) aus der Fehleranalyse von E020-a (LOG [finding] 2026-10-24): einzeln per `--extract` schaltbar
(lists, tables, exempt, tests, modes; dazu vehicle, procedure, procedure2, optional, complete aus der Analyse von E024-hs-c; duties, testcond aus dem R175-Prüfstein), damit jede für sich
gemessen werden kann. Ohne Regel ist der Prompt bytegleich
zu v2, gecachte Antworten (E020-a) bleiben gültig. Die Beispiele in den Regeln sind allgemein formuliert, keine Gold-Texte.
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

# Reihenfolge fest (nicht die der Kommandozeile), damit gleiche Regelmengen denselben Prompt und Cache-Schlüssel ergeben.
RULES = {
    "lists": "Apart from the splits above (including obligations with their own verb, as in the mirror example), one "
             "sentence gives one requirement. A list inside a sentence (conditions, "
             "alternatives, examples or environmental factors such as \"rain, snow, fog or dust\") and the same limit "
             "stated over adjacent ranges of one quantity (e.g. two frequency bands, or 12 V and 24 V systems) stay in "
             "ONE requirement.",
    "tables": "Table cells follow the paragraph text. If the rows of a table are alternatives the manufacturer may "
              "choose from (e.g. alternative test methods), give one requirement that refers to the table by its "
              "number. If every row is mandatory (e.g. each test pulse or each test point), give one requirement per "
              "row that carries every column of that row (all limits and classes, for every variant the row lists).",
    "exempt": "Exemptions and presumptions of conformity (\"shall be deemed to comply with ...\", \"need not be "
              "tested ...\") are requirements too: keep each as one requirement with its condition.",
    "tests": "Test parameters that define the stress or conditions under which the component must perform or be "
             "verified (frequency range and steps, modulation, test level, duration, temperature, impact speed) are "
             "requirements. The physical arrangement of the test set-up (placement of the sample, cables, ground "
             "plane, measuring equipment) is not.",
    "modes": "Also return an empty list when a paragraph only applies to an operating mode, configuration or device "
             "variant that the specification does not have (e.g. a charging mode coupled to the power grid for a "
             "component without a charging function).",
    "vehicle": "Also return an empty list for obligations that only concern the vehicle or its other equipment and that "
               "this component does not influence: whether a device is mandatory or optional on a vehicle category, how "
               "many devices a vehicle carries, tell-tales, switches or notices inside the vehicle, and installation "
               "variants the specification does not mention (e.g. mounting on movable or concealed parts). A requirement "
               "worded for the vehicle still applies when this component forms or carries what it regulates (e.g. the "
               "external surface, a mounting height or position).",
    "procedure": "Instructions on how the Technical Service or test laboratory carries out a test (which standard or "
                 "method to follow, set-up, sequence of steps, sample handling, measuring intervals, test methods the "
                 "manufacturer may choose among) are not requirements: leave them out. Keep what the component must "
                 "withstand or achieve in the test (severity levels, exposure durations, pass or fail criteria).",
    # procedure2 = procedure ohne den Fehler aus E031-hs-c (verwarf „the ESA shall be tested by the method(s) according
    # to ISO 7637-2 as described in Annex 10", eine Gold-Pflicht in R10 6.7.1/6.8.2.1/6.9.1)
    "procedure2": "Instructions on how the Technical Service or test laboratory carries out a test (set-up, sequence of "
                  "steps, sample handling, measuring equipment and intervals, test methods the manufacturer may choose "
                  "among) are not requirements: leave them out. Keep the obligation that the component is tested by a "
                  "named method or standard where the regulation states it (\"the ESA shall be tested according to ISO "
                  "7637-2 as described in Annex 10\"), and keep what the component must withstand or achieve in the test "
                  "(severity levels, exposure durations, pass or fail criteria).",
    # Fehleranalyse E024/E033-hs-c: 6 von 9 Gold-Pflichten mit „optional" fehlen (R48 6.10.4.2 „Where optional rear
    # position lamps are installed …"), 5 von 17 mit „except/however" (Ausnahme gekürzt, z. B. R48 6.7.5, 6.10.7)
    "optional": "Requirements that apply when a device is fitted as an optional or additional device of its type "
                "(\"where optional devices are installed ...\", \"an optional device mounted above ...\") concern this "
                "component too, because it may be installed in that role: keep them, with their condition.",
    "complete": "Carry every exception, alternative and condition that belongs to a requirement into it completely, "
                "including all lettered cases and conditions in parentheses; do not shorten or drop them.",
    # Übergabe A (STATUS 19:45): auf dem R175-Prüfstein fehlen mit Opus 22 Anforderungen, 11 Nachweispflichten des
    # Herstellers („declare / demonstrate / document … to the Approval Authority"), 11 Prüfbedingungen (6.3, 6.5)
    "duties": "Obligations of the manufacturer or applicant to declare, demonstrate, document or justify to the Approval "
              "Authority or Technical Service how this component (or the system it belongs to) meets a technical "
              "requirement are requirements too: keep them, although they address the approval process. Application "
              "forms, approval marks and communication between authorities stay excluded.",
    "testcond": "Test conditions under which the component must meet a requirement are requirements: the test area or "
                "zone on the component, the test target or impact point, speed, mass, environment, and the initial "
                "state or pre-conditioning of the component or vehicle. This narrows the exclusion of the test set-up "
                "above: only measuring instruments, their accuracy, cabling and data recording stay excluded.",
}
ANSWER_MARK = "Answer as JSON matching the schema"


def system_prompt(rules: tuple[str, ...] = ()) -> str:
    """v2-Prompt, optional mit Zusatzregeln vor der Antwortanweisung."""
    unknown = set(rules) - set(RULES)
    if unknown:
        raise ValueError(f"Unbekannte Regeln {sorted(unknown)}, erlaubt: {tuple(RULES)}")
    if not rules:
        return SYSTEM
    extra = "Additional rules:\n" + "".join(f"- {RULES[r]}\n" for r in RULES if r in rules) + "\n"
    i = SYSTEM.index(ANSWER_MARK)
    return SYSTEM[:i] + extra + SYSTEM[i:]


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
                     stats: dict | None = None, rules: tuple[str, ...] = ()) -> list[Requirement]:
    from .llm import ask_many  # erst hier: Tests und B0-Läufe brauchen weder openai noch Key

    system = system_prompt(rules)
    batches = _batches(cands)
    answers = ask_many([dict(system=system, user=_user_prompt(spec_text, b), schema=SCHEMA, name="requirements")
                        for b in batches], workers=workers)
    stats = stats if stats is not None else {}
    stats.update(batches=len(batches), paragraphs=len(cands), kept=0, dropped=0, missing=0)
    if rules:
        stats["rules"] = [r for r in RULES if r in rules]
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
