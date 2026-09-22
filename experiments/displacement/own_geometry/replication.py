"""The seven anger paraphrases: does the geometric null hold across all of them?

    python replication.py --ladder tulu

## WHAT THIS IS REPLICATING, AND WHAT IT CANNOT

The commissioned design named the six other anger paraphrases as the
replication. `substitution_shape/README.md` declares the set and its own
verdict travels with it: **the direction holds on all seven and the magnitude
varies fourfold**, with base `kill` running 16 to 42 of 50 BEFORE alignment
touches anything. So these are neither seven independent observations nor one
observation repeated, and a count of seven overstates the evidence.

What a replication across them CAN show is whether the geometric null is a
property of the exhibit or of the frame. If `scream`'s rank to `kill` is static
on the prompt where 12% of lineages keep `kill` and on the one where 50% do,
the null is not an artefact of the one prompt that was looked at first.

**THE CANDIDATE SET DIFFERS PER PROMPT**, because it is that prompt's own
above-theta words, so a rank of 162 is not comparable across rows. Every rank
is therefore printed with its denominator, and the drift is also given as a
PERCENTILE of the prompt's own |rank change| distribution, which is comparable.
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run as R  # noqa: E402

SPACES = ("input", "resid_23", "unembed", "decision")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ladder", default="tulu")
    ap.add_argument("--word", default="scream")
    a = ap.parse_args(argv)
    d = json.load(open(os.path.join(
        HERE, "results", "geometry_%s_anger7.json" % a.ladder)))
    st, src, W = d["stages"], d["src"], a.word
    print("LADDER %s   %r -> %r   seven anger paraphrases" % (a.ladder, src, W))

    print("\n  PROBABILITY AT THE BLANK")
    print("    %-34s %s   %s" % ("prompt", " ".join("%7s" % s for s in st), "p(kill) base->last"))
    for pr, rec in d["prompts"].items():
        pk = [rec["p"][s][src] for s in st]
        print("    %-34s %s   %.4f -> %.4f"
              % (pr[:34], " ".join("%7.4f" % rec["p"][s][W] for s in st), pk[0], pk[-1]))

    for sp in SPACES:
        print("\n  === SPACE: %s ===  rank of %r to %r (of that prompt's own N)"
              % (sp, W, src))
        print("    %-34s %s   %8s %s"
              % ("prompt", " ".join("%9s" % s for s in st), "N", " drift  pctile"))
        for pr, rec in d["prompts"].items():
            rk, words = rec["rank"][sp], rec["words"]
            n = len(words)
            dr = abs(rk[st[-1]][W] - rk[st[0]][W])
            allch = sorted(abs(rk[st[-1]][w] - rk[st[0]][w]) for w in words)
            pct = 100.0 * sum(1 for x in allch if x <= dr) / n
            print("    %-34s %s   %8d  %5d  %5.0fth"
                  % (pr[:34], " ".join("%9d" % rk[s][W] for s in st), n, dr, pct))

    print("\n  === GEOMETRY vs PROBABILITY === Spearman |dlog p| against |d rank|,"
          " base -> last stage")
    print("    %-34s %s" % ("prompt", " ".join("%11s" % s for s in SPACES)))
    for pr, rec in d["prompts"].items():
        words = rec["words"]
        n = len(words)
        cells = []
        for sp in SPACES:
            rk = rec["rank"][sp]
            dp = [abs(math.log(max(rec["p"][st[-1]][w], 1e-12))
                      - math.log(max(rec["p"][st[0]][w], 1e-12))) for w in words]
            dr = [abs(rk[st[-1]][w] - rk[st[0]][w]) for w in words]
            rx = {v: i for i, v in enumerate(sorted(range(n), key=lambda j: dp[j]))}
            ry = {v: i for i, v in enumerate(sorted(range(n), key=lambda j: dr[j]))}
            xs = [rx[j] for j in range(n)]
            ys = [ry[j] for j in range(n)]
            mx, my = sum(xs) / n, sum(ys) / n
            num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
            cells.append("%+11.3f" % (num / den if den else float("nan")))
        print("    %-34s %s" % (pr[:34], " ".join(cells)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
