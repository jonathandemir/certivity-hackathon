"""CLI.

    .venv/bin/python -m certreq run <fall-ordner> [--regs "UN R148,UN R48"] [--filters all|none] [--extract modal,llm|none] [--out out/<fall>.json] [--team-id ...]
    .venv/bin/python -m certreq eval <abgabe.json> [--record E001 --note "..."]

Ohne Schalter läuft die Bestmarke E020-a (--select llm2 --filters all --extract modal,llm, braucht LLM-Key);
Baseline B0 ohne LLM: --select b0 --filters none --extract none.
Vor zählenden Läufen: scripts/pull-first (AGENTS.md §5).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from . import paths
from .case import load_case
from .evaluate import evaluate, format_result, record
from .extract import OPTIONS, extract_requirements
from .relevance import FILTERS
from .gitmeta import git_state
from . import vision
from .select import select_regulations
from .submission import TEAM_ID, build_submission, write_submission



def cmd_run(args: argparse.Namespace) -> int:
    t0 = time.time()
    case = load_case(args.case)
    case, drawing = vision.apply(case, args.vision)
    forced = [r.strip() for r in args.regs.split(",")] if args.regs else None
    selection: list = []
    regs = select_regulations(case, forced, mode=args.select, explain=selection)
    filters = _parse_filters(args.filters)
    options = _parse_list(args.extract, OPTIONS, "Extraktionsoptionen")
    llm_stats: dict = {}
    reqs = extract_requirements(regs, case.spec_text, filters, options, stats=llm_stats)
    team_id = args.team_id or os.environ.get("CERTIVITY_TEAM_ID") or TEAM_ID
    data = build_submission(team_id, case.case_id, reqs)
    out = Path(args.out) if args.out else paths.OUT_DIR / f"{case.case_id}.json"
    write_submission(data, out)
    meta = {"case_id": case.case_id, "command": " ".join([Path(sys.executable).name, "-m", "certreq", *sys.argv[1:]]),
            "git": git_state(), "team_id": team_id, "selected": [r.name for r in regs], "forced": bool(forced), "select_mode": args.select, "selection": selection, "vision_mode": args.vision, "drawing": drawing,
            "filters": list(filters), "extract": list(options), **_llm_meta(options, llm_stats),
            "n_requirements": len(data["requirements"]), "seconds": round(time.time() - t0, 1),
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out}: {meta['n_requirements']} Anforderungen aus {len(regs)} Regelung(en) {meta['selected']} "
          f"in {meta['seconds']} s, Stand {meta['git']['commit']}"
          + ("" if meta["git"]["clean"] else " (UNSAUBER: zählt nicht)"))
    return 0


def _llm_meta(options: tuple[str, ...], stats: dict) -> dict:
    if "llm" not in options:
        return {}
    from . import llm
    return {"llm": {"model": llm.model_name(), **stats, "usage": llm.usage()}}


def _parse_list(value: str | None, allowed: tuple[str, ...], what: str) -> tuple[str, ...]:
    if not value or value == "none":
        return ()
    names = allowed if value == "all" else tuple(f.strip() for f in value.split(",") if f.strip())
    unknown = [f for f in names if f not in allowed]
    if unknown:
        raise SystemExit(f"Unbekannte {what} {unknown}. Erlaubt: {', '.join(allowed)}, all, none")
    return names


def _parse_filters(value: str | None) -> tuple[str, ...]:
    return _parse_list(value, FILTERS, "Filter")


def cmd_eval(args: argparse.Namespace) -> int:
    sub = Path(args.submission)
    res = evaluate(sub, Path(args.expected) if args.expected else None, args.judge)
    print(format_result(res))
    if args.record:
        dest = record(args.record, sub, res, args.note or "", args.allow_unclean)
        print(f"\nBeleg abgelegt: {dest}\nWeiter (AGENTS.md §5): Zeile in experiments/LEDGER.md, ggf. Scoreboard in "
              f"docs/STATUS.md, dann im main-Worktree committen und scripts/sync.")
    return 0 if res["valid"] else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="certreq", description="Spezifikation → Anforderungen nach UN-Regelungen")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Fall-Ordner → Abgabe-JSON (+ .meta.json)")
    r.add_argument("case", help="Fall-Ordner, z. B. vendor/industrial-ai-hackathon/cases/dev-rear-lamp")
    r.add_argument("--regs", help="Regelungen vorgeben statt auswählen, kommagetrennt (Demo/Diagnose)")
    r.add_argument("--vision", choices=["auto", "off", "on", "only"], default="auto", help="Explosionszeichnung lesen (AP5): auto = nur wenn keine Spec da ist (Standard), on = Beschreibung an die Spec anhängen, only = nur die Zeichnung, off = nie")
    r.add_argument("--select", choices=["b0", "llm", "llm2"], default="llm2", help="Regelungsauswahl (AP2): llm2 = Steckbriefe + LLM ohne Annahmen und reine Fahrzeugebene (Standard seit E020-a), llm = ohne diesen Filter (E016-a), b0 = Titel-Wortüberlappung (Referenz E001); Begründungen in .meta.json")
    r.add_argument("--filters", default="all", help=f"Relevanzfilter (AP4), kommagetrennt aus {', '.join(FILTERS)}, oder all/none. "
                   "Standard: all (seit E020-a), none = B0")
    r.add_argument("--extract", default="modal,llm", help=f"Extraktionsoptionen (AP4), kommagetrennt aus {', '.join(OPTIONS)}, oder all/none. "
                   "Standard: modal,llm (seit E020-a, braucht LLM-Key), none = B0 (nur shall-Absätze, einer je Absatz)")
    r.add_argument("--out", help="Ausgabedatei (Standard: out/<fall>.json)")
    r.add_argument("--team-id", help=f"Team-ID der Plattform (sonst $CERTIVITY_TEAM_ID, sonst {TEAM_ID})")
    r.set_defaults(func=cmd_run)
    e = sub.add_parser("eval", help="validieren, lokal bewerten (P/R/F1/F2), optional als Beleg ablegen")
    e.add_argument("submission")
    e.add_argument("--expected", help="Standard: cases/<case_id>/expected.json, falls vorhanden")
    e.add_argument("--record", metavar="ID", help="Ledger-ID, z. B. E001: Beleg nach experiments/runs/<ID>/")
    e.add_argument("--note", help="kurze Beschreibung für meta.json")
    e.add_argument("--allow-unclean", action="store_true", help="nur für Diagnosen: auch unsaubere Läufe ablegen")
    e.add_argument("--judge", choices=["strict", "lenient"], help="Anforderungsebene per lokalem LLM-Richter (AP10)")
    e.set_defaults(func=cmd_eval)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
