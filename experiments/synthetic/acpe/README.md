# R175-Prüfstein: zweite Referenzliste gegen Überanpassung

`spec.md` ist eine synthetische Spec (vom Team geschrieben). Referenz sind Certivitys 94 Anforderungen aus
`vendor/industrial-ai-hackathon/subgoal/dev/requirements_old.json`: Sie stammen aus UN R175 base. Das `old.pdf` des
Sub-Goals ist byte-gleich mit `UN_R175_base.pdf` im Index. Gewertet werden die Technik-Abschnitte 5–6 (78
Anforderungen). Die Liste deckt die ganze Regelung ab, also auch Varianten, die kein Bauteil hat. Anwendbarkeitsregeln
(`modes`, Filter) werden hier deshalb systematisch bestraft. Für Formulierungs- und Zerlegungsregeln ist der Prüfstein
fair. Belege: Ledger X-R175-*, LEARNINGS.

Die Referenzdatei nie committen (Lizenz). Sie liegt nur lokal unter `out/`:

```bash
mkdir -p out/x-r175 && python3 -c "import json; r=json.load(open('vendor/industrial-ai-hackathon/subgoal/dev/requirements_old.json')); json.dump({'case_id': 'x-r175', 'requirements': [x for x in r if x['source']['paragraph'].split('.')[0] in ('5', '6')]}, open('out/x-r175/expected-eng.json', 'w'))"
```

Lauf mit vorgegebener Regelung (etwa 30 s mit Opus) und Bewertung:

```bash
CERTREQ_PROVIDER=anthropic .venv/bin/python -m certreq run experiments/synthetic/acpe --regs "UN R175" --vision off \
  [--extract modal,llm,lists,tables,exempt,tests,modes,<neue-regel>] --out out/x-r175/<ID>.json
.venv/bin/python -m certreq eval out/x-r175/<ID>.json --expected out/x-r175/expected-eng.json --judge lenient --record X-R175-<ID>
```

Den Richter immer gleich lassen: Basis und Variante mit demselben Richter bewerten. Seit Sa abends ist das gpt-Guthaben fast
leer, also Claude: `CERTREQ_PROVIDER=anthropic … eval … --judge strict`. Die gpt-lenient-Werte unten sind dann nur noch
Rangfolge, keine Basis: die Basis (Standard mit Opus) einmal mit dem Claude-Richter neu bewerten (`certreq.judge --strict`
auf `experiments/runs/X-R175-C/submission.json.gz`, entpackt).

Bestwerte mit gpt-Richter lenient (Abschnitte 5–6):
- gpt-Extraktion: 0.578 / 0.597 (X-R175-B, B-rep)
- Opus-Extraktion: 0.657 / 0.660 (X-R175-C, C-rep)

Mit Opus fehlen 22 Anforderungen, davon 11 Pflichten von Hersteller oder Technischem Dienst („declare“, „demonstrate“,
„document to the Approval Authority“) und 11 Prüfbedingungen (6.2.x, 6.5).
