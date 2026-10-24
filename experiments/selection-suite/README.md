# Auswahl-Test: 10 synthetische Bauteile

Prüft Stufe 1 (Regelungsauswahl) an Bauteilen außerhalb des Dev-Falls, mit Fallen aus dem Index: zusammengelegte
Regelungen (R19/R123 → R149, R3/R104 → R150), Fahrzeugklasse (R131 nur M2/M3/N2/N3), alt gegen neu (R116/R163),
Fahrzeugebene (R94, R137, R155), Bauteile ohne Querschnittsregelung (Windschutzscheibe, Schalldämpfer).

- `<bauteil>/spec.md`: synthetische Spec (vom Team geschrieben, keine Paketdaten).
- `expected.json`: vorab festgelegte Lösung aus den Geltungsbereichen (sure / unsure / traps), committet vor dem
  ersten Lauf. Nicht nachträglich an Modellantworten anpassen; begründete Korrekturen nur mit Logeintrag.

```bash
.venv/bin/python -m certreq.suite experiments/selection-suite [--select llm2] [--record <ID>]
```

Bewertung je Bauteil: Treffer = gewählt ∩ sure, Fehlend = sure − gewählt, Fehlauswahl = gewählt − (sure ∪ unsure);
Summe über alle Bauteile → P, R, F2. Grenzen: Die Lösung ist unser Urteil aus den Geltungsbereichen, nicht
Certivitys Gold (z. B. R10 bei Elektronik nach dem einen Dev-Beleg). Der Test misst nur die Auswahl, nicht die Extraktion.
