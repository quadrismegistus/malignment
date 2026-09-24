"""An interval on the affect-intensity null. -> results/departing_arriving_ci.json, .md

    python -u departing_arriving_ci.py

The paper seat's check (2), 2026-09-24, post hoc: `departing_arriving.json` has
k_charge at +0.007 (24/50 below zero) against v6:harm at -0.1635, and the paper
wants "intensity moves a small fraction as far as harm" as a BOUND, which needs
an interval rather than a p-value.

SAME POPULATION AND STATISTIC AS `departing_arriving.py`: per lineage, arriving
minus departing mass-weighted profile, English, 50 endpoint lineages; the
per-lineage values come from its own `compute()`, not a re-implementation.

TWO BOOTSTRAPS, 10,000 resamples each, seed 20260924, percentile 95% intervals:

    lineage   resample the 50 lineages with replacement (the published unit)
    cluster   resample the SFT clusters of `instrument_calibrations/
              lineage_clusters/clusters.py` with replacement, taking every
              lineage in a drawn cluster (correlated lineages move together)

Statistics, each recomputed inside every resample:

    median(scale)                     for k_charge, inst:arousal, warriner_arousal
    median(scale) / |median(v6:harm)| the fraction-of-harm the paper quotes;
                                      numerator and anchor from the SAME resample
    the 95th percentile of |ratio|    the one-sided bound: "at most X% as far"

All three scales and v6:harm are rated 1-7, so the ratio is in like units. It
does compare a type-level norm (k_charge, warriner) or a contextual one
(inst:arousal) against a contextual anchor, which is the published choice.
"""
import collections, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "experiments", "instrument_calibrations", "lineage_clusters"))
import departing_arriving as DA  # noqa: E402
import clusters  # noqa: E402

SCALES = ["k_charge", "inst:arousal", "warriner_arousal"]
ANCHOR = DA.ANCHOR
B = 10000
SEED = 20260924
OUT = os.path.join(HERE, "results", "departing_arriving_ci")


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def pct(v, q):
    s = sorted(v)
    i = q * (len(s) - 1)
    lo = int(i)
    return s[lo] + (s[min(lo + 1, len(s) - 1)] - s[lo]) * (i - lo)


def main():
    from malignment import roster
    eps, _ = roster.endpoints()
    key = {b: "%s>%s" % (b, a) for b, a in eps.items()}
    res, _cons, per = DA.compute()
    per = {s: {key[b]: v for b, v in per[s].items()} for s in SCALES + [ANCHOR]}
    lineages = sorted(set.intersection(*[set(per[s]) for s in SCALES + [ANCHOR]]))
    grp = clusters.grouping("SFT", set(key.values()))
    members = collections.defaultdict(list)
    for k in lineages:
        members[grp[k]].append(k)
    units = {"lineage": [[k] for k in lineages], "cluster": list(members.values())}
    rnd = random.Random(SEED)
    out = {"population": "%d English endpoint lineages carrying all four scales; %d SFT clusters"
                         % (len(lineages), len(members)),
           "anchor": ANCHOR, "anchor_median": median([per[ANCHOR][k] for k in lineages]),
           "B": B, "seed": SEED, "scales": {}}
    for s in SCALES:
        point = median([per[s][k] for k in lineages])
        row = {"median": point, "ratio": point / abs(out["anchor_median"])}
        for u, pool in units.items():
            meds, ratios = [], []
            for _ in range(B):
                draw = [k for _i in range(len(pool)) for k in rnd.choice(pool)]
                m = median([per[s][k] for k in draw])
                a = median([per[ANCHOR][k] for k in draw])
                meds.append(m)
                ratios.append(m / abs(a))
            row[u] = {"median_ci": [pct(meds, 0.025), pct(meds, 0.975)],
                      "ratio_ci": [pct(ratios, 0.025), pct(ratios, 0.975)],
                      "abs_ratio_95": pct([abs(r) for r in ratios], 0.95)}
        out["scales"][s] = row
    json.dump(out, open(OUT + ".json", "w"), indent=1)
    L = ["# An interval on the affect-intensity null", "",
         "Producer `departing_arriving_ci.py` (paper seat's check 2, 2026-09-24, post hoc). %s. "
         "Per-lineage values from `departing_arriving.compute()`. Anchor %s, median %+.4f. "
         "%d resamples, percentile 95%% intervals." % (out["population"], ANCHOR, out["anchor_median"], B), "",
         "| scale | median | lineage 95% CI | cluster 95% CI | ratio to |harm| | lineage ratio CI | cluster ratio CI | |ratio| 95th pct, lineage / cluster |",
         "|---|---|---|---|---|---|---|---|"]
    for s, r in out["scales"].items():
        L.append("| %s | %+.4f | [%+.4f, %+.4f] | [%+.4f, %+.4f] | %+.1f%% | [%+.1f%%, %+.1f%%] | [%+.1f%%, %+.1f%%] | %.1f%% / %.1f%% |" % (
            s, r["median"], *r["lineage"]["median_ci"], *r["cluster"]["median_ci"], 100 * r["ratio"],
            *[100 * x for x in r["lineage"]["ratio_ci"]], *[100 * x for x in r["cluster"]["ratio_ci"]],
            100 * r["lineage"]["abs_ratio_95"], 100 * r["cluster"]["abs_ratio_95"]))
    L += ["", "Ratio = median(scale) / |median(%s)| within each resample; negative means the scale fell "
          "(the same direction as harm)." % ANCHOR]
    open(OUT + ".md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
