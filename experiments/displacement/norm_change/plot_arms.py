"""kill -> scream, SCALED UP: every norm's mass-weighted level, base to aligned.

    python -u plot_arms.py --pub

The single-prompt slopegraph shows one substitution. This is the same picture
over 50 endpoint lineages and ~2.4M (lineage, prompt, scale) rows: for each
arm, the mass-weighted mean of a word norm over what the model is about to say.
`kill -> scream` IS a fall in bodily harm and vulgarity with a rise in register,
so if that substitution generalises these are the lines that must move.

## READS `levels_long_v4`, COMPUTES NO NORM

`base_level` / `aligned_level` were computed by `run.py` and live in
`~/malignment-data/norm_change` (3.0 GB, outside the checkout). This file
aggregates and draws. A second implementation of a norm is how two figures end
up disagreeing under one name.

## THE POPULATION IS 50, NOT 132

`levels_long_v4` carries every edge in `movement` -- 132 of them here, including
rungs and transitive pairs -- and the README is explicit that the unit is
`roster.endpoints()`, "NOT the 153 edges ... which would let one base model vote
eleven times". Filtered to the declared 50. Unfiltered, `k_bodily_harm` reads
14/118 instead of 4/46: the direction survives, the counts do not.

## THE DELTA HERE IS NOT THE README'S DELTA

`norm_stats.json` takes, per lineage, the MEDIAN OVER PROMPTS of
`(aligned - base)` -- paired within prompt. This takes median(base) and
median(aligned) separately, because a slopegraph must draw two levels and a
paired median is not the difference of two drawable numbers. The counts agree
closely (register 46/4 here against 45/4 there) and the levels are what this
figure is for, but **the two deltas are different statistics and must not be
quoted for each other.**
"""
import argparse, collections, gzip, json, math, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
FIGURES = os.path.join(HERE, "figures")
CACHE = os.path.join(HERE, "results", "arm_levels_en.json")
#: the five with a direction the substitution predicts, plus valence
WANT = {"k_transgressiveness", "k_charge", "k_bodily_harm", "k_vulgarity",
        "k_register_level", "k_valence", "k_concreteness"}
SHOW = ["k_bodily_harm", "k_vulgarity", "k_transgressiveness",
        "k_concreteness", "k_register_level"]


def sign_p(k, n):
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1))
               / 2.0 ** n) if n else float("nan")


def build_cache(out=CACHE):
    """Rebuild `results/arm_levels_en.json` from the long table. -> path

    **A CACHE WITHOUT A PRODUCER IS AN ORPHAN.** This file read a JSON that
    nothing in the repo could regenerate, which is the same defect as a figure
    whose producer lives in a transcript. Streams
    `~/malignment-data/norm_change/levels_long_v4.csv.gz` (938 MB, 14.4M rows,
    ~90 s) and keeps only the 50 declared endpoint lineages -- the file carries
    132 edges including rungs and transitive pairs, and the README is explicit
    that using them lets one base model vote eleven times.
    """
    import gzip
    from malignment import roster
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, a) for b, a in eps.items()}
    src = os.path.expanduser("~/malignment-data/norm_change/levels_long_v4.csv.gz")
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    with gzip.open(src, "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ix["lang"]] != "en" or f[ix["scale"]] not in WANT:
                continue
            lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
            if lin not in keep:
                continue
            try:
                acc[f[ix["scale"]]][lin].append((float(f[ix["base_level"]]),
                                                 float(f[ix["aligned_level"]])))
            except ValueError:
                pass
    per_scale = {}
    for sc, by in acc.items():
        per_scale[sc] = [{"lineage": l, "n_prompts": len(v),
                          "base": st.median(x for x, _ in v),
                          "aligned": st.median(y for _, y in v)}
                         for l, v in by.items()]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"source": "levels_long_v4.csv.gz", "lang": "en",
               "population": "roster.endpoints(), 50 declared pairs",
               "per_scale": per_scale}, open(out, "w"), indent=1)
    return out


def draw(d, out_path, pub=False, scales=None):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd, random
    from plotnine import (ggplot, aes, geom_line, geom_point, geom_errorbar,
                          labs, scale_x_continuous, facet_wrap, theme_minimal,
                          theme, element_text, ggtitle)
    from malignment.figure import PUB_RED, PUB_RULE_PT, pub_theme

    rng = random.Random(17)
    def ci(v):
        bs = sorted(st.median([v[rng.randrange(len(v))] for _ in v])
                    for _ in range(3000))
        return st.median(v), bs[int(.025 * len(bs))], bs[int(.975 * len(bs)) - 1]

    scales = scales or SHOW
    rows = []
    for sc in scales:
        per = d["per_scale"][sc]
        dl = [r["aligned"] - r["base"] for r in per]
        dn = sum(1 for x in dl if x < 0)
        #: the panel strip carries the COUNT and the p, because a slope drawn
        #: without them looks like one measurement rather than 50 agreeing
        #: **THE STRIP CARRIES THE NAME ONLY.** It used to carry the count and
        #: the p as well, and at 4.8 inches five of those overprint each other
        #: into an unreadable band -- a caption line that costs the figure its
        #: labels belongs in the caption. The producer prints them.
        lab = sc.replace("k_", "").replace("_", " ")
        for pos, arm in ((0, "base"), (1, "aligned")):
            m, lo, hi = ci([r[arm] for r in per])
            rows.append({"x": pos, "y": m, "lo": lo, "hi": hi, "scale": lab})
    f = pd.DataFrame(rows)
    p = (ggplot(f, aes("x", "y"))
         + geom_line(size=0.9, color=PUB_RED)
         + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.06,
                         size=PUB_RULE_PT, color=PUB_RED)
         + geom_point(size=1.1, color=PUB_RED)
         #: FREE y. The norms live on different scales (1.03 against 3.94) and
         #: a shared axis would flatten every one of them to a horizontal line.
         #: THREE ACROSS, NOT FIVE. Five panels across a 4.8 in block leaves
         #: ~0.9 in each, where "Base" and "Aligned" collide at 9 pt.
         + facet_wrap("~scale", scales="free_y", ncol=3)
         + scale_x_continuous(breaks=[0, 1], labels=["Base", "Aligned"],
                              limits=(-0.25, 1.25))
         + labs(x="", y="Mass-weighted mean of the norm"))
    p = p + (pub_theme(height=3.6) if pub else
             (ggtitle("Norm levels, 50 endpoint lineages")
              + theme_minimal() + theme(figure_size=(11, 3.4),
                                        plot_title=element_text(size=11, weight="bold"))))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    p.save(out_path, dpi=300, verbose=False)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true",
                    help="rebuild results/arm_levels_en.json from the 938 MB "
                         "long table first (~90 s)")
    ap.add_argument("--pub", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.build or not os.path.exists(CACHE):
        print("building %s ..." % CACHE, flush=True)
        build_cache()
    d = json.load(open(CACHE))
    print("population: %s" % d.get("population"))
    for sc in SHOW:
        per = d["per_scale"][sc]
        dl = [r["aligned"] - r["base"] for r in per]
        dn = sum(1 for x in dl if x < 0)
        print("  %-22s %8.4f -> %8.4f  %+9.5f  %2d/%d down  p=%.1e"
              % (sc, st.median([r["base"] for r in per]),
                 st.median([r["aligned"] for r in per]), st.median(dl),
                 dn, len(per), sign_p(min(dn, len(per) - dn), len(per))))
    out = a.out or os.path.join(FIGURES, "norm_arms%s.png" % ("_pub" if a.pub else ""))
    print("\nwrote %s" % draw(d, out, pub=a.pub))


if __name__ == "__main__":
    main()
