"""AP5 ohne Netz: Bilder im LLM-Aufruf, Cache-Schlüssel, Modi off/on/only."""
import pytest

from certreq import llm, vision
from certreq.case import Case

DESC = {"product": "Rear lamp", "vehicle_location": "rear", "uncertainties": ["colour unknown"],
        "parts": [{"name": "Outer lens", "function": "covers", "technology": "transparent plastic", "evidence": "x"}]}


@pytest.fixture
def img(tmp_path):
    p = tmp_path / "view.png"
    p.write_bytes(b"\x89PNG fake")
    return p


def test_bild_geht_als_data_url_mit_und_der_schluessel_nur_als_hash(monkeypatch, tmp_path, img):
    sent = []
    monkeypatch.setattr(llm, "_call", lambda m, msgs, rf, *a: (sent.append(msgs), ('{"ok": true}', {}))[1])
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "c")
    monkeypatch.delenv("CERTREQ_LLM_CACHE", raising=False)
    llm.ask_json("s", "u", None, images=[img])
    llm.ask_json("s", "u", None, images=[img])  # Cache-Treffer
    assert len(sent) == 1
    content = sent[0][1]["content"]
    assert content[0] == {"type": "text", "text": "u"} and content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    cached = next((tmp_path / "c").glob("*.json")).read_text()
    assert "base64" not in cached  # Bildbytes landen nicht im Cache
    img.write_bytes(b"\x89PNG anderes Bild")
    llm.ask_json("s", "u", None, images=[img])
    assert len(sent) == 2  # anderes Bild → neuer Aufruf


def test_modi(monkeypatch, img):
    calls = []
    monkeypatch.setattr(vision.llm, "ask_json", lambda *a, **kw: (calls.append(kw), DESC)[1])
    case = Case("c", img.parent, spec_text="# Spec\nRear lamp with LEDs", images=[img])
    same, d = vision.apply(case, "off")
    assert same is case and d is None and not calls
    on, d = vision.apply(case, "on")
    assert on.spec_text.startswith("# Spec") and "From the drawing" in on.spec_text and "Outer lens" in on.spec_text
    assert calls[-1]["images"] == [img]
    only, _ = vision.apply(case, "only")
    assert "# Spec" not in only.spec_text and "Outer lens" in only.spec_text
    with pytest.raises(SystemExit):
        vision.apply(Case("c", img.parent, spec_text="x"), "only")  # only ohne Zeichnung
