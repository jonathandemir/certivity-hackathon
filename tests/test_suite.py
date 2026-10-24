import json

from certreq import paths
from certreq.suite import score_component, summarize

SUITE = paths.REPO_ROOT / "experiments" / "selection-suite"


def test_score_component_ignores_unsure_and_marks_traps():
    exp = {"sure": ["UN R149", "UN R48", "UN R10"], "unsure": ["UN R26"], "traps": ["UN R19"]}
    r = score_component(["UN R149", "UN R19", "UN R26"], exp)
    assert r["hits"] == ["UN R149"]
    assert r["missing"] == ["UN R10", "UN R48"]
    assert r["wrong"] == ["UN R19"]  # unsure zählt nicht als falsch
    assert r["traps_taken"] == ["UN R19"]


def test_summarize_micro_average():
    res = {"a": score_component(["X", "Y"], {"sure": ["X"]}), "b": score_component(["Z"], {"sure": ["Z", "W"]})}
    s = summarize(res)
    assert (s["hits"], s["missing"], s["wrong"]) == (2, 1, 1)
    assert s["precision"] == 0.6667 and s["recall"] == 0.6667
    assert s["components_exact"] == 0


def test_expected_matches_spec_folders():
    exp = json.loads((SUITE / "expected.json").read_text(encoding="utf-8"))["components"]
    folders = {p.name for p in SUITE.iterdir() if p.is_dir()}
    assert set(exp) == folders
    for name, e in exp.items():
        assert (SUITE / name / "spec.md").is_file()
        assert e["sure"], name
        groups = [set(e["sure"]), set(e.get("unsure", [])), set(e.get("traps", []))]
        assert not (groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]), name
