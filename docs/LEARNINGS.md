# LEARNINGS: was funktioniert und was nicht, jeweils mit Beleg

Nur auf main ändern. Ein Eintrag = Erkenntnis + Beleg (Commit `<branch>@<hash>`, Ledger-ID, Datei, Messung oder
Quelle) + Konsequenz. Ohne Beleg ist es eine Vermutung und gehört nicht hierher. Neueste oben.

## Funktioniert / gilt

- **2026-10-24 · PDF-Download scheitert mit python.org-Python auf macOS, klappt mit dem certifi-Bündel.**
  Beleg: Jonathans Rechner, Python 3.14 aus /Library/Frameworks: `fetch_regulations.py` → 0 von 94,
  `[SSL: CERTIFICATE_VERIFY_FAILED]`; mit `SSL_CERT_FILE="$(python3 -m certifi)"` → 94 von 94, Checksummen geprüft.
  Konsequenz: `scripts/setup` versucht es automatisch erneut mit certifi (nur für diesen Aufruf, keine Systemänderung).
- **2026-10-24 · `score_local.py` zeigt F1, nicht F2.** Das Ranking nutzt F2 (Recall doppelt gewichtet).
  Beleg: Ausgabe von `python3 tools/score_local.py cases/dev-rear-lamp/expected.json` (Spalten precision, recall, F1).
  Konsequenz: F2 = 5·P·R/(4·P+R) selbst berechnen, im Scoreboard F2 eintragen.
- **2026-10-24 · `validate.py` braucht `jsonschema`, das in Jonathans Python 3.14.2 fehlt.**
  Beleg: `python3 -c "import jsonschema"` → `ModuleNotFoundError`. Konsequenz: `python3 -m pip install --user jsonschema`
  auf jedem Rechner; `scripts/setup` warnt, wenn es fehlt.
- **2026-10-24 · Paralleles Anhängen an docs/LOG.md von zwei Rechnern erzeugt weder bei rebase noch bei merge
  einen Konflikt** (`merge=union` in .gitattributes). Beleg: Testlauf der Skripte mit zwei Klonen gegen ein
  gemeinsames origin (Abschnitt „Tests" im `[decision]`-Eintrag vom 2026-10-24 in docs/LOG.md).

## Verworfen, nicht erneut versuchen

- **Teilnehmerpaket / PDFs / expected.json ins Repo committen.** Beleg: `vendor/industrial-ai-hackathon/LICENSE-DATA.md`
  („may not redistribute"); das Repo wird zur Abgabe geteilt. Stattdessen `vendor/` (gitignored) per `scripts/setup`.
- **Eigene Regulierungsdatenbank oder Crawler bauen.** Beleg: Brief §05 „Not needed"; UNECE-Seiten sind laut
  Brief §06 nicht per Skript ladbar, die PDFs liefert Certivity.
- **docs/LOG.md ausschließlich auf main führen.** Dann können Code (persönlicher Branch) und Logeintrag nie im
  selben Commit landen. Stattdessen: Einträge im eigenen Branch, `merge=union`, `scripts/session-start` liest alle Branches.
