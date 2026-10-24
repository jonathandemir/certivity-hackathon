# Certivity Challenge: von der Produktspezifikation zu den Anforderungen

Beitrag zum Certivity-Track des Industrial Agents Hackathon (München, 24.–25.10.2026): ein Agent, der aus einer
technischen Spezifikation und/oder Explosionszeichnung eines Fahrzeugbauteils die Engineering-Anforderungen nach
UN-Regelungen ableitet, jeweils mit Regelung, Version und Seite. Details: [docs/CONTEXT.md](docs/CONTEXT.md).

## Für Teammitglieder

```bash
git clone https://github.com/jonathandemir/certivity-hackathon.git certivity && cd certivity
scripts/setup                # auf main, Teilnehmerpaket + PDFs unter vendor/, .venv mit requirements.txt
```

Alle arbeiten direkt auf main. Danach Claude Code (oder einen anderen Agenten) **direkt in diesem Ordner** starten. Die Regeln für jede Session
stehen in [AGENTS.md](AGENTS.md), der aktuelle Stand in [docs/STATUS.md](docs/STATUS.md).

## Pipeline

```bash
.venv/bin/python -m pytest                                              # Tests
scripts/pull-first                                                      # vor zählenden Läufen
.venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/dev-rear-lamp   # → out/dev-rear-lamp.json
.venv/bin/python -m certreq eval out/dev-rear-lamp.json [--record E0xx --note "..."]  # validate + P/R/F1/F2
```

Stufen in `certreq/`: `select.py` (Regelungsauswahl), `extract.py` (Anforderungen), `pdf.py` (Absätze mit Seite),
`submission.py` (Abgabeformat), `evaluate.py` (Bewertung, Belege). Team-ID über `CERTIVITY_TEAM_ID`.

## Aufbau

| Pfad | Inhalt |
|---|---|
| AGENTS.md, CLAUDE.md | Arbeitsregeln für Agenten und Menschen |
| docs/ | CONTEXT, STATUS, PLAN, LEARNINGS, LOG |
| experiments/ | LEDGER (ein Versuch pro Zeile) und Belege unter runs/ |
| certreq/, tests/ | Pipeline und Tests |
| scripts/ | sync, log, claim, pull-first, session-start, stop-check, main-wt, tag-best, secret-scan, setup |
| vendor/ | Teilnehmerpaket von Certivity (nicht im Repo, Lizenz: nur für den Hackathon) |
