# Synthetische Fälle (Robustheitsprüfung)

## front-bumper/

Selbst geschriebene Spezifikation im Aufbau der Dev-Spec, um die Pipeline vor Sonntag an einem anderen Bauteil zu
prüfen. **Keine Musterlösung, keine Messung:** geprüft werden nur Laufbarkeit, Plausibilität der Auswahl und Laufzeit.
Der echte Held-out (`heldout-front-bumper`) kommt Sonntag 08:00 und kann anders aussehen.

    .venv/bin/python -m certreq run experiments/synthetic/front-bumper --filters all --extract modal,llm --out out/synthetic-front-bumper.json
