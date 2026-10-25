"""LLM-Prüfung: Welche von HSG4 NICHT markierten alten Anforderungen ändern sich in der neuen Fassung doch?"""
import json, sys, os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "/Users/jonathandemir/projects/certivity")
os.environ.setdefault("CERTREQ_PROVIDER", "anthropic")
from certreq import subgoal as sg, llm

V = Path("/Users/jonathandemir/projects/certivity-a/vendor/industrial-ai-hackathon/subgoal/heldout")
OUT = Path(sys.argv[1])
hsg4 = json.load(open("/Users/jonathandemir/projects/certivity-a/out/upload/HSG4-subgoal-heldout.json"))
flagged = {c["requirement_id"] for c in hsg4["changes"] if c["requirement_id"]}
reqs = json.load(open(V / "requirements_old.json"))
todo = [r for r in reqs if r["id"] not in flagged]
print("alt:", len(reqs), "markiert:", len(flagged), "zu prüfen:", len(todo), file=sys.stderr)

regulation, version = sg.pdf_header(V / "new.pdf")
old_s, new_s = sg.sentences_of(V / "old.pdf"), sg.sentences_of(V / "new.pdf")
idx = sg.Index(new_s)
pairs = sg.align(old_s, new_s)

SYSTEM = """You check whether an engineering requirement, derived from the OLD version of a UN Regulation, changes in the
NEW version. You get the old requirement, the old paragraph(s) it came from and the corresponding new paragraph(s).
A change counts only if it alters what an engineer must do for THIS requirement: a value, limit, unit, tolerance, time,
speed; a condition, scope or applicability; an exception or exemption; a list item or sub-condition belonging to this
requirement added or removed; the modal strength (shall/may/should); or the obligation itself deleted.
Do NOT count: renumbering of paragraphs, changed cross-reference numbers, capitalisation, hyphenation, punctuation,
"Regulation" vs "UN Regulation", editorial rewording with the same meaning, or new content that belongs to a different
requirement. When unsure, answer changed=false.
If changed: write new_text = the requirement as it reads under the NEW version (keep the old wording where unchanged),
list the changes as short verbatim quotes (type became/added/removed) and give the new paragraph label."""
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["changed", "new_text", "new_paragraph", "changes"],
          "properties": {"changed": {"type": "boolean"}, "new_text": {"type": "string"}, "new_paragraph": {"type": "string"},
                         "changes": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                     "required": ["type", "old", "new"], "properties": {
                                         "type": {"type": "string", "enum": ["became", "added", "removed"]},
                                         "old": {"type": "string"}, "new": {"type": "string"}}}}}}


def ctx(req):
    srcs = sg._sources_of(req, old_s)
    label = req["source"].get("paragraph", "")
    old_labels = {old_s[k].label for k in srcs} | {label}
    matched = []
    for k in srcs:
        i, r = pairs[k] if k in pairs else idx.best(old_s[k].full)
        if i >= 0:
            matched.append(i)
    new_labels = {new_s[i].label for i in matched} | {label}
    oldp = " ".join(s.full for s in old_s if s.label in old_labels)[:5000]
    newp = "\n".join(f"[{s.label}, p.{s.page}] {s.full}" for s in new_s if s.label in new_labels)[:6000]
    page = new_s[min(matched)].page if matched else None
    lab = new_s[min(matched)].label if matched else label
    return oldp, newp, page, lab


def check(req):
    oldp, newp, page, lab = ctx(req)
    user = (f"Regulation: {regulation}, new version {version}\n\nOLD REQUIREMENT ({req['id']}, paragraph "
            f"{req['source'].get('paragraph')}):\n{req['text']}\n\nOLD PARAGRAPH TEXT:\n{oldp}\n\nNEW PARAGRAPH TEXT:\n{newp}")
    try:
        a = llm.ask_json(SYSTEM, user, SCHEMA, name="unflagged")
    except (Exception, SystemExit) as e:
        return {"id": req["id"], "error": str(e)[:200]}
    return {"id": req["id"], "old_text": req["text"], "old_paragraph": req["source"].get("paragraph"),
            "page": page, "label": lab, **a}


llm.load_env()
with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(check, todo))
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
ch = [r for r in res if r.get("changed")]
err = [r for r in res if "error" in r]
print("geändert laut LLM:", len(ch), "Fehler:", len(err), file=sys.stderr)
for r in ch:
    print(f"- {r['id']} {r['old_paragraph']} -> {r['new_paragraph']}: " + "; ".join(f"{c['type']}: '{c['old'][:60]}' -> '{c['new'][:80]}'" for c in r['changes']))
