# BarelyLegal – Demo-Video (max. 2:00) für das Formular „Hack and More“

Entwurf von Homsianer (B), 25.10. Aufnahme: Bildschirm + Stimme, Werkbank aus dem Cache (`demo/werkbank`, Lauf H001 bzw.
dev-rear-lamp geöffnet), keine neuen LLM-Läufe nötig. Zahlen vor der Aufnahme gegen docs/STATUS.md prüfen.
Englisch wie das Formular. Hochladen auf YouTube (nicht gelistet) oder Luma, Link ins Formular, **vor 13:00**.

| Zeit | Bild (Werkbank, Tasten 1–5) | Sprecher |
|---|---|---|
| 0:00–0:12 | Titel / Spec des Frontstoßfängers (Prüfungen) | "A front bumper carries lamps, radar, sensors, a towing cover. Which UN regulations apply, and which exact obligations follow? Today an engineer spends days on that." |
| 0:12–0:25 | Prüfung starten (Spec + Zeichnung ablegen) → Überblick | "BarelyLegal takes the spec or the exploded-view drawing and returns every engineering requirement with regulation, version, page and paragraph – no manual steps." |
| 0:25–0:40 | Auswahl (Taste 4): Kreis der 56 Regelungen, gewählte nach Rolle, verworfene mit Grund | "First it narrows 56 regulations down to the few that apply – component, installation, cross-cutting – and says why it rejected the others." |
| 0:40–1:00 | Anforderungen (Taste 3): eine Anforderung anklicken, PDF-Seite mit markiertem Absatz und Belegfaden; A bestätigen, X verwerfen | "Each requirement is one obligation an engineer can act on, linked to the highlighted paragraph in the official PDF. Engineers review with one key per decision and export the result." |
| 1:00–1:15 | Änderungen (Taste 5): R48 9.3.0 → 9.4.0, betroffene Anforderungen | "When a regulation is amended, it shows exactly which of your requirements change, disappear or are new, and which paragraph caused it." |
| 1:15–1:40 | Architektur-Folie (BarelyLegal-Pitch.pdf, sonst docs/pitch/technical-explanation.md „Pipeline“ als Text) | "Under the hood: parse every PDF into numbered paragraphs with page and outline, filter administrative and vehicle-only sections by structure, then let Claude extract one obligation per requirement under five measured rules." |
| 1:40–2:00 | Zahlen-Folie | "Every change was measured on its own: worked example F2 0.06 → 0.76; regulation-change held-out recall 0.91; front-bumper held-out [aktueller Bestwert]. Weakest point: precision on test-procedure details – and we show where." |

Hinweise: Ton vorher testen, Benachrichtigungen aus, Browser-Zoom so, dass die PDF-Seite lesbar ist. Lieber 1:50 als 2:05.
