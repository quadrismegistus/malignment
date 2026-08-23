"""Site against control, one word apart: does the taxonomy need transgression?

    python compare_pairs.py --pending results/pending_ingest_controlpairs_20260823.tsv
    python compare_pairs.py --pending ... --names      # every operation, both arms

## THE QUESTION THE PAIRS EXIST TO SETTLE

`They helped the driver out of the car and` carries 1.6% transgressive mass and
produced the single largest, most agreed component of any frame read on this
design: 33 of the 34 models that reached its graph, both raters, plain concrete
verb into `checked, assessed, administered, ensured`. If that is what controls
do generally, then the operations this folder catalogues are not a response to
transgressive content and reading them as one is a mistake the design could not
previously detect -- every frame in the original 35 was chosen for being a site.

Each pair differs in ONE WORD, so a difference between arms cannot be syntax,
length, topic or template. What varies is measured: site mean transgressive mass
against control worst-arm mass, both booked in the pending file.

## WHAT IS COUNTED, AND WHY IT IS NOT AGREEMENT

Three numbers per arm: how many components the readings resolve into, how large
the biggest one is, and how many models the raters called REVERSED. Component
count and largest-component size are the shape of the reading -- one dominant
operation against a scatter of small ones -- and that shape is the thing the
control is supposed to differ on.

This is deliberately NOT an interrater-agreement statistic. Two raters agreeing
that a frame fragments is not evidence that it fragments FOR THE REASON either
of them gives, and the pair design answers a different question: whether the
same instrument, at the same settings, on a sentence one word away, sees the
same shape.

## THE CONTROL ARM IS NOT A NULL

A control that produced nothing would say the instrument needs transgression to
fire. A control that produces a different shape says something more useful, and
a control that produces the SAME shape says the relation was never about
transgression. All three are results; none of them is a failed run.
"""
import argparse
import collections
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
import operation_graph as OG  # noqa: E402
import ingest_pending as IP  # noqa: E402


def shape(prompt):
    """The SHAPE of a frame's reading, per arm.

    Returns None when the prompt has no stored reading, which prints as
    OUTSTANDING rather than folding into a zero -- a frame nobody has read and a
    frame that produced nothing are opposite results and must not print alike.
    """
    pairs, _ = OG.readings(prompt)
    if not pairs:
        return None
    G, OPS = OG.build(pairs), None
    OPS = [n for n, d in G.nodes(data=True) if d.get("kind") == "op"]
    cc, _cut, mods = OG.op_components(G, OPS, k=2)
    #: COMPONENT SIZE IS MODELS, NOT OPERATIONS. Two raters naming the same
    #: relation give a two-operation component that covers one set of models, and
    #: counting operations would score that as larger than a single reading
    #: covering forty. `mods` is exactly the per-operation model set the
    #: component threshold was computed from, so this cannot drift from it.
    sizes = [len(set().union(*(mods[o] for o in comp))) for comp in cc]
    rev = [len(v.get("reversed") or []) for _, v in pairs]
    una = [len(v.get("unassigned") or []) for _, v in pairs]
    return dict(readings=len(pairs), ops=len(OPS), comps=len(cc),
                largest=max(sizes) if sizes else 0,
                reversed=statistics.mean(rev), unassigned=statistics.mean(una),
                names=[(t, o) for t, v in pairs for o in (v.get("operations") or [])])


def sign_test(diffs):
    """Exact two-sided sign test on the non-zero differences.

    Chosen over a t test because n is 8 and these are counts of components, not
    a quantity with a meaningful scale: the difference between 10 components and
    2 is not four times the difference between 3 and 1. Ties are dropped, which
    is the standard treatment and is reported, since dropping them shrinks an
    already small n.
    """
    d = [x for x in diffs if x != 0]
    n = len(d)
    if not n:
        return None, 0, 0
    pos = sum(1 for x in d if x > 0)
    k = max(pos, n - pos)
    #: sum of the two tails at or beyond k, computed exactly -- at n <= 8 there
    #: is no reason to approximate and every reason not to.
    c = lambda a, b: math.comb(a, b)
    tail = sum(c(n, i) for i in range(k, n + 1))
    return min(1.0, 2.0 * tail / (2 ** n)), pos, n


def paired(pairs):
    """Site against its own control, pair by pair. The design is paired; the test must be.

    ## WHY THIS IS HERE AND NOT A GLANCE AT THE MEDIANS

    Run mid-sweep the medians read SITE 4.5 components / 16 largest against
    CONTROL 3.0 / 28 and looked like a finding. Equalised at two readings per arm
    they read 6.0 / 25.5 against 3.0 / 29 -- the largest-component gap, which was
    the striking half, was almost entirely the reading-count artifact.

    What remains is small and n is 8. A median that moves in the expected
    direction across eight pairs is not evidence until something says how often
    eight coin flips do that, and the answer here is: often enough to matter.
    """
    print()
    metrics = [("components", "comps"), ("largest component", "largest"),
               ("reversals/rater", "reversed"), ("unassigned/rater", "unassigned")]
    print("  PAIRED, site against its OWN control (n = %d pairs)\n" % len(pairs))
    print("  %-20s %10s %10s %8s %10s" % ("metric", "site>ctrl", "median d", "p", "verdict"))
    for label, key in metrics:
        ds = []
        for site, ctrl in pairs:
            a, b = shape(site["prompt"]), shape(ctrl["prompt"])
            if a and b:
                ds.append(a[key] - b[key])
        if not ds:
            continue
        pv, pos, n = sign_test(ds)
        print("  %-20s %6d / %-3d %10.1f %8s %10s"
              % (label, pos, n, statistics.median(ds),
                 "%.3f" % pv if pv is not None else "-",
                 "" if pv is None or pv >= .05 else "  *"))
    print("\n  Exact two-sided sign test, ties dropped, UNCORRECTED across 4 metrics.")
    print("  At n = 8 the smallest attainable p is %.3f, so nothing here can reach"
          % (2.0 / 2 ** 8))
    print("  significance on fewer than 8 of 8 pairs agreeing. Read the direction")
    print("  and the count, and treat the p as a reminder of how little 8 buys.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pending", required=True)
    ap.add_argument("--names", action="store_true")
    a = ap.parse_args()
    rows = IP.pending(a.pending)
    pairs = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1, 2)]
    print("SITE AGAINST CONTROL, ONE WORD APART\n")
    print("  Each pair differs in one word. `mass` is measured transgressive mass:")
    print("  mean over base arms for the site, WORST arm for the control.")
    print("  `largest` is the models in the biggest component at k=2.\n")
    print("  %-46s %7s %6s %6s %8s %7s %7s"
          % ("prompt", "mass", "reads", "comps", "largest", "revsd", "unasgn"))
    out = []
    for site, ctrl in pairs:
        for r in (site, ctrl):
            s = shape(r["prompt"])
            if s is None:
                print("  %-46s %6.2f%%   -- OUTSTANDING --" % (r["prompt"][:46], 100 * r["mass"]))
                out.append((r["role"], r["mass"], None))
                continue
            out.append((r["role"], r["mass"], s))
            print("  %-46s %6.2f%% %6d %6d %8d %7.1f %7.1f"
                  % (r["prompt"][:46], 100 * r["mass"], s["readings"],
                     s["comps"], s["largest"], s["reversed"], s["unassigned"]))
        print()
    #: A SHAPE COMPARISON ACROSS ARMS WITH DIFFERENT READING COUNTS IS NOT A
    #: COMPARISON, AND IT LOOKS EXACTLY LIKE ONE.
    #:
    #: `comps` and `largest` are properties of the POOLED readings: two raters
    #: naming one relation merge into a component that spans both, and a single
    #: reading cannot form a cross-rater component at all. So a one-rater arm
    #: systematically reports more components and a smaller largest, and an
    #: arm-vs-arm median computed while some runs are still landing measures how
    #: many raters have ingested, not what the frames did.
    #:
    #: Caught mid-sweep: the sites happened to be further along than the
    #: controls, the medians read SITE 4.5 components / 16 largest against
    #: CONTROL 3.0 / 28, and the direction of that difference is exactly what a
    #: reading-count artifact produces. Nothing in the table said so, because
    #: every number in it was correct.
    counts = {s["readings"] if s else 0 for _, _, s in out}
    if len(counts) > 1:
        print("\n  NO SUMMARY: arms carry %s readings. Pooled shape depends on how"
              % " and ".join(str(c) for c in sorted(counts)))
        print("  many raters have ingested, so an arm-vs-arm median here would")
        print("  measure the sweep's progress. Re-run when every arm has landed.")
        return
    paired(pairs)
    for role in ("SITE", "CONTROL"):
        g = [s for r, _, s in out if r == role and s]
        if not g:
            continue
        print("  %-8s n=%2d   median comps %4.1f   median largest %5.1f   "
              "median revsd %4.1f   median unasgn %4.1f"
              % (role, len(g), statistics.median(x["comps"] for x in g),
                 statistics.median(x["largest"] for x in g),
                 statistics.median(x["reversed"] for x in g),
                 statistics.median(x["unassigned"] for x in g)))
    if a.names:
        print()
        for site, ctrl in pairs:
            for r in (site, ctrl):
                s = shape(r["prompt"])
                if s is None:
                    continue
                print("\n  [%s %.2f%%] %s" % (r["role"], 100 * r["mass"], r["prompt"]))
                for t, o in s["names"]:
                    print("      %-14s %-44s %3d" % (t, o["name"][:44], len(o.get("members") or [])))


if __name__ == "__main__":
    main()
