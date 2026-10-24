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
