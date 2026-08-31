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


def _tail_excess(sum_base, sum_aligned, departed, faller_base):
    """DIRECTION: does freed mass re-land on nameable words or go to the tail?

    M01 `N_mass_migration`: "Probability is conserved, so 'the mass went
    somewhere' is not a finding; the finding is whether it re-lands on nameable
    words above the resolution floor (substitution) or disperses into the
    unresolvable tail (diffusion). **The comparison is against a
    proportional-renormalisation null** -- what the distribution would look like
    if the freed mass were simply spread evenly over the survivors."

    **THE NULL IS WHAT CONTROLS FOR GENERAL SHARPENING**, and that is the whole
    reason it is the null rather than a raw tail difference. If alignment merely
    rescaled the distribution, the freed mass would land on every survivor --
    the tail included -- in proportion to what it already held. Subtracting that
    expectation leaves only the part that is not rescaling. A raw
    `tail_aligned - tail_base` would confound the two and is not computed here.

        tail_base    = 1 - sum(p_base)          the theta-censored remainder
        survivors    = 1 - faller_base          everything the freed mass could
                                                land on, tail included
        expected     = tail_base * (1 + departed / survivors)
        tail_excess  = tail_aligned - expected

    NEGATIVE means less mass reached the tail than proportional renormalisation
    predicts -- it concentrated on nameable words. That is SUBSTITUTION, and
    negative is the sign M01 found in both languages.
    """
    tail_base = 1.0 - sum_base
    tail_aligned = 1.0 - sum_aligned
    survivors = 1.0 - faller_base
    if survivors <= 0 or tail_base < 0 or tail_aligned < 0:
        return None
    expected = tail_base * (1.0 + departed / survivors)
    return tail_aligned - expected


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
        "sumIf(p_aligned - p_base, cls='riser') AS arr, count() AS nm, "
        "countIf(cls='faller') AS nf, countIf(cls='riser') AS nr, "
        #: the RESOLVED mass on each side. The twp store is theta-censored, so
        #: 1 - sum(p) is the UNRESOLVED TAIL: everything below the floor, which
        #: is where diffusion would put the freed mass.
        "sum(p_base) AS sb, sum(p_aligned) AS sa, "
        "sumIf(p_base, cls='faller') AS fb "
        "FROM movement WHERE cls != 'still' GROUP BY base, aligned, prompt")
    mag = {}
    for r in rows:
        lin = r["base"] + ">" + r["aligned"]
        if lin in EP:
            #: n_fallers and n_risers separately -- the RATE split by
            #: direction. Not `tail_excess`, which asks WHERE the freed mass
            #: lands; this asks whether the extra movement at a loaded prompt is
            #: words LEAVING or words ARRIVING. The two can dissociate: mass can
            #: depart through few large fallers while arriving across many small
            #: risers, which is the shape M01 T section 14 named.
            mag[(lin, r["prompt"])] = (float(r["dep"]), float(r["arr"]),
                                       int(r["nm"]), int(r["nf"]), int(r["nr"]),
                                       int(r["nf"]) - int(r["nr"]),
                                       (float(r["dep"]) / int(r["nf"])) if int(r["nf"]) else None,
                                       (float(r["arr"]) / int(r["nr"])) if int(r["nr"]) else None,
                                       _tail_excess(float(r["sb"]), float(r["sa"]),
                                                    float(r["dep"]), float(r["fb"])))
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
        for j, nm in ((0, "departed"), (1, "arrived"), (2, "n_movers"),
                      (3, "n_fallers"), (4, "n_risers"), (5, "n_fall-n_rise"),
                      (6, "mass/faller"), (7, "mass/riser"), (8, "tail_excess")):
            by = collections.defaultdict(lambda: ([], []))
            for (lin, pr, lg), d in dose.items():
                if lg != lang:
                    continue
                m = mag.get((lin, pr))
                if not m or m[j] is None:
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




def measure_lift(min_prompts=MIN_PROMPTS):
    """The same 9 outcomes regressed on PER-LINEAGE charge.lift_per_lineage.

    **ENGLISH ONLY.** charge ratings are English, flash, 2,400 prompts. Chinese
    has no charge ratings and is not run here.

    **PER-LINEAGE LIFT = T_base - frame.** T_base weights scene ratings by the
    base arm's OWN mass distribution, which varies by model — two bases on the
    same prompt carry different words at different probabilities. The prompt-level
    lift (dose - frame) averages over lineages; the per-lineage version is what
    should predict each lineage's response because it is what alignment displaces.

    Lacan's [6565] flags rate_and_magnitude's language inversion as the shape
    most at risk on a saturating predictor. This re-run checks whether the
    English results survive on lift.
    """
    from malignment import ch, charge
    EP = endpoint_pairs()
    print()
    print("MAGNITUDE LIFT: same 9 outcomes regressed on per-lineage lift (en only)")
    print("unit = the lineage; slope across prompts; %d endpoint pairs" % len(EP))
    print("lift = T_base - frame (per lineage, not averaged)")

    rows = ch.query(
        "SELECT base, aligned, prompt, "
        "sumIf(p_base - p_aligned, cls='faller') AS dep, "
        "sumIf(p_aligned - p_base, cls='riser') AS arr, count() AS nm, "
        "countIf(cls='faller') AS nf, countIf(cls='riser') AS nr, "
        "sum(p_base) AS sb, sum(p_aligned) AS sa, "
        "sumIf(p_base, cls='faller') AS fb "
        "FROM movement WHERE cls != 'still' GROUP BY base, aligned, prompt")
    mag = {}
    base_of = {}
    for r in rows:
        lin = r["base"] + ">" + r["aligned"]
        if lin in EP:
            mag[(lin, r["prompt"])] = (float(r["dep"]), float(r["arr"]),
                                       int(r["nm"]), int(r["nf"]), int(r["nr"]),
                                       int(r["nf"]) - int(r["nr"]),
                                       (float(r["dep"]) / int(r["nf"])) if int(r["nf"]) else None,
                                       (float(r["arr"]) / int(r["nr"])) if int(r["nr"]) else None,
                                       _tail_excess(float(r["sb"]), float(r["sa"]),
                                                    float(r["dep"]), float(r["fb"])))
            base_of[lin] = r["base"]

    all_lifts = charge.lifts_per_lineage()
    n_lift = 0
    print()
    print("  %-10s %4s %12s %8s %10s" % ("outcome", "n", "med slope", "up/dn", "p"))
    for j, nm in ((0, "departed"), (1, "arrived"), (2, "n_movers"),
                  (3, "n_fallers"), (4, "n_risers"), (5, "n_fall-n_rise"),
                  (6, "mass/faller"), (7, "mass/riser"), (8, "tail_excess")):
        by = collections.defaultdict(lambda: ([], []))
        for (lin, pr), m in mag.items():
            base = base_of.get(lin)
            if not base:
                continue
            lft = all_lifts.get((pr, base))
            if lft is None or m[j] is None:
                continue
            by[lin][0].append(lft)
            by[lin][1].append(float(m[j]))
            if j == 0:
                n_lift += 1
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
            print("  %-10s %4d %+12.5f %4d/%-4d %10.6f%s"
                  % (nm, n, med, up, dn, p_, "  <-" if p_ < 0.05 else ""))
    print("\n  %d (lineage, prompt) pairs with per-lineage lift" % n_lift)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--lift", action="store_true",
                    help="re-run on charge.lift instead of k_transgressiveness (en only)")
    a = ap.parse_args(argv)
    if a.lift:
        return measure_lift()
    return measure([a.lang] if a.lang else ["en", "zh"])


if __name__ == "__main__":
    sys.exit(main())
