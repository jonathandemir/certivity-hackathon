# AGENTS.md: Regeln für jede Session

Mehrere KI-Agenten und Menschen arbeiten parallel von verschiedenen Rechnern an diesem Repo.
**Das Repo ist das einzige gemeinsame Gedächtnis. Was nicht committet, geloggt und gepusht ist, existiert für
die anderen nicht.** Diese Regeln gelten für jede Session, auch wenn niemand sie erwähnt.
Projektfakten: docs/CONTEXT.md.

## 0. Wo was steht

| Datei | Genau eine Aufgabe |
|---|---|
| docs/CONTEXT.md | Fakten und Regeln des Projekts (Aufgabe, Termine, Format, Bewertung) |
| docs/STATUS.md | Gegenwart: Stand, Team, Claims, nächste Schritte, Entscheidungen, Scoreboard |
| docs/PLAN.md | Ziele, Arbeitspakete, Zeitplan, Freezes |
| docs/LEARNINGS.md | Was funktioniert und was nicht, jeweils mit Beleg; „Verworfen, nicht erneut versuchen" |
| docs/LOG.md | Historie, nur anhängen (per `scripts/log`) |
| experiments/LEDGER.md | Eine Zeile pro Versuch mit Messung gegen die Bestmarke |
| experiments/runs/<ID>/ | Belege: hochgeladene/bewertete Ausgaben, Score-Ausgaben (klein, keine Rohdaten) |
| vendor/industrial-ai-hackathon/ | Teilnehmerpaket + PDFs (gitignored, Lizenz: nie ins Repo) |
| .worktrees/main/ | main-Checkout für geteilte Dateien (gitignored, von `scripts/main-wt` angelegt) |

## 1. Sessionstart (immer, in dieser Reihenfolge)

1. `scripts/sync`: holt deinen Branch, merged main mit (wenn konfliktfrei) und pusht.
2. STATUS und LOG lesen. Der SessionStart-Hook gibt beides aus (`scripts/session-start`). Fehlt die Ausgabe im
   Kontext (z. B. Session im Oberordner gestartet), führe `scripts/session-start` selbst aus.
3. Aufgabe gegen die Claims prüfen. **Überschneidet sie sich mit einem fremden Claim (gleiche Dateien oder gleiches
   Thema), sag es dem Menschen, bevor du anfängst.**
4. Vor jeder Idee: docs/LEARNINGS.md „Verworfen" und experiments/LEDGER.md prüfen. Ist sie schon widerlegt, sag
   es mit Beleg, statt sie erneut zu bauen.

## 2. Arbeitsschleife

1. **Claim setzen:** `scripts/claim add "Was" "Dateien/Ordner"` (pusht sofort auf main).
2. **Kleiner Schritt** (deutlich unter 30 Minuten).
3. **Tests grün:** die Tests des berührten Codes; erzeugt der Schritt eine Abgabedatei, zusätzlich
   `python3 vendor/industrial-ai-hackathon/tools/validate.py <datei>`. Rot wird nicht committet.
4. **Loggen:** `scripts/log "[change] titel" "was und warum" "wie geprüft"`.
5. **Commit:** `git status` lesen, dann gezielt `git add <deine dateien> docs/LOG.md` und `git commit`.
   Code und Logeintrag im selben Commit.
6. **`scripts/sync`.**

Mindestens alle 30 Minuten und immer vor dem Aufhören pushen. Fertig mit einer Aufgabe:
`scripts/claim done "Was"`, dauerhafte Erkenntnisse mit Beleg in docs/LEARNINGS.md (auf main).

## 3. Git-Sicherheit (nie verhandelbar)

- Nie fremde Dateien überschreiben: nur Dateien aus deinem Claim oder solche, die du selbst angelegt hast.
- Nie `git push --force` / `--force-with-lease`, nie `git reset --hard`, `git checkout -- .`, `git restore .`,
  `git clean -f`, `git stash drop` über Arbeit, die nicht nachweislich deine eigene ist.
- **Vor jedem `git add`: `git status`.** Nie blind `git add -A` / `git add .`.
- Konflikt: nur eigene Dateien selbst lösen; bei fremden Dateien den Menschen fragen. docs/LOG.md: beide Einträge
  behalten. Abbrechen ist immer sicher (`git rebase --abort` / `git merge --abort`).
- Nie den Branch im gemeinsamen Checkout wechseln, um geteilte Dateien zu ändern (siehe §4).

## 4. Branches und geteilte Dateien

- Jede Person arbeitet auf einem eigenen Branch (`<vorname>`, klein, angelegt von `scripts/setup <vorname>`).
  Code entsteht dort. Agenten derselben Person teilen deren Branch, Claims verhindern Doppelarbeit.
- **Geteilte Dateien liegen nur auf main:** AGENTS.md, CLAUDE.md, README.md, docs/, experiments/ (Ergebnisdaten),
  scripts/, .claude/, .gitignore, .gitattributes. Ändern **über den main-Worktree**, nie per Branch-Wechsel:
  ```bash
  MAIN=$(scripts/main-wt)              # legt .worktrees/main an bzw. spult vor, gibt den Pfad aus
  # Dateien unter $MAIN/... bearbeiten
  git -C "$MAIN" status
  git -C "$MAIN" add docs/STATUS.md && git -C "$MAIN" commit -m "status: ..."
  "$MAIN/scripts/sync"
  ```
  `scripts/sync` warnt, wenn auf einem persönlichen Branch geteilte Dateien geändert wurden.
- **Ausnahme docs/LOG.md:** Logeinträge kommen mit dem Code in deinen Branch (Regel §2.5). Das ist konfliktfrei,
  weil LOG.md nur angehängt wird und `merge=union` hat. `scripts/session-start` liest LOG.md aus **allen**
  origin-Branches und zeigt die Einträge zusammengeführt, also sieht jeder alle Einträge, sobald sie gepusht sind.
  Logeinträge ohne Code (z. B. `[decision]`) gehen in den Branch, auf dem du gerade bist.
- `scripts/sync` merged origin/main regelmäßig in deinen Branch (nur wenn konfliktfrei; sonst Warnung).
- **Vor der Deadline wird die beste gemessene Version nach main gemergt** (Zeitpunkt: docs/PLAN.md). Wer merged,
  steht als Entscheidung in docs/STATUS.md.

## 5. Ergebnisse, Läufe, Experimente

- **Vor jedem teuren oder zählenden Lauf: `scripts/pull-first`** (holt den Teamstand; Exit 0 = Lauf zählt).
  Sonst misst man veralteten Code.
- Jedes Ergebnis (Messung, Run, Benchmark, Upload-Score) nennt seinen Commit als `<branch>@<kurzhash>`: gepusht,
  sauberes Arbeitsverzeichnis. **Hashes aus git lesen (`git rev-parse --short HEAD`, Ausgabe von pull-first),
  nie erfinden oder schätzen.**
- Ergebnis eintragen: `[run]`-Logeintrag + Zeile in experiments/LEDGER.md + Belegdatei unter experiments/runs/<ID>/
  (über den main-Worktree; `.venv/bin/python -m certreq eval <abgabe> --record <ID>` legt den Beleg ab).
  Loggst du den Lauf aus einem anderen Checkout als dem gemessenen (z. B. im main-Worktree), gib den gemessenen Stand
  an: `"$MAIN/scripts/log" --commit <branch>@<hash> "[run] ..."`. Das Skript prüft, dass der Commit existiert und gepusht ist. Neue Bestmarke: zusätzlich Scoreboard in docs/STATUS.md und
  `scripts/tag-best <wert>` (Tag `best-<branch>-<wert>`, damit man jederzeit zurück kann).
- **Entscheidungen nur anhand echter Messungen** (score_local.py, Plattform-Score), nie anhand von Simulation,
  Schätzung oder Bauchgefühl. **Jede Änderung einzeln gegen die aktuelle Bestmarke messen**, nicht mehrere auf einmal.
- Plattform-Uploads sind knapp (5 valide/Stunde/Challenge für das ganze Team): vorher `scripts/claim add "upload ..."`,
  hochgeladene Datei und angezeigten Score in experiments/runs/ sichern. Held-out: **der letzte valide Upload zählt.**

## 6. Geheimnisse und Daten

- Keine Schlüssel, Tokens, Passwörter (auch nicht das Plattform-Passwort), `.env` oder Rohdaten in git.
  Schlüssel nur über Umgebungsvariablen bzw. lokale `.env` (gitignored).
- Paketdaten (cases/, subgoal/, index.json, PDFs, Held-out-Eingaben) nie ins Repo kopieren: Lizenz verbietet
  Weitergabe, das Repo wird zur Abgabe geteilt. Nur eigene Ausgaben und Scores committen.
- Vor dem Committen von Transkripten oder Logs: `scripts/secret-scan <dateien>`. `scripts/sync` prüft ausgehende
  Commits automatisch und bricht bei einem Fund ab.

## 7. Haltung

- **Denk mit.** Macht der Mensch einen Denkfehler oder ist eine Idee schon widerlegt, sag es direkt und mit Beleg
  (LEARNINGS, LEDGER, Messung, Quelle). Zustimmen, weil es bequem ist, schadet dem Team.
- Unsicher? Sag, was du nicht weißt, und wie man es messen kann.
- **Memory** (persönlicher Agentenspeicher) nur für dauerhafte Präferenzen der Person. Arbeitsstände, Ergebnisse
  und Entscheidungen gehören ins Repo.
- **Session-Ende:** `scripts/log "[handoff] ..." "Stand: ..." "Nächster Schritt: ..." "Fallen: ..."`, committen,
  `scripts/sync`, Claim entfernen oder bewusst stehen lassen, `scripts/stop-check` muss sauber sein.

## 8. Log-Typen

| Typ | Wann |
|---|---|
| `[change]` | Code oder Doku geändert |
| `[run]` | Messung, Lauf, Upload, mit `<branch>@<hash>` und Zahlen |
| `[finding]` | Erkenntnis aus Daten, Quellen oder Fehlern |
| `[decision]` | Entscheidung mit Begründung (auch in STATUS „Entscheidungen") |
| `[blocker]` | Etwas blockiert dich oder andere |
| `[handoff]` | Session-Ende: Stand, nächster Schritt, Fallen |

## 9. Skripte

| Skript | Zweck |
|---|---|
| `scripts/setup <vorname>` | einmal pro Rechner: Branch, main-Worktree, Paket + PDFs, Oberordner-CLAUDE.md |
| `scripts/session-start` | STATUS (origin/main) + neueste LOG-Einträge aller Branches + Git-Zustand |
| `scripts/sync` | holen (rebase, bei lokalen Merge-Commits merge), main mitmergen, Secret-Scan, pushen |
| `scripts/log [--commit b@h] "[typ] titel" "detail" …` | Eintrag an docs/LOG.md anhängen (Datum, Autor, Rechner, Stand bzw. gemessener Stand) |
| `scripts/claim add/done/list` | Claims in docs/STATUS.md auf main pflegen, sofort gepusht |
| `scripts/main-wt` | Pfad des main-Checkouts für geteilte Dateien |
| `scripts/pull-first` | vor Läufen: Teamstand holen, Commit melden, Exit 1 wenn der Lauf nicht zählt |
| `scripts/tag-best <wert>` | guten, gepushten Stand als `best-<branch>-<wert>` taggen |
| `scripts/stop-check` | warnt bei ungepushten Commits / uncommitteten Änderungen (auch Stop-Hook) |
| `scripts/secret-scan [dateien]` | Schlüsselsuche in ausgehenden Commits oder Dateien |

Alle Skripte sind Bash für macOS und Linux und stoppen mit einer klaren Meldung, statt zu raten.
