"""The (lineage, prompt-cluster) cell as the unit: both variances at once.

    python experiments/slot_ratings/institutional/crossed.py

`base_side_positions.py` makes the LINEAGE the unit and averages prompts away.
`unit_check.py` makes the PROMPT SIDE the unit and averages lineages away. Each
is blind to the variance the other tests, and the corpus has both: 50 lineages
crossed with a set of prompts, every lineage seeing every prompt.

This tests the position effect against BOTH at once, on the (lineage, cluster)
cell, by a two-way cluster bootstrap: resample lineages with replacement AND
clusters with replacement, recompute the mean gap, 2,000 times. A cell's
contribution survives only if it is stable to reshuffling models and prompts
together, which is the property neither marginal test checks.

## THE CLUSTER IS THE MATCHED UNIT, AND IT DIFFERS BY CORPUS

    M03      scenario x stratum = 126 matched pairs. Position varies WITHIN a
             cluster holding scene, person and modal fixed. This is the strong
             design, and unit_check.py wasted it by collapsing to the 7 strata.
    slotpov  6 matched sets. Position varies within, site identical.
    F21      NO pairing. Position varies BETWEEN prompts, so the cluster is the
             prompt and indiv/inst prompts are resampled separately. Weakest.

Writes results/base_side/crossed.json.
"""

import collections, json, os, random
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "base_side")
REPS = 2000
SEED = 20260819


def cells(rows, scale, arm):
    """gap per (lineage, cluster), or per (lineage, position-side) when unpaired."""
    lvl = {}
    for r in rows:
        v = r.get("%s_%s" % (arm, scale))
        if v is not None:
            lvl.setdefault((r["lineage"], r["cluster"], r["position"]), []).append(v)
    lvl = {k: st.mean(v) for k, v in lvl.items()}
    paired = collections.defaultdict(dict)
    for (lin, cl, pos), v in lvl.items():
        paired[(lin, cl)][pos] = v
    both = {k: v["inst"] - v["indiv"] for k, v in paired.items()
            if "inst" in v and "indiv" in v}
    if both:
        return "paired", both
    #: unpaired: keep the sides separate, resample each independently
    return "unpaired", lvl


def boot(kind, data, rng):
    if kind == "paired":
        lins = sorted({l for l, _ in data})
        cls = sorted({c for _, c in data})
        obs = st.mean(data.values())
        reps = []
        for _ in range(REPS):
            L = [rng.choice(lins) for _ in lins]
            C = [rng.choice(cls) for _ in cls]
            vals = [data[(l, c)] for l in L for c in C if (l, c) in data]
            if vals:
                reps.append(st.mean(vals))
        return obs, reps, len(lins), len(cls)
    lins = sorted({k[0] for k in data})
    byside = collections.defaultdict(list)
    for (l, c, pos) in data:
        byside[pos].append(c)
    ci = sorted(set(byside["indiv"])); cn = sorted(set(byside["inst"]))
    def mean_gap(L, A, B):
        a = [data[(l, c, "inst")] for l in L for c in B if (l, c, "inst") in data]
        b = [data[(l, c, "indiv")] for l in L for c in A if (l, c, "indiv") in data]
        return (st.mean(a) - st.mean(b)) if a and b else None
    obs = mean_gap(lins, ci, cn)
    reps = []
    for _ in range(REPS):
        g = mean_gap([rng.choice(lins) for _ in lins],
                     [rng.choice(ci) for _ in ci], [rng.choice(cn) for _ in cn])
        if g is not None:
            reps.append(g)
    return obs, reps, len(lins), len(ci) + len(cn)


def main():
    saved = {}
    for c in ("f21", "m03", "slotpov"):
        p = os.path.join(OUT, "%s.json" % c)
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        rows, res = d["rows"], d["results"]
        if "cluster" not in rows[0]:
            print("%s: rows predate the cluster field; rerun base_side_positions.py" % c)
            continue
        byscale = {r["scale"]: r for r in res}
        print("\n" + "=" * 96)
        print("%s: two-way cluster bootstrap, %d reps" % (c.upper(), REPS))
        out = []
        for s in [r["scale"] for r in res]:
            for arm in ("base", "delta"):
                if arm == "base":
                    kind, data = cells(rows, s, "base")
                else:
                    kb, db = cells(rows, s, "base")
                    ka, da = cells(rows, s, "aligned")
                    if kb != ka:
                        continue
                    if kb == "paired":
                        data = {k: da[k] - db[k] for k in da if k in db}
                    else:
                        data = {k: da[k] - db[k] for k in da if k in db}
                    kind = kb
                if not data:
                    continue
                rng = random.Random(SEED)
                obs, reps, nl, nc = boot(kind, data, rng)
                if not reps or obs is None:
                    continue
                lo, hi = sorted(reps)[int(.025 * len(reps))], sorted(reps)[int(.975 * len(reps))]
                #: two-sided bootstrap p: how often the resampled mean crosses 0
                frac = sum(1 for r in reps if (r > 0) != (obs > 0)) / len(reps)
                out.append(dict(scale=s, arm=arm, kind=kind, obs=obs, lo=lo, hi=hi,
                                p=min(1.0, 2 * frac), n_lineages=nl, n_clusters=nc))
        print("   design: %s | %d lineages x %d clusters"
              % (out[0]["kind"], out[0]["n_lineages"], out[0]["n_clusters"]))
        print("\n   %-14s %9s %9s %19s %8s | %9s %8s | %s"
              % ("scale", "lin-only p", "unit p", "crossed gap [95% CI]", "p", "delta", "p", "survives"))
        for s in [r["scale"] for r in res]:
            b = next((o for o in out if o["scale"] == s and o["arm"] == "base"), None)
            dl = next((o for o in out if o["scale"] == s and o["arm"] == "delta"), None)
            if not b:
                continue
            L = byscale[s]
            print("   %-14s %9.1e %9s %+7.3f [%+6.3f,%+6.3f] %8.3f | %+9.3f %8.3f | %s"
                  % (s, L["p_base"], "-", b["obs"], b["lo"], b["hi"], b["p"],
                     dl["obs"] if dl else float("nan"), dl["p"] if dl else float("nan"),
                     "BASE" if b["p"] < .05 else ""))
        saved[c] = out
    json.dump(saved, open(os.path.join(OUT, "crossed.json"), "w"), indent=1)
    print("\n-> results/base_side/crossed.json")


if __name__ == "__main__":
    main()
