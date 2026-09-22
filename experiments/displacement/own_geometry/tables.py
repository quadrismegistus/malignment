"""Render the tables from `run.py`'s saved geometry. No models loaded.

    python tables.py --ladder olmo2-1b
    python tables.py --ladder tulu --space unembed

One table per space: the rank of `kill`'s destinations and of the controls at
every stage, with the candidate's probability at the blank beside them, so a
reader can see whether the geometry moves where the probabilities move.

## THE BASELINE IS THE POINT

A rank change for `scream` means nothing until you know how much everything
moves. Every table carries, per stage transition, the distribution of |rank
change| over all 307 candidates, and `scream`'s change is reported as a
PERCENTILE of it. A shift that sits at the 50th percentile is the ladder
breathing, not an operation on `scream`.

## AND THE DIRECTION QUESTION NEEDS DISPLACEMENT, NOT COSINE

Cosine is symmetric, so "did `kill` move toward the vocal cluster, or the
cluster toward `kill`" cannot be read off it. The stages are continuous
fine-tunes with no rotation between them, so the same row at two stages is
comparable in absolute terms: `||v_next - v_prev||` per candidate, with `kill`
and the vocal cluster reported against the median candidate's movement.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as R  # noqa: E402

SPACES = ("input", "resid_23", "resid_mean", "unembed", "decision")
ROWS = R.DESTS + ["|"] + R.CONTROLS


def pct(v, xs):
    return 100.0 * sum(1 for x in xs if x <= v) / len(xs)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ladder", default="olmo2-1b")
    ap.add_argument("--space", default="all")
    a = ap.parse_args(argv)
    import numpy as np
    d = json.load(open(os.path.join(HERE, "results", "geometry_%s.json" % a.ladder)))
    st, words, src = d["stages"], d["words"], d["src"]
    N = len(words)
    print("LADDER %s   prompt %r   from %r   %d candidates (%d multi-token)"
          % (a.ladder, d["prompt"], src, N, d["n_multi"]))

    print("\n  p(first token) at the blank, by stage")
    print("    %-9s %s" % ("word", "  ".join("%9s" % s for s in st)))
    for w in [src] + R.DESTS + R.CONTROLS:
        print("    %-9s %s" % (w, "  ".join("%9.5f" % d["p"][s][w] for s in st)))

    spaces = SPACES if a.space == "all" else (a.space,)
    for sp in spaces:
        rk, cs = d["rank"][sp], d["cos"][sp]
        print("\n  === SPACE: %s ===   rank of %d, cosine to %r" % (sp, N, src))
        print("    %-9s %s" % ("word", "  ".join("%14s" % s for s in st)))
        for w in ROWS:
            if w == "|":
                print("    %-9s %s" % ("-" * 9, "  ".join("-" * 14 for _ in st)))
                continue
            print("    %-9s %s" % (w, "  ".join(
                "%4d %+8.3f" % (rk[s][w], cs[s][w]) for s in st)))
        print("    BASELINE: |rank change| over all %d candidates" % N)
        for i in range(len(st) - 1):
            a_, b_ = st[i], st[i + 1]
            ch = [abs(rk[b_][w] - rk[a_][w]) for w in words]
            ch_s = sorted(ch)
            med = ch_s[len(ch_s) // 2]
            p90 = ch_s[int(0.9 * len(ch_s))]
            sc = abs(rk[b_][src if False else "scream"] - rk[a_]["scream"])
            print("      %-4s -> %-4s  median %4d   p90 %4d   max %4d   |"
                  "  scream %4d  = %.0fth pct" % (a_, b_, med, p90, max(ch), sc,
                                                  pct(sc, ch)))

    #: **DOES THE GEOMETRY MOVE WHERE THE PROBABILITY MOVES?** The design asks
    #: for p beside the ranks "so the reader can see" it; an eye over 307 rows
    #: is not a measurement, so it is computed. Spearman between |change in
    #: log p| and |change in rank|, per transition per space. If alignment
    #: rewired the geometry to make room for the words it promotes, these
    #: would be positive; at zero the two are unrelated and the promotion is
    #: happening somewhere the geometry does not record.
    import math as _m
    print("\n  === DOES GEOMETRY MOVE WHERE PROBABILITY MOVES? ===")
    print("    rank corr of |dlog p| against |d rank|, over all %d candidates" % N)
    print("    %-11s %s" % ("space", "  ".join(
        "%9s" % ("%s>%s" % (st[i][:3], st[i + 1][:3])) for i in range(len(st) - 1))))
    for sp in spaces:
        rk = d["rank"][sp]
        cells = []
        for i in range(len(st) - 1):
            a_, b_ = st[i], st[i + 1]
            dp = [abs(_m.log(max(d["p"][b_][w], 1e-12))
                      - _m.log(max(d["p"][a_][w], 1e-12))) for w in words]
            dr = [abs(rk[b_][w] - rk[a_][w]) for w in words]
            rx = {v: i2 for i2, v in enumerate(sorted(range(N), key=lambda j: dp[j]))}
            ry = {v: i2 for i2, v in enumerate(sorted(range(N), key=lambda j: dr[j]))}
            xs = [rx[j] for j in range(N)]
            ys = [ry[j] for j in range(N)]
            mx, my = sum(xs) / N, sum(ys) / N
            num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den = _m.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
            cells.append("%+9.3f" % (num / den if den else float("nan")))
        print("    %-11s %s" % (sp, "  ".join(cells)))

    #: DIRECTION: who moved, in absolute terms
    npz = os.path.join(HERE, "results", "geometry_%s.npz" % a.ladder)
    if os.path.exists(npz):
        z = np.load(npz, allow_pickle=True)
        idx = {w: i for i, w in enumerate(words)}
        print("\n  === WHO MOVED === ||v_next - v_prev||, and the same as a "
              "multiple of the median candidate's movement")
        for sp in spaces:
            print("    space %s" % sp)
            for i in range(len(st) - 1):
                A = z["%s__%s" % (sp, st[i])]
                B = z["%s__%s" % (sp, st[i + 1])]
                mv = np.linalg.norm(B - A, axis=1)
                med = float(np.median(mv))
                if med == 0:
                    print("      %-4s -> %-4s  NOTHING MOVED (identical rows)"
                          % (st[i], st[i + 1]))
                    continue
                voc = [idx[w] for w in R.VOCAL if w in idx]
                print("      %-4s -> %-4s  median %8.4f | %s=%.2fx  vocal "
                      "mean=%.2fx  %s"
                      % (st[i], st[i + 1], med, src, mv[idx[src]] / med,
                         float(np.mean(mv[voc])) / med,
                         "  ".join("%s=%.2fx" % (w, mv[idx[w]] / med)
                                   for w in ("scream", "eat"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
