# BarelyLegal – technical explanation (Formular „Hack and More“)

Homsianer (B), 25.10. Nur die technische Lösung, keine Problembeschreibung (Wunsch Homsianer). Englisch wie das Formular.
Passende Länge ins Feld kopieren. Die Zahlen in der optionalen Ergebniszeile sind fest (dev-Plattform, HSG2); den
Bumper-Wert bewusst weggelassen, weil er bis 13:00 noch steigt.

## Standard (993 Zeichen)

Python agent certreq, provider-agnostic LLM layer (Claude Opus 5.5 / OpenAI): JSON-schema structured outputs, SHA-256 content-addressed response cache. Vision LLM reads exploded-view drawings (parts, functions, vehicle category). Regulation retrieval: one LLM call over auto-built briefs of all 56 UN regulations, role-based (component/installation/cross-cutting), rationale per decision. PyMuPDF parser → paragraph tree (page, outline path, annex context); structural pre-filters; batched per-paragraph extraction of atomic shall-obligations cited to regulation/version/page/paragraph, five ablation-tested prompt rules. Sub-goal: renumbering-robust PDF diff via global 1:1 sentence alignment + LLM-refined reasons. Eval: platform-calibrated LLM judge, F2-optimal pruning, leave-one-out zero-yield filters, 100+ ledgered ablations; held-out subset selection via set arithmetic on platform regulation/page metrics. React/three.js workbench links each requirement to its highlighted PDF source.

## Kurz (533 Zeichen)

certreq: Python + Claude Opus 5.5, JSON-schema structured outputs, hashed response cache. Vision for drawings; LLM regulation retrieval over auto-built briefs of 56 UN regulations; PyMuPDF paragraph tree; structural filters; batched per-paragraph extraction of atomic shall-obligations with page/paragraph citations. Sub-goal: 1:1 sentence-alignment PDF diff + LLM refine. Calibrated LLM judge, F2-optimal pruning, 100+ ledgered ablations; held-out subset selection from platform feedback. React/three.js workbench with PDF evidence.

## Optional anhängen, falls Platz (84 Zeichen)

Results: worked example F2 0.06 → 0.76; regulation-change held-out flag recall 0.91.
