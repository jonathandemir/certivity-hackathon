"""Auswahl-Test (Stufe 1) über synthetische Bauteile mit vorab festgelegten Lösungen.

    .venv/bin/python -m certreq.suite experiments/selection-suite [--select llm2] [--record X-SEL-a]

Jedes Unterverzeichnis mit Spec ist ein Bauteil; `expected.json` legt je Bauteil fest, welche Regelungen sicher gelten
(`sure`), welche vertretbar beides sind (`unsure`, zählen nicht) und welche bekannten Fallen es gibt (`traps`).
Gemessen wird nur die Regelungsauswahl (ein LLM-Aufruf je Bauteil), nicht die Extraktion. Die Lösung ist unser Urteil
aus den Geltungsbereichen, nicht Certivitys Gold: der Test zeigt Auswahlfehler außerhalb des Dev-Falls (zusammengelegte
Regelungen, Fahrzeugklasse, Fahrzeugebene), keinen Plattform-Score. Hintergrund: experiments/selection-suite/README.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import llm, paths
from .case import load_case
from .gitmeta import git_state
from .select import MODES, select_regulations


def f2(p: float, r: float) -> float:
    return 5 * p * r / (4 * p + r) if p + r else 0.0


def score_component(selected: list[str], exp: dict) -> dict:
    sel, sure, unsure = set(selected), set(exp["sure"]), set(exp.get("unsure", []))
    return {"selected": sorted(sel), "hits": sorted(sel & sure), "missing": sorted(sure - sel),
            "wrong": sorted(sel - sure - unsure), "traps_taken": sorted(sel & set(exp.get("traps", [])))}


def summarize(results: dict[str, dict]) -> dict:
    tp = sum(len(r["hits"]) for r in results.values())
    fn = sum(len(r["missing"]) for r in results.values())
    fp = sum(len(r["wrong"]) for r in results.values())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f2": round(f2(p, r), 4), "hits": tp, "missing": fn,
            "wrong": fp, "traps_taken": sum(len(x["traps_taken"]) for x in results.values()),
            "components": len(results),
            "components_exact": sum(1 for x in results.values() if not x["missing"] and not x["wrong"])}


def run_suite(folder: Path, mode: str = "llm2", workers: int = 5) -> dict:
    expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))["components"]

    def one(name: str) -> tuple[str, list[str], list]:
        explain: list = []
        regs = select_regulations(load_case(folder / name), mode=mode, explain=explain)
        return name, [r.name for r in regs], explain

    with ThreadPoolExecutor(max_workers=workers) as ex:
        answers = list(ex.map(one, sorted(expected)))
    results = {name: score_component(sel, expected[name]) | {"explain": explain} for name, sel, explain in answers}
    return {"suite": str(folder), "mode": mode, "model": llm.model_name(llm.STRONG_MODEL),
            "summary": summarize(results), "components": results, "llm_usage": llm.usage()}


def format_report(rep: dict) -> str:
    lines = [f"{'Bauteil':20} {'gewählt':>7}  fehlt / falsch (Fallen)"]
    for name, r in rep["components"].items():
        bad = ", ".join([f"-{x}" for x in r["missing"]] + [f"+{x}" for x in r["wrong"]]) or "ok"
        lines.append(f"{name:20} {len(r['selected']):7}  {bad}")
    s = rep["summary"]
    lines.append(f"Summe: P {s['precision']:.3f} R {s['recall']:.3f} F2 {s['f2']:.3f}  (Treffer {s['hits']}, fehlend "
                 f"{s['missing']}, falsch {s['wrong']}, davon Fallen {s['traps_taken']}; exakt {s['components_exact']}/"
                 f"{s['components']} Bauteile; Modus {rep['mode']}, Modell {rep['model']})")
    return "\n".join(lines)


def record(run_id: str, rep: dict, note: str) -> Path:
    git = git_state()
    if not (git["clean"] and git["pushed"]):
        raise SystemExit(f"Stand {git['commit']} ist nicht sauber und gepusht: zählt nicht (erst committen, scripts/sync).")
    dest = paths.REPO_ROOT / "experiments" / "runs" / run_id
    if dest.exists():
        raise SystemExit(f"{dest} existiert schon. Neue ID wählen.")
    dest.mkdir(parents=True)
    meta = {"run_id": run_id, "note": note, "git": git, "mode": rep["mode"], "model": rep["model"],
            "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (dest / "selection-suite.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.suite", description=__doc__.splitlines()[0])
    ap.add_argument("folder", nargs="?", default=str(paths.REPO_ROOT / "experiments" / "selection-suite"))
    ap.add_argument("--select", choices=[m for m in MODES if m != "b0"], default="llm2")
    ap.add_argument("--record", metavar="ID", help="Beleg nach experiments/runs/<ID>/ (nur sauberer, gepushter Stand)")
    ap.add_argument("--note", default="")
    args = ap.parse_args(argv)
    git = git_state() if args.record else None  # Stand vor dem Lauf festhalten
    rep = run_suite(Path(args.folder), args.select)
    out = paths.OUT_DIR / "suite" / f"selection-{args.select}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(format_report(rep))
    print(f"Bericht: {out}")
    if args.record:
        if git_state()["full_hash"] != git["full_hash"]:
            raise SystemExit("HEAD hat sich während des Laufs geändert: nicht abgelegt.")
        print(f"Beleg: {record(args.record, rep, args.note)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
