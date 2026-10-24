"""Arena (certreq/arena.py): Leck-Schutz, Fallaufteilung, Bewertung ohne LLM."""
from certreq import arena


def test_leaks_find_brands_and_part_numbers():
    words = {"hella", "akrapovic", "tesla"}
    assert arena.leaks("Rule 3: a Hella lamp needs R148", words) == ["hella"]
    assert arena.leaks("part 2BA 959 822 is special", words)
    assert not arena.leaks("Replacement exhaust systems for motorcycles fall under R92 only.", words)


def test_select_cases_keep_holdout_separate():
    sets = arena.select_cases()
    tune = {c["name"] for c in sets["tune"]}
    hold = {c["name"] for c in sets["holdout"]}
    assert not tune & hold
    assert all(n.startswith("real/") for n in hold)


def test_run_select_scores_without_llm(monkeypatch, tmp_path):
    from certreq import select as sel
    d = tmp_path / "lamp"
    d.mkdir()
    (d / "spec.md").write_text("# spec: lamp\nA lamp.", encoding="utf-8")

    class R:
        def __init__(self, n):
            self.name = n

    seen = []
    monkeypatch.setattr(sel, "select_regulations", lambda case, mode: (seen.append(sel.SYSTEM2), [R("UN R148"), R("UN R7")])[1])
    rep = arena.run_select("1. Prefer consolidated regulations.", [{"name": "x/lamp", "dir": d, "exp": {"sure": ["UN R148"], "unsure": [], "traps": ["UN R7"]}}])
    assert rep["summary"]["hits"] == 1 and rep["summary"]["wrong"] == 1
    assert seen[0].endswith("1. Prefer consolidated regulations.")
    arena.run_select("", [])  # Zusatzblock wird wieder entfernt
    assert sel.SYSTEM2 == sel._ARENA_BASE
