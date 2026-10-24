"""Bewertungsschleife: validate.py + score_local.py des Pakets, F2 je Ebene, Beleg nach experiments/runs/<ID>/.

score_local.py zeigt nur P/R/F1 auf Regelungs- und Seitenebene; gerankt wird nach F2 (Recall doppelt gewichtet).
Die Anforderungsebene gibt es nur auf der Plattform.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import paths


def f2(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 5 * precision * recall / (4 * precision + recall)


def validate(submission: Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(paths.TOOLS_DIR / "validate.py"), str(submission)],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def score_local(submission: Path, expected: Path) -> dict:
    r = subprocess.run([sys.executable, str(paths.TOOLS_DIR / "score_local.py"), str(submission),
                        "--expected", str(expected), "--json"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"score_local.py fehlgeschlagen: {r.stderr.strip() or r.stdout.strip()}")
    levels = json.loads(r.stdout)
    for lv in levels.values():
        lv["f2"] = round(f2(lv["precision"], lv["recall"]), 4)
    return levels


def evaluate(submission: Path, expected: Path | None = None) -> dict:
    data = json.loads(submission.read_text(encoding="utf-8"))
    case_id = data.get("case_id", "")
    if expected is None:
        candidate = paths.CASES_DIR / case_id / "expected.json"
        expected = candidate if candidate.exists() else None
    ok, out = validate(submission)
    result = {"case_id": case_id, "n_requirements": len(data.get("requirements", [])), "valid": ok,
              "validate_output": out, "expected": str(expected) if expected else None, "levels": {}}
    if ok and expected:
        result["levels"] = score_local(submission, expected)
    return result


def format_result(res: dict) -> str:
    lines = [f"Fall {res['case_id']}: {res['n_requirements']} Anforderungen, validate.py: "
             + ("OK" if res["valid"] else "UNGÜLTIG\n" + res["validate_output"])]
    if res["levels"]:
        lines.append(f"{'Ebene':<12}{'P':>8}{'R':>8}{'F1':>8}{'F2':>8}   eingereicht/erwartet/getroffen")
        for name, lv in res["levels"].items():
            lines.append(f"{name.replace('_level', ''):<12}{lv['precision']:>8.3f}{lv['recall']:>8.3f}{lv['f1']:>8.3f}"
                         f"{lv['f2']:>8.3f}   {lv['n_submitted']}/{lv['n_expected']}/{lv['n_matched']}")
        lines.append("Anforderungsebene (Hauptscore): nur auf der Plattform.")
    elif res["valid"]:
        lines.append("Kein expected.json für diesen Fall: nur validiert (Held-out wird nur auf der Plattform bewertet).")
    return "\n".join(lines)


def _main_worktree() -> Path:
    r = subprocess.run([str(paths.REPO_ROOT / "scripts" / "main-wt")], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"scripts/main-wt fehlgeschlagen: {r.stderr.strip()}")
    return Path(r.stdout.strip().splitlines()[-1])


def record(run_id: str, submission: Path, res: dict, note: str, allow_unclean: bool = False) -> Path:
    """Legt Abgabe (gzip), Score und Lauf-Metadaten unter experiments/runs/<ID>/ im main-Worktree ab."""
    meta_path = submission.with_suffix(".meta.json")
    if not meta_path.exists():
        raise SystemExit(f"{meta_path} fehlt: die Abgabe stammt nicht aus `python -m certreq run`.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    git = meta["git"]
    if not (git["clean"] and git["pushed"]) and not allow_unclean:
        raise SystemExit(f"Lauf auf {git['commit']} war nicht sauber und gepusht (clean={git['clean']}, "
                         f"pushed={git['pushed']}). Das zählt nicht als Ergebnis: committen, scripts/sync, neu laufen lassen.")
    dest = _main_worktree() / "experiments" / "runs" / run_id
    if dest.exists():
        raise SystemExit(f"{dest} existiert schon. Neue ID wählen (Ledger-IDs nie wiederverwenden).")
    dest.mkdir(parents=True)
    raw = submission.read_bytes()
    with gzip.GzipFile(dest / "submission.json.gz", "wb", mtime=0) as fh:
        fh.write(raw)
    (dest / "score.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    meta.update({"run_id": run_id, "note": note, "submission_sha256": hashlib.sha256(raw).hexdigest(),
                 "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds")})
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dest
