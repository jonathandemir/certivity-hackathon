"""AP6: Die Demo-Seite entsteht aus der Pipeline-Ausgabe und verlinkt jede Anforderung auf ihre PDF-Seite."""
import json
import re
import sys
from pathlib import Path

from certreq import paths
from certreq.regindex import load_index
from conftest import needs_package

sys.path.insert(0, str(paths.REPO_ROOT / "demo"))
import build as demo_build  # noqa: E402


def _data(page_html: str) -> dict:
    m = re.search(r"const D = (.*?);\nconst \$", page_html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


@needs_package
def test_build_embeds_requirements_and_relative_pdf_links(tmp_path):
    reg = load_index()["UN R148"]
    sub = {"team_id": "t", "case_id": "dev-rear-lamp", "requirements": [
        {"id": "R-0001", "text": "The lamp shall </script><b>x</b> emit light.",
         "source": {"regulation": "UN R148", "version": reg.base.label, "page": 6, "paragraph": "5.1"}}]}
    src = tmp_path / "dev-rear-lamp.json"
    src.write_text(json.dumps(sub), encoding="utf-8")
    out = demo_build.build(src, None, tmp_path / "dist" / "index.html")
    page = out.read_text(encoding="utf-8")
    assert page.count("</script>") == 1  # Daten dürfen das Skript nicht schließen
    data = _data(page)
    assert data["requirements"][0]["text"].startswith("The lamp shall </script>")
    rel = data["pdf"]["UN R148"][reg.base.label]
    assert not Path(rel).is_absolute()
    assert (out.parent / rel).resolve().exists()  # Link zeigt auf das echte PDF
    assert data["case"]["spec"]  # Fall wird aus case_id im Paket gefunden
