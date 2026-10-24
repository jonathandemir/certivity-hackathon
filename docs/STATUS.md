# STATUS: die Gegenwart, kurz und wahr

Nur auf main ändern (über `scripts/main-wt`). Claims nur mit `scripts/claim`. Veraltetes sofort löschen,
Historie steht in docs/LOG.md.

## Stand

Arbeitssystem steht (AGENTS.md, docs/, scripts/, Hooks). Noch kein Pipeline-Code, noch keine Messung.
Team-ID der Certivity-Plattform: noch nicht registriert.

## Team

| Name | Branch | Rechner | Fokus |
|---|---|---|---|
| Jonathan Demir | jonathan | MacBook-Pro-von-Jonathan | offen |

Weitere Mitglieder: Zeile ergänzen (über den main-Worktree), Branch kommt von `scripts/setup <vorname>`.

## Claims

| Wer | Branch | Was | Dateien | Seit |
|---|---|---|---|---|
| Jonathan | jonathan | AP1 Gerüst + Bewertungsschleife | certreq/, tests/, requirements.txt | 2026-10-24 13:22 |

## Nächste Schritte

1. Team auf https://hackathon.certivity.io/ registrieren, Team-ID oben eintragen (Passwort nicht ins Repo).
2. Teammitglieder: Repo-Zugang, `scripts/setup <vorname>`, Zeile unter „Team".
3. AP1 (docs/PLAN.md): Gerüst + Bewertungsschleife, erster valider End-to-End-Upload auf `dev-rear-lamp`.
4. Arbeitspakete AP2–AP7 per Claim verteilen.

## Entscheidungen

| Datum | Entscheidung | Warum | Wer |
|---|---|---|---|
| 2026-10-24 | Arbeitssystem nach AGENTS.md: persönliche Branches, geteilte Dateien nur auf main (main-Worktree), Claims, LOG, LEDGER | Mehrere Agenten und Rechner parallel; das Repo ist das einzige gemeinsame Gedächtnis | Jonathan |
| 2026-10-24 | docs/LOG.md ist die Ausnahme: Einträge gehen mit dem Code in den eigenen Branch, `merge=union`, gelesen über alle Branches | Sonst unmöglich, Code und Logeintrag im selben Commit zu haben | Jonathan |
| 2026-10-24 | Teilnehmerpaket und PDFs nur unter `vendor/` (gitignored), nie im Repo | LICENSE-DATA.md: keine Weitergabe; das Repo wird zur Abgabe geteilt | Jonathan |
| 2026-10-24 | GitHub-Repo privat bis zur Abgabe; vor R4 Sichtbarkeit klären | Kein Zugriff Dritter während des Events | Jonathan |
| offen | Freeze-Zeiten aus docs/PLAN.md bestätigen | Vorschlag, Team muss zustimmen | Team |

## Scoreboard

Nur echte Messungen auf einem gepushten, sauberen Commit. F2 = 5·P·R/(4·P+R). Beleg = Datei unter experiments/runs/.

| Fall | Ebene | P | R | F2 | Commit (branch@hash) | Tag | Quelle | Beleg | Wann |
|---|---|---|---|---|---|---|---|---|---|
| dev-rear-lamp | – | – | – | – | noch keine Messung | – | – | – | – |
