"""Messung AP4: Seiten (score_local.score), Absätze und Obergrenze Anforderungsebene gegen expected.json.

Obergrenze Anforderungen: je Gold-Absatz min(unsere Anzahl, Gold-Anzahl), summiert. Unterstellt, dass jede unserer
Anforderungen im richtigen Absatz auch passt; echte 1:1-Bewertung macht nur die Plattform bzw. der Richter (AP10).
"""
import json, sys, importlib.util, collections, re
from certreq import paths, extract
from certreq.case import load_case
from certreq.select import select_regulations
from certreq.submission import build_submission
from certreq.evaluate import f2
spec = importlib.util.spec_from_file_location("score_local", paths.TOOLS_DIR / "score_local.py")
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
case = load_case(paths.CASES_DIR / "dev-rear-lamp")
exp = json.loads((paths.CASES_DIR / "dev-rear-lamp" / "expected.json").read_text())
gold = collections.Counter((r["source"]["regulation"], r["source"]["paragraph"].split(". Table")[0].rstrip(".")) for r in exp["requirements"])
GOLD = ["UN R148", "UN R48", "UN R150", "UN R10"]
FILT = ("admin", "cop", "parts", "esa")

def line(name, reqs):
    sub = build_submission("t", "dev-rear-lamp", reqs)
    pg = sl.score(sub, exp)["page_level"]
    ours = collections.Counter((r.regulation, r.paragraph) for r in reqs)
    hit = len(set(ours) & set(gold)); pp, pr = hit / max(1, len(ours)), hit / len(gold)
    m = sum(min(n, gold[k]) for k, n in ours.items() if k in gold); rp, rr = m / max(1, len(reqs)), m / sum(gold.values())
    return (f"  {name:<26} n={len(reqs):>5}  Seiten F2 {f2(pg['precision'], pg['recall']):.3f} (R {pg['recall']:.3f})"
            f" | Absätze P {pp:.3f} R {pr:.3f} F2 {f2(pp, pr):.3f} | Anf.-Obergrenze P {rp:.3f} R {rr:.3f} F2 {f2(rp, rr):.3f}")

variants = [a for a in sys.argv[1:]] or ["shall"]
for regs_name, forced in [("gold-regs", GOLD), ("auswahl-B0", None)]:
    regs = select_regulations(case, forced)
    print(f"== {regs_name}")
    for v in variants:
        opts = tuple(x for x in v.split("+") if x != "shall")
        reqs = extract.extract_requirements(regs, case.spec_text, FILT, *( [opts] if opts else [] ))
        print(line(v, reqs))
