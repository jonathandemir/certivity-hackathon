"""Upload-Dateien aus gemessenen Läufen bauen: exakt die abgelegte Abgabe, nur mit echter Team-ID, validiert.

    .venv/bin/python -m certreq.upload E020-a E008-a E003-am          (Team-ID Standard: team-12)

Liest experiments/runs/<ID>/submission.json.gz, setzt team_id, schreibt out/upload/<ID>-<case_id>.json und prüft jede
Datei mit dem offiziellen validate.py (Sub-Goal mit requirements_old.json des Falls). So hat die hochgeladene Datei
genau den Inhalt, den wir lokal gemessen haben; der Plattformwert lässt sich 1:1 mit score.json vergleichen.
Am Sonntag gleich nutzen, um zuletzt die beste gemessene Held-out-Datei erneut hochzuladen (der letzte Upload zählt).
"""
from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
from pathlib import Path

from . import paths
from .submission import TEAM_ID

RUNS = paths.REPO_ROOT / "experiments" / "runs"
OUT = paths.OUT_DIR / "upload"


def load_run(run_id: str) -> dict:
    f = RUNS / run_id / "submission.json.gz"
    if not f.exists():
        raise SystemExit(f"{f} fehlt: Lauf {run_id} wurde nicht mit `eval --record` abgelegt.")
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def requirements_old(case_id: str) -> Path | None:
    """subgoal-dev → subgoal/dev/requirements_old.json (Held-out analog), sonst None."""
    if not case_id.startswith("subgoal-"):
        return None
    p = paths.PKG_DIR / "subgoal" / case_id.removeprefix("subgoal-") / "requirements_old.json"
    return p if p.exists() else None


def prepare(run_id: str, team_id: str, out_dir: Path = OUT) -> tuple[Path, bool, str]:
    data = load_run(run_id)
    data["team_id"] = team_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{run_id}-{data['case_id']}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cmd = [sys.executable, str(paths.TOOLS_DIR / "validate.py"), str(out)]
    old = requirements_old(data["case_id"])
    if old:
        cmd += ["--requirements-old", str(old)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, r.returncode == 0, (r.stdout + r.stderr).strip()


def local_scores(run_id: str) -> str:
    f = RUNS / run_id / "score.json"
    if f.exists():
        levels = json.loads(f.read_text(encoding="utf-8")).get("levels", {})
        return ", ".join(f"{k.replace('_level', '')} F2 {v['f2']:.3f} (P {v['precision']:.3f} R {v['recall']:.3f})"
                         for k, v in levels.items())
    txt = RUNS / run_id / "score.txt"
    return txt.read_text(encoding="utf-8").strip().splitlines()[-1] if txt.exists() else "keine lokale Messung"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.upload", description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="+", help="Ledger-IDs mit abgelegter Abgabe, z. B. E020-a")
    ap.add_argument("--team-id", default=TEAM_ID, help=f"Team-ID von hackathon.certivity.io (Standard {TEAM_ID})")
    args = ap.parse_args(argv)
    ok_all = True
    for run_id in args.runs:
        out, ok, msg = prepare(run_id, args.team_id)
        ok_all &= ok
        print(f"{'OK ' if ok else 'FEHLER'} {out.relative_to(paths.REPO_ROOT)}\n    lokal gemessen: {local_scores(run_id)}")
        if not ok:
            print("    " + msg.replace("\n", "\n    "))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
