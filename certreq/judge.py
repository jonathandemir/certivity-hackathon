"""AP10: Lokaler LLM-Richter für die Anforderungsebene, nachgebildet nach dem Plattform-Score.

Plattform (Paket-README „How it is judged"): jede eingereichte Anforderung wird 1:1 einer erwarteten zugeordnet, die
dieselbe Engineering-Pflicht formuliert (gleicher Geltungsbereich, gleiche Bedingung, gleicher Grenzwert).
Precision = Anteil unserer Anforderungen mit Partner, Recall = Anteil der erwarteten mit Partner, Ranking F2.

Vorgehen:
1. Kandidaten (Blocking): je erwarteter Anforderung unsere Anforderungen derselben Regelung mit gleichem Absatz oder
   höchstens WINDOW Seiten Abstand (Annahme: dieselbe Pflicht wird nicht in einer anderen Regelung oder weit entfernt
   zitiert). Ohne Kandidaten kein LLM-Aufruf.
2. LLM (llm.STRONG_MODEL) entscheidet je erwarteter Anforderung, welche Kandidaten dieselbe Pflicht formulieren.
   lenient=True: ein Kandidat mit weiteren Pflichten zählt, wenn eine davon passt (ein zusammengefasster Absatz kann so
   höchstens eine erwartete Anforderung abdecken, wie die Plattform es beschreibt: „merges … recall drops").
   lenient=False: nur Kandidaten, die genau diese eine Pflicht formulieren. Welche Variante näher an der Plattform liegt,
   klärt der Abgleich mit dem Plattform-Score (docs/STATUS.md).
3. 1:1-Zuordnung als maximales bipartites Matching (Kuhn).

Lizenz: Der vollständige Bericht (mit Texten aus expected.json) bleibt unter out/; ins Repo (experiments/runs/) gehen nur
Kennzahlen und IDs (`public_summary`).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import llm

WINDOW = 1  # Seitenabstand für Kandidaten
MAX_CANDIDATES = 40
MAX_TEXT = 1500  # Zeichen je Kandidatentext im Prompt

SYSTEM = """You compare engineering requirements derived from UN vehicle regulations (UNECE).
Decide which candidate requirements state the same engineering obligation as the reference requirement:
- same scope: the same device, part, function or vehicle aspect it applies to,
- same condition: the same circumstances, test conditions or case distinctions,
- same constraint: what must be met, including the same limits, values, units and directions.
{mode}
A candidate does NOT match if it only shares the topic or the paragraph, if it states a different limit or value, applies
to a different device or lamp type, or applies under a different condition.
Return the ids of all matching candidates (often exactly one, sometimes none) and a short reason."""
LENIENT = ("A candidate may contain additional obligations; it matches if one of its obligations is the reference "
           "obligation with the same scope, condition and constraint.")
STRICT = "A candidate matches only if it states this obligation and no substantially different further obligation."


def _para_key(paragraph: str | None) -> str:
    """Absatzlabel normalisiert wie auf der Plattform (Groß/klein, Leerzeichen, Kommas, Schlusspunkt egal)."""
    if not paragraph:
        return ""
    p = re.split(r"\.?\s*table\b", paragraph.lower())[0]
    return re.sub(r"[\s,]+", " ", p).strip().rstrip(".").strip()


def candidates(expected: list[dict], ours: list[dict], window: int = WINDOW) -> dict[str, list[dict]]:
    by_reg: dict[str, list[dict]] = defaultdict(list)
    for r in ours:
        by_reg[r["source"]["regulation"]].append(r)
    out = {}
    for e in expected:
        es = e["source"]
        ek, ep = _para_key(es.get("paragraph")), es["page"]
        cands = [r for r in by_reg.get(es["regulation"], [])
                 if (ek and _para_key(r["source"].get("paragraph")) == ek) or abs(r["source"]["page"] - ep) <= window]
        cands.sort(key=lambda r: (_para_key(r["source"].get("paragraph")) != ek, abs(r["source"]["page"] - ep)))
        out[e["id"]] = cands[:MAX_CANDIDATES]
    return out


def _request(e: dict, cands: list[dict], lenient: bool) -> dict:
    ids = [f"c{i}" for i in range(1, len(cands) + 1)]
    s = e["source"]
    lines = [f"Reference requirement ({s['regulation']}, paragraph {s.get('paragraph', '?')}, page {s['page']}):",
             e["text"], "", "Candidates:"]
    for cid, r in zip(ids, cands):
        rs = r["source"]
        lines.append(f"[{cid}] ({rs['regulation']}, paragraph {rs.get('paragraph', '?')}, page {rs['page']}) "
                     f"{r['text'][:MAX_TEXT]}")
    schema = {"type": "object", "additionalProperties": False, "required": ["matching_ids", "reason"],
              "properties": {"matching_ids": {"type": "array", "items": {"type": "string", "enum": ids}},
                             "reason": {"type": "string"}}}
    return dict(system=SYSTEM.format(mode=LENIENT if lenient else STRICT), user="\n".join(lines), schema=schema,
                name="match", model=llm.STRONG_MODEL, effort="low")


def max_matching(edges: dict[str, list[str]]) -> dict[str, str]:
    """Maximales bipartites Matching (Kuhn). edges: erwartete ID → passende eigene IDs. Ergebnis: erwartet → eigen."""
    owner: dict[str, str] = {}

    def augment(e: str, seen: set[str]) -> bool:
        for o in edges.get(e, []):
            if o in seen:
                continue
            seen.add(o)
            if o not in owner or augment(owner[o], seen):
                owner[o] = e
                return True
        return False

    for e in sorted(edges, key=lambda k: len(edges[k])):  # wenig Optionen zuerst
        augment(e, set())
    return {e: o for o, e in owner.items()}


def judge(submission: dict, expected: list[dict], lenient: bool = True, workers: int = 8) -> dict:
    ours = submission["requirements"]
    cands = candidates(expected, ours)
    todo = [e for e in expected if cands[e["id"]]]
    answers = llm.ask_many([_request(e, cands[e["id"]], lenient) for e in todo], workers=workers) if todo else []
    edges: dict[str, list[str]] = {e["id"]: [] for e in expected}
    reasons = {}
    for e, ans in zip(todo, answers):
        cid_to_id = {f"c{i}": r["id"] for i, r in enumerate(cands[e["id"]], start=1)}
        edges[e["id"]] = [cid_to_id[c] for c in ans["matching_ids"] if c in cid_to_id]
        reasons[e["id"]] = ans.get("reason", "")
    match = max_matching(edges)
    n_ours, n_exp, n = len(ours), len(expected), len(match)
    p = n / n_ours if n_ours else 0.0
    r = n / n_exp if n_exp else 0.0
    per_reg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for e in expected:
        per_reg[e["source"]["regulation"]][1] += 1
        if e["id"] in match:
            per_reg[e["source"]["regulation"]][0] += 1
    return {
        "level": {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0,
                  "f2": round(5 * p * r / (4 * p + r), 4) if p + r else 0.0,
                  "n_submitted": n_ours, "n_expected": n_exp, "n_matched": n},
        "config": {"model": llm.STRONG_MODEL, "lenient": lenient, "window": WINDOW, "max_candidates": MAX_CANDIDATES},
        "recall_by_regulation": {k: f"{v[0]}/{v[1]}" for k, v in sorted(per_reg.items())},
        "no_candidates": sorted(e["id"] for e in expected if not cands[e["id"]]),
        "llm_said_match_but_unassigned": sorted(e for e, os_ in edges.items() if os_ and e not in match),
        "matches": sorted(match.items()),
        "missed": [{"id": e["id"], "regulation": e["source"]["regulation"], "paragraph": e["source"].get("paragraph"),
                    "page": e["source"]["page"], "text": e["text"], "n_candidates": len(cands[e["id"]]),
                    "reason": reasons.get(e["id"], "")} for e in expected if e["id"] not in match],
        "llm_usage": llm.usage(),
    }


def public_summary(report: dict) -> dict:
    """Ohne Texte aus expected.json (Lizenz: keine Weitergabe) – das darf nach experiments/runs/."""
    return {k: v for k, v in report.items() if k not in ("missed",)} | {
        "missed_ids": [m["id"] for m in report["missed"]]}


def main(argv: list[str]) -> int:
    import argparse

    from . import paths
    ap = argparse.ArgumentParser(prog="python -m certreq.judge", description="Lokaler Richter für die Anforderungsebene")
    ap.add_argument("submission")
    ap.add_argument("--expected", help="Standard: cases/<case_id>/expected.json")
    ap.add_argument("--strict", action="store_true", help="nur exakt eine Pflicht pro Kandidat zählt")
    args = ap.parse_args(argv)
    sub = json.loads(Path(args.submission).read_text(encoding="utf-8"))
    exp_path = Path(args.expected) if args.expected else paths.CASES_DIR / sub["case_id"] / "expected.json"
    expected = json.loads(exp_path.read_text(encoding="utf-8"))["requirements"]
    report = judge(sub, expected, lenient=not args.strict)
    out = Path(args.submission).with_suffix(".judge.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lv = report["level"]
    print(f"Anforderungsebene (lokaler Richter, {'strikt' if args.strict else 'tolerant'}): P {lv['precision']:.3f} "
          f"R {lv['recall']:.3f} F2 {lv['f2']:.3f}  ({lv['n_submitted']}/{lv['n_expected']}/{lv['n_matched']})")
    print(f"Recall je Regelung: {report['recall_by_regulation']}  Bericht: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
