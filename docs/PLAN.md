# PLAN: Ziele, Arbeitspakete, Zeitplan

Nur auf main ändern. Änderungen am Plan sind `[decision]`-Einträge im LOG.

## Ziele (nach Gewicht der Jury, docs/CONTEXT.md §5)

1. **Held-out-Score (40 %):** höchstes F2 auf `heldout-front-bumper` auf Ebene Regelungen, Seiten, Anforderungen.
   Pflicht: valider Upload vor So 13:00 (R1, R2).
2. **Demo (20 %):** Spec/Zeichnung rein, Anforderungsliste raus, ohne manuelle Schritte (R3), jede Anforderung
   verlinkt auf ihre PDF-Seite.
3. **Sub-Goal (15 %):** Änderungsliste für `subgoal-heldout`.
4. **Impact + Pitch (25 %):** zeigen, was gemessen wurde und wo die Lösung schwach ist.

**Größtes Risiko: Überanpassung an den einzigen Dev-Fall.** Dev ist eine Heckleuchte (Lichttechnik: R148, R48,
R150, R10), Held-out ist ein Frontstoßfänger, dort gelten vermutlich andere Regelungen. Regelungsauswahl und
Extraktion müssen generisch sein; keine Regel, die nur auf Leuchten passt. Wer eine Heuristik aus dem Dev-Fall
ableitet, notiert in LEARNINGS, ob sie für einen Stoßfänger plausibel ist.

## Arbeitspakete

Owner per `scripts/claim`. Fertig = Kriterium erfüllt, gemessen, geloggt, gepusht.

| AP | Inhalt | Fertig, wenn | Wer |
|---|---|---|---|
| AP1 | Gerüst + Bewertungsschleife: ein Befehl `case-ordner → out/<case>.json`; danach validate.py, score_local.py, F2-Berechnung, Ablage in experiments/runs/<ID>/ | Erster valider Upload auf `dev-rear-lamp`, Score im Scoreboard. **Stand: Code fertig (E001), Upload offen** | A |
| AP2 | Regelungsauswahl: Steckbrief je Regelung (Geltungsbereich aus Absatz 1, Bauteilarten, Ebene Bauteil/Fahrzeug, ersetzt durch …); Schluss Teile → Eigenschaften → Regelungen | Regelungs-F2 auf dev gemessen (E001: 0.405); Begründung je Regelung für die Demo | A |
| AP3 | PDF-Aufbereitung: Absätze + Seite **erledigt** (121/121 Referenz-Absätze). Offen: Gliederung (Überschriften-Hierarchie je Absatz), Tabellen | Jeder Absatz kennt seine Abschnittsüberschriften; Tabellen-Pflichten der Referenz (z. B. R150 „Table 3") auffindbar | B |
| AP4 | Extraktion: Relevanzfilter entlang der Gliederung (betrifft der Abschnitt unser Teil? richtet er sich an den Bauteilhersteller?), dann Zerlegung in eine Pflicht pro Bedingung/Grenzwert | Seiten-F2 lokal und Anforderungs-F2 (AP10-Richter, gelegentlich Plattform) besser als E001 | B |
| AP5 | Vision: Explosionszeichnung → Teile + Funktionen (Eingabe für AP2). **Stand: erledigt** (`--vision auto`, E017-a/E018-a) | Teileliste der Dev-Zeichnung stimmt mit spec.md überein. Ergebnis: Leuchte, Lichtscheibe, LED-Felder, Rückfahrfach erkannt; Rückstrahler auf der Zeichnung nicht erkennbar (als unsicher gemeldet) | A |
| AP6 | Demo/UI: Eingabe → Liste mit Links auf PDF-Seite (`#page=N`), Begründung je Regelung | Läuft end-to-end ohne Handgriffe auf dem Dev-Fall | C |
| AP7 | Sub-Goal: Absatz-Diff alt/neu → modified/removed/added + reason | Recall auf `subgoal-dev` gegen expected.json gemessen | C |
| AP8 | Held-out-Lauf + Upload-Strategie (So) | Beste Datei ist der letzte valide Upload vor 13:00 | alle, Uploads: A |
| AP9 | Pitch: Lösung, Demo, Beleg aus LEDGER, Schwächen | Probedurchlauf vor 14:30 | C (Lead), alle |
| AP10 | Lokaler LLM-Richter: unsere Anforderungen 1:1 nach Bedeutung gegen expected.json abgleichen wie die Plattform (gleicher Geltungsbereich, Bedingung, Grenzwert) | P/R/F2 der Anforderungsebene lokal in Minuten; einmal gegen den Plattform-Score von E001 geeicht | A |

## Aufteilung (beschlossen 2026-10-24, Jonathan)

Alle arbeiten direkt auf main (AGENTS.md §4); die Dateigrenzen unten ersetzen die getrennten Branches.

| Person | Wer | Pakete | Reihenfolge |
|---|---|---|---|
| **A** | Jonathan | AP2, AP10, AP5, AP1-Rest; LLM-Zugang; Plattform-Uploads | 1. LLM-Zugang festlegen (Modell, Key in `.env`, nie ins Repo) und gemeinsamen Client `certreq/llm.py` bereitstellen, weil B und C ihn brauchen · 2. AP10 Richter · 3. AP2 Auswahl · 4. AP5 Vision |
| **B** | Homsianer | AP3-Rest, AP4 | 1. Gliederung/Überschriften im Parser · 2. Relevanzfilter je Abschnitt · 3. Zerlegung in einzelne Pflichten · 4. Tabellen |
| **C** | Amiad | AP6, AP7, AP9-Lead | 1. Demo-Gerüst auf E001-Ausgabe · 2. Sub-Goal auf `subgoal-dev` · 3. Demo fertig machen (So vormittags) · 4. Pitch |
| alle | | AP8 | So 07:30 Freeze, 08:00 Held-out, letzter Upload 12:30 („Sonntagsablauf“ unten) |

**Wer ändert welche Dateien** (vermeidet Konflikte; Ausnahmen vorher per Claim ankündigen):
- A: `certreq/select.py`, `certreq/llm.py`, `certreq/judge.py`, `certreq/vision.py`, `certreq/evaluate.py`, `certreq/submission.py`
- B: `certreq/extract.py`, `certreq/pdf.py`
- C: `demo/`, `certreq/subgoal.py`
- gemeinsam, nur kleine Änderungen mit Claim: `certreq/__main__.py` (CLI), `requirements.txt`, `tests/`

**Schnittstellen, damit niemand auf jemanden wartet:**
- A → B: Bis die Auswahl gut ist, misst B mit vorgegebenen Regelungen (`--regs "UN R148,UN R48,UN R150,UN R10"`, Diagnose wie E002), damit Extraktion und Auswahl getrennt messbar bleiben.
- A → B: Der Richter (AP10) wird B's Hauptmessgröße für die Anforderungsebene; bis dahin Seiten-F2 lokal.
- A/B → C: Die Demo liest nur `out/<fall>.json` + `.meta.json` (Format steht, E001 ist ein Beispiel). A liefert dazu die Begründung je Regelung in `.meta.json`.
- C nutzt für das Sub-Goal `certreq.pdf.parse_pdf` auf alter und neuer Version (Absätze mit Seite).

## Verbesserungen nach Punkten (Stand 16:35, aus Plattform-Eichung und Fehleranalyse E020-a)

Hauptscore dev auf der Plattform: F2 0.687 (P 0.428, R 0.811). 207 von 360 Anforderungen ohne Treffer, 37 von 190
Gold-Pflichten fehlen (experiments/runs/E020-a/analyse.json). Messung lokal mit `eval --judge lenient` (= Plattform
±1 Treffer) und `--judge strict` (Untergrenze); jede Änderung einzeln, Streuung ±0.02 beachten.

| Prio | Wer | Was | Beleg / erwarteter Effekt |
|---|---|---|---|
| 1 | B | **Anwendbarkeit je Absatz** wie `--select llm2`, eine Ebene tiefer: verwerfen, was nur das Fahrzeug ausrüstet („Presence: mandatory on vehicles …"), Varianten, die die Spec nicht hat (S3/S4-Bremsleuchte, bewegliche/versenkbare Leuchten, asymmetrische Fahrzeuge, Anhänger-Dreiecke), reine Verwaltung, reine Prüfabläufe | 139 Treffer-lose aus Nicht-Gold-Absätzen (R48 General specs 60, R48 Individual 15, R148 14, R150 Prüfungen 20, R10 Prüfverfahren ~20). Ohne Trefferverlust: Precision 0.43 → ~0.69, F2 → ~0.78 (Obergrenze) |
| 2 | B | **Überzerlegung/Dubletten**: Varianten derselben Pflicht nicht einzeln ausgeben (z. B. R148 3.3.3.4 dreimal „marking of rated voltage …") | 39 überzählige Anforderungen in Gold-Absätzen; F2 ~+0.02 |
| 3 | B | **Recall R10 (EMV)**: Prüfpegel je Puls/Stufe als Einzelpflichten (R10 6.9.1 = 10 Gold-Anforderungen) | 17 der 37 Fehlenden sind R10 |
| 4 | B | **Fehlende ohne jede Extraktion** prüfen (Filter oder LLM verwirft Gold-Absatz, z. B. R48 5.18, 6.14.5) | 13 der 37 Fehlenden |
| 5 | A | Sonntag: **R127 vs GTR 9** und **R26/R42** per Upload-Paar entscheiden (mit/ohne), nicht vorher raten | dev: R26/R42 kosten 14 Treffer-lose (~0.01 F2) |
| 6 | C | **Sub-Goal**: Recall der `added` (13/17), Change accuracy 0.889; lokale Messung der Change accuracy fehlt; Held-out-Sub-Goal ist eine andere Regelung | Plattform E003-am-P: Recall 0.792, Precision 0.760 |
| 7 | C | **Demo-Pflicht R3 prüfen**: Spec **oder** nur Zeichnung → Anforderungen ohne Handgriffe; jede Anforderung verlinkt auf ihre PDF-Seite; Auswahl-Begründungen (`.meta.json` `selection`) zeigen; neuer Fall dauert ~4 min → Held-out-Ergebnis vorab rechnen, Live-Demo aus Cache | Jury: Demo 20 % |
| 8 | alle | **Pitch-Belege**: Richter gegen Plattform geeicht (±1 Treffer), 20+ gemessene Versuche im Ledger, Schwächen offen (Streuung ±0.02, Zeichnung allein 0.42, EMV-Recall) | Pitch 10 % + Impact 15 % |
| 9 | A | **R4 vorbereiten**: Repo wird abgegeben → vor dem Öffnen prüfen, dass keine Paketdaten in der Historie sind; Basisfragen + Demo-Link | Pflicht R4 |

## Zeitplan (Vorschlag, vom Team zu bestätigen; Sonntag = MEZ nach Zeitumstellung)

| Wann | Was |
|---|---|
| Sa bis ~16:00 | AP1 fertig: erster valider End-to-End-Upload auf dev (R1-Risiko früh beseitigen) |
| Sa ab ~16:00 | A: AP2/AP10, B: AP3/AP4, C: AP6/AP7 parallel; jede Änderung einzeln gegen die Bestmarke messen; Bestmarken taggen |
| Sa abends | Demo-Grundgerüst (AP6) läuft auf dev |
| So 07:30–12:30 | **Held-out nach „Sonntagsablauf“ (unten)**: Code-Freeze 07:30, Lauf mit Opus 5.5 ab 08:00, Sicherungs-Upload, Upload-Paare, letzter Upload = beste Datei um 12:30 |
| So 13:00 | Upload-Schluss |
| So 13:00–14:30 | Demo- und Pitch-Freeze 14:30; R4 auf der Veranstalter-Plattform einreichen (Frist dort prüfen) |
| So 15:00 | Pitch |

## Sonntagsablauf (Held-out)

Zeiten MEZ: in der Nacht springt die Uhr 03:00 → 02:00. Stand Sa 24.10. abends, beschlossen: Held-out mit Opus 5.5
(STATUS „Entscheidungen“). Rollen: **Jonathan** Lauf + Uploads (Anthropic-Key und Plattform-Login auf seinem Rechner),
**Homsianer** Bereitschaft für Pipeline-Fehler (nach 07:30 nur Fixes, kein Tuning), **Amiad** Sub-Goal-Held-out + Demo
mit dem Held-out-Ergebnis. Held-out-Eingaben nie ins Repo (Lizenz), nur eigene Ausgaben und Scores.

| Wann | Wer | Schritt | Befehl / Kriterium |
|---|---|---|---|
| 07:30 | alle | Code-Freeze: alles gepusht, Tests grün, Stand taggen | `scripts/sync`, `scripts/tag-best freeze-so` |
| 07:45 | J | Key und Modell prüfen | `CERTREQ_PROVIDER=anthropic .venv/bin/python -m certreq.llm` |
| 08:00 | J | Held-out holen; Ordner prüfen (erwartet `cases/heldout-front-bumper`, `subgoal/heldout`). Kommt er als Zip (Brief): nach `vendor/industrial-ai-hackathon/` entpacken, dann `python tools/fetch_regulations.py` im Paket | `scripts/setup`, `ls vendor/industrial-ai-hackathon/cases vendor/industrial-ai-hackathon/subgoal` |
| 08:05 | J | Lauf H001 (2–4 min) und ablegen | `scripts/pull-first`, dann `CERTREQ_PROVIDER=anthropic .venv/bin/python -m certreq run vendor/industrial-ai-hackathon/cases/heldout-front-bumper --out out/H001.json`, dann `.venv/bin/python -m certreq eval out/H001.json --record H001` (nur Validierung), commit + `scripts/sync` |
| 08:15 | J | **Sicherungs-Upload H001** | `.venv/bin/python -m certreq.upload H001` → `out/upload/H001-heldout-front-bumper.json` hochladen; Score nach `experiments/runs/H001/platform.json`, Ledger-Zeile, `[run]`-Log |
| 08:15 | J | Zeigt die Plattform beim Held-out einen Score? → Weg A, sonst Weg B | |
| 08:20 | J+H | Auswahl ansehen: Regelungen, Gründe, Anforderungen je Regelung | `out/H001.meta.json` (`selection`), `.venv/bin/python -m certreq.variants H001 --list` |
| 08:05 | A | Sub-Goal-Held-out rechnen, ablegen; Upload über J (eigenes Kontingent) | `.venv/bin/python -m certreq.subgoal run vendor/industrial-ai-hackathon/subgoal/heldout --out out/subgoal-heldout.json`, Variante nach dem Dev-Plattformvergleich E037-am vs E038-am |
| 12:00 | J | Beste Datei festlegen (nur nach Plattform-Score bzw. Weg B), Eintrag in STATUS | |
| 12:30 | J | **Letzter Upload = beste Datei**, auch wenn sie schon einmal oben war (der letzte valide zählt). Danach keine Uploads mehr | `.venv/bin/python -m certreq.upload <ID>` |

**Weg A: Score sichtbar → Upload-Paare gegen H001**, je Paar genau eine Änderung, höchstens 5 Uploads pro Stunde
(etwa einer alle 12 min). Varianten ohne neuen LLM-Lauf (`certreq.variants`, übrige Anforderungen byte-gleich):
1. R94 gewählt? → `certreq.variants H001 --drop "UN R94" --as H001-noR94` (Opus nahm R94 am synthetischen Stoßfänger, X-BUMPER-c).
2. R127 und GTR 9 beide gewählt? → `--drop "UN GTR 9" --as H001-noGTR9`, danach `--drop "UN R127" --as H001-noR127`.
3. R26 bzw. R42 nur testen, wenn Zeit bleibt (beim Stoßfänger vermutlich richtig).
4. `modes` (R175-Prüfstein: kostet dort ~5 Treffer): Neulauf H002 mit `--extract modal,llm,lists,tables,exempt,tests`
   (neuer LLM-Lauf, Streuung ~0.01).
Übernehmen nur bei mehr als ~0.01 F2 Gewinn; Gewinne kombinieren (mehrere `--drop`) und die Kombination ebenfalls hochladen.
5. Opus streut auf dev ±0.02 je Lauf (E039-a/E040-a): gleich nach H001 einen zweiten Lauf H002 (gleiche Einstellungen,
   `CERTREQ_LLM_CACHE=0`) rechnen und hochladen; der bessere Wurf ist die Basis für die Varianten 1–3.

**Weg B: kein Score → nicht spielen, nichts weglassen.** H001 bleibt die Abgabe (bzw. der Fallback-Lauf). Grund F2-Asymmetrie:
eine überzählige Regelung kostet ~0.01 F2 (dev: R26/R42 zusammen ~0.016, Nebelscheinwerfer: 4 falsche Regelungen = 11 von
303 Anforderungen), eine fehlende mit ~20 Gold-Anforderungen ~0.08. Weglassen lohnt nur, wenn die Regelung mit über ~90 %
falsch ist; das gilt auch für R94. Keine weiteren Uploads.

**Fallbacks:** Opus-Fehler oder Rate-Limit → Lauf ohne `CERTREQ_PROVIDER` (gpt-Standard, ~3 min) als H001-gpt.
Validierungsfehler der Plattform → `python tools/validate.py <datei>` zeigt den JSON-Pfad. Schief gelaufener Upload
→ beste bisherige Datei erneut hochladen (alle liegen unter experiments/runs/).

