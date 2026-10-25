#!/usr/bin/env python3
"""BarelyLegal Werkbank: lokaler Server für das Produkt (AP6). Nur Standardbibliothek + pymupdf.

    .venv/bin/python demo/server.py            # öffnet http://127.0.0.1:8765 im Browser
    .venv/bin/python demo/server.py --port 9000 --no-browser

Was der Server kann (alles lokal, bindet nur an 127.0.0.1):
  * Fälle: Paket-Fälle (vendor/.../cases) und eigene Uploads (Spec und/oder Zeichnung, landen in out/cases/).
  * Prüfungen starten: `certreq run` als Unterprozess, Fortschritt per Abfrage (Log + Status), Ergebnis in out/runs/<id>/.
    Modus "best" = Bestmarke = Standard von certreq run (--select llm2 --filters all --extract modal,llm, braucht LLM-Key),
    Modus "fast" = Baseline ohne KI (--select b0 --filters none --extract none).
  * Läufe ansehen: eigene Läufe, abgelegte Messungen (experiments/runs/<ID>) und ältere out/<fall>.json.
  * PDF-Seiten werden erst bei Bedarf gerendert (Cache out/cache/pages), Markierung des zitierten Absatzes je Seite.
  * Review je Anforderung (offen/bestätigt/verworfen + Notiz), Export als Abgabe-JSON (ohne Verworfene) oder CSV.
  * Versionsvergleich (Sub-Goal, certreq.subgoal) für Ordner unter vendor/.../subgoal.
  * Änderungs-Check je Lauf: Gibt es zu einer zitierten Regelung eine neuere Fassung im Index, prüft derselbe Vergleich,
    welche Anforderungen DIESES Laufs sie ändert, entfernt oder ergänzt (/api/impact).
  * /present/<lauf>/ = die 3D-Präsentation (demo/web/index.html) mit den Daten des Laufs.
"""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

import pymupdf  # noqa: E402

import prepare  # noqa: E402
from certreq import paths  # noqa: E402
from certreq.regindex import load_index  # noqa: E402

WEB = HERE / "web"
RUNS = paths.OUT_DIR / "runs"
UPLOADS = paths.OUT_DIR / "cases"
REVIEWS = paths.OUT_DIR / "reviews"
PAGE_CACHE = paths.OUT_DIR / "cache" / "pages"
SUBGOAL_OUT = paths.OUT_DIR / "subgoal"
SUBGOAL_DIR = paths.PKG_DIR / "subgoal"
EXPERIMENTS = REPO / "experiments" / "runs"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
MODES = {
    "best": [],  # Standard von certreq run = gemessene Bestmarke (AGENTS.md §4), braucht LLM-Key
    "fast": ["--select", "b0", "--filters", "none", "--extract", "none"],
}
TYPICAL_SECONDS = {"best": 240, "fast": 25}

PROCS: dict[str, subprocess.Popen] = {}
LOCK = threading.Lock()
_payload_cache: dict[str, tuple[float, dict]] = {}
_docs: dict[Path, "pymupdf.Document"] = {}


# ---------------------------------------------------------------- Hilfen
def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:50] or "fall"


def llm_available() -> bool:
    """Grob: ein Key in der Umgebung oder eine .env(.local) im Repo (certreq.llm liest dieselben Quellen)."""
    keys = ("OPENAI_API_KEY", "LLM_API_KEY", "ANTHROPIC_API_KEY")
    return any(os.environ.get(k) for k in keys) or any((REPO / f).exists() for f in (".env.local", ".env"))


_gz_cache: dict[Path, tuple[float, object]] = {}


def read_json(p: Path, default=None):
    try:
        if p.suffix == ".gz":
            mt = p.stat().st_mtime
            hit = _gz_cache.get(p)
            if not hit or hit[0] != mt:
                hit = _gz_cache[p] = (mt, json.loads(gzip.decompress(p.read_bytes()).decode("utf-8")))
            return hit[1]
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def doc(pdf: Path) -> "pymupdf.Document":
    with LOCK:
        if pdf not in _docs:
            _docs[pdf] = pymupdf.open(pdf)
        return _docs[pdf]


def pdf_for(reg: str, ver: str) -> Path | None:
    r = load_index().get(reg)
    for v in (r.versions if r else ()):
        if v.label == ver:
            return next((p for p in v.pdfs if p.exists()), None)
    return None


# ---------------------------------------------------------------- Fälle
def list_cases() -> list[dict]:
    out = []
    for base, source in ((paths.CASES_DIR, "paket"), (UPLOADS, "upload")):
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            files = [p for p in d.iterdir() if p.is_file()]
            spec = next((p for p in files if p.suffix.lower() in {".md", ".txt"} and not p.stem.lower().startswith("readme")), None)
            img = next((p for p in files if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)
            if not spec and not img:
                continue
            title = prepare.parse_spec(spec.read_text(encoding="utf-8"))["title"] if spec else ""
            out.append({"id": d.name, "source": source, "title": title or d.name, "hasSpec": bool(spec),
                        "hasDrawing": bool(img), "hasExpected": (d / "expected.json").exists()})
    return out


def case_dir(case_id: str) -> Path | None:
    for base in (UPLOADS, paths.CASES_DIR):
        d = base / case_id
        if ID_RE.match(case_id) and d.is_dir():
            return d
    hit = product_dirs().get(case_id) if ID_RE.match(case_id or "") else None
    return hit[0] if hit else None


def create_case(body: dict) -> dict:
    name = slug(body.get("name") or "eigener-fall")
    spec, image = (body.get("spec") or "").strip(), body.get("image")
    if not spec and not image:
        raise ValueError("Spezifikation oder Zeichnung nötig")
    cid, k = name, 2
    while (UPLOADS / cid).exists() or (paths.CASES_DIR / cid).exists():
        cid, k = f"{name}-{k}", k + 1
    d = UPLOADS / cid
    d.mkdir(parents=True)
    if spec:
        (d / "spec.md").write_text(spec, encoding="utf-8")
    if image:
        ext = Path(image.get("name") or "x.png").suffix.lower()
        ext = ext if ext in {".png", ".jpg", ".jpeg", ".webp"} else ".png"
        (d / f"exploded_view{ext}").write_bytes(base64.b64decode(image["b64"].split(",")[-1]))
    return {"id": cid}


# ---------------------------------------------------------------- Produkte
# Ein Eintrag je Produkt, egal wie oft es gerechnet wurde: Certivity-Fälle, selbst recherchierte echte Teile,
# eigene Testfälle und Uploads. Gezeigt wird nur das beste Ergebnis (Plattform-F2 > lokaler F2 > Auswahl-F2 > jüngster Lauf).
EXP = REPO / "experiments"
PRODUCT_SOURCES = (  # (Ordner mit Produkt-Unterordnern, Gruppe); frühere gewinnen bei gleichem Namen
    (EXP / "real-parts" / "tune", "recherche"),
    (EXP / "real-parts" / "holdout", "recherche"),
    (EXP / "synthetic", "testfall"),
    (EXP / "selection-suite", "testfall"),
    (EXP / "guard-cases", "testfall"),
)
# In der Demo ausgeblendet (Team-Entscheidung So 25.10.): bleibt im Prüfstand und in allen Kennzahlen (Holdout-F2 0.91 enthält es)
HIDDEN_PRODUCTS = {"tesla-model3-alarm-immobiliser"}
GROUPS = {"certivity": "Certivity-Aufgabe", "recherche": "Echte Teile (recherchiert)", "testfall": "Eigene Testfälle", "upload": "Eigene Uploads"}


def _spec_file(d: Path) -> Path | None:
    return next((p for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() in {".md", ".txt"}
                 and not p.stem.lower().startswith("readme")), None)


def _img_file(d: Path) -> Path | None:
    return next((p for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)


def product_dirs() -> dict[str, tuple[Path, str]]:
    out: dict[str, tuple[Path, str]] = {}
    bases = [(paths.CASES_DIR, "certivity"), *PRODUCT_SOURCES, (UPLOADS, "upload")]
    for base, grp in bases:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name not in out and d.name not in HIDDEN_PRODUCTS and ID_RE.match(d.name) and (_spec_file(d) or _img_file(d)):
                out[d.name] = (d, grp)
    return out


def _f2(hits: int, missing: int, wrong: int) -> float | None:
    if hits + missing + wrong == 0:
        return None
    p = hits / (hits + wrong) if hits + wrong else 0.0
    r = hits / (hits + missing) if hits + missing else 1.0
    return round(5 * p * r / (4 * p + r), 3) if p + r else 0.0


def _gold() -> dict[str, dict]:
    """Musterlösung der Regelungsauswahl je Produkt (sure/unsure/traps, Beleg, Quelle)."""
    gold: dict[str, dict] = {}
    for base, _ in PRODUCT_SOURCES:
        for c, g in ((read_json(base / "expected.json", {}) or {}).get("components") or {}).items():
            gold.setdefault(c, g)
    return gold


def _selections() -> dict[str, dict]:
    """Bestes gespeichertes Auswahl-Ergebnis je Produkt aus den Auswahl-Tests (experiments/runs)."""
    best: dict[str, dict] = {}
    if not EXPERIMENTS.is_dir():
        return best
    for ed in sorted(EXPERIMENTS.iterdir()):
        for f in (ed / "meta.json", ed / "selection-suite.json"):
            data = read_json(f, {}) or {}
            comps = data.get("components") if isinstance(data, dict) else None
            if not isinstance(comps, dict):
                continue
            for c, r in comps.items():
                if not isinstance(r, dict) or "selected" not in r:
                    continue
                f2 = _f2(len(r.get("hits", [])), len(r.get("missing", [])), len(r.get("wrong", [])))
                cand = {**r, "run": ed.name, "f2": f2, "model": data.get("model"), "mode": data.get("mode")}
                cur = best.get(c)
                if cur is None or (f2 or 0) > (cur["f2"] or 0) or ((f2 or 0) == (cur["f2"] or 0) and ed.name > cur["run"]):
                    best[c] = cand
    # Frontstoßfänger-Probelauf (ohne Musterlösung, Auswahl gegen die Schutzfall-Lösung gewertet)
    fb = read_json(EXP / "synthetic" / "front-bumper-run.json", {}) or {}
    if fb.get("auswahl") and "front-bumper" not in best:
        sel = [a["regulation"] for a in fb["auswahl"] if a.get("role") != "rejected"]
        g = _gold().get("front-bumper") or {}
        sure, unsure = set(g.get("sure", [])), set(g.get("unsure", []))
        hits = [r for r in sel if r in sure]
        wrong = [r for r in sel if r not in sure and r not in unsure] if g else []
        missing = sorted(sure - set(sel))
        best["front-bumper"] = {"selected": sel, "hits": hits, "missing": missing, "wrong": wrong, "traps_taken": [],
                                "explain": fb["auswahl"], "run": "front-bumper-run", "f2": _f2(len(hits), len(missing), len(wrong)) if g else None}
    return best


def _run_score(r: dict) -> tuple[int, float, str, str | None]:
    """(Rang, Wert, Anzeige, Quelle) eines fertigen Laufs; höherer Rang gewinnt."""
    ed = EXPERIMENTS / r["id"]
    plat = read_json(ed / "platform.json", {}) if r.get("kind") == "messung" else {}
    f2 = ((plat or {}).get("requirements") or {}).get("f2")
    if f2 is not None:
        return 3, f2, f"{f2:.3f}", "Plattform-F2"
    sc = read_json(ed / "score.json", {}) if r.get("kind") == "messung" else {}
    f2 = (((sc or {}).get("levels") or {}).get("requirement_level") or {}).get("f2")
    if f2 is not None:
        return 2, f2, f"{f2:.3f}", "lokaler F2"
    return 1, 0.0, "", None


def list_products(runs: list[dict] | None = None) -> list[dict]:
    runs = runs if runs is not None else list_runs()
    sels, gold = _selections(), _gold()
    by_case: dict[str, list[dict]] = {}
    for r in runs:
        if r.get("case"):
            by_case.setdefault(r["case"], []).append(r)
    out = []
    for pid, (d, grp) in product_dirs().items():
        sp, img = _spec_file(d), _img_file(d)
        title = prepare.parse_spec(sp.read_text(encoding="utf-8"))["title"] if sp else ""
        item = {"id": pid, "group": grp, "groupLabel": GROUPS[grp], "title": title or pid, "hasDrawing": bool(img),
                "hasGold": pid in gold or (d / "expected.json").exists(), "best": None, "running": None}
        mine = by_case.get(pid, [])
        live = [r for r in mine if r.get("state") == "running"]
        if live:
            item["running"] = {k: live[0].get(k) for k in ("id", "elapsed", "typical", "mode")}
        done = [r for r in mine if r.get("state") == "done" and r.get("n")]
        if done:
            ranked = sorted(done, key=lambda r: (_run_score(r)[:2], r.get("started") or ""), reverse=True)
            top = ranked[0]
            rank, val, txt, src = _run_score(top)
            item["best"] = {"kind": "run", "runId": top["id"], "n": top.get("n"), "regs": top.get("regs"),
                            "score": txt or None, "scoreLabel": src, "started": top.get("started"), "of": len(done)}
        elif pid in sels:
            s = sels[pid]
            item["best"] = {"kind": "auswahl", "runId": s["run"], "regs": len(s["selected"]), "score": f"{s['f2']:.2f}" if s.get("f2") is not None else None,
                            "scoreLabel": "Auswahl-F2" if s.get("f2") is not None else None, "selected": s["selected"]}
        out.append(item)
    order = {"certivity": 0, "upload": 1, "recherche": 2, "testfall": 3}
    out.sort(key=lambda p: (order[p["group"]], p["best"] is None, p["title"].lower()))
    return out


def product_detail(pid: str) -> dict:
    hit = product_dirs().get(pid)
    if not hit:
        raise FileNotFoundError(pid)
    d, grp = hit
    sp = _spec_file(d)
    g = _gold().get(pid)
    s = _selections().get(pid)
    index = load_index()
    title = lambda reg: getattr(index.get(reg), "title", "") if index.get(reg) else ""  # noqa: E731
    sel = []
    if s:
        why = {e.get("regulation"): e for e in s.get("explain") or []}
        for reg in s["selected"]:
            st = "hit" if reg in s.get("hits", []) else "wrong" if reg in s.get("wrong", []) else "ok"
            sel.append({"reg": reg, "title": title(reg), "status": st, "role": (why.get(reg) or {}).get("role"), "reason": (why.get(reg) or {}).get("reason")})
        for reg in s.get("missing", []):
            sel.append({"reg": reg, "title": title(reg), "status": "missing", "role": None, "reason": None})
    return {"id": pid, "group": grp, "groupLabel": GROUPS[grp], "spec": sp.read_text(encoding="utf-8") if sp else "",
            "gold": g, "selection": sel, "selRun": s and s["run"], "selF2": s and s.get("f2"), "selModel": s and s.get("model")}


# ---------------------------------------------------------------- Läufe
def run_dir(run_id: str) -> Path:
    return RUNS / run_id


def start_run(case_id: str, mode: str) -> dict:
    d = case_dir(case_id)
    if not d:
        raise ValueError(f"Fall unbekannt: {case_id}")
    if mode not in MODES:
        raise ValueError(f"Modus unbekannt: {mode}")
    if mode == "best" and not llm_available():
        raise ValueError("Kein LLM-Key (.env.local). Modus 'fast' nutzen oder Key eintragen.")
    rid = f"{datetime.now().strftime('%m%d-%H%M%S')}-{slug(case_id)[:24]}"
    rd = run_dir(rid)
    rd.mkdir(parents=True)
    cmd = [sys.executable, "-m", "certreq", "run", str(d), "--out", str(rd / "submission.json"), *MODES[mode]]
    status = {"id": rid, "case": case_id, "mode": mode, "state": "running", "started": now_iso(), "t0": time.time(),
              "command": " ".join(cmd[1:])}
    write_json(rd / "status.json", status)
    log = open(rd / "run.log", "w", encoding="utf-8")
    p = subprocess.Popen(cmd, cwd=REPO, stdout=log, stderr=subprocess.STDOUT, text=True,
                         env={**os.environ, "PYTHONUNBUFFERED": "1"})
    PROCS[rid] = p

    def wait():
        rc = p.wait()
        log.close()
        st = read_json(rd / "status.json", status)
        st.update(state="done" if rc == 0 and (rd / "submission.json").exists() else "failed", rc=rc,
                  ended=now_iso(), seconds=round(time.time() - st["t0"], 1))
        write_json(rd / "status.json", st)
        PROCS.pop(rid, None)

    threading.Thread(target=wait, daemon=True).start()
    return status


def run_status(run_id: str) -> dict:
    rd = run_dir(run_id)
    st = read_json(rd / "status.json", {}) or {}
    if st.get("state") == "running" and run_id not in PROCS:
        st["state"] = "interrupted"
    log = (rd / "run.log").read_text(encoding="utf-8", errors="replace") if (rd / "run.log").exists() else ""
    st["log"] = log[-4000:]
    if st.get("state") == "running":
        st["elapsed"] = round(time.time() - st.get("t0", time.time()), 1)
        st["typical"] = TYPICAL_SECONDS.get(st.get("mode"), 120)
    return st


def _summary(sub: dict, meta: dict) -> dict:
    reqs = sub.get("requirements", [])
    return {"n": len(reqs), "regs": len({r["source"]["regulation"] for r in reqs}),
            "pages": len({(r["source"]["regulation"], r["source"].get("version"), r["source"]["page"]) for r in reqs}),
            "seconds": meta.get("seconds"), "created": meta.get("created_at") or meta.get("recorded_at"),
            "git": (meta.get("git") or {}).get("commit"), "select": meta.get("select_mode"),
            "extract": meta.get("extract"), "note": meta.get("note")}


def list_runs() -> list[dict]:
    runs = []
    if RUNS.is_dir():
        for rd in RUNS.iterdir():
            st = run_status(rd.name)
            item = {"id": rd.name, "kind": "lauf", "case": st.get("case"), "mode": st.get("mode"),
                    "state": st.get("state"), "started": st.get("started"), "elapsed": st.get("elapsed"),
                    "typical": st.get("typical")}
            if st.get("state") == "done":
                sub = read_json(rd / "submission.json", {})
                item.update(_summary(sub, read_json(rd / "submission.meta.json", {}) or {}))
            runs.append(item)
    if EXPERIMENTS.is_dir():
        for ed in EXPERIMENTS.iterdir():
            sub_p, meta_p = ed / "submission.json.gz", ed / "meta.json"
            if not sub_p.exists():
                continue
            meta = read_json(meta_p, {}) or {}
            sub = read_json(sub_p, {}) or {}
            if not sub.get("requirements"):
                continue
            runs.append({"id": ed.name, "kind": "messung", "case": meta.get("case_id") or sub.get("case_id"),
                         "mode": meta.get("select_mode"), "state": "done", "started": meta.get("created_at"),
                         **_summary(sub, meta)})
    for p in sorted(paths.OUT_DIR.glob("*.meta.json")):
        sub_p = p.with_name(p.name.replace(".meta.json", ".json"))
        sub = read_json(sub_p, {}) or {}
        if not sub.get("requirements"):
            continue
        meta = read_json(p, {}) or {}
        runs.append({"id": f"out-{sub_p.stem}", "kind": "ausgabe", "case": sub.get("case_id"), "state": "done",
                     "mode": meta.get("select_mode"), "started": meta.get("created_at"), **_summary(sub, meta)})
    runs.sort(key=lambda r: r.get("started") or "", reverse=True)
    return runs


def load_run(run_id: str) -> tuple[dict, dict, Path]:
    """(Abgabe, Meta, Review-Datei) eines Laufs, egal welcher Herkunft."""
    if not ID_RE.match(run_id):
        raise ValueError("ungültige Lauf-ID")
    rd = run_dir(run_id)
    if (rd / "submission.json").exists():
        return read_json(rd / "submission.json", {}), read_json(rd / "submission.meta.json", {}) or {}, rd / "review.json"
    ed = EXPERIMENTS / run_id
    if (ed / "submission.json.gz").exists():
        return read_json(ed / "submission.json.gz", {}), read_json(ed / "meta.json", {}) or {}, REVIEWS / f"{run_id}.json"
    if run_id.startswith("out-"):
        sub_p = paths.OUT_DIR / f"{run_id[4:]}.json"
        if sub_p.exists():
            return read_json(sub_p, {}), read_json(sub_p.with_suffix(".meta.json"), {}) or {}, REVIEWS / f"{run_id}.json"
    raise FileNotFoundError(run_id)


def run_payload(run_id: str) -> dict:
    sub, meta, review_p = load_run(run_id)
    key = run_id
    stamp = json.dumps([len(sub.get("requirements", [])), meta.get("created_at"), meta.get("recorded_at")])
    hit = _payload_cache.get(key)
    if hit and hit[0] == stamp:
        payload = hit[1]
    else:
        case_id = sub.get("case_id") or meta.get("case_id") or ""
        cdir = case_dir(case_id)
        spec, spec_text, drawing = prepare.parse_spec(""), "", None
        if cdir:
            sp = next((p for p in sorted(cdir.iterdir()) if p.suffix.lower() in {".md", ".txt"} and not p.stem.lower().startswith("readme")), None)
            if sp:
                spec_text = sp.read_text(encoding="utf-8")
                spec = prepare.parse_spec(spec_text)
            img = next((p for p in sorted(cdir.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None)
            if img:
                pm = pymupdf.Pixmap(str(img))
                drawing = {"src": f"/api/drawing?case={quote(case_id)}", "w": pm.width, "h": pm.height}
        index = load_index()
        titles = {n: r.title for n, r in index.items()}
        parts = [{"id": f"p{i + 1}", "n": i + 1, "name": n} for i, n in enumerate(spec["parts"])]
        match = prepare.make_matcher(parts, titles)
        reqs = []
        for i, r in enumerate(sub.get("requirements", [])):
            s = r.get("source", {})
            reqs.append({"id": r.get("id") or f"R-{i + 1:04d}", "text": r.get("text", ""), "reg": s.get("regulation", ""),
                         "version": s.get("version", ""), "page": s.get("page", 0), "para": s.get("paragraph", ""),
                         "part": match(r.get("text", ""), s.get("regulation", ""))})
        counts = Counter(r["reg"] for r in reqs)
        versions = {r["reg"]: r["version"] for r in reqs}
        selected = set(meta.get("selected") or counts)
        regs = [{"id": n, "title": t, "selected": n in selected or n in counts, "count": counts.get(n, 0),
                 "version": versions.get(n, "")} for n, t in titles.items()]
        updates = []
        for n, c in counts.items():
            reg = index.get(n)
            new = reg.version("latest") if reg else None
            if new and new.label != versions.get(n) and pdf_for(n, versions.get(n, "")) and pdf_for(n, new.label):
                updates.append({"reg": n, "from": versions.get(n, ""), "to": new.label, "n": c})
        payload = {
            "version": 1, "runId": run_id, "updates": updates,
            "case": {"id": case_id, "title": spec["title"] or case_id, "productType": spec["productType"],
                     "category": spec["category"], "functions": spec["functions"], "parts": parts,
                     "hasSpec": bool(spec_text), "spec": spec_text, "drawing": drawing,
                     "hasExpected": bool(cdir and (cdir / "expected.json").exists())},
            "run": {"seconds": meta.get("seconds"), "git": (meta.get("git") or {}).get("commit"),
                    "created": meta.get("created_at"), "team": sub.get("team_id", ""), "command": meta.get("command"),
                    "selection": meta.get("selection") or [], "drawingNote": meta.get("drawing"),
                    "select": meta.get("select_mode"), "filters": meta.get("filters"), "extract": meta.get("extract"),
                    "llm": meta.get("llm")},
            "regs": regs, "reqs": reqs,
            "pagesTotal": len({(r["reg"], r["version"], r["page"]) for r in reqs}),
        }
        _payload_cache[key] = (stamp, payload)
    out = dict(payload)
    out["review"] = read_json(review_p, {}) or {}
    return out


def page_info(reg: str, ver: str, page: int) -> dict | None:
    pdf = pdf_for(reg, ver)
    if not pdf:
        return None
    d = doc(pdf)
    if not 1 <= page <= d.page_count:
        return None
    r = d[page - 1].rect
    return {"src": f"/api/page?reg={quote(reg)}&ver={quote(ver)}&page={page}", "w": round(r.width), "h": round(r.height),
            "of": d.page_count, "pdf": f"/api/pdf?reg={quote(reg)}&ver={quote(ver)}#page={page}"}


def page_jpeg(reg: str, ver: str, page: int) -> bytes | None:
    PAGE_CACHE.mkdir(parents=True, exist_ok=True)
    f = PAGE_CACHE / f"{slug(reg)}_{slug(ver)}_{page}.jpg"
    if f.exists():
        return f.read_bytes()
    pdf = pdf_for(reg, ver)
    if not pdf:
        return None
    d = doc(pdf)
    if not 1 <= page <= d.page_count:
        return None
    with LOCK:
        pix = d[page - 1].get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
        data = pix.tobytes("jpeg", jpg_quality=70)
    f.write_bytes(data)
    return data


def page_hits(run_id: str, reg: str, ver: str, page: int) -> dict:
    payload = run_payload(run_id)
    info = page_info(reg, ver, page) or {}
    pdf = pdf_for(reg, ver)
    hits = {}
    if pdf:
        d = doc(pdf)
        if 1 <= page <= d.page_count:
            with LOCK:
                pg = d[page - 1]
                cache: dict = {}
                for r in payload["reqs"]:
                    if r["reg"] == reg and r["version"] == ver and r["page"] == page:
                        ln = prepare.find_lines(pg, r["para"], r["text"], cache)
                        if ln:
                            hits[r["id"]] = ln
    return {**info, "hits": hits}


def presentation_js(run_id: str, max_pages: int = 120) -> str:
    p = dict(run_payload(run_id))
    by: Counter = Counter((r["reg"], r["version"], r["page"]) for r in p["reqs"])
    pages, hits = {}, {}
    for (reg, ver, pno), _ in by.most_common(max_pages):
        h = page_hits(run_id, reg, ver, pno)
        if h.get("src"):
            pages[f"{reg}#{ver}#{pno}"] = {k: h[k] for k in ("src", "w", "h", "of")}
            hits.update(h["hits"])
    p.update(pages=pages, hits=hits)
    p.pop("review", None)
    return "window.CERTREQ = " + json.dumps(p, ensure_ascii=False) + ";\n"


def save_review(run_id: str, body: dict) -> dict:
    _, _, review_p = load_run(run_id)
    rev = read_json(review_p, {}) or {}
    ids = body.get("ids") or [body.get("id")]
    for rid in ids:
        if not rid:
            continue
        cur = rev.get(rid, {})
        if "status" in body:
            cur["status"] = body["status"]
        if "note" in body:
            cur["note"] = body["note"]
        cur["at"] = now_iso()
        if cur.get("status") in (None, "open") and not cur.get("note"):
            rev.pop(rid, None)
        else:
            rev[rid] = cur
    write_json(review_p, rev)
    return rev


def export(run_id: str, fmt: str) -> tuple[bytes, str, str]:
    sub, _, review_p = load_run(run_id)
    rev = read_json(review_p, {}) or {}
    reqs = [r for r in sub.get("requirements", []) if rev.get(r.get("id"), {}).get("status") != "rejected"]
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "regulation", "version", "page", "paragraph", "status", "note", "text"])
        for r in reqs:
            s, rv = r.get("source", {}), rev.get(r.get("id"), {})
            w.writerow([r.get("id"), s.get("regulation"), s.get("version"), s.get("page"), s.get("paragraph"),
                        rv.get("status", "open"), rv.get("note", ""), r.get("text")])
        return buf.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8", f"{run_id}.csv"
    out = {**{k: v for k, v in sub.items() if k != "requirements"}, "requirements": reqs}
    return json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8"), "application/json", f"{run_id}.json"


# ---------------------------------------------------------------- Sub-Goal
def list_subgoals() -> list[dict]:
    out = []
    if SUBGOAL_DIR.is_dir():
        for d in sorted(SUBGOAL_DIR.iterdir()):
            if (d / "old.pdf").exists() and (d / "new.pdf").exists() and (d / "requirements_old.json").exists():
                out.append({"id": d.name, "hasExpected": (d / "expected.json").exists(),
                            "done": (SUBGOAL_OUT / f"{d.name}.json").exists()})
    return out


def run_subgoal(folder: str, force: bool = False) -> dict:
    from certreq import subgoal
    d = SUBGOAL_DIR / folder
    if not ID_RE.match(folder) or not d.is_dir():
        raise ValueError("Sub-Goal-Ordner unbekannt")
    cache = SUBGOAL_OUT / f"{folder}.json"
    t0 = time.time()
    stamp = Path(subgoal.__file__).stat().st_mtime  # neue Verfahrensversion → neu rechnen
    res = None if force else read_json(cache)
    if not res or res.get("stamp") != stamp:
        reqs = json.loads((d / "requirements_old.json").read_text(encoding="utf-8"))
        from certreq.submission import TEAM_ID
        sub = subgoal.compare(d / "old.pdf", d / "new.pdf", reqs, os.environ.get("CERTIVITY_TEAM_ID", TEAM_ID),
                              f"subgoal-{folder}", refine="llm" if llm_available() else "none")
        reg_new, ver_new = subgoal.pdf_header(d / "new.pdf")
        reg_old, ver_old = subgoal.pdf_header(d / "old.pdf")
        res = {"submission": sub, "regulation": reg_new or reg_old, "old": ver_old, "new": ver_new,
               "requirements": reqs, "seconds": round(time.time() - t0, 1), "created": now_iso(), "stamp": stamp}
        exp = read_json(d / "expected.json")
        if exp:
            res["eval"] = subgoal.evaluate(sub, exp)
        write_json(cache, res)
    return res


def run_impact(run_id: str, reg: str, force: bool = False) -> dict:
    """Welche Anforderungen dieses Laufs ändert die neuere Fassung einer zitierten Regelung? (Sub-Goal auf eigenen Daten)"""
    from certreq import subgoal
    sub, meta, _ = load_run(run_id)
    reqs = [r for r in sub.get("requirements", []) if r.get("source", {}).get("regulation") == reg]
    if not reqs:
        raise ValueError(f"{reg} kommt in {run_id} nicht vor")
    old_v = reqs[0]["source"].get("version", "")
    entry = load_index().get(reg)
    new = entry.version("latest") if entry else None
    old_pdf, new_pdf = pdf_for(reg, old_v), (pdf_for(reg, new.label) if new else None)
    if not (old_pdf and new_pdf) or new.label == old_v:
        raise ValueError(f"Keine neuere Fassung von {reg} im Paket")
    cache = SUBGOAL_OUT / f"impact-{slug(run_id)}-{slug(reg)}.json"
    stamp = [len(reqs), meta.get("created_at"), Path(subgoal.__file__).stat().st_mtime]
    res = None if force else read_json(cache)
    if not res or res.get("stamp") != stamp:
        t0 = time.time()
        from certreq.submission import TEAM_ID
        out = subgoal.compare(old_pdf, new_pdf, reqs, os.environ.get("CERTIVITY_TEAM_ID", TEAM_ID), f"impact-{run_id}")
        res = {"submission": out, "regulation": reg, "old": old_v, "new": new.label, "requirements": reqs, "run": run_id,
               "seconds": round(time.time() - t0, 1), "created": now_iso(), "stamp": stamp}
        write_json(cache, res)
    return res


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "barelylegal-werkbank"

    def log_message(self, fmt, *args):  # ruhig, nur Fehler
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if ctype.startswith(("application/json", "text/html", "application/javascript")) else "max-age=3600")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, code: int = 200):
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _err(self, code: int, msg: str):
        self._json({"error": msg}, code)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 40_000_000:
            raise ValueError("zu groß")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            self._route_get(u.path, q)
        except FileNotFoundError as e:
            self._err(404, f"nicht gefunden: {e}")
        except ValueError as e:
            self._err(400, str(e))
        except Exception as e:  # noqa: BLE001 – Server soll weiterlaufen
            self._err(500, f"{type(e).__name__}: {e}")

    def _route_get(self, path: str, q: dict):
        if path in ("/", "/index.html"):
            f = WEB / "werkbank.html"
            return self._send(200, f.read_bytes(), "text/html; charset=utf-8") if f.exists() else self._err(404, "demo/web/werkbank.html fehlt")
        m = re.match(r"^/present/([^/]+)/(index\.html|data\.js)?$", path)
        if m:
            rid = m.group(1)
            if m.group(2) == "data.js":
                return self._send(200, presentation_js(rid).encode("utf-8"), "application/javascript; charset=utf-8")
            return self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            runs = list_runs()
            return self._json({"cases": list_cases(), "runs": runs, "products": list_products(runs), "subgoals": list_subgoals(),
                               "llm": llm_available(), "modes": list(MODES), "typical": TYPICAL_SECONDS})
        if path == "/api/run":
            return self._json(run_payload(q["id"]))
        if path == "/api/product":
            return self._json(product_detail(q["id"]))
        if path == "/api/status":
            return self._json(run_status(q["id"]))
        if path == "/api/hits":
            return self._json(page_hits(q["run"], q["reg"], q["ver"], int(q["page"])))
        if path == "/api/page":
            data = page_jpeg(q["reg"], q["ver"], int(q["page"]))
            return self._send(200, data, "image/jpeg") if data else self._err(404, "Seite nicht verfügbar")
        if path == "/api/pdf":
            pdf = pdf_for(q["reg"], q["ver"])
            return self._send(200, pdf.read_bytes(), "application/pdf") if pdf else self._err(404, "PDF fehlt")
        if path == "/api/drawing":
            d = case_dir(q["case"])
            img = next((p for p in sorted(d.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}), None) if d else None
            if not img:
                return self._err(404, "keine Zeichnung")
            ctype = "image/png" if img.suffix.lower() == ".png" else "image/jpeg"
            return self._send(200, img.read_bytes(), ctype)
        if path == "/api/export":
            body, ctype, name = export(q["run"], q.get("fmt", "json"))
            return self._send(200, body, ctype, {"Content-Disposition": f'attachment; filename="{name}"'})
        if path == "/api/subgoal":
            return self._json(run_subgoal(q["id"]))
        if path == "/api/impact":
            return self._json(run_impact(q["run"], q["reg"]))
        self._err(404, "unbekannt")

    def do_POST(self):
        u = urlparse(self.path)
        try:
            body = self._body()
            if u.path == "/api/cases":
                return self._json(create_case(body))
            if u.path == "/api/runs":
                return self._json(start_run(body["case"], body.get("mode", "best")))
            if u.path == "/api/review":
                return self._json(save_review(body["run"], body))
            if u.path == "/api/subgoal":
                return self._json(run_subgoal(body["id"], force=bool(body.get("force"))))
            if u.path == "/api/impact":
                return self._json(run_impact(body["run"], body["reg"], force=bool(body.get("force"))))
            self._err(404, "unbekannt")
        except (ValueError, KeyError) as e:
            self._err(400, str(e))
        except FileNotFoundError as e:
            self._err(404, f"nicht gefunden: {e}")
        except Exception as e:  # noqa: BLE001
            self._err(500, f"{type(e).__name__}: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    paths.require_package()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    url = f"http://{a.host}:{a.port}/"
    print(f"BarelyLegal Werkbank läuft: {url}  (Strg+C beendet)")
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
