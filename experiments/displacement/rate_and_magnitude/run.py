"""How MUCH mass moves, and how OFTEN -- and whether either scales with the frame.

    python -u run.py                 # both languages
    python -u run.py --lang zh

## THE TWO QUANTITIES, AND WHY THE FOLDER IS NAMED FOR BOTH

M01 `F_G_rate_magnitude` separated them and found they behave differently:

    RATE       does alignment displace MORE OFTEN at transgressive sites?
               NULL -- n=33 pair-sites, p=0.148
    MAGNITUDE  does it displace HARDER?
               CONFIRMED -- d=0.748, p=6e-5

"Alignment does not displace more often at transgressive sites; it displaces
harder." `Q_bridge` names the magnitude quantity: `departed`, "how much mass
leaves words at all", against `tail_excess` for DIRECTION -- whether freed mass
"re-lands on nameable substitute words or disperses into the unresolved tail".

**This folder does not measure direction.** `displacement_axis` measures
magnitude and direction along author-declared pole axes; `displacement_taxonomy`
asks what KIND of movement; `register_shift` asks about one scale. None of them
asks how much mass moves at all, which is why this exists.

## WHAT IS NEW HERE: THE CONTINUOUS VERSION

M01 asked it as a BINARY contrast -- a transgressive twin against its matched
neutral twin. This regresses three outcomes on a CONTINUOUS base-arm
transgressive level, per lineage, across prompts:

    departed   sum of p_base - p_aligned over fallers
    arrived    sum of p_aligned - p_base over risers
    n_movers   how many words moved at all -- M01's RATE, per prompt

All three travel together and that is not decoration. More words moving while
LESS mass moves is a DISPERSAL, and a departed-only reading would call it a
smaller effect rather than a differently-shaped one. That is exactly what
Chinese does.

## SHARED WITH norm_change AND NOT COPIED

The dose is the base-arm mass-weighted mean of `k_transgressiveness`, read from
`norm_change`'s `levels_long`, and the lineage roster is
`roster.endpoints()` -- 50 pairs, not the 153 edges in `movement`, which include
rungs and transitive pairs and would let one base model vote eleven times.
"""

import argparse, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "norm_change")))
DATA = os.path.expanduser("~/malignment-data/norm_change")

MIN_PROMPTS = 25
DOSE = "k_transgressiveness"

from analyse import endpoint_pairs          # noqa: E402


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def slope(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    my = sum(ys) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def report(target, sl):
    import statistics as st
    v = list(sl.values())
    up = sum(1 for x in v if x > 0)
    dn = sum(1 for x in v if x < 0)
    if up + dn < 3:
        return None
    return (binom(up, up + dn), target, st.median(v), up, dn, len(v))


def measure(langs, min_prompts=MIN_PROMPTS):
    """Does MORE MASS MOVE where the base arm is more transgressive?

    M01 asked this as a BINARY contrast and answered it: `F_G_rate_magnitude`
    finds the RATE null (n=33 pair-sites, p=0.148) and the MAGNITUDE confirmed
    (d=0.748, p=6e-5) -- "alignment does not displace more often at
    transgressive sites; it displaces HARDER". `Q_bridge` names the quantity:
    `departed` is "how much mass leaves words at all".

    This is the CONTINUOUS version, which had not been run. Three outcomes per
    (lineage, prompt), each regressed on the same base-arm transgressive level:

        departed   sum of p_base - p_aligned over fallers
        arrived    sum of p_aligned - p_base over risers
        n_movers   how many words moved at all -- M01's RATE, per prompt

    Reporting all three matters because they can separate: more words moving
    while less mass moves is a DISPERSAL, and a departed-only reading would
    call it a smaller effect rather than a differently-shaped one.
    """
    import gzip, statistics as st
    from malignment import ch
    EP = endpoint_pairs()
    print("MAGNITUDE DOSE: does more mass move where the base is transgressive?")
    print("unit = the lineage; slope across prompts; %d endpoint pairs" % len(EP))
    rows = ch.query(
        "SELECT base, aligned, prompt, "
        "sumIf(p_base - p_aligned, cls='faller') AS dep, "
        "sumIf(p_aligned - p_base, cls='riser') AS arr, count() AS nm "
        "FROM movement WHERE cls != 'still' GROUP BY base, aligned, prompt")
    mag = {}
    for r in rows:
        lin = r["base"] + ">" + r["aligned"]
        if lin in EP:
            mag[(lin, r["prompt"])] = (float(r["dep"]), float(r["arr"]), int(r["nm"]))
    dose = {}
    with gzip.open(os.path.join(DATA, "levels_long.csv.gz"), "rt",
                   encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["scale"]] != DOSE:
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in EP:
                continue
            try:
                dose[(lin, v[ix["prompt"]], v[ix["lang"]])] = float(v[ix["base_level"]])
            except ValueError:
                pass
    print()
    print("  %-4s %-10s %4s %12s %8s %10s" % ("lang", "outcome", "n", "med slope", "up/dn", "p"))
    for lang in langs:
        for j, nm in ((0, "departed"), (1, "arrived"), (2, "n_movers")):
            by = collections.defaultdict(lambda: ([], []))
            for (lin, pr, lg), d in dose.items():
                if lg != lang:
                    continue
                m = mag.get((lin, pr))
                if not m:
                    continue
                by[lin][0].append(d)
                by[lin][1].append(float(m[j]))
            sl = {}
            for lin, (xs, ys) in by.items():
                if len(xs) < min_prompts:
                    continue
                s2 = slope(xs, ys)
                if s2 is not None:
                    sl[lin] = s2
            r = report(nm, sl)
            if r:
                p_, _t, med, up, dn, n = r
                print("  %-4s %-10s %4d %+12.5f %4d/%-4d %10.6f%s"
                      % (lang, nm, n, med, up, dn, p_, "  <-" if p_ < 0.05 else ""))
    return 0




def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    a = ap.parse_args(argv)
    return measure([a.lang] if a.lang else ["en", "zh"])


if __name__ == "__main__":
    sys.exit(main())
