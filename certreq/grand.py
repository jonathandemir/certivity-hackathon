"""Großer Vergleichstest: alle Stellschrauben einzeln, jeweils auch das Gegenteil, auf allen Prüfständen mit Lösung.

    .venv/bin/python -m certreq.grand                 # alles (dauert, kostet Tokens; braucht LLM-Key)
    .venv/bin/python -m certreq.grand --only select   # nur Regelungsauswahl
    .venv/bin/python -m certreq.grand --only extract --workers 2
    .venv/bin/python -m certreq.grand --only subgoal

Prüfstände (jede Variante auf allen, damit nichts auf einen Fall zugeschnitten wird):
- Auswahl: echte Teile tune (18) + holdout (10), synthetische Suite (10), Schutzfall Frontstoßfänger, Dev-Rückleuchte.
- Extraktion: dev-rear-lamp (Certivity-Gold, 190) und R175 (synthetische ACPE-Spec, Certivitys requirements_old
  Abschnitte 5–6, 78) – beide mit dem Claude-Richter strict (= Plattform-Prognose, AP10-K3-c).
- Sub-Goal: subgoal-dev (Flags + Change accuracy per certreq.subgoal_judge).

Entscheidungsregel (gegen Overfitting und gegen Streuung ±0.02): Eine Variante schlägt den Standard nur, wenn sie
auf JEDEM Prüfstand ihrer Ebene mindestens gleich ist (−0.01 Toleranz) und auf mindestens einem um mehr als die
Streuung (+0.02) besser. Sonst bleibt der Standard. Ergebnis: out/grand/report.md (+ .json), Tabellen auch auf stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm, paths

OUT = paths.OUT_DIR / "grand"
STD_EXTRACT = "modal,llm,lists,tables,exempt,tests,modes"
FILTERS = ["admin", "cop", "parts", "esa", "rationale"]
DEV_REGS = "UN R148,UN R150,UN R48,UN R10,UN R26"  # Claude-Auswahl auf dev (wie E033/E034-hs-c), Extraktion isoliert
NOISE, TOL = 0.02, 0.01

# ---------------------------------------------------------------- Auswahl-Varianten
RULE_VEHICLE = ("Select only regulations under which the component itself, or its installation on the vehicle, is "
                "approved. Do not select whole-vehicle regulations whose test object is the complete vehicle (frontal or "
                "side impact, external projections, pedestrian safety, rear impact) merely because the component "
                "contributes to that test; select them only when the specification states the component is approved "
                "under that regulation or explicitly requests vehicle-type approval.")
RULE_LIGHTSOURCE = ("A light source (filament, gas-discharge or LED replacement lamp) is approved only under its "
                    "light-source regulation (R37, R99, R128). Do not select the regulations for the lamps it is used in, "
                    "the lighting-installation regulation (R48) or EMC (R10).")
RULE_REPLACEMENT = ("A replacement or aftermarket part with its own replacement-part regulation (e.g. replacement "
                    "silencing systems R92, replacement pollution control devices R103) is approved under that regulation "
                    "only. Do not add the vehicle-level emission or noise regulations whose limits the part must preserve.")
RULE_INCLUSIVE = ("When in doubt, include. A regulation whose vehicle tests or installation rules are influenced by the "
                  "component (crash and pedestrian tests of the structure it forms, external projections, lighting "
                  "installation, EMC of electronics on or near it) applies to the component. Missing a regulation costs "
                  "far more than an extra one.")
RULE_EXCLUSIVE = ("Select the smallest set: only the regulation that approves the component itself. Never add installation, "
                  "EMC or vehicle-level regulations unless the specification names them.")


def _arena_guidance(run_id: str, rnd: int) -> str:
    p = paths.REPO_ROOT / "experiments" / "runs" / run_id / "meta.json"
    if not p.exists():
        return ""
    for h in json.loads(p.read_text(encoding="utf-8"))["rounds"]:
        if h["round"] == rnd:
            return h["guidance"]
    return ""


def select_variants() -> list[tuple[str, str, str]]:
    """(Name, Modus, Zusatzregeln)."""
    return [
        ("Standard llm2", "llm2", ""),
        ("Gegenteil: llm (ohne Annahme-/Fahrzeugfilter)", "llm", ""),
        ("Arena Lauf 1 (alle Regeln)", "llm2", _arena_guidance("X-ARENA-SEL-1", 2)),
        ("Arena Lauf 2 (Runde 3)", "llm2", _arena_guidance("X-ARENA-SEL-2", 3)),
        ("nur Regel Fahrzeugebene raus", "llm2", RULE_VEHICLE),
        ("nur Regel Lichtquelle ≠ Leuchte", "llm2", RULE_LIGHTSOURCE),
        ("nur Regel Ersatzteil", "llm2", RULE_REPLACEMENT),
        ("Lichtquelle + Ersatzteil", "llm2", RULE_LIGHTSOURCE + "\n" + RULE_REPLACEMENT),
        ("Gegenteil: im Zweifel aufnehmen", "llm2", RULE_INCLUSIVE),
        ("Gegenteil: kleinste Menge", "llm2", RULE_EXCLUSIVE),
    ]


def run_selection(workers: int) -> list[dict]:
    from . import arena
    from . import select as sel
    sets = arena.select_cases()
    groups = {"real-tune": [c for c in sets["tune"] if c["name"].startswith("real/")],
              "synth": [c for c in sets["tune"] if c["name"].startswith("synth/")],
              "holdout": sets["holdout"],
              "bumper": [c for c in sets["tune"] if c["name"].startswith("guard/")],
              "dev": [c for c in sets["tune"] if c["name"].startswith("certivity/")]}
    rows = []
    for name, mode, guidance in select_variants():
        t0 = time.time()
        orig_mode = sel.select_regulations

        def with_mode(case, mode_arg=None, _m=mode, **kw):  # arena ruft mode="llm2"; hier Modus der Variante
            return orig_mode(case, mode=_m, **{k: v for k, v in kw.items() if k != "mode"})
        sel.select_regulations = lambda case, mode=None, **kw: with_mode(case, **kw)
        try:
            res = {g: arena.run_select(guidance, cs, workers) for g, cs in groups.items() if cs}
        finally:
            sel.select_regulations = orig_mode
        bumper = res.get("bumper", {}).get("components", {}).get("guard/front-bumper", {})
        row = {"variant": name, "mode": mode, "guidance": guidance, "seconds": round(time.time() - t0),
               **{g: r["summary"] for g, r in res.items()},
               "bumper_selected": bumper.get("selected"), "bumper_missing": bumper.get("missing"),
               "errors": {g: {n: {"missing": c["missing"], "wrong": c["wrong"]} for n, c in r["components"].items()
                              if c["missing"] or c["wrong"]} for g, r in res.items()}}
        rows.append(row)
        print(f"  Auswahl · {name:45} real-tune {row['real-tune']['f2']:.3f} · synth {row['synth']['f2']:.3f} · "
              f"holdout {row['holdout']['f2']:.3f} · Stoßfänger fehlt {row['bumper_missing']} · dev "
              f"{'exakt' if not row['errors'].get('dev') else row['errors']['dev']} · {row['seconds']} s", flush=True)
    return rows


# ---------------------------------------------------------------- Extraktions-Varianten
def extract_variants() -> list[tuple[str, str, str]]:
    """(Name, --filters, --extract)."""
    v = [("Standard", "all", STD_EXTRACT),
         ("Gegenteil: keine Prompt-Regeln (modal,llm)", "all", "modal,llm"),
         ("ohne modes", "all", STD_EXTRACT.replace(",modes", "")),
         ("+procedure2 +testcond", "all", STD_EXTRACT + ",procedure2,testcond"),
         ("Gegenteil: keine Filter", "none", STD_EXTRACT)]
    v += [(f"ohne Filter {f}", ",".join(x for x in FILTERS if x != f), STD_EXTRACT) for f in FILTERS]
    return v


def _r175_expected() -> Path:
    src = paths.PKG_DIR / "subgoal" / "dev" / "requirements_old.json"
    reqs = [r for r in json.loads(src.read_text(encoding="utf-8"))
            if r["source"].get("paragraph", "").split(".")[0] in ("5", "6")]
    out = OUT / "r175-expected-eng.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"requirements": reqs}, ensure_ascii=False), encoding="utf-8")
    return out


def _run_case(tag: str, case: Path, regs: str, filters: str, extract: str, extra: list[str]) -> Path:
    out = OUT / "runs" / f"{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        cmd = [sys.executable, "-m", "certreq", "run", str(case), "--regs", regs, "--filters", filters,
               "--extract", extract, "--out", str(out), *extra]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=paths.REPO_ROOT, env=os.environ)
        if r.returncode != 0:
            raise RuntimeError(f"{tag}: {r.stderr[-600:]}")
    return out


def run_extraction(workers: int) -> list[dict]:
    from .judge import judge
    benches = {
        "dev": (paths.CASES_DIR / "dev-rear-lamp", DEV_REGS, [],
                json.loads((paths.CASES_DIR / "dev-rear-lamp" / "expected.json").read_text())["requirements"]),
        "r175": (paths.REPO_ROOT / "experiments" / "synthetic" / "acpe", "UN R175", ["--vision", "off"],
                 json.loads(_r175_expected().read_text())["requirements"]),
    }
    jobs = [(name, flt, ext, b) for name, flt, ext in extract_variants() for b in benches]

    def one(job):
        name, flt, ext, b = job
        case, regs, extra, exp = benches[b]
        tag = f"{b}__{flt.replace(',', '-')}__{ext.replace(',', '-')}"
        t0 = time.time()
        try:
            sub = json.loads(_run_case(tag, case, regs, flt, ext, extra).read_text(encoding="utf-8"))
            rep = judge(sub, exp, lenient=False)
            lv = rep["level"]
            print(f"  Extraktion · {b:4} · {name:42} F2 {lv['f2']:.3f} (P {lv['precision']:.3f} R {lv['recall']:.3f}, "
                  f"{lv['n_matched']}/{lv['n_expected']}, {lv['n_submitted']} Anf.) · {time.time() - t0:.0f} s", flush=True)
            return {"variant": name, "bench": b, "filters": flt, "extract": ext, **lv,
                    "recall_by_regulation": rep["recall_by_regulation"]}
        except Exception as e:  # noqa: BLE001
            print(f"  ! {b} {name}: {e}", flush=True)
            return {"variant": name, "bench": b, "error": str(e)}

    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(one, jobs))


# ---------------------------------------------------------------- Sub-Goal-Varianten
def run_subgoal() -> list[dict]:
    from . import subgoal as sg
    from .subgoal_judge import judge as acc_judge  # noqa: F401 (Signatur: Pfade)
    d = paths.PKG_DIR / "subgoal" / "dev"
    reqs = json.loads((d / "requirements_old.json").read_text(encoding="utf-8"))
    exp = json.loads((d / "expected.json").read_text(encoding="utf-8"))
    rows, base_min = [], sg.MODIFIED_MIN
    for name, refine, mm in [("Standard (refine llm)", "llm", 0.55), ("Gegenteil: regelbasiert (none)", "none", 0.55),
                             ("llm-all (auch modified per LLM)", "llm-all", 0.55), ("Ähnlichkeit 0.45", "llm", 0.45),
                             ("Ähnlichkeit 0.65", "llm", 0.65)]:
        sg.MODIFIED_MIN = mm
        sub = sg.compare(d / "old.pdf", d / "new.pdf", reqs, "team-x", "subgoal-dev", refine=refine)
        sg.MODIFIED_MIN = base_min
        ev = sg.evaluate(sub, exp)["all"]
        p = OUT / "subgoal" / f"{refine}-{mm}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(sub, ensure_ascii=False), encoding="utf-8")
        acc = _accuracy(p, d / "expected.json")
        rows.append({"variant": name, "refine": refine, "modified_min": mm, "recall": ev["recall"],
                     "precision": ev["precision"], "accuracy": acc})
        print(f"  Sub-Goal · {name:34} Flags R {ev['recall']:.3f} P {ev['precision']:.3f} · Change accuracy (lokal) "
              f"{acc:.3f}", flush=True)
    return rows


def _accuracy(sub_p: Path, exp_p: Path) -> float:
    import contextlib
    import io
    from . import subgoal_judge
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        subgoal_judge.judge(str(sub_p), str(exp_p))
    first = buf.getvalue().splitlines()[0]  # „Flags getroffen x/y, accurate a/b = 0.917"
    return float(first.rsplit("=", 1)[1])


# ---------------------------------------------------------------- Auswertung
def verdict(rows: list[dict], key, benches: list[str], std_name: str) -> list[str]:
    std = next(r for r in rows if r["variant"] == std_name)
    out = []
    for r in rows:
        if r is std:
            continue
        diffs = [key(r, b) - key(std, b) for b in benches]
        if all(d >= -TOL for d in diffs) and any(d > NOISE for d in diffs):
            out.append(f"BESSER: {r['variant']} ({', '.join(f'{b} {d:+.3f}' for b, d in zip(benches, diffs))})")
    return out or [f"Kein Kandidat schlägt „{std_name}“ auf allen Prüfständen über die Streuung hinaus → Standard bleibt."]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.grand", description=__doc__.splitlines()[0])
    ap.add_argument("--only", choices=["select", "extract", "subgoal"])
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict = {"model": llm.model_name(llm.STRONG_MODEL)}
    lines = [f"# Großer Vergleichstest (Modell {report['model']})", ""]
    t0 = time.time()
    if a.only in (None, "subgoal"):
        print("Sub-Goal …", flush=True)
        report["subgoal"] = rows = run_subgoal()
        lines += ["## Sub-Goal (subgoal-dev)", "", "| Variante | Flag-R | Flag-P | Change accuracy lokal |", "|---|---|---|---|"]
        lines += [f"| {r['variant']} | {r['recall']:.3f} | {r['precision']:.3f} | {r['accuracy']:.3f} |" for r in rows]
        lines += ["", *verdict(rows, lambda r, b: r[b], ["recall", "accuracy"], "Standard (refine llm)"), ""]
    if a.only in (None, "select"):
        print("Regelungsauswahl …", flush=True)
        report["select"] = rows = run_selection(max(a.workers, 6))
        lines += ["## Regelungsauswahl", "", "| Variante | echte Teile tune F2 | synthetisch F2 | holdout F2 | Stoßfänger fehlt | Dev |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| {r['variant']} | {r['real-tune']['f2']:.3f} | {r['synth']['f2']:.3f} | {r['holdout']['f2']:.3f} | "
                  f"{', '.join(r['bumper_missing']) or '—'} | {'exakt' if not r['errors'].get('dev') else r['errors']['dev']} |"
                  for r in rows]
        safe = [r for r in rows if not r["bumper_missing"] and not r["errors"].get("dev", {}).get("certivity/dev-rear-lamp", {}).get("missing")]
        lines += ["", *verdict(safe or rows, lambda r, b: r[b]["f2"], ["real-tune", "synth", "holdout"], "Standard llm2"),
                  "(Varianten, die beim Frontstoßfänger oder bei der Dev-Rückleuchte eine Pflicht-Regelung verlieren, scheiden vorher aus.)", ""]
    if a.only in (None, "extract"):
        print("Extraktion (dauert) …", flush=True)
        report["extract"] = rows = run_extraction(a.workers)
        ok = [r for r in rows if "error" not in r]
        names = list(dict.fromkeys(r["variant"] for r in ok))
        table = {n: {r["bench"]: r for r in ok if r["variant"] == n} for n in names}
        lines += ["## Extraktion (Claude-Richter strict)", "", "| Variante | dev F2 | R175 F2 | dev P/R | R175 P/R |", "|---|---|---|---|---|"]
        for n in names:
            d, s = table[n].get("dev"), table[n].get("r175")
            lines.append(f"| {n} | {d['f2']:.3f} | {s['f2']:.3f} | {d['precision']:.2f}/{d['recall']:.2f} | "
                         f"{s['precision']:.2f}/{s['recall']:.2f} |" if d and s else f"| {n} | Fehler | | | |")
        full = [{"variant": n, **{b: table[n][b]["f2"] for b in table[n]}} for n in names if len(table[n]) == 2]
        if any(r["variant"] == "Standard" for r in full):
            lines += ["", *verdict(full, lambda r, b: r[b], ["dev", "r175"], "Standard"), ""]
    lines += [f"Dauer {time.time() - t0:.0f} s · LLM: {llm.usage()}"]
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
