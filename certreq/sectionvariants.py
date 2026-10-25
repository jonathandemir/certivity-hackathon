"""Upload-Varianten auf Abschnittsebene: Anforderungen einzelner Abschnitte einer Regelung weglassen, ohne LLM-Lauf.

    .venv/bin/python -m certreq.sectionvariants H001 --list "UN R48"                       # Anforderungen je Abschnitt
    .venv/bin/python -m certreq.sectionvariants H001 --drop "UN R48=Front fog lamp" --as H001-noFog
    .venv/bin/python -m certreq.upload H001-noFog                                           # Upload-Datei + Validierung
    .venv/bin/python -m certreq.sectionvariants H001 --add "H003=UN GTR 9" --as H001-plusGTR9  # Regelung aus anderem Lauf

Ergänzt certreq.variants (ganze Regelungen) um eine Ebene darunter. Ein Abschnitt ist eine Überschrift im
Gliederungspfad des zitierten Absatzes (certreq.pdf: headings + eigener Titel), z. B. R48 „Individual specifications >
Front fog lamp“. `--drop "REG=Titel"` entfernt jede Anforderung von REG, deren Pfad eine Überschrift enthält, die mit
Titel beginnt (Groß/klein egal); mehrfach angebbar. Die übrigen Anforderungen bleiben byte-gleich, ein Upload-Paar misst
also genau diese Entscheidung.

Anlass (Held-out 25.10.): H001 hat 432 von 648 Anforderungen aus R48/R148, die Spec nennt nur „(Side) Lighting —
signalling“ und „Lighting — decorative“; ganze R48-Abschnitte für nicht genannte Leuchten (Nebel, Tagfahr, Park,
Abbiege …) sind drin. Nach F2 = 5·TP/(4·Gold + Abgabe) lohnt Weglassen nur bei sehr sicher falschen Abschnitten,
also nur per Plattform-Paar entscheiden, nicht raten. Umgekehrt lohnt Hinzufügen schon, wenn eine Anforderung mit mehr
als ~F2/5 trifft: `--add "LAUF=REGELUNG"` übernimmt alle Anforderungen dieser Regelung aus einem anderen abgelegten Lauf
(neue IDs, Regelung darf in der Basis noch nicht vorkommen).
"""
from __future__ import annotations

import argparse
from collections import Counter

from .pdf import parse_pdf
from .regindex import load_index
from .upload import RUNS, load_run
from .variants import save_variant


def _paths(regulation: str) -> dict[str, tuple[str, ...]]:
    """Absatzlabel → Gliederungspfad (Überschriften außen zuerst, eigener Titel zuletzt) der base-Version."""
    reg = load_index()[regulation]
    out: dict[str, tuple[str, ...]] = {}
    for pdf in reg.base.pdfs:
        for p in parse_pdf(pdf):
            out.setdefault(p.label, p.headings + ((p.title,) if p.title else ()))
    return out


def sections(sub: dict, regulation: str, depth: int = 2) -> Counter:
    paths = _paths(regulation)
    c: Counter = Counter()
    for r in sub["requirements"]:
        if r["source"]["regulation"] == regulation:
            c[" > ".join(paths.get(r["source"].get("paragraph") or "", ("?",))[:depth]) or "-"] += 1
    return c


def parse_drop(specs: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in specs:
        reg, sep, title = s.partition("=")
        if not sep or not reg.strip() or not title.strip():
            raise SystemExit(f'--drop erwartet "REGELUNG=Abschnittstitel", nicht {s!r}')
        out.setdefault(reg.strip(), []).append(title.strip().lower())
    return out


def drop_sections(sub: dict, drop: dict[str, list[str]], paths_of=_paths) -> tuple[dict, Counter]:
    """Neue Abgabe ohne Anforderungen, deren Gliederungspfad eine der Überschriften enthält; zählt Entferntes je Regel."""
    present = {r["source"]["regulation"] for r in sub["requirements"]}
    unknown = [reg for reg in drop if reg not in present]
    if unknown:
        raise SystemExit(f"Nicht in der Abgabe: {unknown}. Vorhanden: {sorted(present)}")
    paths = {reg: paths_of(reg) for reg in drop}
    removed: Counter = Counter()
    kept = []
    for r in sub["requirements"]:
        reg = r["source"]["regulation"]
        titles = drop.get(reg)
        path = paths[reg].get(r["source"].get("paragraph") or "", ()) if titles else ()
        hit = next((t for t in titles or () if any(h.lower().startswith(t) for h in path)), None)
        if hit:
            removed[f"{reg}={hit}"] += 1
        else:
            kept.append(r)
    for reg, titles in drop.items():
        for t in titles:
            if not removed[f"{reg}={t}"]:
                raise SystemExit(f"Kein Abschnitt '{t}' mit Anforderungen in {reg} (Tippfehler? --list zeigt die Titel)")
    if not kept:
        raise SystemExit("Die Variante hätte keine Anforderung mehr.")
    return {**sub, "requirements": kept}, removed


def add_regulations(sub: dict, specs: list[str], load=load_run) -> tuple[dict, list[str]]:
    """Anforderungen ganzer Regelungen aus anderen Läufen anhängen ("H003=UN GTR 9"), mit fortlaufenden neuen IDs."""
    present = {r["source"]["regulation"] for r in sub["requirements"]}
    reqs, added = list(sub["requirements"]), []
    ids = {r["id"] for r in reqs}
    for spec in specs:
        run, sep, reg = spec.partition("=")
        if not sep or not run.strip() or not reg.strip():
            raise SystemExit(f'--add erwartet "LAUF=REGELUNG", nicht {spec!r}')
        reg = reg.strip()
        if reg in present:
            raise SystemExit(f"{reg} ist schon in der Basis; erst mit certreq.variants --drop entfernen")
        extra = [r for r in load(run.strip())["requirements"] if r["source"]["regulation"] == reg]
        if not extra:
            raise SystemExit(f"{reg} hat in {run} keine Anforderungen")
        for r in extra:
            n = len(reqs) + 1
            while f"R-{n:04d}" in ids:
                n += 1
            ids.add(f"R-{n:04d}")
            reqs.append({**r, "id": f"R-{n:04d}"})
        present.add(reg)
        added.append(f"+{reg} aus {run.strip()} ({len(extra)})")
    return {**sub, "requirements": reqs}, added


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.sectionvariants", description=__doc__.splitlines()[0])
    ap.add_argument("run_id", help="abgelegter Lauf unter experiments/runs/, z. B. H001")
    ap.add_argument("--list", metavar="REGELUNG", help="Anforderungen je Abschnitt dieser Regelung zeigen")
    ap.add_argument("--depth", type=int, default=2, help="Tiefe des Gliederungspfads für --list (Standard 2)")
    ap.add_argument("--drop", action="append", default=[], metavar="REG=Titel", help="Abschnitt weglassen (mehrfach)")
    ap.add_argument("--add", action="append", default=[], metavar="LAUF=REG", help="Regelung aus anderem Lauf anhängen (mehrfach)")
    ap.add_argument("--as", dest="new_id", help="ID der Variante unter experiments/runs/")
    args = ap.parse_args(argv)
    sub = load_run(args.run_id)
    if args.list:
        for k, v in sections(sub, args.list, args.depth).most_common():
            print(f"{v:4d}  {k}")
        return 0
    if not (args.drop or args.add) or not args.new_id:
        raise SystemExit("--drop und/oder --add sowie --as angeben (oder --list)")
    new, removed = drop_sections(sub, parse_drop(args.drop)) if args.drop else (sub, {})
    new, added = add_regulations(new, args.add) if args.add else (new, [])
    dest = save_variant(args.run_id, args.new_id, new, [f"{k} ({v})" for k, v in removed.items()] + added, runs=RUNS)
    print(f"{dest}: {len(new['requirements'])} Anforderungen (vorher {len(sub['requirements'])}), entfernt {dict(removed)}, {added}")
    print(f"Weiter: .venv/bin/python -m certreq.upload {args.new_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
