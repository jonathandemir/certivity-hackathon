"""Jev ohne Netz: Fragen werden richtig gebaut, Antworten den richtigen IDs zugeordnet."""
from types import SimpleNamespace

from certreq import jev


def test_score_requirements_baut_fragen_und_ordnet_zu(monkeypatch):
    seen = []
    def fake(requests, workers=8, model=jev.MODEL):
        seen.extend(requests)
        return [{"answers": {k: {"type": "boolean", "probability": 0.1 * (i + 1)} for i, k in enumerate(q)}}
                for _state, q in requests]
    monkeypatch.setattr(jev, "decide_many", fake)
    reqs = [{"id": f"R-{i}", "text": f"t{i}", "source": {"regulation": "UN R48", "page": 3, "paragraph": "6.1"}}
            for i in range(3)]
    p = jev.score_requirements("spec", reqs, form="B", batch=2)
    assert len(seen) == 2 and seen[0][0].startswith("Component specification:")
    assert "UN R48, paragraph 6.1 (page 3)" in seen[0][1]["q0"]["instructions"]
    assert p == {"R-0": 0.1, "R-1": 0.2, "R-2": 0.1}


def test_score_paragraphs_kuerzt_lange_absaetze(monkeypatch):
    seen = []
    def fake(requests, workers=8, model=jev.MODEL):
        seen.extend(requests)
        return [{"answers": {k: {"type": "boolean", "probability": 0.5} for k in q}} for _s, q in requests]
    monkeypatch.setattr(jev, "decide_many", fake)
    reg = SimpleNamespace(name="UN R10", title="EMC")
    par = SimpleNamespace(label="6.9.1", headings=("Specifications",), page=12, text="x" * (jev.PARA_MAX_CHARS + 50))
    assert jev.score_paragraphs("spec", [(reg, par)]) == [0.5]
    assert seen[0][1]["q0"]["instructions"].count("x") <= jev.PARA_MAX_CHARS + 5
