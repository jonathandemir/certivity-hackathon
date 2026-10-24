# Kosten-Experimente (Homsianer, B)

Ziel: ein Lauf soll weniger Tokens kosten, ohne dass F2 schlechter wird. Hintergrund und Zahlen: docs/LOG.md
`[finding] Tokenverbrauch je Stufe und Spar-Hebel` (2026-10-24 21:0x).

`costexp.py` ändert **keinen** Code in `certreq/`, sondern patcht zur Laufzeit und startet dann `certreq run`.
Erst wenn eine Variante gemessen mindestens gleich gut und billiger ist, kommt sie als Schalter in den Code.

| Schalter | Was | Qualitätsrisiko |
|---|---|---|
| `--cache` | System-Prompt mit `cache_control` (Anthropic Prompt Caching). `usage` zählt `cache_read`, `cache_write`, `input_uncached` getrennt | keins: Prompt bytegleich |
| `--batch 24 18000` | 24 Absätze / 18000 Zeichen je Aufruf statt 12 / 9000 → 34 statt 65 Aufrufe auf dev | offen |
| `--effort low` | effort nur für die Extraktion (Standard medium) → weniger Ausgabe-/Denk-Tokens | offen |
| `--dry` | kein API-Aufruf, zählt nur Aufrufe und Prompt-Zeichen (braucht `--regs`) | – |

Trocken geprüft (main@13292fb, dev, 6 Regelungen): Standard 65 Aufrufe, 744k Zeichen Eingabe (System-Prompt 302k);
`--batch 24 18000` 34 Aufrufe, 556k Zeichen.

## Messplan (Claude-Reihe, braucht `ANTHROPIC_API_KEY`)

Referenz: E024-hs-c 0.721 / E033-hs-c 0.714 (Richter Claude strict, gleiche Regelungen). Streuung ~0.01.
Je Lauf ~2–3 $ plus Richter. IDs: nächste freie Nummer im LEDGER, Suffix `-hs-c`.

```bash
scripts/pull-first
export CERTREQ_PROVIDER=anthropic CERTREQ_LLM_CACHE=0
R='UN R148,UN R150,UN R48,UN R10,UN R26'   # Claude-Auswahl von E024-hs-c (ohne R42, siehe dessen meta.json), isoliert die Extraktion
C=vendor/industrial-ai-hackathon/cases/dev-rear-lamp

# 0. Trockenlauf (kostenlos)
.venv/bin/python experiments/costexp/costexp.py --dry --batch 24 18000 -- $C --regs "$R" --out out/dry.json

# 1. Caching (1 Lauf): nur Kosten messen, F2 muss in der Streuung bleiben
.venv/bin/python experiments/costexp/costexp.py --cache -- $C --regs "$R" --out out/<ID>.json
# 2. Batches (2 Läufe), 3. effort low (2 Läufe): gleich, mit --batch 24 18000 bzw. --effort low (immer mit --cache)

# Bewerten (Richter-Cache darf an bleiben)
CERTREQ_LLM_CACHE=1 .venv/bin/python -m certreq eval out/<ID>.json --judge strict --record <ID>
```

Auswerten: `experiments/runs/<ID>/meta.json` → `llm.usage` (prompt/completion, bei `--cache` zusätzlich
cache_read/cache_write/input_uncached), dazu F2 und Recall je Regelung. Kosten Opus 5.5: Eingabe 4 $/M,
Ausgabe 20 $/M, Cache-Lesen 0.20 $/M, Cache-Schreiben 5 $/M.

Übernahme: Variante ist ≥ Referenz minus Streuung (Mittel aus 2 Läufen) und billiger → als Schalter in
`certreq/llm_anthropic.py` bzw. `certreq/llmextract.py`, LEDGER-Zeile, `[decision]`. `--cache` darf ohne
F2-Gewinn rein, wenn Kosten sinken und F2 in der Streuung bleibt.

## Stand 2026-10-24 21:30: nicht gemessen

Entscheidung Homsianer (Credits knapp, Pipeline eingefroren): keine bezahlten Kosten-Läufe. Rechnung mit belegten Läufen (Listenpreis Opus 5.5): Held-out-großer Lauf ≈ 4.1 $ (synthetischer Stoßfänger 529k Eingabe / 98k Ausgabe), dev ≈ 2.4 $. `--cache` spart davon ~0.8 $ je Lauf (System-Prompt ~41 % der Eingabe), eine Messung kostet ~2.5–3 $; bei 2–3 Läufen am Sonntag lohnt sich das nicht. Ausgabe/Denken ist der größere Posten (~2 $ je Lauf); `--effort low` wäre der Hebel, aber mit Qualitätsrisiko und nur mit 2 Messläufen zu bewerten.
