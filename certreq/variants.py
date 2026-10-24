"""Upload-Varianten aus einem abgelegten Lauf ableiten: Regelungen weglassen, ohne neuen LLM-Lauf.

    .venv/bin/python -m certreq.variants H001 --list                          # Anforderungen je Regelung
    .venv/bin/python -m certreq.variants H001 --drop "UN R94" --as H001-noR94  # Variante ablegen
    .venv/bin/python -m certreq.upload H001-noR94                              # Upload-Datei bauen + validieren

Zweck (Sonntag, docs/PLAN.md „Sonntagsablauf"): Upload-Paare, die sich in genau einer Regelung unterscheiden
(mit/ohne R94, R127 oder GTR 9, mit/ohne R26/R42). Die Anforderungen der übrigen Regelungen bleiben byte-gleich, also
misst ein Paar nur diese eine Entscheidung. Die Variante liegt wie jeder Lauf unter experiments/runs/<ID>/ (Abgabe gzip
+ meta.json mit Herkunft), damit `certreq.upload` sie unverändert hochladen und man sie zuletzt erneut hochladen kann.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .gitmeta import git_state
from .upload import RUNS, load_run


def per_regulation(sub: dict) -> Counter:
    return Counter(r["source"]["regulation"] for r in sub["requirements"])


def drop_regulations(sub: dict, drop: list[str]) -> dict:
    """Neue Abgabe ohne die Anforderungen der genannten Regelungen; unbekannte Namen sind ein Fehler (Tippfehler)."""
    present = per_regulation(sub)
    unknown = [d for d in drop if d not in present]
    if unknown:
        raise SystemExit(f"Nicht in der Abgabe: {unknown}. Vorhanden: {sorted(present)}")
    kept = [r for r in sub["requirements"] if r["source"]["regulation"] not in set(drop)]
    if not kept:
        raise SystemExit("Die Variante hätte keine Anforderung mehr.")
    return {**sub, "requirements": kept}


def save_variant(base_id: str, new_id: str, sub: dict, drop: list[str], runs: Path = RUNS) -> Path:
    dest = runs / new_id
    if dest.exists():
        raise SystemExit(f"{dest} existiert schon. Neue ID wählen (Ledger-IDs nie wiederverwenden).")
    base_meta_path = runs / base_id / "meta.json"
    base_meta = json.loads(base_meta_path.read_text(encoding="utf-8")) if base_meta_path.exists() else {}
    dest.mkdir(parents=True)
    raw = (json.dumps(sub, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    with gzip.GzipFile(dest / "submission.json.gz", "wb", mtime=0) as fh:
        fh.write(raw)
    meta = {"run_id": new_id, "derived_from": base_id, "dropped_regulations": drop,
            "requirements": len(sub["requirements"]), "per_regulation": dict(per_regulation(sub)),
            "base_git": base_meta.get("git"), "base_command": base_meta.get("command"),
            "base_llm_model": (base_meta.get("llm") or {}).get("model"), "derived_on": git_state()["commit"],
            "submission_sha256": hashlib.sha256(raw).hexdigest(),
            "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.variants", description=__doc__.splitlines()[0])
    ap.add_argument("run", help="Ledger-ID eines abgelegten Laufs (experiments/runs/<ID>/submission.json.gz)")
    ap.add_argument("--list", action="store_true", help="nur Anforderungen je Regelung zeigen")
    ap.add_argument("--drop", action="append", default=[], metavar="REGELUNG", help='z. B. --drop "UN R94" (mehrfach)')
    ap.add_argument("--as", dest="new_id", metavar="ID", help="ID der Variante, z. B. H001-noR94")
    args = ap.parse_args(argv)
    sub = load_run(args.run)
    if args.list or not args.drop:
        for reg, n in sorted(per_regulation(sub).items(), key=lambda kv: -kv[1]):
            print(f"{n:5}  {reg}")
        print(f"{len(sub['requirements']):5}  gesamt ({args.run})")
        return 0
    if not args.new_id:
        raise SystemExit("--as <ID> fehlt (z. B. H001-noR94).")
    var = drop_regulations(sub, args.drop)
    dest = save_variant(args.run, args.new_id, var, args.drop)
    print(f"{dest}: {len(var['requirements'])} von {len(sub['requirements'])} Anforderungen, ohne {', '.join(args.drop)}")
    print(f"Weiter: .venv/bin/python -m certreq.upload {args.new_id}  (dann Plattform-Score nach {dest}/platform.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
