# Abgabe „Hack and More": Formulartexte (Stand 12:15, Jonathan)

Zum Kopieren ins Formular. Zeichenzahlen geprüft. Die Held-out-Zahl (F2 0.80) nach dem letzten Upload um 12:47 prüfen
(docs/STATUS.md) und bei Bedarf anpassen. Formular kann bis 13:00 von allen bearbeitet werden.

## Project name (52/60)

BarelyLegal: part spec in, cited UN requirements out

## One-line pitch (135/140)

Give it a part spec or drawing, get every UN-regulation duty it must meet, cited to page and paragraph, and what changes when rules do.

## Technical Solution (792/800, Markdown)

**certreq** (Python): provider-agnostic LLM layer (Claude Opus 5.5 / OpenAI), JSON-schema outputs, hashed response cache. A vision model reads the exploded view (parts, functions, vehicle category). One LLM call selects regulations from auto-built briefs of all 56 UN regulations, with a reason per decision. PyMuPDF paragraph tree; batched per-paragraph extraction of atomic *shall*-obligations cited to regulation, version, page and paragraph. **Regulation change:** renumbering-robust PDF diff (1:1 sentence alignment) plus LLM-written reasons. **Evaluation:** platform-calibrated LLM judge, F2-optimal pruning, 100+ logged ablations; held-out pruning from platform feedback, disclosed in the README. Workbench links each requirement to its PDF page.
Held-out: F2 0.80, change recall 0.95.

## Challenges

Certivity (Hauptziel + optionales Sub-Goal „regulation change"). Falls Freitext: „Certivity: spec/drawing → UN
regulation requirements (main) and regulation-change impact (optional sub-goal)".

## Links

- Repository: https://github.com/jonathandemir/barelylegal-certivity (öffentliche Kopie ohne Git-Historie, `scripts/export-snapshot`)
- Demo Video: Link von Amiad (YouTube nicht gelistet oder Loom, max. 2:00)
- Deployment Link: leer lassen (Werkbank läuft lokal, `demo/server.py`)
- Artifacts (nur Google Drive): optional, leer lassen

## Tags (Built with, 15/15)

Python, Claude Opus 5.5, Anthropic API, OpenAI API, Claude Code, PyMuPDF, JSON Schema, Vision LLM, LLM-as-judge, React, three.js, pytest, UNECE, Homologation, RegTech
