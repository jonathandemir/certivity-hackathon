"""AP4: Relevanzfilter entlang der Gliederung (welche Abschnitte einer Regelung betreffen unser Bauteil?).

Regeln, einzeln schaltbar (`filters`), damit jede einzeln gegen die Bestmarke gemessen werden kann:

  admin  Verwaltungsabschnitte fallen weg: Scope, Definitions, Application for approval, Approval, Modifications,
         Penalties, Production discontinued, Names and addresses, Transitional provisions, Anhänge Communication /
         Information document / Arrangement of approval marks. Sie richten sich an Behörde und Technischen Dienst,
         nicht an den Konstrukteur. „Approval marking and other markings" bleibt.
  cop    Conformity of production (Abschnitt und Anhänge „Minimum requirements for conformity …/sampling …") fällt
         weg, außer Absätzen mit Fertigungstoleranz („shall not deviate … by more than 20 per cent"): die sind
         eine Konstruktionsreserve und stehen im Gold des Dev-Falls (R148 6.1.3, R150 Annex 2 1.2).
  parts  In einer Aufzählung von Gerätetypen (Geschwisterabschnitte wie R48 6.1 Main-beam headlamp … 6.28) bleiben
         nur die, deren Name ein Teil oder eine Funktion aus der Spezifikation enthält. Greift nur, wenn mindestens
         ein Geschwister passt und mindestens drei denselben Gerätebegriff tragen (sonst ist es keine Aufzählung).
         Allgemeine Geschwister („General …", „Other requirements", „Exceptions") gelten für alle und bleiben.
         Zweite Form einer Aufzählung: mindestens drei Geschwister mit gleichem Titelanfang wie der Treffer
         (R150 5.1–5.3 „Technical requirements concerning retro-reflectors / marking materials / triangles").
  rationale  Teil I einer GTR („Statement of technical rationale and justification", GTR 9 S. 1–70) fällt weg: Begründung
         und Vorgeschichte, keine Pflichten; verbindlich ist erst „II. Text of the Regulation" (certreq/pdf.py).
  esa    Wo Geschwister nach Fahrzeug und Bauteil getrennt sind (R10 6.2 „… from vehicles" / 6.5 „… by ESAs", auch
         Anhänge), bleiben die Bauteil-Abschnitte: Eingabe ist immer ein Bauteil, nie ein ganzes Fahrzeug.

Unsicher heißt behalten: ohne Spezifikationstext oder ohne Treffer greift `parts` nicht.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from .pdf import RATIONALE_TITLE, Paragraph

FILTERS = ("admin", "cop", "parts", "esa", "rationale")

ADMIN_RE = re.compile(
    r"^((application\s*/\s*)?scope|definitions?|application for( type)?[- ]approval|approval\s*$|approval of a vehicle type|esa type approval|"
    r"type approval procedures|granting of type approval|notice of approval|modifications?\b|amendment or extension|"
    r"penalties\b|production definitively discontinued|names and addresses|transitional provisions|communication\b|"
    r"information document|arrangements? of approval mark|examples of approval mark)", re.I)
COP_RE = re.compile(r"^((control of )?conformity of production|minimum requirements for (conformity|verification of conformity|sampling))",
                    re.I)
TOLERANCE_RE = re.compile(r"\bdeviat\w*\b.{0,80}?\b(\d+ ?per ?cent|\d+ ?%)", re.I)
ESA_RE = re.compile(r"\b(ESAs?|sub-?\s?assembl\w*|components?)\b", re.I)
VEHICLE_RE = re.compile(r"\bvehicles?\b", re.I)
GENERIC_RE = re.compile(r"^(general|other|exceptions?|common|miscellaneous)\b", re.I)
POSITION_WORDS = {"front", "rear", "side", "left", "right", "upper", "lower", "inner", "outer", "interior",
                  "exterior", "top", "bottom", "lateral"}
SPEC_SECTIONS = {"product type", "function", "functions", "main parts", "parts", "components"}


def _words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower().replace("-", " "))
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words]


def spec_terms(spec_text: str) -> list[tuple[str, ...]]:
    """Teile und Funktionen aus der Spezifikation: Aufzählungspunkte unter Product Type / Function / Main Parts,
    Klammerinhalt als eigener Begriff („Braking indication (stop lamp)" → braking indication, stop lamp).
    Einzelwörter zählen nur als ganzer Aufzählungspunkt unter Main Parts („Housing"), nicht aus Klammern oder
    Funktionen („(presence/visibility)" würde sonst Unterabschnitte wie „Geometric visibility" treffen)."""
    terms: list[tuple[str, ...]] = []
    section = None
    for raw in spec_text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            section = line.lstrip("#").strip().lower()
            continue
        if section not in SPEC_SECTIONS or not line or line.startswith("|"):
            continue
        line = line.lstrip("-*• ").split("—")[0].split(" - ")[0]
        whole = tuple(_words(line))
        for piece in re.split(r"[()&/,;]", line):
            w = tuple(_words(piece))
            if w and w not in terms and (len(w) >= 2 or (w == whole and section in {"main parts", "parts", "components"})):
                terms.append(w)
    return terms


def _contains(title: list[str], term: tuple[str, ...]) -> bool:
    n = len(term)
    return any(tuple(title[i:i + n]) == term for i in range(len(title) - n + 1))


def _matching_term(title: str, terms: list[tuple[str, ...]], spec_words: set[str]) -> tuple[str, ...] | None:
    """Begriff der Spezifikation, der im Titel vorkommt; ein Lagewort im Titel (front, side …), das die
    Spezifikation nicht kennt, schließt aus („Front retro-reflector" passt nicht zu einem Heck-Rückstrahler)."""
    w = _words(title)
    if any(x in POSITION_WORDS and x not in spec_words for x in w):
        return None
    return next((t for t in sorted(terms, key=len, reverse=True) if _contains(w, t)), None)


def _sibling_groups(paras: tuple[Paragraph, ...]) -> dict[tuple, list[tuple[str, str]]]:
    """Gruppen gleichrangiger Abschnitte mit Titel: (Kontext, Elternnummer) → [(Präfix, Titel)].
    Anhänge bilden zusätzlich eine eigene Gruppe auf oberster Ebene (Präfix „Annex 4 ")."""
    groups: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    seen: set[str] = set()
    for p in paras:
        ctx = p.label[: len(p.label) - len(p.number)]
        if p.title:
            parent = p.number.rpartition(".")[0]
            groups[(ctx, parent)].append((p.label, p.title))
        if re.fullmatch(r"Annex \w+ ", ctx) and p.context and ctx not in seen:
            seen.add(ctx)
            groups[("annexes",)].append((ctx, p.context[0]))
    return groups


def _dropped_sections(paras: tuple[Paragraph, ...], filters: tuple[str, ...], terms: list[tuple[str, ...]],
                      spec_words: set[str]) -> set[str]:
    dropped: set[str] = set()
    for members in _sibling_groups(paras).values():
        if "esa" in filters:
            esa = [lab for lab, t in members if ESA_RE.search(t)]
            vehicle_only = [lab for lab, t in members if VEHICLE_RE.search(t) and not ESA_RE.search(t)]
            if esa and vehicle_only:
                dropped.update(vehicle_only)
        if "parts" in filters and terms and len(members) >= 3:
            matched = {lab: _matching_term(t, terms, spec_words) for lab, t in members}
            heads = {t[-1] for t in matched.values() if t}
            nouns = Counter(w for _, t in members for w in set(_words(t)))
            if heads and any(nouns[h] >= 3 for h in heads):
                dropped.update(lab for lab, t in members if matched[lab] is None and not GENERIC_RE.match(t))
                continue
            for lab, t in members:  # parallele Abschnitte: gleicher Titelanfang wie ein Treffer
                prefix = _words(t)[:3]
                parallel = [x for x, u in members if _words(u)[:3] == prefix]
                if matched[lab] and len(prefix) == 3 and len(parallel) >= 3:
                    dropped.update(x for x in parallel if matched[x] is None)
    return dropped


def _under(label: str, section: str) -> bool:
    """Liegt der Absatz `label` im Abschnitt `section`? Ganze Anhänge enden auf Leerzeichen („Annex 4 ")."""
    if section.endswith(" "):
        return label.startswith(section)
    return label == section or label.startswith(section + ".")


def relevant(paras: tuple[Paragraph, ...], filters: tuple[str, ...] = FILTERS,
             spec_text: str = "") -> list[bool]:
    """Pro Absatz: bleibt er nach den gewählten Filtern drin?"""
    unknown = set(filters) - set(FILTERS)
    if unknown:
        raise ValueError(f"Unbekannte Filter {sorted(unknown)}, erlaubt: {FILTERS}")
    terms = spec_terms(spec_text)
    spec_words = set(_words(spec_text))
    dropped = _dropped_sections(paras, filters, terms, spec_words)
    keep = []
    for p in paras:
        path = p.headings + ((p.title,) if p.title else ())
        if "rationale" in filters and p.context[:1] == (RATIONALE_TITLE,):
            keep.append(False)
        elif "admin" in filters and any(ADMIN_RE.match(h) for h in path):
            keep.append(False)
        elif "cop" in filters and any(COP_RE.match(h) for h in path) and not TOLERANCE_RE.search(p.text):
            keep.append(False)
        else:
            keep.append(not any(_under(p.label, s) for s in dropped))
    return keep
