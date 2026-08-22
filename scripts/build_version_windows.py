#!/usr/bin/env python
"""Which library versions a checkpoint is KNOWN to work and fail under. Points, not ranges.

    python scripts/build_version_windows.py
    python scripts/build_version_windows.py --write   -> roster/models/version_windows.json
    python scripts/build_version_windows.py --holes   only the models with a hole

## A RANGE IS A CLAIM. A POINT IS AN OBSERVATION.

`requirements.json` carries `transformers: ">=4.57,<5"` -- a BOUND, and a bound
cannot express what Falcon-H1 does:

    4.57.1   loads, and accepts use_cache
    5.4.0    LOAD FAILED
    5.14.1   loads, and uses the mamba kernels

That is **a hole, not a floor or a ceiling**, and no specifier in PEP 440 says
it. The fact was established, written in a chatlog, and dropped, because the
schema had nowhere to put it. Storing the POINTS instead makes the hole simply
what the rows say, and the bound becomes DERIVED -- which is the right
direction, and the same distinction that governs the whole record: cells are
existential, requirements are modal, and you may only go from the first to the
second, never back.

## EVERY POINT IS EVIDENCED, AND ABSENCE IS NOT A POINT

Two sources, both already in the repo:

    observations.json   an outcome, plus the environment it happened in. Only
                        environments that declare `transformers`/`torch` as
                        FIELDS can contribute -- prose cannot be read as a
                        version, and guessing one would manufacture evidence.
    twp cells           successes at an exactly recorded version, via the
                        `*_tf*` environments record_successes derives.

A version nobody has tried yields NO row. It is not a failure and not a pass,
and the gap between two tested points is exactly as unknown as it looks.
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

OBS = os.path.join(ROOT, "roster", "models", "observations.json")
OUT = os.path.join(ROOT, "roster", "models", "version_windows.json")
SOURCES = ["roster/models/observations.json"]

WORKS = {"loads", "load_ok", "ok", "runs", "run_ok"}
FAILS = {"load_failed", "run_failed"}


def _key(v):
    """Sortable version key; unparseable versions sort last rather than raise."""
    try:
        from packaging.version import Version
        return (0, Version(v))
    except Exception:                                            # noqa: BLE001
        return (1, v)


def build():
    doc = json.load(open(OBS))
    envs = doc.get("environments") or {}
    out = {}
    for o in doc["observations"]:
        e = envs.get(o["environment"])
        if not isinstance(e, dict):
            continue
        outcome = o["outcome"]
        if outcome in WORKS:
            verdict = "works"
        elif outcome in FAILS:
            verdict = "fails"
        else:
            continue
        for pkg in ("transformers", "torch"):
            ver = e.get(pkg)
            if not ver:
                #: **A NULL IS UNKNOWN, NOT A VERSION.** The `*_unversioned`
                #: environments carry None on purpose; taking them as a point
                #: would attach an outcome to a toolchain nobody recorded.
                continue
            rec = out.setdefault(o["model_id"], {}).setdefault(pkg, OrderedDict())
            slot = rec.setdefault(str(ver), OrderedDict([
                ("version", str(ver)), ("verdicts", OrderedDict()),
            ]))
            slot["verdicts"].setdefault(verdict, []).append(OrderedDict([
                ("environment", o["environment"]),
                ("outcome", outcome),
                ("cause", (o.get("cause") or "")[:180] or None),
            ]))
    #: Sort by version and mark holes.
    rows = OrderedDict()
    for m in sorted(out):
        entry = OrderedDict()
        for pkg in sorted(out[m]):
            pts = sorted(out[m][pkg].values(), key=lambda s: _key(s["version"]))
            for p in pts:
                v = p["verdicts"]
                p["verdict"] = ("mixed" if len(v) > 1
                                else next(iter(v)))
            entry[pkg] = OrderedDict([("points", pts), ("hole", _hole(pts))])
        rows[m] = entry
    return rows


def _hole(points):
    """True when a FAILING version sits between two that WORK.

    Only `works` and `fails` count. A `mixed` point -- the same version both
    working and failing -- is a repair-in-place (AmberSafe loaded after two
    packages went in), not a hole, and treating it as one would invent a
    version bound out of a packaging fix.
    """
    seq = [p["verdict"] for p in points]
    if "fails" not in seq:
        return False
    first_ok = next((i for i, s in enumerate(seq) if s == "works"), None)
    last_ok = next((len(seq) - 1 - i for i, s in enumerate(reversed(seq))
                    if s == "works"), None)
    if first_ok is None or last_ok is None or last_ok <= first_ok:
        return False
    return any(s == "fails" for s in seq[first_ok + 1:last_ok])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--holes", action="store_true")
    a = ap.parse_args()
    rows = build()
    holes = {m: e for m, e in rows.items()
             if any(v.get("hole") for v in e.values())}
    npts = sum(len(v["points"]) for e in rows.values() for v in e.values())
    print("models with at least one version point: %d  (%d points)"
          % (len(rows), npts))
    print("models with a HOLE (a failing version between two working ones): %d"
          % len(holes))
    show = holes if a.holes else rows
    for m, e in sorted(show.items()):
        for pkg, v in e.items():
            if a.holes and not v.get("hole"):
                continue
            line = "  ".join("%s=%s" % (p["version"], p["verdict"])
                             for p in v["points"])
            if len(v["points"]) < 2 and not v.get("hole"):
                continue
            print("  %-44s %-13s %s%s"
                  % (m.split("/")[-1][:44], pkg, line,
                     "   <-- HOLE" if v.get("hole") else ""))
    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    json.dump(OrderedDict([
        ("_about", "Library versions a checkpoint is KNOWN to work or fail "
                   "under, as OBSERVED POINTS. A range cannot express a HOLE "
                   "(Falcon-H1: 4.57.1 ok, 5.4.0 fails, 5.14.1 ok), so the "
                   "points are stored and any bound is derived from them."),
        ("_producer", "scripts/build_version_windows.py"),
        ("_sources", SOURCES),
        ("_absence", "A version with no row was never tried. Not a pass, not a "
                     "failure, and the gap between two tested points is exactly "
                     "as unknown as it looks."),
        ("n", len(rows)),
        ("models", rows),
    ]), open(OUT, "w"), indent=1, ensure_ascii=False)
    open(OUT, "a").write("\n")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
