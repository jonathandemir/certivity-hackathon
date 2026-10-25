"""Upload-Varianten auf Abschnittsebene: Anforderungen einzelner Abschnitte einer Regelung weglassen, ohne LLM-Lauf.

    .venv/bin/python -m certreq.sectionvariants H001 --list "UN R48"                       # Anforderungen je Abschnitt
    .venv/bin/python -m certreq.sectionvariants H001 --drop "UN R48=Front fog lamp" --as H001-noFog
    .venv/bin/python -m certreq.upload H001-noFog                                           # Upload-Datei + Validierung
    .venv/bin/python -m certreq.sectionvariants H001 --add "H003=UN GTR 9" --as H001-plusGTR9  # Regelung aus anderem Lauf
    .venv/bin/python -m certreq.sectionvariants BEST --zero-yield E024-hs-c,E033-hs-c --as BEST-zy   # Dev-Nullabschnitte raus
    .venv/bin/python -m certreq.sectionvariants BEST --drop-pages "UN R48=40-45,80" --as BEST-noP    # ganze Seiten raus
    .venv/bin/python -m certreq.sectionvariants BEST --zero-yield E024-hs-c,… --depth 0 --min-count 4 --as BEST-P  # Absätze

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

`--drop-pages "REG=40-45,80"` entfernt alle Anforderungen, die diese Seiten zitieren. Der Seiten-Score der Plattform ist
eine Mengenrechnung (Precision = Gold-Seiten / eingereichte Seiten, Recall = Gold-Seiten / alle Gold-Seiten): aus einem
Upload-Paar folgt exakt, wie viele der weggelassenen Seiten im Gold stehen. Seiten ohne Gold-Absatz tragen praktisch
keine Anforderungs-Treffer.

`--zero-yield … --depth 0` arbeitet auf Absatzebene (Regelung, Absatzlabel) statt auf Abschnitten. Leave-one-out auf dev
(6 Claude-Läufe, je 5 lernen, 1 prüfen, ≥ 4 Ausgaben, 0 Treffer): je Lauf ≈ 148 Anforderungen weg, 0.5 Treffer verloren.
"""
from __future__ import annotations

import argparse
import re
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


def parse_pages(specs: list[str]) -> dict[str, set[int]]:
    """["UN R48=40-45,80"] → {"UN R48": {40, …, 45, 80}}"""
    out: dict[str, set[int]] = {}
    for s in specs:
        reg, sep, spec = s.partition("=")
        if not sep or not reg.strip() or not re.fullmatch(r"\s*\d+(\s*-\s*\d+)?(\s*,\s*\d+(\s*-\s*\d+)?)*\s*", spec):
            raise SystemExit(f'--drop-pages erwartet "REGELUNG=40-45,80", nicht {s!r}')
        pages = out.setdefault(reg.strip(), set())
        for part in spec.split(","):
            a, _, b = part.partition("-")
            pages.update(range(int(a), int(b or a) + 1))
    return out


def drop_pages(sub: dict, pages: dict[str, set[int]]) -> tuple[dict, Counter]:
    """Neue Abgabe ohne Anforderungen auf diesen Seiten; zählt Entferntes je (Regelung, Seite). Fehlt eine Seite, Abbruch."""
    removed: Counter = Counter()
    kept = []
    for r in sub["requirements"]:
        reg, page = r["source"]["regulation"], r["source"]["page"]
        if page in pages.get(reg, ()):
            removed[f"{reg} S.{page}"] += 1
        else:
            kept.append(r)
    missing = [f"{reg} S.{p}" for reg, ps in pages.items() for p in sorted(ps) if not removed[f"{reg} S.{p}"]]
    if missing:
        raise SystemExit(f"Keine Anforderung auf {missing} (Tippfehler? Bereich zu groß?)")
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


def _zy_key(r: dict, depth: int, paths_of) -> tuple:
    """Schlüssel für --zero-yield: (Regelung, Gliederungspfad bis depth); depth 0 = (Regelung, Absatzlabel)."""
    reg, label = r["source"]["regulation"], r["source"].get("paragraph") or ""
    return (reg, ("¶", label)) if depth == 0 else (reg, paths_of(reg).get(label, ())[:depth])


def zero_yield_sections(dev_runs: list[str], regs: set[str], min_count: int = 6, depth: int = 2, paths_of=_paths,
                        load=load_run) -> set[tuple[str, tuple[str, ...]]]:
    """Abschnitte (Regelung, Pfad bis depth), die in den bewerteten Dev-Läufen mindestens min_count Ausgaben, aber keinen
    einzigen Treffer hatten (experiments/runs/<ID>/score.json judge.matches). Nach F2 = 5·TP/(4·Gold+Abgabe) kostet jede
    Anforderung mit Trefferchance unter ~F2/5 Punkte; Trefferchance 0 aus 6+ Ausgaben ist der klarste Fall."""
    import json
    cnt: Counter = Counter()
    hit: Counter = Counter()
    for rid in dev_runs:
        score = json.loads((RUNS / rid / "score.json").read_text(encoding="utf-8"))
        matched = {ours for _, ours in score["judge"]["matches"]}
        for r in load(rid)["requirements"]:
            reg = r["source"]["regulation"]
            if reg not in regs:
                continue
            key = _zy_key(r, depth, paths_of)
            cnt[key] += 1
            hit[key] += r["id"] in matched
    reg_hits = Counter()
    for (reg, _), h in hit.items():
        reg_hits[reg] += h
    # Nur Regelungen, die auf dev Treffer haben: ohne Treffer ist die Regelung dort nicht im Gold (z. B. R26 auf dev),
    # dann sagt ein Nullabschnitt nichts über den Abschnitt.
    return {k for k, n in cnt.items() if n >= min_count and hit[k] == 0 and reg_hits[k[0]] > 0}


def drop_zero_yield(sub: dict, zero: set, depth: int = 2, paths_of=_paths) -> tuple[dict, Counter]:
    regs = {reg for reg, _ in zero}
    paths = {reg: paths_of(reg) for reg in regs} if depth else {}
    removed: Counter = Counter()
    kept = []
    for r in sub["requirements"]:
        reg = r["source"]["regulation"]
        key = _zy_key(r, depth, paths.get) if reg in regs else None
        if key in zero:
            removed[f"{reg}={' > '.join(key[1])[:70]}"] += 1
        else:
            kept.append(r)
    return {**sub, "requirements": kept}, removed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m certreq.sectionvariants", description=__doc__.splitlines()[0])
    ap.add_argument("run_id", help="abgelegter Lauf unter experiments/runs/, z. B. H001")
    ap.add_argument("--list", metavar="REGELUNG", help="Anforderungen je Abschnitt dieser Regelung zeigen")
    ap.add_argument("--depth", type=int, default=2, help="Tiefe des Gliederungspfads für --list/--zero-yield (Standard 2; 0 = je Absatz)")
    ap.add_argument("--drop", action="append", default=[], metavar="REG=Titel", help="Abschnitt weglassen (mehrfach)")
    ap.add_argument("--drop-pages", action="append", default=[], metavar="REG=40-45,80",
                    help="alle Anforderungen auf diesen Seiten weglassen (mehrfach)")
    ap.add_argument("--add", action="append", default=[], metavar="LAUF=REG", help="Regelung aus anderem Lauf anhängen (mehrfach)")
    ap.add_argument("--zero-yield", metavar="DEV1,DEV2", help="Abschnitte ohne Treffer in diesen bewerteten Dev-Läufen weglassen")
    ap.add_argument("--min-count", type=int, default=6, help="Mindestzahl Dev-Ausgaben je Abschnitt für --zero-yield (Standard 6)")
    ap.add_argument("--as", dest="new_id", help="ID der Variante unter experiments/runs/")
    args = ap.parse_args(argv)
    sub = load_run(args.run_id)
    if args.list:
        for k, v in sections(sub, args.list, args.depth).most_common():
            print(f"{v:4d}  {k}")
        return 0
    if not (args.drop or args.drop_pages or args.add or args.zero_yield) or not args.new_id:
        raise SystemExit("--drop, --drop-pages, --add oder --zero-yield sowie --as angeben (oder --list)")
    new, removed = drop_sections(sub, parse_drop(args.drop)) if args.drop else (sub, Counter())
    if args.drop_pages:
        new, pr = drop_pages(new, parse_pages(args.drop_pages))
        removed = Counter(removed) + pr
    if args.zero_yield:
        regs = {r["source"]["regulation"] for r in new["requirements"]}
        zero = zero_yield_sections([x.strip() for x in args.zero_yield.split(",") if x.strip()], regs, args.min_count, args.depth)
        new, zr = drop_zero_yield(new, zero, args.depth)
        removed = Counter(removed) + zr
    new, added = add_regulations(new, args.add) if args.add else (new, [])
    dest = save_variant(args.run_id, args.new_id, new, [f"{k} ({v})" for k, v in removed.items()] + added, runs=RUNS)
    print(f"{dest}: {len(new['requirements'])} Anforderungen (vorher {len(sub['requirements'])}), entfernt {dict(removed)}, {added}")
    print(f"Weiter: .venv/bin/python -m certreq.upload {args.new_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
