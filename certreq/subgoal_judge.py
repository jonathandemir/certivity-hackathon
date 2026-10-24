"""Lokale Näherung der Sub-Goal-Wertung „Change accuracy": ein Sprachmodell vergleicht je getroffenem Flag unsere Änderung
mit der Referenz (expected.json). Streng; Abweichungen der Referenz selbst (z. B. gekürzte new_text) zählen als Fehler.

    .venv/bin/python -m certreq.subgoal_judge out/subgoal-dev.json [vendor/.../subgoal/dev/expected.json]
"""
import json, sys, os
from concurrent.futures import ThreadPoolExecutor
from certreq import llm
from certreq.subgoal import _tokens

SYS = ("You grade a regulation-change detector. For one requirement you get the REFERENCE change (written by experts) and "
       "the SUBMITTED change. Decide if the submitted change is accurate: same change type, and its text/reason state the same "
       "substantive change(s) as the reference (what was added, removed or altered, with the right values). Extra correct detail "
       "is fine; a missing or wrong substantive change, a wrong value, or noise that misstates the change is not. Be strict but fair.")
SCHEMA = {"type": "object", "properties": {"accurate": {"type": "boolean"}, "why": {"type": "string"}},
          "required": ["accurate", "why"], "additionalProperties": False}

def pairs(sub, exp):
    from difflib import SequenceMatcher
    out = []
    for e in exp["changes"]:
        if e["change"] != "added":
            out.append((e, next((c for c in sub["changes"] if c.get("requirement_id") == e["requirement_id"]), None)))
    # added: global beste 1:1-Zuordnung je Absatz nach Textähnlichkeit
    ea = [e for e in exp["changes"] if e["change"] == "added"]
    sa = [c for c in sub["changes"] if c["change"] == "added"]
    cand = []
    for i, e in enumerate(ea):
        for j, c in enumerate(sa):
            if (e.get("source") or {}).get("paragraph") == (c.get("source") or {}).get("paragraph"):
                r = SequenceMatcher(None, _tokens(e.get("new_text") or ""), _tokens(c.get("new_text") or ""), autojunk=False).ratio()
                cand.append((r, i, j))
    ui, uj, m = set(), set(), {}
    for r, i, j in sorted(cand, reverse=True):
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); m[i] = sa[j]
    out += [(e, m.get(i)) for i, e in enumerate(ea)]
    return out

def show(c):
    return json.dumps({k: c.get(k) for k in ("change", "requirement_id", "new_text", "reason")}, ensure_ascii=False)

def judge(sub_path, exp_path):
    sub, exp = json.load(open(sub_path)), json.load(open(exp_path))
    pr = [(e, c) for e, c in pairs(sub, exp) if c]
    def one(ec):
        e, c = ec
        return llm.ask_json(SYS, f"REFERENCE:\n{show(e)}\n\nSUBMITTED:\n{show(c)}", SCHEMA, name="grade")
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, pr))
    ok = sum(r["accurate"] for r in res)
    print(f"Flags getroffen {len(pr)}/{len(exp['changes'])}, accurate {ok}/{len(pr)} = {ok/len(pr):.3f}")
    for (e, c), r in zip(pr, res):
        if not r["accurate"]:
            print(" ✗", e["change"], e.get("requirement_id") or (e.get("source") or {}).get("paragraph"), "|", r["why"][:300])

if __name__ == "__main__":
    from certreq import paths
    sub_p = sys.argv[1]
    exp_p = sys.argv[2] if len(sys.argv) > 2 else str(paths.PKG_DIR / "subgoal" / json.load(open(sub_p))["case_id"].removeprefix("subgoal-") / "expected.json")
    judge(sub_p, exp_p)
