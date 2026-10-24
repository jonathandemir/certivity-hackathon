"""Gemeinsamer LLM-Zugang (OpenAI) für alle Stufen.

    from certreq.llm import ask_json, ask_many
    data = ask_json(system="...", user="...", schema={...}, name="relevanz")      # dict
    results = ask_many([dict(system=..., user=..., schema=...), ...], workers=8)   # Reihenfolge bleibt erhalten

Schlüssel und Modell nie im Repo: OPENAI_API_KEY (oder LLM_API_KEY) und CERTREQ_MODEL kommen aus der Umgebung oder
aus `.env` / `.env.local` im Repo-Root (beide gitignored, Vorlage `.env.example`). `.venv/bin/python -m certreq.llm` prüft Key und Modell, listet die
verfügbaren Modelle und macht einen Testaufruf.

Cache: out/cache/llm/<sha256>.json, Schlüssel = Modell + Nachrichten + Schema. Gleiche Anfrage → gleiche Antwort ohne
Kosten, Messungen bleiben reproduzierbar. Abschalten mit CERTREQ_LLM_CACHE=0.
`schema` wird als OpenAI Structured Output (strict) geschickt: jedes Objekt braucht "additionalProperties": false und
alle Felder in "required". Ohne `schema` gilt JSON-Modus (die Anweisung muss dann "JSON" erwähnen).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import paths

# Team-Entscheidung 2026-10-24: gpt-6.1-sol für alles. Es gibt davon keinen datierten Snapshot; jede gecachte Antwort
# speichert das Modell. Günstige Alternative für Massenaufrufe, falls Tempo/Kosten drücken: "gpt-5.4-mini-2026-03-17".
DEFAULT_MODEL = "gpt-6.1-sol"  # Override: CERTREQ_MODEL oder ask_json(..., model=...)
STRONG_MODEL = "gpt-6.1-sol"  # schwere Einzelentscheidungen (Auswahl, Richter)
CACHE_DIR = paths.OUT_DIR / "cache" / "llm"
_usage = {"calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0}
_lock = threading.Lock()
_client_obj = None


KEY_NAMES = ("OPENAI_API_KEY", "LLM_API_KEY")


def load_env(env_file: Path | None = None) -> None:
    """KEY=VALUE aus .env und .env.local übernehmen, ohne gesetzte Umgebungsvariablen zu überschreiben."""
    files = [env_file] if env_file else [paths.REPO_ROOT / ".env", paths.REPO_ROOT / ".env.local"]
    for f in files:
        if f.exists():
            _load_file(f)


def _load_file(env_file: Path) -> None:
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip().removeprefix("export ").strip(), value.strip().strip("'\"")
        if key and value and key not in os.environ:
            os.environ[key] = value


def model_name(model: str | None = None) -> str:
    load_env()
    return model or os.environ.get("CERTREQ_MODEL", "") or DEFAULT_MODEL


def _client():
    global _client_obj
    if _client_obj is None:
        load_env()
        key = next((os.environ[k] for k in KEY_NAMES if os.environ.get(k)), "")
        if not key:
            raise SystemExit("OPENAI_API_KEY (oder LLM_API_KEY) fehlt: in .env oder .env.local im Repo-Root eintragen "
                             "(gitignored; nie committen, nie in den Chat kopieren).")
        from openai import OpenAI  # erst hier, damit Tests ohne Netz und ohne Key laufen
        _client_obj = OpenAI(api_key=key, max_retries=5, timeout=180)
    return _client_obj


def _call(model: str, messages: list[dict], response_format: dict, effort: str | None = None) -> tuple[str, dict]:
    """Ein API-Aufruf. Gibt (Antworttext, Token-Verbrauch) zurück; in Tests ersetzt."""
    extra = {"reasoning_effort": effort} if effort else {}
    r = _client().chat.completions.create(model=model, messages=messages, response_format=response_format, **extra)
    u = r.usage
    return r.choices[0].message.content or "", {"prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                                                "completion_tokens": getattr(u, "completion_tokens", 0) or 0}


def _image_part(path: Path) -> tuple[dict, dict]:
    """Bild als Nachrichtenteil (data-URL) und als Platzhalter für den Cache-Schlüssel (nur Hash, nicht die Bytes)."""
    data = Path(path).read_bytes()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
            ".gif": "image/gif"}.get(Path(path).suffix.lower(), "application/octet-stream")
    url = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
    return ({"type": "image_url", "image_url": {"url": url, "detail": "high"}},
            {"type": "image_sha256", "sha256": hashlib.sha256(data).hexdigest()})


def ask_json(system: str, user: str, schema: dict | None = None, name: str = "antwort", model: str | None = None,
             effort: str | None = None, images: list[Path] | None = None) -> dict:
    """effort: Denkaufwand, erlaubte Werte je Modell (gpt-6.1-sol: low/medium/high/xhigh; gpt-5.4-mini zusätzlich none);
    None = Modell-Standard. images: Bilder (z. B. Explosionszeichnung), die mit der Nutzernachricht geschickt werden."""
    model = model_name(model)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    key_messages = messages
    if images:
        parts = [_image_part(p) for p in images]
        messages = [messages[0], {"role": "user", "content": [{"type": "text", "text": user}] + [a for a, _ in parts]}]
        key_messages = [messages[0], {"role": "user", "content": [{"type": "text", "text": user}] + [b for _, b in parts]}]
    response_format = ({"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}}
                       if schema else {"type": "json_object"})
    # Ohne Bilder ist der Schlüssel identisch zu früher, vorhandene Caches bleiben gültig.
    key = hashlib.sha256(json.dumps([model, key_messages, response_format, effort], sort_keys=True, ensure_ascii=False)
                         .encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{key}.json"
    use_cache = os.environ.get("CERTREQ_LLM_CACHE", "1") != "0"
    if use_cache and cache_file.exists():
        with _lock:
            _usage["cached"] += 1
        return json.loads(cache_file.read_text(encoding="utf-8"))["answer"]
    t0 = time.time()
    content, usage = _call(model, messages, response_format, effort) if effort else _call(model, messages, response_format)
    try:
        answer = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Modell {model} lieferte kein gültiges JSON ({e}): {content[:300]}") from e
    with _lock:
        _usage["calls"] += 1
        for k in ("prompt_tokens", "completion_tokens"):
            _usage[k] += usage.get(k, 0)
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(f".{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps({"model": model, "name": name, "usage": usage, "seconds": round(time.time() - t0, 2),
                                   "answer": answer}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(cache_file)
    return answer


def ask_many(requests: list[dict], workers: int = 8) -> list[dict]:
    """Mehrere ask_json-Aufrufe parallel; Ergebnis in derselben Reihenfolge wie `requests`."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda kw: ask_json(**kw), requests))


def usage() -> dict:
    """Verbrauch dieses Prozesses (für .meta.json eines Laufs)."""
    with _lock:
        return dict(_usage)


def _check() -> int:
    load_env()
    client = _client()
    ids = sorted(m.id for m in client.models.list())
    print(f"Key OK. {len(ids)} Modelle verfügbar, u. a.: {', '.join(i for i in ids if i.startswith(('gpt', 'o')))[:600]}")
    chosen = model_name()
    for m in (DEFAULT_MODEL, STRONG_MODEL):
        if m not in ids:
            print(f"WARNUNG: {m} ist mit diesem Key nicht verfügbar.")
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}
    t0 = time.time()
    os.environ["CERTREQ_LLM_CACHE"] = "0"
    answer = ask_json("Antworte als JSON.", "Gib ok=true zurück.", schema, name="check")
    print(f"Testaufruf mit {chosen}: {answer} in {time.time() - t0:.1f} s, Verbrauch {usage()}")
    return 0 if answer.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(_check())
