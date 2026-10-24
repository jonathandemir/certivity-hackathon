"""AP7 Sub-Goal: Welche Anforderungen aus Version A ändern sich in Version B einer Regelung?

    .venv/bin/python -m certreq.subgoal run  vendor/industrial-ai-hackathon/subgoal/dev [--out out/subgoal-dev.json]
    .venv/bin/python -m certreq.subgoal eval out/subgoal-dev.json            # Recall/Precision gegen expected.json

Verfahren (regelbasiert, ohne LLM; jede Stufe ist austauschbar):
1. Alt- und Neu-PDF mit `certreq.pdf.parse_pdf` in Absätze zerlegen, diese in Sätze und Aufzählungspunkte.
2. Jede alte Anforderung wird den alten Sätzen zugeordnet, aus denen sie stammt (Absatzlabel + Wortüberdeckung).
3. Jeder alte Satz sucht global den ähnlichsten neuen Satz (nicht nur gleiches Label: Absätze werden verschoben und
   umnummeriert). Identisch → unverändert; ähnlich → `modified`; kein Gegenstück → `removed`.
4. Neue Sätze mit „shall“ ohne alte Entsprechung → `added`.
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

SHALL_RE = re.compile(r"\bshall\b", re.IGNORECASE)
HEADER_RE = re.compile(r"^(UN [^,|]+?), version (\S+) \| page \d+ of \d+", re.M)
# Satzende: . ; : gefolgt von Großbuchstabe oder Aufzählungsklammer. „5.1.2. are“ (klein) trennt nicht.
SPLIT_RE = re.compile(r"(?<=[.;:])\s+(?=[A-Z(])|\s+(?=\([a-z]\)\s)|\s+(?=\([ivx]+\)\s)")
TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*|[^\sa-z0-9]", re.I)
MODIFIED_MIN = 0.55  # darunter gilt ein alter Satz als ersatzlos weg
MAX_TEXT = 2000
PLACEHOLDER_TEAM = "team-unregistered"
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
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        x, y = " ".join(a[i1:i2]), " ".join(b[j1:j2])
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


def _sources_of(req: dict, old_sents: list[Sentence]) -> list[Sentence]:
    """Alte Sätze, aus denen die Anforderung abgeleitet wurde (Label + Wortüberdeckung)."""
    label = req["source"].get("paragraph", "")
    rt = set(_tokens(req["text"]))
    pool = [s for s in old_sents if s.label == label] or old_sents
    scored = []
    for s in pool:
        st = set(_tokens(s.text))
        if not st:
            continue
        cover = len(st & rt) / len(st)  # wie viel des Satzes steckt in der Anforderung
        within = len(rt & st) / (len(rt) or 1)  # wie viel der Anforderung steckt im Satz
        scored.append((max(cover, within * 0.9), s))
    hits = [s for sc, s in scored if sc >= 0.8]
    if not hits and scored:
        hits = [max(scored, key=lambda t: t[0])[1]]
    return hits


def compare(old_pdf: Path, new_pdf: Path, reqs_old: list[dict], team_id: str, case_id: str) -> dict:
    regulation, version = pdf_header(new_pdf)
    old_s, new_s = sentences_of(old_pdf), sentences_of(new_pdf)
    idx = Index(new_s)
    used_new: set[int] = set()
    changes: list[dict] = []
    for req in reqs_old:
        srcs = _sources_of(req, old_s)
        modified, missing = [], []
        for s in srcs:
            i, r = idx.best(s.full)
            if i >= 0 and r >= MODIFIED_MIN:
                used_new.add(i)
                if r < 0.999 and _canon(s.full).lower() != _canon(new_s[i].full).lower():
                    modified.append((s, new_s[i]))
            else:
                missing.append(s)
        label_old = req["source"].get("paragraph", "")
        if modified:
            olds = " ".join(s.text for s, _ in modified)
            news = " ".join(n.text for _, n in modified)
            n0 = modified[0][1]
            former = f" (formerly {label_old})" if n0.label != label_old else ""
            plist = diff_phrases(olds, news)
            if not plist:
                continue  # nur Schreibweise/Überschrift/Umnummerierung
            phrases = "; ".join(plist)
            changes.append({"requirement_id": req["id"], "change": "modified", "new_text": _norm(news)[:MAX_TEXT],
                            "reason": f"Paragraph {n0.label}{former} of {regulation} was amended in version {version}: "
                                      f"{phrases}.", "source": {"page": n0.page, "paragraph": n0.label}})
        elif missing and len(missing) == len(srcs):
            gone = " ".join(s.text for s in missing)[:300]
            changes.append({"requirement_id": req["id"], "change": "removed", "new_text": None,
                            "reason": f"Paragraph {label_old} of {regulation} was amended in version {version}; "
                                      f"the provision '{gone}' was removed."})
    old_idx = Index(old_s)
    mod_sets = [set(_tokens(_canon(c["new_text"]))) for c in changes if c["change"] == "modified"]
    for i, s in enumerate(new_s):
        if i in used_new or not SHALL_RE.search(s.full) or ADMIN_RE.search(s.full):
            continue
        if s.text.endswith(":") and not s.lead:
            continue  # bloße Einleitung („…shall be as follows:“); die Pflichten stehen in den Aufzählungspunkten
        st = set(_tokens(_canon(s.full)))
        if any(len(st & m) / (len(st) or 1) >= 0.8 for m in mod_sets):
            continue  # steckt schon in einer `modified`-Meldung
        j, r = old_idx.best(s.full)
        if r >= MODIFIED_MIN:  # steht (ähnlich) schon in der alten Fassung, nur ohne Anforderung → nicht neu
            continue
        changes.append({"requirement_id": None, "change": "added", "new_text": _norm(s.full)[:MAX_TEXT],
                        "reason": f"Paragraph {s.label} of {regulation} is new in version {version}: "
                                  f"'{s.text[:300]}'.", "source": {"page": s.page, "paragraph": s.label}})
    return {"team_id": team_id, "case_id": case_id, "changes": changes}


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
    team = a.team_id or os.environ.get("CERTIVITY_TEAM_ID") or PLACEHOLDER_TEAM
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
