# CLAUDE.md

Dieses Repo nutzt ein gemeinsames Arbeitssystem für mehrere Agenten und Menschen auf verschiedenen Rechnern.
Die Arbeitsregeln (AGENTS.md) und die Projektfakten (docs/CONTEXT.md) sind unten importiert und gelten für jede Session.

@AGENTS.md
@docs/CONTEXT.md

## Nur für Claude Code

- `.claude/settings.json` (committet) hat zwei Hooks: SessionStart → `scripts/session-start` (Teamstand landet im
  Kontext), Stop → `scripts/stop-check --hook` (warnt bei ungepushter Arbeit, blockiert einmal, wenn sie älter als
  30 Minuten ist).
- Siehst du keinen Abschnitt „# Teamstand" im Kontext, ist der Hook nicht gelaufen: `scripts/session-start` selbst ausführen.
- Persönliche Einstellungen gehören in `.claude/settings.local.json` (gitignored), nicht in `.claude/settings.json`.
