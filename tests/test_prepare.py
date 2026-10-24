"""AP6 demo/prepare.py: Spezifikation lesen und Anforderungen Bauteilen zuordnen (ohne PDFs)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("prepare", Path(__file__).resolve().parent.parent / "demo" / "prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

SPEC = """# spec: Rear Lamp

## Product Type

Rear lamp — exterior lighting module.

## Vehicle Category

M1 — passenger car.

## Main Parts

- Rear position lamp
- Stop lamp
- Outer lens
- Retro-reflector
"""


def test_parse_spec():
    s = prepare.parse_spec(SPEC)
    assert s["title"] == "Rear Lamp"
    assert s["parts"] == ["Rear position lamp", "Stop lamp", "Outer lens", "Retro-reflector"]
    assert s["category"].startswith("M1")


def test_parse_spec_without_sections():
    s = prepare.parse_spec("just some text")
    assert s["parts"] == [] and s["title"] == ""


def test_matcher():
    parts = [{"id": f"p{i + 1}", "name": n} for i, n in enumerate(prepare.parse_spec(SPEC)["parts"])]
    m = prepare.make_matcher(parts, {"UN R150": "Retro-Reflective Devices (RRD)", "UN R10": "Electromagnetic compatibility"})
    assert m("All stop lamps shall be switched ON simultaneously.", "UN R48") == "p2"
    assert m("The device shall bear the trade name of the applicant.", "UN R150") == "p4"
    assert m("The outer lens shall be marked.", "UN R148") == "p3"
    assert m("The vehicle shall comply with the emission limits.", "UN R10") == "device"
