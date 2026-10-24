"""Abgabedatei im Format von schemas/submission_main.schema.json schreiben."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Team-ID auf hackathon.certivity.io (Team BarelyLegal), kein Geheimnis. Override: --team-id / CERTIVITY_TEAM_ID.
TEAM_ID = "team-12"
MAX_TEXT = 2000
MAX_REQUIREMENTS = 5000


@dataclass
class Requirement:
    text: str
    regulation: str  # exakt wie im Index
    version: str  # version_label der base-Version
    page: int  # 1-basiert, Seite im PDF dieser Version
    paragraph: str | None = None
    test_case: str | None = None


def build_submission(team_id: str, case_id: str, reqs: list[Requirement]) -> dict:
    if len(reqs) > MAX_REQUIREMENTS:
        raise ValueError(f"{len(reqs)} Anforderungen, erlaubt sind {MAX_REQUIREMENTS}")
    items = []
    for i, r in enumerate(reqs, start=1):
        text = " ".join(r.text.split())
        if not text:
            continue
        source = {"regulation": r.regulation, "version": r.version, "page": int(r.page)}
        if r.paragraph:
            source["paragraph"] = r.paragraph
        item = {"id": f"R-{i:04d}", "text": text[:MAX_TEXT], "source": source}
        if r.test_case:
            item["test_case"] = r.test_case
        items.append(item)
    return {"team_id": team_id, "case_id": case_id, "requirements": items}


def write_submission(data: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out_path
