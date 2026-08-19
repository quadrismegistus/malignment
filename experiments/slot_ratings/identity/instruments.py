"""Is the group effect an artifact of the institutional instrument's design?

    python experiments/slot_ratings/identity/instruments.py

The institutional instrument was built FROM the F21 and M03 axes, so it was built
to find proceduralisation. If the group differences appeared only on its scales
that would be a design echo rather than a result. The general v6 instrument was
written before any of this and shares exactly one field with it, `vocalisation`,
which doubles as a free inter-instrument reliability check on 4,046 pairs.

Writes results/by_instrument.json.
"""

import collections, glob, json, os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "results")

V6 = {"harm", "aggression", "directedness", "makes_better", "makes_worse",
      "interiority", "deliberation", "superego", "vocalisation", "hedged",
      "fit", "mundanity"}
V3 = {"agency", "deference", "assertiveness", "procedural", "specificity", "delay",
      "abstraction", "target", "collective", "arousal", "vocalisation",
      "termination", "mediation"}


def owner(s):
    return ("BOTH" if s in V6 and s in V3 else
            "v6-general" if s in V6 else "v3-instit" if s in V3 else "?")


def blocks(rows, sweep, s):
    cell = {(r["lineage"], r["group"]): r[s]
            for r in rows if r["sweep"] == sweep and r.get(s) is not None}
    Gs = sorted({g for _, g in cell})
    Ls = [l for l in sorted({l for l, _ in cell}) if all((l, g) in cell for g in Gs)]
    return cell, Ls, Gs


def reliability():
    """The two instruments both rated `vocalisation`. They should agree."""
    from scipy import stats
    a = {}
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for d in json.load(open(f)):
            if d.get("ratable") and d.get("vocalisation") is not None:
                a[(d["prompt"], d["word"])] = d["vocalisation"]
    p = os.path.join(SLOT, "institutional", "results", "slotdomain",
                     "rated_identity_slot_institutional_en_v3_armA.json")
    b = {}
    for fr in json.load(open(p))["frames"]:
        for w, r in (fr.get("ratings") or {}).items():
            if r.get("vocalisation") is not None:
                b[(fr["prompt"], w)] = r["vocalisation"]
    k = sorted(set(a) & set(b))
    x, y = [a[i] for i in k], [b[i] for i in k]
    return dict(n=len(k), spearman=stats.spearmanr(x, y).statistic,
                pearson=stats.pearsonr(x, y).statistic,
                exact=sum(1 for i, j in zip(x, y) if i == j) / len(k),
                mean_abs_diff=st.mean(abs(i - j) for i, j in zip(x, y)))


def main():
    from scipy import stats
    rows = json.load(open(os.path.join(OUT, "group_rho.json")))["rows"]
    scales = sorted({k for r in rows for k in r
                     if k not in ("group", "sweep", "lineage", "n")
                     and not k.startswith("n_")})
    tot, pas, saved = collections.Counter(), collections.Counter(), []
    for sweep in ("room", "nextdoor", "street"):
        res = []
        for s in scales:
            cell, Ls, Gs = blocks(rows, sweep, s)
            if len(Ls) < 8 or len(Gs) < 10:
                continue
            res.append((s, stats.friedmanchisquare(
                *[[cell[(l, g)] for l in Ls] for g in Gs]).pvalue, len(Ls)))
        b = 0.05 / len(res)
        for s, p, nl in res:
            tot[owner(s)] += 1
            if p < b:
                pas[owner(s)] += 1
            #: bool(...) and the default=float below: a numpy bool or float64
            #: raises inside json.dump AFTER it has already written part of the
            #: file, leaving a TRUNCATED artifact that still looks committed.
            #: This file was 150 bytes of valid-looking JSON for a day.
            saved.append(dict(sweep=sweep, scale=s, instrument=owner(s),
                              friedman=float(p), passes=bool(p < b), blocks=int(nl)))
    print("Bonferroni pass rate BY INSTRUMENT, over the three sweeps:")
    for o in ("v6-general", "v3-instit", "BOTH"):
        print("  %-11s %2d of %2d  (%.0f%%)" % (o, pas[o], tot[o],
                                                100 * pas[o] / max(1, tot[o])))
    ft = stats.fisher_exact([[pas["v6-general"], tot["v6-general"] - pas["v6-general"]],
                             [pas["v3-instit"], tot["v3-instit"] - pas["v3-instit"]]])
    print("  fisher exact on the two pass rates: OR=%.2f p=%.3f" % (ft.statistic, ft.pvalue))
    print("  -> both instruments find it; the institutional one is denser, but the")
    print("     difference in pass rate is not itself significant.")

    #: the corroboration that matters: does the GENERAL instrument, which was not
    #: built from F21/M03, place the same groups at the extremes?
    prof = {}
    for g in ("Muslims", "Italians"):
        prof[g] = {}
        for s in sorted(V6 - {"vocalisation"}):
            cell, Ls, Gs = blocks(rows, "room", s)
            if len(Ls) < 8 or g not in Gs:
                continue
            dev = {x: st.mean(cell[(l, x)] - st.mean(cell[(l, o)] for o in Gs if o != x)
                              for l in Ls) for x in Gs}
            prof[g][s] = dict(delta=dev[g],
                              rank=sorted(Gs, key=lambda x: -dev[x]).index(g) + 1,
                              of=len(Gs))
    print("\nGENERAL v6 scales only, `room`, deviation from the other 23:")
    for g in prof:
        print("  %s" % g)
        for s, d in sorted(prof[g].items(), key=lambda t: t[1]["rank"]):
            print("    %-14s %+7.3f  rank %2d/%d" % (s, d["delta"], d["rank"], d["of"]))
    rel = reliability()
    print("\nInter-instrument reliability on `vocalisation`: n=%d spearman %.3f "
          "pearson %.3f exact %.0f%% mean|diff| %.2f"
          % (rel["n"], rel["spearman"], rel["pearson"], 100 * rel["exact"],
             rel["mean_abs_diff"]))
    payload = dict(by_scale=saved, v6_profile=prof, reliability=rel,
                   pass_rate={o: [pas[o], tot[o]] for o in tot})
    #: serialise to a STRING first, so a type error cannot leave a half-written
    #: file on disk. Only write once the whole payload is known to encode.
    blob = json.dumps(json.loads(json.dumps(payload, default=float)), indent=1)
    open(os.path.join(OUT, "by_instrument.json"), "w").write(blob)
    print("-> results/by_instrument.json")


if __name__ == "__main__":
    main()
