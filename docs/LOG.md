# LOG: Historie, nur anhängen

Nie Einträge ändern oder löschen. Neue Einträge nur mit `scripts/log "[typ] titel" "detail" …`; der Eintrag kommt
in denselben Commit wie der Code, den er beschreibt. `merge=union` (.gitattributes) führt parallele Einträge
konfliktfrei zusammen; `scripts/session-start` zeigt die neuesten Einträge aller Branches nach Zeit sortiert.

Kopfzeile: `### JJJJ-MM-TT HH:MM:SS +zone | [typ] titel | Autor @ Rechner | <branch>@<kurzhash>` (Stand beim Schreiben;
`+lokale Änderungen` = der beschriebene Code ist in diesem Commit). Typen: [change] [run] [finding] [decision]
[blocker] [handoff].

### 2026-10-24 13:08:41 +0200 | [change] Arbeitssystem eingerichtet | Jonathan @ MacBook-Pro-von-Jonathan | main@ohne-commit +lokale Änderungen
- AGENTS.md + CLAUDE.md (Regeln), docs/ (CONTEXT, STATUS, PLAN, LEARNINGS, LOG), experiments/LEDGER.md, scripts/ (log, sync, pull-first, session-start, stop-check, claim, main-wt, tag-best, secret-scan, setup), .claude/settings.json (SessionStart- und Stop-Hook)
- Geprüft: Testsuite mit bare origin + 3 Klonen, 134/134 auf macOS (bash 3.2, BSD) und Debian (bash 5.2, mawk)

### 2026-10-24 13:09:14 +0200 | [decision] Arbeitssystem für parallele Agenten und Menschen | Jonathan @ MacBook-Pro-von-Jonathan | main@9fffaa8
- Grundsatz: Das Repo ist das einzige gemeinsame Gedächtnis. Regeln in AGENTS.md, Projektfakten in docs/CONTEXT.md; CLAUDE.md lädt beide per @-Import.
- Branches: eine Person = ein Branch <vorname> (scripts/setup). Geteilte Dateien (AGENTS.md, CLAUDE.md, README.md, docs/, experiments/, scripts/, .claude/) nur auf main, geändert über den main-Worktree .worktrees/main (scripts/main-wt), nie per Branch-Wechsel. scripts/sync merged origin/main konfliktfrei in den eigenen Branch.
- Ausnahme docs/LOG.md: Eintrag im selben Commit wie der Code auf dem eigenen Branch, merge=union; scripts/session-start liest LOG.md aus allen origin-Branches, entfernt Duplikate und sortiert nach Zeit. Grund: Liegt LOG.md nur auf main, können Code und Logeintrag nie im selben Commit landen.
- Schleife: scripts/claim add → kleiner Schritt → Tests grün → scripts/log → Code + LOG in einem Commit → scripts/sync (mindestens alle 30 min, immer vor Schluss) → scripts/claim done, LEARNINGS, [handoff] am Session-Ende.
- sync: git pull --rebase ohne lokale Merge-Commits, sonst --no-rebase; Stopp mit Anleitung bei Konflikt, nichts gepusht; Secret-Scan der ausgehenden Commits vor jedem Push; nie force.
- Ergebnisse: scripts/pull-first vor jedem zählenden Lauf (Exit 0 = zählt, gibt <branch>@<hash> aus); Zeile in experiments/LEDGER.md + Beleg unter experiments/runs/<ID>/; Bestmarken als Tag best-<branch>-<wert> (scripts/tag-best); Entscheidungen nur auf echte Messungen, jede Änderung einzeln gegen die Bestmarke.
- Hooks (.claude/settings.json): SessionStart → scripts/session-start (STATUS + LOG im Kontext); Stop → scripts/stop-check --hook (Warnung; blockiert einmal, wenn Arbeit länger als 30 min ungepusht oder ein Konflikt offen ist).
- Tests: Sandbox mit bare origin, anna auf zwei Rechnern + ben. Geprüft u. a.: union-Merge von LOG.md bei rebase und merge ohne Konflikt, Merge-Pfad spielt lokalen Merge-Commit nicht neu ab, Konflikt stoppt ohne Push, Claim-Race beim Push (Retry), pull-first-Gates (ungetrackt, uncommittet, ungepusht, neuer Code auf main), Stop-Hook-JSON, Secret-Scan blockiert Push. 134/134 auf macOS (bash 3.2, BSD-Tools, git 2.51) und Debian (bash 5.2, GNU, mawk, git 2.47).
- Offen: Freeze-Zeiten in docs/PLAN.md vom Team bestätigen; Team-Namen fehlen noch in docs/STATUS.md.

### 2026-10-24 13:16:14 +0200 | [change] setup: PDF-Download mit certifi-Retry | Jonathan @ MacBook-Pro-von-Jonathan | main@b24caa0 +lokale Änderungen
- python.org-Python auf macOS hat keine CA-Zertifikate; setup versucht es nach CERTIFICATE_VERIFY_FAILED einmal mit SSL_CERT_FILE=$(python3 -m certifi), nur für diesen Aufruf
- Geprüft: UN_R3_base.pdf entfernt → erster Versuch 93/94 (SSL-Fehler), Retry 94/94, Datei bytegleich; bash -n ok
- LEARNINGS-Eintrag mit Beleg ergänzt

### 2026-10-24 13:16:49 +0200 | [handoff] Arbeitssystem fertig, Team-Onboarding offen | Jonathan @ MacBook-Pro-von-Jonathan | jonathan@857c5a0
- Stand: main@857c5a0 enthält Regeln, docs, Skripte, Hooks; getestet auf macOS + Debian (134/134), SessionStart-Hook in echter Claude-Session geprüft. Jonathans Rechner: Branch jonathan, .worktrees/main, Paket + 94 PDFs unter vendor/, ~/projects/CLAUDE.md angelegt.
- Nächster Schritt: Team auf hackathon.certivity.io registrieren (Team-ID in STATUS), Teammitglieder als Collaborators zum privaten Repo einladen, Namen in STATUS/Team, dann AP1 aus docs/PLAN.md claimen.
- Fallen: jsonschema fehlt in Jonathans Python (validate.py); ~/projects/CLAUDE.md wird auch in Sessions anderer Projekte unter ~/projects geladen (nach dem Hackathon löschen); Zeitumstellung in der Nacht auf Sonntag; Held-out ist ein Frontstoßfänger, nicht an der Heckleuchte überanpassen.

### 2026-10-24 13:27:36 +0200 | [change] AP1: Pipeline-Gerüst + Bewertungsschleife (certreq/) | Jonathan @ MacBook-Pro-von-Jonathan | jonathan@ef1d9f5 +lokale Änderungen
- CLI: .venv/bin/python -m certreq run <fall-ordner> [--regs ...] → out/<fall>.json + .meta.json (Git-Stand aus git); eval <abgabe> → validate.py + score_local.py + F2, --record <ID> legt Beleg unter experiments/runs/<ID>/ im main-Worktree ab (verweigert unsaubere/ungepushte Läufe)
- Stufen austauschbar: select.select_regulations (B0: Wortüberlappung Spec↔Titel, --regs erzwingt), extract.extract_requirements (B0: jeder Absatz mit 'shall'), pdf.parse_pdf (Absatz + Seite, Labels wie Referenz: '4.8.1.7', 'Annex 9 3.1', 'Annex 4 Part 1 1.2')
- Fix im Parser: Anhang-Überschriften nur in Reihenfolge akzeptieren; Tabellenzelle 'Annex 10 (values in' (UN R150 S. 5) hatte vorher alle Haupttext-Absätze falsch gelabelt (90/121 → 121/121 Referenz-Absätze mit Label + Seite gefunden)
- Tests: 8 grün (pytest), u. a. Regressionstest 121/121 Absätze der Referenz, Abgaben bestehen validate.py, expected.json wird nie gelesen
- Setup: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt (pymupdf, jsonschema, pytest)
