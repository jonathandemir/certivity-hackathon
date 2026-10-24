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
| E001 | 2026-10-24 | Jonathan | Naive Referenz: Titel-Wortüberlappung findet die Regelungen, jeder shall-Absatz ist eine Anforderung | B0: select = Wortüberlappung Spec↔Titel (≥1 Wort), extract = alle Absätze mit „shall" der base-Version | Erste Messung, keine Referenz. dev: Regelungen P 0.143 R 0.750 F2 0.405 (21 gewählt, R10 fehlt); Seiten P 0.073 R 0.849 F2 0.272; 3624 Anforderungen | übernommen als Referenz | jonathan@29c0d0b | experiments/runs/E001/ |
| E002 | 2026-10-24 | Jonathan | Diagnose: Wie gut wäre B0-Extraktion bei perfekter Auswahl? | wie E001, aber `--regs` = die 4 Gold-Regelungen des Dev-Falls (Gold-Wissen, für Held-out unzulässig) | vs E001: Regelungen F2 1.000; Seiten P 0.206 R 1.000 F2 0.565; 1214 Anforderungen (Referenz hat 190) | Diagnose, nicht übernehmen: Auswahl ist der größte Hebel, Extraktion braucht Precision | jonathan@29c0d0b | experiments/runs/E002/ |
