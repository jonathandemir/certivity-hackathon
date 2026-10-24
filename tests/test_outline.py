"""AP3: Gliederung im Parser (title, headings)."""
from certreq.pdf import _title, parse_pdf
from certreq.regindex import load_index
from conftest import needs_package


def test_title_detection_rules():
    assert _title(["Rear position lamp"]) == "Rear position lamp"
    assert _title(["Presence", "Devices of R or R1 or R2 categories: Mandatory"]) == "Presence"
    assert _title(["Tell-tale.", "Closed-circuit tell-tale mandatory."]) == "Tell-tale"
    # Sätze und Satzfragmente sind keine Überschriften
    assert _title(["The approval mark shall be clearly legible and be indelible."]) == ""
    assert _title(["In length: The rear of the vehicle."]) == ""
    assert _title(["If not otherwise specified:"]) == ""
    assert _title(["Within 60 seconds of the activation of the acoustic warning signal required by paragraph",
                   "5.2.1.14.1.2., there shall be an automatic function"]) == ""
    # umgebrochene Überschrift nur, wenn der Absatz danach endet
    assert _title(["Specifications concerning the immunity of ESAs to transient", "disturbances"]) \
        == "Specifications concerning the immunity of ESAs to transient disturbances"
    assert _title(["Two samples bearing the new trade", "name or mark", "and more text"]) == ""


@needs_package
def test_headings_main_text_and_annex_parts():
    idx = load_index()
    r48 = {p.label: p for p in parse_pdf(idx["UN R48"].base.pdfs[0])}
    assert r48["6.10"].title == "Rear position lamp"
    assert r48["6.10.1"].title == "Presence" and r48["6.10.1"].body.startswith("Devices of R")
    assert r48["6.10.4.1"].title == ""  # „In width: …" ist Inhalt
    assert r48["6.10.5.1"].headings == ("Individual specifications", "Rear position lamp", "Geometric visibility")
    assert r48["12"].title == "Transitional provisions"
    r150 = {p.label: p for p in parse_pdf(idx["UN R150"].base.pdfs[0])}
    assert r150["Annex 6 Part 4 1"].headings == ("Environmental Testing", "Resistance to corrosion")
    assert r150["Annex 4 Part 1 1.2"].headings[:2] == ("Photometric and colorimetric measurements",
                                                       "Photometric measurements of retro-reflective devices")
    r10 = {p.label: p for p in parse_pdf(idx["UN R10"].base.pdfs[0])}
    assert r10["Annex 9 3.1"].headings[0].startswith("Method(s) of testing for immunity of electrical/electronic sub-assemblies")
    assert r10["6.9.1"].headings[-1].startswith("Specifications concerning the immunity of ESAs to transient")
