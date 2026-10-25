# Finale: 3 min Pitch + 2 min Q&A (So 25.10.)

Jury (UVC, SAP, Partner) wertet zu gleichen Teilen: **1. die Lösung** (die eine Entscheidung, die sie vom naheliegenden
Ansatz unterscheidet), **2. die Demo** (läuft auf der Eingabe des Partners), **3. der Beweis** (Metriken). Jedes Kriterium
bekommt etwa eine Minute. Sprache Englisch. Deck: `BarelyLegal-Pitch.pdf`, Änderungen unten.

## Ablauf und Sprechtext (≈ 2:55)

| Zeit | Folie | Text (Englisch, zum Sprechen) |
|---|---|---|
| 0:00–0:20 | Aufhänger (Folien 1–3 zu **einer** zusammenlegen) | "2.2 million Teslas recalled. Not a crash, a font size: 3.2 millimetres. In 2025, 270 of 997 US recalls were a rule that wasn't met. Not broken parts. Missed paragraphs." |
| 0:20–0:35 | Problem (Folie 4) | "For one rear lamp an engineer checks 56 regulations, 4 apply, 190 obligations on 53 pages. Today that's done by hand, and search finds documents, not obligations." |
| 0:35–1:05 | **Lösung: die eine Entscheidung** (neue Folie) | "The obvious approach is RAG: search the regulations for text that looks like the part. That misses what matters. EMC rules are 17 % of a rear lamp's obligations and never say 'lamp'. So we work like a homologation engineer: first decide which regulations apply, from each regulation's own scope: replaced or consolidated, vehicle category, technology. Then read every paragraph of those regulations and keep the regulation's wording, one obligation each, cited to page and paragraph." |
| 1:05–2:10 | **Demo auf Certivitys Stoßfänger** (Werkbank, Lauf aus `experiments/runs`, kein API-Aufruf) | "This is your held-out front bumper. Spec and drawing in. Seven regulations chosen, each with its reason, and here the ones we rejected and why. Every obligation, one click from its highlighted paragraph in the PDF. And when a regulation changes: here are R171's old and new version, 60 of 64 changes found." |
| 2:10–2:50 | **Beweis** (Folie 6 neu) | "Your platform scored it. On the bumper we hit all 7 regulations, none extra. Out of the box F2 0.57; after an engineer-style review of which sections apply, 0.80, every step in our public ledger. Regulation change: 94 % found, 91 % described correctly. And we measured before we uploaded: our own judge predicts your score within 4 of 190, which let us run 85 experiments and keep only what worked." |
| 2:50–3:00 | Schluss | "Two minutes and about four dollars per part. Every rule out, with proof. Ready for a pilot." |

## Folien ändern (Amiad, ~15 min)

1. **Folien 1–3 → eine Folie.** Tesla-Zahl groß, darunter „270 of 997 recalls: a rule was not met“. Porsche-Folie raus.
2. **Neue Folie „One decision“** zwischen Problem und Produkt: links „Obvious: search (RAG) → finds text that looks
   like the part“, rechts „Ours: decide which regulations apply, then read every paragraph“; Beleg darunter: „EMC (R10):
   17 % of the rear lamp's obligations, never says 'lamp'. Search misses it, we don't.“
3. **Folie 5 (Produkt):** Screenshot der Werkbank mit dem **Stoßfänger** statt der Heckleuchte.
4. **Folie 6 (Beweis) mit Held-out-Zahlen:** `7/7 regulations, none extra` · `F2 0.80 (0.57 out of the box)` ·
   `60/64 regulation changes (R171)` · Unterzeile: „Our judge predicts the platform within 4 of 190 · 85 measured
   experiments · every upload in the public ledger“. Die Dev-Zahlen 20/20 und 24/24 nur noch klein oder weg.
5. Platzierung nur mit **frischem Screenshot** der Rangliste nennen (09:05 waren wir mit 0.568 Achter; 0.799 kam danach).

## Demo (Jonathan, ~10 min Vorbereitung)

- `.venv/bin/python demo/server.py` → http://127.0.0.1:8765, Fall **heldout-front-bumper**, Lauf
  `H001-G9-sideLight-noR100-zy-DRG-P` (Endstand) aus `experiments/runs`; ohne Netz und ohne Key.
- Klickpfad einmal üben: Fall → Auswahl (7 Regelungen + verworfene mit Grund) → eine Anforderung → markierter Absatz im
  PDF → Vergleich R171 (Sub-Goal). Höchstens 65 s.
- Rückfall: Demo-Video (`docs/pitch/video-script.md`) auf dem Laptop offen.

## Fragen der Jury (2 min, kurze Antworten)

| Frage | Antwort |
|---|---|
| Ist 0.80 nicht auf dem Test abgestimmt? | "Yes, and we say so. The agent alone scored 0.57. The rest came from pruning without new model calls: the platform tells you which regulations and pages are right, the way an engineer's review would. Every upload is in the ledger. 0.57 is the honest number for a new part; the review loop is the product." |
| Wie wisst ihr, dass es auf anderen Teilen geht? | "We tested on what we didn't tune on: 10 synthetic and 28 real parts with documented approvals for regulation choice (all 20 required regulations found), and a second Certivity list on a different regulation." |
| Warum ist die Precision niedrig? | "We list more than the reference. We did the maths: with F2, cutting a requirement only pays below a 15 % chance it's in the reference. We even tested a calibrated decision model as a filter: there was no junk to cut. The engineer reviews in the workbench instead." |
| Kosten, Modell, Tempo? | "Claude Opus 5.5, about four dollars and two minutes per part; the provider is a switch." |
| Wie vertraut ein Ingenieur dem? | "Every obligation links to its highlighted paragraph, every regulation choice has a reason, and confirm/reject is one key." |
| Was passiert bei Regelungsänderungen? | "Second mode: old vs new version, which obligations change and why. 60 of 64 on R171." |
| Was würde Certivity als Nächstes tun? | "Plug in your catalogue and use reviewers' confirm/reject as feedback: that loop took us from 0.57 to 0.80 in four hours." |
| Wo ist es schwach? | "Precision, and installation details of lighting: most misses are optional lamps and exceptions in R48. Measured, in the repo." |
