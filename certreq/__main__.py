"""CLI.

    .venv/bin/python -m certreq run <fall-ordner> [--regs "UN R148,UN R48"] [--filters all] [--out out/<fall>.json] [--team-id ...]
    .venv/bin/python -m certreq eval <abgabe.json> [--record E001 --note "..."]

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
from .extract import extract_requirements
from .relevance import FILTERS
from .gitmeta import git_state
from .select import select_regulations
from .submission import build_submission, write_submission

PLACEHOLDER_TEAM = "team-unregistered"


def cmd_run(args: argparse.Namespace) -> int:
    t0 = time.time()
    case = load_case(args.case)
    forced = [r.strip() for r in args.regs.split(",")] if args.regs else None
    regs = select_regulations(case, forced)
    filters = _parse_filters(args.filters)
    reqs = extract_requirements(regs, case.spec_text, filters)
    team_id = args.team_id or os.environ.get("CERTIVITY_TEAM_ID") or PLACEHOLDER_TEAM
    data = build_submission(team_id, case.case_id, reqs)
    out = Path(args.out) if args.out else paths.OUT_DIR / f"{case.case_id}.json"
    write_submission(data, out)
    meta = {"case_id": case.case_id, "command": " ".join([Path(sys.executable).name, "-m", "certreq", *sys.argv[1:]]),
            "git": git_state(), "team_id": team_id, "selected": [r.name for r in regs], "forced": bool(forced),
            "filters": list(filters),
            "n_requirements": len(data["requirements"]), "seconds": round(time.time() - t0, 1),
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{out}: {meta['n_requirements']} Anforderungen aus {len(regs)} Regelung(en) {meta['selected']} "
          f"in {meta['seconds']} s, Stand {meta['git']['commit']}"
          + ("" if meta["git"]["clean"] else " (UNSAUBER: zählt nicht)"))
    if team_id == PLACEHOLDER_TEAM:
        print(f"Hinweis: team_id ist '{PLACEHOLDER_TEAM}'. Vor dem Upload CERTIVITY_TEAM_ID setzen bzw. --team-id angeben.")
    return 0


def _parse_filters(value: str | None) -> tuple[str, ...]:
    if not value or value == "none":
        return ()
    names = FILTERS if value == "all" else tuple(f.strip() for f in value.split(",") if f.strip())
    unknown = [f for f in names if f not in FILTERS]
    if unknown:
        raise SystemExit(f"Unbekannte Filter {unknown}. Erlaubt: {', '.join(FILTERS)}, all, none")
    return names


def cmd_eval(args: argparse.Namespace) -> int:
    sub = Path(args.submission)
    res = evaluate(sub, Path(args.expected) if args.expected else None)
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
    r.add_argument("--filters", help=f"Relevanzfilter (AP4), kommagetrennt aus {', '.join(FILTERS)}, oder all/none. "
                   "Standard: none (B0)")
    r.add_argument("--out", help="Ausgabedatei (Standard: out/<fall>.json)")
    r.add_argument("--team-id", help="Team-ID der Plattform (sonst $CERTIVITY_TEAM_ID)")
    r.set_defaults(func=cmd_run)
    e = sub.add_parser("eval", help="validieren, lokal bewerten (P/R/F1/F2), optional als Beleg ablegen")
    e.add_argument("submission")
    e.add_argument("--expected", help="Standard: cases/<case_id>/expected.json, falls vorhanden")
    e.add_argument("--record", metavar="ID", help="Ledger-ID, z. B. E001: Beleg nach experiments/runs/<ID>/")
    e.add_argument("--note", help="kurze Beschreibung für meta.json")
    e.add_argument("--allow-unclean", action="store_true", help="nur für Diagnosen: auch unsaubere Läufe ablegen")
    e.set_defaults(func=cmd_eval)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
