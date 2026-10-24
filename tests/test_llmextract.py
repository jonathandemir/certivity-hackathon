"""AP4: LLM-Extraktion ohne Netz (ask_many ersetzt): Batches, Reihenfolge, Rückfall bei fehlender Antwort."""
from certreq import llm, llmextract
from certreq.pdf import Paragraph
from certreq.regindex import Regulation, Version


def _reg(name):
    return Regulation(name, f"title of {name}", (Version(name, "base", "1.0.0", ()),))


def _p(label, text="The lamp shall be red."):
    return Paragraph(label, label, 3, 3, text, "", ("Section", "Sub"))


def test_batches_split_by_regulation_size_and_count(monkeypatch):
    monkeypatch.setattr(llmextract, "BATCH_PARAS", 3)
    a, b = _reg("UN R1"), _reg("UN R2")
    cands = [(a, _p(f"1.{i}")) for i in range(5)] + [(b, _p("2.1"))]
    batches = llmextract._batches(cands)
    assert [[p.label for _, p in bt] for bt in batches] == [["1.0", "1.1", "1.2"], ["1.3", "1.4"], ["2.1"]]
    prompt = llmextract._user_prompt("# spec: Lamp", batches[0])
    assert "[1] paragraph 1.0 | section: Section > Sub | page 3" in prompt and "UN R1 (title of UN R1)" in prompt


def test_answers_map_to_paragraphs_with_fallback(monkeypatch):
    def fake_many(requests, workers=8):
        assert all(r["schema"] is llmextract.SCHEMA for r in requests)
        return [{"paragraphs": [{"ref": 1, "requirements": ["A shall x.", "A shall y."], "note": ""},
                                {"ref": 2, "requirements": [], "note": "definition"}]}]  # ref 3 fehlt

    monkeypatch.setattr(llm, "ask_many", fake_many)
    reg = _reg("UN R1")
    stats = {}
    reqs = llmextract.llm_requirements([(reg, _p("1.1")), (reg, _p("1.2")), (reg, _p("1.3", "Raw text shall stay."))],
                                       "# spec", stats=stats)
    assert [(r.paragraph, r.text) for r in reqs] == [("1.1", "A shall x."), ("1.1", "A shall y."),
                                                      ("1.3", "Raw text shall stay.")]
    assert reqs[0].regulation == "UN R1" and reqs[0].version == "1.0.0" and reqs[0].page == 3
    assert stats == {"batches": 1, "paragraphs": 3, "kept": 2, "dropped": 1, "missing": 1}


def test_schema_is_strict():
    item = llmextract.SCHEMA["properties"]["paragraphs"]["items"]
    assert item["additionalProperties"] is False and set(item["required"]) == set(item["properties"])
