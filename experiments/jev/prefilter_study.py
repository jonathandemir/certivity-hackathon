"""Versuch 2 (experiments/jev/PROTOKOLL.md): Jev als Vorfilter auf Kandidaten-Absätze, gemessen ohne LLM-Lauf.

    .venv/bin/python experiments/jev/prefilter_study.py

Kandidaten wie in certreq.extract (Filter all, modale Pflichtwörter); Gold-Absätze aus dem Gold (Label normalisiert
wie im Richter). Schreibt experiments/jev/results-prefilter.json (nur Labels, p, Kennzahlen).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from certreq import jev, paths  # noqa: E402
from certreq.__main__ import _parse_filters  # noqa: E402
from certreq.extract import MODAL_RE  # noqa: E402
from certreq.judge import _para_key  # noqa: E402
from certreq.pdf import parse_pdf  # noqa: E402
from certreq.regindex import load_index  # noqa: E402
from certreq.relevance import relevant  # noqa: E402

GRID = [round(i * 0.05, 2) for i in range(20)]
FILTERS = _parse_filters("all")


def candidates(regs: list[str], spec: str) -> list:
    index, cands = load_index(), []
    for name in regs:
        reg = index[name]
        for pdf in reg.base.pdfs:
            paras = parse_pdf(pdf)
            keep = relevant(paras, FILTERS, spec)
            cands += [(reg, p) for p, ok in zip(paras, keep) if ok and MODAL_RE.search(p.text)]
    return cands


def study(name: str, regs: list[str], spec: str, gold: list[dict]) -> dict:
    cands = candidates(regs, spec)
    p = jev.score_paragraphs(spec, cands)
    keys = [(reg.name, _para_key(par.label)) for reg, par in cands]
    gold_keys = {(g["source"]["regulation"], _para_key(g["source"].get("paragraph"))) for g in gold}
    in_cands = gold_keys & set(keys)
    chars = [len(par.text) for _, par in cands]
    curve = {}
    for t in GRID:
        kept = {k for k, pi in zip(keys, p) if pi >= t}
        curve[f"{t:.2f}"] = {
            "kept": sum(1 for pi in p if pi >= t),
            "dropped_share": round(1 - sum(1 for pi in p if pi >= t) / len(p), 3),
            "chars_kept_share": round(sum(c for c, pi in zip(chars, p) if pi >= t) / sum(chars), 3),
            "gold_kept": len(in_cands & kept), "gold_recall": round(len(in_cands & kept) / len(in_cands), 4)}
    return {"case": name, "regs": regs, "candidates": len(cands), "gold_paragraphs": len(gold_keys),
            "gold_in_candidates": len(in_cands), "curve": curve,
            "p": [{"reg": k[0], "para": k[1], "p": round(pi, 4), "gold": k in gold_keys} for k, pi in zip(keys, p)]}


def main() -> int:
    dev_spec = (paths.CASES_DIR / "dev-rear-lamp" / "spec.md").read_text(encoding="utf-8")
    dev_gold = json.loads((paths.CASES_DIR / "dev-rear-lamp" / "expected.json").read_text(encoding="utf-8"))["requirements"]
    acpe_spec = (ROOT / "experiments" / "synthetic" / "acpe" / "spec.md").read_text(encoding="utf-8")
    old = json.loads((paths.PKG_DIR / "subgoal" / "dev" / "requirements_old.json").read_text(encoding="utf-8"))
    r175_eng = [r for r in old if r["source"]["paragraph"].split(".")[0] in ("5", "6")]
    res = [study("dev (Opus-Auswahl)", ["UN R148", "UN R150", "UN R48", "UN R10", "UN R26"], dev_spec, dev_gold),
           study("R175 (Abschnitte 5–6)", ["UN R175"], acpe_spec, r175_eng)]
    for x in res:
        print(f"{x['case']}: {x['candidates']} Kandidaten, Gold-Absätze {x['gold_paragraphs']} (davon unter Kandidaten {x['gold_in_candidates']})")
        for t in GRID:
            c = x["curve"][f"{t:.2f}"]
            if t in (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5):
                print(f"   θ {t:.2f}: gestrichen {c['dropped_share']:.0%} (Text {1 - c['chars_kept_share']:.0%}), Gold-Absätze behalten {c['gold_kept']}/{x['gold_in_candidates']} = {c['gold_recall']:.1%}")
    ok = [t for t in GRID if all(x["curve"][f"{t:.2f}"]["gold_recall"] >= 0.99 and x["curve"][f"{t:.2f}"]["dropped_share"] >= 0.30 for x in res)]
    print("Schwellen, die das Kriterium erfüllen (≥99 % Gold-Absätze auf beiden, ≥30 % gestrichen):", ok or "keine")
    print("Jev-Verbrauch:", jev.usage())
    out = ROOT / "experiments" / "jev" / "results-prefilter.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
