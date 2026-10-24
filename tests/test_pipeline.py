import json

import pytest

from certreq.case import load_case
from certreq.evaluate import f2, validate
from certreq.pdf import parse_pdf
from certreq.regindex import load_index
from certreq.select import select_regulations
from certreq.submission import MAX_TEXT, Requirement, build_submission, write_submission
from conftest import DEV_CASE, needs_package


def test_f2():
    assert f2(1.0, 1.0) == 1.0
    assert f2(0.0, 0.0) == 0.0
    assert f2(0.5, 1.0) == pytest.approx(5 * 0.5 / 3)


def test_build_submission_ids_text_and_optional_fields():
    reqs = [Requirement("  The lamp\nshall   emit red light. ", "UN R148", "1.6.0", 6, "5.1"),
            Requirement("x" * (MAX_TEXT + 50), "UN R48", "9.3.0", 19),
            Requirement("   ", "UN R48", "9.3.0", 19)]
    data = build_submission("team-x", "dev-rear-lamp", reqs)
    items = data["requirements"]
    assert [r["id"] for r in items] == ["R-0001", "R-0002"]  # leerer Text fällt weg, IDs eindeutig
    assert items[0]["text"] == "The lamp shall emit red light."
    assert items[0]["source"] == {"regulation": "UN R148", "version": "1.6.0", "page": 6, "paragraph": "5.1"}
    assert "paragraph" not in items[1]["source"] and len(items[1]["text"]) == MAX_TEXT


@needs_package
def test_index_base_versions_and_pdf_paths():
    idx = load_index()
    assert len(idx) == 56
    assert idx["UN R148"].base.label == "1.6.0"
    assert idx["UN R10"].base.label == "7.2.0"
    assert idx["UN R148"].base.pdfs[0].name == "UN_R148_base.pdf"


@needs_package
def test_case_never_reads_expected():
    case = load_case(DEV_CASE)
    assert case.case_id == "dev-rear-lamp"
    assert "Rear lamp" in case.spec_text and "G-0001" not in case.spec_text
    assert [p.name for p in case.images] == ["exploded_view.png"]


@needs_package
def test_select_forced_and_unknown():
    case = load_case(DEV_CASE)
    assert [r.name for r in select_regulations(case, ["UN R148", "UN R10"])] == ["UN R148", "UN R10"]
    with pytest.raises(SystemExit):
        select_regulations(case, ["UN R999"])


@needs_package
def test_pdf_paragraphs_header_and_annex_labels():
    idx = load_index()
    r148 = parse_pdf(idx["UN R148"].base.pdfs[0])
    p = next(p for p in r148 if p.label == "4.8.1.7")
    assert p.page == 14 and "continuously lit" in p.text
    assert not any("| page " in p.text for p in r148), "Kopfzeile darf nicht im Absatztext landen"
    r150 = {p.label: p for p in parse_pdf(idx["UN R150"].base.pdfs[0])}
    assert r150["3.3.1.1"].page == 7  # Tabellenzelle "Annex 10 (values in" auf S. 5 darf den Kontext nicht kapern
    assert r150["Annex 4 Part 1 1.2"].page == 28


@needs_package
def test_paragraph_labels_match_reference(dev_expected):
    """Jedes (Regelung, Absatz, Seite) der Referenz muss der Parser mit gleichem Label und passender Seite finden."""
    idx = load_index()
    pairs = {(r["source"]["regulation"], r["source"]["paragraph"], r["source"]["page"]) for r in dev_expected}
    missing = []
    for reg, par, page in pairs:
        label = par.split(". Table")[0].rstrip(".")
        found = [p for p in parse_pdf(idx[reg].base.pdfs[0]) if p.label == label]
        if not any(p.page - 1 <= page <= p.end_page + 1 for p in found):
            missing.append((reg, par, page))
    assert not missing, f"{len(missing)}/{len(pairs)} nicht gefunden: {sorted(missing)[:10]}"


@needs_package
def test_written_submission_passes_validate_py(tmp_path):
    data = build_submission("team-x", "dev-rear-lamp", [Requirement("The lamp shall be red.", "UN R148", "1.6.0", 6, "5.1")])
    ok, out = validate(write_submission(data, tmp_path / "s.json"))
    assert ok, out
    bad = build_submission("team-x", "dev-rear-lamp", [Requirement("x", "UN R148", "1.7.0-falsch", 6)])
    ok, _ = validate(write_submission(bad, tmp_path / "bad.json"))
    assert not ok
    assert json.loads((tmp_path / "s.json").read_text())["team_id"] == "team-x"
