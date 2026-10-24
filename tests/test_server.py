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
