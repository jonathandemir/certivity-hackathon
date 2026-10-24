# STATUS: die Gegenwart, kurz und wahr

Nur auf main ändern (über `scripts/main-wt`). Claims nur mit `scripts/claim`. Veraltetes sofort löschen,
Historie steht in docs/LOG.md.

## Stand

AP1 steht: Pipeline-Gerüst `certreq` (run/eval) mit Baseline B0, Bewertungsschleife mit Belegen.
Bestmarke Seiten/Regelungen (zulässig): E008 (`--filters all --extract modal,llm`: Relevanzfilter + LLM-Extraktion je Absatz), Seiten-F2 0.714, Regelungs-F2 0.556 lokal (mit Gold-Regelungen Seiten 0.943). **Anforderungsebene (Hauptscore) jetzt lokal messbar** (AP10-Richter, `eval --judge strict`): Bestmarke E011-a `--filters all --extract modal,split` F2 0.098 (P 0.025, R 0.384); B0 0.060. E008 auf Anforderungsebene noch ungemessen. Standard ohne Schalter ist weiter B0.
Anforderungs-Engpässe (E011-a): 32 von 190 fehlen, weil UN R10 nicht gewählt ist (AP2); 85 trotz Kandidaten (Absätze statt Einzelpflichten, AP4); Precision 0.025 (2966 statt ~190 Anforderungen).
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
| Jonathan | MacBook-Pro-von-Jonathan | AP4 LLM-Extraktion je Absatz (Relevanz + Zerlegung) | certreq/llmextract.py, tests/test_llmextract.py, certreq/extract.py | 2026-10-24 14:42 |

## Nächste Schritte

1. **Jonathan (A):** Team auf https://hackathon.certivity.io/ registrieren, Team-ID oben eintragen (Passwort nicht ins Repo);
   Homsianer und Amiad als Collaborators ins GitHub-Repo einladen (GitHub-Namen nötig).
2. **Alle:** LLM-Zugang steht (`certreq/llm.py`, OpenAI). Einmal `scripts/setup` (installiert `openai`), Key in `.env.local` im eigenen Checkout (von Jonathan; nie ins Repo, nie in den Chat), Check: `.venv/bin/python -m certreq.llm`.
3. **Jonathan (A, AP1-Rest):** E001 mit echter Team-ID hochladen, Anforderungs-Score ins Scoreboard. Der Wert eicht den
   lokalen Richter: liegt er nahe E008-a (strict, F2 0.060) oder E009-a (lenient, F2 0.095)? Datei neu erzeugen:
   `CERTIVITY_TEAM_ID=<id> .venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/dev-rear-lamp`
   (gleicher Commit wie E001, nur `team_id` anders). E002 nicht hochladen: nutzt Gold-Wissen, verfälscht das Dev-Leaderboard.
4. **B (Omar/Homsianer):** Standard auf `--filters all --extract modal,split` umstellen: auf der Anforderungsebene besser
   (E011-a 0.098 vs E010-a 0.084 vs B0 0.060), obwohl Seiten-F2 leicht sinkt (0.339 vs 0.348). Jede AP4-Änderung ab jetzt
   mit `eval --judge strict` messen (~1–2 min, ~150–330k Tokens; Wiederholungen gecacht).
5. **Jonathan (A):** AP2 Regelungsauswahl (R10 fehlt: 32 von 190 Anforderungen).
6. **Homsianer (B), Amiad (C):** Repo klonen, `scripts/setup` (stellt auf main, holt Paket + PDFs, legt .venv an),
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
| 2026-10-24 | Lokaler Richter (AP10) bewertet standardmäßig strikt | Gegenprobe: strict 0 echte Fehlurteile (5 Treffer = Duplikate in der Referenz), lenient 10 → 5,3 % falscher Recall. Eichung gegen Plattform mit E001-Upload | Jonathan |
| offen | Freeze-Zeiten aus docs/PLAN.md bestätigen | Vorschlag, Team muss zustimmen | Team |

## Scoreboard

Nur echte Messungen auf einem gepushten, sauberen Commit. F2 = 5·P·R/(4·P+R). Beleg = Datei unter experiments/runs/.

| Fall | Ebene | P | R | F2 | Commit (branch@hash) | Tag | Quelle | Beleg | Wann |
|---|---|---|---|---|---|---|---|---|---|
| dev-rear-lamp | Regelungen | 0.273 | 0.750 | 0.556 | main@dc1350a (`--filters all --extract modal,llm`) | best-main-pagef2-0.714 | score_local | E008 | 2026-10-24 14:53 |
| dev-rear-lamp | Seiten | 0.437 | 0.849 | 0.714 | main@dc1350a (`--filters all --extract modal,llm`) | best-main-pagef2-0.714 | score_local | E008 | 2026-10-24 14:53 |
| dev-rear-lamp | Anforderungen | 0.025 | 0.384 | 0.098 | main@66d51fc (`--filters all --extract modal,split`) | – | lokaler Richter strict (gpt-6.1-sol) | E011-a | 2026-10-24 15:00 |
| dev-rear-lamp | Anforderungen | – | – | – | – | – | Plattform (offen, E001-Upload) | – | – |
