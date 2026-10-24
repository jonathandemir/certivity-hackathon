#!/usr/bin/env python3
"""AP6 Demo: Pipeline-Ausgabe + Fall-Ordner -> demo/dist/data.js (+ index.html aus demo/web/).

    .venv/bin/python demo/prepare.py out/<fall>.json [--case <fall-ordner>] [--out-dir demo/dist]

Funktioniert für jeden Fall: Spezifikation und Explosionszeichnung sind beide optional (README: "a technical
specification and/or an exploded view"). Die App (demo/web/index.html, einmal mit Node gebaut und eingecheckt)
liest nur window.CERTREQ aus data.js; am Sonntag braucht es also kein Node, nur dieses Skript.

Was hier passiert:
  * Spezifikation lesen (Titel, Produkttyp, Fahrzeugklasse, Hauptbauteile), falls vorhanden.
  * Jede Anforderung einem Hauptbauteil zuordnen (Wortabgleich Bauteilname <-> Anforderungstext und
    Regelungstitel), sonst "Gesamtgerät". Heuristik, keine KI; im UI so gekennzeichnet.
  * Jede zitierte PDF-Seite als JPEG rendern und die Zeilen des zitierten Absatzes als Markierung bestimmen.
    Seiten mit den meisten Anforderungen zuerst, höchstens --max-pages (Größe von data.js).
Die Zerlegung der Zeichnung in Teile macht die App selbst im Browser (Zusammenhangsanalyse auf dem Bild).
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import pymupdf  # noqa: E402

from certreq import paths  # noqa: E402
from certreq.regindex import load_index  # noqa: E402

WEB = Path(__file__).with_name("web") / "index.html"
GENERIC = {"lamp", "lamps", "device", "devices", "unit", "part", "parts", "module", "system", "assembly", "light",
           "main", "component", "with", "and", "for", "the", "rear", "front", "side", "cover"}
WORD = re.compile(r"[a-z][a-z\-]{2,}")


# ---------------------------------------------------------------- Spezifikation
def parse_spec(text: str) -> dict:
    title = ""
    sections: dict[str, list[str]] = defaultdict(list)
    cur = None
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = re.sub(r"^#\s*(spec\s*:\s*)?", "", line, flags=re.I).strip()
        elif line.startswith("## "):
            cur = line[3:].strip().lower()
        elif cur is not None:
            sections[cur].append(line)

    def bullets(key: str) -> list[str]:
        for k, lines in sections.items():
            if key in k:
                return [re.sub(r"^[-*]\s*", "", ln).strip() for ln in lines if re.match(r"^\s*[-*]\s+\S", ln)]
        return []

    def para(key: str) -> str:
        for k, lines in sections.items():
            if key in k:
                return " ".join(ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("|")).strip()
        return ""

    return {"title": title, "productType": para("product type"), "category": para("vehicle category"),
            "functions": bullets("function"), "parts": bullets("main part")}


# ---------------------------------------------------------------- Zuordnung Anforderung -> Bauteil
def _words(s: str) -> list[str]:
    return WORD.findall(s.lower())


def make_matcher(parts: list[dict], titles: dict[str, str]):
    freq = Counter(w for p in parts for w in set(_words(p["name"])))
    rules = []
    for p in parts:
        name = p["name"].lower()
        phrase = re.compile(r"\b" + re.escape(name).replace(r"\ ", r"[\s\-]+") + r"(s|es)?\b")
        stems = [w[:6] for w in _words(name) if freq[w] == 1 and w not in GENERIC and len(w) >= 4]
        rules.append((p["id"], phrase, stems))

    def match(text: str, reg: str) -> str:
        t = text.lower()
        tw = _words(t)
        title = titles.get(reg, "").lower()
        best, best_s = "device", 0
        for pid, phrase, stems in rules:
            s = 3 if phrase.search(t) else 0
            s += sum(1 for st in stems if any(w.startswith(st) for w in tw))
            s += 2 * sum(1 for st in stems if st in title)
            if s > best_s:
                best, best_s = pid, s
        return best if best_s >= 2 else "device"

    return match


# ---------------------------------------------------------------- PDF-Seiten und Markierungen
def _overlap(a: str, b: str) -> float:
    A, B = set(_words(a)), set(_words(b))
    return len(A & B) / max(1, min(len(A), len(B)))


def find_lines(page: "pymupdf.Page", para: str, text: str, cache: dict) -> list[list[float]]:
    """Normierte Zeilenrechtecke [x, y, w, h] des zitierten Absatzes auf der Seite (leer, wenn nicht gefunden)."""
    if "blocks" not in cache:
        cache["blocks"] = [b for b in page.get_text("blocks") if b[6] == 0]
        cache["words"] = page.get_text("words")
    blocks = cache["blocks"]
    if not blocks:
        return []
    para = (para or "").strip().rstrip(".")
    starts = [b for b in blocks if para and re.match(re.escape(para) + r"\.?\s", b[4].strip())]
    cand = starts or blocks
    best = max(cand, key=lambda b: _overlap(b[4], text))
    if not starts and _overlap(best[4], text) < 0.35:
        return []
    words = [w for w in cache["words"] if w[5] == best[5]]
    lines: dict[int, list[float]] = {}
    first_line = None
    for w in sorted(words, key=lambda w: (w[6], w[7])):
        if first_line is None:
            first_line = w[6]
        r = lines.setdefault(w[6], [w[0], w[1], w[2], w[3], w[4]])
        r[0], r[1], r[2], r[3] = min(r[0], w[0]), min(r[1], w[1]), max(r[2], w[2]), max(r[3], w[3])
    out = []
    W, H = page.rect.width, page.rect.height
    for i, (ln, (x0, y0, x1, y1, first_word)) in enumerate(sorted(lines.items())):
        if i > 0 and re.fullmatch(r"\d+(\.\d+)*\.", first_word):
            break  # nächster nummerierter Absatz im selben Block
        out.append([round(x0 / W, 4), round(y0 / H, 4), round((x1 - x0) / W, 4), round((y1 - y0) / H, 4)])
        if len(out) >= 8:
            break
    return out


def render_pages(reqs: list[dict], index, max_pages: int, dpi: int) -> tuple[dict, dict]:
    by_page: dict[tuple, list[dict]] = defaultdict(list)
    for r in reqs:
        by_page[(r["reg"], r["version"], r["page"])].append(r)
    order = sorted(by_page, key=lambda k: -len(by_page[k]))[:max_pages]
    docs: dict[Path, pymupdf.Document] = {}
    pages, hits = {}, {}
    for reg, ver, pno in order:
        regobj = index.get(reg)
        v = next((v for v in (regobj.versions if regobj else ()) if v.label == ver), None)
        pdf = next((p for p in (v.pdfs if v else ()) if p.exists()), None)
        if not pdf:
            continue
        doc = docs.get(pdf) or docs.setdefault(pdf, pymupdf.open(pdf))
        if not (1 <= pno <= doc.page_count):
            continue
        page = doc[pno - 1]
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        jpg = pix.tobytes("jpeg", jpg_quality=60)
        key = f"{reg}#{ver}#{pno}"
        pages[key] = {"src": "data:image/jpeg;base64," + base64.b64encode(jpg).decode(), "w": pix.width,
                      "h": pix.height, "of": doc.page_count}
        cache: dict = {}
        for r in by_page[(reg, ver, pno)]:
            ln = find_lines(page, r["para"], r["text"], cache)
            if ln:
                hits[r["id"]] = ln
    return pages, hits


# ---------------------------------------------------------------- Zusammenbau
def build(submission: Path, case_dir: Path | None, out_dir: Path, max_pages: int, dpi: int) -> Path:
    data = json.loads(submission.read_text(encoding="utf-8"))
    meta_path = submission.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    case_id = data.get("case_id", "")
    if case_dir is None and case_id:
        guess = paths.CASES_DIR / case_id
        case_dir = guess if guess.is_dir() else None

    spec, spec_text, drawing = parse_spec(""), "", None
    if case_dir and case_dir.is_dir():
        sp = case_dir / "spec.md"
        if sp.exists():
            spec_text = sp.read_text(encoding="utf-8")
            spec = parse_spec(spec_text)
        img = next((p for p in sorted(case_dir.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg"}), None)
        if img:
            pm = pymupdf.Pixmap(str(img))
            mime = "image/png" if img.suffix.lower() == ".png" else "image/jpeg"
            drawing = {"src": f"data:{mime};base64," + base64.b64encode(img.read_bytes()).decode(),
                       "w": pm.width, "h": pm.height}

    index = load_index()
    titles = {n: r.title for n, r in index.items()}
    parts = [{"id": f"p{i + 1}", "n": i + 1, "name": n} for i, n in enumerate(spec["parts"])]
    match = make_matcher(parts, titles)

    reqs = []
    for i, r in enumerate(data.get("requirements", [])):
        s = r.get("source", {})
        reqs.append({"id": r.get("id") or f"R-{i + 1:04d}", "text": r.get("text", ""), "reg": s.get("regulation", ""),
                     "version": s.get("version", ""), "page": s.get("page", 0), "para": s.get("paragraph", ""),
                     "part": match(r.get("text", ""), s.get("regulation", ""))})

    counts = Counter(r["reg"] for r in reqs)
    versions = {r["reg"]: r["version"] for r in reqs}
    selected = set(meta.get("selected") or counts)
    regs = [{"id": n, "title": t, "selected": n in selected or n in counts, "count": counts.get(n, 0),
             "version": versions.get(n, "")} for n, t in titles.items()]

    pages, hits = render_pages(reqs, index, max_pages, dpi)
    payload = {
        "version": 1,
        "case": {"id": case_id, "title": spec["title"] or case_id, "productType": spec["productType"],
                 "category": spec["category"], "functions": spec["functions"], "parts": parts,
                 "hasSpec": bool(spec_text), "drawing": drawing},
        "run": {"seconds": meta.get("seconds"), "git": (meta.get("git") or {}).get("commit"),
                "created": meta.get("created_at"), "team": data.get("team_id", ""),
                "selection": meta.get("selection") or [], "drawingNote": meta.get("drawing")},
        "regs": regs, "reqs": reqs, "pages": pages, "hits": hits,
        "pagesTotal": len({(r["reg"], r["version"], r["page"]) for r in reqs}),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "data.js"
    out.write_text("window.CERTREQ = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    if WEB.exists():
        shutil.copyfile(WEB, out_dir / "index.html")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("submission", help="out/<fall>.json (daneben optional <fall>.meta.json)")
    p.add_argument("--case", help="Fall-Ordner mit spec.md und/oder Zeichnung (Standard: aus case_id)")
    p.add_argument("--out-dir", default=str(REPO / "demo" / "dist"))
    p.add_argument("--max-pages", type=int, default=150, help="höchstens so viele PDF-Seiten einbetten")
    p.add_argument("--dpi", type=int, default=120)
    a = p.parse_args()
    out = build(Path(a.submission), Path(a.case) if a.case else None, Path(a.out_dir), a.max_pages, a.dpi)
    d = json.loads(out.read_text(encoding="utf-8")[len("window.CERTREQ = "):-2])
    print(f"{out} ({out.stat().st_size // 1024} KB): {len(d['reqs'])} Anforderungen, {len(d['pages'])} Seiten, "
          f"{len(d['hits'])} markiert, {len(d['case']['parts'])} Bauteile. Öffnen: {out.parent / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
