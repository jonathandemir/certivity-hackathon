"""AP2-Auswahl ohne Netz: Steckbriefe aus den PDFs, Auswertung der LLM-Antwort, Modi."""
import pytest

from certreq import select as S
from certreq.case import load_case
from conftest import DEV_CASE, needs_package


@needs_package
def test_steckbrief_enthaelt_einleitung_scope_und_keine_bannerzeilen():
    b148 = S.brief("UN R148")
    assert "combines the provisions" in b148 and "7, 23" in b148  # Konsolidierung steht im PDF selbst
    assert "Scope" in b148 and "Stop lamps" in b148
    assert "rendered by Certivity" not in b148 and "Role in the hackathon" not in b148
    assert "Front and rear position lamps" in S.brief("UN R7")
    assert "Components and separate technical units" in S.brief("UN R10")


@needs_package
def test_llm_antwort_wird_zu_regelungen_mit_begruendung(monkeypatch):
    seen = {}

    def fake(system, user, schema, **kw):
        seen["enum"] = schema["properties"]["selected"]["items"]["properties"]["regulation"]["enum"]
        seen["user"] = user
        return {"selected": [{"regulation": "UN R148", "role": "component", "reason": "a"},
                             {"regulation": "UN R10", "role": "cross-cutting", "reason": "b"},
                             {"regulation": "UN R148", "role": "component", "reason": "doppelt"}],
                "rejected": [{"regulation": "UN R7", "reason": "in R148 aufgegangen"}]}
    monkeypatch.setattr(S.llm, "ask_json", fake)
    explain = []
    regs = S.select_regulations(load_case(DEV_CASE), mode="llm", explain=explain)
    assert [r.name for r in regs] == ["UN R148", "UN R10"]
    assert len(seen["enum"]) == 56 and "### UN R10" in seen["user"] and "Rear lamp" in seen["user"]
    assert [e["role"] for e in explain] == ["component", "cross-cutting", "rejected"]


@needs_package
def test_modi():
    case = load_case(DEV_CASE)
    assert len(S.select_regulations(case)) == 21  # B0 unverändert (E001)
    with pytest.raises(SystemExit):
        S.select_regulations(case, mode="quatsch")


@needs_package
def test_llm2_verwirft_annahmen_und_fahrzeugebene(monkeypatch):
    seen = {}

    def fake(system, user, schema, **kw):
        seen["system"], seen["required"] = system, schema["properties"]["selected"]["items"]["required"]
        sel = lambda reg, stated, locus: {"regulation": reg, "role": "cross-cutting", "reason": "r", "trigger": "t",
                                          "stated_in_spec": stated, "requirement_locus": locus}
        return {"selected": [sel("UN R42", True, "component"), sel("UN R48", True, "installation"),
                             sel("UN R152", False, "installation"), sel("UN R155", True, "vehicle-only")],
                "rejected": []}
    monkeypatch.setattr(S.llm, "ask_json", fake)
    explain = []
    regs = S.select_regulations(load_case(DEV_CASE), mode="llm2", explain=explain)
    assert [r.name for r in regs] == ["UN R42", "UN R48"]
    assert "requirement_locus" in seen["required"] and "vehicle-only" in seen["system"]
    dropped = {e["regulation"]: e["reason"] for e in explain if e["role"] == "rejected"}
    assert dropped["UN R152"].startswith("verworfen (Annahme") and dropped["UN R155"].startswith("verworfen (nur Fahrzeugebene")
