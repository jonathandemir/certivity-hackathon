"""AP6 demo/server.py: Hilfsfunktionen und Laufdaten (ohne HTTP)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("werkbank_server", ROOT / "demo" / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def test_slug():
    assert server.slug("Front-Stoßfänger (v2)!") == "front-sto-f-nger-v2"
    assert server.slug("") == "fall"


def test_ids_are_safe():
    assert server.ID_RE.match("E016-a")
    assert not server.ID_RE.match("../etc")
    with pytest.raises(ValueError):
        server.load_run("../x")


def test_payload_of_recorded_run():
    if not (server.EXPERIMENTS / "E016-a" / "submission.json.gz").exists():
        pytest.skip("Messung E016-a fehlt")
    p = server.run_payload("E016-a")
    assert len(p["reqs"]) > 0 and p["run"]["selection"]
    assert {"id", "text", "reg", "version", "page", "para", "part"} <= set(p["reqs"][0])
    assert len(p["regs"]) == 56


def test_updates_and_impact_for_recorded_run():
    if not (server.EXPERIMENTS / "E016-a" / "submission.json.gz").exists():
        pytest.skip("Messung E016-a fehlt")
    p = server.run_payload("E016-a")
    ups = {u["reg"]: u for u in p["updates"]}
    for u in ups.values():  # nur zitierte Regelungen mit neuerer Fassung, deren PDFs vorliegen
        assert u["from"] != u["to"] and u["n"] > 0
    if "UN R148" not in ups:
        pytest.skip("R148 latest fehlt")
    res = server.run_impact("E016-a", "UN R148")
    assert res["old"] == ups["UN R148"]["from"] and res["new"] == ups["UN R148"]["to"]
    ids = {r["id"] for r in res["requirements"]}
    assert all(c["requirement_id"] in ids for c in res["submission"]["changes"] if c["requirement_id"])
    with pytest.raises(ValueError):
        server.run_impact("E016-a", "UN R999")
