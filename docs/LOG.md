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

### 2026-10-24 17:15:47 +0200 | [run] E023-hs-c: Referenz der Claude-Reihe (Standard mit CERTREQ_PROVIDER=anthropic) | Homsianer @ vm | gemessen auf main@ca4c59f
- Richter claude-opus-5-5 strict (= Plattform-Prognose, AP10-K3-c): Anforderungen P 0.468 R 0.795 F2 0.697 (151/190, 323 eingereicht), lenient 0.752; Seiten 0.942, Regelungen 0.952 (R148, R150, R48, R10, R26; kein R42)
- Recall je Regelung R10 19/32, R148 57/63, R150 35/39, R48 40/56. 100 s, 63 Aufrufe, 254k Eingabe-/63k Ausgabe-Tokens. Beleg experiments/runs/E023-hs-c

### 2026-10-24 17:32:52 +0200 | [run] E024-hs-c…E029-hs-c: Prompt-Regeln mit Claude, gesamt und je eine weggelassen | Homsianer @ vm | gemessen auf main@8c201e1
- Richter claude-opus-5-5 strict (Plattform-Prognose, AP10-K3-c), Referenz E023-hs-c 0.697 (151/190, 323): alle 5 Regeln 0.721 (161, 356); ohne modes 0.695 (159, 384); ohne tables 0.690 (153, 349; R10 29→22); ohne tests 0.719 (154, 311); ohne exempt 0.722 (159, 341); ohne lists 0.709 (160, 368)
- Schluss: modes und tables tragen den Gewinn (je ~−0.03 ohne), lists leicht, tests/exempt neutral. Der Verdacht aus dem Vergleich E021/E022 (modes kostet R48) bestätigt sich mit Claude nicht (R48 40 mit, 39 ohne modes). Bündel in beiden Modellreihen besser: gpt E021-hs→E022-hs strict +0.021/lenient +0.039, Claude E023-hs-c→E024-hs-c strict +0.024
- Kosten je Lauf ~260k Eingabe-/66k Ausgabe-Tokens (62 Aufrufe, ~85 s) + Richter ~440k/22k. Belege experiments/runs/E024-hs-c … E029-hs-c

### 2026-10-24 17:49:16 +0200 | [decision] run ohne Schalter = E022-hs: --extract modal,llm,lists,tables,exempt,tests,modes | Homsianer @ vm | main@4d69ad8 +lokale Änderungen
- Begründung: Bündel in beiden Modellreihen besser (gpt E021-hs→E022-hs lenient 0.704→0.743, strict 0.650→0.671; Claude E023-hs-c→E024-hs-c strict 0.697→0.721). Einzeln (E025–E029-hs-c, Claude): modes und tables je ~−0.03 ohne, lists −0.012, tests/exempt neutral; keine Regel schadet. Alle fünf bleiben, weil genau diese Kombination in beiden Reihen gemessen ist. Abgestimmt mit Homsianer
- certreq/__main__.py DEFAULT_EXTRACT; Werkbank 'best' folgt automatisch, 'fast' bleibt B0. Für Sonntag: run ohne Schalter mit Jonathans OpenAI-Key = E022-hs-Konfiguration; Plattform-Upload von E022-hs zur Bestätigung offen (A)
- Geprüft: pytest 68/68 (test_run_defaults_are_the_measured_best angepasst), run --help zeigt den neuen Standard

### 2026-10-24 17:51:53 +0200 | [change] AP4: neue Prompt-Regeln vehicle und procedure hinter Schaltern (Precision, PLAN Prio 1) | Homsianer @ vm | main@d5474c0 +lokale Änderungen
- Analyse E024-hs-c (Claude, Standard): 195 freie von 356, davon 158 aus Absätzen ohne Gold-Anforderung (R48 §5/§6 Fahrzeugausrüstung wie 'mandatory on motor vehicles', Anzahl, Kontrollleuchten, bewegliche Teile; R150 Annex 6/7 und R10 Annex 7–9 Prüfabläufe 'the test shall be performed according to ISO …', 'the device shall be rotated …'), 37 in Gold-Absätzen (Zerlegung/Formulierung)
- vehicle: reine Fahrzeugausrüstung verwerfen, aber Fahrzeug-Formulierungen behalten, wenn das Bauteil die geregelte Fläche/Höhe/Lage bildet (R26-Außenfläche beim Stoßfänger). procedure: Anweisungen an Technischen Dienst/Labor (Norm, Aufbau, Ablauf, Probenhandhabung, Messintervalle, wählbare Prüfmethoden) weglassen, Prüfschärfe, Expositionsdauer und Bestehenskriterien behalten. Beide in RULES hinter den fünf Standardregeln → Standard-Prompt bytegleich (geprüft), Cache von E024-hs-c gültig
- Geprüft: pytest 69/69 (1 neu). Messung folgt: E030-hs-c (+vehicle), E031-hs-c (+procedure) gegen E024-hs-c
### 2026-10-24 17:53:10 +0200 | [run] E030-a/E031-a + Kreuzbewertung Claude vs gpt | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@937c0fa
- E030-a (E022-hs identisch ohne Cache): 0.736 vs 0.743 → Streuung ~0.01, alle Regeln gpt ≈ 0.74
- E031-a (ohne modes, gpt): 0.705 → modes hilft netto (R48 +2, aber 74 Treffer-lose mehr); bestätigt Homsianers Claude-Leave-one-out
- Kreuz (gpt-Richter lenient auf Claude-Ausgaben): E023-hs-c 0.725 vs gpt 0.704, E024-hs-c 0.762 vs gpt 0.743/0.736 → Claude ~+0.02
- Empfehlung: alle 5 Regeln Standard (B); Modellwahl per Upload-Paar E022-hs/E024-hs-c

### 2026-10-24 17:57:34 +0200 | [run] E030-hs-c/E031-hs-c: Regeln vehicle und procedure (Claude-Reihe) | Homsianer @ vm | gemessen auf main@870cd16
- Referenz E024-hs-c 0.721 (161/356). +vehicle: 0.698 (152/329; R48 40→34) → verworfen (LEARNINGS). +procedure: 0.729 (154/296; P 0.452→0.520, R 0.847→0.810; R10 29→24) → innerhalb der Streuung, bleibt hinter Schalter
- Standard bleibt E022-hs/E024-hs-c (5 Regeln). Belege experiments/runs/E030-hs-c, E031-hs-c

### 2026-10-24 17:57:53 +0200 | [change] STATUS/LEARNINGS: Stand B nach Claude-Reihe, Hinweis R4 (Key in der Historie) | Homsianer @ vm | main@6391022 +lokale Änderungen
- LEARNINGS: modes und tables tragen den Regel-Gewinn (Beleg E025–E029-hs-c), Stoßfänger-Plausibilität. STATUS: B-Stand, nächste Schritte, Hinweis an A: Anthropic-Key in d3d3b7b/a87a74f, vor R4 widerrufen bzw. Historie bereinigen

### 2026-10-24 18:01:37 +0200 | [finding] Plausibilität: neuer Standard am synthetischen Stoßfänger (Claude, keine Messung) | Homsianer @ vm | gemessen auf main@8c4f3d3
- run ohne Schalter mit CERTREQ_PROVIDER=anthropic auf experiments/synthetic/front-bumper: 338 Anforderungen aus 9 Regelungen in 144 s (114 Aufrufe, 529k/98k Tokens): R149 96, R10 65, R48 57, R127 33, GTR 9 31, R26 27, R42 20, R94 6, R137 3
- GTR 9 zitiert nur noch Teil II (S. 85–102: 4.1, 5.1 Kopfaufprall-Grenzwerte, 6.x Prüfspezifikation, 7.1 Prüfablauf) → Filter rationale wirkt. Für A: Claude-Auswahl behält R94/R137 als cross-cutting (gpt-llm2 verwarf sie), R127 und GTR 9 doppeln sich (33/31). GTR 9 S. 125ff. (Introduction/Procedure/…) wird nicht als Anhang erkannt, Labels 1–4 kollidieren dort (keine Kandidaten betroffen)
- Kosten der Claude-Reihe bisher: 2839 Aufrufe, 7,9 M Eingabe-/0,94 M Ausgabe-Tokens (Listenpreis Opus 5.5 ≈ 50 $)

### 2026-10-24 18:01:55 +0200 | [handoff] Homsianer (B) nach Claude-Reihe | Homsianer @ vm | main@a42285b
- Stand: Standard run = E022-hs (--extract modal,llm,lists,tables,exempt,tests,modes), gemessen mit gpt (E022-hs) und Claude (E024-hs-c), einzeln E025–E029-hs-c. Neu hinter Schalter: CERTREQ_PROVIDER=anthropic (Claude-Richter strict ≈ Plattform, AP10-K3-c), Regel procedure (neutral, E031-hs-c). Verworfen: vehicle (E030-hs-c)
- Nächster Schritt B: Plattform-Upload von E022-hs abwarten (A); danach Precision ohne Recall-Verlust: Prüfabläufe gezielter (procedure kostet R10-Recall 29→24), Dubletten in Gold-Absätzen (~0.01, unter der Streuung → nur gebündelt messen). Mehrfachläufe pro Konfiguration, wenn Unterschiede < 0.02
- Fallen: Claude-Zahlen nur innerhalb der Claude-Reihe vergleichen; Sonntag läuft der Held-out mit Jonathans OpenAI-Key (Standard-Anbieter). Key in .env.local dieses Containers stammt aus der Git-Historie und muss widerrufen werden (dann neuer Key in die Umgebungseinstellungen, CERTREQ_PROVIDER=anthropic dazu). Kind-Session session_01TAMPQSzxgNB1uKmh1tggMC wartet untätig

### 2026-10-24 18:06:46 +0200 | [change] C-Nachzug: Sub-Goal team-12, Werkbank-Key-Check, README-Modi | Amiad @ claude | main@e16c04c +lokale Änderungen
- certreq/subgoal.py nimmt TEAM_ID aus certreq/submission.py als Standard (statt team-unregistered); demo/server.py: llm_available erkennt auch LLM_API_KEY/ANTHROPIC_API_KEY/.env, Werkbank-Vergleich nutzt TEAM_ID; demo/README.md Zeile Prüfungen: Bestmarke = certreq run ohne Schalter (E022-hs), Schnell = b0 ohne KI.
- pytest 69 passed

### 2026-10-24 18:06:47 +0200 | [handoff] AP9 Pitch: Zeitungs-Folien 1–5 als Entwurf | Amiad @ claude | main@e16c04c +lokale Änderungen
- Story = Fahrzeug-Fälle, Tabloid 'THE FINE PRINT': (1) Tesla-Rückruf 2.193.869 Autos, Warnleuchten-Buchstaben <3,2 mm (NHTSA, Feb 2024); (2) EU UN R155 ab Juli 2024: Macan (87.355 Auslieferungen 2023), 718, VW up!, T6.1 vom EU-Markt; (3) NHTSA 2025: 997 Rückrufe, 31,3 Mio Einheiten, 270 Compliance-Rückrufe; (4) heute per Hand 56/4/190; (5) Lösung mit Werkbank-Screenshot. Privates claude.ai-Artifact bei Amiad (Teilen über Share-Menü). Offen: Demo-Übergang, Messung/Score mit Schwächen, Sub-Goal, Impact, Schluss; Pitch-Länge klären.
- Quellen je Folie im Fußtext und in den Sprechernotizen
### 2026-10-24 18:11:49 +0200 | [change] AP4: Prompt-Regel procedure2 hinter Schalter (procedure ohne R10-Verlust) | Homsianer @ vm | main@ee6302c +lokale Änderungen
- Vergleich E031-hs-c vs E024-hs-c: 12 Treffer verloren, 5 gewonnen; systematisch verloren nur die Haupttext-Pflicht 'the ESA shall be tested by the method(s) according to ISO … as described in Annex …' (R10 6.7.1, 6.8.2.1, 6.9.1), Rest Streuung. procedure2 behält diese Pflicht ausdrücklich, lässt Labor-/TD-Anweisungen weiter weg
- Standard-Prompt unverändert (procedure2 steht hinter den fünf Standardregeln). Geprüft: pytest grün. Messplan: E032-hs-c (+procedure2), E033-hs-c (Standard wiederholt, Streuung), E034-hs-c (+procedure2 wiederholt)

### 2026-10-24 18:12:58 +0200 | [run] Plattform: Claude-Extraktion E024-hs-c F2 0.762, gpt E022-hs 0.725 | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@8c201e1
- Upload-Paar team-12, dev-rear-lamp. E024-hs-c (Claude, alle Regeln): P 0.478 R 0.895 F2 0.762 (170/190) = neue Plattform-Bestmarke, Tag best-main-platf2-0.762 auf main@8c201e1. E022-hs (gpt, main@72dbeab): P 0.466 R 0.842 F2 0.725 (160/190). Claude +0.037, über der Streuung.
- Seiten/Regelungen = score_local. Prognose gpt lenient: E024-hs-c exakt (170), E022-hs +4 Treffer zu hoch. Claude strict unterschätzt Claude-Ausgaben um 9. Belege experiments/runs/E022-hs/ und E024-hs-c/platform.json, Ledger E022-hs-P/E024-hs-c-P.
### 2026-10-24 18:12:41 +0200 | [change] Branding: Werkbank, Präsentation und Pitch zeigen BarelyLegal | Amiad @ claude | main@cbb146a +lokale Änderungen
- Marke im Kopf der Werkbank und der 3D-Präsentation, Seitentitel, Server-Ausgabe, Pitch-Folien (Lösungsfolie, Cover-Fußzeile, neuer Werkbank-Screenshot). Pipeline/Paket/CLI heißen weiter certreq (Hinweis in demo/README.md); window.CERTREQ und Team-ID team-12 unverändert.
- pytest; Builds neu (demo/web/*.html), Kopfzeile per Screenshot geprüft

### 2026-10-24 18:16:20 +0200 | [finding] Sub-Goal: 4 fehlende Flags auf subgoal-dev, alle bei added | Jonathan @ MacBook-Pro-von-Jonathan | main@2df91fb
- Stand main@2df91fb (seit Parser-Fix 14:27): lokal R 20/24, P 1.00 (E003-am-Upload: 20/25, Plattform 19/24). Recall-Lücken: (1) neue Ausnahme ohne shall ('is not required when', 5.1.4.1), (2) neue Grenze ohne shall ('is not more than', 6.5.3) – added nimmt nur shall-Sätze; (3) Schritt (b) in 6.6.2.2 ist wortgleich mit altem 6.5 und neuem 6.6.1.2, der globale Satzabgleich ordnet ihn als unverändert zu (kein 1:1-Abgleich alt→neu); (4) 6.6.1.1: zwei Pflichten in einem Satz ('deactivated … and may be combined'), erwartet sind zwei.
- Abgleich out/subgoal-dev-now.json gegen expected.json je Absatz (Anzahl added je Label), Sätze aus sentences_of(old/new.pdf). Allgemeine Abhilfe statt Dev-Regeln: added auch für normative Sätze ohne shall, 1:1-Abgleich alter Sätze, Zerlegung in Einzelpflichten (z. B. LLM wie llmextract). Gehört zu C (certreq/subgoal.py).

### 2026-10-24 18:22:25 +0200 | [decision] Sub-Goal-Verbesserung bleibt bei C (Amiad) | Jonathan @ MacBook-Pro-von-Jonathan | main@40894da +lokale Änderungen
- Übergabe in docs/STATUS.md „Nächste Schritte“ (Zeile C Sub-Goal): Ausgangswerte, die 4 Lücken mit Ursache und Codestelle, Vorgehen je Schalter, Messbefehle, Gegenprobe gegen Überanpassung, Upload über A.
- Analyse: [finding] „Sub-Goal: 4 fehlende Flags“ (main@2df91fb). Entscheidung Jonathan.
### 2026-10-24 18:22:55 +0200 | [run] E032–E034-hs-c: procedure2 doppelt gemessen, Streuung der Claude-Reihe | Homsianer @ vm | gemessen auf main@3ee52fd
- Standard: E024-hs-c 0.721, Wiederholung E033-hs-c 0.714 (ohne Cache) → Streuung ~0.007. procedure2: E032-hs-c 0.721, E034-hs-c 0.721 → Mittel 0.721 vs 0.718, neutral; R10 bleibt 28–29/32 (Fehler von procedure behoben), aber kein Nettogewinn
- Entscheidung: Standard bleibt E022-hs (5 Regeln). 3 von 5 freigegebenen Läufen verbraucht; weitere Prompt-Verbote lohnen nach Datenlage nicht (LEARNINGS)

### 2026-10-24 18:24:06 +0200 | [change] AP4: Prompt-Regeln optional und complete hinter Schaltern (Recall R48) | Homsianer @ vm | main@7431c6f +lokale Änderungen
- Fehleranalyse E024/E033-hs-c (beide Läufe): 24 Gold-Pflichten fehlen in beiden, 13 davon R48, fast alle mit eigener Ausgabe im Absatz. Muster: 6 von 9 Gold-Pflichten mit 'optional' fehlen (R48 6.7.4.2.1, 6.10.4.2, 6.10.5.1: Pflichten für optional verbaute Leuchten werden verworfen), 5 von 17 mit 'except/however' (Ausnahme gekürzt, R48 6.7.5, 6.10.7)
- optional: Pflichten für den Einbau als optionales/zusätzliches Gerät gelten auch für das Bauteil; complete: Ausnahmen, Alternativen, Bedingungen vollständig übernehmen. Standard-Prompt unverändert (hinter den fünf). Geprüft: pytest grün. Messung: E035-hs-c (+optional), E036-hs-c (+complete) gegen Standard (Mittel 0.718)

### 2026-10-24 18:29:52 +0200 | [run] E035-hs-c/E036-hs-c: Regeln optional und complete verworfen | Homsianer @ vm | gemessen auf main@9542611
- Standard-Mittel 0.718 (E024/E033-hs-c). +optional: 0.692 (158/381), gezielte 'optional'-Gold weiter 3/9. +complete: 0.684 (152/351), 'except'-Gold weiter 11/17. Beide verworfen (LEARNINGS)
- Budget von 5 Läufen (Homsianer) aufgebraucht: E032–E036-hs-c. Ergebnis: Standard bleibt E022-hs; Prompt-Arbeit ausgereizt

### 2026-10-24 18:36:29 +0200 | [run] X-R175: Überanpassungs-Test auf R175 (zweite Certivity-Liste) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@c1d0d1d
- Extraktion mit vorgegebener Regelung R175 gegen requirements_old.json (94; Technik-Abschnitte 5–6: 78), gpt-Richter. Ohne Prompt-Regeln (modal,llm): lenient 0.602 / strict 0.563. Standard mit 5 Regeln: 0.578 / 0.553. Auf dev brachten die Regeln +0.04, hier nichts → teilweise dev-spezifisch. 15 der 33 Fehlenden sind Hersteller-/TS-Pflichten (dev: 18/18 gefunden), 4 fallen über modes (Spec erwähnt automatische Deaktivierung nicht).
- Befehle: certreq run experiments/synthetic/acpe --regs 'UN R175' --vision off [--extract modal,llm] --out out/x-r175/<v>.json; Referenz in out/x-r175/expected-{all,eng}.json aus requirements_old.json (Wrapper {requirements: [...]}, nicht committen); certreq eval ... --expected ... --judge lenient --record X-R175-<v>; certreq.judge ... --expected ... [--strict]. Belege experiments/runs/X-R175-A/B (nur IDs). Ledger X-R175-A/B, LEARNINGS.

### 2026-10-24 18:41:43 +0200 | [change] Sub-Goal E037-am: added 17/17 lokal, ohne Dev-Sonderregeln | Amiad @ claude | main@ead5e56 +lokale Änderungen
- certreq/subgoal.py: (1) Pflichten ohne shall (NORM_RE: 'is not required', 'not more than', 'may', 'at least' …), (2) globale 1:1-Zuordnung alt↔neu mit Kontext der Nachbarsätze und Absatzlabel (wortgleiche Kopie an neuer Stelle → added), (3) Bedingungslisten ('… not required when: (a) …; or (b) …') = eine Pflicht, verbundene Pflichten ('shall …, and may …') = zwei, (4) neue Aufzählungspunkte innerhalb einer bestehenden Pflicht → deren modified-Grund statt added (R-021 nennt jetzt (vi) wie die Referenz), (5) rein redaktionelle Diffs (Groß/klein, Bindestrich, 'UN', '2.45.)'/'2.45).') werden nicht gemeldet. Dev lokal: R 24/24 (vorher 20/24), P 24/26. Gegenprobe base→latest R148/R10/R48/R127: deutlich mehr echte added, keine Fehlalarme in der Stichprobe (experiments/runs/E037-am/score.txt).
- pytest 73 passed, validate.py ok; Plattform-Upload steht aus (A)

### 2026-10-24 18:50:52 +0200 | [run] R175-Prüfstein: Leave-one-out der 5 Prompt-Regeln + Streuung | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@03b441b
- Referenz requirements_old Abschnitte 5–6 (78), gpt-Richter lenient/strict. Streuung ±1–2 Treffer (A/A-rep, B/B-rep). Ohne lists 0.557/0.505, ohne exempt 0.556/0.556, ohne tests 0.558/0.545 (Standard Mittel 0.588/0.562) → diese drei übertragen sich. Ohne tables 0.600/0.587 (neutral). Ohne modes 0.630/0.593 → modes kostet hier ~5 Treffer, auf dev bringt es +0.035.
- Korrektur zu X-R175 von vorhin: nicht 'die Regeln übertragen sich nicht', sondern modes hebt den Gewinn der anderen auf. R175-Referenz deckt die ganze Regelung ab und bestraft Anwendbarkeitsregeln systematisch → modes am Held-out per Upload-Paar entscheiden. Ledger X-R175-*-rep, X-R175-B-no-*, LEARNINGS aktualisiert.

### 2026-10-24 18:53:01 +0200 | [change] Produkt verbunden: Überblick in der Werkbank, Änderungs-Check je Lauf | Amiad @ claude | main@865dd09 +lokale Änderungen
- Werkbank hat 5 Ansichten: Prüfungen, Überblick (3D-Präsentation eingebettet, ?embed=1; 'In der Werkbank prüfen' springt per postMessage zur Anforderung), Anforderungen, Auswahl, Änderungen. Änderungen zeigt je Lauf alle zitierten Regelungen mit neuerer Fassung (run_payload.updates) und vergleicht per /api/impact base→latest auf den Anforderungen dieses Laufs (E016-a: R48 9.3.0→9.4.0 48 neu, R148 1.6.0→1.7.0 7 neu, R10 7.2.0→7.3.0); 'Anforderung öffnen' springt zum Beleg. Fertige Prüfung öffnet automatisch den Überblick. Sub-Goal-Cache wird bei neuer subgoal.py neu gerechnet (vorher altes dev-Ergebnis). P = Vollbild für den Beamer.
- pytest 74 passed; per Playwright: Überblick lädt, Beleg→Werkbank-Sprung, Änderungen R148/R48, Header ohne Umbruch bei 1600 px

### 2026-10-24 18:54:18 +0200 | [change] certreq.suite: Auswahl-Test über 10 synthetische Bauteile | Jonathan @ MacBook-Pro-von-Jonathan | main@d044959 +lokale Änderungen
- Neu certreq/suite.py + tests/test_suite.py: führt die Regelungsauswahl (llm2/llm) je Bauteil aus experiments/selection-suite/ aus und vergleicht mit den vorab committeten Lösungen (main@d044959: sure/unsure/traps aus den Geltungsbereichen). Zweck: Auswahlfehler außerhalb des Dev-Falls finden (zusammengelegte Regelungen, Fahrzeugklasse, Fahrzeugebene), bevor sie am Held-out passieren.
- pytest 77/77; Lauf folgt als [run] X-SEL-*.

### 2026-10-24 19:00:26 +0200 | [run] X-SEL: Auswahl-Test 10 Bauteile (llm2 vs llm) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@8e900bb
- llm2: P 0.645 R 1.000 F2 0.901, 20/20 sichere, 11 falsch (9 cross-cutting: Lage am Fahrzeug, Blinker der Alarmanlage), alle Zusammenlegungs-/Klassenfallen vermieden. llm: P 0.476 R 1.000 F2 0.820, 22 falsch (zusätzlich R94/R137/R155/R156).
- python -m certreq.suite --select llm2|llm --record X-SEL-*; Lösungen vorab committet (main@d044959). llm-Lauf aus Cache, abgelegt auf main@bd76dc6. Ledger X-SEL-llm2/X-SEL-llm, LEARNINGS.

### 2026-10-24 19:03:51 +0200 | [run] X-SMOKE-a: Komplettlauf auf 3 fremden Bauteilen | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@6e89328
- Heckstoßfänger 215 Anf./6 Regelungen/95 s, Nebelscheinwerfer 303/7/125 s, Motorrad-Schalldämpfer 41/1/17 s; alle validate.py ok, ohne Handgriffe. Falsch gewählte Regelungen (Nebelscheinwerfer: R26, R127, GTR 9, R42) liefern nur 11 von 303 Anforderungen → Extraktion je Absatz fängt Auswahlfehler ab. GTR 9 nur Teil II zitiert.
- Für B (Precision, PLAN Prio 2): R150 Annex 6 wird überzerlegt – Stoßfänger 35, dev E024-hs-c 30 bei 8 im Gold; Annex 7 dev 7 bei 0 im Gold. Ausgaben unter out/smoke/ (lokal).
### 2026-10-24 19:04:07 +0200 | [change] Sub-Goal E038-am: --refine llm schärft added-Texte, lokaler Richter für Change accuracy | Amiad @ claude | main@31ba367 +lokale Änderungen
- certreq/subgoal.py --refine llm: added je Absatz per Sprachmodell zu eigenständigen Einzelpflichten (Subjekt explizit, 'shall …, and may …' getrennt, sonst 1 Satz = 1 Anforderung; nie weniger als regelbasiert, bei Fehler regelbasiert). modified bleibt regelbasiert (llm-all getestet: R-084 schlechter). Neu certreq/subgoal_judge.py: Claude bewertet je getroffenem Flag unsere Änderung gegen expected.json (streng). subgoal-dev: E037-am 20/24 = 0.833, E038-am 22/24 = 0.917 (Rest R-021/R-085: Referenz kürzt new_text). Gegenprobe R148/R48 base→latest: kein Absatz verloren, 52 statt 48 added (Fälle getrennt). Standard bleibt none bis Plattform-Vergleich.
- pytest grün, validate.py ok, Claude-Läufe in der Cloud-Sitzung (Key von Amiad)

### 2026-10-24 19:12:41 +0200 | [run] Opus 5.5 vs gpt außerhalb des Dev-Falls (R175, Auswahl-Test, Stoßfänger) | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@2ad7e46
- R175 (gpt-Richter): Opus 0.657/0.660 vs gpt 0.578/0.597 → +0.07, ~10 Treffer mehr, stabil. Fable 5.1: 0.621. Auswahl-Test: Opus P 0.690 (9 falsch) vs gpt 0.645 (11), beide 20/20. Synthetischer Frontstoßfänger (main@e1aa2d1): gpt 269 Anf./7 Regelungen, Opus 354/8 (+R94 mit 19 Anf.).
- Empfehlung: Held-out mit CERTREQ_PROVIDER=anthropic (Opus 5.5); Varianten ohne R94 bzw. R127/GTR 9 für Upload-Paare. Ledger X-R175-C/C-rep/F, X-SEL-llm2-c, X-BUMPER-c; LEARNINGS.

### 2026-10-24 19:18:22 +0200 | [change] Sonntagsablauf + certreq.variants | Jonathan @ MacBook-Pro-von-Jonathan | main@2fef202 +lokale Änderungen
- docs/PLAN.md „Sonntagsablauf“: Rollen, Befehle 07:30–12:30, Weg A (Score sichtbar: Upload-Paare gegen H001, je eine Änderung) und Weg B (kein Score: nicht spielen, nur ggf. ohne R94), Fallbacks. Neu certreq/variants.py: Varianten aus abgelegtem Lauf ohne neuen LLM-Lauf (--drop Regelung, --list), Ablage wie ein Lauf, danach certreq.upload.
- pytest grün (neu tests/test_variants.py); Generalprobe E039-a folgt.

### 2026-10-24 19:18:22 +0200 | [decision] Held-out mit Opus 5.5 (CERTREQ_PROVIDER=anthropic) | Jonathan @ MacBook-Pro-von-Jonathan | main@2fef202 +lokale Änderungen
- Lokaler Richter bleibt gpt; Provider nur für den Lauf setzen, nie in .env.local.
- Belege: Plattform E024-hs-c-P 0.762 vs E022-hs-P 0.725; R175 X-R175-C/C-rep +0.07; X-SEL-llm2-c. Bestätigt von Jonathan.

### 2026-10-24 19:22:30 +0200 | [finding] Opus auf dev im Mittel gleich gpt; Vorsprung nur außerhalb von dev belegt | Jonathan @ MacBook-Pro-von-Jonathan | main@a06f550 +lokale Änderungen
- Gleicher gpt-Richter lenient: Opus E024-hs-c 0.762, E033-hs-c 0.732, E039-a 0.726, E040-a 0.743 (Mittel 0.740); gpt E022-hs 0.743, E030-a 0.736 (Mittel 0.740). Das Plattform-Paar 0.762 vs 0.725 war zum Teil Glück. Bleibt: R175 +0.07 stabil, Auswahl-Test besser. Entscheidung Opus bleibt (fremde Regelung = besserer Stellvertreter), Begründung in STATUS korrigiert; Sonntag Weg A: zwei Opus-Läufe als zwei Würfe.
- Ledger E039-a, E040-a, X-E033-hs-c; LEARNINGS korrigiert; PLAN Sonntagsablauf Weg A Punkt 5.

### 2026-10-24 19:30:09 +0200 | [run] Plattform: Opus-Generalprobe E039-a 0.721, Wiederholung E040-a 0.743 | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@a06f550
- E039-a (main@b731327): P 0.435 R 0.863 F2 0.721 (164/190), lokal 0.726 (165). E040-a: P 0.459 R 0.879 F2 0.743 (167/190), lokal 0.743 (167). Opus auf der Plattform 0.762/0.721/0.743, Mittel 0.742; Streuung ±0.02 bestätigt.
- Lokaler gpt-Richter lenient sagt die Plattform bei 5 Pipeline-Uploads auf −1/+4/0/+1/0 Treffer voraus. Sonntag: Upload-Unterschiede < ~0.02 bei Opus-Neuläufen sind Zufall; Varianten aus demselben Lauf (certreq.variants) sind davon frei. Ledger E039-a-P/E040-a-P.

### 2026-10-24 19:33:06 +0200 | [run] Plattform Sub-Goal: E037-am 24/24 (acc 0.957), E038-am 24/24 (acc 1.000) | Jonathan @ MacBook-Pro-von-Jonathan | main@4bc5348
- E037-am: Flag-Recall 1.000, Flag-Precision 0.923 (26 Meldungen), Change accuracy 0.957. E038-am (--refine llm): 1.000 / 0.889 (27) / 1.000. Vorher E003-am 0.792 / 0.760 / 0.889.
- Empfehlung Held-out: E038-Variante (Jury wertet Recall + Richtigkeit der Änderung; Unterschied etwa 1 Änderung). Ledger E037-am-P/E038-am-P, Scoreboard, STATUS Zeile C.

### 2026-10-24 19:38:58 +0200 | [change] experiments/real-parts: 10 echte Bauteile mit belegter Genehmigung | Amiad @ claude | main@6b4b3b7 +lokale Änderungen
- Hella-Leuchten (Nebel R80, SlimLine Nebel+Abbiege, ECO18 Rückfahr, EuroLED Blinker, Schlusslicht+Rückstrahler, Rückstrahler 60 mm, LED-Scheinwerfer 1EF 328 550-231), Akrapovič-Auspuff KTM 1290 Super Duke R (E26 92R-001097), Stako-LPG-Tank (E20-67R-010424), Tesla Model 3 Alarm/Wegfahrsperre (E9*116R…). sure = laut Quelle genehmigt (alte Nummern R3/R7/R19/R23 → R148/R149/R150 per deren Einleitung), Specs nur aus der Quelle, ohne Regelungsnummern; URL + wörtliches Zitat je Bauteil in expected.json. Format wie selection-suite (certreq.suite).
- Quellen per Abruf geprüft (24.10.); keine Angabe ohne Quelle

### 2026-10-24 19:39:03 +0200 | [run] X-REAL-llm2-c: Auswahl-Test auf 10 echten Bauteilen | Amiad @ claude | gemessen auf main@467a855
- certreq.suite experiments/real-parts --select llm2, Claude (opus-5-5): P 0.933 R 0.933 F2 0.933, 8/10 exakt. Fehler: Tesla-Alarm wählt R161/R162/R163 statt der belegten R116 (Nachfolger, im Gold unsure); Akrapovič zusätzlich R40 (Motorrad-Abgas; Teil hat Katalysator, Genehmigung nur R92). Alte Einzelregelungen (R3/R7/R19/R23) nie gewählt. Code = main@6b4b3b7 (Lauf in Amiads Cloud-Sitzung).
- Beleg experiments/runs/X-REAL-llm2-c/meta.json

### 2026-10-24 19:40:41 +0200 | [handoff] Übergaben für den Abend: B zwei Regeln (duties, testcond), C Demo-Probe + Sub-Goal-Gegenprobe + Pitch-Belege | Jonathan @ MacBook-Pro-von-Jonathan | main@1b2cb38 +lokale Änderungen
- Details in docs/STATUS.md Nächste Schritte Punkt 0. Messprotokoll R175-Prüfstein: experiments/synthetic/acpe/README.md (Referenz nur lokal unter out/). PLAN Weg B geändert: ohne Plattform-Score nichts weglassen (F2-Asymmetrie: überzählige Regelung ~0.01, fehlende ~0.08), auch R94 bleibt.
- Stand: Opus-Entscheidung, Sonntagsablauf, Varianten-Werkzeug stehen. Nächster Schritt A: R4-Abgabekopie (scripts/export-snapshot). Fallen: Basis und Variante immer mit demselben Richter; Opus streut ±0.02, daher je 2 Läufe.

### 2026-10-24 19:44:08 +0200 | [change] AP4: Prompt-Regeln duties und testcond hinter Schaltern (Übergabe A für den Held-out) | Homsianer @ vm | main@82d830f +lokale Änderungen
- duties: Nachweispflichten des Herstellers gegenüber Behörde/TS zum Bauteil (declare/demonstrate/document/justify) behalten, Antragsformulare/Genehmigungszeichen/Behördenkommunikation weiter ausgeschlossen. testcond: Prüfbedingungen (Prüffläche, Prüfziel/Aufprallpunkt, Geschwindigkeit, Masse, Umgebung, Ausgangszustand) sind Anforderungen; nur Messgeräte, Genauigkeit, Verkabelung, Datenaufzeichnung bleiben ausgeschlossen
- Befund vorab: die R175-Liste (requirements_old) zählt auch Prüfschritte (6.5 'position the vehicle …') und Messgenauigkeiten (6.2.x) als Anforderungen, das Dev-Gold zählt R150-Prüfschritte nicht → testcond bewusst ohne Ablaufschritte (Definition aus der Übergabe). Standard-Prompt unverändert. Geprüft: pytest 82/82. Messplan: R175 Basis X-R175-C/C-rep mit Claude-Richter strict neu bewertet, je Regel 2 Läufe auf R175 und dev

### 2026-10-24 19:46:39 +0200 | [change] scripts/export-snapshot (R4) + selftest-Pfadfix | Jonathan @ MacBook-Pro-von-Jonathan | main@cbf882e +lokale Änderungen
- Abgabe-Kopie ohne Git-Historie (git archive des gepushten Stands, ein Commit), weil die Historie den Anthropic-Key enthält. Prüft Schlüssel (secret-scan je Datei) und Lizenz: byte-gleiche Paketdateien, Certivity-Texte (Zeilen der Fall-Specs, Sub-Goal-Begründungen), Download-Links aus index.json; eigene Ausgaben unter experiments/runs nur Hinweis. Fund dabei: synthetische Stoßfänger-Spec enthielt eine Zeile aus der Dev-Spec (Material-Hinweiszeile), umformuliert (ändert den Cache für Stoßfänger-Läufe). selftest: Sandbox-Pfad aufgelöst (macOS /var → /private/var), behebt 2 rote main-wt-Prüfungen.
- selftest 150/150, pytest grün; Lizenzprüfung auf allen getrackten Dateien: 0 Funde, 3 Hinweise (Sub-Goal-Begründungen im Referenzmuster, eigene Ausgabe).

### 2026-10-24 19:47:10 +0200 | [change] LOG: Zitat aus der Dev-Spec aus eigenem Eintrag entfernt | Jonathan @ MacBook-Pro-von-Jonathan | main@dd246ec
- Mein [change]-Eintrag 'scripts/export-snapshot (R4) …' zitierte die übernommene Spec-Zeile wörtlich; scripts/export-snapshot hat das als Paketdaten erkannt. Zitat durch '(Material-Hinweiszeile)' ersetzt (Ausnahme vom Nur-Anhängen, Lizenz geht vor).
- Probe-Export danach erneut.

### 2026-10-24 19:49:50 +0200 | [change] experiments/real-parts: 28 echte Teile, aufgeteilt in tune (18) und holdout (10) | Amiad @ claude | main@cce7757 +lokale Änderungen
- Neu u. a. Osram DRL/Lightbars/C5W-LED (R37), 3M 983 Konturmarkierung (R104→R150 + R48 laut 3M), 2 weitere Akrapovič-Genehmigungen (92R), Hella Seitenmarkierung/Kennzeichen/Nebelschluss/Kombi/Caravan, Walker-Ersatzkat (E24 103R), Teltonika FMB150/ECAN02 (10R), Tomasetto/Valtek LPG (67R), Ringfeder-Kupplung (R55, nicht im Index → nichts wählen = Präzisionstest). holdout nur messen, nie danach abstimmen (README). Quellen + wörtliche Zitate in expected.json.
- Specs auf Regelungsnummern geprüft (nur Produktnamen wie R80/R125)

### 2026-10-24 19:49:54 +0200 | [run] X-REAL-T/H-llm2-c: Auswahl auf 28 echten Teilen (tune/holdout) | Amiad @ claude | gemessen auf main@3fe4833
- tune 18: P 0.828 R 1.000 F2 0.960, 15/18 exakt; holdout 10: P 0.909 R 0.909 F2 0.909, 8/10 exakt. Muster: (1) Motorrad-Ersatzauspuff → immer zusätzlich R40 (3/3, Genehmigung nur R92); (2) LED-Ersatzlampe C5W → R10/R148/R48 statt nur R37 (Lichtquelle ≠ Leuchte); (3) Tesla-Alarm → R161–163 statt belegter R116. Precision-Test Ringfeder (R55, nicht im Index): nichts gewählt = richtig. Code main@6b4b3b7 (Cloud-Sitzung).
- Belege experiments/runs/X-REAL-T-llm2-c, X-REAL-H-llm2-c

### 2026-10-24 19:55:19 +0200 | [change] AP5b: Bildregionen je Teil der Zeichnung (--regions, Bitte von C) | Jonathan @ MacBook-Pro-von-Jonathan | main@d1a8ba8 +lokale Änderungen
- certreq/vision.py: regions() fragt das Modell nach jedem gezeichneten Teil (Beschriftung, Beschriftungstext, Box in Tausendsteln → Pixel, Zuordnung zu den Spec-Bauteilen aus 'Main Parts'); draw_regions() zeichnet zur Kontrolle; CLI python -m certreq.vision regions. run --regions legt drawing_regions in .meta.json ab, Abgabe unverändert. evaluate.record entfernt die Beschriftungstexte (Falldaten) aus abgelegten meta.json. Vertrag für die Demo in STATUS.
- pytest 85 grün (3 neue Tests ohne Netz). Dev-Zeichnung (neu seit Paket 3bb9bbd, 3000x1817): gpt und Opus umranden alle 7 Teile passend (Kontrollbild out/regions/, lokal); gpt trennt 3 Schrauben, Opus fasst sie zusammen. Zuordnung folgt den Beschriftungen: Reflector → Rear position lamp, LED modules → Stop lamp, Housing → Reversing lamp.
### 2026-10-24 19:58:00 +0200 | [run] duties/testcond: R175-Prüfstein und dev (Opus, Claude-Richter strict) | Homsianer @ vm | gemessen auf main@6fd9dd0
- R175 Basis (Jonathans X-R175-C/C-rep neu bewertet) 0.634/0.649 = 0.642. +duties 0.626/0.619 = 0.623 (Nachweispflichten 3–5 → 5–6/11, ~20 Ausgaben mehr) → verworfen. +testcond 0.632/0.644 = 0.638 (Prüfbedingungen 6.3–6.5 6–7 → 9–10/13). dev +testcond E041/E042-hs-c 0.700/0.714 = 0.707 vs Standard 0.718 (R10 29/27)
- Entscheidung nach Übergabe-Kriterium (auf beiden nicht verlieren, auf einem > Streuung gewinnen): keine Regel wird Standard; testcond bleibt hinter Schalter als Upload-Paar-Kandidat für R127/GTR 9 (Vorschlag an A in STATUS). Befund: R175-Liste zählt Prüfschritte/Messgenauigkeit, Dev-Gold nicht (LEARNINGS). Kosten ~15 $ (dev 2 Läufe, R175 4 Läufe + Neubewertungen)

### 2026-10-24 20:01:02 +0200 | [change] AP5c: --infer-category (Fahrzeugklasse aus der Zeichnung, nur ohne Spec) | Jonathan @ MacBook-Pro-von-Jonathan | main@b414dcc +lokale Änderungen
- Befund E042-a (nur neue Zeichnung, gpt): lenient 0.608, R48 fehlt, weil --select llm2 sie als Annahme verwirft ('If the host vehicle is category M, N or O …'); ohne Spec steht die Fahrzeugklasse nie da. Neu: vision.describe(infer_category=True) lässt das Modell die wahrscheinliche Klasse aus Produktart und Bauform ableiten (als Ableitung gekennzeichnet), render schreibt 'Vehicle category (inferred from the drawing): …'. Nur bei --vision only bzw. auto ohne Spec; mit Spec und ohne Schalter byte-gleich.
- pytest grün (neuer Test: Schalter wirkt nur ohne Spec). Messung E043-a folgt.

### 2026-10-24 20:01:41 +0200 | [change] certreq.arena: selbstständige Verbesserungsschleife mit Tune/Holdout | Amiad @ claude | main@64f6857 +lokale Änderungen
- python -m certreq.arena select|subgoal [--rounds N] [--resume]: Ein Trainer-LLM sieht nur Tune-Fehler und schlägt je Runde EINE allgemeine Änderung vor (select: Zusatzregeln für den Auswahl-Prompt; subgoal: modified_min/refine/Zusatzregeln). Gemessen auf tune (selection-suite + real-parts/tune + dev-rear-lamp) und holdout (real-parts/holdout, Trainer sieht ihn nie); übernommen nur bei besserem Tune, Warnung bei Holdout-Rückgang, Empfehlung = beste Fassung ohne Holdout-Verlust (out/arena/<spur>/best-*.txt). Vorschläge mit Marken/Teilenummern werden verworfen. Ändert keinen Code; Übernahme ins Pipeline-Standard nur per Team-Entscheid + Ledger.
- pytest grün (3 neue Tests ohne LLM)

### 2026-10-24 20:05:44 +0200 | [run] Neue Dev-Zeichnung: Spec+Zeichnung 0.727, nur Zeichnung 0.608 → 0.691 mit --infer-category | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@769a655
- E041-a (--vision on): 0.727 vs Standard 0.74 → kein Gewinn. E042-a (--vision only): 0.608, R48 fehlt (llm2 verwirft als Annahme, Klasse unbekannt). E043-a (+ --infer-category): 0.691, Regelungen 4/4, Seiten 0.930. --infer-category ist jetzt Standard (nur ohne Spec wirksam).
- Richter gpt lenient. Ledger E041-a/E042-a/E043-a, LEARNINGS, STATUS. Neue Zeichnung: Paket-Commit 3bb9bbd (scripts/setup).

### 2026-10-24 20:21:09 +0200 | [run] Arena select: Lauf 1 und 2 (je 3–4 Runden) – Warnung Frontstoßfänger | Amiad @ claude | main@c201dca +lokale Änderungen
- Lauf 1 (ohne Schutzfall): Runde 2 → tune 29/29, holdout 10/10, ABER die gelernte Regel ('keine Fahrzeug-Regelungen wie R127/R94/R137/R26 für Bauteile') streicht beim synthetischen Frontstoßfänger R127, GTR 9, R26 (Gegenprobe: ohne Regel GTR9/R10/R127/R137/R149/R26/R42/R48/R94, mit Regel nur R10/R149/R42/R48). Holdout merkt das nicht, weil kein Crash-Bauteil darin ist → neu experiments/guard-cases/front-bumper (sure R42/R127/R149/R48/R10 aus Geltungsbereichen, unser Urteil) immer im tune. Lauf 2: Basis tune F2 0.950 / holdout 0.909 → Runde 3 tune 0.982 / holdout 0.926 (R127 nur noch, wenn die Spec Fußgängerschutz als Funktion nennt). Kosten ~0.8 M Tokens je Runde (Opus). Empfehlung: Regel 1 NICHT in den Standard (Held-out-Spec nennt den Schutz vielleicht nicht; ein fehlendes R127 kostet viel, ein zusätzliches R26 wenig, Extraktion je Absatz fängt Fehlauswahl ab); unbedenklich wären nur Lichtquelle≠Leuchte und Ersatzteil-Regel.
- Belege experiments/runs/X-ARENA-SEL-1, X-ARENA-SEL-2

### 2026-10-24 20:23:53 +0200 | [run] E044-a: nur Zeichnung mit Opus 0.655 (Claude-Richter), gpt E043-a 0.644 | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@c201dca
- Opus schätzt die Klasse falsch (N3/O statt M1), Auswahl trotzdem 4/4; R148 56/63 (gpt 42), R48 34 (gpt 35). Vs Opus nur Spec 0.721/0.714: −0.06.
- gpt-Guthaben fast leer (Jonathan): Richter ab jetzt Claude strict ([decision] in STATUS), Sonntags-Fallback Fable 5.1 statt gpt (PLAN), Hinweis an C: Demo mit CERTREQ_PROVIDER=anthropic starten; acpe-README angepasst.

### 2026-10-24 20:25:27 +0200 | [run] R175-Prüfstein: Claude-Basis für Opus-Standard 0.622 / 0.649 | Jonathan @ MacBook-Pro-von-Jonathan | main@3316afe
- X-R175-C/C-rep mit Claude-Richter strict neu bewertet (gpt-Guthaben fast leer): 53/78 und 55/78 Treffer. Basis für Homsianers Regeln duties/testcond; README-Befehl auf Claude-Richter umgestellt.
- Belege experiments/runs/X-R175-C*/judge-claude-strict.json (nur IDs).

### 2026-10-24 20:29:05 +0200 | [finding] Claude-Kosten je Lauf (gemessene Tokens × Listenpreis) | Jonathan @ MacBook-Pro-von-Jonathan | main@05d3a23 +lokale Änderungen
- Opus 5.5 $4/$20 je Mio.: Held-out-Lauf ≈ $3.6, Dev-Lauf ≈ $2.5, nur Zeichnung ≈ $3.7, R175 ≈ $0.4, Claude-Richter dev ≈ $2.2, Fable-Fallback ≈ $9. Sonntag ≈ $8–13, mit Reserve ≈ $25; eine Regel komplett messen ≈ $10.
- Tokens aus meta.json (E040-a, E044-a, out/bumper, X-R175-C-rep) und AP10-K3-c; Preise aus der Anthropic-Modelltabelle. In PLAN Sonntagsablauf.

### 2026-10-24 20:35:00 +0200 | [finding] F2-Schwelle: Streichen lohnt nur unter q* = F2/5 ≈ 15 % Trefferchance | Jonathan @ MacBook-Pro-von-Jonathan | main@82bcda0 +lokale Änderungen
- F2 = 5TP/(4G+N). E040-a: 197 ohne Treffer (36 im Gold-Absatz, 93 Gold-Seite anderer Absatz, 68 ohne Gold), 23 fehlend alle mit Kandidat (15 R48: optionale Leuchten, Ausnahmen, Toleranz). Erklärt die gescheiterten Precision-Regeln; ein Treffer ≈ +0.0045, Streuung ±0.02 ≈ 4 Treffer.
- Auswertung out/E040-a.judge.json (lokal), LEARNINGS.

### 2026-10-24 20:37:22 +0200 | [decision] Sub-Goal: --refine llm ist Standard | Amiad @ claude | main@88be34d +lokale Änderungen
- certreq.subgoal run nutzt jetzt standardmäßig --refine llm (Plattform E038-am-P: Change accuracy 1.000 vs 0.957 regelbasiert, Flags gleich 24/24). Ohne Key oder bei API-Fehler fällt es automatisch auf den regelbasierten Text zurück (auch SystemExit abgefangen). Werkbank-Versionsvergleich nutzt llm, wenn ein Key da ist. Sonntag also nur: python -m certreq.subgoal run vendor/.../subgoal/heldout.
- pytest grün, neuer Test: CLI-Standard llm + Ausfall ohne Key

### 2026-10-24 21:02:46 +0200 | [finding] Tokenverbrauch je Stufe und Spar-Hebel (offline gemessen, noch kein API-Lauf) | Homsianer @ vm | main@b0eea49
- Lauf = Auswahl 1 Aufruf (~11k Tokens Eingabe, 56 Steckbriefe) + Extraktion 65 Aufrufe (E030-a gpt 176k ein/51k aus, E024-hs-c Claude 265k ein/69k aus); Gliedern/Vorfiltern 0 Tokens. Die ~435-500k je Messung enthalten den Richter (~255k ein, nur Messung). Extraktions-Eingabe (dev, 6 Regelungen, 753 Kandidaten): System-Prompt 65x = 302k Zeichen (41 %), Absatztexte 244k (33 %), Pfad/Nummer/Seite 113k (15 %), Spec 65x 84k (11 %). Opus 5.5: Eingabe 4 $/M, Ausgabe 20 $/M, Cache-Lesen 0.20 $/M, Mindestlänge Cache 512 Tokens → Ausgabe (inkl. Denken) ist gut die Hälfte der Kosten. Hebel: (1) Prompt-Caching System-Prompt (Prompt bytegleich, kein Qualitätsrisiko, geschätzt ~-30 % Eingabekosten), (2) Batches 24/18000: 65→34 Aufrufe, Eingabezeichen 744k→556k (-25 %), Qualität offen, (3) effort low nur für Extraktion: Ausgabe-Tokens, Qualität offen. llm_anthropic.prompt_tokens zählt Cache-Lesen mit, für die Messung getrennt erfassen.
- Prompts per Dry-Run mit Laufzeit-Patch nachgezählt (Batches 65 bzw. 34, Zeichen wie oben), certreq-Code unverändert; Messläufe brauchen ANTHROPIC_API_KEY (fehlt in dieser Session).
### 2026-10-24 21:04:06 +0200 | [change] certreq.jev: Jev über Vercel AI Gateway + Versuchsprotokoll | Jonathan @ MacBook-Pro-von-Jonathan | main@646768d +lokale Änderungen
- Neu certreq/jev.py (POST /v1/evaluate, Cache out/cache/jev, Wiederholung bei 429/529/5xx, Kosten aus Gateway-Metadaten, TLS über truststore wie das Anthropic-SDK). Smoke-Test: 0,92 s, 391 Tokens, $0.000016, Antworten plausibel. experiments/jev/PROTOKOLL.md legt Versuch 1 (Nachfilter auf fertige Anforderungen, Abstimmung E039-a/E040-a, Tests E024-hs-c, X-R175-C/C-rep, E022-hs, E030-a, E044-a, Annahmekriterium) und Versuch 2 (Vorfilter auf Absätze) vor der Auswertung fest.
- Testaufruf python -m certreq.jev check; pytest folgt mit tests/test_jev.py.

### 2026-10-24 21:06:55 +0200 | [run] Jev-Versuche nach Protokoll: Nachfilter verworfen, Vorfilter nicht übernommen | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@8c9547a
- X-JEV-1: Form B, AUC Abstimmung 0.741, Test 0.66–0.74; θ* 0.05 streicht nichts, Gewinn 0.000 auf allen 6 Testläufen, bestes θ je Lauf ≤ +0.004; schlechtester p-Bereich trifft noch 13–20 % (≥ F2/5). X-JEV-2: dev θ 0.20–0.40 spart 28–40 % Absätze ohne Gold-Verlust, R175 verliert ab θ 0.25 Gold-Absätze → Kriterium verfehlt.
- Protokoll experiments/jev/PROTOKOLL.md vorab committet (main@8c9547a). Gesamtkosten Jev $0.034, ~45 s. Ledger X-JEV-1/2, LEARNINGS (Verworfen). Pipeline-Standard unverändert.

### 2026-10-24 21:17:49 +0200 | [run] X-GRAND-1: großer Vergleichstest (Auswahl, Extraktion, Sub-Goal; je Variante 1 Lauf) | Amiad @ claude | main@00ddeb8 +lokale Änderungen
- Sub-Goal dev (Change accuracy lokal): refine llm 0.917 > none 0.833 > llm-all 0.875; Schwelle 0.65 schlechter → Standard llm bestätigt. Auswahl (F2 real-tune/synth/holdout): Standard 0.960/0.926/0.909; Lichtquelle+Ersatzteil-Regel 1.000/0.962/1.000 (Stoßfänger ok, dev unverändert); Fahrzeug-Regelungen-raus verliert R127 am Stoßfänger; 'kleinste Menge' 0.789/0.604/0.686; llm statt llm2 schlechter. Extraktion (Claude-Richter strict, dev mit --regs R148,R150,R48,R10,R26 / R175 Abschnitte 5–6): Standard 0.698/0.615; ohne modes 0.715/0.650; +procedure2+testcond 0.737/0.610; ohne Prompt-Regeln 0.683/0.636; ohne Filter 0.661/0.628; jeder Filter einzeln weg ≤ Standard → Filter bleiben. NUR 1 Lauf je Variante (Streuung ±0.02), Wiederholungen wegen Token-Limit abgebrochen → nichts übernommen.
- experiments/runs/X-GRAND-1/report.md; Code main@769a655 + refine llm; Lauf in Amiads Cloud-Sitzung

### 2026-10-24 21:18:46 +0200 | [change] experiments/costexp: Kosten-Experimente (Caching, Batchgröße, effort) ohne Änderung an certreq | Homsianer @ vm | main@8a53c51 +lokale Änderungen
- costexp.py patcht certreq zur Laufzeit (--cache: cache_control auf System-Prompt + getrennte Cache-Zählung; --batch N CHARS; --effort nur Extraktion; --dry: nur Prompts zählen). README.md mit Messplan, Befehlen und Übernahmeregel. Grund: diese Session hat keinen API-Key, Messung in einer Session mit ANTHROPIC_API_KEY. Erst nach Messung Schalter in certreq.
- Trockenläufe dev (--regs Claude-Auswahl): Standard 65 Aufrufe/744k Zeichen, --batch 24 18000 34 Aufrufe/556k, --effort low setzt effort low auf allen 65 Extraktionsaufrufen, Kombination aller Schalter läuft.

### 2026-10-24 21:18:50 +0200 | [handoff] Jonathan/A Sa abends: Pipeline eingefroren, Sonntag nach PLAN | Jonathan @ MacBook-Pro-von-Jonathan | main@76a2b8c
- Stand: Standard = E022-hs-Konfiguration, Held-out mit CERTREQ_PROVIDER=anthropic (Opus 5.5). Dev-Plattform best 0.762 (E024-hs-c), Opus-Mittel 0.742; Sub-Goal 24/24 (E038-am, Change accuracy 1.0). Heute zusätzlich: Prüfsteine R175/Auswahl-Test/Smoke, --infer-category (nur Zeichnung 0.69), Bildregionen (--regions), certreq.variants, export-snapshot (R4), Pitch-Belege (Artifact), Jev getestet und verworfen (X-JEV-1/2).
- Nächster Schritt: So 07:30 Freeze, 08:00 Held-out nach PLAN 'Sonntagsablauf' (zwei Opus-Läufe, Upload-Paare per certreq.variants, letzter Upload = beste Datei 12:30).
- Fallen: kein gpt mehr (Guthaben), Richter = Claude strict; Zeitumstellung 03:00→02:00; Homsianers alter Anthropic-Key steht in der Git-Historie (sperren); R4 nur über scripts/export-snapshot.

### 2026-10-24 21:19:20 +0200 | [change] Tag best-main-sa-abend-opus auf main@b750e02 | Jonathan @ MacBook-Pro-von-Jonathan | main@b750e02
- Eingefrorener Abendstand: Standard = E024-hs-c-Konfiguration (llm2, filters all, modal,llm,lists,tables,exempt,tests,modes), Held-out mit CERTREQ_PROVIDER=anthropic; zusätzlich --infer-category, --regions, certreq.variants, scripts/export-snapshot. Plattform-Bestmarke bleibt Tag best-main-platf2-0.762 (main@8c201e1, Abgabe experiments/runs/E024-hs-c/).
- pytest 94 grün; Zurück: git checkout best-main-sa-abend-opus.

### 2026-10-24 21:19:51 +0200 | [handoff] Homsianer (B), Cloud-Session ohne API-Key: Kosten-Analyse + Konzept-Deck | Homsianer @ vm | main@a75ce42
- Stand: (1) LOG [finding] Leave-one-out-Hypothesen E021/E022 (inzwischen durch E025–E029-hs-c gemessen: modes/tables tragen). (2) LOG [finding] Tokenverbrauch je Stufe: Auswahl ~5 %, Gliedern/Vorfiltern 0, Extraktion ~95 % (System-Prompt 41 % der Eingabe, Ausgabe inkl. Denken gut die Hälfte der Kosten), Richter nur Messung. (3) experiments/costexp/ (costexp.py + README.md): --cache, --batch 24 18000, --effort low, --dry; nur trocken geprüft, certreq unverändert. (4) Konzept-Deck (10 Folien, Certivity-Palette) als privates Claude-Artifact bei Homsianer, nicht im Repo.
- Nächster Schritt: in einer Session mit ANTHROPIC_API_KEY den Messplan aus experiments/costexp/README.md fahren (Caching 1 Lauf, Batches 2, effort low 2; Referenz E024-hs-c 0.721 / E033-hs-c 0.714, Claude strict), LEDGER-Zeilen, erst dann Schalter in certreq/llm_anthropic.py bzw. llmextract.py.
- Fallen: costexp.py lief noch nie gegen die echte API (Cache-Zählung im Patch prüfen); immer CERTREQ_LLM_CACHE=0 beim Lauf, sonst kommen alte Antworten aus dem Cache; im Deck sind 'Seite 12' (Titel/Konzept) ein Platzhalter und '0.69 nur Zeichnung' lokal gemessen (E043-a). Claim 'AP3-Rest + AP4' bleibt bewusst stehen.

### 2026-10-24 21:26:04 +0200 | [change] Pitch-Folien (AP9) als PDF im Repo | Amiad @ claude | main@6aa7984
- docs/pitch/BarelyLegal-Pitch.pdf: 5 Folien (Zeitungs-Aufmacher Tesla-Rückruf, EU R155/Macan, NHTSA 31 Mio, heute per Hand, Lösung mit Werkbank-Screenshot). Quellen in den Fußzeilen. *.pdf ist gitignored (Paketschutz), daher bewusst mit git add -f. Offen: Demo-Übergang, Score mit Schwächen, Sub-Goal, Impact, Schluss.
- Seiten per pymupdf gelesen (5 Seiten, Texte geprüft)

### 2026-10-24 21:28:14 +0200 | [decision] Keine weiteren bezahlten Kosten-/Prompt-Tests vor dem Held-out (Credits Homsianer knapp) | Homsianer @ vm | main@3019e31 +lokale Änderungen
- Abgesprochen mit Jonathan (über Homsianer). Rechnung aus belegten Läufen (Opus 5.5 Listenpreis): Held-out-großer Lauf ~4.1 $ (synthetischer Stoßfänger 529k/98k Tokens), dev-Lauf ~2.4 $, Richter dev ~2.2 $, R175-Lauf ~0.4 $. Prompt-Caching (experiments/costexp --cache) spart ~0.8 $ je Lauf, die Messung kostet ~2.5–3 $ → lohnt bei 2–3 Sonntagsläufen nicht; Ausgabe/Denken (~2 $ je Lauf) wäre nur über effort low zu senken, mit Qualitätsrisiko
- Offene Kandidaten bleiben ungemessen hinter Schalter (testcond, procedure2) bzw. im Werkzeug (costexp). Korrektur experiments/costexp/README.md: --regs ohne R42 (Claude-Auswahl von E024-hs-c hatte kein R42). Sonntag: Credits für 2 Held-out-Läufe (~8 $) + Sub-Goal einplanen; prüfen, ob Jonathans Opus-Lauf denselben Key nutzt wie der zu sperrende alte

### 2026-10-24 21:28:33 +0200 | [decision] Kein Code-Freeze: nur A (Jonathan) pausiert | Jonathan @ MacBook-Pro-von-Jonathan | main@52a6ba3 +lokale Änderungen
- Korrektur zu meinem [handoff] von 21:18 ('Pipeline eingefroren') und zum Tag best-main-sa-abend-opus: Das galt nur für A. Alle anderen arbeiten normal weiter (neue Ansätze hinter Schalter, Standard nur nach Messung umstellen). Auch Sonntag kein Code-Freeze: J taggt um 07:30 den Stand für den Held-out-Lauf; wer danach den Standard von run ändert, sagt es J vor dem Lauf.
- Geändert: STATUS Punkt 0, PLAN (Zeitplan, Sonntagsablauf), AGENTS.md §4. Entscheidung Jonathan.

### 2026-10-24 21:32:03 +0200 | [run] Plattform: X-GRAND-1-Varianten E045-a 0.705, E046-a 0.751, E047-a 0.743 | Jonathan @ MacBook-Pro-von-Jonathan | gemessen auf main@359aa91
- ohne modes 0.705 (163/190), modes+procedure2+testcond 0.751 (168), ohne modes+procedure2+testcond 0.743 (169). Opus-Standard auf der Plattform 0.762/0.721/0.743 (Mittel 0.742).
- Keine Variante über der Streuung (~0.765) → Standard bleibt; ohne modes bleibt Upload-Paar-Kandidat für den Held-out (R175 sprach dafür, dev dagegen). Ledger E045-a-P..E047-a-P.

### 2026-10-24 21:37:54 +0200 | [change] scripts/heldout-auto: Held-out So 08:00 automatisch rechnen | Jonathan @ MacBook-Pro-von-Jonathan | main@f5ac02d +lokale Änderungen
- Zieht ab 08:00 bis 10:00 minütlich das Paket nach, bis ein neuer Fall unter cases/ liegt (auch Zip von Hand nach vendor/), lädt PDFs, pull-first, drei Opus-Läufe parallel (H001 Standard + --regions, H002 ohne Cache, H003 ohne modes), Fable-Fallback, eval --record, Varianten aus H001 (ohne R94, R127/GTR 9 allein), Sub-Goal HSG1, Upload-Dateien, Commit + Log + sync, SUMMARY.md + macOS-Mitteilung. Lädt nichts hoch. Nur am 25.10. (sonst --force); --test probt am Dev-Fall ohne Commit.
- bash -n ok; Probe --test folgt; Start per LaunchAgent (nicht im Repo).

### 2026-10-24 21:39:11 +0200 | [change] Held-out-Automatik eingerichtet (launchd So 25.10. 08:00) | Jonathan @ MacBook-Pro-von-Jonathan | main@6d09c43 +lokale Änderungen
- LaunchAgent com.barelylegal.certivity-heldout (nur auf Jonathans Mac, nicht im Repo) startet scripts/heldout-auto in certivity-a; caffeinate hält den Mac bis So 10:30 wach (am Netzteil, Deckel offen lassen). PLAN Sonntagsablauf: Automatik-Absatz, reservierte IDs H001–H003, H001-*, HSG1.
- Probe --test in launchd-Umgebung am Dev-Fall: alle 4 Upload-Dateien gültig, 17 s (Cache), Belege wieder entfernt; launchctl kickstart heute: Datumssperre greift, Exit 0.

### 2026-10-24 22:00:40 +0200 | [change] Pitch: Folie 6 „Ready for a pilot.“ (Impact) angehängt | Jonathan @ MacBook-Pro-von-Jonathan | main@8452f3c +lokale Änderungen
- Im Stil von Folie 4 (Hintergrund #f3f2ee, Anton/Schibsted Grotesk, drei Karten, schwarze Karte mit roter Zahl): $3.60 und 2 min je Bauteil (synthetischer Frontstoßfänger, Opus, Listenpreis), 100 % mit Seite und Absatz, 24/24 Regelungsänderungen (E038-am-P); Satz: Richter sagt die Plattform auf 4 von 190 voraus (5 Uploads). Quelle docs/pitch/slide-06-impact.html, gerendert mit docs/pitch/render-slide.sh (Chrome headless, 3840x2160). Als Seite 6 ans PDF gehängt; @Amiad: Reihenfolge im Pitch nach Bedarf verschieben (offen bei dir: Demo-Übergang, Score, Sub-Goal, Schluss).
- PDF 6 Seiten, Textebene auf Seite 6 lesbar; Folie optisch gegen Folie 4 verglichen.

### 2026-10-24 22:02:24 +0200 | [change] Pitch Folie 6: Kosten/Zeit-Karte ersetzt durch 20/20 | Jonathan @ MacBook-Pro-von-Jonathan | main@37cead8 +lokale Änderungen
- Auf Wunsch von Jonathan ohne Geld/Zeit (bei uns schwach). Erste Karte jetzt 20/20 rules found on 10 new parts (Auswahl-Test X-SEL-llm2/X-SEL-llm2-c: alle 20 sicheren Regelungen, Lösungen vorab festgelegt); Quellenzeile angepasst.
- PDF 6 Seiten, Seite 6 ersetzt, Textebene geprüft; Folie optisch geprüft.

### 2026-10-25 00:45:01 +0200 | [change] Werkbank produktzentriert + 3D-Heckleuchte | Amiad @ claude | main@95d359f
- main@331f5e5: 41 Produkte je genau einmal, nur bestes Ergebnis (Plattform-F2 > lokaler F2 > Auswahl-F2 > jüngster Lauf); Läufe-Liste weg, Upload als Dialog; Überblick der Heckleuchte als 3D-Modell nach Explosionszeichnung (Skizze/Render).
