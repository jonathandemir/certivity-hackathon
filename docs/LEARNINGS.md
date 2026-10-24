# LEARNINGS: was funktioniert und was nicht, jeweils mit Beleg

Nur auf main ändern. Ein Eintrag = Erkenntnis + Beleg (Commit `<branch>@<hash>`, Ledger-ID, Datei, Messung oder
Quelle) + Konsequenz. Ohne Beleg ist es eine Vermutung und gehört nicht hierher. Neueste oben.

## Funktioniert / gilt

- **2026-10-24 · Die LLM-Extraktion muss den Geltungsbereich wörtlich aus der Regelung übernehmen.** Beleg: E013 →
  E015 (Gold-Regelungen, Richter strict): Prompt v1 („name the subject explicitly" + Bauteil-Spec) schrieb „the rear
  lamp shall …", wo die Regelung „lamps" / „all light-signalling devices" sagt, und zerlegte „clearly legible and
  indelible" in zwei; Anforderungs-F2 0.356. Prompt v2 (Geltungsbereich wörtlich, Bauteil entscheidet nur ob ein Absatz
  gilt, trennen nur an (a)(b)(c)/Sätzen/unabhängigen Grenzwerten): 0.637; mit B0-Auswahl E012 0.290 → E014 0.491.
  Konsequenz: Umformulieren ja (shall-Satz, Subjekt statt „it"), Verengen nie. Gilt für jedes Bauteil, auch den Stoßfänger.
- **2026-10-24 · Ein LLM je Absatz schlägt alle Regelfilter um Längen.** Beleg: E008 vs E006 (gleiche Kandidaten
  `--filters all`): Seiten-F2 0.348→0.714, Regelungs-F2 0.405→0.556 (in unpassenden Regelungen findet es nichts),
  Anforderungen (Richter strict) E011-a 0.098 → E012 0.290. Konsequenz: Regelfilter bleiben als billige Vorauswahl
  (2614 statt 3642 Kandidaten), die Entscheidung trifft das LLM.

- **2026-10-24 · Der lokale Richter (AP10) ist im strikten Modus verlässlich.** Beleg: AP10-K (main@66d51fc,
  experiments/runs/AP10-kalibrierung/): Selbsttest 190/190; Gegenprobe ohne identisches Gegenstück 0 echte Fehlurteile
  (strict) bzw. 5,3 % falscher Recall (lenient). Konsequenz: `eval --judge strict` als Messgröße für AP4/AP2; Eichung
  gegen den Plattformwert des E001-Uploads steht aus.
- **2026-10-24 · Seiten-F2 und Anforderungs-F2 können gegenläufig sein.** Beleg: E011-a vs E010-a: modal+split senkt
  Seiten-F2 (0.348→0.339), hebt aber Anforderungs-F2 (0.084→0.098, Recall 52→73). Konsequenz: Entscheidungen über die
  Extraktion nach der Anforderungsebene treffen (Hauptscore), Seiten nur als Nebenmaß.
- **2026-10-24 · Auf der Anforderungsebene ist Precision der Engpass.** Beleg: E011-a P 0.025 bei 2966 Anforderungen
  (Referenz 190); selbst perfekter Recall ergäbe F2 ≈ 0.11. Konsequenz: AP4 muss die Menge um Faktor ~10 senken
  (Relevanz je Absatz per LLM, Zerlegung nur relevanter Absätze).
- **2026-10-24 · Relevanzfilter entlang der Gliederung hebt die Precision ohne Recall-Verlust.** Beleg: E006
  (main@3e979ed, experiments/runs/E006/filters.txt): `--filters all` Seiten-F2 0.272→0.348 (B0-Auswahl) bzw.
  0.565→0.773 mit Gold-Regelungen, Seiten-Recall unverändert, kein Gold-Absatz von B0 geht verloren (Test
  `test_filters_keep_every_gold_paragraph_of_b0`). Jede Regel einzeln besser: admin, cop, parts, esa. Konsequenz:
  Kandidat für den Standard, sobald der E001-Upload die Anforderungsebene geeicht hat. **Für den Stoßfänger
  plausibel?** admin/cop/esa sind Struktur der UN-Regelungen, nicht leuchtenspezifisch; parts hängt an den Teilenamen
  der Spec (Lagewörter front/rear müssen stimmen) und greift ohne Treffer nicht.
- **2026-10-24 · Conformity of production enthält konstruktionsrelevante Toleranzen.** Beleg: Gold dev R148 6.1.3 und
  R150 Annex 2 1.2 („shall not deviate unfavourably by more than 20 per cent"); ohne Ausnahme verlor `cop` 2 Gold-Seiten
  (Vormessung vor E004, LOG 14:25). Konsequenz: `cop` behält Absätze mit Abweichung + Prozentwert.
- **2026-10-24 · 35 von 190 Gold-Anforderungen stammen aus Absätzen ohne „shall".** Beleg: Abgleich expected.json mit
  parse_pdf (must, „is not permitted", „may … only", Listen wie R48 6.10.2 „Number Two"); die Referenz formuliert sie
  als shall-Sätze. `--extract modal` holt sie (Absatz-Recall 0.798→0.975 mit Gold-Regelungen, E007/options.txt), kostet
  aber Seiten-F2 (0.773→0.759). Konsequenz: Entscheidung erst mit Anforderungs-Messung (AP10 oder Plattform).
- **2026-10-24 · Gold zerlegt 119 Absätze in 190 Anforderungen; (a)(b)(c)-Aufzählungen lassen sich regelbasiert
  zerlegen.** Beleg: E007/options.txt: `--extract split` hebt die Obergrenze der Anforderungsebene (je Gold-Absatz
  min(unsere, Gold-Anzahl), kein Plattformwert) von 0.359 auf 0.384, mit modal 0.430; Seiten unverändert. Nur 8 der 35
  mehrfach zerlegten Gold-Absätze sind Aufzählungen, der Rest ist Bedingung/Grenzwert im Fließtext (R10 6.9.1: 10
  Anforderungen) → braucht das LLM.
- **2026-10-24 · Überschriften sind in den PDFs typografisch nicht abgesetzt.** Beleg: `page.get_text("dict")` auf R48
  S. 50, R148 S. 9, R10 S. 20: Überschriften und Text gleich (TimesNewRomanPSMT 10.5, flags 4). Konsequenz: pdf.py
  erkennt Überschriften am Text (kurz, ohne Verb/Doppelpunkt, danach neuer Satz); 7967 von 27231 Absätzen mit Titel.

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

- **Anforderungen satzweise zerlegen (ein Pflichtsatz = eine Anforderung).** Beleg: Vormessung auf dem Arbeitsstand
  vor main@006d141 (LOG-Eintrag „[change] AP4: Extraktionsoptionen --extract"): Obergrenze Anforderungsebene 0.411
  statt 0.407 ohne Zerlegung, geschätzt 0.437 mit Aufzählungs-Zerlegung (umgesetzt: 0.430, E007); Precision fällt 0.174→0.143, weil auch Absätze ohne Gold-Zerlegung zerfallen. Stattdessen
  `--extract split` (nur (a)(b)(c)) und für Bedingungen/Grenzwerte im Fließtext das LLM.
- **Teilnehmerpaket / PDFs / expected.json ins Repo committen.** Beleg: `vendor/industrial-ai-hackathon/LICENSE-DATA.md`
  („may not redistribute"); das Repo wird zur Abgabe geteilt. Stattdessen `vendor/` (gitignored) per `scripts/setup`.
- **Eigene Regulierungsdatenbank oder Crawler bauen.** Beleg: Brief §05 „Not needed"; UNECE-Seiten sind laut
  Brief §06 nicht per Skript ladbar, die PDFs liefert Certivity.
- **Persönliche Branches pro Person (ursprünglicher Plan).** Beleg: Schon das erste Paket (AP1) musste vorzeitig
  nach main gemergt werden, damit die anderen darauf aufbauen können (Entscheidung 2026-10-24); dazu kamen
  main-Worktree für Doku und eine Sonderregel für LOG.md. Bei drei Leuten mit getrennten Dateien und gegenseitigen
  Abhängigkeiten kostet das mehr, als es schützt. Stattdessen: alle auf main, Tests in `scripts/sync`, Schalter für neue Ansätze.
