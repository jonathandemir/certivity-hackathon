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
    n = len(calls)
    same, d = vision.apply(case, "auto")  # Spec vorhanden → Zeichnung nicht nötig
    assert same is case and d is None and len(calls) == n
    drawing_only, d = vision.apply(Case("c", img.parent, spec_text="", images=[img]), "auto")
    assert d == DESC and "Outer lens" in drawing_only.spec_text and len(calls) == n + 1


def test_spec_parts_wie_demo():
    spec = "# spec: X\n\n## Main Parts\n\n- Outer lens\n* Stop lamp\n\n## Materials\n- PMMA\n"
    assert vision.spec_parts(spec) == ["Outer lens", "Stop lamp"]


def _png(tmp_path, w=200, h=100):
    import pymupdf
    p = tmp_path / "view.png"
    pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, w, h), False).save(str(p))
    return p


def test_regions_rechnet_tausendstel_in_pixel_und_filtert(monkeypatch, tmp_path):
    img = _png(tmp_path)
    case = Case("c", tmp_path, "## Main Parts\n- Outer lens\n", [img])
    seen = {}
    def fake(system, user, schema, **kw):
        seen["enum"] = schema["properties"]["parts"]["items"]["properties"]["spec_parts"]["items"]["enum"]
        return {"parts": [{"label": "Lens", "note": "red", "box": {"x0": 500, "y0": 1200, "x1": 100, "y1": -5},
                           "spec_parts": ["Outer lens", "Erfunden"]}]}
    monkeypatch.setattr(vision.llm, "ask_json", fake)
    reg = vision.regions(case)
    assert seen["enum"] == ["Outer lens"]
    assert (reg["width"], reg["height"]) == (200, 100)
    assert reg["parts"][0]["bbox"] == [20, 0, 100, 100]  # sortiert, auf 0..1000 begrenzt, in Pixel
    assert reg["parts"][0]["spec_parts"] == ["Outer lens"]
    out = vision.draw_regions(case, reg, tmp_path / "k.png")
    assert out.stat().st_size > 0


def test_regions_ohne_zeichnung():
    assert vision.regions(Case("c", None, "spec", [])) is None
