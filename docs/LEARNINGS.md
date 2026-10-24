# LEARNINGS: was funktioniert und was nicht, jeweils mit Beleg

Nur auf main ändern. Ein Eintrag = Erkenntnis + Beleg (Commit `<branch>@<hash>`, Ledger-ID, Datei, Messung oder
Quelle) + Konsequenz. Ohne Beleg ist es eine Vermutung und gehört nicht hierher. Neueste oben.

## Funktioniert / gilt

- **2026-10-24 · Zwei Agenten im selben Checkout blockieren sich.** Beleg: Eine zweite Session in
  `~/projects/certivity` arbeitete uncommittet an `certreq/pdf.py`/`extract.py`, während diese Session pushen wollte;
  `scripts/sync` verweigert zu Recht bei fremden uncommitteten Dateien. Konsequenz: eine Session = ein Klon
  (AGENTS.md §4); diese Session arbeitet seitdem in `~/projects/certivity-a`.
- **2026-10-24 · `reasoning_effort`-Werte hängen vom Modell ab.** Beleg: HTTP 400 im Live-Test: gpt-5.4-mini kennt
  none/low/medium/high/xhigh (kein „minimal"), gpt-6.1-sol nur low/medium/high/xhigh. gpt-6.1-sol: ~3 s pro kurzem Aufruf
  (gpt-5.4-mini: <1 s). Konsequenz: `effort` nur mit gültigem Wert setzen; Massenaufrufe über `ask_many` parallelisieren.
- **2026-10-24 · Mit den richtigen Regelungen findet schon die naive shall-Extraktion alle 53 Gold-Seiten.**
  Beleg: E002 (jonathan@29c0d0b, experiments/runs/E002): Seiten-Recall 1.000, Precision 0.206, 1214 statt 190
  Anforderungen. Konsequenz: Auswahl (AP2) ist der größte Hebel; danach Relevanzfilter/Zerlegung (AP4) für Precision.
- **2026-10-24 · Titel-Wortüberlappung reicht für die Regelungsauswahl nicht.** Beleg: E001 (jonathan@29c0d0b): 21
  Regelungen gewählt, nur 3 von 4 richtig; UN R10 (EMV, 32 von 190 Anforderungen) fehlt, weil kein Titelwort in der
  Spezifikation vorkommt. Konsequenz: AP2 muss aus Bauteilen/Eigenschaften schließen (Elektronik → EMV), nicht aus Wörtern.
- **2026-10-24 · Absatz-Parser: Anhang-Überschriften nur in Reihenfolge akzeptieren.** Beleg: Tabellenzelle
  „Annex 10 (values in" (UN R150, S. 5) labelte vorher alle folgenden Haupttext-Absätze als Anhang 10 (90/121
  Referenz-Absätze gefunden); mit Reihenfolgeregel 121/121 (Test `test_paragraph_labels_match_reference`).
- **2026-10-24 · PDF-Download scheitert mit python.org-Python auf macOS, klappt mit dem certifi-Bündel.**
  Beleg: Jonathans Rechner, Python 3.14 aus /Library/Frameworks: `fetch_regulations.py` → 0 von 94,
  `[SSL: CERTIFICATE_VERIFY_FAILED]`; mit `SSL_CERT_FILE="$(python3 -m certifi)"` → 94 von 94, Checksummen geprüft.
  Konsequenz: `scripts/setup` versucht es automatisch erneut mit certifi (nur für diesen Aufruf, keine Systemänderung).
- **2026-10-24 · `score_local.py` zeigt F1, nicht F2.** Das Ranking nutzt F2 (Recall doppelt gewichtet).
  Beleg: Ausgabe von `python3 tools/score_local.py cases/dev-rear-lamp/expected.json` (Spalten precision, recall, F1).
  Konsequenz: F2 = 5·P·R/(4·P+R) selbst berechnen, im Scoreboard F2 eintragen.
- **2026-10-24 · `validate.py` braucht `jsonschema`, das in Jonathans Python 3.14.2 fehlt.**
  Beleg: `python3 -c "import jsonschema"` → `ModuleNotFoundError`. Konsequenz: steht in requirements.txt (.venv);
  für `python3 tools/validate.py` außerhalb der venv `python3 -m pip install --user jsonschema` (bei Jonathan erledigt).
- **2026-10-24 · Paralleles Anhängen an docs/LOG.md von zwei Rechnern erzeugt weder bei rebase noch bei merge
  einen Konflikt** (`merge=union` in .gitattributes). Beleg: Testlauf der Skripte mit zwei Klonen gegen ein
  gemeinsames origin (Abschnitt „Tests" im `[decision]`-Eintrag vom 2026-10-24 in docs/LOG.md).

## Verworfen, nicht erneut versuchen

- **Teilnehmerpaket / PDFs / expected.json ins Repo committen.** Beleg: `vendor/industrial-ai-hackathon/LICENSE-DATA.md`
  („may not redistribute"); das Repo wird zur Abgabe geteilt. Stattdessen `vendor/` (gitignored) per `scripts/setup`.
- **Eigene Regulierungsdatenbank oder Crawler bauen.** Beleg: Brief §05 „Not needed"; UNECE-Seiten sind laut
  Brief §06 nicht per Skript ladbar, die PDFs liefert Certivity.
- **Persönliche Branches pro Person (ursprünglicher Plan).** Beleg: Schon das erste Paket (AP1) musste vorzeitig
  nach main gemergt werden, damit die anderen darauf aufbauen können (Entscheidung 2026-10-24); dazu kamen
  main-Worktree für Doku und eine Sonderregel für LOG.md. Bei drei Leuten mit getrennten Dateien und gegenseitigen
  Abhängigkeiten kostet das mehr, als es schützt. Stattdessen: alle auf main, Tests in `scripts/sync`, Schalter für neue Ansätze.
