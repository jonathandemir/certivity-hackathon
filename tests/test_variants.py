import gzip
import json

import pytest

from certreq.variants import drop_regulations, per_regulation, save_variant


def _sub():
    reqs = [{"id": f"R-{i}", "text": "x shall y", "source": {"regulation": reg, "version": "1", "page": 1}}
            for i, reg in enumerate(["UN R42", "UN R42", "UN R94", "UN R127", "UN GTR 9"])]
    return {"team_id": "team-12", "case_id": "heldout-front-bumper", "requirements": reqs}


def test_drop_keeps_other_requirements_unchanged():
    sub = _sub()
    var = drop_regulations(sub, ["UN R94"])
    assert per_regulation(var) == {"UN R42": 2, "UN R127": 1, "UN GTR 9": 1}
    assert [r for r in sub["requirements"] if r["source"]["regulation"] != "UN R94"] == var["requirements"]
    assert var["case_id"] == sub["case_id"] and len(sub["requirements"]) == 5  # Original unverändert


def test_drop_rejects_unknown_regulation():
    with pytest.raises(SystemExit, match="Nicht in der Abgabe"):
        drop_regulations(_sub(), ["UN R94 "])


def test_save_variant_writes_run_folder(tmp_path):
    (tmp_path / "H001").mkdir()
    (tmp_path / "H001" / "meta.json").write_text(json.dumps({"git": {"commit": "main@abc1234"}}), encoding="utf-8")
    dest = save_variant("H001", "H001-noR94", drop_regulations(_sub(), ["UN R94"]), ["UN R94"], runs=tmp_path)
    with gzip.open(dest / "submission.json.gz", "rt", encoding="utf-8") as fh:
        assert len(json.load(fh)["requirements"]) == 4
    meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
    assert meta["derived_from"] == "H001" and meta["base_git"]["commit"] == "main@abc1234"
    with pytest.raises(SystemExit, match="existiert schon"):
        save_variant("H001", "H001-noR94", _sub(), [], runs=tmp_path)
