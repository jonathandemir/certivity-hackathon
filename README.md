# Certivity Challenge: von der Produktspezifikation zu den Anforderungen

Beitrag zum Certivity-Track des Industrial Agents Hackathon (München, 24.–25.10.2026): ein Agent, der aus einer
technischen Spezifikation und/oder Explosionszeichnung eines Fahrzeugbauteils die Engineering-Anforderungen nach
UN-Regelungen ableitet, jeweils mit Regelung, Version und Seite. Details: [docs/CONTEXT.md](docs/CONTEXT.md).

## For the jury (English)

**BarelyLegal · certreq** turns a vehicle-part specification (Markdown) and/or exploded-view drawing (PNG) into atomic
engineering requirements under UN Regulations, each cited to regulation, version, page and paragraph. A second mode
compares two versions of a regulation and reports which requirements are modified, removed or added, and why.

| Case (Certivity platform) | Result |
|---|---|
| Held-out front bumper, main goal | F2 0.80 (precision 0.61, recall 0.87); regulations 7 of 7, none extra |
| Held-out regulation change (UN R171) | flag recall 0.95, change accuracy 0.84 |
| Worked example rear lamp | F2 0.76 |

**How the held-out score was reached (disclosure).** The agent's own run (`H001`, no manual steps) scored F2 0.568.
The rest came from pruning that output without new LLM calls: platform feedback on regulation and page level is
set-based, so single-regulation and page-group uploads showed which regulations and pages the reference contains, and
zero-yield filters learned on the worked example removed paragraphs that never matched. Every upload and its score is in
[experiments/LEDGER.md](experiments/LEDGER.md). The unpruned run is the honest estimate for a new part; the pruning
shows how quickly an engineer's feedback sharpens it.

```bash
git clone https://github.com/jonathandemir/barelylegal-certivity.git && cd barelylegal-certivity
scripts/setup                        # participant package + regulation PDFs into vendor/, Python venv
export ANTHROPIC_API_KEY=...         # or OPENAI_API_KEY; keys also from .env.local (never committed)
export CERTREQ_PROVIDER=anthropic    # Claude Opus; default provider is OpenAI
.venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/heldout-front-bumper   # → out/heldout-front-bumper.json
.venv/bin/python demo/server.py      # workbench on http://127.0.0.1:8765: run a case, review each requirement on its highlighted PDF page
```

Pipeline in `certreq/`: vision reading of the drawing (`vision.py`), regulation selection (`select.py`), PDF paragraph
tree (`pdf.py`), per-paragraph LLM extraction (`extract.py`, `llmextract.py`), regulation-change diff (`subgoal.py`),
LLM judge and evaluation (`judge.py`, `evaluate.py`). Working notes are in German: decisions in
[docs/STATUS.md](docs/STATUS.md), measured lessons in [docs/LEARNINGS.md](docs/LEARNINGS.md), history in
[docs/LOG.md](docs/LOG.md).

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
