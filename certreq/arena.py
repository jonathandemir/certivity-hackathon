"""Arena: selbstständige Verbesserungsschleife mit strenger Trennung von Tune und Holdout.

    .venv/bin/python -m certreq.arena select            # Regelungsauswahl (Hauptziel, Stufe 1), läuft bis Strg+C
    .venv/bin/python -m certreq.arena subgoal           # Sub-Goal (Flags + Texte)
    .venv/bin/python -m certreq.arena select --rounds 5 --resume

Ablauf je Runde:
1. Ein Sprachmodell (der „Trainer") sieht die aktuelle Fassung, die Fehler auf dem TUNE-Set und die bisherigen
   Versuche und schlägt EINE allgemeine Änderung vor (Hypothese + neue Fassung).
2. Die Fassung wird auf Tune UND Holdout gemessen. Der Trainer sieht nur Tune-Fehler; Holdout-Ergebnisse bekommt er
   nie zu sehen (sonst wäre es kein Holdout mehr).
3. Übernommen wird nur, was auf Tune besser ist. Fällt Holdout dabei unter die Basislinie, steht „Overfitting-Verdacht"
   im Protokoll, und die empfohlene Fassung (best-guidance.txt) ist die beste, deren Holdout nicht schlechter ist.
4. Jede Runde wird gedruckt und in out/arena/<spur>/history.jsonl abgelegt; --resume setzt dort fort.

Schutz gegen Auswendiglernen: Der Trainer darf keine Marken, Teilenummern oder Bauteilnamen aus den Testfällen
nennen (Vorschläge mit solchen Wörtern werden verworfen), nur allgemeine Grundsätze der Typgenehmigung.

Die Arena ändert keinen Code: Sie hängt die Fassung zur Laufzeit an den Prompt (select.SYSTEM2 bzw. die Sub-Goal-
Parameter). Eine gute Fassung übernimmt das Team bewusst (Ledger-Zeile, Messung), nicht die Arena.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import llm, paths

OUT = paths.OUT_DIR / "arena"
REAL = paths.REPO_ROOT / "experiments" / "real-parts"
SYNTH = paths.REPO_ROOT / "experiments" / "selection-suite"
SUBSUITE = paths.REPO_ROOT / "experiments" / "subgoal-suite"
GUARD = paths.REPO_ROOT / "experiments" / "guard-cases"  # Schutzfälle (z. B. Frontstoßfänger), gehören immer zu tune
MAX_GUIDANCE_WORDS = 300


# ------------------------------------------------------------------ gemeinsame Teile
def f2(p: float, r: float) -> float:
    return 5 * p * r / (4 * p + r) if p + r else 0.0


def now() -> str:
    return datetime.now().astimezone().strftime("%H:%M:%S")


def forbidden_words() -> set[str]:
    """Marken/Namen aus den echten Teilen (erstes Wort des Ordnernamens) + Teilenummern: dürfen nie in eine Fassung."""
    words = set()
    for split in ("tune", "holdout"):
        d = REAL / split
        if d.is_dir():
            for c in d.iterdir():
                if c.is_dir():
                    words.add(c.name.split("-")[0])
    words |= {"tesla", "model 3", "ktm", "husqvarna", "yamaha", "nissan", "citro", "peugeot", "mini cooper"}
    return {w for w in words if len(w) >= 2}


def leaks(text: str, words: set[str]) -> list[str]:
    low = text.lower()
    hits = [w for w in words if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low)]
    hits += re.findall(r"\b\d[A-Z]{1,3} ?\d{3} ?\d{3}", text)  # Hella-Teilenummern u. Ä.
    return hits


def usage_tokens() -> int:
    u = llm.usage()
    return int(u.get("prompt_tokens", 0) + u.get("completion_tokens", 0))


class Log:
    def __init__(self, track: str, resume: bool):
        self.dir = OUT / track
        self.dir.mkdir(parents=True, exist_ok=True)
        self.hist_p = self.dir / "history.jsonl"
        if not resume and self.hist_p.exists():
            self.hist_p.rename(self.dir / f"history-{datetime.now():%Y%m%d-%H%M%S}.jsonl")
        self.history = [json.loads(l) for l in self.hist_p.read_text().splitlines()] if self.hist_p.exists() else []

    def add(self, entry: dict) -> None:
        self.history.append(entry)
        with self.hist_p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_best(self, name: str, data: dict, text: str) -> None:
        (self.dir / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (self.dir / f"{name}.txt").write_text(text + "\n", encoding="utf-8")


def ask_trainer(system: str, user: str, schema: dict) -> dict:
    return llm.ask_json(system, user, schema, name="trainer", model=llm.STRONG_MODEL)


# ------------------------------------------------------------------ Spur „select" (Hauptziel, Regelungsauswahl)
def select_cases() -> dict[str, list[dict]]:
    """tune = synthetische Suite + Schutzfälle + echte Teile (tune) + Dev-Rückleuchte (Gold aus expected.json);
    holdout = echte Teile (holdout)."""
    sets: dict[str, list[dict]] = {"tune": [], "holdout": []}

    def from_suite(folder: Path, split: str, tag: str):
        exp_p = folder / "expected.json"
        if not exp_p.exists():
            return
        for name, exp in json.loads(exp_p.read_text(encoding="utf-8"))["components"].items():
            if (folder / name).is_dir():
                sets[split].append({"name": f"{tag}/{name}", "dir": folder / name, "exp": exp})

    from_suite(SYNTH, "tune", "synth")
    from_suite(GUARD, "tune", "guard")
    from_suite(REAL / "tune", "tune", "real")
    from_suite(REAL / "holdout", "holdout", "real")
    dev = paths.CASES_DIR / "dev-rear-lamp"
    if (dev / "expected.json").exists():
        gold = sorted({r["source"]["regulation"] for r in json.loads((dev / "expected.json").read_text())["requirements"]})
        sets["tune"].append({"name": "certivity/dev-rear-lamp", "dir": dev, "exp": {"sure": gold, "unsure": [], "traps": [],
                             "basis": "Certivity-Gold (expected.json)"}})
    return sets


def run_select(guidance: str, cases: list[dict], workers: int = 6) -> dict:
    from . import select as sel
    from .case import load_case
    from .suite import score_component, summarize

    base = getattr(sel, "_ARENA_BASE", None) or sel.SYSTEM2
    sel._ARENA_BASE = base
    sel.SYSTEM2 = base + (f"\n\nAdditional principles (learned on validation cases):\n{guidance.strip()}" if guidance.strip() else "")

    def one(c: dict):
        try:
            regs = sel.select_regulations(load_case(c["dir"]), mode="llm2")
            return c["name"], [r.name for r in regs]
        except Exception as e:  # noqa: BLE001 – ein Fehler soll die Runde nicht abbrechen
            print(f"  ! {c['name']}: {e}", file=sys.stderr)
            return c["name"], None

    with ThreadPoolExecutor(workers) as ex:
        answers = list(ex.map(one, cases))
    by = {c["name"]: c for c in cases}
    res = {n: score_component(s, by[n]["exp"]) for n, s in answers if s is not None}
    return {"summary": summarize(res), "components": res, "failed": [n for n, s in answers if s is None]}


SELECT_TRAINER = """You improve the regulation-selection step of a UNECE type-approval assistant. The step gets a component
specification plus a catalogue of 56 UN Regulations and must select every regulation with requirements for that
component or its installation, and nothing else. Its base prompt is fixed; you write an extra block of
"Additional principles" that is appended to it.

You see results on a TUNE set only (synthetic and real components with known approvals). A hidden HOLDOUT set of
other real components decides whether your principles generalise, so:
- write general type-approval principles (scope logic, consolidated vs. replaced regulations, device vs. installation
  vs. vehicle level, light source vs. lamp, replacement parts, electronics/EMC, vehicle categories, when nothing in the
  catalogue applies), never rules about one product;
- never mention brands, product names, part numbers or the component names you see;
- you may name regulations by number when the principle is general (e.g. which regulation covers a device class);
- keep the whole block under 300 words, as numbered rules; delete rules that do not help.
Change ONE thing per round (add, sharpen, merge or remove a rule) so its effect can be measured, and state the
hypothesis. Look at the history: do not repeat a change that did not help."""

SELECT_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["hypothesis", "guidance"],
                 "properties": {"hypothesis": {"type": "string"}, "guidance": {"type": "string"}}}


def select_feedback(rep: dict, cases: list[dict]) -> str:
    by = {c["name"]: c for c in cases}
    lines = []
    for name, r in sorted(rep["components"].items()):
        if not r["missing"] and not r["wrong"]:
            continue
        c = by[name]
        spec = re.sub(r"\s+", " ", (c["dir"] / "spec.md").read_text(encoding="utf-8") if (c["dir"] / "spec.md").exists()
                      else "")[:500]
        lines.append(f"- {name.split('/')[0]} component (spec excerpt: {spec})\n  selected: {r['selected']}\n"
                     f"  missing: {r['missing']}  wrongly added: {r['wrong']}\n  why the gold is what it is: "
                     f"{c['exp'].get('basis', '')[:400]}")
    return "\n".join(lines) or "(no errors on tune)"


def fmt(s: dict) -> str:
    return f"P {s['precision']:.3f} R {s['recall']:.3f} F2 {s['f2']:.3f} · exakt {s['components_exact']}/{s['components']}"


def arena_select(a: argparse.Namespace) -> int:
    sets = select_cases()
    words = forbidden_words()
    log = Log("select", a.resume)
    print(f"[{now()}] Arena „select“: tune {len(sets['tune'])} Bauteile, holdout {len(sets['holdout'])} "
          f"(Holdout sieht der Trainer nie). Modell: {llm.model_name(llm.STRONG_MODEL)}. Abbruch: Strg+C.\n")
    start_tok = usage_tokens()
    if log.history:
        base = log.history[0]
        best = max((h for h in log.history if h["accepted"]), key=lambda h: (h["tune"]["f2"], -h["tune"]["wrong"]))
        print(f"Fortsetzung: {len(log.history)} Runden, beste Tune-F2 {best['tune']['f2']:.3f}\n")
    else:
        t0 = time.time()
        rt, rh = run_select("", sets["tune"]), run_select("", sets["holdout"])
        base = {"round": 0, "hypothesis": "Basislinie (ohne Zusatzregeln)", "guidance": "", "tune": rt["summary"],
                "holdout": rh["summary"], "accepted": True, "tune_detail": rt["components"], "at": now()}
        log.add(base)
        best = base
        print(f"Runde 0 · Basislinie · {time.time() - t0:.0f} s\n  tune    {fmt(rt['summary'])}\n"
              f"  holdout {fmt(rh['summary'])}\n")
    rnd = len(log.history)
    limit = rnd + a.rounds if a.rounds else None
    while limit is None or rnd < limit:
        t0 = time.time()
        tried = "\n".join(f"- round {h['round']}: {h['hypothesis'][:200]} → tune F2 {h['tune']['f2']:.3f} "
                          f"({'kept' if h['accepted'] else 'rejected'})" for h in log.history[-10:])
        user = (f"CURRENT PRINCIPLES (tune F2 {best['tune']['f2']:.3f}, P {best['tune']['precision']:.3f}, "
                f"R {best['tune']['recall']:.3f}):\n{best['guidance'] or '(none yet)'}\n\n"
                f"ERRORS ON TUNE WITH THE CURRENT PRINCIPLES:\n"
                f"{select_feedback({'components': best['tune_detail']}, sets['tune'])}\n\nHISTORY:\n{tried}")
        prop = None
        for attempt in range(3):
            p = ask_trainer(SELECT_TRAINER, user + (f"\n\n(Attempt {attempt + 1}: previous proposal was rejected for "
                                                    "naming products/brands or being too long.)" if attempt else ""),
                            SELECT_SCHEMA)
            bad = leaks(p["guidance"], words)
            if not bad and len(p["guidance"].split()) <= MAX_GUIDANCE_WORDS:
                prop = p
                break
            print(f"  (Vorschlag verworfen: {'nennt ' + ', '.join(bad) if bad else 'zu lang'})")
        if prop is None:
            rnd += 1
            continue
        rt, rh = run_select(prop["guidance"], sets["tune"]), run_select(prop["guidance"], sets["holdout"])
        better = (rt["summary"]["f2"], -rt["summary"]["wrong"]) > (best["tune"]["f2"] + a.min_delta, -best["tune"]["wrong"])
        overfit = better and rh["summary"]["f2"] < base["holdout"]["f2"] - a.tolerance
        entry = {"round": rnd, "hypothesis": prop["hypothesis"], "guidance": prop["guidance"], "tune": rt["summary"],
                 "holdout": rh["summary"], "accepted": better, "overfit_suspect": overfit,
                 "tune_detail": rt["components"], "at": now()}
        log.add(entry)
        if better:
            best = entry
        safe = max((h for h in log.history if h["accepted"] and h["holdout"]["f2"] >= base["holdout"]["f2"] - a.tolerance),
                   key=lambda h: (h["tune"]["f2"], h["holdout"]["f2"]), default=base)
        log.save_best("best-guidance", {k: safe[k] for k in ("round", "hypothesis", "guidance", "tune", "holdout")},
                      safe["guidance"])
        d = rt["summary"]["f2"] - log.history[-2]["tune"]["f2"] if len(log.history) > 1 else 0
        print(f"Runde {rnd} · {time.time() - t0:.0f} s · Tokens bisher {(usage_tokens() - start_tok) / 1e6:.2f} M\n"
              f"  Idee:    {prop['hypothesis'][:220]}\n"
              f"  tune    {fmt(rt['summary'])}  (bisher bestes {best['tune']['f2']:.3f})\n"
              f"  holdout {fmt(rh['summary'])}  (Basis {base['holdout']['f2']:.3f})\n"
              f"  → {'ÜBERNOMMEN' if better else 'verworfen'}{'  ⚠ Overfitting-Verdacht: Holdout schlechter' if overfit else ''}"
              f"   · Empfehlung: Runde {safe['round']} (out/arena/select/best-guidance.txt)\n")
        rnd += 1
    return 0


# ------------------------------------------------------------------ Spur „subgoal"
def subgoal_cases() -> dict[str, list[dict]]:
    """tune = Paket-Fall subgoal/dev (+ experiments/subgoal-suite/tune), holdout = experiments/subgoal-suite/holdout.
    Ein Fall der Suite: Ordner mit case.json {old_pdf, new_pdf, requirements_old, expected} (Pfade relativ zum Repo)."""
    sets: dict[str, list[dict]] = {"tune": [], "holdout": []}
    dev = paths.PKG_DIR / "subgoal" / "dev"
    if (dev / "expected.json").exists():
        sets["tune"].append({"name": "certivity/subgoal-dev", "old": dev / "old.pdf", "new": dev / "new.pdf",
                             "reqs": dev / "requirements_old.json", "exp": dev / "expected.json"})
    for split in ("tune", "holdout"):
        d = SUBSUITE / split
        for c in sorted(d.iterdir()) if d.is_dir() else []:
            if (c / "case.json").exists():
                j = json.loads((c / "case.json").read_text(encoding="utf-8"))
                sets[split].append({"name": f"official/{c.name}", **{k: paths.REPO_ROOT / j[v] for k, v in
                                    (("old", "old_pdf"), ("new", "new_pdf"), ("reqs", "requirements_old"))},
                                    "exp": c / j.get("expected", "expected.json")})
    return sets


SUB_DEFAULT = {"modified_min": 0.55, "refine": "llm", "added_guidance": ""}


def run_subgoal(cfg: dict, cases: list[dict], workers: int = 4) -> dict:
    from . import subgoal as sg

    base_add = getattr(sg, "_ARENA_ADD", None) or sg.REFINE_ADD
    sg._ARENA_ADD = base_add
    sg.MODIFIED_MIN = float(cfg["modified_min"])
    sg.REFINE_ADD = base_add + (f"\nAdditional rules:\n{cfg['added_guidance']}" if cfg.get("added_guidance") else "")

    def one(c: dict):
        try:
            reqs = json.loads(Path(c["reqs"]).read_text(encoding="utf-8"))
            sub = sg.compare(c["old"], c["new"], reqs, "team-x", "arena", refine=cfg["refine"])
            return c["name"], sg.evaluate(sub, json.loads(Path(c["exp"]).read_text(encoding="utf-8"))), sub
        except Exception as e:  # noqa: BLE001
            print(f"  ! {c['name']}: {e}", file=sys.stderr)
            return c["name"], None, None

    with ThreadPoolExecutor(workers) as ex:
        out = list(ex.map(one, cases))
    tp = sum(r["all"]["tp"] for _, r, _ in out if r)
    ne = sum(r["all"]["expected"] for _, r, _ in out if r)
    ng = sum(r["all"]["got"] for _, r, _ in out if r)
    p, r_ = (tp / ng if ng else 0.0), (tp / ne if ne else 0.0)
    return {"summary": {"precision": p, "recall": r_, "f2": f2(p, r_), "tp": tp, "expected": ne, "got": ng,
                        "cases": len(out)}, "cases": {n: r for n, r, _ in out if r}}


SUB_TRAINER = """You tune a rule-based + LLM tool that compares two versions of a UN Regulation and flags which requirements
were modified, removed or added. Knobs: modified_min (0.40–0.80, similarity above which an old sentence counts as
still present), refine ("none" or "llm": an LLM rewrites added obligations as standalone requirements),
added_guidance (extra rules for that LLM, max 150 words, general only, never mention specific paragraphs or values).
You see TUNE results only; a hidden HOLDOUT of other regulations decides. Change ONE knob per round and state why."""
SUB_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["hypothesis", "modified_min", "refine", "added_guidance"],
              "properties": {"hypothesis": {"type": "string"}, "modified_min": {"type": "number"},
                             "refine": {"type": "string", "enum": ["none", "llm"]}, "added_guidance": {"type": "string"}}}


def arena_subgoal(a: argparse.Namespace) -> int:
    sets = subgoal_cases()
    log = Log("subgoal", a.resume)
    print(f"[{now()}] Arena „subgoal“: tune {len(sets['tune'])} Fälle, holdout {len(sets['holdout'])}."
          + ("  ⚠ Kein Holdout vorhanden: Verbesserungen sind nicht gegen Overfitting geprüft." if not sets["holdout"] else "")
          + "\n")
    if log.history:
        base = log.history[0]
        best = max((h for h in log.history if h["accepted"]), key=lambda h: h["tune"]["f2"])
    else:
        rt = run_subgoal(SUB_DEFAULT, sets["tune"])
        rh = run_subgoal(SUB_DEFAULT, sets["holdout"]) if sets["holdout"] else None
        base = {"round": 0, "hypothesis": "Basislinie", "cfg": SUB_DEFAULT, "tune": rt["summary"],
                "holdout": rh["summary"] if rh else None, "accepted": True, "tune_detail": rt["cases"], "at": now()}
        log.add(base)
        best = base
        print(f"Runde 0 · Basislinie\n  tune    {sfmt(rt['summary'])}\n  holdout {sfmt(rh['summary']) if rh else '—'}\n")
    rnd = len(log.history)
    limit = rnd + a.rounds if a.rounds else None
    while limit is None or rnd < limit:
        tried = "\n".join(f"- round {h['round']}: {json.dumps(h['cfg'])} {h['hypothesis'][:150]} → tune F2 "
                          f"{h['tune']['f2']:.3f}" for h in log.history[-10:])
        detail = json.dumps(best["tune_detail"], ensure_ascii=False)[:3000]
        p = ask_trainer(SUB_TRAINER, f"CURRENT: {json.dumps(best['cfg'])} tune F2 {best['tune']['f2']:.3f}\n"
                                     f"PER-CASE COUNTS (tp/expected/got per change type): {detail}\n\nHISTORY:\n{tried}",
                        SUB_SCHEMA)
        cfg = {"modified_min": min(0.8, max(0.4, p["modified_min"])), "refine": p["refine"],
               "added_guidance": " ".join(p["added_guidance"].split()[:150])}
        t0 = time.time()
        rt = run_subgoal(cfg, sets["tune"])
        rh = run_subgoal(cfg, sets["holdout"]) if sets["holdout"] else None
        better = rt["summary"]["f2"] > best["tune"]["f2"] + a.min_delta
        overfit = bool(better and rh and base["holdout"] and rh["summary"]["f2"] < base["holdout"]["f2"] - a.tolerance)
        entry = {"round": rnd, "hypothesis": p["hypothesis"], "cfg": cfg, "tune": rt["summary"],
                 "holdout": rh["summary"] if rh else None, "accepted": better, "overfit_suspect": overfit,
                 "tune_detail": rt["cases"], "at": now()}
        log.add(entry)
        if better:
            best = entry
            log.save_best("best-config", {k: entry[k] for k in ("round", "hypothesis", "cfg", "tune", "holdout")},
                          json.dumps(cfg, ensure_ascii=False, indent=1))
        print(f"Runde {rnd} · {time.time() - t0:.0f} s\n  Idee:    {p['hypothesis'][:220]}\n  Konfig:  {json.dumps(cfg)[:200]}\n"
              f"  tune    {sfmt(rt['summary'])}  (bisher bestes {best['tune']['f2']:.3f})\n"
              f"  holdout {sfmt(rh['summary']) if rh else '—'}\n"
              f"  → {'ÜBERNOMMEN' if better else 'verworfen'}{'  ⚠ Overfitting-Verdacht' if overfit else ''}\n")
        rnd += 1
    return 0


def sfmt(s: dict) -> str:
    return f"Flags P {s['precision']:.3f} R {s['recall']:.3f} F2 {s['f2']:.3f} ({s['tp']}/{s['expected']}, geliefert {s['got']})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.arena", description=__doc__.splitlines()[0])
    ap.add_argument("track", choices=["select", "subgoal"])
    ap.add_argument("--rounds", type=int, default=0, help="Anzahl neuer Runden (0 = bis Strg+C)")
    ap.add_argument("--resume", action="store_true", help="bei out/arena/<spur>/history.jsonl weitermachen")
    ap.add_argument("--min-delta", type=float, default=0.005, help="so viel muss Tune-F2 mindestens steigen")
    ap.add_argument("--tolerance", type=float, default=0.02, help="erlaubter Holdout-Rückgang ohne Overfitting-Warnung")
    a = ap.parse_args(argv)
    try:
        return arena_select(a) if a.track == "select" else arena_subgoal(a)
    except KeyboardInterrupt:
        print("\nAbgebrochen. Stand: out/arena/" + a.track + "/ (history.jsonl, best-*)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
