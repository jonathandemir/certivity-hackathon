# Großer Vergleichstest (Modell claude-opus-5-5)

## Sub-Goal (subgoal-dev)

| Variante | Flag-R | Flag-P | Change accuracy lokal |
|---|---|---|---|
| Standard (refine llm) | 1.000 | 0.889 | 0.917 |
| Gegenteil: regelbasiert (none) | 1.000 | 0.923 | 0.833 |
| llm-all (auch modified per LLM) | 1.000 | 0.889 | 0.875 |
| Ähnlichkeit 0.45 | 1.000 | 0.889 | 0.917 |
| Ähnlichkeit 0.65 | 0.958 | 0.767 | 0.875 |

Kein Kandidat schlägt „Standard (refine llm)“ auf allen Prüfständen über die Streuung hinaus → Standard bleibt.

## Regelungsauswahl

| Variante | echte Teile tune F2 | synthetisch F2 | holdout F2 | Stoßfänger fehlt | Dev |
|---|---|---|---|---|---|
| Standard llm2 | 0.960 | 0.926 | 0.909 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| Gegenteil: llm (ohne Annahme-/Fahrzeugfilter) | 0.923 | 0.893 | 0.848 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| Arena Lauf 1 (alle Regeln) | 1.000 | 1.000 | 1.000 | UN R127 | exakt |
| Arena Lauf 2 (Runde 3) | 0.984 | 0.971 | 0.926 | — | exakt |
| nur Regel Fahrzeugebene raus | 0.960 | 0.990 | 0.982 | UN R127 | exakt |
| nur Regel Lichtquelle ≠ Leuchte | 0.984 | 0.943 | 0.909 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| nur Regel Ersatzteil | 0.976 | 0.962 | 0.926 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| Lichtquelle + Ersatzteil | 1.000 | 0.962 | 1.000 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| Gegenteil: im Zweifel aufnehmen | 0.938 | 0.870 | 0.909 | — | {'certivity/dev-rear-lamp': {'missing': [], 'wrong': ['UN R26']}} |
| Gegenteil: kleinste Menge | 0.789 | 0.604 | 0.686 | UN R10 | {'certivity/dev-rear-lamp': {'missing': ['UN R10', 'UN R48'], 'wrong': []}} |

BESSER: Arena Lauf 2 (Runde 3) (real-tune +0.024, synth +0.045, holdout +0.017)
BESSER: nur Regel Lichtquelle ≠ Leuchte (real-tune +0.024, synth +0.018, holdout +0.000)
BESSER: nur Regel Ersatzteil (real-tune +0.016, synth +0.036, holdout +0.017)
BESSER: Lichtquelle + Ersatzteil (real-tune +0.040, synth +0.036, holdout +0.091)
(Varianten, die beim Frontstoßfänger oder bei der Dev-Rückleuchte eine Pflicht-Regelung verlieren, scheiden vorher aus.)

## Extraktion (Claude-Richter strict)

| Variante | dev F2 | R175 F2 | dev P/R | R175 P/R |
|---|---|---|---|---|
| Standard | 0.698 | 0.615 | 0.43/0.83 | 0.47/0.67 |
| Gegenteil: keine Prompt-Regeln (modal,llm) | 0.683 | 0.636 | 0.47/0.77 | 0.54/0.67 |
| ohne modes | 0.715 | 0.650 | 0.42/0.87 | 0.43/0.74 |
| +procedure2 +testcond | 0.737 | 0.610 | 0.48/0.85 | 0.46/0.67 |
| Gegenteil: keine Filter | 0.661 | 0.628 | 0.34/0.86 | 0.46/0.69 |
| ohne Filter admin | 0.692 | 0.620 | 0.42/0.82 | 0.40/0.72 |
| ohne Filter cop | 0.669 | 0.626 | 0.39/0.82 | 0.48/0.68 |
| ohne Filter parts | 0.695 | 0.615 | 0.41/0.84 | 0.47/0.67 |
| ohne Filter esa | 0.694 | 0.615 | 0.42/0.83 | 0.47/0.67 |
| ohne Filter rationale | 0.698 | 0.615 | 0.43/0.83 | 0.47/0.67 |

BESSER: ohne modes (dev +0.016, r175 +0.035)
BESSER: +procedure2 +testcond (dev +0.039, r175 -0.004)

Dauer 1349 s · LLM: {'calls': 1963, 'cached': 1288, 'prompt_tokens': 9876305, 'completion_tokens': 455904, 'fallbacks': 0}
