import json, sys
sys.path.insert(0, "/Users/jonathandemir/projects/certivity")
from pathlib import Path
from certreq import subgoal as sg
V = Path("/Users/jonathandemir/projects/certivity-a/vendor/industrial-ai-hackathon/subgoal/heldout")
regulation, version = sg.pdf_header(V / "new.pdf")
h7 = json.load(open("HSG7-subgoal-heldout.json"))
SKIP = {"2.28.1", "18"}  # Begriffsdefinitionen ohne Pflicht, Einleitungshinweis
new = []
for r in json.load(open("gap3.json")):
    if r["label"] in SKIP: continue
    for it in r["items"]:
        q = " ".join(it["quote"].split())[:300]
        new.append({"requirement_id": None, "change": "added", "new_text": " ".join(it["text"].split())[:2000],
                    "reason": f"Paragraph {r['label']} of {regulation} is new in version {version}: '{q}'.",
                    "source": {"page": r["page"], "paragraph": r["label"]}})
out = {**h7, "changes": h7["changes"] + new}
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(len(h7["changes"]), "→", len(out["changes"]), "(+%d added)" % len(new))
reqs = json.load(open(V / "requirements_old.json"))
fl = {c["requirement_id"] for c in out["changes"] if c["requirement_id"]}
print("alte Anf. 5.5.4.2.8.2 / 5.5.4.2.6.5 / Annex 3 3.5.6:", [(x["id"], x["source"]["paragraph"], x["id"] in fl) for x in reqs if x["source"].get("paragraph") in ("5.5.4.2.8.2", "5.5.4.2.6.5", "Annex 3 3.5.6")])
