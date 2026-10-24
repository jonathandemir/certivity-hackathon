# LEARNINGS: was funktioniert und was nicht, jeweils mit Beleg

Nur auf main ändern. Ein Eintrag = Erkenntnis + Beleg (Commit `<branch>@<hash>`, Ledger-ID, Datei, Messung oder
Quelle) + Konsequenz. Ohne Beleg ist es eine Vermutung und gehört nicht hierher. Neueste oben.

## Funktioniert / gilt

- **2026-10-24 · Prompt-Regeln modes und tables tragen den Gewinn der Zusatzregeln, in beiden Modellen.** Beleg: Bündel (lists, tables, exempt, tests, modes) gpt E021-hs→E022-hs lenient 0.704→0.743, Claude E023-hs-c→E024-hs-c strict 0.697→0.721; je eine weggelassen (E025–E029-hs-c, main@8c201e1): ohne modes 0.695, ohne tables 0.690 (R10 29→22), ohne lists 0.709, ohne tests 0.719, ohne exempt 0.722. Konsequenz: Standard von `run` seit 2026-10-24 mit allen fünf. **Für den Stoßfänger plausibel?** Ja: tables betrifft R10-Prüfpegel (Sensoren/Elektronik im Stoßfänger), modes verwirft Betriebsarten, die die Spec nicht hat; beide ohne Leuchten-Bezug formuliert.
- **2026-10-24 · Rechner im Team laufen in verschiedenen Zeitzonen.** Beleg: LOG-Einträge von Homsianer (VM) und Amiad
  (Cloud) mit +0000, Jonathan mit +0200 → session-start sortierte 16:22 vor 15:00. Konsequenz: `scripts/log` schreibt
  immer `TZ=Europe/Berlin` (selftest prüft das mit TZ=UTC); ältere +0000-Einträge bleiben leicht falsch einsortiert.
  Linux braucht dafür `tzdata` (auf normalen VMs vorhanden).
- **2026-10-24 · Precision-Verlust kommt vor allem aus Absätzen, die die Musterlösung gar nicht nimmt.** Beleg:
  experiments/runs/E020-a/analyse.json (Richter lenient): 207 Treffer-lose = 139 aus Nicht-Gold-Absätzen, 54 aus
  Gold-Absätzen (39 rechnerisch überzählig), 14 aus Extra-Regelungen. In R48 lässt das Gold „Presence"-Absätze
  (Ausrüstungspflicht des Fahrzeugs), nicht vorhandene Varianten (S3/S4, bewegliche/versenkbare Leuchten,
  asymmetrische Fahrzeuge, Anhänger) und Verwaltung weg. **Für den Stoßfänger plausibel?** Ja als Prinzip
  (Anwendbarkeit auf das Bauteil), nicht als Liste von Absatznummern. Fehlende 37: R10 17, R48 11, R150 5, R148 4.
- **2026-10-24 · GTRs haben einen unverbindlichen Teil I, der wie Regelungstext aussieht.** Beleg: UN GTR 9 base (131 S.): „I. Statement of technical rationale and justification" S. 1–70 mit eigener Nummerierung 1., 2. … (13 doppelte Absatzlabels mit Teil II), „II. Text of the Regulation" ab S. 71; mit `--filters` admin/cop/parts/esa stammen 38 von 214 modal-Kandidaten aus Teil I (Jonathans Robustheitslauf zitierte S. 4/15/18). Konsequenz: pdf.py markiert Teil I im Kontext, Filter `rationale` wirft ihn raus (in `--filters all`). **Für den Stoßfänger plausibel?** Ja, genau dort: GTR 9 (Fußgängerschutz) betrifft die Fahrzeugfront.
- **2026-10-24 · Plattform-Eichung: Seiten und Regelungen lokal exakt, Anforderungen lokal mit `--judge lenient`.**
  Beleg: E020-a-P, E008-a-P, AP10-K2 (experiments/runs/*/platform.json): Seiten- und Regelungswerte von score_local
  stimmen auf 3 Stellen mit der Plattform überein. Anforderungen Plattform 154 Treffer (F2 0.687) vs lokal lenient 153
  (0.683) bzw. strict 141 (0.629); bei der Absatz-Baseline Plattform 62 vs lenient 84 / strict 53. Größeres Seitenfenster
  ändert nichts. Konsequenz: für Pipeline-Ausgaben (Einzelpflichten) ist `--judge lenient` die Plattform-Prognose,
  strict die konservative Untergrenze; Rangfolgen stimmen bei beiden. Die Plattform wertet eine Anforderung mit der
  erwarteten Pflicht plus etwas Zusatz als Treffer, ganze Absätze mit vielen Pflichten aber nur selten.
- **2026-10-24 · Sub-Goal-Näherung (Amiad) liegt nah an der Plattform.** Beleg: E003-am-P: Plattform Flag-Recall 0.792,
  Precision 0.760, Change accuracy 0.889 vs lokal 0.833/0.800. Konsequenz: lokale Näherung brauchbar, 1 Treffer optimistisch.
- **2026-10-24 · Auswahl mit strukturierter Begründung statt Bitte im Prompt filtert Spekulatives zuverlässig.**
  Beleg: E020-a (main@fd0820a): Modell gibt je Regelung `stated_in_spec` und `requirement_locus` an, Code verwirft
  Annahmen und reine Fahrzeugebene. Dev: R13H/R128 raus, Regelungen 0.870→0.909, Anforderungen 0.621→0.629 bei
  gleichem Recall (ohne Streuung, weil die Extraktion der übrigen Regelungen aus dem Cache identisch ist); 3/3 Läufe
  gleich. Stoßfänger (synthetisch) 2/2: genau der plausible Kern bleibt (R42, R127, GTR 9, R26, R149, R48, R10).
  **Für den Stoßfänger plausibel?** Ja, dort wirkt es stärker als beim Leuchten-Fall.
- **2026-10-24 · Robustheit an einem anderen Bauteil (synthetischer Frontstoßfänger, keine Messung).** Beleg:
  experiments/synthetic/front-bumper-run.json (main@ff9e843): läuft fehlerfrei, validate.py ok, 231 s und ~435k Tokens
  für einen neuen Fall (146 LLM-Aufrufe). Auswahl-Kern plausibel (R42, R26, R127, R149 statt R19, R48, R10).
  Schwächen, die der Leuchten-Fall nicht zeigen konnte: (1) **GTR 9 hat 70 Seiten Begründung vor dem verbindlichen
  Text** (ab S. 71 „II. Text of the Regulation"); die Extraktion zitiert auch S. 4/15/18 daraus. (2) Die Auswahl nimmt
  bedingte Kandidaten („If the radar supplies AEBS …": R128, R152) und Regelungen der Fahrzeugebene (R94, R137, R155);
  R155 liefert 23, R128 32 Anforderungen, vermutlich Rauschen. (3) R127 und GTR 9 überschneiden sich (Beinaufprall).
- **2026-10-24 · Fall-Ordner können Anleitungstexte enthalten.** Beleg: `load_case` las jede .md/.txt als Spec; eine
  README im Held-out-Ordner wäre ans LLM gegangen. Konsequenz: README* wird übersprungen (main@ff9e843, Test).
- **2026-10-24 · Die LLM-Pipeline streut um etwa ±0.02 Anforderungs-F2 je Lauf.** Beleg: E019-a = E016-a identisch
  ohne Cache: 0.621 → 0.602, Auswahl gleich, Recall je Regelung schwankt (R10 14↔19). Konsequenz: Unterschiede unter
  ~0.03 aus Einzelläufen nicht als Verbesserung werten; bei knappen Entscheidungen 2–3 Läufe ohne Cache vergleichen.
  Bestmarke realistisch ~0.61.
- **2026-10-24 · Nur aus der Zeichnung trägt die Pipeline, aber schwächer; zusätzlich zur Spec bringt sie nichts.**
  Beleg: E017-a (`--vision only`) Anforderungen 0.417, Regelungen 0.682 (R150 fehlt: Rückstrahler auf der
  Patentzeichnung nicht erkennbar; R53 falsch: Fahrzeugklasse fehlt im Bild); E018-a (`--vision on`) 0.605 vs 0.621,
  innerhalb der Streuung. Konsequenz: `--vision auto` (Standard): Zeichnung nur lesen, wenn keine Spec da ist.
  **Sonntag:** Ist die Held-out-Spec deutlich dünner als die Dev-Spec, `--vision on` per Plattform-Upload testen.
- **2026-10-24 · Regelungsauswahl per LLM mit Steckbriefen aus den PDFs trifft alle Gold-Regelungen.** Beleg: E016-a
  (main@39b1077): 7 gewählt, 4/4 Gold inkl. UN R10 (Begründung: LED-Platine → EMV), Regelungs-F2 0.405→0.870,
  Anforderungs-F2 0.491→0.621 (Gold-Diagnose 0.637); 3 Läufe ohne Cache identisch. Die PDFs nennen ihre Konsolidierung
  selbst (R148 „combines … Nos. 4, 6, 7, 23 …", R150 „Nos. 3, 27, 69, 70 and 104"): das LLM verwirft R7/R23/R3 mit dieser
  Begründung. **Für den Stoßfänger plausibel?** Ja: Prinzipien und Steckbriefe sind fallunabhängig; Extras wie R26/R42
  kosten beim Leuchten-Fall ~0.016 F2, sind beim Stoßfänger aber vermutlich Pflicht.
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

- **Fahrzeugausrüstung per Prompt-Regel verwerfen (`--extract …,vehicle`).** Beleg: E030-hs-c vs E024-hs-c (Claude-Reihe, main@870cd16): F2 strict 0.721→0.698, R48-Recall 40→34/56: das Modell verwirft mit der Regel auch Installationspflichten der Leuchte (Lage, Sichtbarkeit), obwohl die Regel sie ausdrücklich ausnimmt. Für den Stoßfänger noch riskanter (R26/R127 sind fahrzeugseitig formuliert). Stattdessen: Precision über Prüfabläufe (`procedure`, E031-hs-c: P 0.45→0.52 bei −7 Treffern) oder über Dubletten (PLAN Prio 2) holen.
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
