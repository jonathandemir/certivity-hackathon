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

### 2026-10-24 13:09:14 +0200 | [decision] Arbeitssystem für parallele Agenten und Menschen | Jonathan @ MacBook-Pro-von-Jonathan | main@9fffaa8
- Grundsatz: Das Repo ist das einzige gemeinsame Gedächtnis. Regeln in AGENTS.md, Projektfakten in docs/CONTEXT.md; CLAUDE.md lädt beide per @-Import.
- Branches: eine Person = ein Branch <vorname> (scripts/setup). Geteilte Dateien (AGENTS.md, CLAUDE.md, README.md, docs/, experiments/, scripts/, .claude/) nur auf main, geändert über den main-Worktree .worktrees/main (scripts/main-wt), nie per Branch-Wechsel. scripts/sync merged origin/main konfliktfrei in den eigenen Branch.
- Ausnahme docs/LOG.md: Eintrag im selben Commit wie der Code auf dem eigenen Branch, merge=union; scripts/session-start liest LOG.md aus allen origin-Branches, entfernt Duplikate und sortiert nach Zeit. Grund: Liegt LOG.md nur auf main, können Code und Logeintrag nie im selben Commit landen.
- Schleife: scripts/claim add → kleiner Schritt → Tests grün → scripts/log → Code + LOG in einem Commit → scripts/sync (mindestens alle 30 min, immer vor Schluss) → scripts/claim done, LEARNINGS, [handoff] am Session-Ende.
- sync: git pull --rebase ohne lokale Merge-Commits, sonst --no-rebase; Stopp mit Anleitung bei Konflikt, nichts gepusht; Secret-Scan der ausgehenden Commits vor jedem Push; nie force.
- Ergebnisse: scripts/pull-first vor jedem zählenden Lauf (Exit 0 = zählt, gibt <branch>@<hash> aus); Zeile in experiments/LEDGER.md + Beleg unter experiments/runs/<ID>/; Bestmarken als Tag best-<branch>-<wert> (scripts/tag-best); Entscheidungen nur auf echte Messungen, jede Änderung einzeln gegen die Bestmarke.
- Hooks (.claude/settings.json): SessionStart → scripts/session-start (STATUS + LOG im Kontext); Stop → scripts/stop-check --hook (Warnung; blockiert einmal, wenn Arbeit länger als 30 min ungepusht oder ein Konflikt offen ist).
- Tests: Sandbox mit bare origin, anna auf zwei Rechnern + ben. Geprüft u. a.: union-Merge von LOG.md bei rebase und merge ohne Konflikt, Merge-Pfad spielt lokalen Merge-Commit nicht neu ab, Konflikt stoppt ohne Push, Claim-Race beim Push (Retry), pull-first-Gates (ungetrackt, uncommittet, ungepusht, neuer Code auf main), Stop-Hook-JSON, Secret-Scan blockiert Push. 134/134 auf macOS (bash 3.2, BSD-Tools, git 2.51) und Debian (bash 5.2, GNU, mawk, git 2.47).
- Offen: Freeze-Zeiten in docs/PLAN.md vom Team bestätigen; Team-Namen fehlen noch in docs/STATUS.md.

### 2026-10-24 13:16:14 +0200 | [change] setup: PDF-Download mit certifi-Retry | Jonathan @ MacBook-Pro-von-Jonathan | main@b24caa0 +lokale Änderungen
- python.org-Python auf macOS hat keine CA-Zertifikate; setup versucht es nach CERTIFICATE_VERIFY_FAILED einmal mit SSL_CERT_FILE=$(python3 -m certifi), nur für diesen Aufruf
- Geprüft: UN_R3_base.pdf entfernt → erster Versuch 93/94 (SSL-Fehler), Retry 94/94, Datei bytegleich; bash -n ok
- LEARNINGS-Eintrag mit Beleg ergänzt

### 2026-10-24 13:16:49 +0200 | [handoff] Arbeitssystem fertig, Team-Onboarding offen | Jonathan @ MacBook-Pro-von-Jonathan | jonathan@857c5a0
- Stand: main@857c5a0 enthält Regeln, docs, Skripte, Hooks; getestet auf macOS + Debian (134/134), SessionStart-Hook in echter Claude-Session geprüft. Jonathans Rechner: Branch jonathan, .worktrees/main, Paket + 94 PDFs unter vendor/, ~/projects/CLAUDE.md angelegt.
- Nächster Schritt: Team auf hackathon.certivity.io registrieren (Team-ID in STATUS), Teammitglieder als Collaborators zum privaten Repo einladen, Namen in STATUS/Team, dann AP1 aus docs/PLAN.md claimen.
- Fallen: jsonschema fehlt in Jonathans Python (validate.py); ~/projects/CLAUDE.md wird auch in Sessions anderer Projekte unter ~/projects geladen (nach dem Hackathon löschen); Zeitumstellung in der Nacht auf Sonntag; Held-out ist ein Frontstoßfänger, nicht an der Heckleuchte überanpassen.

### 2026-10-24 13:27:36 +0200 | [change] AP1: Pipeline-Gerüst + Bewertungsschleife (certreq/) | Jonathan @ MacBook-Pro-von-Jonathan | jonathan@ef1d9f5 +lokale Änderungen
- CLI: .venv/bin/python -m certreq run <fall-ordner> [--regs ...] → out/<fall>.json + .meta.json (Git-Stand aus git); eval <abgabe> → validate.py + score_local.py + F2, --record <ID> legt Beleg unter experiments/runs/<ID>/ im main-Worktree ab (verweigert unsaubere/ungepushte Läufe)
- Stufen austauschbar: select.select_regulations (B0: Wortüberlappung Spec↔Titel, --regs erzwingt), extract.extract_requirements (B0: jeder Absatz mit 'shall'), pdf.parse_pdf (Absatz + Seite, Labels wie Referenz: '4.8.1.7', 'Annex 9 3.1', 'Annex 4 Part 1 1.2')
- Fix im Parser: Anhang-Überschriften nur in Reihenfolge akzeptieren; Tabellenzelle 'Annex 10 (values in' (UN R150 S. 5) hatte vorher alle Haupttext-Absätze falsch gelabelt (90/121 → 121/121 Referenz-Absätze mit Label + Seite gefunden)
- Tests: 8 grün (pytest), u. a. Regressionstest 121/121 Absätze der Referenz, Abgaben bestehen validate.py, expected.json wird nie gelesen
- Setup: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt (pymupdf, jsonschema, pytest)

### 2026-10-24 13:29:05 +0200 | [run] E001 Baseline B0 auf dev-rear-lamp | Jonathan @ MacBook-Pro-von-Jonathan | main@9c48f4f +lokale Änderungen (ungepusht)
- Stand jonathan@29c0d0b (pull-first: zählt), Tag best-jonathan-pagef2-0.272
- Regelungen P 0.143 R 0.750 F2 0.405 (21 gewählt, UN R10 fehlt); Seiten P 0.073 R 0.849 F2 0.272 (score_local); 3624 Anforderungen; Anforderungsebene braucht Plattform-Upload
- Beleg experiments/runs/E001/

### 2026-10-24 13:29:06 +0200 | [run] E002 Diagnose: B0-Extraktion mit Gold-Regelungen | Jonathan @ MacBook-Pro-von-Jonathan | main@9c48f4f +lokale Änderungen (ungepusht)
- Stand jonathan@29c0d0b; --regs 'UN R148,UN R48,UN R150,UN R10' (Gold-Wissen, für Held-out unzulässig, nicht hochladen)
- Regelungen F2 1.000; Seiten P 0.206 R 1.000 F2 0.565; 1214 Anforderungen statt 190
- Schluss: Auswahl (AP2) ist der größte Hebel, dann Precision (AP4). Beleg experiments/runs/E002/

### 2026-10-24 13:29:06 +0200 | [decision] AP1-Gerüst jetzt nach main | Jonathan @ MacBook-Pro-von-Jonathan | main@9c48f4f +lokale Änderungen
- certreq/ + tests/ auf main gemergt (Merge-Commit), damit alle Branches dieselbe Basis für AP2–AP7 haben; sync merged main automatisch in jeden Branch
- Die finale beste Version wird trotzdem vor der Deadline nach main gemergt (PLAN So 07:30)

### 2026-10-24 13:31:32 +0200 | [change] scripts/log --commit <branch>@<hash> für [run]-Einträge aus anderem Checkout | Jonathan @ MacBook-Pro-von-Jonathan | main@40fd760 +lokale Änderungen
- Problem (gesehen bei E001/E002): [run] aus dem main-Worktree geloggt → Kopf zeigte main@9c48f4f +lokale Änderungen (ungepusht) und zwei falsche Warnungen, obwohl auf sauberem, gepushtem jonathan@29c0d0b gemessen wurde. Die Details dieser Einträge nennen den richtigen Stand.
- Jetzt: --commit setzt 'gemessen auf <branch>@<hash>', prüft Existenz (sonst Abbruch) und ob gepusht (sonst Warnung + '(ungepusht)')
- AGENTS.md §5/§9 ergänzt
- Geprüft: Sandbox-Suite um 9 Prüfungen erweitert, 143/143 auf macOS (bash 3.2) und Debian (bash 5.2, mawk)

### 2026-10-24 13:31:50 +0200 | [handoff] AP1 fertig bis auf den Plattform-Upload | Jonathan @ MacBook-Pro-von-Jonathan | jonathan@a48c8a5
- Stand: certreq (run/eval/--record) auf main und jonathan (a48c8a5); 8 Tests grün; E001 = Referenz (Seiten-F2 0.272, Regelungs-F2 0.405, Tag best-jonathan-pagef2-0.272); E002 = Diagnose mit Gold-Regelungen (Seiten-R 1.000, P 0.206)
- Nächster Schritt: Jonathan registriert das Team und lädt E001 mit echter Team-ID hoch (Befehl in STATUS 'Nächste Schritte'), Anforderungs-Score ins Scoreboard; danach AP2 (Regelungsauswahl, größter Hebel) und AP4 (Precision: 1214 statt ~190 Anforderungen) claimen
- Fallen: E002 nicht hochladen (Gold-Wissen verfälscht Dev-Leaderboard); out/ ist gitignored, Belege nur über eval --record; [run]-Einträge aus dem main-Worktree mit scripts/log --commit; venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
### 2026-10-24 13:52:33 +0200 | [decision] Aufteilung A/B/C | Jonathan @ MacBook-Pro-von-Jonathan | main@f8ff330 +lokale Änderungen
- A = Jonathan (jonathan): LLM-Zugang + certreq/llm.py zuerst, dann AP10 lokaler LLM-Richter, AP2 Regelungsauswahl, AP5 Vision, Plattform-Uploads
- B = Homsianer (homsianer): AP3-Rest (Gliederung/Überschriften, Tabellen), AP4 Relevanzfilter entlang der Gliederung + Zerlegung in einzelne Pflichten; misst mit --regs, bis AP2 steht
- C = Amiad (amiad): AP6 Demo-Gerüst auf E001-Ausgabe, AP7 Sub-Goal, AP9 Pitch-Lead; So alle AP8
- Dateigrenzen je Person und Schnittstellen in docs/PLAN.md 'Aufteilung'; neues Paket AP10 (lokaler Richter für die Anforderungsebene)

### 2026-10-24 14:01:58 +0200 | [decision] Alle arbeiten auf main | Jonathan @ MacBook-Pro-von-Jonathan | main@907f57a +lokale Änderungen
- Ersetzt persönliche Branches (ursprünglicher Plan): drei Leute mit getrennten Dateien und gegenseitigen Abhängigkeiten; AP1 musste schon vorzeitig nach main, damit die anderen darauf aufbauen können
- Schutz statt Branches: scripts/sync führt vor jedem Push mit Code-Änderungen die Tests aus und pusht bei Rot nicht; neue Ansätze kommen hinter Schalter, der Standard wird erst nach besserer Messung umgestellt; Sonntag Freeze + Tag best-main-…
- Branches nur noch ausnahmsweise für riskante Experimente (kurzlebig)
- Migration: Branch jonathan nach main gemergt (alle Commits enthalten, geprüft mit merge-base), lokal und auf origin gelöscht; main-Worktree entfernt; Tag best-jonathan-pagef2-0.272 zeigt weiter auf einen Commit in main

### 2026-10-24 14:01:58 +0200 | [change] Skripte und Doku auf 'alle auf main' umgestellt | Jonathan @ MacBook-Pro-von-Jonathan | main@907f57a +lokale Änderungen
- setup: stellt auf main, legt .venv an (requirements.txt), kein Namensargument mehr; sync: Test-Check vor Push, nur wenn ausgehende Commits Code berühren (rote fremde Tests blockieren keine Doku-Pushes); claim: Spalte Rechner statt Branch, spult main selbst vor
- AGENTS.md §1-§5, §9, README, PLAN, STATUS, LEARNINGS (Verworfen: persönliche Branches), CONTEXT angepasst
- Neu: scripts/selftest (Sandbox mit 3 simulierten Rechnern, alle auf main): 132/132 auf macOS (bash 3.2) und Debian (bash 5.2, mawk); pytest 8/8

### 2026-10-24 12:10:19 +0000 | [change] AP6: Demo-Gerüst (demo/build.py + template.html) | Amiad @ claude | main@fbec7d5 +lokale Änderungen
- Pipeline-Ausgabe out/<fall>.json (+ .meta.json) → eine selbstständige HTML-Seite: Regelungsfilter mit Zähler, Suche mit Markierung, Sortierung, je Anforderung Regelung/Version/Seite/Absatz, Viewer-Pane mit PDF an der zitierten Seite (#page=N, relative Links), Eingabe (Spezifikation + Zeichnung) aufklappbar, Hell/Dunkel. demo/dist/ ist gitignored (enthält Paketdaten). Liest nur das JSON-Format aus CONTEXT §8; optionales meta.reasons {regulation: Begründung} wird je Regelung angezeigt, sobald AP2 es liefert.
- Geprüft: pytest 9 grün (neu tests/test_demo.py: Daten-Einbettung, </script>-Escape, PDF-Link relativ + existiert); Headless-Chromium auf E001-Ausgabe (3624 Anforderungen): keine JS-Fehler, Filter/Suche/Viewer funktionieren; PDF-Anzeige im Frame nicht getestet (Headless ohne PDF-Viewer).

### 2026-10-24 14:17:30 +0200 | [change] AP3: Gliederung im Parser (title, headings) | Jonathan @ MacBook-Pro-von-Jonathan | main@9314c99 +lokale Änderungen
- certreq/pdf.py: Paragraph.title (eigene Überschrift, z. B. R48 6.10 'Rear position lamp'), Paragraph.headings (umgebende Abschnitte außen zuerst, inkl. Anhang- und Teil-Titel, z. B. R150 'Annex 6 Part 4 1' → Environmental Testing › Resistance to corrosion), Paragraph.body (Text ohne Überschrift). Felder mit Default, bestehende Aufrufer unverändert
- Überschriften sind typografisch nicht abgesetzt (alles TimesNewRoman 10.5, per get_text('dict') geprüft), daher Texterkennung: kurze Zeile ohne Verb/Doppelpunkt/Satzanfang/hängende Präposition, danach Absatzende oder neuer Satz. Stichprobe 70 Titel über alle 56 Regelungen: nach Regel-Feinschliff keine falschen mehr gesehen (vorher z. B. 'Within 60 seconds … by paragraph'); 7967 von 27231 Absätzen haben einen Titel
- Geprüft: pytest 11/11 (neu tests/test_outline.py, Regressionstest 121/121 unverändert); B0-Ausgabe für E001 und E002 bytegleich zur abgelegten Abgabe (Parser-Änderung verschiebt keine Messung)

### 2026-10-24 12:19:02 +0000 | [change] AP7: Sub-Goal regelbasiert (certreq/subgoal.py) | Amiad @ claude | main@576182a +lokale Änderungen
- Satzweiser Vergleich alt/neu: Anforderung → alte Sätze (Label + Wortüberdeckung) → ähnlichster neuer Satz (global, Verschiebungen/Umnummerierung egal). identisch = unverändert, ähnlich (≥0.55) = modified mit 'a' became 'b'-Reason im Referenzstil, kein Gegenstück = removed; neue shall-Sätze (auch Aufzählungspunkte mit shall in der Einleitung) ohne Gegenstück = added. Normalisierung: % = per cent, seconds = s, eingefügte Überschrift und Absatznummer-Reste zählen nicht. CLI: python -m certreq.subgoal run|eval <subgoal-ordner>; Version/Regelung aus der PDF-Kopfzeile, nichts hartkodiert.
- Geprüft: pytest 16 grün (neu tests/test_subgoal.py), validate.py --requirements-old ok; subgoal-dev lokal (id/Absatzlabel-Näherung): modified R 6/6, removed 1/1, added 13/17, Precision 0.75/0.5/0.87. Nur an einem Fall abgestimmt, Held-out ungetestet.

### 2026-10-24 12:19:28 +0000 | [run] E003-am Sub-Goal auf subgoal-dev | Amiad @ claude | gemessen auf main@bc77252
- Lokale Näherung (id bzw. Absatzlabel, nicht die semantische Plattformbewertung): modified R 6/6 P 0.75, removed R 1/1 P 0.50, added R 13/17 P 0.87, gesamt R 0.833 P 0.800 F2 0.826. Beleg experiments/runs/E003-am/. Die Reason-Texte folgen dem Referenzstil, ob die Plattform die Änderung als richtig wertet, ist offen.

### 2026-10-24 12:19:28 +0000 | [finding] pdf.py übersieht Absätze ohne Punkt nach der Nummer | Amiad @ claude | main@bc77252 +lokale Änderungen
- Beleg: subgoal/dev/new.pdf Seite 5: '5.1.4.1 An ACPE intervention is not required when:' und '5.1.4.2 If ACPE is not ready ...' (Nummer ohne abschließenden Punkt). PARA_RE verlangt den Punkt, die Absätze verschmelzen mit 5.1.4. Folge im Sub-Goal: 'added 5.1.4.1' fehlt, Reason von R-019/R-020 enthält den Rest '5.1.4.2'. Betrifft auch das Hauptziel, falls Regelungen dieses Format haben. Für B (certreq/pdf.py), von mir nicht angefasst.

### 2026-10-24 14:24:35 +0200 | [change] AP4: Relevanzfilter entlang der Gliederung (--filters, Standard bleibt B0) | Jonathan @ MacBook-Pro-von-Jonathan | main@4a82cc6 +lokale Änderungen
- Neu certreq/relevance.py, Schalter run --filters admin,cop,parts,esa | all | none (Standard none = B0, meta.json hält 'filters' fest). admin: Verwaltungsabschnitte (Definitions, Application for approval, Approval, Modifications, Penalties, Transitional provisions, Communication, Information document …) weg, 'Approval marking and other markings' bleibt. cop: Conformity of production weg außer Toleranzabsätzen ('shall not deviate … more than 20 per cent'). parts: in Aufzählungen von Gerätetypen (R48 6.1–6.28, R148 5.1–5.12) nur Abschnitte, deren Titel ein Teil/eine Funktion aus der Spec enthält (Lagewörter front/side … müssen in der Spec stehen); greift nur bei ≥1 Treffer und ≥3 Geschwistern mit demselben Gerätebegriff, 'General …' bleibt. esa: wo Geschwister nach vehicles/ESAs getrennt sind (R10 6.2–6.4 vs 6.5–6.9, Anhänge 4–6/11–16), nur ESA. pdf.py: Paragraph.context (Anhang-/Teil-Titel), zweizeilige Überschrift mit hängendem Wort ('… generated by' / 'ESAs on 12/24 V …')
- Vormessung (Arbeitsstand, offizielle Messung folgt als [run]): Seiten-F2 gold-Regelungen 0.565→0.753, B0-Auswahl 0.272→0.342; jeder Filter einzeln besser, keiner verliert einen Gold-Absatz von B0 (Test test_filters_keep_every_gold_paragraph_of_b0). Ohne cop-Ausnahme gingen R148 6.1.3 und R150 Annex 2 1.2 verloren
- Geprüft: pytest 22/22 (neu tests/test_extract.py); B0 ohne --filters weiterhin 1214 bzw. 3624 Anforderungen

### 2026-10-24 14:25:41 +0200 | [run] E004 Relevanzfilter --filters all auf dev-rear-lamp | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@d962217
- vs E001 (B0): Regelungen unverändert P 0.143 R 0.750 F2 0.405; Seiten P 0.073→0.101, R 0.849→0.849, F2 0.272→0.342; 2403 statt 3624 Anforderungen; 446 statt 616 zitierte Seiten, 45/53 Gold-Seiten wie vorher
- Einzeln (gleicher Stand, experiments/runs/E004/filters.txt): admin 0.302, cop 0.277, parts 0.295, esa 0.272; mit Gold-Regelungen 0.565→0.753 bei Seiten-R 1.000. Absatz-Ebene gegen expected.json (eigene Messung, nicht Plattform): F2 0.100→0.142 bzw. mit Gold-Regelungen 0.282→0.430
- Neue Bestmarke Seiten-F2 hinter Schalter, Tag best-main-pagef2-0.342. Standard bleibt B0, damit der geplante E001-Upload (Eichung der Anforderungsebene) nicht unbemerkt eine andere Datei erzeugt. Beleg experiments/runs/E004/

### 2026-10-24 14:26:10 +0200 | [run] E005 Diagnose: Gold-Regelungen + --filters all | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@60fef43
- vs E002: Seiten P 0.206→0.379, R 1.000→1.000, F2 0.565→0.753; 632 statt 1214 Anforderungen, 140 statt 257 zitierte Seiten. Gold-Wissen, nicht hochladen
- Rest: Gold hat 119 Absätze/190 Anforderungen, wir 632 Absätze. Absatz-Recall bleibt 0.798, weil 37 Gold-Anforderungen aus Absätzen ohne 'shall' stammen (must, 'may … only', Listen wie R48 6.10.2 'Number Two'). Beleg experiments/runs/E005/
### 2026-10-24 14:26:27 +0200 | [change] certreq/llm.py: gemeinsamer LLM-Zugang (OpenAI) | Jonathan @ MacBook-Pro-von-Jonathan | main@0812aec +lokale Änderungen
- ask_json(system, user, schema) → dict als Structured Output (strict), ask_many parallel mit fester Reihenfolge, usage() für die Lauf-Metadaten
- Key aus OPENAI_API_KEY oder LLM_API_KEY, gelesen aus Umgebung, .env oder .env.local (gitignored); Vorlage .env.example
- Modelle als feste Snapshots: DEFAULT_MODEL gpt-5.4-mini-2026-03-17 (Massenaufrufe), STRONG_MODEL gpt-5.5-2026-04-23 (Auswahl, Richter); Override CERTREQ_MODEL bzw. model=; effort none/low/medium/high/xhigh (minimal gibt 400)
- Cache out/cache/llm/<sha256>.json über Modell+Prompt+Schema+effort: Wiederholungen kosten nichts und sind reproduzierbar
- Geprüft: 8 neue Tests ohne Netz (24/24 grün), Live-Check beider Modelle ok (python -m certreq.llm)

### 2026-10-24 14:27:53 +0200 | [change] pdf.py: Absatznummern ohne abschließenden Punkt (Fund von Amiad) | Jonathan @ MacBook-Pro-von-Jonathan | main@7a5d0ef +lokale Änderungen
- Behebt [finding] 'pdf.py übersieht Absätze ohne Punkt nach der Nummer' (Amiad, 12:19): '5.1.4.1 An ACPE intervention …' (subgoal/dev/new.pdf S. 5) wird jetzt eigener Absatz. Regel: Nummer mehrstufig, danach großgeschriebenes Wort (keine Einheit wie Hz), und direkter Nachfolger des laufenden Absatzes (Kind, Geschwister oder nächste höhere Ebene), sonst bleibt es Fließtext (Messwerte wie '13.5 V')
- Wirkung: 228 neue Absätze über alle 56 Regelungen (126 in base), Stichprobe 25/25 echte Absätze; dev: R48 bekommt u. a. 5.7 (Unterabsätze tragen 4 Gold-Anforderungen), Scores auf 3 Stellen unverändert (E004-Konfiguration Seiten-F2 0.342, gold-Regelungen 0.753). B0-Standard auf dev: 3642 statt 3624 Anforderungen
- Achtung E001-Upload: die abgelegte Datei experiments/runs/E001/submission.json.gz nehmen (team_id ersetzen) oder vom Tag best-jonathan-pagef2-0.272 erzeugen; ein Lauf auf dem aktuellen main ist nicht mehr bytegleich zu E001. Geprüft: pytest 24/24
### 2026-10-24 14:28:15 +0200 | [change] Paket-Check im Sessionstart, Sonntagsbefehl, Regel 'eine Session = ein Checkout' | Jonathan @ MacBook-Pro-von-Jonathan | main@7660278 +lokale Änderungen
- scripts/session-start fetcht das offizielle Paket (15-s-Limit) und meldet neue Commits bei Certivity mit ACHTUNG + neuen Fällen unter cases/ bzw. subgoal/; sonst 'Teilnehmerpaket: @hash, aktuell'
- PLAN: Sonntag 08:00 = scripts/setup (holt Held-out + PDFs) + Zip-Ankündigung prüfen
- AGENTS §4: mehrere Agenten auf einem Rechner → je ein eigener Klon; Anlass: zweite Session uncommittet in ~/projects/certivity, sync dort blockiert; diese Session arbeitet jetzt in ~/projects/certivity-a
- STATUS: LLM-Entscheidung (OpenAI, Modelle, .env.local) eingetragen; LEARNINGS: 2 Einträge mit Beleg
- Geprüft: scripts/selftest 138/138 auf macOS (bash 3.2) und Debian (bash 5.2, mawk), inkl. simuliertem Held-out-Push bei Certivity

### 2026-10-24 14:29:13 +0200 | [change] AP4: cop erkennt 'Control of conformity of production', parts erkennt parallele Abschnitte | Jonathan @ MacBook-Pro-von-Jonathan | main@3f2f666 +lokale Änderungen
- cop: COP_RE auch 'Control of conformity of production' (R48-Anhang). parts: zweite Aufzählungsform, ≥3 Geschwister mit gleichem Titelanfang (3 Wörter) wie ein Treffer, z. B. R150 5.1–5.3 'Technical requirements concerning retro-reflectors / marking materials / advance warning triangles' → 5.2/5.3 fallen weg; nur die parallelen Geschwister, andere bleiben
- Vormessung je Änderung (Arbeitsstand, offizielle Messung folgt): cop-Erweiterung allein Seiten-F2 gold-Regelungen 0.753→0.757, B0-Auswahl 0.342→0.344; parallele Abschnitte zusätzlich 0.757→0.773 bzw. 0.344→0.348; Seiten-Recall jeweils unverändert (1.000 bzw. 0.849)
- Geprüft: pytest 33/33 (neu test_parts_parallel_sections_with_same_title_opening)

### 2026-10-24 14:29:39 +0200 | [run] E006 Relevanzfilter-Feinschliff, --filters all | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@3e979ed
- vs E004: Seiten P 0.101→0.103, R 0.849 gleich, F2 0.342→0.348; Regelungen gleich (F2 0.405); 2341 Anforderungen
- Mit Gold-Regelungen (Diagnose, filters.txt): Seiten-F2 0.773 bei R 1.000, Absatz-Ebene F2 0.458 (eigene Messung gegen expected.json). Tag best-main-pagef2-0.348. Beleg experiments/runs/E006/

### 2026-10-24 14:32:13 +0200 | [decision] LLM-Modell: gpt-6.1-sol für alles | Jonathan @ MacBook-Pro-von-Jonathan | main@49c80eb +lokale Änderungen
- Vorgabe Jonathan. certreq/llm.py: DEFAULT_MODEL und STRONG_MODEL = gpt-6.1-sol (Override CERTREQ_MODEL bzw. model=)
- Live-Test: Structured Output ok, fachlich richtige Antwort (UN R148), ~2,5–3 s pro kurzem Aufruf; reasoning_effort nur low/medium/high/xhigh
- Kein datierter Snapshot verfügbar (nur Alias): jede gecachte Antwort speichert das Modell; Fallback für Massenaufrufe bei Tempo-/Kostenproblemen: gpt-5.4-mini-2026-03-17

### 2026-10-24 14:33:04 +0200 | [change] AP4: Extraktionsoptionen --extract modal,split (Standard none) | Jonathan @ MacBook-Pro-von-Jonathan | main@475417f +lokale Änderungen
- modal: auch Absätze mit must/may/(not) permitted/allowed/required/mandatory/prohibited (im Dev-Gold 35 von 190 Anforderungen ohne shall). split: Aufzählungen (a)(b)(c) je Punkt eine Anforderung mit Einleitungssatz (R150 5.1.1 → 3), Verweise wie 'paragraphs 3.3.3.5. (a) and (b)' bleiben ganz; Text aus Paragraph.body (ohne Überschrift). Satzweises Zerlegen geprüft und verworfen (Obergrenze 0.411 statt 0.407, Precision fällt). meta.json hält 'extract' fest
- Vormessung (offiziell folgt): Obergrenze Anforderungsebene = je Gold-Absatz min(unsere, Gold-Anzahl), unterstellt Treffer im richtigen Absatz, KEIN Plattformwert. Mit Gold-Regelungen + --filters all: ohne 0.359, modal 0.407, split 0.384, beide 0.430; Seiten-F2 modal 0.773→0.759 (zusätzliche Nicht-Gold-Seiten), split unverändert
- Geprüft: pytest 35/35, Ausgabe mit --filters all --extract all besteht validate.py

### 2026-10-24 14:33:34 +0200 | [run] E007 --filters all --extract modal,split | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@8357f66
- vs E006: Seiten-F2 0.348→0.339 (P 0.103→0.100, R 0.849 gleich), Regelungen gleich; 2966 Anforderungen
- Gegen expected.json, keine Plattform: Absatz-F2 0.145→0.166; Obergrenze Anforderungsebene (je Gold-Absatz min(unsere, Gold-Anzahl)) F2 0.131→0.152, R 0.426→0.595; mit Gold-Regelungen 0.359→0.430. Einzeln in experiments/runs/E007/options.txt: modal kostet Seiten-F2 (−0.009 bzw. −0.014), split ist auf Seiten neutral
- Keine neue Bestmarke. Konflikt Seiten vs Anforderungen löst nur eine Anforderungs-Messung (AP10 oder Plattform-Upload): Kandidat für den ersten Richter-Lauf

### 2026-10-24 14:34:30 +0200 | [handoff] B-Arbeit vorgezogen (AP3/AP4), Übergabe an Omar | Jonathan @ MacBook-Pro-von-Jonathan | main@a288b28 +lokale Änderungen
- Stand: AP3 Gliederung fertig (Paragraph.title/headings/context/body, Nummern ohne Punkt). AP4 hinter Schaltern: run --filters all (admin,cop,parts,esa; Bestmarke E006 Seiten-F2 0.348, mit Gold-Regelungen 0.773) und --extract modal,split (E007: Seiten 0.339, Obergrenze Anforderungsebene 0.152, mit Gold-Regelungen 0.430). Standard ohne Schalter bleibt B0. Code: certreq/pdf.py, certreq/relevance.py, certreq/extract.py; Tests tests/test_outline.py, tests/test_extract.py; Messskripte experiments/runs/E004/measure_filters.py, E007/measure_options.py
- Nächster Schritt: (1) Sobald der AP10-Richter steht: E006 vs E007 auf Anforderungsebene messen, dann über modal/split und den Standard entscheiden. (2) Tabellen (Plan B Schritt 4): R148 4.8.3.1 Tabellenzellen wie '4.8.3.1. (c))' werden zu Schein-Absätzen; Gold zitiert 'R150 … Table 3'. (3) Rest-Precision braucht Inhaltsverständnis (R48 5.x, R148 4.8, R10 Anhang 9 Prüfaufbau, R150 Klassen IIIA/IVA): LLM-Relevanzentscheid je Abschnitt mit der Gliederung als Eingabe, certreq/llm.py ist da
- Fallen: (a) E001-Upload nicht vom aktuellen main erzeugen (B0 jetzt 3642 statt 3624 wegen Parser-Fix), sondern experiments/runs/E001/submission.json.gz mit echter team_id oder Tag best-jonathan-pagef2-0.272. (b) parts-Filter hängt an den Teilenamen der Spec; bei Eingabe nur Zeichnung greift er nicht (Vision AP5). (c) Regeln wurden mit Blick auf das Dev-Gold gebaut: Stoßfänger-Plausibilität steht je Regel in LEARNINGS. (d) Claim 'AP3-Rest Gliederung + AP4 Relevanzfilter' steht noch auf Jonathan: Omar übernimmt ihn per scripts/claim done/add

### 2026-10-24 14:46:53 +0200 | [change] AP10: lokaler LLM-Richter für die Anforderungsebene (certreq/judge.py) | Jonathan @ MacBook-Pro-von-Jonathan | main@4734526 +lokale Änderungen
- Nachbildung des Plattform-Scores: Kandidaten je erwarteter Anforderung (gleiche Regelung, gleicher Absatz oder ±1 Seite), gpt-6.1-sol entscheidet 'gleiche Pflicht' (Geltungsbereich, Bedingung, Grenzwert), dann 1:1 per maximalem Matching
- Modi: strict (Standard) und lenient (Kandidat mit weiteren Pflichten zählt); CLI: certreq eval <abgabe> --judge strict|lenient [--record ...]; auch python -m certreq.judge
- Lizenz: voller Bericht mit Texten aus expected.json nur lokal (<abgabe>.judge.json unter out/), ins Repo nur Kennzahlen/IDs (public_summary)
- Tests: 8 neue ohne Netz (Kandidaten, Kuhn-Matching, Kennzahlen, Lizenzschutz), gesamt 42 grün

### 2026-10-24 14:52:40 +0200 | [change] AP4: LLM-Extraktion je Absatz (--extract llm) | Jonathan @ MacBook-Pro-von-Jonathan | main@f80cc7c +lokale Änderungen
- Neu certreq/llmextract.py: Kandidat-Absätze (nach --filters, shall bzw. modal) in Batches ≤12 Absätze/9000 Zeichen je Regelung an gpt-6.1-sol (certreq/llm.py, Cache), mit Gliederungspfad, Seite und Bauteil-Spec. Antwort je Absatz: eigenständige shall-Sätze, eine Pflicht je Satz, leer = gilt nicht für das Bauteil/keine Pflicht (Definition, Verwaltung, andere Geräte/Klassen, reiner Prüfaufbau). Fehlende Antwort → Rohtext bleibt. Prompt-Beispiel selbst geschrieben (R46-Spiegel), nichts aus dem Dev-Gold. run schreibt meta.json 'llm' (Modell, Batches, behalten/verworfen, Verbrauch)
- Vormessung (offiziell folgt), --filters all, gegen expected.json: B0-Auswahl Seiten-F2 0.348→0.714 (modal+llm), Obergrenze Anforderungsebene 0.131→0.493 (kein Plattformwert); mit Gold-Regelungen Seiten 0.773→0.943, Obergrenze 0.430→0.691. shall+llm: 0.680 bzw. 0.909. Kosten: 227 Aufrufe für B0-Auswahl, ~7,5 min ungecacht mit 8 parallel
- Geprüft: pytest 45/45 (neu tests/test_llmextract.py, ohne Netz), Lauf aus Cache bytegleich zur Vormessung
### 2026-10-24 14:52:13 +0200 | [run] AP10-K Kalibrierung des lokalen Richters | Jonathan @ MacBook-Pro-von-Jonathan | main@66d51fc +lokale Änderungen
- Selbsttest expected gegen sich selbst: strict und lenient je 190/190
- Gegenprobe ohne identisches Gegenstück: strict 5 Treffer (alle Duplikate in der Referenz), lenient 14 (10 nach 1:1 → 5,3 % falscher Recall) → strict als Standard
- Beleg experiments/runs/AP10-kalibrierung/summary.json (nur IDs)

### 2026-10-24 14:52:13 +0200 | [run] E008-a bis E011-a: Anforderungsebene lokal gemessen | Jonathan @ MacBook-Pro-von-Jonathan | main@66d51fc +lokale Änderungen
- Stand main@66d51fc (pull-first: zählt), Richter gpt-6.1-sol
- B0 strict F2 0.060 (P 0.015 R 0.279), B0 lenient 0.095, --filters all 0.084, --filters all --extract modal,split 0.098 (P 0.025 R 0.384) = Bestmarke Anforderungsebene
- Fehlende bei E011-a: 32 wegen fehlender UN R10 (AP2), 85 trotz Kandidaten (Absätze statt Einzelpflichten); Precision ist der Engpass
- Belege experiments/runs/E008-a..E011-a (ohne Gold-Texte geprüft)

### 2026-10-24 14:53:23 +0200 | [change] scripts/log: [run] prüft nur Code, nicht docs/ und experiments/ | Jonathan @ MacBook-Pro-von-Jonathan | main@66d51fc +lokale Änderungen
- Anlass: die beiden [run]-Einträge eben warnten fälschlich vor uncommitteten Änderungen (nur STATUS/LEDGER/Belege waren offen); Hash main@66d51fc darin ist korrekt
- Geprüft: scripts/selftest 142/142 auf macOS und Debian (4 neue Prüfungen)

### 2026-10-24 14:53:32 +0200 | [run] E008 --filters all --extract modal,llm (gpt-6.1-sol) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@dc1350a
- vs E006: Regelungen F2 0.405→0.556 (P 0.143→0.273, 11 statt 21 zitiert, R 0.750 gleich); Seiten F2 0.348→0.714 (P 0.103→0.437, R 0.849 gleich); 618 statt 2341 Anforderungen; LLM: 227 Batches, 2614 Kandidaten, 327 behalten, 2287 verworfen, 0 ohne Antwort
- Gegen expected.json (keine Plattform): Absatz-F2 0.145→0.599, Obergrenze Anforderungsebene 0.131→0.493. Varianten in experiments/runs/E008/options.txt (shall+llm Seiten 0.680). Falsch zitiert bleiben R3, R7, R23, R128 (alte Leuchten-Regelungen): Auswahl AP2
- Neue Bestmarke hinter Schalter, Tag best-main-pagef2-0.714. Reproduzierbar mit dem LLM-Cache auf Jonathans Rechner (out/cache/llm); auf anderem Rechner neue Antworten → neu messen

### 2026-10-24 14:55:50 +0200 | [run] E012 Richter strict auf --filters all --extract modal,llm | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@bd16d85
- Anforderungsebene (lokaler Richter strict, gpt-6.1-sol): P 0.129 R 0.421 F2 0.290 (80/190 getroffen, 618 eingereicht) vs E011-a modal,split F2 0.098 (P 0.025 R 0.384) und B0 0.060. Seiten 0.714, Regelungen 0.556 wie E008
- Engpässe: 32 von 190 Gold-Anforderungen sind UN R10, die B0-Auswahl wählt R10 nicht (AP2); Precision: 618 statt ~190, u. a. alte Leuchten-Regelungen R3/R7/R23/R128 (AP2) und Überzerlegung (6.10.5.1 → 5 statt 3)
- Neue Bestmarke Anforderungsebene, Tag best-main-reqf2-0.290. Vorschlag: Standard auf --filters all --extract modal,llm umstellen (Entscheidung Jonathan, wegen E001-Upload)

### 2026-10-24 15:00:02 +0200 | [change] AP4: LLM-Prompt übernimmt den Geltungsbereich der Regelung, zerlegt nur an echten Grenzen | Jonathan @ MacBook-Pro-von-Jonathan | main@6c9dad3 +lokale Änderungen
- Richter-Bericht E013 (lokal): häufigster Fehlgriff war verengter Geltungsbereich ('the rear lamp …' statt 'lamps'/'all light-signalling devices'/'devices marked TOP'), zweithäufigster Überzerlegung ('clearly legible and indelible' → 2 statt 1). Neue Schreibregeln: Geltungsbereich wörtlich, das Bauteil entscheidet nur OB ein Absatz gilt; trennen nur an (a)(b)(c), eigenständigen Sätzen, unabhängigen Grenzwerten; koordinierte Eigenschaften, Min/Max und Ausnahme+Regel zusammen; nichts aus Verweisen ergänzen. Beispiel im Prompt angepasst (weiter selbst geschrieben, R46)
- Vormessung mit Gold-Regelungen (Diagnose, nicht hochladbar), Richter strict: Anforderungen P 0.200→0.407, R 0.442→0.742, F2 0.356→0.637; Seiten 0.943→0.946. Die Regeln beschreiben den Stil der Referenz, nicht die Heckleuchte
- Geprüft: pytest tests/test_llmextract.py 3/3; offizielle Messung folgt

### 2026-10-24 15:00:17 +0200 | [run] E013 Diagnose LLM-Extraktion mit Gold-Regelungen, Richter strict | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@6c9dad3
- Anforderungen P 0.200 R 0.442 F2 0.356 (84/190), Seiten 0.943, Regelungen 1.000; Recall je Regelung: R10 4/32, R148 34/63, R150 24/39, R48 22/56
- Fehlgriffe (106) laut Richter-Begründung: ~42 anderer Geltungsbereich/Bedingung (meist auf 'rear lamp' verengt), 26 überzerlegt, 25 Inhalt fehlt. Gold-Wissen, nicht hochladen. Beleg experiments/runs/E013/ (nur Kennzahlen)

### 2026-10-24 15:04:01 +0200 | [run] E014 Prompt v2, --filters all --extract modal,llm, Richter strict | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@8a17957
- vs E012: Anforderungen P 0.129→0.238, R 0.421→0.668 (127/190), F2 0.290→0.491; Seiten 0.714→0.717; Regelungen 0.556 gleich; 533 Anforderungen
- Rest-Recall: UN R10 fehlt in der B0-Auswahl (32 Gold-Anforderungen, AP2); Rest-Precision u. a. alte Leuchten-Regelungen R3/R7/R23/R128 (AP2). Tag best-main-reqf2-0.491. Beleg experiments/runs/E014/
- Vorschlag an Jonathan: Standard auf --filters all --extract modal,llm umstellen (bessere Messung auf allen drei Ebenen); Kosten ungecacht ~7 min für 227 Aufrufe

### 2026-10-24 15:04:40 +0200 | [run] E015 Diagnose Prompt v2 mit Gold-Regelungen, Richter strict | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@0b7af93
- vs E013: Anforderungen P 0.200→0.407, R 0.442→0.742 (141/190), F2 0.356→0.637; Seiten 0.946; Recall je Regelung R10 14/32, R148 54/63, R150 33/39, R48 40/56
- Gold-Wissen, nicht hochladen. Beleg experiments/runs/E015/

### 2026-10-24 15:04:40 +0200 | [handoff] B-Arbeit Stand 15:10, Übergabe an Omar | Jonathan @ MacBook-Pro-von-Jonathan | main@0b7af93 +lokale Änderungen
- Stand: Bestmarke E014 = run --filters all --extract modal,llm: Anforderungen 0.491 (Richter strict), Seiten 0.717, Regelungen 0.556; Diagnose mit Gold-Regelungen E015: Anforderungen 0.637. Code B: certreq/pdf.py (Gliederung), relevance.py (Regelfilter), extract.py (Optionen), llmextract.py (LLM je Absatz, Prompt v2). Standard ohne Schalter bleibt B0, Umstellung schlägt B vor, entscheidet Jonathan
- Nächster Schritt B: (1) R10 bei perfekter Auswahl nur 14/32: Prüfpegel/Prüfbedingungen als Einzelpflichten (R10 6.9.1 hat 10 Gold-Anforderungen), Fehlgriffe in out/E015.judge.json lesen (lokal, enthält Gold-Texte, nie committen). (2) R48 40/56. (3) Tabellen. Jede Prompt-Änderung zuerst mit --regs Gold + eval --judge strict messen (~2 min), dann offiziell mit B0-Auswahl
- Fallen: LLM-Antworten liegen im Cache out/cache/llm auf Jonathans Rechner; auf Omars Rechner erzeugt derselbe Commit neue Antworten (Kosten ~7 min, Werte können leicht abweichen) → dort neu messen. Prompt-Beispiel nie aus dem Dev-Gold nehmen (verfälscht die Messung). Claims 'AP3-Rest …' und 'AP4 LLM-Extraktion …' stehen auf Jonathan: Omar per scripts/claim übernehmen
### 2026-10-24 15:06:41 +0200 | [change] AP2: Regelungsauswahl per LLM (--select llm) | Jonathan @ MacBook-Pro-von-Jonathan | main@61430f9 +lokale Änderungen
- Steckbrief je Regelung aus der base-PDF: Titel, Einleitung (enthält Konsolidierung, z. B. R148 'combines … Nos. 4, 6, 7, 23 …'), Geltungsbereich; ganzer Katalog ~10k Tokens in einem Aufruf
- gpt-6.1-sol (effort high) wählt nach allgemeinen Prinzipien (Bauteil, Anbau, querschnittlich, konsolidiert statt ersetzt, Fahrzeugklasse) mit Rolle + Begründung, dazu verworfene Kandidaten; alles in .meta.json 'selection' (für die Demo)
- Standard bleibt b0, bis die Anforderungsebene besser gemessen ist
- Vormessung dev (Regelungsebene, ohne Cache, 3 Läufe identisch): 7 gewählt, alle 4 Gold-Regelungen inkl. UN R10, R7/R23/R3 mit Begründung 'konsolidiert' verworfen; P 0.57 R 1.00 F2 0.870 (B0 0.405); Extras R26, R13H, R42
- Tests: 3 neue (Steckbrief, Antwortauswertung, Modi), gesamt 48 grün

### 2026-10-24 15:08:41 +0200 | [run] E016-a: --select llm + beste Extraktion | Jonathan @ MacBook-Pro-von-Jonathan | main@39b1077 +lokale Änderungen
- Stand main@39b1077 (pull-first: zählt), Richter strict
- Regelungen P 0.571 R 1.000 F2 0.870; Seiten P 0.697 R 1.000 F2 0.920; Anforderungen P 0.375 R 0.742 F2 0.621 (141/190, 376 eingereicht)
- vs E014 (B0-Auswahl) 0.491; Gold-Regelungen-Diagnose E015 0.637 → Auswahl nahezu ausgereizt; Recall je Regelung R10 14/32, R148 54/63, R150 33/39, R48 40/56
- Tag best-main-reqf2-0.621, Beleg experiments/runs/E016-a/

### 2026-10-24 15:08:41 +0200 | [decision] --select llm ist Standard | Jonathan @ MacBook-Pro-von-Jonathan | main@39b1077 +lokale Änderungen
- auf allen drei Ebenen besser gemessen (E016-a vs E014); b0 bleibt per --select b0 verfügbar (Referenz E001)
- Filter/Extraktion-Standards sind B's Entscheidung, Empfehlung in STATUS

### 2026-10-24 15:24:33 +0200 | [change] AP5: Explosionszeichnung lesen (certreq/vision.py, --vision off|on|only) | Jonathan @ MacBook-Pro-von-Jonathan | main@5eb2652 +lokale Änderungen
- llm.ask_json kann Bilder (data-URL, detail high); Cache-Schlüssel enthält nur den Bild-Hash, Textaufrufe behalten ihre alten Schlüssel (geprüft: Auswahl weiter Cache-Treffer)
- vision.describe: Produkt, Lage am Fahrzeug, Teile mit Funktion/Technik/Bildbeleg, Unsicherheiten; nennt bewusst keine Regelungen. on = an Spec anhängen, only = nur Zeichnung (Demo R3); Standard off bis gemessen
- Vorprüfung dev (Patentzeichnung ohne Beschriftung): nur Zeichnung → 'Außenleuchte, vermutlich Heck-Kombinationsleuchte', Lichtscheibe, LED-artige Felder, Funktionen offen; mit Spec → Rückfahrleuchte zugeordnet; Rückstrahler in beiden Fällen nicht erkennbar und als unsicher markiert
- Tests: 2 neue (Bild im Aufruf + Cache, Modi), gesamt 50 grün

### 2026-10-24 15:33:57 +0200 | [run] E017-a/E018-a: Explosionszeichnung (AP5) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@fa3816e
- nur Zeichnung (--vision only): Anforderungen F2 0.417 (P 0.205 R 0.563), Regelungen 0.682, Seiten 0.654; R150 0/39, weil der Rückstrahler auf der Patentzeichnung nicht erkennbar ist, R53 falsch gewählt (Fahrzeugklasse fehlt im Bild)
- Spec + Zeichnung (--vision on): Anforderungen 0.605 vs 0.621 nur Spec → kein Gewinn
- Belege experiments/runs/E017-a, E018-a

### 2026-10-24 15:38:28 +0200 | [run] E019-a: Streuung der LLM-Pipeline | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@19423b2
- E016-a-Konfiguration identisch ohne LLM-Cache: Anforderungen 0.621 → 0.602, Seiten 0.920 → 0.895, Auswahl identisch
- Schluss: ±0.02 je Einzellauf, Unterschiede < ~0.03 nicht belastbar; E018-a (Zeichnung + Spec, 0.605) damit ohne Befund
- Beleg experiments/runs/E019-a

### 2026-10-24 15:38:28 +0200 | [decision] --vision auto ist Standard | Jonathan @ MacBook-Pro-von-Jonathan | main@19423b2 +lokale Änderungen
- mit Spec: Zeichnung ignoriert (E016-a; E018-a ohne Gewinn); ohne Spec: nur Zeichnung (E017-a, F2 0.417) → Demo läuft mit reinem Zeichnungsordner ohne Schalter (geprüft)
- Sonntag: bei dünner Held-out-Spec --vision on per Upload testen

### 2026-10-24 15:41:06 +0200 | [change] load_case ignoriert README-Dateien; synthetische Stoßfänger-Spec | Jonathan @ MacBook-Pro-von-Jonathan | main@88fee6d +lokale Änderungen
- Fund: load_case las jede .md/.txt im Fall-Ordner als Spezifikation; eine README im Held-out-Ordner wäre als Spec ans LLM gegangen. Jetzt übersprungen (Test test_case_ignoriert_readme)
- experiments/synthetic/front-bumper/spec.md: selbst geschriebene M1-Frontstoßfänger-Spec im Aufbau der Dev-Spec (Fascia, Träger, Absorber, Nebelscheinwerfer LED, Parksensoren, Radarhalter, Kennzeichenhalter), nur für Robustheit/Laufzeit, keine Musterlösung

### 2026-10-24 15:46:17 +0200 | [finding] Robustheit: Pipeline am synthetischen Frontstoßfänger | Jonathan @ MacBook-Pro-von-Jonathan | main@ff9e843 +lokale Änderungen
- läuft fehlerfrei, validate ok, 231 s und ~435k Tokens für einen neuen Fall (146 LLM-Aufrufe) → Sonntag: erster Upload ~10 min nach Release realistisch
- Auswahl (12): Kern plausibel R42, R26, R127, R149 (R19 als konsolidiert verworfen), R48, R10; schwach: bedingte Picks R128/R152, Fahrzeugebene R94/R137/R155 (R155 23, R128 32 Anforderungen)
- GTR 9: Extraktion zitiert den Begründungsteil (S. 4/15/18); verbindlicher Text erst ab S. 71 → Aufgabe für B in STATUS
- Beleg experiments/synthetic/front-bumper-run.json (Zusammenfassung, keine Messung)

### 2026-10-24 15:49:01 +0200 | [change] AP2b: --select llm2 verwirft Annahmen und reine Fahrzeugebene | Jonathan @ MacBook-Pro-von-Jonathan | main@3467af0 +lokale Änderungen
- Modell gibt je Regelung trigger, stated_in_spec, requirement_locus (component/installation/vehicle-only) an; Code verwirft stated_in_spec=false und vehicle-only, mit Begründung in .meta.json 'selection'
- Anlass: synthetischer Stoßfänger wählte R128/R152 ('If …') und R94/R137/R155 (Fahrzeugebene)
- llm-Modus unverändert (Cache-Treffer geprüft); Tests: 1 neuer, gesamt 52 grün

### 2026-10-24 13:50:01 +0000 | [change] AP6 Demo v2: 3D-App für jeden Fall (demo/app, demo/web, demo/prepare.py, demo/run) | Amiad @ claude | main@ff99d4b +lokale Änderungen
- Helle 3D-Demo mit drei Szenen (Lauf: Ring der 56 Regelungen; Zeichnung: Explosion der Fallzeichnung + Anforderungen je Bauteil; Beleg: Anforderung → Regelung → Absatz → markierte PDF-Seite mit Lupe). Allgemein statt auf die Heckleuchte zugeschnitten: Zeichnung wird im Browser per Zusammenhangsanalyse in Teile zerlegt, Bauteile aus spec.md, Zuordnung Anforderung → Bauteil per Wortabgleich, sonst Gesamtgerät. prepare.py rendert die zitierten Seiten (Graustufen-JPEG, max. 150) und bestimmt die Zeilen des zitierten Absatzes. Gebaute App liegt als demo/web/index.html im Repo (ohne Falldaten), Ausgabe mit Paketdaten nur in demo/dist/ (gitignored). Am Sonntag kein Node nötig: demo/run <fall> = certreq run + prepare. Doku: demo/README.md.
- Geprüft: pytest 55 grün (neu tests/test_prepare.py: Spec-Parser, Zuordnung). prepare.py auf expected.json des Dev-Falls: 190 Anforderungen, 53 Seiten, 189 markiert, 11 s, data.js 9,6 MB; auf out/dev-rear-lamp.json (3624 Anf.): 150 Seiten, 34 s, 31 MB. UI per Playwright (Software-Rendering, ?lite) in 5 Varianten ohne Fehler: Dev komplett, ohne Zeichnung, ohne Spec, ohne beides, echter Pipeline-Lauf (21 Regelungen). Grenzen: Zeichnungsteile nicht mit Spec-Bauteilen verknüpft; Dev-Zeichnung zerfällt in 2 statt 3 Teile; auf echter GPU noch nicht vom Agenten gesehen.

### 2026-10-24 13:50:51 +0000 | [handoff] AP6 Demo v2 gepusht (main@fd0820a) | Amiad @ claude | main@fd0820a
- Stand: demo/run <fall> erzeugt die Demo end-to-end; demo/dist/index.html öffnen. Alles in demo/README.md.
- Nächster Schritt C: Begründungen je Regelung (.meta.json selection) in Szene 1 zeigen; Pitch AP9 vorbereiten; Demo auf echter GPU prüfen.
- Fallen: demo/dist/ nie committen (Paketdaten). Nach Änderungen an demo/app neu bauen und dist/index.html nach demo/web/ kopieren, sonst zeigt prepare.py die alte App. data.js beim Pipeline-Lauf ~30 MB (max. 150 Seiten).
### 2026-10-24 15:52:23 +0200 | [run] E020-a: --select llm2 | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@fd0820a
- Regelungen P 0.667 R 1.000 F2 0.909; Seiten 0.936; Anforderungen P 0.392 R 0.742 F2 0.629 (141/190, 360 eingereicht)
- vs E016-a 0.621: nur die 16 R13H-Anforderungen fehlen, Extraktion sonst identisch (Cache) → Unterschied ohne Streuung
- Auswahl 3× (dev) bzw. 2× (Stoßfänger) ohne Cache identisch; Tag best-main-reqf2-0.629; Beleg experiments/runs/E020-a

### 2026-10-24 15:52:23 +0200 | [decision] --select llm2 ist Standard | Jonathan @ MacBook-Pro-von-Jonathan | main@fd0820a +lokale Änderungen
- besser auf dev (alle Ebenen, gleicher Recall) und am synthetischen Stoßfänger plausibler (6 spekulative Regelungen raus, darunter R155 mit 23 und R128 mit 32 Anforderungen)
- llm bleibt per --select llm verfügbar

### 2026-10-24 15:57:26 +0200 | [change] certreq/upload.py: Upload-Dateien aus gemessenen Läufen | Jonathan @ MacBook-Pro-von-Jonathan | main@574b70d +lokale Änderungen
- nimmt experiments/runs/<ID>/submission.json.gz unverändert, setzt nur die echte team_id, schreibt out/upload/<ID>-<case>.json, validiert mit dem offiziellen validate.py (Sub-Goal mit requirements_old.json); zeigt die lokalen Werte zum Vergleich
- Probelauf mit team-TEST: E020-a, E008-a, E003-am alle gültig; Tests 2 neu, gesamt 57 grün
- Zweck: Plattformwert ↔ lokaler Richter 1:1 vergleichbar; Sonntag: beste Held-out-Datei zuletzt exakt erneut hochladen

### 2026-10-24 16:03:38 +0200 | [change] Teamname BarelyLegal in STATUS | Jonathan @ MacBook-Pro-von-Jonathan | main@4342e4f +lokale Änderungen
- Team-ID noch offen: erscheint nach der Registrierung auf der Plattform (Format laut expected.json/README team-NN); Upload-Dateien entstehen danach mit certreq.upload

### 2026-10-24 16:10:32 +0200 | [change] Team-ID team-12 als Standard (certreq/submission.py TEAM_ID) | Jonathan @ MacBook-Pro-von-Jonathan | main@4cca05a +lokale Änderungen
- run und certreq.upload setzen team-12 ohne Schalter; Override --team-id / CERTIVITY_TEAM_ID
- Upload-Dateien erzeugt und validiert: out/upload/E020-a-dev-rear-lamp.json (360), E008-a-dev-rear-lamp.json (3642), E003-am-subgoal-dev.json (25 Änderungen)
- Hinweis an C in STATUS: subgoal.py hat noch eigenen Platzhalter

### 2026-10-24 14:13:06 +0000 | [change] AP6 Werkbank: lokaler Server + Produkt-UI (demo/server.py, demo/werkbank, demo/web/werkbank.html) | Amiad @ claude | main@ea51a6c +lokale Änderungen
- Das eigentliche Produkt neben der 3D-Präsentation. demo/werkbank startet einen lokalen Server (Standardbibliothek + pymupdf, nur 127.0.0.1) und öffnet die Werkbank: Prüfungen (Spec/Zeichnung hochladen, certreq run als Unterprozess starten, Modus Bestmarke oder Schnell/B0, Liste aller Läufe inkl. experiments/runs), Anforderungen (Regelungs-Rad als Filter, virtuelle Liste, Beleg mit live gerenderter PDF-Seite und markiertem Absatz, Belegfaden Zeile→Stelle, Review per Tastatur A/X/U/N, Export Abgabe-JSON ohne Verworfene + CSV), Auswahl (56 Regelungen auf Kreis, Begründungen aus .meta.json selection), Vergleich (Sub-Goal mit Wort-Diff und lokaler Bewertung), Befehlspalette Strg+K. /present/<lauf>/ liefert die 3D-Präsentation mit Live-Seiten. Doku: demo/README.md.
- Geprüft: pytest 6 neue/angepasste Tests grün (tests/test_server.py, test_prepare.py); Server-Endpunkte per curl (state, run, hits, page, subgoal, present). Schnell-Lauf (B0) auf dev über den Server: fertig nach ~20 s, 3642 Anforderungen. Sub-Goal dev über die Werkbank: 20 Änderungen, lokal F2 0.862 (wie E003-am-Methode). UI per Playwright: alle vier Ansichten + Palette ohne Konsolenfehler (Lauf E016-a). Nicht geprüft: Modus Bestmarke (kein LLM-Key auf diesem Rechner).

### 2026-10-24 14:19:32 +0000 | [decision] run ohne Schalter = Bestmarke E020-a (--filters all --extract modal,llm Standard) | Homsianer @ vm | main@0a5261e +lokale Änderungen
- certreq/__main__.py: Standard --filters all, --extract modal,llm; none schaltet weiter auf B0. Begründung: E020-a/E016-a/E014 auf allen drei Ebenen besser (Anforderungen 0.629 vs B0 0.060, modal,split 0.098); STATUS-Schritte 4/5 waren B's Entscheidung
- demo/server.py MODES (abgesprochen über Homsianer, Claim): best = [] (Standard = Bestmarke, damit jetzt auch --select llm2 statt llm), fast = --select b0 --filters none --extract none, sonst bräuchte der Fallback ohne Key nach der Umstellung einen Key
- Geprüft: pytest 61/61 (neu test_run_defaults_are_the_measured_best); fast-Modus ohne Key 1,9 s, 3642 Anforderungen, bytegleich zu E008-a; run ohne Schalter ohne Key bricht mit klarer Meldung ab. Keine neue Messung nötig: Standard = Konfiguration von E020-a (meta.json command)

### 2026-10-24 16:22:47 +0200 | [run] Plattform-Uploads Worked example (team-12) | Jonathan @ MacBook-Pro-von-Jonathan | main@62c5bf4 +lokale Änderungen
- E020-a: Anforderungen P 0.428 R 0.811 F2 0.687 (154/190); Seiten P 0.746 R 1.000, Regelungen P 0.667 R 1.000 = lokal exakt
- E008-a (B0): Anforderungen P 0.017 R 0.326 F2 0.070 (62/190); Seiten/Regelungen = lokal
- E003-am (Sub-Goal): Flag-Recall 0.792, Flag-Precision 0.760, Change accuracy 0.889
- Belege experiments/runs/{E020-a,E008-a,E003-am}/platform.json

### 2026-10-24 16:22:47 +0200 | [finding] Lokaler Richter gegen Plattform geeicht (AP10-K2) | Jonathan @ MacBook-Pro-von-Jonathan | main@62c5bf4 +lokale Änderungen
- lenient sagt die Plattform für Pipeline-Ausgaben vorher (E020-a 153 vs 154 Treffer, F2 0.683 vs 0.687), strict ist Untergrenze (141); bei Absätzen überschätzt lenient (B0 84 vs 62). Seitenfenster ±3 ändert nichts
- Konsequenz: Messungen mit --judge lenient als Plattform-Prognose, strict zusätzlich als Untergrenze; Seiten/Regelungen lokal = Plattform
### 2026-10-24 14:22:49 +0000 | [change] AP3/AP4: GTR-Teil I (Begründung) erkennen und per Filter rationale verwerfen | Homsianer @ vm | main@62c5bf4 +lokale Änderungen
- pdf.py: Zeile 'I. Statement of technical rationale and justification' bzw. 'II. Text of the Regulation' schaltet um; Absätze aus Teil I tragen RATIONALE_TITLE als äußersten Kontext (Labels unverändert). relevance.py: neuer Filter rationale (in --filters all, also Standard), admin erkennt zusätzlich 'APPLICATION / SCOPE' (GTR-Schreibweise von Scope)
- Anlass: Robustheitslauf am synthetischen Stoßfänger zitierte GTR 9 S. 4/15/18 (Begründung). GTR 9: 137 Absätze in Teil I (S. 1–58), 298 in Teil II (ab S. 71); modal-Kandidaten nach Filtern 214 → 176, davon vor S. 71: 38 → 0
- Geprüft: pytest 62/62 (neu test_gtr_rationale_part_is_marked_and_filtered); alter gegen neuen Parser über alle 94 PDFs inkl. Sub-Goal: nur UN_GTR_9_base.pdf anders; alte gegen neue Filter (Dev- und Stoßfänger-Spec, alle 56 Regelungen): nur GTR 9 anders → E020-a/dev unverändert, keine neue Dev-Messung nötig

### 2026-10-24 14:27:49 +0000 | [change] AP3: Anhänge zum Haupttext (Appendix 1–8 vor Annex 1) bekommen eigene Labels | Homsianer @ vm | main@63c5416 +lokale Änderungen
- pdf.py: Zeile 'Appendix N <Titel>' vor Annex 1, der Reihe nach ab 1, Titel großgeschrieben → Label 'Appendix N <nr>', Titel als Kontext. Vorher liefen sie als Haupttext weiter: R10 Appendix 1 (Normenliste 1.–23.) kollidierte mit '1. Scope' usw., und '23.' reichte über S. 29–35 (Grenzwertformeln der Appendices 2–7); daraus kamen in E020-a 6 freie (nicht zugeordnete) R10-Anforderungen mit Label 23, S. 29
- Betroffen (alt gegen neu, alle 94 PDFs): R10 base/latest (doppelte Labels 34→12), R103 (6→1, Info-Dokument → admin), R40 latest (38→25), R49 (Absatz 14 endet S. 22 statt 28). Dev-Kandidaten R10 (--filters all, modal): '23' (S. 29–35) raus, 'Appendix 8 1' (künstliche Netzwerke) neu, 8 Labels 'n' → 'Appendix 8 n'; sonst gleich
- Geprüft: pytest 63/63 (neu test_main_text_appendices_get_own_labels; test_paragraph_labels_match_reference weiter 121/121). Anforderungsebene ungemessen (kein LLM-Key in dieser Session): die geänderten R10-Batches brauchen neue LLM-Antworten → Messung E020-Konfiguration mit Key offen

### 2026-10-24 14:29:47 +0000 | [finding] E020-a Fehleranalyse (Richter strict): Lücke liegt in Zerlegung/Formulierung, nicht in den Kandidaten | Homsianer @ vm | gemessen auf main@fd0820a
- Kandidaten: R10 15 von 15, R48 34 von 35 Gold-Absätzen sind nach --filters all + modal Kandidaten (R48 6.14.5 ohne Pflichtwort, 2 Gold). Fehlend je Regelung: R10 18 (12 mit freier eigener Ausgabe im selben Absatz, 6 Absatz ohne Ausgabe), R48 16 (10/3/3 bereits anderweitig zugeordnet), R148 9, R150 6. Frei (FP) 219 von 360, davon R48 §5 'General specifications' 45 von 55
- Muster: (1) Aufzählung im selben Satz zerlegt: R48 5.26.1 (7 Umweltbedingungen → 7), 5.9.2 (3), R10 6.5.2.1/6.6.2.1 (Grenzwert über zwei Frequenzbänder in einem Satz → 2; Gold 1). (2) Tabellen: R10 6.8.2.1 Tabelle mit alternativen Prüfmethoden → 14 Zeilen-Anforderungen, Gold verweist auf die Tabelle (2); R10 6.9.1 Pflicht-Prüfpulse je Zeile wie Gold, aber Spalte 'nicht immunitätsrelevant' fehlt (8 strict-Fehlgriffe). (3) Ausnahmen 'shall be deemed to comply' (R10 6.10.1, 6.10.5) verworfen. (4) Prüfparameter (Annex 9 3.1 Frequenzbereich/Modulation, 4 Gold) verworfen, Prüfaufbau ('ESA in normal operation mode', 4 FP) behalten. (5) REESS-Lademodus-Abschnitte (R10 7.x, Annex 21/22) für eine Leuchte ohne Ladefunktion behalten
- Beleg: lokale Auswertung von experiments/runs/E020-a/score.json (matches) gegen expected.json; Gold-Texte nur lokal, nicht committet. Plattform zählt mehr Treffer (154 vs 141 strict), Muster (1)/(2) kosten dort vor allem Precision
### 2026-10-24 16:31:26 +0200 | [finding] Fehleranalyse E020-a: wo die Punkte liegen | Jonathan @ MacBook-Pro-von-Jonathan | main@87ffc6c +lokale Änderungen
- 207 Treffer-lose: 139 aus Absätzen, die das Gold nicht nimmt (R48 General specs 60, R48 Individual 15, R148 14, R150 Prüfungen 20, R10 Prüfverfahren ~20), 54 in Gold-Absätzen (39 überzählig), 14 aus R26/R42
- Gold lässt in R48 'Presence'-Absätze, nicht vorhandene Varianten (S3/S4, beweglich, versenkbar, asymmetrisch, Anhänger) und Verwaltung weg → Prinzip Anwendbarkeit je Absatz (wie llm2)
- 37 Fehlende: R10 17, R48 11, R150 5, R148 4; 13 ohne jede Extraktion aus dem Gold-Absatz
- Priorisierte Liste in docs/PLAN.md 'Verbesserungen nach Punkten', Beleg experiments/runs/E020-a/analyse.json

### 2026-10-24 16:31:26 +0200 | [change] scripts/log: Zeitstempel immer Berliner Zeit | Jonathan @ MacBook-Pro-von-Jonathan | main@87ffc6c +lokale Änderungen
- Anlass: UTC-Einträge von VM/Cloud wurden im Sessionstart falsch sortiert
- selftest 143/143 auf macOS und Debian (neue Prüfung mit TZ=UTC)

### 2026-10-24 14:31:44 +0000 | [change] AP4: Zusatzregeln für den LLM-Prompt hinter Schaltern (--extract …,lists,tables,exempt,tests,modes) | Homsianer @ vm | main@2be1f20 +lokale Änderungen
- llmextract.RULES aus der Fehleranalyse E020-a: lists = eine Aufzählung im Satz bzw. derselbe Grenzwert über benachbarte Bereiche bleibt eine Anforderung; tables = Tabellen mit Alternativen als eine Anforderung mit Tabellenverweis, Pflichtzeilen je Zeile mit allen Spalten; exempt = 'deemed to comply'/'need not be tested' behalten; tests = Prüfparameter (Frequenz, Modulation, Pegel, Dauer, Temperatur, Aufprallgeschwindigkeit) behalten, Prüfaufbau nicht; modes = Absätze nur für Betriebsarten/Varianten, die die Spec nicht hat, verwerfen. Beispiele allgemein formuliert, keine Gold-Texte
- Standard unverändert (modal,llm ohne Regeln): Prompt bytegleich zu v2 (Test), gecachte Antworten bleiben gültig. Regeln ohne llm → Fehler. Reihenfolge der Regeln im Prompt fest. meta.json llm.rules nennt die aktiven Regeln
- Geprüft: pytest 65/65 (2 neue, ohne Netz). Ungemessen (kein Key in dieser Session): Messplan im [handoff]

### 2026-10-24 16:32:19 +0200 | [handoff] Homsianer (B), Cloud-Session ohne LLM-Key | Homsianer @ vm | main@033acb6 +lokale Änderungen
- Stand: gepusht auf main: run-Standard = E020-a (Demo fast weiter ohne Key), Filter rationale (GTR 9 Teil I), Parser-Fix Appendices zum Haupttext (R10), Prompt-Zusatzregeln lists/tables/exempt/tests/modes hinter --extract, Fehleranalyse E020-a als [finding]. Alles offline geprüft (pytest 65/65, Parser-Diff über alle 94 PDFs), Anforderungsebene ungemessen
- Nächster Schritt (mit Key, zuerst scripts/pull-first): E021 Referenz auf aktuellem main: .venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/dev-rear-lamp --out out/E021.json && .venv/bin/python -m certreq eval out/E021.json --judge lenient --record E021-hs (zusätzlich --judge strict ohne --record). E022 alle Regeln: run vendor/industrial-ai-hackathon/cases/dev-rear-lamp --extract modal,llm,lists,tables,exempt,tests,modes --out out/E022.json, eval wie oben (--record E022-hs). Besser als E021 um mehr als die Streuung (±0.02) → Regeln einzeln messen und den Standard umstellen; sonst je Regelung (recall_by_regulation, freie Ausgaben) prüfen, welche Regel schadet
- Fallen: Parser-Fix ändert R10-Kandidaten → R10-Batches sind auch mit v2 keine Cache-Treffer mehr (E021 nötig, bevor man gegen E020-a vergleicht). Regeln ändern den System-Prompt → alle Batches neu (~7 min, ~435k Tokens je Lauf). Gold-Texte nur lokal (Auswertung über experiments/runs/<ID>/score.json matches + expected.json), nie committen. Jonathans alte B-Claims (AP3-Rest, AP4 LLM-Extraktion) kann nur er entfernen; Homsianers Claim AP3-Rest + AP4 bleibt bewusst stehen

### 2026-10-24 16:42:16 +0200 | [decision] Werkbank folgt der Pipeline-Standardkonfiguration | Amiad @ claude | main@72dbeab +lokale Änderungen
- Bitte an A/B in STATUS: beste Konfiguration als Standard von certreq run setzen und melden; dann ruft die Werkbank certreq run ohne Schalter auf. Bis dahin fest E016-a-Schalter in demo/server.py MODES.
### 2026-10-24 16:43:07 +0200 | [run] E021-hs/E022-hs: Homsianers Messplan ausgeführt (mit LLM-Key) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@72dbeab
- E021-hs (aktueller main, Parser-Fix + rationale): Anforderungen lenient 0.704 (157/190), strict 0.650; Seiten 0.950; R10 19/32
- E022-hs (+ lists,tables,exempt,tests,modes): lenient 0.743 (P 0.478 R 0.863, 164/190), strict 0.671; R10 29/32, R48 45→41; Seiten 0.927
- Schluss: Regeln helfen mehr als die Streuung; nächster Schritt laut Plan Regeln einzeln messen (R48-Verlust), dann Standard. Tag best-main-reqf2lenient-0.743; Belege experiments/runs/E021-hs, E022-hs

### 2026-10-24 16:57:43 +0200 | [blocker] API-Key war in .env auf main committet (d3d3b7b, a87a74f), Datei entfernt | Homsianer @ vm | main@a87a74f +lokale Änderungen
- Homsianer hat über GitHub eine .env mit einem Anthropic-Key (sk-ant…, zuerst als OPENAI_API_KEY, dann ANTHROPIC_API_KEY) auf main angelegt. Datei jetzt aus dem Repo gelöscht; die Historie behält den Key (kein Force-Push nach AGENTS.md §3) → der Key gilt als offengelegt und muss in der Anthropic-Konsole widerrufen werden
- Keys nur über die Umgebungseinstellungen der Session (Network secrets/Umgebungsvariable) oder lokal in .env.local (gitignored), nie über GitHub. Die Pipeline nutzt OpenAI (OPENAI_API_KEY), ein Anthropic-Key funktioniert mit certreq/llm.py nicht

### 2026-10-24 17:05:35 +0200 | [finding] E021-hs vs E022-hs ohne LLM: wo die Regeln R48/R148 kosten (Hypothesen für Leave-one-out) | Homsianer @ vm | main@eacdf8b
- R48 −4 (45→41) bei 132→104 Ausgaben: verloren 5.7.2.1 (Einzelleuchte aus mehreren Teilen), 6.10.7 (Leuchte reziprok mit Fahrtrichtungsanzeiger kombiniert), 6.7.4.2.1 (optionale Leuchten) – in E022 keine Ausgabe dort → Verdacht 'modes' (Variante 'nicht in der Spec' zu eng); 6.4.4.2 Ausnahme (Geländefahrzeuge) abgeschnitten, Gold behält sie. R148 −1: 6.1.3 in 6 Tabellenzeilen zerlegt, Gold = 1 Anforderung mit Tabellenverweis → Verdacht 'tables' (Mindestwerte-Tabelle als 'jede Zeile Pflicht' gelesen). R150 61→85 Ausgaben für +2 Treffer → eine Regel bläht R150 auf (Verdacht 'tests' oder 'exempt'). R10 56→47 Ausgaben, 19→29 Treffer. Reihenfolge Leave-one-out daher: ohne modes, ohne tables, ohne tests, ohne exempt, ohne lists.
- Skript: experiments/runs/E021-hs|E022-hs score.json (judge.matches) + submission.json.gz gegen expected.json, Gold-Texte nur lokal angesehen. Streuung ±0.02 (Einzelabsätze können auch Zufall sein).

### 2026-10-24 17:06:33 +0200 | [change] LLM: Anthropic-Zugang hinter Schalter CERTREQ_PROVIDER=anthropic (Standard bleibt OpenAI) | Homsianer @ vm | main@182d79b +lokale Änderungen
- Neu certreq/llm_anthropic.py: übersetzt die OpenAI-förmige Anfrage von llm.ask_json (System → system, data-URL-Bilder → base64-Bildblöcke, JSON-Schema → Structured Output output_config.format, effort → output_config.effort, ohne effort medium); claude-opus-5-5 (CERTREQ_ANTHROPIC_MODEL), Streaming, max_tokens 32000, serverseitiger Ersatz bei Ablehnung (fallbacks=default, gezählt in usage.fallbacks). llm.py: provider(), model_name bildet gpt-Namen der Aufrufer auf das Claude-Modell ab, _call verzweigt, _check für beide; judge.py meldet das tatsächlich genutzte Richter-Modell. requirements.txt +anthropic
- Anlass: Homsianer hat nur einen Anthropic-Key. Ohne Schalter ist alles wie vorher (Cache-Schlüssel enthalten das Modell, gpt-Antworten bleiben gültig). Messungen mit Claude sind eine eigene Reihe (Auswahl, Extraktion und Richter mit Claude), nicht mit gpt-6.1-sol-Bestmarken vergleichbar
- Geprüft: pytest 68/68 (3 neue ohne Netz; conftest setzt in Tests den Standardanbieter, auch wenn .env.local anthropic sagt); Live-Check python -m certreq.llm mit Anthropic: Key OK, 13 Modelle, Testaufruf ok in 2,7 s

### 2026-10-24 17:10:37 +0200 | [run] AP10-K3-c: Claude-Richter gegen Plattform geeicht (E020-a-Abgabe) | Homsianer @ vm | gemessen auf main@9886bfe
- Gleiche Abgabe wie E020-a-P (360 Anforderungen, gpt-Ausgabe), Richter claude-opus-5-5: strict 152 Treffer F2 0.679, lenient 165 F2 0.737; Plattform 154 F2 0.687; gpt lenient 153, gpt strict 141
- Schluss: für Claude-Messreihen strict als Plattform-Prognose nehmen, lenient als Obergrenze. Kosten je Richter-Lauf ~442k/22k Tokens (190 Aufrufe, ~70 s)
