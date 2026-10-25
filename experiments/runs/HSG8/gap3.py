"""LLM: neue Pflichten je geändertem Absatz, die HSG7 noch nicht enthält."""
import json, sys, os
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "/Users/jonathandemir/projects/certivity")
os.environ.setdefault("CERTREQ_PROVIDER", "anthropic")
from certreq import subgoal as sg, llm
V = Path("/Users/jonathandemir/projects/certivity-a/vendor/industrial-ai-hackathon/subgoal/heldout")
old_s, new_s = sg.sentences_of(V / "old.pdf"), sg.sentences_of(V / "new.pdf")
pairs = sg.align(old_s, new_s)
inv = {i: (k, r) for k, (i, r) in pairs.items()}
regulation, version = sg.pdf_header(V / "new.pdf")
h7 = json.load(open("HSG7-subgoal-heldout.json"))["changes"]
groups = OrderedDict()
for i, s in enumerate(new_s):
    groups.setdefault(s.label, []).append(i)
todo = []
for lab, ids in groups.items():
    changed = False
    for i in ids:
        if i not in inv: changed = True; break
        k, r = inv[i]
        if r < 0.999 and sg._canon(old_s[k].full).lower() != sg._canon(new_s[i].full).lower() and \
           sg.diff_phrases(sg._canon(old_s[k].text), sg._canon(new_s[i].text)): changed = True; break
    if not changed: continue
    newp = " ".join(new_s[i].full for i in ids)
    if not sg.NORM_RE.search(newp): continue
    old_labels = OrderedDict((old_s[inv[i][0]].label, 1) for i in ids if i in inv)
    oldp = " ".join(s.full for s in old_s if s.label in old_labels) or "(no corresponding old text: the paragraph is new)"
    ex = [c for c in h7 if (c.get("source") or {}).get("paragraph") == lab]
    todo.append({"label": lab, "page": new_s[ids[0]].page, "old": oldp[:5000], "new": newp[:6000],
                 "existing": [f"[{c['change']}{' ' + c['requirement_id'] if c['requirement_id'] else ''}] {c['new_text']}" for c in ex]})
print("geänderte Absätze mit Pflichtwort:", len(todo), file=sys.stderr)

SYSTEM = """You find engineering requirements that are NEW in the new version of a UN Regulation paragraph.
You get the OLD paragraph text (if any), the NEW paragraph text, and the EXISTING ENTRIES our tool already reports for
this paragraph. List only obligations that (1) are new or substantively new in the NEW text compared to the OLD text
(a new duty, permission, prohibition, limit, condition or documentation/demonstration duty of the manufacturer), and
(2) are NOT already covered by an existing entry (same obligation, even if worded differently or merged with others).
Ignore renumbering, editorial rewording, changed cross-references, headings, definitions without a duty, and
administrative/transitional provisions about Contracting Parties or approvals. One obligation per item, written as a
standalone sentence close to the regulation wording, values and references exactly as in the text. Also give the
verbatim source sentence. If nothing is missing, return an empty list. Be strict: most paragraphs need nothing."""
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"], "properties": {"items": {"type": "array",
          "items": {"type": "object", "additionalProperties": False, "required": ["text", "quote"],
                    "properties": {"text": {"type": "string"}, "quote": {"type": "string"}}}}}}

def run(t):
    user = (f"Regulation: {regulation}, new version {version}, paragraph {t['label']}\n\nOLD PARAGRAPH:\n{t['old']}\n\n"
            f"NEW PARAGRAPH:\n{t['new']}\n\nEXISTING ENTRIES:\n" + ("\n".join(t["existing"]) or "(none)"))
    try:
        a = llm.ask_json(SYSTEM, user, SCHEMA, name="gap3")
    except (Exception, SystemExit) as e:
        return {**t, "error": str(e)[:200], "items": []}
    return {**t, "items": a["items"]}

llm.load_env()
with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(run, todo))
json.dump(res, open("gap3.json", "w"), indent=1, ensure_ascii=False)
print("Fehler:", sum("error" in r for r in res), "Funde:", sum(len(r["items"]) for r in res), file=sys.stderr)
for r in res:
    for it in r["items"]:
        print(f"[{r['label']} S.{r['page']}] {it['text'][:260]}")
