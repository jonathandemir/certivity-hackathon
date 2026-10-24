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
