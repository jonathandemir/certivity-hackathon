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

| AP | Inhalt | Fertig, wenn |
|---|---|---|
| AP1 | Gerüst + Bewertungsschleife: ein Befehl `case-ordner → out/<case>.json`; danach validate.py, score_local.py, F2-Berechnung, Ablage in experiments/runs/<ID>/ | Erster valider Upload auf `dev-rear-lamp`, Score im Scoreboard |
| AP2 | Regelungsauswahl: Spec + Teileliste → zutreffende Regelungen aus `index.json` (Titel, Scope-Absatz der PDFs) | Regelungs-F2 auf dev gemessen; Begründung je Regelung für die Demo |
| AP3 | PDF-Aufbereitung: base-PDFs → Text je Seite + Absatznummern + Absatz→Seite-Zuordnung (Cache unter `out/`) | Stichprobe: Absatz → richtige Seite für die 53 Gold-Seiten des Dev-Falls |
| AP4 | Anforderungsextraktion: relevante Absätze → eine Pflicht pro Anforderung, Seite + Absatz | Seiten-F2 lokal, Anforderungs-F2 auf der Plattform gemessen |
| AP5 | Vision: Explosionszeichnung → Teile + Funktionen | Teileliste der Dev-Zeichnung stimmt mit spec.md überein |
| AP6 | Demo/UI: Eingabe → Liste mit Links auf PDF-Seite (`#page=N`), Begründung je Regelung | Läuft end-to-end ohne Handgriffe auf dem Dev-Fall |
| AP7 | Sub-Goal: Absatz-Diff alt/neu → modified/removed/added + reason | Recall auf `subgoal-dev` gegen expected.json gemessen |
| AP8 | Held-out-Lauf + Upload-Strategie (So) | Beste Datei ist der letzte valide Upload vor 13:00 |
| AP9 | Pitch: Lösung, Demo, Beleg aus LEDGER, Schwächen | Probedurchlauf vor 14:30 |

## Zeitplan (Vorschlag, vom Team zu bestätigen; Sonntag = MEZ nach Zeitumstellung)

| Wann | Was |
|---|---|
| Sa bis ~16:00 | AP1 fertig: erster valider End-to-End-Upload auf dev (R1-Risiko früh beseitigen) |
| Sa ab ~16:00 | AP2–AP7 parallel; jede Änderung einzeln gegen die Bestmarke messen; Bestmarken taggen |
| Sa abends | Demo-Grundgerüst (AP6) läuft auf dev |
| So 07:30 | **Code-Freeze Hauptpipeline:** beste gemessene Version nach main gemergt und getaggt |
| So 08:00 | Held-out holen (`git -C vendor/industrial-ai-hackathon pull` + Ankündigung), PDFs nachladen, Lauf von main, validate, **sofort erster Upload als Sicherung** |
| So 08:00–12:30 | Nur einzeln gemessene Änderungen; jede hochgeladene Datei + Plattform-Score in experiments/runs/ |
| So 12:30 | Finale Auswahl der besten Datei (Entscheidung in STATUS) |
| So 12:45 | **Letzter Upload = beste Datei** (der letzte valide zählt). Danach nichts mehr hochladen |
| So 13:00 | Upload-Schluss |
| So 13:00–14:30 | Demo- und Pitch-Freeze 14:30; R4 auf der Veranstalter-Plattform einreichen (Frist dort prüfen) |
| So 15:00 | Pitch |
