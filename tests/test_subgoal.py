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
    res = evaluate(sub, exp)  # Untergrenzen aus der Messung E037-am (Recall 6/6, 1/1, 17/17); nur Regressionsschutz
    assert res["modified"]["recall"] == 1.0 and res["removed"]["recall"] == 1.0
    assert res["added"]["recall"] >= 0.94


def test_coordinated_obligations_are_split():
    from certreq.subgoal import split_coordinated
    parts = split_coordinated("For tests without a target the ACPE shall be deactivated if necessary, and may be combined where feasible.")
    assert parts == ["For tests without a target the ACPE shall be deactivated if necessary.",
                     "For tests without a target the ACPE may be combined where feasible."]
    assert split_coordinated("The lamp shall be red and white.") == ["The lamp shall be red and white."]


def test_obligations_without_shall_and_condition_lists():
    from certreq.subgoal import NORM_RE, Sentence, _obligations
    assert NORM_RE.search("The lateral offset is not more than 25 per cent of the vehicle width.")
    assert NORM_RE.search("An ACPE intervention is not required when:")
    assert not NORM_RE.search("Offset of vehicle and target")
    lead = "An ACPE intervention is not required when:"
    items = [Sentence("5.1.4.1", 4, "(a) there is an AEBS warning; or", lead), Sentence("5.1.4.1", 4, "(b) the speed is above 10 km/h.", lead)]
    out = _obligations(items)
    assert len(out) == 1 and out[0][1].startswith(lead) and "(b) the speed" in out[0][1]  # Alternativen = eine Pflicht
    steps = [Sentence("6.6", 9, "(a) Position the vehicle.", "The procedure shall be as follows:"),
             Sentence("6.6", 9, "(b) Hold it.", "The procedure shall be as follows:")]
    assert len(_obligations(steps)) == 2  # Prüfschritte bleiben einzeln


def test_align_is_one_to_one_and_uses_context():
    from certreq.subgoal import Sentence, align
    old = [Sentence("6.5", 1, t, "") for t in ("(a) Position the vehicle at the target.", "(b) Hold the vehicle stationary.",
                                              "(c) Accelerate the vehicle to the speed.")]
    new = [Sentence("6.6.1", 1, t, "") for t in ("(a) Position the vehicle at the relevant target.", "(b) Hold the vehicle stationary.",
                                                "(c) Accelerate the vehicle to the speed.")]
    new += [Sentence("6.6.2", 2, t, "") for t in ("(a) Release the brake so it creeps.", "(b) Hold the vehicle stationary.")]
    pairs = align(old, new)
    assert pairs[1][0] == 1  # die wortgleiche Kopie in 6.6.2 bleibt frei (→ added)
    assert len({j for j, _ in pairs.values()}) == len(pairs)


def test_editorial_changes_are_not_reported():
    assert diff_phrases("granted type approvals under paragraph 2.45.)", "granted type-approvals under paragraph 2.45).") == []
    assert diff_phrases("the Contracting Parties applying this Regulation", "the contracting parties applying this UN Regulation") == []
