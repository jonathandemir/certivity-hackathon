import json, sys, re
sys.path.insert(0, "/Users/jonathandemir/projects/certivity")
from pathlib import Path
from certreq import subgoal as sg
V = Path("/Users/jonathandemir/projects/certivity-a/vendor/industrial-ai-hackathon/subgoal/heldout")
regulation, version = sg.pdf_header(V / "new.pdf")
h = json.load(open("/Users/jonathandemir/projects/certivity-a/out/upload/HSG4-subgoal-heldout.json"))
res = [x for x in json.load(open("result.json")) if x.get("changed")]
n = lambda s: " ".join(s.lower().split())
new = []
for x in res:
    chs = [({**c, "type": "became"} if c["type"] == "removed" and c["old"] and c["new"] else c) for c in x["changes"] if c["type"] == "removed" or n(c["new"])[:60] in n(x["new_text"])]
    reason = (f"Paragraph {x['new_paragraph']} of {regulation} was amended in version {version}: "
              + "; ".join(sg._phrase(c) for c in chs) + ".")
    new.append({"requirement_id": x["id"], "change": "modified", "new_text": " ".join(x["new_text"].split())[:2000],
                "reason": reason, "source": {"page": x["page"], "paragraph": x["new_paragraph"]}})
ch = h["changes"]
last_mod = max(i for i, c in enumerate(ch) if c["change"] == "modified")
out = {**h, "changes": ch[:last_mod + 1] + new + ch[last_mod + 1:]}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(len(ch), "→", len(out["changes"]), "Version", version)
for c in new: print(c["requirement_id"], "|", c["reason"][:230])
