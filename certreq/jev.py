"""Jev (TypeSafe AI) über das Vercel AI Gateway: Entscheidungen mit Wahrscheinlichkeit statt Text.

Jev beantwortet typisierte Fragen (boolean, choice, score) zu einem Zustand und liefert je Antwort eine
Wahrscheinlichkeit. Es schreibt keinen Text; hier bewertet es fertige Anforderungen oder Kandidaten-Absätze.
Aufruf: POST https://ai-gateway.vercel.sh/v1/evaluate mit {model, state, questions}; Key AI_GATEWAY_API_KEY
(.env.local). Cache unter out/cache/jev (gleiche Anfrage → gleiche Antwort, ohne Kosten); abschalten mit
CERTREQ_LLM_CACHE=0. Versuche und Kriterien: experiments/jev/PROTOKOLL.md.

    .venv/bin/python -m certreq.jev check        # ein Testaufruf, zeigt Antwort, Dauer und Kosten
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from . import llm, paths

URL = "https://ai-gateway.vercel.sh/v1/evaluate"
MODEL = "typesafe-ai/jev"
CACHE_DIR = paths.OUT_DIR / "cache" / "jev"
RETRY_STATUS = {429, 500, 502, 503, 504, 529}
_usage = {"calls": 0, "cached": 0, "input_tokens": 0, "cost_usd": 0.0, "seconds": 0.0}
_lock = threading.Lock()


def _ssl_context() -> ssl.SSLContext:
    """macOS-Python (python.org) kennt die System-Zertifikate oft nicht: truststore (System-Schlüsselbund, über das
    Anthropic-SDK installiert) oder certifi nehmen, sonst Standard."""
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _key() -> str:
    llm.load_env()
    key = os.environ.get("AI_GATEWAY_API_KEY", "")
    if not key:
        raise SystemExit("AI_GATEWAY_API_KEY fehlt: in .env.local eintragen (nie ins Repo).")
    return key


def decide(state, questions: dict, model: str = MODEL, retries: int = 4) -> dict:
    """Eine Anfrage an /v1/evaluate. Rückgabe: die Antwort des Gateways (answers, usage, providerMetadata)."""
    body = {"model": model, "state": state, "questions": questions}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
    cache_file = CACHE_DIR / f"{hashlib.sha256(raw.encode()).hexdigest()}.json"
    use_cache = os.environ.get("CERTREQ_LLM_CACHE", "1") != "0"
    if use_cache and cache_file.exists():
        with _lock:
            _usage["cached"] += 1
        return json.loads(cache_file.read_text(encoding="utf-8"))
    req = urllib.request.Request(URL, data=json.dumps(body, ensure_ascii=False).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as r:
                ans = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code in RETRY_STATUS and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Jev: HTTP {e.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"Jev: Verbindung fehlgeschlagen: {e}") from None
    if "answers" not in ans:
        raise SystemExit(f"Jev: Antwort ohne answers: {json.dumps(ans)[:500]}")
    gw = (ans.get("providerMetadata") or {}).get("gateway") or {}
    with _lock:
        _usage["calls"] += 1
        _usage["input_tokens"] += int((ans.get("usage") or {}).get("inputTokens") or 0)
        _usage["cost_usd"] += float(gw.get("cost") or 0)
        _usage["seconds"] += time.time() - t0
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(f".{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(ans, ensure_ascii=False), encoding="utf-8")
        tmp.replace(cache_file)
    return ans


def decide_many(requests: list[tuple], workers: int = 8, model: str = MODEL) -> list[dict]:
    """requests: Liste von (state, questions); parallel, Reihenfolge bleibt."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda rq: decide(rq[0], rq[1], model=model), requests))


def usage() -> dict:
    with _lock:
        return dict(_usage, cost_usd=round(_usage["cost_usd"], 6), seconds=round(_usage["seconds"], 2))


def _check() -> int:
    t0 = time.time()
    ans = decide("The rear lamp housing is made of polycarbonate and contains an LED module on a circuit board.", {
        "electronic": {"type": "boolean", "instructions": "Does the component contain electronics?",
                       "criteria": {"true": "it contains electrical or electronic parts", "false": "purely mechanical or optical"}},
        "location": {"type": "choice", "instructions": "Where on the vehicle is this component mounted?",
                     "criteria": {"front": "front of the vehicle", "rear": "rear of the vehicle", "side": "side of the vehicle"}},
    })
    gw = (ans.get("providerMetadata") or {}).get("gateway") or {}
    print(json.dumps({"answers": ans["answers"], "usage": ans.get("usage"), "model": ans.get("model"),
                      "cost_usd": gw.get("cost"), "seconds": round(time.time() - t0, 2)}, indent=1))
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        os.environ["CERTREQ_LLM_CACHE"] = "0"
        raise SystemExit(_check())
    raise SystemExit(__doc__)
