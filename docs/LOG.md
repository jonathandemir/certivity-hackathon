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
