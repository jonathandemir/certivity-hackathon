"""AP7 Sub-Goal: Welche Anforderungen aus Version A ändern sich in Version B einer Regelung?

    .venv/bin/python -m certreq.subgoal run  vendor/industrial-ai-hackathon/subgoal/dev [--out out/subgoal-dev.json]
    .venv/bin/python -m certreq.subgoal eval out/subgoal-dev.json            # Recall/Precision gegen expected.json

Verfahren (regelbasiert, ohne LLM; jede Stufe ist austauschbar):
1. Alt- und Neu-PDF mit `certreq.pdf.parse_pdf` in Absätze zerlegen, diese in Sätze und Aufzählungspunkte.
2. Jede alte Anforderung wird den alten Sätzen zugeordnet, aus denen sie stammt (Absatzlabel + Wortüberdeckung).
3. Alte und neue Sätze werden global 1:1 einander zugeordnet (nicht nur gleiches Label: Absätze werden verschoben und
   umnummeriert; jeder alte Satz höchstens einmal, bei Gleichstand entscheidet der Kontext der Nachbarsätze).
   Identisch → unverändert; ähnlich → `modified`; kein Gegenstück → `removed`.
4. Neue normative Sätze ohne alte Entsprechung → `added`: „shall“, aber auch Pflichten ohne „shall“ („is not required
   when“, „is not more than“, „may“). Bedingungslisten („… not required when: (a) …; or (b) …“) bleiben eine Pflicht,
   zwei verbundene Pflichten in einem Satz („shall …, and may …“) werden zwei.
`reason` nennt Absatz, Version und die Wortänderungen („'a' became 'b'; 'c' was added“), `new_text` den neuen Satz.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .pdf import Paragraph, parse_pdf
from .submission import TEAM_ID

SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)
# Pflicht, Verbot, Erlaubnis oder Grenzwert, auch ohne „shall“ (z. B. „is not required when“, „is not more than 25 per cent“)
NORM_RE = re.compile(r"\b(?:shall|must|may|required|exceed(?:s|ed|ing)?|permitted|prohibited|allowed)\b|"
                     r"\b(?:not|no) (?:be )?(?:more|less|greater|lower|higher|smaller|larger|fewer) than\b|\bat (?:least|most)\b", re.I)
# Einleitung einer Bedingungsliste: die Punkte sind Alternativen einer Pflicht, keine eigenen Pflichten
COND_LEAD_RE = re.compile(r"\b(?:when|if|where|unless|provided(?: that)?|in (?:the )?case(?: of)?|following conditions?)\b[^:]*:$", re.I)
# „X shall a, and may b“: zweite Pflicht mit ausgelassenem Subjekt
COORD_RE = re.compile(r",?\s+and\s+(?=(?:shall|may|must)\b)", re.I)
MODAL_RE = re.compile(r"\b(?:shall|may|must)\b", re.I)
HEADER_RE = re.compile(r"^(UN [^,|]+?), version (\S+) \| page \d+ of \d+", re.M)
# Satzende: . ; : gefolgt von Großbuchstabe oder Aufzählungsklammer. „5.1.2. are“ (klein) trennt nicht.
SPLIT_RE = re.compile(r"(?<=[.;:])\s+(?=[A-Z(])|\s+(?=\([a-z]\)\s)|\s+(?=\([ivx]+\)\s)")
TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*|[^\sa-z0-9]", re.I)
MODIFIED_MIN = 0.55  # darunter gilt ein alter Satz als ersatzlos weg
MAX_TEXT = 2000
# Übergangs-/Verwaltungsbestimmungen sind keine Ingenieuranforderungen (Absatz über Vertragsparteien u. Ä.)
ADMIN_RE = re.compile(r"Contracting Part|shall not refuse|shall (?:not )?be obliged to accept|granting approvals|"
                      r"national or regional type", re.I)


@dataclass(frozen=True)
class Sentence:
    label: str
    page: int
    text: str
    lead: str = ""  # Einleitung eines Aufzählungspunkts („…shall be as follows:“)

    @property
    def full(self) -> str:
        return f"{self.lead} {self.text}".strip() if self.lead else self.text


UNIT_SUBS = [(re.compile(r"(\d)\s*%"), r"\1 per cent"), (re.compile(r"\bseconds?\b"), "s"), (re.compile(r"\bmetres?\b"), "m"),
             (re.compile(r"\bcentre\b"), "center"), (re.compile(r"\bcentreline\b"), "centerline")]
EDITORIAL_WORDS = {"UN", "the"}  # „UN Regulation“ statt „Regulation“, Artikel: keine inhaltliche Änderung


def _editorial(x: str, y: str) -> bool:
    """Nur Schreibweise: Groß/klein, Bindestrich/Leerzeichen, Satzzeichen am Ende, Punkt vor Klammer („2.45.)“ ↔ „2.45)“)."""
    f = lambda t: re.sub(r"[.,;:]+$", "", re.sub(r"[\s\-]|\.(?=\))", "", t.lower()))
    return f(x) == f(y)
TRAILING_NUM_RE = re.compile(r"(?:\s+\d{1,2}(?:\.\d{1,2}){1,7}\.?)+\s*$")  # „… 10 km/h. 5.1.4.2“: Parser-Rest


def _norm(s: str) -> str:
    return " ".join(s.split())


def _canon(s: str) -> str:
    """Text für Vergleich und Diff: gleiche Bedeutung → gleiche Zeichenfolge."""
    s = TRAILING_NUM_RE.sub("", _norm(s))
    for rx, rep in UNIT_SUBS:
        s = rx.sub(rep, s)
    return s


def _tokens(s: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(s)]


def split_sentences(p: Paragraph) -> list[Sentence]:
    parts = [x.strip() for x in SPLIT_RE.split(_norm(p.text)) if x.strip()]
    out: list[Sentence] = []
    lead = ""
    for part in parts:
        if re.match(r"^\(([a-z]|[ivx]+)\)\s", part):
            out.append(Sentence(p.label, p.page, part, lead))
            continue
        out.append(Sentence(p.label, p.page, part))
        lead = part if part.endswith(":") else ""
    return out


def sentences_of(pdf: Path) -> list[Sentence]:
    return [s for p in parse_pdf(pdf) for s in split_sentences(p)]


def pdf_header(pdf: Path) -> tuple[str, str]:
    """(Regelung, Version) aus der Kopfzeile des PDFs, z. B. ('UN R175', '1.0.0')."""
    import pymupdf

    with pymupdf.open(str(pdf)) as doc:
        m = HEADER_RE.search(doc[0].get_text())
    if not m:
        raise SystemExit(f"Keine Kopfzeile „UN Rxxx, version x | page“ in {pdf}")
    return m.group(1), m.group(2)


def diff_phrases(old: str, new: str) -> list[str]:
    """Wortgenaue Änderungen im Stil der Referenz: 'a' became 'b'; 'c' was added; 'd' was removed."""
    a, b = _canon(old).split(), _canon(new).split()
    out = []
    key = lambda w: re.sub(r"\.(?=\))", "", w.lower())  # Groß/klein und „5.1.2.)“/„5.1.2)“ sind keine Änderung
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, [key(w) for w in a], [key(w) for w in b], autojunk=False).get_opcodes():
        x, y = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        if (tag == "replace" and _editorial(x, y)) or (tag != "replace" and (x or y) in EDITORIAL_WORDS):
            continue
        if tag == "insert" and i1 == 0 and j2 - j1 <= 6 and not SHALL_RE.search(y):
            continue  # eingefügte Überschrift („Acceleration from standstill“), keine inhaltliche Änderung
        if tag == "replace":
            out.append(f"'{x}' became '{y}'")
        elif tag == "insert":
            out.append(f"'{y}' was added")
        elif tag == "delete":
            out.append(f"'{x}' was removed")
    return out


def _ratio(a: list[str], b: list[str]) -> float:
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


class Index:
    """Neue Sätze mit Token-Listen; Kandidatensuche über gemeinsame Wörter, dann exaktes Verhältnis."""

    def __init__(self, sents: list[Sentence]):
        self.sents = sents
        self.toks = [_tokens(_canon(s.full)) for s in sents]
        self.sets = [set(t) for t in self.toks]

    def best(self, text: str, top: int = 6) -> tuple[int, float]:
        tk = _tokens(_canon(text))
        ts = set(tk)
        if not ts:
            return -1, 0.0
        cands = sorted(range(len(self.sents)), key=lambda i: -len(ts & self.sets[i]) / (len(ts | self.sets[i]) or 1))[:top]
        best_i, best_r = -1, 0.0
        for i in cands:
            r = _ratio(tk, self.toks[i])
            if r > best_r:
                best_i, best_r = i, r
        return best_i, best_r


def align(old_s: list[Sentence], new_s: list[Sentence], top: int = 8) -> dict[int, tuple[int, float]]:
    """1:1-Zuordnung alter zu neuen Sätzen (alt-Index → (neu-Index, Ähnlichkeit)), nur Paare ab MODIFIED_MIN.

    Gierig nach Ähnlichkeit plus Kontext: stimmen auch Vorgänger, Nachfolger oder Absatzlabel überein, gewinnt dieses Paar. So landet
    ein wortgleicher Satz („(b) Hold the vehicle stationary …“) bei seiner echten Nachfolgerin, eine zweite, neue Kopie
    an anderer Stelle bleibt frei und wird als `added` erkannt."""
    ot = [_tokens(_canon(s.full)) for s in old_s]
    nt = [_tokens(_canon(s.full)) for s in new_s]
    ns = [set(t) for t in nt]
    inv: dict[str, list[int]] = {}
    for j, st in enumerate(ns):
        for t in st:
            inv.setdefault(t, []).append(j)
    cache: dict[tuple[int, int], float] = {}

    def r(i: int, j: int) -> float:
        if not (0 <= i < len(ot) and 0 <= j < len(nt)):
            return 0.0
        if (i, j) not in cache:
            cache[(i, j)] = 1.0 if ot[i] == nt[j] else _ratio(ot[i], nt[j])
        return cache[(i, j)]

    pairs = []
    for i, tk in enumerate(ot):
        st = set(tk)
        if not st:
            continue
        common: dict[int, int] = {}
        for t in st:
            lst = inv.get(t, ())
            if len(lst) > 400:  # Allerweltswort, trägt nichts zur Auswahl bei
                continue
            for j in lst:
                common[j] = common.get(j, 0) + 1
        cands = sorted(common, key=lambda j: -common[j] / (len(st | ns[j]) or 1))[:top]
        for j in cands:
            v = r(i, j)
            if v >= MODIFIED_MIN:
                ctx = 0.1 * (r(i - 1, j - 1) + r(i + 1, j + 1)) + (0.05 if old_s[i].label == new_s[j].label else 0.0)
                pairs.append((v + ctx, v, i, j))
    out: dict[int, tuple[int, float]] = {}
    taken: set[int] = set()
    for _, v, i, j in sorted(pairs, reverse=True):
        if i in out or j in taken:
            continue
        out[i] = (j, v)
        taken.add(j)
    return out


def _sources_of(req: dict, old_sents: list[Sentence]) -> list[int]:
    """Indizes der alten Sätze, aus denen die Anforderung abgeleitet wurde (Label + Wortüberdeckung)."""
    label = req["source"].get("paragraph", "")
    rt = set(_tokens(req["text"]))
    pool = [k for k, s in enumerate(old_sents) if s.label == label] or list(range(len(old_sents)))
    scored = []
    for k in pool:
        s = old_sents[k]
        st = set(_tokens(s.text))
        if not st:
            continue
        cover = len(st & rt) / len(st)  # wie viel des Satzes steckt in der Anforderung
        within = len(rt & st) / (len(rt) or 1)  # wie viel der Anforderung steckt im Satz
        scored.append((max(cover, within * 0.9), k))
    hits = [k for sc, k in scored if sc >= 0.8]
    if not hits and scored:
        hits = [max(scored, key=lambda t: t[0])[1]]
    return hits


def compare(old_pdf: Path, new_pdf: Path, reqs_old: list[dict], team_id: str, case_id: str) -> dict:
    regulation, version = pdf_header(new_pdf)
    old_s, new_s = sentences_of(old_pdf), sentences_of(new_pdf)
    idx = Index(new_s)
    pairs = align(old_s, new_s)
    used_new: set[int] = {j for j, _ in pairs.values()}
    changes: list[dict] = []
    for req in reqs_old:
        srcs = _sources_of(req, old_s)
        changed, missing, matched = [], [], []
        for k in srcs:
            s = old_s[k]
            i, r = pairs[k] if k in pairs else idx.best(s.full)  # ohne 1:1-Partner: bester Kandidat (Zusammenlegung)
            if i >= 0 and r >= MODIFIED_MIN:
                used_new.add(i)
                matched.append(i)
                if r < 0.999 and _canon(s.full).lower() != _canon(new_s[i].full).lower():
                    changed.append((k, i))
            else:
                missing.append(k)
        label_old = req["source"].get("paragraph", "")
        if not matched:
            if srcs:
                gone = " ".join(old_s[k].text for k in missing)[:300]
                changes.append({"requirement_id": req["id"], "change": "removed", "new_text": None,
                                "reason": f"Paragraph {label_old} of {regulation} was amended in version {version}; "
                                          f"the provision '{gone}' was removed."})
            continue
        extras = _new_list_items(matched, new_s, used_new)
        used_new.update(extras)
        if not changed and not extras and not any(NORM_RE.search(old_s[k].full) for k in missing):
            continue  # unverändert (höchstens Überschriften o. Ä. verschwunden)
        olds = " ".join(old_s[k].text for k in sorted({k for k, _ in changed} | set(missing)))
        news = " ".join(new_s[i].text for i in sorted({i for _, i in changed} | set(extras)))
        plist = diff_phrases(olds, news)
        if not plist:
            continue  # nur Schreibweise/Überschrift/Umnummerierung
        n0 = new_s[min(matched)]
        former = f" (formerly {label_old})" if n0.label != label_old else ""
        full_new = " ".join(new_s[i].text for i in sorted(set(matched) | set(extras)))
        changes.append({"requirement_id": req["id"], "change": "modified", "new_text": _norm(full_new)[:MAX_TEXT],
                        "reason": f"Paragraph {n0.label}{former} of {regulation} was amended in version {version}: "
                                  f"{'; '.join(plist)}.", "source": {"page": n0.page, "paragraph": n0.label}})
    mod_sets = [set(_tokens(_canon(c["new_text"]))) for c in changes if c["change"] == "modified"]
    fresh: list[Sentence] = []
    for i, s in enumerate(new_s):
        if i in used_new or not NORM_RE.search(s.full) or ADMIN_RE.search(s.full):
            continue
        if s.text.endswith(":") and not s.lead:
            continue  # bloße Einleitung („…shall be as follows:“); die Pflichten stehen in den Aufzählungspunkten
        st = set(_tokens(_canon(s.full)))
        if any(len(st & m) / (len(st) or 1) >= 0.8 for m in mod_sets):
            continue  # steckt schon in einer `modified`-Meldung
        fresh.append(s)
    for s, text in _obligations(fresh):
        changes.append({"requirement_id": None, "change": "added", "new_text": text[:MAX_TEXT],
                        "reason": f"Paragraph {s.label} of {regulation} is new in version {version}: "
                                  f"'{text[:300]}'.", "source": {"page": s.page, "paragraph": s.label}})
    return {"team_id": team_id, "case_id": case_id, "changes": changes}


def _new_list_items(matched: list[int], new_s: list[Sentence], used: set[int]) -> list[int]:
    """Neue Aufzählungspunkte unter einer schon vorhandenen Pflicht (gleiche Einleitung, gleicher Absatz), z. B. eine
    zusätzliche Bedingung (vi) in „…, provided: (a) … (b) …“: Sie ändern diese Anforderung, sind keine neue."""
    labels = {new_s[i].label for i in matched}
    anchors = {_norm(new_s[i].text) for i in matched} | {_norm(new_s[i].lead) for i in matched if new_s[i].lead}
    lo, hi = min(matched), max(matched)  # nur innerhalb der Spanne der Anforderung; Anhänge am Listenende → `added`
    return [i for i in range(lo, hi + 1)
            if i not in used and new_s[i].lead and new_s[i].label in labels and _norm(new_s[i].lead) in anchors]


def _obligations(fresh: list[Sentence]) -> list[tuple[Sentence, str]]:
    """Neue Sätze → einzelne Pflichten: Bedingungslisten zusammenfassen, verbundene Pflichten trennen."""
    out: list[tuple[Sentence, str]] = []
    k = 0
    while k < len(fresh):
        s = fresh[k]
        if s.lead and COND_LEAD_RE.search(s.lead):
            group = [s]
            while k + 1 < len(fresh) and fresh[k + 1].lead == s.lead and fresh[k + 1].label == s.label:
                k += 1
                group.append(fresh[k])
            out.append((s, _norm(s.lead + " " + " ".join(g.text for g in group))))
        else:
            out.extend((s, t) for t in split_coordinated(_norm(s.full)))
        k += 1
    return out


def split_coordinated(text: str) -> list[str]:
    """„For tests without a target the ACPE shall be deactivated if necessary, and may be combined where feasible.“
    → zwei Pflichten; die zweite bekommt den Satzanfang bis zum ersten Modalverb als Subjekt."""
    first = MODAL_RE.search(text)
    m = COORD_RE.search(text, first.end()) if first else None
    if not m:
        return [text]
    one = text[:m.start()].rstrip(" ,;") + "."
    two = text[:first.start()].rstrip() + " " + text[m.end():].lstrip()
    return [one, *split_coordinated(two)]


def evaluate(sub: dict, expected: dict) -> dict:
    """Lokale Näherung (die Plattform urteilt semantisch): modified/removed zählen bei gleicher requirement_id und
    gleichem Typ, added bei gleichem Absatzlabel (je erwartetem Eintrag höchstens einmal)."""
    res: dict = {}
    for kind in ("modified", "removed", "added"):
        exp = [c for c in expected["changes"] if c["change"] == kind]
        got = [c for c in sub["changes"] if c["change"] == kind]
        if kind == "added":
            pool = [(c.get("source") or {}).get("paragraph") for c in exp]
            tp = 0
            for c in got:
                lab = (c.get("source") or {}).get("paragraph")
                if lab in pool:
                    pool.remove(lab)
                    tp += 1
        else:
            keys = {c["requirement_id"] for c in exp}
            tp = len({c["requirement_id"] for c in got} & keys)
        res[kind] = {"expected": len(exp), "got": len(got), "tp": tp,
                     "recall": tp / len(exp) if exp else 1.0, "precision": tp / len(got) if got else 0.0}
    tp = sum(v["tp"] for v in res.values())
    ne, ng = sum(v["expected"] for v in res.values()), sum(v["got"] for v in res.values())
    p, r = (tp / ng if ng else 0.0), (tp / ne if ne else 0.0)
    res["all"] = {"expected": ne, "got": ng, "tp": tp, "recall": r, "precision": p,
                  "f2": 5 * p * r / (4 * p + r) if p + r else 0.0}
    return res


def format_eval(res: dict) -> str:
    lines = [f"{'Typ':9} {'erwartet':>8} {'geliefert':>9} {'Treffer':>7} {'Recall':>7} {'Precision':>9}"]
    for k in ("modified", "removed", "added", "all"):
        v = res[k]
        lines.append(f"{k:9} {v['expected']:8} {v['got']:9} {v['tp']:7} {v['recall']:7.3f} {v['precision']:9.3f}")
    lines.append(f"F2 gesamt: {res['all']['f2']:.3f}  (lokale Näherung: id bzw. Absatzlabel, nicht semantisch)")
    return "\n".join(lines)


def cmd_run(a: argparse.Namespace) -> int:
    folder = Path(a.folder)
    reqs = json.loads((folder / "requirements_old.json").read_text(encoding="utf-8"))
    team = a.team_id or os.environ.get("CERTIVITY_TEAM_ID") or TEAM_ID
    sub = compare(folder / "old.pdf", folder / "new.pdf", reqs, team, f"subgoal-{folder.name}")
    from . import paths
    out = Path(a.out) if a.out else paths.OUT_DIR / f"{sub['case_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sub, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    from collections import Counter
    print(f"{out}: {dict(Counter(c['change'] for c in sub['changes']))}")
    return 0


def cmd_eval(a: argparse.Namespace) -> int:
    from . import paths
    sub = json.loads(Path(a.submission).read_text(encoding="utf-8"))
    exp_path = Path(a.expected) if a.expected else paths.PKG_DIR / "subgoal" / sub["case_id"].removeprefix("subgoal-") / "expected.json"
    print(format_eval(evaluate(sub, json.loads(exp_path.read_text(encoding="utf-8")))))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="certreq.subgoal", description=__doc__.splitlines()[0])
    s = p.add_subparsers(dest="cmd", required=True)
    r = s.add_parser("run")
    r.add_argument("folder", help="subgoal-Ordner mit old.pdf, new.pdf, requirements_old.json")
    r.add_argument("--out")
    r.add_argument("--team-id")
    r.set_defaults(func=cmd_run)
    e = s.add_parser("eval")
    e.add_argument("submission")
    e.add_argument("--expected")
    e.set_defaults(func=cmd_eval)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
