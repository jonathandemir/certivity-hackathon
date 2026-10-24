"""Versuch 1 (experiments/jev/PROTOKOLL.md): Jev-Nachfilter auf fertige Läufe mit bekannten Treffern.

    .venv/bin/python experiments/jev/study.py tune            # Formulierungen A/B auf E039-a, E040-a
    .venv/bin/python experiments/jev/study.py test --form A --theta 0.30

Schreibt experiments/jev/results-<phase>.json (nur IDs, p und Kennzahlen; keine Gold-Texte).
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from certreq import jev, paths  # noqa: E402
from certreq.vision import render  # noqa: E402

RUNS = ROOT / "experiments" / "runs"
OUT = ROOT / "out"
DEV_SPEC = (paths.CASES_DIR / "dev-rear-lamp" / "spec.md").read_text(encoding="utf-8")
ACPE_SPEC = (ROOT / "experiments" / "synthetic" / "acpe" / "spec.md").read_text(encoding="utf-8")
GRID = [round(i * 0.05, 2) for i in range(20)]


def _sub(run: str) -> dict:
    with gzip.open(RUNS / run / "submission.json.gz", "rt", encoding="utf-8") as fh:
        return json.load(fh)


def _matches_from(path: Path) -> set[str]:
    d = json.loads(path.read_text(encoding="utf-8"))
    d = d.get("judge", d)
    return {ours for _exp, ours in d["matches"]}


def _drawing_spec(run: str) -> str:
    return render(json.loads((RUNS / run / "meta.json").read_text(encoding="utf-8"))["drawing"])


SETS = {  # Lauf: (Abgabe, Treffer-IDs, G, Spec, Richter)
    "E039-a": lambda: (_sub("E039-a"), _matches_from(RUNS / "E039-a" / "score.json"), 190, DEV_SPEC, "gpt lenient"),
    "E040-a": lambda: (_sub("E040-a"), _matches_from(RUNS / "E040-a" / "score.json"), 190, DEV_SPEC, "gpt lenient"),
    "E024-hs-c": lambda: (_sub("E024-hs-c"), _matches_from(RUNS / "E024-hs-c" / "judge-gpt-lenient.json"), 190, DEV_SPEC, "gpt lenient"),
    "X-R175-C": lambda: (_sub("X-R175-C"), _matches_from(OUT / "x-r175" / "C-claude.judge.json"), 78, ACPE_SPEC, "Claude strict"),
    "X-R175-C-rep": lambda: (_sub("X-R175-C-rep"), _matches_from(OUT / "x-r175" / "C-rep-claude.judge.json"), 78, ACPE_SPEC, "Claude strict"),
    "E022-hs": lambda: (_sub("E022-hs"), _matches_from(OUT / "E022-hs.lenient.judge.json"), 190, DEV_SPEC, "gpt lenient"),
    "E030-a": lambda: (_sub("E030-a"), _matches_from(OUT / "E030-a.judge.json"), 190, DEV_SPEC, "gpt lenient"),
    "E044-a": lambda: (_sub("E044-a"), _matches_from(RUNS / "E044-a" / "score.json"), 190, _drawing_spec("E044-a"), "Claude strict"),
}
TUNE = ["E039-a", "E040-a"]
TEST = ["E024-hs-c", "X-R175-C", "X-R175-C-rep", "E022-hs", "E030-a", "E044-a"]


def f2(tp: int, n: int, g: int) -> float:
    return 5 * tp / (4 * g + n) if n else 0.0


def auc(pos: list[float], neg: list[float]) -> float:
    """Wahrscheinlichkeit, dass ein Treffer ein höheres p hat als ein Nicht-Treffer (Gleichstand = 1/2)."""
    if not pos or not neg:
        return float("nan")
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def evaluate(run: str, form: str) -> dict:
    sub, hits, g, spec, judge = SETS[run]()
    reqs = sub["requirements"]
    ids = {r["id"] for r in reqs}
    hits &= ids
    p = jev.score_requirements(spec, reqs, form=form)
    pos = [p[i] for i in ids if i in hits]
    neg = [p[i] for i in ids if i not in hits]
    curve = {}
    for t in GRID + [0.15]:
        keep = [i for i in ids if p[i] >= t]
        tp = sum(1 for i in keep if i in hits)
        curve[f"{t:.2f}"] = {"tp": tp, "n": len(keep), "f2": round(f2(tp, len(keep), g), 4)}
    bins = []
    for lo in (0.0, 0.2, 0.4, 0.6, 0.8):
        sel = [i for i in ids if lo <= p[i] < lo + 0.2 or (lo == 0.8 and p[i] == 1.0)]
        bins.append({"p": f"{lo:.1f}-{lo + 0.2:.1f}", "n": len(sel),
                     "trefferquote": round(sum(1 for i in sel if i in hits) / len(sel), 3) if sel else None})
    return {"run": run, "form": form, "judge": judge, "G": g, "N": len(reqs), "TP": len(hits),
            "auc": round(auc(pos, neg), 4), "curve": curve, "calibration": bins, "p": p}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["tune", "test"])
    ap.add_argument("--form", choices=["A", "B"])
    ap.add_argument("--theta", type=float)
    a = ap.parse_args()
    forms = ["A", "B"] if a.phase == "tune" else [a.form]
    runs = TUNE if a.phase == "tune" else TEST
    res = [evaluate(r, f) for f in forms for r in runs]
    for x in res:
        c = x["curve"]
        best = max(GRID, key=lambda t: c[f"{t:.2f}"]["f2"])
        line = f"{x['run']:13} {x['form']}  AUC {x['auc']:.3f}  F2(0) {c['0.00']['f2']:.3f}  F2(0.15) {c['0.15']['f2']:.3f}"
        if a.theta is not None:
            k = f"{a.theta:.2f}"
            line += f"  F2(θ={k}) {c[k]['f2']:.3f} ({c[k]['tp']}/{c[k]['n']})  Δ {c[k]['f2'] - c['0.00']['f2']:+.3f}"
        line += f"  bestes θ {best:.2f} → {c[f'{best:.2f}']['f2']:.3f}"
        print(line)
        print("   Kalibrierung:", ", ".join(f"{b['p']}: {b['trefferquote']} (n={b['n']})" for b in x["calibration"]))
    if a.phase == "tune":
        for f in forms:
            sel = [x for x in res if x["form"] == f]
            mean_auc = sum(x["auc"] for x in sel) / len(sel)
            mean_curve = {t: sum(x["curve"][f"{t:.2f}"]["f2"] for x in sel) / len(sel) for t in GRID}
            tbest = max(GRID, key=lambda t: mean_curve[t])
            print(f"Form {f}: mittlere AUC {mean_auc:.3f}; θ* {tbest:.2f}: mittl. F2 {mean_curve[tbest]:.4f} vs θ=0 {mean_curve[0.0]:.4f}")
    else:
        k = f"{a.theta:.2f}"
        gains = [x["curve"][k]["f2"] - x["curve"]["0.00"]["f2"] for x in res]
        print(f"Testläufe: Gewinne {[round(g, 4) for g in gains]}, Mittel {sum(gains) / len(gains):+.4f}, "
              f"alle ≥ 0: {all(g >= -1e-9 for g in gains)}")
    print("Jev-Verbrauch:", jev.usage())
    out = ROOT / "experiments" / "jev" / f"results-{a.phase}{'-' + a.form if a.form else ''}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Ergebnis:", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
