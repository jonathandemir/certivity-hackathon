# STATUS: die Gegenwart, kurz und wahr

Nur auf main ändern (über `scripts/main-wt`). Claims nur mit `scripts/claim`. Veraltetes sofort löschen,
Historie steht in docs/LOG.md.

## Stand

AP1 steht: Pipeline-Gerüst `certreq` (run/eval) mit Baseline B0, Bewertungsschleife mit Belegen.
Bestmarke (zulässig, alle Ebenen): **E020-a** = `--select llm2 --filters all --extract modal,llm` (Tag `best-main-reqf2-0.629`): Anforderungen F2 **0.629** (P 0.392, R 0.742; lokaler Richter strict), Seiten 0.936, Regelungen 0.909. Vorher E016-a (`--select llm`) 0.621, E014 (B0-Auswahl) 0.491, B0 0.060. `--select llm2` ist seit E020-a Standard (verwirft Annahmen und reine Fahrzeugebene, am synthetischen Stoßfänger: R94/R137/R128/R152/R155/R156 raus). Das ist jetzt auch der Standard von `run` ohne Schalter: `--filters all --extract modal,llm`; B0 = `--select b0 --filters none --extract none`.
**Standard von `run` seit Homsianers Umstellung: E022-hs** = `--select llm2 --filters all --extract modal,llm,lists,tables,exempt,tests,modes` (Tag `best-main-reqf2lenient-0.743`): gpt lenient **0.743** / strict 0.671 (E021-hs ohne Regeln 0.704 / 0.650). Gegenprobe mit Claude (`CERTREQ_PROVIDER=anthropic`, Richter strict = Plattform-Prognose, AP10-K3-c): E023-hs-c 0.697 → E024-hs-c 0.721; je eine Regel weggelassen (E025–E029-hs-c): modes und tables tragen den Gewinn (je ~−0.03 ohne), lists leicht, tests/exempt neutral. Bestätigt in der gpt-Reihe (A): Wiederholung ohne Cache E030-a 0.736 (Streuung ~0.01), ohne modes E031-a 0.705. Kreuzbewertung mit gleichem Maßstab (gpt-Richter lenient): Claude-Extraktion E024-hs-c **0.762** vs gpt 0.743/0.736, ohne Regeln 0.725 vs 0.704 → Claude ~+0.02; Upload-Paar hat entschieden (unten).
**Plattform (Dev-Leaderboard): Anforderungen F2 0.762** (P 0.478, R 0.895, 170/190) für **E024-hs-c** (Claude-Extraktion, alle Regeln, `CERTREQ_PROVIDER=anthropic`, Tag `best-main-platf2-0.762`). Upload-Paar: gpt-Standard E022-hs 0.725 (160/190), Claude E024-hs-c 0.762 → Claude +0.037, über der Streuung. Vorher E020-a 0.687. Seiten und Regelungen identisch mit lokal. Lokale Prognose der Anforderungsebene: `eval --judge lenient` (153 statt 154 Treffer), strict = Untergrenze (AP10-K2).
Streuung (E019-a): identische Konfiguration ohne Cache 0.602 statt 0.621 → Unterschiede < ~0.03 sind nicht belastbar. AP5 (Zeichnung) fertig: `--vision auto` liest die Zeichnung, wenn keine Spec vorliegt (nur Zeichnung: F2 0.417, E017-a).
Anforderungs-Engpässe (E016-a): Recall je Regelung R10 14/32, R48 40/56, R150 33/39, R148 54/63; 376 eingereicht (Referenz 190), davon 30 aus den Extra-Regelungen R26/R13H/R42 (beim Stoßfänger vermutlich richtig, daher bewusst behalten).
Diagnose E002: Mit den richtigen Regelungen findet B0 alle 53 Gold-Seiten → größter Hebel ist die Auswahl (AP2),
danach Precision der Extraktion (AP4: 1214 statt ~190 Anforderungen).
Teamname: **BarelyLegal**. Team-ID der Certivity-Plattform: **team-12** (registriert 2026-10-24; Standard in `certreq/submission.py`, Passwort nicht im Repo).

## Team

| Name | Rolle | Rechner | Fokus |
|---|---|---|---|
| Jonathan Demir | A | MacBook-Pro-von-Jonathan | AP2 Auswahl, AP10 Richter, AP5 Vision, LLM-Zugang, Uploads |
| Homsianer | B | vm (Claude Code Cloud) | AP3-Rest Gliederung/Tabellen, AP4 Relevanzfilter + Zerlegung |
| Amiad | C | Fedora-Laptop (Claude über Cowork) | AP6 Demo, AP7 Sub-Goal, AP9 Pitch-Lead |

Alle arbeiten auf main. „Rechner" trägt jeder nach `scripts/setup` selbst ein. Details: docs/PLAN.md „Aufteilung".

## Claims

| Wer | Rechner | Was | Dateien | Seit |
|---|---|---|---|---|
| Jonathan | MacBook-Pro-von-Jonathan | AP3-Rest Gliederung + AP4 Relevanzfilter (B vorgezogen, Übergabe an Omar) | certreq/pdf.py, certreq/extract.py, tests/test_extract.py | 2026-10-24 14:10 |
| Jonathan | MacBook-Pro-von-Jonathan | AP4 LLM-Extraktion je Absatz (Relevanz + Zerlegung) | certreq/llmextract.py, tests/test_llmextract.py, certreq/extract.py | 2026-10-24 14:42 |
| Homsianer | vm | AP3-Rest + AP4 (Übernahme von Jonathan): Parser, Relevanzfilter, LLM-Extraktion, GTR Teil II, R10 | certreq/pdf.py, certreq/extract.py, certreq/relevance.py, certreq/llmextract.py, tests/test_extract.py, tests/test_llmextract.py, tests/test_outline.py | 2026-10-24 14:16 |
| Homsianer | vm | Anthropic-Zugang hinter Schalter CERTREQ_PROVIDER=anthropic (Standard bleibt OpenAI; Homsianer hat nur Anthropic-Key) | certreq/llm_anthropic.py (neu), certreq/llm.py (nur Anbieter-Schalter in model_name/_call/_check), certreq/judge.py (nur config.model), requirements.txt (+anthropic), tests/test_llm.py | 2026-10-24 17:04 |

## Nächste Schritte

0. **Übergaben für den Abend (A, Sa 24.10. ~19:45), Freeze So 07:30.** Hintergrund: Opus ist auf dev im Mittel gleich gpt (0.740, ±0.02),
   außerhalb von dev klar besser (R175 +0.07); Sub-Goal auf dev ausgereizt (24/24, Change accuracy 1.000).
   **B (Homsianer) erledigt 20:05:** `duties` und `testcond` gebaut und gemessen (Claude-Richter strict, je 2 Läufe; Ledger X-R175-C-cj, X-R175-hs-duties/testcond, E041/E042-hs-c). `duties`: R175 0.642 → 0.623 → verworfen. `testcond`: R175 0.638 (Prüfbedingungen 6–7 → 9–10/13), dev 0.707 vs 0.718 → nicht Standard, hinter Schalter. **Vorschlag an A (Weg A):** am Held-out ein Upload-Paar H001 vs H00x mit `--extract modal,llm,lists,tables,exempt,tests,modes,testcond` (neuer Lauf), falls R127/GTR 9 gewählt sind – dort sind Prüfbedingungen der Kern. Standard bleibt E022-hs. Der Auftrag lautete:
   **B (Homsianer): zwei neue Prompt-Regeln für den Held-out, je hinter Schalter in `llmextract.RULES`.**
   (1) `duties`: Pflichten von Hersteller oder Technischem Dienst, die das Bauteil betreffen („shall declare / demonstrate /
   document / justify … to the Approval Authority or Technical Service“), sind Anforderungen, behalten. Beleg: mit Opus fehlen auf
   R175 22 Anforderungen, 11 davon diese Art (X-R175-C und C-rep identisch); auf dev fanden wir alle 18 dieser Art, also prüfen,
   dass dev nicht verliert. (2) `testcond`: Prüfbedingungen, unter denen das Bauteil die Anforderung erfüllen muss (Prüffläche,
   Umgebung, Geschwindigkeit, Prüfziel, Ausgangszustand), sind Anforderungen; nur der Messaufbau nicht. Beleg: die übrigen 11
   Lücken auf R175 (6.2.x, 6.5); R127/GTR 9 beim Stoßfänger bestehen großteils aus Prüfbedingungen. Achtung: die Regel `tests`
   schließt bisher den „physical arrangement of the test set-up“ aus, `testcond` darf R10 auf dev nicht verschlechtern.
   **Messen:** je Regel Opus auf dev und auf dem R175-Prüfstein, je 2 Läufe (2. mit `CERTREQ_LLM_CACHE=0`), Basis und Variante mit
   demselben Richter (Befehle: `experiments/synthetic/acpe/README.md`). Übernehmen nur, wenn die Regel auf beiden nicht verliert
   und auf mindestens einem mehr als die Streuung (~0.02) gewinnt. Bis 07:30 Standard umstellen oder hinter Schalter lassen.
   Nebenbefund (Precision, niedrigere Priorität): R150 Annex 6 überzerlegt (dev 30 vs Gold 8, Annex 7: 7 vs 0), X-SMOKE-a.
   **C (Amiad):** (a) Demo komplett proben auf dem Pitch-Rechner: synthetischer Stoßfänger einmal mit Spec, einmal nur Zeichnung
   (`--vision only`), ohne Handgriffe, jede Anforderung verlinkt auf ihre PDF-Seite; Ergebnis für So vorrechnen (Cache).
   (b) Sub-Goal-Gegenprobe für `--refine llm` auf einem großen Paar (z. B. R48 base→latest): läuft durch, Laufzeit, Fehlalarme
   in einer Stichprobe. (c) Pitch-Belege: Richter gegen Plattform geeicht (5 Uploads, −1/+4/0/+1/0 Treffer), Gegenproben
   außerhalb von dev (R175-Prüfstein, Auswahl-Test mit 10 Bauteilen und vorab festgelegten Lösungen), offene Schwächen
   (Opus-Streuung ±0.02, nur Zeichnung 0.42, Hersteller-Pflichten).
   **A (Jonathan):** R4 vorbereiten (Abgabe-Kopie ohne Historie, `scripts/export-snapshot`), Sonntag Lauf + Uploads nach PLAN
   „Sonntagsablauf“. **Homsianer:** alten Anthropic-Key widerrufen (steht in der Git-Historie).
1. **Alle: priorisierte Verbesserungsliste in docs/PLAN.md „Verbesserungen nach Punkten"** (Plattform-Eichung + Fehleranalyse E020-a).
   Messen mit `eval --judge lenient` (= Plattform ±1 Treffer) und `--judge strict` (Untergrenze).
2. **Erledigt (A):** Team BarelyLegal registriert (team-12), alle drei im Repo; LLM-Zugang (`certreq/llm.py`); Plattform-Eichung
   (E020-a-P F2 0.687, E008-a-P, E003-am-P, AP10-K2). Upload-Dateien: `.venv/bin/python -m certreq.upload <IDs>` → `out/upload/`.
3. **A als Nächstes:** Bitte von C umsetzen (Bildregion je Bauteil aus `vision.py` in `.meta.json`), Sonntag-Ablauf vorbereiten
   (R127/GTR 9 und R26/R42 per Upload-Paar entscheiden), R4 vorbereiten (Historie vor dem Öffnen des Repos prüfen).
4. **B (Homsianer):** erledigt: Standard `run` = E022-hs (5 Prompt-Regeln); GTR-Teil I raus; R10-Appendices; Anthropic-Zugang hinter `CERTREQ_PROVIDER=anthropic` (Claude-Reihe E023–E031-hs-c, Claude-Richter geeicht: strict ≈ Plattform, AP10-K3-c). Verworfen: `vehicle` (E030-hs-c), `optional` (E035-hs-c), `complete` (E036-hs-c). Neutral hinter Schalter: `procedure`/`procedure2` (E031/E032/E034-hs-c). Streuung der Claude-Reihe ~0.007 (E033-hs-c). Prompt-Arbeit damit ausgereizt (LEARNINGS). Offen (klein, unter 0.01): Dubletten in Gold-Absätzen (Prio 2), R48 6.14.5 ohne Pflichtwort (Prio 4). **A (R4):** Die Git-Historie enthält einen Anthropic-Key (`.env`, Commits d3d3b7b/a87a74f, Datei gelöscht in 33ee39b): vor dem Öffnen des Repos muss er widerrufen sein, sonst Historie bereinigen (Force-Push nur nach Team-Entscheidung).
   **C (Demo):** `demo/server.py` MODES angepasst (abgesprochen über Homsianer): „best" = Standard von `run` (jetzt `--select llm2`), „fast" = `--select b0 --filters none --extract none` (sonst bräuchte fast nach der Umstellung einen Key). Bitte demo/README.md Zeile „Prüfungen" nachziehen.
   **C (Sub-Goal):** hochgeladen (A, 19:30/19:31): E037-am Flag-Recall 1.000, Precision 0.923, Change accuracy 0.957; **E038-am**
   **C → A/B (bitte mit euren Credits prüfen, Amiads Kontingent ist leer), Beleg experiments/runs/X-GRAND-1/report.md:**
   (1) Extraktion „ohne modes“: dev 0.698→0.715, R175 0.615→0.650 (je 1 Lauf, Claude strict). Widerspricht E031-a (gpt, dev −0.035 ohne modes) → 2 Wiederholungen ohne Cache auf dev + R175, dann ggf. Upload-Paar.
   (2) Extraktion „+procedure2 +testcond“: dev 0.698→0.737, R175 0.615→0.610 (je 1 Lauf). Einzeln waren beide neutral (E032/E034, E041/E042) → Kombination wiederholen.
   (3) Kombination ohne modes +procedure2 +testcond: ungetestet. Befehl: `CERTREQ_PROVIDER=anthropic .venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/dev-rear-lamp --extract modal,llm,lists,tables,exempt,tests,procedure2,testcond`, dann Upload gegen Opus-Mittel 0.742.
   (4) Auswahl-Zusatzregeln „Lichtquelle ≠ Leuchte“ + „Ersatzteil nur nach Ersatzteil-Regelung“ (Text in certreq/grand.py RULE_LIGHTSOURCE/RULE_REPLACEMENT): Suiten 0.960/0.926/0.909 → 1.000/0.962/1.000, Stoßfänger und dev unverändert → kann A in select.SYSTEM2 aufnehmen (kein Score-Effekt auf dev erwartet). NICHT übernehmen: Regel „Fahrzeug-Regelungen raus“ (verliert R127 am Stoßfänger).
   Wiederholen: `.venv/bin/python -m certreq.grand [--only select|extract|subgoal]` (alles ≈ 10 M Tokens, extract allein ≈ 7 M).
