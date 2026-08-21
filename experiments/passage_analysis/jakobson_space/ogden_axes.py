"""Where does Ogden Basic English sit on our two axes, and does alignment go there?

    python .../ogden_axes.py

Reads `results/ogden_groups.csv` (paired passages from `ogden_align.py`), scores
both sides through `malignment.score`, and reports the paired difference.

## WHY THIS IS WORTH DOING AT ALL

Every direction this campaign has measured is one of its own construction:
base-to-aligned, small-to-large, unframed-to-framed. **Ogden Basic English is a
direction someone else defined, for reasons that had nothing to do with us** --
a deliberate restriction to an 850-word vocabulary, executed by editors in the
1930s on stories they did not write. It is the only external, named
simplification we can put on the same axes.

So the question is not "is Basic English simpler" -- it is by construction. It
is whether ALIGNMENT MOVES A MODEL IN THE SAME DIRECTION. `arm_paired.py` puts
the alignment step at -0.8435 surprisal and -0.0254 drift over 22 lineages. If
simplification moves the same way in similar proportion, alignment resembles a
named human editorial operation. If it does not, alignment lowers surprisal
WITHOUT being simplification in Ogden's sense, which is the more interesting
outcome and the one that cannot be reached without an external reference.

## THE PAIRING IS THE DESIGN

Each row is one passage said twice. Content, order and author are held by
construction, so the difference is the rendering and nothing else -- which no
corpus-level comparison of "simple text" against "complex text" can claim, since
those differ in what they are about as well as how they say it.

The consequence for the statistic: the unit is the PAIR, the test is on
within-pair differences, and a bootstrap resamples pairs. 47 groups from three
stories by three authors, so the effective independence is closer to three than
to 47 -- reported per text as well as pooled, and no claim rests on the pooled
interval alone.

## LENGTH IS NOT CONTROLLED AND MUST NOT BE

Basic runs longer than its original in 45 of 47 groups. That is the Ogden
constraint operating -- an 850-word vocabulary buys the same content with more
words -- so holding length constant would remove part of the very effect being
measured. Surprisal is therefore reported at a common TOKEN PREFIX (which
controls the measurement window without deleting the length difference) and
also whole-passage, with both shown; drift is per-step and length-free.
"""

import argparse, csv, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SRC = os.path.join(HERE, "results", "ogden_groups.csv")


def boot(d, n=4000, seed=20260821):
    """CI on the median of PAIRED differences, resampling pairs."""
    rng = random.Random(seed)
    s = sorted(statistics.median(rng.choices(d, k=len(d))) for _ in range(n))
    return s[int(0.025 * n)], s[int(0.975 * n)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--m", type=int, default=100, help="surprisal prefix, tokens")
    a = ap.parse_args(argv)
    from malignment import Passage, score, score_all

    rows = list(csv.DictReader(open(a.src, newline="")))
    P = [(r["text"], Passage(r["basic"]), Passage(r["original"]),
          int(r["basic_words"]), int(r["orig_words"])) for r in rows]
    print("%d paired passages from %d texts" % (len(P), len({t for t, *_ in P})))
    score_all([p for _, b, o, *_ in P for p in (b, o)], m=a.m)

    def diffs(f):
        out = []
        for t, b, o, bw, ow in P:
            x, y = f(b), f(o)
            if x is not None and y is not None:
                out.append((t, x - y))
        return out

    print("\nBASIC minus ORIGINAL   (negative = Basic is lower on that axis)")
    print("%-26s %9s %9s %11s %6s" % ("", "median", "n", "95% CI", "neg"))
    tests = [("surprisal (M=%d)" % a.m, lambda p: p.surprisal_at(a.m)),
             ("surprisal (whole)", lambda p: p.surprisal),
             ("drift", lambda p: p.drift),
             ("n_sents", lambda p: float(p.n_sents))]
    pooled = {}
    for lab, f in tests:
        d = diffs(f)
        if not d:
            print("%-26s -- no pairs --" % lab); continue
        v = [x for _, x in d]
        lo, hi = boot(v)
        pooled[lab] = statistics.median(v)
        print("%-26s %+9.4f %9d [%+.4f,%+.4f] %5.0f%%"
              % (lab, statistics.median(v), len(v), lo, hi,
                 100 * sum(1 for x in v if x < 0) / len(v)))

    #: PER TEXT, because three stories by three authors is the real n. A pooled
    #: interval over 47 groups asserts an independence the design does not have.
    print("\nper text, median difference (the effective n is 3, not 47)")
    print("%-26s %10s %10s %10s" % ("", "surprisal", "drift", "n groups"))
    for t in sorted({x[0] for x in P}):
        s = [d for tt, d in diffs(lambda p: p.surprisal_at(a.m)) if tt == t]
        dr = [d for tt, d in diffs(lambda p: p.drift) if tt == t]
        print("%-26s %+10.4f %+10.4f %10d"
              % (t.split(".")[0], statistics.median(s) if s else float("nan"),
                 statistics.median(dr) if dr else float("nan"), len(s)))

    #: THE COMPARISON THE FILE EXISTS FOR
    print("\nAGAINST THE ALIGNMENT STEP (arm_paired.py, 22 lineages)")
    print("%-26s %12s %12s" % ("", "surprisal", "drift"))
    print("%-26s %+12.4f %+12.4f" % ("alignment (aligned-base)", -0.8435, -0.0254))
    print("%-26s %+12.4f %+12.4f" % ("simplification (basic-orig)",
                                     pooled.get("surprisal (M=%d)" % a.m, float("nan")),
                                     pooled.get("drift", float("nan"))))
    print("\nSame sign on an axis means alignment moves a model the way an editor")
    print("moved a story. Opposite means alignment is not simplification in")
    print("Ogden's sense on that axis, whatever else it is.")


if __name__ == "__main__":
    main()
