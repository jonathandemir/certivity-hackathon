"""AP7: Sub-Goal-Diff alt/neu (certreq/subgoal.py)."""
import json
import subprocess
import sys

from certreq import paths
from certreq.pdf import Paragraph
from certreq.subgoal import _canon, compare, diff_phrases, evaluate, split_sentences
from conftest import needs_package

SUBGOAL_DEV = paths.PKG_DIR / "subgoal" / "dev"


def test_diff_phrases_matches_reference_style():
    assert diff_phrases("The lamp shall emit red light.", "The lamp shall emit amber light.") == ["'red' became 'amber'"]
    assert diff_phrases("a b c", "a b c") == []
    assert diff_phrases("a b", "a x b") == ["'x' was added"]
    assert diff_phrases("a x b", "a b") == ["'x' was removed"]


def test_spelling_variants_are_not_changes():
    assert diff_phrases("not more than 70% after 6 seconds", "not more than 70 per cent after 6 s") == []
    assert _canon("... greater than 10 km/h. 5.1.4.2") == "... greater than 10 km/h."  # Parser-Rest am Ende
    assert diff_phrases("Acceleration limit shall apply.", "Acceleration from standstill Acceleration limit shall apply.") == []  # Überschrift


def test_split_sentences_keeps_references_and_list_items():
    p = Paragraph("6.6.2.2", "6.6.2.2", 11, 11,
                  "The procedure shall be as follows: (a) Position the vehicle. (b) Hold it, see paragraph 5.1.2. are met.")
    s = split_sentences(p)
    assert [x.text for x in s][1].startswith("(a) Position")
    assert s[1].lead == "The procedure shall be as follows:"  # Pflicht steckt in der Einleitung
    assert any("paragraph 5.1.2. are met" in x.text for x in s)  # „5.1.2. are“ trennt nicht


def test_evaluate_counts_by_type():
    exp = {"changes": [{"change": "modified", "requirement_id": "R-1"}, {"change": "removed", "requirement_id": "R-2"},
                       {"change": "added", "requirement_id": None, "source": {"paragraph": "6.1"}}]}
    got = {"changes": [{"change": "modified", "requirement_id": "R-1"}, {"change": "modified", "requirement_id": "R-9"},
                       {"change": "added", "requirement_id": None, "source": {"paragraph": "6.1"}}]}
    r = evaluate(got, exp)
    assert r["modified"]["recall"] == 1.0 and r["modified"]["precision"] == 0.5
    assert r["removed"]["recall"] == 0.0 and r["added"]["recall"] == 1.0


@needs_package
def test_dev_case_is_valid_and_finds_most_changes(tmp_path):
    reqs = json.loads((SUBGOAL_DEV / "requirements_old.json").read_text(encoding="utf-8"))
    sub = compare(SUBGOAL_DEV / "old.pdf", SUBGOAL_DEV / "new.pdf", reqs, "team-x", "subgoal-dev")
    out = tmp_path / "sub.json"
    out.write_text(json.dumps(sub), encoding="utf-8")
    r = subprocess.run([sys.executable, str(paths.TOOLS_DIR / "validate.py"), str(out), "--requirements-old",
                        str(SUBGOAL_DEV / "requirements_old.json")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    exp = json.loads((SUBGOAL_DEV / "expected.json").read_text(encoding="utf-8"))
    res = evaluate(sub, exp)  # Untergrenzen aus der Messung E003-am (Recall 6/6, 1/1, 13/17); nur Regressionsschutz
    assert res["modified"]["recall"] == 1.0 and res["removed"]["recall"] == 1.0
    assert res["added"]["recall"] >= 0.7
