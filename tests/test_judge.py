"""AP10-Richter ohne Netz: Kandidaten, 1:1-Zuordnung, Kennzahlen, Lizenzschutz des Berichts."""
import pytest

from certreq import judge as J


def req(id_, text, reg="UN R148", page=10, par="5.1"):
    return {"id": id_, "text": text, "source": {"regulation": reg, "version": "1.6.0", "page": page, "paragraph": par}}


def test_para_key_wie_plattform():
    assert J._para_key("Annex 8, 2.1.") == J._para_key("annex 8 2.1") == "annex 8 2.1"
    assert J._para_key("5.1.4.4.1. Table 3") == "5.1.4.4.1"
    assert J._para_key("5.4.2.3") != J._para_key("5.4.23")


def test_kandidaten_nur_gleiche_regelung_und_nahe_seite():
    exp = [req("G1", "a", page=10, par="5.1")]
    ours = [req("R1", "x", page=10, par="5.1"), req("R2", "x", page=11, par="9.9"), req("R3", "x", page=13, par="9.9"),
            req("R4", "x", page=30, par="5.1."), req("R5", "x", reg="UN R48", page=10, par="5.1")]
    ids = [r["id"] for r in J.candidates(exp, ours)["G1"]]
    assert ids[:2] == ["R1", "R4"]  # gleicher Absatz zuerst, auch weit weg
    assert set(ids) == {"R1", "R2", "R4"}  # R3 zu weit, R5 andere Regelung


def test_max_matching_ist_eins_zu_eins_und_maximal():
    # G1 kann nur R1; G2 kann R1 oder R2 → beide zuordenbar (G2 muss auf R2 ausweichen)
    m = J.max_matching({"G2": ["R1", "R2"], "G1": ["R1"], "G3": []})
    assert m == {"G1": "R1", "G2": "R2"}
    assert J.max_matching({"G1": ["R1"], "G2": ["R1"]}) in ({"G1": "R1"}, {"G2": "R1"})


@pytest.fixture
def fake_llm(monkeypatch):
    """Ersatz-LLM: ein Kandidat passt genau dann, wenn sein Text dem Referenztext gleicht."""
    def ask_many(requests, workers=8):
        out = []
        for rq in requests:
            lines = rq["user"].splitlines()
            ref = lines[1]
            hits = [ln.split("]")[0][1:] for ln in lines if ln.startswith("[c") and ln.split(") ", 1)[1] == ref]
            out.append({"matching_ids": hits, "reason": "fake"})
        return out
    monkeypatch.setattr(J.llm, "ask_many", ask_many)


def test_expected_gegen_sich_selbst_ist_perfekt(fake_llm):
    exp = [req("G1", "The lamp shall be red."), req("G2", "The lamp shall be white.", page=11, par="5.2")]
    sub = {"requirements": [dict(r, id=f"R{i}") for i, r in enumerate(exp)]}
    lv = J.judge(sub, exp)["level"]
    assert (lv["precision"], lv["recall"], lv["f2"]) == (1.0, 1.0, 1.0)


def test_fehlende_und_ueberzaehlige(fake_llm):
    exp = [req("G1", "A shall."), req("G2", "B shall."), req("G3", "C shall.", reg="UN R10")]
    sub = {"requirements": [req("R1", "A shall."), req("R2", "X shall."), req("R3", "Y shall."), req("R4", "Z shall.")]}
    rep = J.judge(sub, exp)
    assert rep["level"]["n_matched"] == 1 and rep["level"]["precision"] == 0.25 and rep["level"]["recall"] == pytest.approx(1 / 3, abs=1e-4)
    assert rep["no_candidates"] == ["G3"]
    assert rep["recall_by_regulation"] == {"UN R10": "0/1", "UN R148": "1/2"}


def test_oeffentliche_zusammenfassung_ohne_expected_texte(fake_llm):
    exp = [req("G1", "GEHEIMER GOLDTEXT shall.")]
    rep = J.judge({"requirements": [req("R1", "anders shall.")]}, exp)
    pub = J.public_summary(rep)
    assert "GEHEIMER GOLDTEXT" not in str(pub) and pub["missed_ids"] == ["G1"]


def test_prompt_erzwingt_gueltige_ids_und_modus():
    rq = J._request(req("G1", "ref"), [req("R1", "a"), req("R2", "b")], lenient=False)
    assert rq["schema"]["properties"]["matching_ids"]["items"]["enum"] == ["c1", "c2"]
    assert J.STRICT in rq["system"] and rq["model"] == J.llm.STRONG_MODEL
