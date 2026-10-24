"""Schnellmessung je Filterkombination: Seiten (score_local-Logik) + Absatz-Ebene gegen expected.json."""
import json, sys, importlib.util
from certreq import paths
from certreq.case import load_case
from certreq.select import select_regulations
from certreq.extract import extract_requirements
from certreq.submission import build_submission
from certreq.evaluate import f2
spec = importlib.util.spec_from_file_location("score_local", paths.TOOLS_DIR / "score_local.py")
sl = importlib.util.module_from_spec(spec); spec.loader.exec_module(sl)
case = load_case(paths.CASES_DIR / "dev-rear-lamp")
exp = json.loads((paths.CASES_DIR / "dev-rear-lamp" / "expected.json").read_text())
gold_par = {(r["source"]["regulation"], r["source"]["paragraph"].split(". Table")[0].rstrip(".")) for r in exp["requirements"]}
GOLD = ["UN R148", "UN R48", "UN R150", "UN R10"]
combos = [(), ("admin",), ("cop",), ("parts",), ("esa",), ("admin", "cop", "parts", "esa")]
for regs_name, forced in [("gold-regs", GOLD), ("auswahl-B0", None)]:
    regs = select_regulations(case, forced)
    print(f"== {regs_name}")
    for fl in combos:
        reqs = extract_requirements(regs, case.spec_text, fl)
        sub = build_submission("t", "dev-rear-lamp", reqs)
        pg = sl.score(sub, exp)["page_level"]
        ours = {(r.regulation, r.paragraph) for r in reqs}
        pp = len(ours & gold_par) / max(1, len(ours)); pr = len(ours & gold_par) / len(gold_par)
        print(f"  {'+'.join(fl) or 'B0':<18} n={len(reqs):>5}  Seiten P {pg['precision']:.3f} R {pg['recall']:.3f} F2 {f2(pg['precision'], pg['recall']):.3f}"
              f"  | Absätze P {pp:.3f} R {pr:.3f} F2 {f2(pp, pr):.3f}")
