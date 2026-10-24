# Demo (AP6, Amiad / C)

## Werkbank (das Produkt)

    demo/werkbank                 # = .venv/bin/python demo/server.py, öffnet http://127.0.0.1:8765

Lokaler Server (`demo/server.py`, nur Standardbibliothek + pymupdf, bindet an 127.0.0.1) + App
(`demo/web/werkbank.html`). Vier Ansichten, Tasten 1–4, ⌘K/Strg+K = Befehlspalette, P = Präsentation:

| Ansicht | Was |
|---|---|
| Prüfungen | Spec und/oder Zeichnung ablegen → Fall in `out/cases/`, Prüfung starten (`certreq run` als Unterprozess, Ergebnis in `out/runs/<id>/`). Modus „Bestmarke" = `certreq run` ohne Schalter, also immer der gemessene Standard (derzeit E022-hs; braucht einen LLM-Key in `.env.local`), „Schnell" = B0 ohne KI (`--select b0 --filters none --extract none`). Liste aller Läufe: eigene, Messungen aus `experiments/runs/`, ältere `out/<fall>.json`. |
| Anforderungen | Regelungs-Rad als Filter, Bauteile, Status; Liste (virtuell, auch 3600+); Beleg rechts mit live gerenderter PDF-Seite (Cache `out/cache/pages/`), markiertem Absatz und rotem Belegfaden Zeile → Stelle. Review: J/K blättern, A bestätigen, X verwerfen, U offen, N Notiz (gespeichert in `out/runs/<id>/review.json` bzw. `out/reviews/<id>.json`). Export: Abgabe-JSON ohne Verworfene, CSV mit Status/Notiz. |
| Auswahl | Alle 56 Regelungen auf einem Kreis, gewählte nach Rolle (Bauteil/Anbau/Querschnitt), verworfene mit Grund; Begründungen aus `.meta.json` `selection`. |
| Vergleich | Sub-Goal (AP7): alte → neue Fassung, Wort-Diff je Anforderung, lokale Bewertung gegen `expected.json` (Cache `out/subgoal/`). |

`/present/<lauf>/` zeigt die 3D-Präsentation (unten) mit den Daten eines Laufs, Seiten werden live gerendert.

## Präsentation (3D, ohne Server)

Ein Befehl von der Eingabe bis zur Präsentation (R3):

    demo/run vendor/industrial-ai-hackathon/cases/<fall>      # certreq run + prepare, ~4 min mit LLM
    # oder nur aus einer vorhandenen Abgabe:
    .venv/bin/python demo/prepare.py out/<fall>.json          # ~10–40 s
    # dann demo/dist/index.html im Browser öffnen (kein Server, kein Node)

## Aufbau

| Pfad | Was | Im Repo? |
|---|---|---|
| `demo/prepare.py` | Abgabe-JSON + `.meta.json` + Fall-Ordner → `demo/dist/data.js` (`window.CERTREQ`), kopiert `web/index.html` dazu | ja |
| `demo/web/index.html` | fertig gebaute Präsentation (Vite, eine Datei, ~1,6 MB, ohne Falldaten) | ja |
| `demo/web/werkbank.html` | fertig gebaute Werkbank (~0,7 MB) | ja |
| `demo/server.py`, `demo/werkbank` | lokaler Server der Werkbank | ja |
| `demo/app/` | Quellcode der App (React, three.js/react-three-fiber, motion) | ja |
| `demo/dist/` | Ausgabe mit Paketdaten (Seitenbilder, Zeichnung) | **nein** (gitignored, Lizenz) |
| `demo/build.py`, `demo/template.html` | erste einfache Demo (Liste mit PDF-Links), bleibt als Rückfall | ja |

`prepare.py` ist allgemein, nichts ist auf die Heckleuchte zugeschnitten. Spec und Zeichnung sind beide optional:
- Bauteile aus `spec.md` „Main Parts"; Anforderung → Bauteil per Wortabgleich (Bauteilname im Text, eindeutige
  Wortstämme, Regelungstitel), sonst „Gesamtgerät". Heuristik, keine KI; das UI sagt das.
- Jede zitierte PDF-Seite als Graustufen-JPEG; Markierung = Zeilen des zitierten Absatzes (Absatznummer am
  Blockanfang, sonst bester Wortüberlapp). Dev-Fall: 189/190 markiert. Höchstens `--max-pages` (150) Seiten,
  die mit den meisten Anforderungen zuerst; der Rest zeigt eine nachgesetzte Seite.
- Reicht `.meta.json` `selection` (Begründung je Regelung) und `drawing` durch (`window.CERTREQ.run`), im UI noch nicht genutzt.

Die App zerlegt die Explosionszeichnung selbst im Browser (Zusammenhangsanalyse, `app/src/segment.js`) und zeigt
die Teile als Karten im Raum. Ohne Zeichnung: Karten mit den Bauteilnamen; ohne beides: eine Karte mit dem Fall.
Drei Szenen, Wechsel mit ←/→ oder 1/2/3, R startet den Lauf neu: 01 Lauf (Ring der 56 Regelungen), 02 Zeichnung
(Explosion + Anforderungen je Bauteil), 03 Beleg (Anforderung → Regelung → Absatz → markierte PDF-Seite).

## App ändern

    cd demo/app && npm install && npm run build      # baut beide Seiten
    cp dist/index.html ../web/index.html && cp dist-werkbank/werkbank.html ../web/werkbank.html
    # zum Testen: Daten danebenlegen
    cp ../dist/data.js dist/ && open dist/index.html     # ?lite = ohne Glas/Bloom, ?t=1 = Lauf sofort fertig

Node nur zum Bauen nötig, am Sonntag nicht. `app/src/lamp/` = handgebaute 3D-Heckleuchte (nur Dev-Fall), derzeit
nicht eingebunden.

## Offen

- Teile der Zeichnung ↔ Bauteile der Spec sind nicht verknüpft (Karten heißen „Teil n"). Lösung: Vision-Aufruf
  (A, `certreq/vision.py`) liefert je Bauteil eine Bildregion, `prepare.py` reicht sie durch.
- Begründungen je Regelung (`selection`) in Szene 1 anzeigen.
- Zerlegung trennt dicht beieinanderliegende Teile nicht (Dev-Fall: 2 Teile statt 3).
