"""certreq.sectionvariants ohne PDFs: Abschnitte weglassen, Rest byte-gleich, Tippfehler werden erkannt."""
import pytest

from certreq import sectionvariants as sv

PATHS = {"6.1": ("Individual specifications", "Front fog lamp"), "6.1.2": ("Individual specifications", "Front fog lamp", "Position"),
         "6.2": ("Individual specifications", "Side-marker lamps"), "5.1": ("General specifications",)}


def _sub():
    req = lambda i, reg, lab: {"id": i, "text": f"t{i}", "source": {"regulation": reg, "version": "1", "page": 1, "paragraph": lab}}
    return {"team_id": "t", "case_id": "c", "requirements": [req("R1", "UN R48", "6.1"), req("R2", "UN R48", "6.1.2"),
                                                             req("R3", "UN R48", "6.2"), req("R4", "UN R48", "5.1"),
                                                             req("R5", "UN R10", "6.1")]}


def test_drop_section_keeps_rest_identical():
    sub = _sub()
    new, removed = sv.drop_sections(sub, sv.parse_drop(["UN R48=front fog"]), paths_of=lambda reg: PATHS)
    assert [r["id"] for r in new["requirements"]] == ["R3", "R4", "R5"]  # R10 6.1 bleibt: andere Regelung
    assert new["requirements"][0] is sub["requirements"][2] and dict(removed) == {"UN R48=front fog": 2}


def test_typos_and_bad_specs_fail():
    with pytest.raises(SystemExit):
        sv.drop_sections(_sub(), sv.parse_drop(["UN R48=Rear fog lamp"]), paths_of=lambda reg: PATHS)
    with pytest.raises(SystemExit):
        sv.drop_sections(_sub(), sv.parse_drop(["UN R99=Front fog lamp"]), paths_of=lambda reg: PATHS)
    with pytest.raises(SystemExit):
        sv.parse_drop(["UN R48 Front fog lamp"])


def test_add_regulation_from_other_run_with_new_ids():
    other = {"requirements": [{"id": "R-0001", "text": "g", "source": {"regulation": "UN GTR 9", "version": "0.3.0", "page": 85, "paragraph": "4.1"}}]}
    new, added = sv.add_regulations(_sub(), ["H003=UN GTR 9"], load=lambda run: other)
    ids = [r["id"] for r in new["requirements"]]
    assert len(ids) == len(set(ids)) == 6 and new["requirements"][-1]["source"]["regulation"] == "UN GTR 9"
    with pytest.raises(SystemExit):
        sv.add_regulations(_sub(), ["H003=UN R48"], load=lambda run: other)  # schon in der Basis


def test_drop_zero_yield_only_hits_listed_paths():
    zero = {("UN R48", ("Individual specifications", "Front fog lamp"))}
    paths = lambda reg: {k: v[:2] for k, v in PATHS.items()}
    new, removed = sv.drop_zero_yield(_sub(), zero, paths_of=paths)
    assert [r["id"] for r in new["requirements"]] == ["R3", "R4", "R5"] and sum(removed.values()) == 2


def test_drop_pages_removes_all_requirements_on_listed_pages():
    sub = _sub()
    sub["requirements"][1]["source"]["page"] = 3
    assert sv.parse_pages(["UN R48=1-2, 5", "UN R10=7"]) == {"UN R48": {1, 2, 5}, "UN R10": {7}}
    new, removed = sv.drop_pages(sub, sv.parse_pages(["UN R48=3"]))
    assert [r["id"] for r in new["requirements"]] == ["R1", "R3", "R4", "R5"] and dict(removed) == {"UN R48 S.3": 1}
    with pytest.raises(SystemExit):
        sv.drop_pages(_sub(), sv.parse_pages(["UN R48=1-2"]))  # Seite 2 hat keine Anforderung
    with pytest.raises(SystemExit):
        sv.parse_pages(["UN R48=vierzig"])


def test_zero_yield_on_paragraph_level(tmp_path, monkeypatch):
    import json
    dev = {"requirements": [{"id": f"D{i}", "text": "t", "source": {"regulation": "UN R48", "version": "1", "page": 1,
                                                                   "paragraph": lab}}
                            for i, lab in enumerate(["6.1", "6.1", "6.1.2", "6.1.2"])]}
    (tmp_path / "DEV").mkdir()
    (tmp_path / "DEV" / "score.json").write_text(json.dumps({"judge": {"matches": [[0, "D2"]]}}))
    monkeypatch.setattr(sv, "RUNS", tmp_path)
    zero = sv.zero_yield_sections(["DEV"], {"UN R48"}, min_count=2, depth=0, load=lambda rid: dev)
    assert zero == {("UN R48", ("¶", "6.1"))}  # 6.1.2 hat einen Treffer, R10 kommt auf dev nicht vor
    new, removed = sv.drop_zero_yield(_sub(), zero, depth=0)
    assert [r["id"] for r in new["requirements"]] == ["R2", "R3", "R4", "R5"] and sum(removed.values()) == 1
