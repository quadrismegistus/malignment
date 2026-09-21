"""Does a word's lift predict that it LOSES mass, WITHIN each lineage?

    python -u lift_within_lineage.py
    python -u lift_within_lineage.py --cut 2.0 --hold-out kill,beat

The README's lift table is pooled over lineages and counts roles from
`substitution_shape`. The paper seat asked whether it survives at the roster's
own unit. Three things had to change to ask that honestly:

**1. THERE IS NO PER-LINEAGE FALLER.** `substitution_shape` averages the fifty
lineages' probabilities BEFORE it picks a biggest faller, so its faller is a
property of the averaged distribution and does not exist per lineage. The
within-lineage question therefore cannot be asked about fallers at all. It is
asked about every rated word instead: did THIS word LOSE mass in THIS lineage.
That is a cleaner test and it is not the same quantity, so it is reported under
its own name.

**2. LIFT IS TAKEN PER LINEAGE TOO.** `charge.word_lift(prompt, base)` is the
word's rating over THAT LINEAGE'S OWN frame rating. Using a corpus-level lift
inside a per-lineage test would put one population's predictor against
another's outcome.

**3. TWO DENOMINATORS, BOTH REPORTED.** Per OBSERVATION, every (prompt, word)
cell counts. Per WORD, a word counts once per lineage by its net direction
there. The pooled table used the first and the paper seat pointed out that
`kill` and `beat` alone carry 115 of its 190 top-band falls, so the second is
the one a sceptical reader computes. `--hold-out` drops named words entirely.
"""
import argparse, collections, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)


def binom(k, n):
    """Two-sided exact binomial against p=0.5."""
    from math import comb
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2.0 ** n)
    return min(1.0, 2.0 * tail)


def cells(lin_b, lin_a):
    """{(prompt, word): delta} for one lineage, raw arm."""
    from malignment import ch
    rows = ch.query(
        "SELECT prompt, word, (p_aligned - p_base) AS delta "
        "FROM {db}.movement_v4 "
        "WHERE base='%s' AND aligned='%s' AND frame_base='' "
        "AND frame_aligned=''"
        % (lin_b.replace("'", "\\'"), lin_a.replace("'", "\\'")),
        limit_bytes=None)
    return {(r["prompt"], r["word"]): float(r["delta"]) for r in rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cut", type=float, default=2.0,
                    help="a word is HIGH lift at or above this, in its cell")
    ap.add_argument("--hold-out", default="",
                    help="comma-separated words to drop entirely")
    ap.add_argument("--lang", default="en", choices=("en", "zh", "both"))
    a = ap.parse_args(argv)
    drop = {w.strip() for w in a.hold_out.split(",") if w.strip()}

    from malignment import charge, roster
    eps, _ = roster.endpoints()
    print("HIGH lift is >= %+.1f in the cell; %d lineages; lang=%s%s"
          % (a.cut, len(eps), a.lang,
             "; holding out %s" % ", ".join(sorted(drop)) if drop else ""))

    per_lin = []
    for b, al in sorted(eps.items()):
        d = cells(b, al)
        if not d:
            continue
        obs = collections.Counter()
        word_dir = collections.defaultdict(lambda: [0.0, 0])
        #: **word_lift IS A FILE SEEK PER CALL**, so it is fetched once per
        #: PROMPT and not once per word. Called per (prompt, word) this loop
        #: reads the annotation file about seven million times.
        lift_of, lang_of = {}, {}
        for (p, w), delta in d.items():
            if w in drop:
                continue
            if p not in lang_of:
                lang_of[p] = charge.language(p)
            if a.lang != "both" and lang_of[p] != a.lang:
                continue
            if p not in lift_of:
                lift_of[p] = charge.word_lift(p, b)
            L = lift_of[p].get(w)
            if L is None or delta == 0:
                continue
            hi = L >= a.cut
            obs[(hi, delta < 0)] += 1
            k = (w, hi)
            word_dir[k][0] += delta
            word_dir[k][1] += 1
        wc = collections.Counter()
        for (w, hi), (tot, _n) in word_dir.items():
            if tot != 0:
                wc[(hi, tot < 0)] += 1
        def rate(c, hi):
            f, r = c[(hi, True)], c[(hi, False)]
            return (f / (f + r) if f + r else None), f + r
        oh, noh = rate(obs, True)
        ol, nol = rate(obs, False)
        wh, nwh = rate(wc, True)
        wl, nwl = rate(wc, False)
        if None in (oh, ol) or min(noh, nol) < 5:
            continue
        per_lin.append((b.split("/")[-1], oh, ol, noh, nol, wh, wl, nwh, nwl))

    print("  %d lineages with at least 5 high-lift and 5 low-lift observations"
          % len(per_lin))

    for name, i_h, i_l, nh, nl in (("PER OBSERVATION", 1, 2, 3, 4),
                                   ("PER WORD", 5, 6, 7, 8)):
        v = [r for r in per_lin if r[i_h] is not None and r[i_l] is not None]
        up = sum(1 for r in v if r[i_h] > r[i_l])
        dn = sum(1 for r in v if r[i_h] < r[i_l])
        print("\n  %s" % name)
        print("    lineages where HIGH-lift words fall more often: %d of %d"
              " (ties %d)" % (up, len(v), len(v) - up - dn))
        print("    sign test p = %.3g" % binom(min(up, dn), up + dn))
        print("    median fall rate   high %.3f   low %.3f   difference %+.3f"
              % (st.median([r[i_h] for r in v]), st.median([r[i_l] for r in v]),
                 st.median([r[i_h] - r[i_l] for r in v])))
        print("    median n per lineage   high %d   low %d"
              % (st.median([r[nh] for r in v]), st.median([r[nl] for r in v])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
