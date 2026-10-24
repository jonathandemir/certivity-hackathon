# STATUS: die Gegenwart, kurz und wahr

Nur auf main ändern (über `scripts/main-wt`). Claims nur mit `scripts/claim`. Veraltetes sofort löschen,
Historie steht in docs/LOG.md.

## Stand

AP1 steht: Pipeline-Gerüst `certreq` (run/eval) mit Baseline B0, Bewertungsschleife mit Belegen.
Bestmarke (zulässig): E006 (`--filters all`, Relevanzfilter AP4), Seiten-F2 0.348 lokal (mit Gold-Regelungen 0.773); Standard ohne Schalter ist weiter B0 (E001, 0.272), bis der E001-Upload geeicht ist. Anforderungsebene noch ungemessen (braucht Plattform-Upload).
Diagnose E002: Mit den richtigen Regelungen findet B0 alle 53 Gold-Seiten → größter Hebel ist die Auswahl (AP2),
danach Precision der Extraktion (AP4: 1214 statt ~190 Anforderungen).
Team-ID der Certivity-Plattform: noch nicht registriert.

## Team

| Name | Rolle | Rechner | Fokus |
|---|---|---|---|
| Jonathan Demir | A | MacBook-Pro-von-Jonathan | AP2 Auswahl, AP10 Richter, AP5 Vision, LLM-Zugang, Uploads |
| Homsianer | B | – | AP3-Rest Gliederung/Tabellen, AP4 Relevanzfilter + Zerlegung |
| Amiad | C | – | AP6 Demo, AP7 Sub-Goal, AP9 Pitch-Lead |

Alle arbeiten auf main. „Rechner" trägt jeder nach `scripts/setup` selbst ein. Details: docs/PLAN.md „Aufteilung".

## Claims

| Wer | Rechner | Was | Dateien | Seit |
|---|---|---|---|---|
| Jonathan | MacBook-Pro-von-Jonathan | AP3-Rest Gliederung + AP4 Relevanzfilter (B vorgezogen, Übergabe an Omar) | certreq/pdf.py, certreq/extract.py, tests/test_extract.py | 2026-10-24 14:10 |
| Jonathan | MacBook-Pro-von-Jonathan | AP10 Lokaler LLM-Richter (Anforderungsebene) | certreq/judge.py, tests/test_judge.py, certreq/evaluate.py, eval-Teil von certreq/__main__.py | 2026-10-24 14:41 |
| Jonathan | MacBook-Pro-von-Jonathan | AP4 LLM-Extraktion je Absatz (Relevanz + Zerlegung) | certreq/llmextract.py, tests/test_llmextract.py, certreq/extract.py | 2026-10-24 14:42 |
| Jonathan | MacBook-Pro-von-Jonathan | run-Teil __main__.py: LLM-Stats in meta.json, klein | certreq/__main__.py (cmd_run) | 2026-10-24 14:52 |

## Nächste Schritte

1. **Jonathan (A):** Team auf https://hackathon.certivity.io/ registrieren, Team-ID oben eintragen (Passwort nicht ins Repo);
   Homsianer und Amiad als Collaborators ins GitHub-Repo einladen (GitHub-Namen nötig).
2. **Alle:** LLM-Zugang steht (`certreq/llm.py`, OpenAI). Einmal `scripts/setup` (installiert `openai`), Key in `.env.local` im eigenen Checkout (von Jonathan; nie ins Repo, nie in den Chat), Check: `.venv/bin/python -m certreq.llm`.
3. **Jonathan (A, AP1-Rest):** E001 mit echter Team-ID hochladen, Anforderungs-Score ins Scoreboard. Datei neu erzeugen:
   `CERTIVITY_TEAM_ID=<id> .venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/dev-rear-lamp`
   (gleicher Commit wie E001, nur `team_id` anders). E002 nicht hochladen: nutzt Gold-Wissen, verfälscht das Dev-Leaderboard.
4. **Homsianer (B), Amiad (C):** Repo klonen, `scripts/setup` (stellt auf main, holt Paket + PDFs, legt .venv an),
   „Rechner" unter Team eintragen, dann erstes Paket per `scripts/claim add` übernehmen (Reihenfolge: docs/PLAN.md).

## Entscheidungen

| Datum | Entscheidung | Warum | Wer |
|---|---|---|---|
| 2026-10-24 | Arbeitssystem nach AGENTS.md: alle auf main, Claims, LOG, LEDGER, Tests vor jedem Code-Push | Drei Leute + Agenten parallel; das Repo ist das einzige gemeinsame Gedächtnis | Jonathan |
| 2026-10-24 | Alle arbeiten direkt auf main statt auf persönlichen Branches (ersetzt den ursprünglichen Plan) | Getrennte Dateien je Person, gegenseitige Abhängigkeiten (llm.py, Ausgaben für die Demo), weniger Git-Aufwand; Schutz durch Tests in sync und Schalter für neue Ansätze | Jonathan |
| 2026-10-24 | Teilnehmerpaket und PDFs nur unter `vendor/` (gitignored), nie im Repo | LICENSE-DATA.md: keine Weitergabe; das Repo wird zur Abgabe geteilt | Jonathan |
| 2026-10-24 | GitHub-Repo privat bis zur Abgabe; vor R4 Sichtbarkeit klären | Kein Zugriff Dritter während des Events | Jonathan |
| 2026-10-24 | Aufteilung: A = Jonathan (AP2, AP10, AP5, LLM-Zugang, Uploads), B = Homsianer (AP3-Rest, AP4), C = Amiad (AP6, AP7, Pitch-Lead); So alle AP8 | Drei Stränge mit festen Dateigrenzen; B misst mit `--regs`, C arbeitet auf der JSON-Ausgabe, niemand wartet | Jonathan |
| 2026-10-24 | LLM: OpenAI über `certreq/llm.py`, Modell `gpt-6.1-sol` für alles; Key in `.env.local` (gitignored) | Vorgabe Jonathan; Live-Test ok (Structured Output, ~3 s/Aufruf). Kein datierter Snapshot verfügbar, Cache hält Antworten reproduzierbar | Jonathan |
| offen | Freeze-Zeiten aus docs/PLAN.md bestätigen | Vorschlag, Team muss zustimmen | Team |

## Scoreboard

Nur echte Messungen auf einem gepushten, sauberen Commit. F2 = 5·P·R/(4·P+R). Beleg = Datei unter experiments/runs/.

| Fall | Ebene | P | R | F2 | Commit (branch@hash) | Tag | Quelle | Beleg | Wann |
|---|---|---|---|---|---|---|---|---|---|
| dev-rear-lamp | Regelungen | 0.143 | 0.750 | 0.405 | jonathan@29c0d0b | best-jonathan-pagef2-0.272 | score_local | E001 | 2026-10-24 13:27 |
| dev-rear-lamp | Seiten | 0.103 | 0.849 | 0.348 | main@3e979ed (`--filters all`) | best-main-pagef2-0.348 | score_local | E006 | 2026-10-24 14:41 |
| dev-rear-lamp | Anforderungen | – | – | – | jonathan@29c0d0b | – | Plattform (offen) | – | – |
