#!/usr/bin/env python3
"""AP6 Demo: Pipeline-Ausgabe (out/<fall>.json + .meta.json) -> eine einzige HTML-Datei.

    .venv/bin/python demo/build.py out/dev-rear-lamp.json [--case <fall-ordner>] [--out demo/dist/index.html]

Die Seite liest nur die Ausgabe der Pipeline (Format: docs/CONTEXT.md §8, .meta.json von `certreq run`) und
verlinkt jede Anforderung auf ihre Quellseite im PDF (`...pdf#page=N`). Keine externen Abhängigkeiten, keine
Daten im Repo: PDFs bleiben unter vendor/ (gitignored); die Links sind relativ zur erzeugten Datei.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from certreq import paths  # noqa: E402
from certreq.regindex import load_index  # noqa: E402

TEMPLATE = Path(__file__).with_name("template.html")


def _pdf_links(index, out_dir: Path) -> dict[str, dict[str, str]]:
    """regulation -> version_label -> relativer Pfad zum (ersten) PDF der Version."""
    links: dict[str, dict[str, str]] = {}
    for name, reg in index.items():
        for v in reg.versions:
            if v.pdfs and v.pdfs[0].exists():
                rel = os.path.relpath(v.pdfs[0], out_dir)
                links.setdefault(name, {})[v.label] = Path(rel).as_posix()
    return links


def _case_info(case_dir: Path | None) -> dict:
    info: dict = {"title": "", "spec": "", "image": ""}
    if not case_dir or not case_dir.is_dir():
        return info
    spec = case_dir / "spec.md"
    if spec.exists():
        info["spec"] = spec.read_text(encoding="utf-8")
    for img in sorted(case_dir.iterdir()):
        if img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            mime = "image/png" if img.suffix.lower() == ".png" else "image/jpeg"
            info["image"] = f"data:{mime};base64," + base64.b64encode(img.read_bytes()).decode()
            break
    return info


def build(submission: Path, case_dir: Path | None, out: Path) -> Path:
    data = json.loads(submission.read_text(encoding="utf-8"))
    meta_path = submission.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if case_dir is None and data.get("case_id"):
        guess = paths.CASES_DIR / data["case_id"]
        case_dir = guess if guess.is_dir() else None
    out.parent.mkdir(parents=True, exist_ok=True)
    index = load_index()
    payload = {
        "case_id": data.get("case_id", ""),
        "team_id": data.get("team_id", ""),
        "requirements": data.get("requirements", []),
        "meta": {k: meta.get(k) for k in ("selected", "forced", "n_requirements", "seconds", "created_at", "git",
                                          "reasons") if k in meta},
        "titles": {n: r.title for n, r in index.items()},
        "pdf": _pdf_links(index, out.parent),
        "case": _case_info(case_dir),
    }
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", blob)
    page = page.replace("__TITLE__", html.escape(f"Certreq · {payload['case_id']}"))
    out.write_text(page, encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("submission", help="out/<fall>.json (daneben liegt <fall>.meta.json)")
    p.add_argument("--case", help="Fall-Ordner für Spezifikation + Zeichnung (Standard: aus case_id im Paket)")
    p.add_argument("--out", default=str(REPO / "demo" / "dist" / "index.html"))
    a = p.parse_args()
    out = build(Path(a.submission), Path(a.case) if a.case else None, Path(a.out))
    print(f"{out} ({out.stat().st_size // 1024} KB). Im Browser öffnen: file://{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
