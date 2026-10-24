# LEDGER: eine Zeile pro Versuch

Nur auf main anhängen (über `scripts/main-wt`), nie Zeilen löschen; eine spätere Korrektur ist eine neue Zeile.
`merge=union` erlaubt paralleles Anhängen.

Regeln:
- Entscheidungen fallen anhand echter Messungen (score_local.py, Plattform-Score), nicht anhand von Simulation oder Bauchgefühl.
- Jede Änderung einzeln gegen die **aktuelle Bestmarke** messen (Spalte „Ergebnis vs. Referenz" nennt die Referenz-ID).
- Commit = gemessener, gepushter, sauberer Stand `<branch>@<kurzhash>` (Ausgabe von `scripts/pull-first`), nie erfunden.
- Beleg = Datei unter `experiments/runs/<ID>/` (Ausgabe-JSON, Score-Ausgabe, Plattform-Screenshot-Text) oder Logeintrag.
- Übernommen + neue Bestmarke → Scoreboard in docs/STATUS.md und `scripts/tag-best <wert>`.
- Verworfen → kurzer Eintrag in docs/LEARNINGS.md „Verworfen", wenn die Erkenntnis allgemein gilt.

ID-Schema: `E001`, `E002`, … (fortlaufend; bei gleichzeitigem Anhängen mit Kürzel eindeutig machen, z. B. `E014-jd`).
Metriken: F2 je Ebene, z. B. `reg 1.00 / page 0.71 / req 0.43 (Plattform)`.

| ID | Datum | Wer | Hypothese | Änderung | Ergebnis vs. Referenz | Entscheidung | Commit | Beleg |
|---|---|---|---|---|---|---|---|---|
