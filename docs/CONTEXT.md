# CONTEXT: Fakten und Regeln des Projekts

Aufgabe dieser Datei: alles, was jede Session über das Projekt wissen muss, aus den Quellen zusammengefasst.
Ändert sich eine Regel oder ein Fakt, wird diese Datei auf main aktualisiert (mit Quelle). Meinungen und
Messergebnisse gehören nicht hierher, sondern in LEARNINGS.md bzw. experiments/LEDGER.md.

Quellen: Challenge-Brief `certivity-challenge-brief.pdf` (3 Seiten, liegt bei Jonathan, nicht im Repo) und das
Teilnehmerpaket https://github.com/Certivity/industrial-ai-hackathon (lokal: `vendor/industrial-ai-hackathon/`,
per `scripts/setup`). Stand: 2026-10-24, Paket-Commit `2104a8e`.

## 1. Das Projekt in einem Satz

Für den Certivity-Track des Industrial Agents Hackathon (München, 24.–25.10.2026) bauen wir einen Agenten, der aus
einer technischen Spezifikation und/oder Explosionszeichnung eines Fahrzeugbauteils die Engineering-Anforderungen
ableitet, die es nach UN-Regelungen (UNECE) erfüllen muss, jeweils mit Regelung, Version und Seite.

Team: Jonathan Demir (weitere Mitglieder tragen sich in docs/STATUS.md unter „Team" ein). Plattform: max. 6 Personen.

## 2. Termine (alle Zeiten Europe/Berlin)

| Wann | Was |
|---|---|
| Sa 24.10. | Kickoff; Paket, PDFs und Worked Examples sind verfügbar |
| **Nacht Sa→So** | **Zeitumstellung: So 03:00 MESZ → 02:00 MEZ.** Alle Sonntagszeiten sind MEZ. Wecker und Nachtläufe prüfen |
| So 25.10. 08:00 | Held-out-Fall wird veröffentlicht (Frontstoßfänger `heldout-front-bumper` + Sub-Goal-Paar `subgoal-heldout`) |
| So 25.10. 13:00 | **Upload-Schluss** auf der Certivity-Plattform |
| So 25.10. 15:00 | Finalisten pitchen (Lösung, Demo, Beleg). Certivity wählt vorher ~4 Finalisten nach Score + Demo |

Interne Freezes und Zeitplan: docs/PLAN.md.

Widerspruch in den Quellen: Laut Brief kommt der Held-out-Fall als „second zip, link announced on screen", laut
Paket-README per `git pull` im Paket-Repo. Sonntag 08:00 beides prüfen: `git -C vendor/industrial-ai-hackathon pull`
und Ankündigung vor Ort. Danach `python tools/fetch_regulations.py` im Paket erneut ausführen.

## 3. Aufgabe

**Hauptziel (Pflicht).** Eingabe: Spezifikation (Markdown) und/oder Explosionszeichnung (PNG) eines Bauteils.
Ausgabe: Liste von Anforderungen. Jede Anforderung = genau eine Engineering-Pflicht, die ein Ingenieur umsetzen
kann, mit Zitat: UN-Regelung, Version, Seite (Absatz dringend empfohlen). Testfall pro Anforderung optional.

**Sub-Goal (optional, 15 % der Jury-Wertung).** Eingabe: Anforderungen aus Version A einer Regelung + PDF von
Version B. Ausgabe: welche Anforderungen sich ändern (`modified` / `removed` / `added`) und was in der Regelung
die Änderung verursacht.

**Nicht nötig:** eigene Regulierungsdatenbank oder Crawler (Brief §05).
**Hinweise aus dem Brief:** erst die zutreffenden Regelungen eingrenzen, dann nur diese lesen (der Index enthält
mehr Regelungen als zutreffen); Explosionszeichnung mit einem Vision-Modell lesen (Teile + Funktionen).

## 4. Pflichtelemente (Brief §05)

| # | Element | Geprüft durch |
|---|---|---|
| R1 | Hauptziel-JSON besteht `validate.py`, hochgeladen für `heldout-front-bumper` | Plattform |
| R2 | Jede Anforderung zitiert eine Regelung aus `regulations/index.json` mit `version_label` und Seite | Plattform-Validierung |
| R3 | Demo läuft von der Eingabe (Spec oder Zeichnung) bis zu den Anforderungen **ohne manuelle Schritte** | Demo im Pitch |
| R4 | Basisfragen, GitHub-Repo und Demo auf der Plattform der Veranstalter eingereicht | Veranstalter |

## 5. Bewertung

| Kriterium | Gewicht | Worauf geachtet wird |
|---|---|---|
| Score auf dem Held-out-Fall | 40 % | Recall und Precision gegen den Golden Dataset auf Ebene Regelungen, Seiten, Anforderungen. **Ranking: F2** (Recall doppelt gewichtet), Recall als Tie-Break |
| Demo und UI | 20 % | Ablauf end-to-end, für Ingenieure nachvollziehbar, jede Anforderung verlinkt auf ihre Quellseite |
| Sub-Goal | 15 % | Recall der als geändert markierten Anforderungen, Richtigkeit der genannten Änderung |
| Potential Impact | 15 % | Würde Certivity es weiterführen, testen, einsetzen |
| Pitch | 10 % | |

Stark: nur zutreffende Regelungen, richtige Version und Seite, eine Pflicht pro Anforderung, im Pitch zeigen, wo die
Lösung schwach ist und wie das gemessen wurde. Schwach: viele Regelungen „sicherheitshalber" (Precision fällt),
mehrere Pflichten in einer Anforderung (Recall fällt), falsche Version, keine laufende Demo.

**Bewertungsdetails (Paket-README „How it is judged"):**
- *Regelungen:* richtige UN-Regelungen und nur diese.
- *Seiten:* richtige Seite der richtigen Version. **Seite ODER Absatz genügt**: immer `source.paragraph` mitgeben,
  dann kostet eine um eins verschobene Seite nichts. Absatzlabels werden normalisiert verglichen
  (`Annex 8 2.1` = `annex 8, 2.1.`), aber `5.4.2.3` ≠ `5.4.23`.
- *Anforderungen:* 1:1-Matching per Sprachmodell auf gleiche Pflicht (gleicher Geltungsbereich, Bedingung, Grenzwert).
  Precision = Anteil eigener Anforderungen mit Match, Recall = Anteil gefundener erwarteter Anforderungen.
- Recall zählt etwas mehr als Precision, aber Auffüllen „zur Sicherheit" kostet Precision.

## 6. Abgabe

1. Certivity-Plattform https://hackathon.certivity.io/ mit Invite-Code (vor Ort): Teamname, 1–6 Mitglieder (Name,
   E-Mail), Passwort ≥ 10 Zeichen. **Passwort nie ins Repo.** Die danach angezeigte Team-ID kommt in jede Datei (`team_id`).
2. Eine JSON-Datei pro Challenge und Fall hochladen. Fehler werden mit JSON-Pfad gezeigt.
3. **Limit: 5 valide Uploads pro Stunde und Challenge** (gilt für den Team-Account, also alle zusammen; daher Uploads per Claim absprechen). Ungültige zählen nicht.
4. Dev-Fall: der beste Upload zählt für das Leaderboard. **Held-out: der LETZTE valide Upload zählt, nicht der beste.**
   Also nie zum Schluss eine schlechtere Datei hochladen; jede hochgeladene Datei und ihren Plattform-Score
   in `experiments/runs/` sichern, damit die beste zuletzt erneut hochgeladen werden kann.
5. GitHub-Repo, Demo und Basisfragen auf der Plattform der Veranstalter einreichen (R4).

## 7. Daten und Lizenz

- `regulations/index.json`: 56 Regelungen (UN R3 … R175, UN GTR 9). Jede hat eine `base`-Version, die meisten
  zusätzlich `latest`. **Hauptziel zitiert immer die `base`-Version** (`version_label` aus dem Index); eine Seite der
  `latest`-Version zählt als andere, also falsche Seite. Sub-Goal: `latest` ist das, was sich geändert hat.
- PDFs: `python tools/fetch_regulations.py` → `regulations/pdf/<regelung>/<base|latest>/*.pdf` (~220 MB, Checksummen
  werden geprüft). **Links laufen nach dem Event ab.** macOS + python.org-Python: bei `CERTIFICATE_VERIFY_FAILED`
  siehe Paket-README §1 (`Install Certificates.command` oder `SSL_CERT_FILE` auf certifi).
- **Lizenz (LICENSE-DATA.md):** `cases/`, `subgoal/`, `index.json` und die Held-out-Eingaben nur für diesen Hackathon,
  keine Weitergabe. Deshalb liegt das Paket gitignored unter `vendor/` und wird **nie ins Repo kopiert** (das Repo
  wird zur Abgabe geteilt). Tools und Schemas sind MIT.

## 8. Formate (Kurzfassung, maßgeblich: `vendor/industrial-ai-hackathon/schemas/`)

Hauptziel:
```json
{"team_id": "team-07", "case_id": "dev-rear-lamp",
 "requirements": [{"id": "R-001", "text": "The rear lamp shall ...",
   "source": {"regulation": "UN R48", "version": "9.3.0", "page": 6, "paragraph": "6.2"},
   "test_case": "optional"}]}
```
`id` eindeutig; `text` nicht leer, ≤ 2000 Zeichen; `regulation` exakt wie im Index (z. B. `"UN R148"`);
`version` = `version_label`; `page` ≥ 1 im PDF dieser Version; max. 5000 Anforderungen, 5 MB.
`case_id`: `dev-rear-lamp`, Held-out = Ordnername unter `cases/`.

Sub-Goal:
```json
{"team_id": "team-07", "case_id": "subgoal-dev",
 "changes": [{"requirement_id": "R-014", "change": "modified", "new_text": "...",
   "reason": "Paragraph 5.3 now sets ...", "source": {"page": 9, "paragraph": "5.3"}}]}
```
`modified`/`removed`: `requirement_id` aus `requirements_old.json`; `added`: `requirement_id: null`.
`new_text` Pflicht bei `modified` und `added`; `reason` immer Pflicht.

## 9. Werkzeuge des Pakets

```bash
cd vendor/industrial-ai-hackathon
python3 -m pip install --user jsonschema            # einzige Abhängigkeit von validate.py
python3 tools/validate.py <datei>.json [--strict]
python3 tools/validate.py <changes>.json --requirements-old subgoal/dev/requirements_old.json
python3 tools/score_local.py <datei>.json [--expected cases/dev-rear-lamp/expected.json] [--json]
```
`score_local.py` misst nur Regelungs- und Seitenebene, offline, und zeigt **F1, nicht F2**. F2 selbst rechnen:
F2 = 5·P·R / (4·P + R). Die Anforderungsebene (Hauptscore) gibt es nur auf der Plattform. Die Plattform wertet
Seiten über den vollen Seitenbereich eines erwarteten Absatzes, lokale Zahlen können leicht abweichen.

## 10. Worked Examples (Fakten zum Kalibrieren, gezählt am 2026-10-24 aus dem Paket)

**dev-rear-lamp** (Heckleuchte, Kategorie M1; Teile: Schlusslicht, Bremslicht, Rückfahrscheinwerfer,
Lichtscheibe, Rückstrahler; LED auf Platine): 190 erwartete Anforderungen, 4 Regelungen, 53 verschiedene Seiten,
alle auf der `base`-Version:

| Regelung | Version | Anforderungen |
|---|---|---|
| UN R148 (Light-Signalling Devices) | 1.6.0 | 63 |
| UN R48 (Installation of lighting) | 9.3.0 | 56 |
| UN R150 (Retro-Reflective Devices) | 1.2.1 | 39 |
| UN R10 (EMV) | 7.2.0 | 32 |

Die Zeichnung im Brief nennt nur R148, R48, R150. **R10 (EMV) ist trotzdem erwartet** (17 % der Anforderungen),
vermutlich wegen der Elektronik (LED-Module). Ältere Leuchten-Regelungen aus dem Index (R7, R6, R23, R38) sind
**nicht** erwartet. Anforderungstexte sind nahezu wörtliche „shall"-Sätze aus der Regelung, ein Absatz je Anforderung.

**subgoal-dev**: UN R175 (ACPE), `requirements_old.json` mit 94 Anforderungen (Quelle: Regelung, Seite, Absatz,
keine Version); erwartet 24 Änderungen: 17 `added`, 6 `modified`, 1 `removed`; `source` meist mit Seite + Absatz
der neuen Version, `reason` nennt den Absatz und was sich geändert hat.

## 11. Arbeitsregeln

Wie wir zusammenarbeiten (alle auf main, Claims, Log, Sync, Messungen): AGENTS.md. Diese Datei ist nur der Projektinhalt.
