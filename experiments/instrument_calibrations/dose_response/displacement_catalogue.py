"""Which frames displace, what falls, what arrives. The catalogue.

    .venv/bin/python -u displacement_catalogue.py
    .venv/bin/python -u displacement_catalogue.py --n 40

**NOT NAMED `catalogue.py`.** It was, for about an hour, and that shadowed the
`catalogue` PACKAGE that spacy depends on -- every module in this folder puts its
own directory on `sys.path`, so `import spacy` anywhere downstream died with
`AttributeError: module 'catalogue' has no attribute 'create'`, naming neither
this file nor the collision. `pos.get_pos` is on the path of `rank.cells_bulk`,
so that breaks candidate construction for the whole folder.

THIS IS THE DELIVERABLE THE TAGGER WAS BUILT FOR, and the corpus statistics were
never it. Pole sums mix two populations that move in opposite directions -- on
`The other inmates surrounded him and began to`, the tagger's unmarked pole holds
`taunt` at x9.17 and `scream` at x0.33 -- and 80% of the corpus has nothing
happening, so any mean reports the corpus's composition. What the data supports
is a per-frame catalogue: which frames displace, by how much, and INTO WHAT.

## THE UNIT IS (prompt, relation), NOT (prompt)

A frame can displace under one relation and not another, and the relations name
different things. `He raised his fist and` on Llama has VOCALISATION marked
(punched, hit, struck) barely moving at x1.09 while INTENSITY marked (shouted,
yelled) rises x1.79 -- one frame, two true and different readings.

**NO REDUCTION ACROSS SPLITS.** `task_multi.poles(mode="unanimous")` drops words
the rater placed on opposite sides of two relations, and those are exactly the
substitutes: `shouted` is unmarked against `punched` and marked against `said`.
On the Llama fist cell that reduction removed shouted/yelled/screamed and left
`said` alone. Each split keeps its own two sets here.

## WHAT MAKES AN ENTRY

    fall        median over lineages of (marked aligned mass / marked base mass).
                Below 1 means the marked pole shrank. A RATIO, so a frame whose
                marked words are small is not penalised against one whose are large.
    arrived     the largest riser anywhere in the cell, by excess over the
                renormalisation null, with its ratio. This is the substitute, and
                naming it is the point -- "violence falls" is a weaker fact than
                "violence falls and taunt takes 31% of the distribution".
    n_lineages  how many of the five show fall < 0.8. A frame that moves on one
                arm of five is a different object from one that moves on all five.

Base mass floor: the marked pole must hold >= 2% in the base arm on a lineage for
that lineage to count, because a pole at 0.3% can halve on rounding.
"""

import argparse
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

import pole_null as PN                                             # noqa: E402
import rank as R                                                   # noqa: E402

def _med(v):
    """median or None. `statistics.median([])` raises."""
    return st.median(v) if v else None


MIN_BASE = 0.02
DISPLACES = 0.8


def build():
    rows = [json.loads(l) for l in open(PN.OUT) if l.strip()]
    by_pair = collections.defaultdict(list)
    for r in rows:
        by_pair[(r["base"], r["aligned"])].append(r)
    per = collections.defaultdict(list)
    for base, aligned in R.PAIRS:
        g = by_pair.get((base, aligned), [])
        if not g:
            continue
        inf = PN.cell_inflation(base, aligned, [r["prompt"] for r in g])
        for r in g:
            got = inf.get(r["prompt"])
            if not got:
                continue
            fl, rb, d = got
            #: the arrival is the top riser ANYWHERE in the cell, not only in the
            #: unmarked pole. On the inmates frame the destination is `taunt`,
            #: which the tagger did place unmarked -- but on others the substitute
            #: sits in neutral, and a catalogue that could not name it would be
            #: reporting half the event.
            best, bx = None, 0.0
            for w, (pb, pa, cl) in d.items():
                x = pa - pb * fl
                if x > bx:
                    best, bx = w, x
            seen = set()
            for s in r.get("splits", []):
                key = (s["relation"], tuple(sorted(s["marked"])),
                       tuple(sorted(s["unmarked"])))
                #: DUPLICATE SPLITS ARE REAL. On `When he found the man who hurt
                #: him` VOCALISATION and RATIONALISATION came back with identical
                #: poles and identical masses. Counting both double-weights the
                #: cell in every per-relation summary.
                if key[1:] in seen:
                    continue
                seen.add(key[1:])
                mk = [w for w in s["marked"] if w in d]
                if not mk:
                    continue
                mb = sum(d[w][0] for w in mk)
                ma = sum(d[w][1] for w in mk)
                if mb < MIN_BASE:
                    continue
                per[(r["prompt"], s["relation"])].append(dict(
                    base=base, fall=ma / mb, m_base=mb, m_aligned=ma,
                    marked=mk, axis=s["axis"],
                    arrived=best, arrived_excess=bx,
                    arrived_ratio=(d[best][1] / d[best][0]
                                   if best and d[best][0] > 0 else None),
                    arrived_from=d[best][0] if best else None,
                    arrived_to=d[best][1] if best else None))
        print("  %-18s %d (prompt, relation) entries" % (base.split("/")[-1], len(per)),
              flush=True)
    out = []
    for (prompt, rel), v in per.items():
        falls = [x["fall"] for x in v]
        arr = collections.Counter(x["arrived"] for x in v if x["arrived"])
        top = arr.most_common(1)[0] if arr else (None, 0)
        ex = [x for x in v if x["arrived"] == top[0]]
        out.append(dict(
            prompt=prompt, relation=rel,
            fall=st.median(falls), n_lineages=len(v),
            n_displacing=sum(1 for f in falls if f < DISPLACES),
            m_base=st.median([x["m_base"] for x in v]),
            marked=sorted({w for x in v for w in x["marked"]}),
            arrived=top[0], arrived_agree=top[1],
            #: `median([])` raises rather than returning None, and a top riser
            #: absent from the base arm has no ratio at all -- so each of these
            #: guards its own list, not just `ex`.
            arrived_ratio=_med([x["arrived_ratio"] for x in ex if x["arrived_ratio"]]),
            arrived_from=_med([x["arrived_from"] for x in ex
                               if x["arrived_from"] is not None]),
            arrived_to=_med([x["arrived_to"] for x in ex
                             if x["arrived_to"] is not None]),
            axis=v[0]["axis"]))
    return out


def report(cat, n=30, min_lineages=3):
    live = [c for c in cat if c["n_lineages"] >= min_lineages]
    print("\n(prompt, relation) entries: %d | on >=%d lineages: %d"
          % (len(cat), min_lineages, len(live)))
    print("displacing (fall < %.1f) on ALL their lineages: %d"
          % (DISPLACES, sum(1 for c in live if c["n_displacing"] == c["n_lineages"])))
    c = collections.Counter(x["relation"] for x in live
                            if x["n_displacing"] == x["n_lineages"])
    print("  by relation: %s" % dict(c.most_common()))
    print("\nTOP %d BY FALL (median marked aligned/base over lineages)" % n)
    for x in sorted(live, key=lambda c: c["fall"])[:n]:
        print("\n  x%.3f  %d/%d lineages  %-15s %r"
              % (x["fall"], x["n_displacing"], x["n_lineages"], x["relation"],
                 x["prompt"][:60]))
        print("      falls  : %s" % ", ".join(x["marked"][:9]))
        if x["arrived"]:
            print("      arrives: %-12s %s -> %s  x%s   (%d/%d lineages agree)"
                  % (x["arrived"],
                     "%.4f" % x["arrived_from"] if x["arrived_from"] is not None else "  -   ",
                     "%.4f" % x["arrived_to"] if x["arrived_to"] is not None else "  -   ",
                     "%.1f" % x["arrived_ratio"] if x["arrived_ratio"] else "inf",
                     x["arrived_agree"], x["n_lineages"]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--min-lineages", type=int, default=3)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "catalogue.json"))
    a = ap.parse_args(argv)
    cat = build()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(cat, open(a.out, "w"), ensure_ascii=False, indent=1)
    report(cat, a.n, a.min_lineages)
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
