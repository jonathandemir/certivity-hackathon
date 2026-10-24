# Echte Bauteile mit belegter Genehmigung (Auswahl-Test, Hauptziel)

10 reale Teile, deren UN-Regelungen der Hersteller (bzw. ein Händler-Datenblatt oder ein Homologationsschreiben)
angibt. Ergänzt `experiments/selection-suite` (synthetisch, Lösung aus Geltungsbereichen) um echte Belege.

- `<teil>/spec.md`: nur Angaben aus der Quelle (Funktion, Aufbau, Technik), **keine Regelungsnummern** (sonst wäre die
  Lösung verraten). Was die Quelle nicht nennt, steht nicht drin (z. B. Fahrzeugklasse).
- `expected.json`: `sure` = laut Quelle genehmigt (alte Einzelregelung → Sammelregelung R148/R149/R150, belegt durch deren
  Einleitung), `unsure` = vertretbar, nicht belegt, `traps` = alte, in Sammelregelungen aufgegangene Nummern u. Ä.
  `basis` zitiert die Quelle wörtlich, `source` ist die URL (abgerufen 24.10.2026).

```bash
.venv/bin/python -m certreq.suite experiments/real-parts [--select llm2] [--record X-REAL-...]
```

Grenzen: Genehmigungen gelten dem Gerät, nicht dem Einbau (R48 deshalb unsure); ein Datenblatt nennt nicht
zwingend alle zutreffenden Regelungen (R10 nur sure, wenn genannt). Requirement-Ebene: für fremde Teile gibt es
keine öffentliche Lösung, nur für dev-rear-lamp (Paket) und R175 (requirements_old.json).
