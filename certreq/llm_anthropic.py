"""Anthropic-Zugang für certreq.llm, Schalter CERTREQ_PROVIDER=anthropic (Standard bleibt OpenAI, Team-Entscheidung).

    CERTREQ_PROVIDER=anthropic  ANTHROPIC_API_KEY=…  (Umgebung oder .env.local, nie ins Repo)
    optional CERTREQ_ANTHROPIC_MODEL (Standard claude-opus-5-5)

llm.ask_json baut die Anfrage wie für OpenAI (Nachrichten, response_format); `call` übersetzt sie: System-Nachricht →
`system`, Bilder (data-URL) → base64-Bildblock, JSON-Schema → Structured Output (`output_config.format`), effort →
`output_config.effort`. Opus 5.5 denkt immer adaptiv; ohne effort gilt "medium". Bei einer Ablehnung durch die
Sicherheitsklassifikatoren springt serverseitig das von Anthropic empfohlene Ersatzmodell ein (`fallbacks="default"`);
`usage["fallbacks"]` zählt das, damit eine Messung es ausweisen kann.

Messungen mit Claude sind nicht mit gpt-6.1-sol-Messungen vergleichbar (anderes Modell für Auswahl, Extraktion und
Richter): eigene Referenz messen, nur innerhalb derselben Reihe vergleichen.
"""
from __future__ import annotations

import json
import os
import threading

MODEL = "claude-opus-5-5"
MAX_TOKENS = 32000  # mit Streaming, damit lange Batches nicht abgeschnitten werden und kein HTTP-Timeout greift
EFFORTS = {"none": "low", "minimal": "low", "low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh",
           "max": "max"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
_client_obj = None
_lock = threading.Lock()


def model_name() -> str:
    return os.environ.get("CERTREQ_ANTHROPIC_MODEL", "") or MODEL


def client():
    global _client_obj
    with _lock:
        if _client_obj is None:
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                raise SystemExit("ANTHROPIC_API_KEY fehlt (CERTREQ_PROVIDER=anthropic): in den Umgebungseinstellungen "
                                 "oder in .env.local eintragen (gitignored; nie committen, nie in den Chat kopieren).")
            import anthropic  # erst hier, damit Tests und OpenAI-Läufe das Paket nicht brauchen
            _client_obj = anthropic.Anthropic(api_key=key, max_retries=5, timeout=600)
    return _client_obj


def _content(content):
    """OpenAI-Nachrichteninhalt → Anthropic-Inhalt (Text bleibt Text, data-URL-Bilder werden base64-Bildblöcke)."""
    if isinstance(content, str):
        return content
    blocks = []
    for part in content:
        if part.get("type") == "text":
            blocks.append({"type": "text", "text": part["text"]})
        elif part.get("type") == "image_url":
            head, data = part["image_url"]["url"].split(",", 1)  # data:image/png;base64,…
            blocks.append({"type": "image", "source": {"type": "base64", "media_type": head[5:].split(";")[0],
                                                       "data": data}})
    return blocks


def request(model: str, messages: list[dict], response_format: dict, effort: str | None = None) -> dict:
    """Parameter für client().beta.messages.stream (getrennt, damit Tests sie ohne Netz prüfen können)."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    output_config: dict = {"effort": EFFORTS.get(effort or "medium", "medium")}
    if response_format.get("type") == "json_schema":
        output_config["format"] = {"type": "json_schema", "schema": response_format["json_schema"]["schema"]}
    else:
        system += "\n\nAnswer with one JSON object only, without any text around it."
    return dict(model=model, max_tokens=MAX_TOKENS, system=system,
                messages=[{"role": m["role"], "content": _content(m["content"])} for m in messages
                          if m["role"] != "system"],
                output_config=output_config, betas=[FALLBACK_BETA], fallbacks="default")


def _json_text(text: str) -> str:
    """Ohne Schema: das JSON-Objekt aus der Antwort schneiden (falls doch Text oder ```-Zäune darum stehen)."""
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if 0 <= start < end else text


def call(model: str, messages: list[dict], response_format: dict, effort: str | None = None) -> tuple[str, dict]:
    """Ein API-Aufruf wie llm._call: (Antworttext, Token-Verbrauch)."""
    params = request(model, messages, response_format, effort)
    with client().beta.messages.stream(**params) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"{model} hat abgelehnt (auch das Ersatzmodell): {getattr(msg, 'stop_details', None)}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError(f"{model}: Antwort nach max_tokens={MAX_TOKENS} abgeschnitten")
    text = "".join(b.text for b in msg.content if b.type == "text")
    if "format" not in params["output_config"]:
        text = _json_text(text)
    u = msg.usage
    fallbacks = sum(1 for b in msg.content if b.type == "fallback")
    return text, {"prompt_tokens": (u.input_tokens or 0) + (getattr(u, "cache_read_input_tokens", 0) or 0)
                  + (getattr(u, "cache_creation_input_tokens", 0) or 0),
                  "completion_tokens": u.output_tokens or 0, "fallbacks": fallbacks}


def check() -> list[str]:
    """Modelle, die der Key sieht (für llm._check)."""
    return sorted(m.id for m in client().models.list())

