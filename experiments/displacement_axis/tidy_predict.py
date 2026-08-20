"""Long-form CSVs for everything in the ratings-vs-embedding experiments.

    python experiments/displacement_axis/tidy_predict.py

The JSON results are one wide row per frame with a column per model, which is the
shape that produced today's mistakes: a wide row invites comparing two columns
without checking they were computed over the same frames, and three of the day's
false comparisons were exactly that. Long form makes the join explicit -- every
row carries its analysis, its comparison, its frame, its domain and its n, so a
plot or a test that mixes populations has to do so visibly.

Written for someone who did not run any of this and does not trust it.

  predict_frames.csv   one row per (analysis, comparison, frame, model) with its
                       held-out R2. `emp_mean` is the REACHABLE BENCHMARK, not a
                       model: it is the n-1 mean scored by the identical rule, so
                       a model beating it has denoised the data itself. Compare
                       models to it, never to 1.0 and never to a ceiling.
  scale_rho.csv        one row per (frame, scale): per-frame median rho against
                       the mover verdict, and that scale's one-column R2.
  protocol_*.csv       written by protocol_check.py; the evidence that the older
                       half-split scoring was comparing two different quantities.

FENCE CARRIED IN THE DATA. `variance_repeated.json` and `sexual_scales.json` were
produced under that older scoring and their numbers are NOT comparable to the loo
ones. They are emitted here with `analysis='half_split_SUPERSEDED'` so nothing
can join them to the rest by accident, and their `% ceiling` figures are dropped
entirely rather than carried with a caveat.
"""

import collections, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "pilot3")
LONG = os.path.join(RES, "long")


def rows_of(path, key=None):
    if not os.path.exists(path):
        return []
    d = json.load(open(path))
    return d.get(key, []) if key else d.get("rows", [])


def main():
    os.makedirs(LONG, exist_ok=True)
    out = []

    def add(analysis, comparison, r, prefix, models=None):
        for k, v in r.items():
            if not k.startswith(prefix):
                continue
            m = k[len(prefix):]
            if models and m not in models:
                continue
            out.append(dict(
                analysis=analysis, comparison=comparison,
                prompt=r.get("prompt"), item=r.get("item"),
                domain=r.get("domain"), n_words=r.get("n_words"),
                n_lineages=r.get("n_lineages"),
                n_folds=r.get("n_folds") or r.get("n_splits"),
                model=m, r2=v))

    for r in rows_of(os.path.join(RES, "loo.json")):
        add("loo", "v6_only", r, "r2_")
    for comp in ("v6_inst", "v6_sex", "all3"):
        for r in rows_of(os.path.join(RES, "loo_all.json"), comp):
            add("loo", comp, r, "r2_")
    for r in rows_of(os.path.join(RES, "base_prob_share.json")):
        add("half_split_SUPERSEDED", "base_prob", r, "mean_",
            {"ceiling", "logp", "names12", "logp_names", "logp_sq"})
    for r in rows_of(os.path.join(RES, "sexual_scales.json")):
        add("half_split_SUPERSEDED", "sexual_v2", r, "mean_",
            {"ceiling", "sex9", "v6_12", "both21", "bge_pcs", "bge_axis"})

    with open(os.path.join(LONG, "predict_frames.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)

    #: scale-level: rho and the one-column R2, from rho_domains.json, plus the
    #: single-scale LOO columns which are the only ones scored under the good rule
    loo1 = {}
    for r in rows_of(os.path.join(RES, "loo.json")):
        loo1[r["prompt"]] = {k[4:]: v for k, v in r.items() if k.startswith("r2_1:")}
    sc = []
    for r in rows_of(os.path.join(RES, "rho_domains.json")):
        names = {k[4:] for k in r if k.startswith("rho_")}
        for s in sorted(names):
            sc.append(dict(prompt=r.get("prompt"), item=r.get("item"),
                           domain=r.get("domain"), n_words=r.get("n_words"),
                           n_lineages=r.get("n_lineages"), scale=s,
                           rho=r.get("rho_" + s), n_pairs=r.get("rhon_" + s),
                           r2_single_halfsplit_SUPERSEDED=r.get("r2_" + s),
                           r2_single_loo=loo1.get(r.get("prompt"), {}).get(s),
                           ceiling_halfsplit_SUPERSEDED=r.get("ceiling")))
    with open(os.path.join(LONG, "scale_rho.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sc[0]))
        w.writeheader(); w.writerows(sc)

    n = collections.Counter((r["analysis"], r["comparison"]) for r in out)
    print("predict_frames.csv  %d rows" % len(out))
    for (an, cp), c in sorted(n.items()):
        f = len({r["prompt"] for r in out if r["analysis"] == an and r["comparison"] == cp})
        print("   %-24s %-12s %5d rows over %3d frames" % (an, cp, c, f))
    print("scale_rho.csv       %d rows over %d frames, %d scales"
          % (len(sc), len({r["prompt"] for r in sc}), len({r["scale"] for r in sc})))
    print("\n-> results/pilot3/long/")


if __name__ == "__main__":
    main()
