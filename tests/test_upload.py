"""Upload-Vorbereitung: gleicher Inhalt wie der gemessene Lauf, nur echte Team-ID, offizielle Validierung."""
import gzip
import json

from certreq import upload
from conftest import needs_package


@needs_package
def test_team_id_ersetzt_inhalt_sonst_identisch(tmp_path, monkeypatch):
    sub = {"team_id": "team-unregistered", "case_id": "dev-rear-lamp", "requirements": [
        {"id": "R-0001", "text": "The lamp shall be red.",
         "source": {"regulation": "UN R148", "version": "1.6.0", "page": 6, "paragraph": "5.1"}}]}
    run = tmp_path / "runs" / "E999"
    run.mkdir(parents=True)
    with gzip.open(run / "submission.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(sub, fh)
    monkeypatch.setattr(upload, "RUNS", tmp_path / "runs")
    out, ok, msg = upload.prepare("E999", "team-42", tmp_path / "up")
    data = json.loads(out.read_text())
    assert ok, msg
    assert out.name == "E999-dev-rear-lamp.json" and data["team_id"] == "team-42"
    assert data["requirements"] == sub["requirements"]


@needs_package
def test_subgoal_bekommt_requirements_old():
    assert upload.requirements_old("subgoal-dev").name == "requirements_old.json"
    assert upload.requirements_old("dev-rear-lamp") is None
