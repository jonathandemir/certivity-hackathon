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
| alle | | AP8 | So 07:30 Freeze, 08:00 Held-out, Uploads bis 12:45 (Zeitplan unten) |

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

## Zeitplan (Vorschlag, vom Team zu bestätigen; Sonntag = MEZ nach Zeitumstellung)

| Wann | Was |
|---|---|
| Sa bis ~16:00 | AP1 fertig: erster valider End-to-End-Upload auf dev (R1-Risiko früh beseitigen) |
| Sa ab ~16:00 | A: AP2/AP10, B: AP3/AP4, C: AP6/AP7 parallel; jede Änderung einzeln gegen die Bestmarke messen; Bestmarken taggen |
| Sa abends | Demo-Grundgerüst (AP6) läuft auf dev |
| So 07:30 | **Code-Freeze Hauptpipeline:** Standard-Einstellungen = beste gemessene Variante, Stand als `best-main-…` getaggt; danach nur noch Fixes |
| So 08:00 | Held-out holen: `scripts/setup` (zieht das Paket nach und lädt neue PDFs; `scripts/session-start` meldet neue Commits bei Certivity mit „ACHTUNG"). Zusätzlich Ankündigung vor Ort prüfen (Brief: zweites Zip). Dann Lauf von main, `certreq eval`, **sofort erster Upload als Sicherung** |
| So 08:00–12:30 | Nur einzeln gemessene Änderungen; jede hochgeladene Datei + Plattform-Score in experiments/runs/ |
| So 12:30 | Finale Auswahl der besten Datei (Entscheidung in STATUS) |
| So 12:45 | **Letzter Upload = beste Datei** (der letzte valide zählt). Danach nichts mehr hochladen |
| So 13:00 | Upload-Schluss |
| So 13:00–14:30 | Demo- und Pitch-Freeze 14:30; R4 auf der Veranstalter-Plattform einreichen (Frist dort prüfen) |
| So 15:00 | Pitch |
