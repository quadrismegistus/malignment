"""Ingest every run in a pending-ingest file that has landed, skipping what is stored.

    python ingest_pending.py --pending results/pending_ingest_controlpairs_20260823.tsv
    python ingest_pending.py --pending ... --status     # what is in, what is not

## WHY A FILE AND NOT A COMMAND PER RUN

A run id exists nowhere on disk -- it is returned once, in the launch reply, and
is unrecoverable afterwards. Sixteen of them typed one at a time into sixteen
`--ingest` calls is sixteen chances to pair a run with the wrong slug, and the
failure is silent: `--ingest` would store a real reading for a real prompt, just
not the one that produced it. The pending file pairs them once, checked, and
this reads that pairing.

## IT IS RE-RUNNABLE ON PURPOSE

Runs land over tens of minutes and the useful thing is to sweep repeatedly. A
run already in the stash is reported and skipped rather than re-ingested, so the
same command can be run after every notification without duplicating readings --
`crosslineage.readings` de-duplicates by content, but relying on that would be
leaning on a downstream guard to cover an upstream mistake.

## A RUN THAT NEVER LANDS IS REPORTED, NEVER ASSUMED

`--status` prints the outstanding ones by name. Silence from a workflow is
indistinguishable from a workflow still working, and the only thing that
separates them is a list of what has not arrived.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
import crosslineage as X  # noqa: E402


def pending(path):
    rows = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if f[0] == "run_id":
            continue
        rows.append(dict(run_id=f[0], role=f[1], mass=float(f[2]), slug=f[3], prompt=f[4]))
    return rows


def wanted(slug):
    """How many raters this run was PREPARED with, from its own state file.

    State files written before `prepare` recorded `raters` do not carry it. Those
    fall back to 2, which is what every run on this design used -- but the
    fallback SAYS SO, because a default that is right today is indistinguishable
    from a measurement until the day it is not.
    """
    d = json.load(open(os.path.join(HERE, "results", "xling_%s.json" % slug)))
    if "raters" not in d:
        print("  (%s predates `raters` in the state file; assuming 2)" % slug,
              file=sys.stderr)
    return int(d.get("raters") or 2), d.get("version")


def stored(prompt, version=None):
    """How many readings the stash holds for this prompt, at this version."""
    st = X._stash()
    return sum(1 for k in st if isinstance(k, dict)
               and k.get("frame_prompt") == prompt
               and (version is None or k.get("version") == version))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pending", required=True)
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    rows = pending(a.pending)
    done = miss = new = 0
    out = []
    for r in rows:
        #: COUNT AGAINST THE EXPECTED RATERS, NEVER AGAINST ZERO.
        #:
        #: The first version skipped any prompt with a reading already stored,
        #: and the first sweep caught `He pulled the wallet from his jacket and`
        #: mid-flight: rater 1 had written to the journal and rater 2 had not, so
        #: it stored `1 of 1` and the gate would then have reported it done and
        #: never looked again. Half a reading of a control is worse than none,
        #: because the pair still appears complete in every count.
        #:
        #: Re-ingesting is safe -- `crosslineage.ingest` re-reads the journal
        #: from disk and keys each reading by rater, so an already-stored rater
        #: is overwritten with itself -- so the gate can be "not yet all of
        #: them" rather than "not any of them".
        want, ver = wanted(r["slug"])
        n = stored(r["prompt"], ver)
        if n >= want:
            done += 1
            out.append(("IN   %d of %d reading(s)" % (n, want), r))
            continue
        if n:
            out.append(("PARTIAL %d of %d, retrying" % (n, want), r))
        if a.status:
            miss += 1
            out.append(("OUT", r))
            continue
        try:
            X.ingest(r["run_id"], r["slug"])
            new += 1
            out.append(("INGESTED", r))
        except SystemExit as e:
            miss += 1
            out.append(("WAITING  %s" % str(e)[:44], r))
        except Exception as e:
            miss += 1
            out.append(("ERROR    %s" % str(e)[:44], r))
    print("\n%-26s %-8s %7s  %s" % ("state", "role", "mass", "prompt"))
    for s, r in out:
        print("%-26s %-8s %6.2f%%  %s" % (s, r["role"], 100 * r["mass"], r["prompt"][:44]))
    print("\n%d of %d already stored, %d ingested now, %d outstanding"
          % (done, len(rows), new, miss))


if __name__ == "__main__":
    main()
