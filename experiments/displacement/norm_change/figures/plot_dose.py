"""Dose-response: does base-arm transgressive mass predict what alignment changes?

    python plot_dose.py

Per lineage, OLS slope of (aligned - base) on base k_transgressiveness across
prompts. One dot per lineage (n=50), one panel per target scale. A slope to the
left of zero means the scale FALLS more where the frame is more transgressive;
to the right means it RISES more. The vertical line is zero; the distribution
should sit one side of it if the dose predicts the direction.

## WHICH SCALES AND WHY

The panel shows scales chosen for INTERPRETABILITY relative to the taxonomy, not
for p-value:

    k_bodily_harm      the harm content -- does it fall where the frame is loaded?
    k_register_level   register -- does formality rise more at loaded frames?
    k_valence          valence -- does sweetening concentrate at loaded frames?
    k_concreteness     concreteness -- does abstraction concentrate?
    k_vulgarity        vulgarity -- does profanity fall where the frame is loaded?
    warriner_valence   human valence norm, for cross-instrument confirmation
    warriner_arousal   arousal -- does calm rise more at loaded frames?

These cover the taxonomy's three main operation types: displacement (harm,
vulgarity fall), attenuation (valence, register rise), and the concreteness
asymmetry (falls in Chinese, dose-dependent in English).
"""
import collections
import gzip
import math
import os
import statistics
import sys

import plotnine as p9
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "..", "..", ".."))
DATA = os.path.expanduser("~/malignment-data/norm_change")

DOSE = "k_transgressiveness"
TARGETS = [
    ("k_bodily_harm", "bodily harm"),
    ("k_vulgarity", "vulgarity"),
    ("k_concreteness", "concreteness"),
    ("warriner_arousal", "arousal"),
    ("k_register_level", "register level"),
    ("k_valence", "valence (k)"),
    ("warriner_valence", "valence (Warriner)"),
]
MIN_PROMPTS = 25
LANG = "en"
W, H = 10, 5.5


def endpoint_pairs():
    from malignment import roster
    ep, _ = roster.endpoints()
    return {"%s>%s" % (k, v) for k, v in ep.items()}


def slope(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def load():
    EP = endpoint_pairs()
    keep = {DOSE} | {t for t, _ in TARGETS}
    by = collections.defaultdict(dict)
    dose_by = collections.defaultdict(dict)
    p = os.path.join(DATA, "levels_long.csv.gz")
    with gzip.open(p, "rt") as fh:
        head = fh.readline().strip().split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.strip().split("\t")
            if len(v) != len(head):
                continue
            if v[ix["lang"]] != LANG:
                continue
            sc = v[ix["scale"]]
            if sc not in keep:
                continue
            b, a = v[ix["base_level"]], v[ix["aligned_level"]]
            if not b or not a or b == "\\N" or a == "\\N":
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in EP:
                continue
            pr = v[ix["prompt"]]
            try:
                bf, af = float(b), float(a)
            except ValueError:
                continue
            if sc == DOSE:
                dose_by[lin][pr] = bf
            else:
                by[(sc, lin)][pr] = af - bf
    return by, dose_by


def compute():
    by, dose_by = load()
    rows = []
    stats = {}
    for target, label in TARGETS:
        slopes = []
        for lin in sorted(dose_by):
            xs, ys = [], []
            for pr, d in dose_by[lin].items():
                delta = by.get((target, lin), {}).get(pr)
                if delta is not None:
                    xs.append(d)
                    ys.append(delta)
            if len(xs) < MIN_PROMPTS:
                continue
            s = slope(xs, ys)
            if s is not None:
                slopes.append(s)
                rows.append({"scale": label, "lineage": lin, "slope": s})
        up = sum(1 for s in slopes if s > 0)
        dn = sum(1 for s in slopes if s < 0)
        n = up + dn
        pv = binom(up, n)
        med = statistics.median(slopes) if slopes else 0
        stats[label] = {"up": up, "dn": dn, "n": n, "p": pv, "med": med}
        print("  %-22s  med %+.4f  %2d up / %2d dn  p=%.5f%s"
              % (label, med, up, dn, pv, "  *" if pv < 0.05 else ""))
    return pd.DataFrame(rows), stats


def pfmt(pv):
    if pv < 0.0001:
        return "p < 0.0001"
    if pv < 0.01:
        return "p = %.4f" % pv
    return "p = %.2f" % pv


FIGURES = {"dose_response_en": None}


def draw(df, stats):
    order = [label for _, label in TARGETS]
    df["scale"] = pd.Categorical(df["scale"], categories=order, ordered=True)
    ann = []
    for label in order:
        s = stats[label]
        sig = s["p"] < 0.05
        ann.append({"scale": label,
                    "label": "%d / %d  %s" % (s["up"], s["n"], pfmt(s["p"])),
                    "sig": sig})
    ann_df = pd.DataFrame(ann)
    ann_df["scale"] = pd.Categorical(ann_df["scale"], categories=order, ordered=True)

    med_df = (df.groupby("scale", observed=True)["slope"]
              .median().reset_index())
    med_df["scale"] = pd.Categorical(med_df["scale"], categories=order, ordered=True)

    xmin = df["slope"].quantile(0.005)
    xmax = df["slope"].quantile(0.995)
    pad = (xmax - xmin) * 0.15
    xlim = (xmin - pad, xmax + pad * 2.5)

    fig = (
        p9.ggplot(df, p9.aes(x="slope", y="scale"))
        + p9.geom_vline(xintercept=0, color="#aaaaaa", linetype="dashed", size=0.4)
        + p9.geom_jitter(height=0.18, size=1.3, alpha=0.45, color="#4e79a7")
        + p9.geom_point(data=med_df,
                        mapping=p9.aes(x="slope", y="scale"),
                        shape="D", size=3.5, color="#e15759", fill="#e15759")
        + p9.geom_text(data=ann_df,
                       mapping=p9.aes(y="scale", label="label"),
                       x=xlim[1] - pad * 0.3, ha="right", size=7, color="#555555")
        + p9.scale_x_continuous(limits=xlim)
        + p9.labs(
            title="Dose-response: base-arm transgressive mass predicts alignment's effect",
            subtitle=("Per lineage (n = 50), OLS slope of (aligned minus base) on base k_transgressiveness. Red diamond = median.\n"
                      "Register level rises marginally (45/50) but shows no dose dependence (p = 0.67)."),
            x="slope (positive = scale rises more at transgressive frames)",
            y="")
        + p9.theme_minimal()
        + p9.theme(figure_size=(W, H),
                   plot_title=p9.element_text(size=11, weight="bold"),
                   plot_subtitle=p9.element_text(size=7.5, color="#444444"),
                   axis_text_y=p9.element_text(size=9))
    )
    out = os.path.join(HERE, "dose_response_en.png")
    fig.save(out, dpi=300, verbose=False)
    print("\n  saved %s" % out)
    return fig


if __name__ == "__main__":
    print("loading levels_long (~15M rows, en only, 8 scales)...")
    df, stats = compute()
    print("\ndrawing...")
    draw(df, stats)
