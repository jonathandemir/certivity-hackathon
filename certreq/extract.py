"""Stufe 2: Anforderungen aus den gewählten Regelungen.

Baseline B0 (AP1): jeder nummerierte Absatz der base-Version, der „shall" enthält, wird eine Anforderung
(Text = Absatztext, Seite = Startseite, Absatz = Label). Keine Zerlegung in einzelne Pflichten.
AP4: `filters` schaltet den Relevanzfilter entlang der Gliederung zu (certreq/relevance.py), `options` ändert die
Extraktion. Die Funktion selbst ist ohne Argumente B0; die CLI (`certreq run`) nimmt `--filters all` und
`--extract modal,llm` + alle Zusatzregeln als Standard (Bestmarke E022-hs/E024-hs-c, AGENTS.md §4).

Optionen:
  modal  auch Absätze ohne „shall" mit anderer Pflicht- oder Erlaubnisform: must, may, (not) permitted/allowed,
         required, mandatory, prohibited. Im Dev-Gold stammen 35 von 190 Anforderungen aus solchen Absätzen
         (R150 4.1.6.2 „… is not permitted", R48 5.7.1 „Lamps may be grouped …"); die Referenz formuliert sie als shall.
  split  Aufzählungen (a), (b), (c) … werden je Punkt eine Anforderung: Einleitung + Punkt, wie die Referenz es tut
         (R150 5.1.1 „Every retro-reflector … shall meet: (a) … (b) … (c) …" → 3 Anforderungen). Verschachtelte
         (i), (ii) bleiben im Punkt. Verweise wie „paragraph 3.3.3.5. (a)" sind keine Aufzählung.
  llm    das LLM liest jeden Kandidat-Absatz mit Gliederungspfad und Bauteil-Spec und gibt die einzelnen Pflichten
         als shall-Sätze zurück, leer = nicht anwendbar (certreq/llmextract.py). Ersetzt split; Kandidaten wie sonst
         (Filter, shall bzw. modal).
  lists, tables, exempt, tests, modes, vehicle, procedure, procedure2, optional, complete, duties, testcond
         Zusatzregeln für den LLM-Prompt (nur mit llm, llmextract.RULES): Aufzählungen im Satz zusammen lassen,
         Tabellen mit Alternativen vs. Pflichtzeilen, Ausnahmen behalten, Prüfparameter behalten, fremde
         Betriebsarten verwerfen. Einzeln messbar (E025-hs-c…E029-hs-c); in der CLI die ersten fünf Standard.
         vehicle (reine Fahrzeugausrüstung verwerfen) und procedure (Prüfanweisungen an Labor/Technischen Dienst
         weglassen; procedure2 behält dabei „shall be tested by method X"), optional (Pflichten für den Einbau als
         optionales Gerät behalten), complete (Ausnahmen vollständig übernehmen), duties (Nachweispflichten des
         Herstellers behalten) und testcond (Prüfbedingungen behalten) sind neu und noch hinter Schalter.
"""
from __future__ import annotations

import re

from .pdf import Paragraph, parse_pdf
from .regindex import Regulation
from .llmextract import RULES
from .relevance import relevant
from .submission import Requirement

OPTIONS = ("modal", "split", "llm", *RULES)
SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)
MODAL_RE = re.compile(r"\b(shall|must|may|permitted|allowed|required|mandatory|prohibited)\b", re.IGNORECASE)
ITEM_RE = re.compile(r"(?:^|(?<=\s))\(([a-z])\)\s+")
REFERENCE_BEFORE_RE = re.compile(r"(\d\.?|paragraphs?|\)\s+(and|or|to))\s*$", re.IGNORECASE)  # „5. (a)", „(a) and (b)"


def split_items(text: str) -> list[str]:
    """„Lead: (a) X; (b) Y; and (c) Z." → ["Lead X.", "Lead Y.", "Lead Z."]; ohne Aufzählung [text]."""
    marks = []
    for m in ITEM_RE.finditer(text):
        if ord(m.group(1)) - ord("a") == len(marks) and not REFERENCE_BEFORE_RE.search(text[:m.start()]):
            marks.append(m)
    if len(marks) < 2:
        return [text]
    lead = text[:marks[0].start()].strip().rstrip(":").strip()
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        item = re.sub(r"[;,]?\s*\b(and|or)\s*$", "", text[m.end():end].strip()).strip().rstrip(";,").strip()
        if item and lead and item[:1].isupper() and item[1:2].islower():  # „shall meet: (a) The …" → „shall meet the …"
            item = item[0].lower() + item[1:]
        if item:
            out.append(" ".join(x for x in (lead, item) if x).rstrip(".") + ".")
    return out or [text]


def extract_requirements(regs: list[Regulation], spec_text: str = "", filters: tuple[str, ...] = (),
                         options: tuple[str, ...] = (), stats: dict | None = None) -> list[Requirement]:
    unknown = set(options) - set(OPTIONS)
    if unknown:
        raise ValueError(f"Unbekannte Optionen {sorted(unknown)}, erlaubt: {OPTIONS}")
    rules = tuple(o for o in options if o in RULES)
    if rules and "llm" not in options:
        raise ValueError(f"Regeln {rules} wirken nur zusammen mit llm (--extract modal,llm,{','.join(rules)})")
    obligation = MODAL_RE if "modal" in options else SHALL_RE
    cands: list[tuple[Regulation, Paragraph]] = []
    for reg in regs:
        base = reg.base
        for pdf in base.pdfs:
            if not pdf.exists():
                raise SystemExit(f"PDF fehlt: {pdf}. Im Paket python3 tools/fetch_regulations.py ausführen.")
            paras = parse_pdf(pdf)
            keep = relevant(paras, filters, spec_text) if filters else [True] * len(paras)
            cands.extend((reg, para) for para, ok in zip(paras, keep) if ok and obligation.search(para.text))
    if "llm" in options:
        from .llmextract import llm_requirements
        return llm_requirements(cands, spec_text, stats=stats, rules=rules)
    reqs: list[Requirement] = []
    for reg, para in cands:
        texts = split_items(para.body) if "split" in options else [para.text]
        reqs.extend(Requirement(text, reg.name, reg.base.label, para.page, para.label) for text in texts)
    return reqs
