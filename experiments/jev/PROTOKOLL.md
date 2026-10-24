# Jev-Versuche: Protokoll (vor der ersten Auswertung festgelegt)

Jev (`typesafe-ai/jev`, Vercel AI Gateway, `certreq/jev.py`) beantwortet Ja/Nein-Fragen mit einer Wahrscheinlichkeit p.
Frage: Hebt ein Filter mit p die Precision so, dass F2 steigt (Versuch 1), oder spart ein Vorfilter Opus-Kosten ohne
Gold-Absätze zu verlieren (Versuch 2)? Grundlage: F2 = 5·TP / (4·G + N). Streichen lohnt nur bei Trefferchance unter
F2/5 ≈ 15 % (LEARNINGS). Festgelegt Sa 24.10. abends, vor jeder Jev-Antwort auf Testdaten.

## Versuch 1: Nachfilter auf fertige Anforderungen

Jev bewertet jede ausgegebene Anforderung eines fertigen Laufs. Zustand (`state`) ist die Spec, mit der der Lauf
gerechnet hat (nur Zeichnung: die Zeichnungsbeschreibung aus `.meta.json`). Gestrichen wird alles mit p < θ.
Der Lauf selbst wird nicht neu gerechnet. Trefferkennzeichen stammen aus den vorhandenen Richter-Berichten
(1:1-Zuordnung): TP(θ) = behaltene Treffer, N(θ) = behaltene Ausgaben, F2(θ) = 5·TP(θ)/(4G+N(θ)). Konservativ: Eine
gestrichene Anforderung mit Treffer zählt als verlorener Treffer, auch wenn eine andere sie hätte ersetzen können.

| Rolle | Läufe | G | Richter |
|---|---|---|---|
| Abstimmung (Formulierung, Schwelle) | E039-a, E040-a (Opus, dev) | 190 | gpt lenient (= Plattform ±1) |
| Test | E024-hs-c (Opus, dev, Plattform bestätigt) | 190 | gpt lenient |
| Test | X-R175-C, X-R175-C-rep (Opus, fremde Regelung, Abschnitte 5–6) | 78 | Claude strict |
| Test | E022-hs, E030-a (gpt-Ausgaben, dev) | 190 | gpt lenient |
| Test | E044-a (Opus, nur Zeichnung, dev) | 190 | Claude strict |

- Höchstens zwei Frageformulierungen: **A** Anwendbarkeit („muss das Bauteil das erfüllen?“), **B** Liste des
  Homologations-Ingenieurs („würde er das aufnehmen?“). Gewählt wird die mit der höheren mittleren AUC auf den
  Abstimmungsläufen.
- Schwelle θ* = argmax des mittleren F2 der Abstimmungsläufe, Raster 0.00–0.95 in 0.05-Schritten.
- **Annahme nur, wenn** auf **jedem** Testlauf F2(θ*) ≥ F2(0) **und** der mittlere Gewinn über die Testläufe
  ≥ +0.010 ist. Sonst verworfen. Zusätzlich berichtet: AUC je Lauf, Kalibrierung (Trefferquote je p-Bereich), F2 bei
  der theoretischen Schwelle 0.15.

## Versuch 2: Vorfilter auf Kandidaten-Absätze

Jev bewertet jeden Kandidaten-Absatz vor der LLM-Extraktion (dev: Opus-Auswahl R148, R150, R48, R10, R26; R175: nur
R175). Gemessen ohne LLM-Lauf: Anteil gestrichener Absätze und Anteil behaltener Gold-Absätze (Absatzlabel aus dem
Gold) je Schwelle. **Weiter zu einem echten Opus-Lauf nur, wenn** eine Schwelle auf dev **und** R175 ≥ 99 % der
Gold-Absätze behält und ≥ 30 % der Absätze streicht. Der echte Lauf misst dann Kosten, Laufzeit und F2
(Claude-Richter) gegen den Standard.

## Kosten

Jev: $0.042 je Million Eingabe-Tokens, Ausgabe frei (Testaufruf: 391 Tokens, $0.000016). Versuch 1 und die Messung
von Versuch 2 brauchen kein Opus und keinen Richter. Ein echter Lauf in Versuch 2 ≈ $1.5–3.5 Opus + $2.2 Richter.
