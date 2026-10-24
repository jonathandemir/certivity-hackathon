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
| certreq/, tests/ | Pipeline und Tests (Dateigrenzen je Person: docs/PLAN.md „Aufteilung") |

## 1. Sessionstart (immer, in dieser Reihenfolge)

1. `scripts/sync`: holt den aktuellen Stand von main und pusht deine Commits.
2. STATUS und LOG lesen. Der SessionStart-Hook gibt beides aus (`scripts/session-start`). Fehlt die Ausgabe im
   Kontext (z. B. Session im Oberordner gestartet), führe `scripts/session-start` selbst aus.
3. Aufgabe gegen die Claims prüfen. **Überschneidet sie sich mit einem fremden Claim (gleiche Dateien oder gleiches
   Thema), sag es dem Menschen, bevor du anfängst.**
4. Vor jeder Idee: docs/LEARNINGS.md „Verworfen" und experiments/LEDGER.md prüfen. Ist sie schon widerlegt, sag
   es mit Beleg, statt sie erneut zu bauen.

## 2. Arbeitsschleife

1. **Claim setzen:** `scripts/claim add "Was" "Dateien/Ordner"` (pusht sofort auf main).
2. **Kleiner Schritt** (deutlich unter 30 Minuten).
3. **Tests grün:** `.venv/bin/python -m pytest`; erzeugt der Schritt eine Abgabedatei, zusätzlich
   `.venv/bin/python -m certreq eval <datei>`. Rot wird nicht gepusht: `scripts/sync` führt die Tests vor jedem
   Push mit Code-Änderungen selbst aus und bricht bei Rot ab.
4. **Loggen:** `scripts/log "[change] titel" "was und warum" "wie geprüft"`.
5. **Commit:** `git status` lesen, dann gezielt `git add <deine dateien> docs/LOG.md` und `git commit`.
   Code und Logeintrag im selben Commit.
6. **`scripts/sync`.**

Mindestens alle 30 Minuten und immer vor dem Aufhören pushen. Fertig mit einer Aufgabe:
`scripts/claim done "Was"`, dauerhafte Erkenntnisse mit Beleg in docs/LEARNINGS.md.

## 3. Git-Sicherheit (nie verhandelbar)

- Nie fremde Dateien überschreiben: nur Dateien aus deinem Claim oder solche, die du selbst angelegt hast.
- Nie `git push --force` / `--force-with-lease`, nie `git reset --hard`, `git checkout -- .`, `git restore .`,
  `git clean -f`, `git stash drop` über Arbeit, die nicht nachweislich deine eigene ist.
- **Vor jedem `git add`: `git status`.** Nie blind `git add -A` / `git add .`.
- Konflikt: nur eigene Dateien selbst lösen; bei fremden Dateien den Menschen fragen. docs/LOG.md: beide Einträge
  behalten. Abbrechen ist immer sicher (`git rebase --abort` / `git merge --abort`).
- Nie fremde Arbeit „aufräumen": rote Tests oder kaputter Code eines anderen → dem Menschen sagen bzw. `[blocker]` loggen.

## 4. Alle arbeiten auf main

- **Alle arbeiten direkt auf main** (entschieden 2026-10-24, docs/STATUS.md). Code, Doku, Ergebnisse und LOG liegen
  am selben Ort; jeder sieht den Stand der anderen nach dem nächsten `scripts/sync`.
- **Konflikte vermeiden durch Dateigrenzen:** Jede Person ändert ihre Dateien (docs/PLAN.md „Aufteilung").
  Gemeinsame Dateien (`certreq/__main__.py`, `requirements.txt`, `tests/conftest.py`, docs/) nur mit Claim und klein.
  Agenten derselben Person teilen sich deren Claims.
- **Kein kaputter Code auf main:** `scripts/sync` lässt vor jedem Push mit Code-Änderungen die Tests laufen und pusht
  bei Rot nicht. Nie Tests abschalten oder löschen, um grün zu werden.
- **Neue Ansätze hinter einen Schalter** (z. B. `--select llm`, Umgebungsvariable oder Parameter), der Standard bleibt
  der gemessene Bestwert. Den Standard umstellen erst, wenn die Messung besser ist (LEDGER-Zeile). So bleibt main
  jederzeit lauffähig und jede Änderung einzeln messbar, obwohl alle gleichzeitig pushen.
- **Eine Session = ein eigener Checkout.** Laufen mehrere Agenten auf demselben Rechner, bekommt jeder einen eigenen
  Klon (z. B. `git clone <repo-url> ../certivity-<kürzel>`, dann `scripts/setup`; PDFs ohne Download per
  `cp -cR ../certivity/vendor/industrial-ai-hackathon vendor/` auf macOS). Zwei Agenten im selben Ordner blockieren
  sich: `scripts/sync` braucht einen sauberen Stand, und Tests messen den halbfertigen Code des anderen mit.
  Schlüssel-Dateien (`.env.local`) per Symlink teilen, nie kopieren oder committen.
- **Branches nur ausnahmsweise** für ein riskantes Experiment, das länger als eine Stunde nicht lauffähig ist.
  Dann kurzlebig, `scripts/sync` funktioniert dort auch (merged main konfliktfrei mit); geteilte Dateien weiter auf
  main ändern (`scripts/main-wt` gibt den Pfad eines main-Checkouts). Danach zügig nach main mergen und löschen.
- **Gute Stände sichern:** `scripts/tag-best <wert>` (Tag `best-main-<wert>`); Sonntag läuft der Held-out auf einem getaggten Stand (docs/PLAN.md „Sonntagsablauf“); einen Code-Freeze für alle gibt es nicht.

## 5. Ergebnisse, Läufe, Experimente

- **Vor jedem teuren oder zählenden Lauf: `scripts/pull-first`** (holt den Teamstand; Exit 0 = Lauf zählt).
  Sonst misst man veralteten Code.
- Jedes Ergebnis (Messung, Run, Benchmark, Upload-Score) nennt seinen Commit als `<branch>@<kurzhash>`: gepusht,
  sauberes Arbeitsverzeichnis. **Hashes aus git lesen (`git rev-parse --short HEAD`, Ausgabe von pull-first),
  nie erfinden oder schätzen.**
- Ergebnis eintragen: `[run]`-Logeintrag + Zeile in experiments/LEDGER.md + Beleg unter experiments/runs/<ID>/
  (`.venv/bin/python -m certreq eval <abgabe> --record <ID>` legt den Beleg ab). Lief die Messung auf einem anderen
  Commit als deinem aktuellen Stand, gib ihn an: `scripts/log --commit main@<hash> "[run] ..."` (das Skript prüft,
  dass der Commit existiert und gepusht ist). Neue Bestmarke: zusätzlich Scoreboard in docs/STATUS.md und
  `scripts/tag-best <wert>` (Tag `best-main-<wert>`, damit man jederzeit zurück kann).
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
| `scripts/setup` | einmal pro Rechner: auf main stellen, Paket + PDFs, .venv, Oberordner-CLAUDE.md |
| `scripts/session-start` | STATUS (origin/main) + neueste LOG-Einträge aller Branches + Git-Zustand |
| `scripts/sync` | holen (rebase, bei lokalen Merge-Commits merge), Secret-Scan, Tests bei Code-Änderungen, pushen |
| `scripts/log [--commit b@h] "[typ] titel" "detail" …` | Eintrag an docs/LOG.md anhängen (Datum, Autor, Rechner, Stand bzw. gemessener Stand) |
| `scripts/claim add/done/list` | Claims in docs/STATUS.md pflegen, sofort gepusht |
| `scripts/main-wt` | nur auf Experiment-Branches: Pfad eines main-Checkouts für geteilte Dateien |
| `scripts/pull-first` | vor Läufen: Teamstand holen, Commit melden, Exit 1 wenn der Lauf nicht zählt |
| `scripts/tag-best <wert>` | guten, gepushten Stand als `best-<branch>-<wert>` taggen |
| `scripts/stop-check` | warnt bei ungepushten Commits / uncommitteten Änderungen (auch Stop-Hook) |
| `scripts/secret-scan [dateien]` | Schlüsselsuche in ausgehenden Commits oder Dateien |
| `scripts/export-snapshot <ordner>` | R4: Abgabe-Kopie ohne Git-Historie (ein Commit), prüft Schlüssel und Paketdaten; pusht nichts |
| `scripts/selftest` | testet alle Skripte in einer Sandbox (3 simulierte Rechner); nach jeder Änderung an scripts/ ausführen |

Alle Skripte sind Bash für macOS und Linux und stoppen mit einer klaren Meldung, statt zu raten.
