"""certreq.llm ohne Netz und ohne Key: Cache, Reihenfolge, .env, klare Fehler."""
import json

import pytest

from certreq import llm

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"], "additionalProperties": False}


@pytest.fixture
def fake(monkeypatch, tmp_path):
    calls = []

    def fake_call(model, messages, response_format, effort=None):
        calls.append((model, messages[-1]["content"], response_format["type"]))
        return json.dumps({"x": len(messages[-1]["content"])}), {"prompt_tokens": 10, "completion_tokens": 2}

    monkeypatch.setattr(llm, "_call", fake_call)
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setenv("CERTREQ_MODEL", "test-model")
    monkeypatch.delenv("CERTREQ_LLM_CACHE", raising=False)
    return calls


def test_cache_spart_wiederholte_aufrufe(fake):
    a = llm.ask_json("sys", "abc", SCHEMA)
    b = llm.ask_json("sys", "abc", SCHEMA)
    c = llm.ask_json("sys", "abcd", SCHEMA)
    assert a == b == {"x": 3} and c == {"x": 4}
    assert len(fake) == 2, "gleiche Anfrage darf nur einmal ans Modell gehen"
    assert fake[0] == ("test-model", "abc", "json_schema")


def test_cache_abschaltbar(fake, monkeypatch):
    monkeypatch.setenv("CERTREQ_LLM_CACHE", "0")
    llm.ask_json("sys", "abc", SCHEMA)
    llm.ask_json("sys", "abc", SCHEMA)
    assert len(fake) == 2


def test_effort_ist_teil_des_cache_schluessels(fake):
    llm.ask_json("s", "q", SCHEMA)
    llm.ask_json("s", "q", SCHEMA, effort="low")
    assert len(fake) == 2


def test_ohne_schema_json_modus(fake):
    llm.ask_json("Antworte als JSON.", "q")
    assert fake[0][2] == "json_object"


def test_ask_many_behaelt_reihenfolge(fake):
    reqs = [dict(system="s", user="u" * n, schema=SCHEMA) for n in (5, 1, 3, 2)]
    assert [r["x"] for r in llm.ask_many(reqs, workers=4)] == [5, 1, 3, 2]


def test_kaputtes_json_gibt_klare_meldung(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "_call", lambda *a: ("kein json", {}))
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    monkeypatch.setenv("CERTREQ_MODEL", "m")
    with pytest.raises(RuntimeError, match="kein gültiges JSON"):
        llm.ask_json("s", "u", SCHEMA)


def test_env_datei_ueberschreibt_nichts(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# Kommentar\nCERTREQ_MODEL='aus-datei'\nexport OPENAI_API_KEY=abc\nLEER=\n", encoding="utf-8")
    monkeypatch.delenv("CERTREQ_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "schon-gesetzt")
    llm.load_env(env)
    import os
    assert os.environ["CERTREQ_MODEL"] == "aus-datei"
    assert os.environ["OPENAI_API_KEY"] == "schon-gesetzt"
    assert "LEER" not in os.environ


def test_modellwahl_und_fehlender_key(monkeypatch, tmp_path):
    monkeypatch.setattr(llm.paths, "REPO_ROOT", tmp_path)  # keine .env
    monkeypatch.setattr(llm, "load_env", lambda *a, **k: None)
    monkeypatch.delenv("CERTREQ_MODEL", raising=False)
    assert llm.model_name() == llm.DEFAULT_MODEL
    monkeypatch.setenv("CERTREQ_MODEL", "anderes")
    assert llm.model_name() == "anderes" and llm.model_name("explizit") == "explizit"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setattr(llm, "_client_obj", None)
    with pytest.raises(SystemExit, match="OPENAI_API_KEY .*fehlt"):
        llm._client()


def test_anthropic_bildet_gpt_modelle_ab(monkeypatch):
    monkeypatch.setenv("CERTREQ_PROVIDER", "anthropic")
    monkeypatch.delenv("CERTREQ_ANTHROPIC_MODEL", raising=False)
    monkeypatch.setenv("CERTREQ_MODEL", "")
    assert llm.model_name() == llm.model_name(llm.STRONG_MODEL) == "claude-opus-5-5"
    assert llm.model_name("claude-sonnet-5-5") == "claude-sonnet-5-5"
    monkeypatch.setenv("CERTREQ_PROVIDER", "")
    assert llm.model_name(llm.STRONG_MODEL) == llm.STRONG_MODEL


def test_anthropic_anfrage_uebersetzt(tmp_path):
    from certreq import llm_anthropic
    img = tmp_path / "z.png"
    img.write_bytes(b"\x89PNG fake")
    part, _ = llm._image_part(img)
    msgs = [{"role": "system", "content": "SYS"}, {"role": "user", "content": [{"type": "text", "text": "U"}, part]}]
    fmt = {"type": "json_schema", "json_schema": {"name": "n", "schema": SCHEMA, "strict": True}}
    r = llm_anthropic.request("claude-opus-5-5", msgs, fmt, "xhigh")
    assert r["system"] == "SYS" and r["output_config"] == {"effort": "xhigh", "format": {"type": "json_schema", "schema": SCHEMA}}
    assert r["messages"][0]["content"][0] == {"type": "text", "text": "U"}
    assert r["messages"][0]["content"][1]["source"]["media_type"] == "image/png"
    assert r["fallbacks"] == "default" and r["betas"] == [llm_anthropic.FALLBACK_BETA]
    plain = llm_anthropic.request("m", [{"role": "user", "content": "q"}], {"type": "json_object"}, None)
    assert plain["output_config"] == {"effort": "medium"} and "JSON" in plain["system"]
    assert llm_anthropic.EFFORTS["none"] == "low"
    assert llm_anthropic._json_text('Hier:\n```json\n{"a": 1}\n```') == '{"a": 1}'


def test_anthropic_eigener_cache_schluessel(monkeypatch, tmp_path):
    from certreq import llm_anthropic
    seen = []
    monkeypatch.setattr(llm_anthropic, "call", lambda model, m, f, e=None: seen.append(model) or ('{"x": 1}', {"prompt_tokens": 1, "completion_tokens": 1, "fallbacks": 0}))
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    monkeypatch.delenv("CERTREQ_LLM_CACHE", raising=False)
    monkeypatch.setenv("CERTREQ_PROVIDER", "anthropic")
    monkeypatch.setenv("CERTREQ_MODEL", "")
    monkeypatch.delenv("CERTREQ_ANTHROPIC_MODEL", raising=False)
    assert llm.ask_json("s", "q", SCHEMA, model=llm.STRONG_MODEL) == {"x": 1}
    assert seen == ["claude-opus-5-5"]
    json_files = list(tmp_path.glob("*.json"))
    assert len(json_files) == 1 and json.loads(json_files[0].read_text())["model"] == "claude-opus-5-5"
