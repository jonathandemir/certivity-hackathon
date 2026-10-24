# Echte Bauteile mit belegter Genehmigung (Auswahl-Test, Hauptziel)

28 reale Teile, deren UN-Regelungen eine echte Quelle angibt: Hersteller-Datenblatt, Genehmigungsbescheid,
Homologationsschreiben oder Händler-Datenblatt. Ergänzt `experiments/selection-suite` (synthetisch, Lösung aus
Geltungsbereichen) um belegte Lösungen. Abgerufen am 24.10.2026.

## Gegen Overfitting: tune/ und holdout/

- `tune/` (18 Teile): darf man ansehen, Fehler analysieren, Prompts danach verbessern.
- `holdout/` (10 Teile): **nur messen, nie danach abstimmen.** Wer einen Fehler im Holdout „repariert", macht ihn zum
  Tune-Fall und muss das loggen. Verbessert sich tune, aber nicht holdout, war es Overfitting.
- Die Aufteilung ist vorab festgelegt und mischt die Arten (Leuchten, Auspuff, LPG, Elektronik, Reflexstoffe, ein Teil
  ohne Index-Regelung).

```bash
.venv/bin/python -m certreq.suite experiments/real-parts/tune    [--select llm2] [--record X-REAL-T-...]
.venv/bin/python -m certreq.suite experiments/real-parts/holdout [--select llm2] [--record X-REAL-H-...]
```

## Wie die Lösung festgelegt ist

- `<teil>/spec.md`: nur Angaben aus der Quelle (Funktion, Aufbau, Technik), **keine Regelungsnummern** (sonst wäre die
  Lösung verraten). Was die Quelle nicht nennt, fehlt (z. B. Fahrzeugklasse).
- `expected.json` je Ordner: `sure` = laut Quelle genehmigt. Nennt die Quelle eine alte Einzelregelung, die laut
  Einleitung von R148/R149/R150 in diese Sammelregelung aufgegangen ist (R3, R6, R7, R19, R23, R38, R87, R91, R104),
  ist die Sammelregelung `sure` und die alte Nummer eine Falle (wie im Dev-Gold, docs/CONTEXT.md §10).
  `unsure` = vertretbar, aber nicht belegt (R48-Anbau, R10 ohne Angabe, Regelung hinter einer Genehmigungsnummer
  ohne Regelungsangabe). `basis` zitiert die Quelle wörtlich, `source` ist die URL.
- Ein Teil (`ringfeder-coupling-86-g110`) ist nach R55 genehmigt, die nicht im Index steht: richtig ist dort, nichts zu
  wählen (Präzisionstest).

## Grenzen

Genehmigungen gelten dem Gerät, nicht dem Einbau; ein Datenblatt nennt nicht zwingend alle zutreffenden Regelungen.
Der Test misst nur die Regelungsauswahl. Eine echte Lösung auf Anforderungsebene gibt es öffentlich nur für
dev-rear-lamp (Paket) und R175 (requirements_old.json).
