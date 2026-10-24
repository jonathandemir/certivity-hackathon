# STATUS: die Gegenwart, kurz und wahr

Nur auf main ändern (über `scripts/main-wt`). Claims nur mit `scripts/claim`. Veraltetes sofort löschen,
Historie steht in docs/LOG.md.

## Stand

AP1 steht: Pipeline-Gerüst `certreq` (run/eval) mit Baseline B0, Bewertungsschleife mit Belegen.
Bestmarke (zulässig, alle Ebenen): **E020-a** = `--select llm2 --filters all --extract modal,llm` (Tag `best-main-reqf2-0.629`): Anforderungen F2 **0.629** (P 0.392, R 0.742; lokaler Richter strict), Seiten 0.936, Regelungen 0.909. Vorher E016-a (`--select llm`) 0.621, E014 (B0-Auswahl) 0.491, B0 0.060. `--select llm2` ist seit E020-a Standard (verwirft Annahmen und reine Fahrzeugebene, am synthetischen Stoßfänger: R94/R137/R128/R152/R155/R156 raus); Filter/Extraktion stehen noch per Schalter.
Streuung (E019-a): identische Konfiguration ohne Cache 0.602 statt 0.621 → Unterschiede < ~0.03 sind nicht belastbar. AP5 (Zeichnung) fertig: `--vision auto` liest die Zeichnung, wenn keine Spec vorliegt (nur Zeichnung: F2 0.417, E017-a).
Anforderungs-Engpässe (E016-a): Recall je Regelung R10 14/32, R48 40/56, R150 33/39, R148 54/63; 376 eingereicht (Referenz 190), davon 30 aus den Extra-Regelungen R26/R13H/R42 (beim Stoßfänger vermutlich richtig, daher bewusst behalten).
Diagnose E002: Mit den richtigen Regelungen findet B0 alle 53 Gold-Seiten → größter Hebel ist die Auswahl (AP2),
danach Precision der Extraktion (AP4: 1214 statt ~190 Anforderungen).
Teamname: **BarelyLegal**. Team-ID der Certivity-Plattform: **team-12** (registriert 2026-10-24; Standard in `certreq/submission.py`, Passwort nicht im Repo).

## Team

| Name | Rolle | Rechner | Fokus |
|---|---|---|---|
| Jonathan Demir | A | MacBook-Pro-von-Jonathan | AP2 Auswahl, AP10 Richter, AP5 Vision, LLM-Zugang, Uploads |
| Homsianer | B | – | AP3-Rest Gliederung/Tabellen, AP4 Relevanzfilter + Zerlegung |
| Amiad | C | Fedora-Laptop (Claude über Cowork) | AP6 Demo, AP7 Sub-Goal, AP9 Pitch-Lead |

Alle arbeiten auf main. „Rechner" trägt jeder nach `scripts/setup` selbst ein. Details: docs/PLAN.md „Aufteilung".

## Claims

| Wer | Rechner | Was | Dateien | Seit |
|---|---|---|---|---|
| Jonathan | MacBook-Pro-von-Jonathan | AP3-Rest Gliederung + AP4 Relevanzfilter (B vorgezogen, Übergabe an Omar) | certreq/pdf.py, certreq/extract.py, tests/test_extract.py | 2026-10-24 14:10 |
| Jonathan | MacBook-Pro-von-Jonathan | AP4 LLM-Extraktion je Absatz (Relevanz + Zerlegung) | certreq/llmextract.py, tests/test_llmextract.py, certreq/extract.py | 2026-10-24 14:42 |
| Jonathan | MacBook-Pro-von-Jonathan | Upload-Vorbereitung (certreq/upload.py) + Plattform-Eichung | certreq/upload.py, tests/test_upload.py | 2026-10-24 15:56 |
| Jonathan | MacBook-Pro-von-Jonathan | Upload dev: E020-a + E008-a (Hauptziel), E003-am (Sub-Goal) – Plattform-Eichung | Plattform team-12 | 2026-10-24 16:10 |

## Nächste Schritte

1. **Jonathan (A):** Team auf https://hackathon.certivity.io/ registrieren, Team-ID oben eintragen (Passwort nicht ins Repo);
   Homsianer und Amiad als Collaborators ins GitHub-Repo einladen (GitHub-Namen nötig).
2. **Alle:** LLM-Zugang steht (`certreq/llm.py`, OpenAI). Einmal `scripts/setup` (installiert `openai`), Key in `.env.local` im eigenen Checkout (von Jonathan; nie ins Repo, nie in den Chat), Check: `.venv/bin/python -m certreq.llm`.
3. **Jonathan (A): Plattform-Eichung** (wichtigster offener Punkt). Dateien: `.venv/bin/python -m certreq.upload E020-a E008-a E003-am`
   → `out/upload/`. Hochladen: E020-a + E008-a (Hauptziel, dev-rear-lamp), E003-am (Sub-Goal, subgoal-dev). Angezeigte
   Plattformwerte an A geben → Eichung lokaler Richter (strict 0.629 / 0.060, lenient B0 0.095) und Sub-Goal-Näherung (0.826).
4. **B (Omar/Homsianer):** Standard auf `--filters all --extract modal,split` umstellen: auf der Anforderungsebene besser
   (E011-a 0.098 vs E010-a 0.084 vs B0 0.060), obwohl Seiten-F2 leicht sinkt (0.339 vs 0.348). Jede AP4-Änderung ab jetzt
   mit `eval --judge strict` messen (~1–2 min, ~150–330k Tokens; Wiederholungen gecacht).
5. **B:** Standard für Filter/Extraktion auf `--filters all --extract modal,llm` umstellen (E014/E016-a besser auf allen Ebenen). Größte Recall-Lücken: R10 (EMV-Prüfpegel als Einzelpflichten) und R48.
   **C (Sub-Goal):** `certreq/subgoal.py` nutzt noch `team-unregistered`; bitte `from .submission import TEAM_ID` (team-12) als Standard nehmen.
   **C (Demo):** `.meta.json` enthält jetzt `selection` (je Regelung Rolle + Begründung, auch verworfene wie „R7 in R148 aufgegangen") – gut für die Demo und den Pitch.
   **C:** Demo v2 steht (demo/README.md): `demo/run <fall-ordner>` = `certreq run` + `demo/prepare.py`, dann `demo/dist/index.html` öffnen, ohne Node/Server. Läuft für jeden Fall (Spec und/oder Zeichnung), am Dev-Fall 189/190 Anforderungen auf der PDF-Seite markiert. Nächstes C: `selection`-Begründungen in Szene 1, Pitch (AP9).
   **A (Bitte):** Falls `vision.py` je Bauteil eine Bildregion (bbox in Pixeln der Zeichnung) liefern kann, in `.meta.json` ablegen; dann verknüpft die Demo Zeichnungsteile mit Spec-Bauteilen.
   **A:** AP5 erledigt. Robustheit am synthetischen Stoßfänger geprüft (LEARNINGS): läuft, 4 min/neuer Fall. Nächster
   AP2b erledigt (E020-a, `--select llm2` Standard). Offenes Risiko Auswahl: R127 und GTR 9 überschneiden sich; welches das
   Gold nimmt, ist unbekannt (beide behalten, F2 gewichtet Recall).
   **B:** Bei GTRs nur den verbindlichen Teil „II. Text of the Regulation" extrahieren (GTR 9: ab S. 71; S. 1–70 sind
   Begründung). Betrifft den Held-out sehr wahrscheinlich, falls GTR 9 gewählt wird.
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
| dev-rear-lamp | Regelungen | 0.667 | 1.000 | 0.909 | main@fd0820a (`--select llm2 --filters all --extract modal,llm`) | best-main-reqf2-0.629 | score_local | E020-a | 2026-10-24 16:05 |
| dev-rear-lamp | Seiten | 0.746 | 1.000 | 0.936 | main@fd0820a (dto.) | best-main-reqf2-0.629 | score_local | E020-a | 2026-10-24 16:05 |
| dev-rear-lamp | Anforderungen | 0.392 | 0.742 | 0.629 | main@fd0820a (dto.) | best-main-reqf2-0.629 | lokaler Richter strict (gpt-6.1-sol) | E020-a | 2026-10-24 16:05 |
| dev-rear-lamp | Anforderungen | – | – | – | – | – | Plattform (offen, E001-Upload) | – | – |
