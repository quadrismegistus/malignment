"""LAYER 1, fewest assumptions: per prompt, does each scale's level move?

    python experiments/slot_ratings/sexual/levels.py

Nothing is pooled, nothing is paired, gender is not used. One prompt at a time:

    base level      mass-weighted E[scale|rated] on the base arm
    aligned level   the same on the aligned arm
    delta           aligned minus base
    p               Wilcoxon signed-rank over the 33 LINEAGES of that prompt

The unit is the lineage and the test is a magnitude test on the per-lineage
delta, so what it asks is "do the models agree that this prompt's distribution
moved on this scale, and by how much". It assumes only that the lineages are
comparable observations of the same prompt.

Later layers add assumptions and are kept in separate files so it is visible
which result needs which:

    LAYER 2  pair male against female within a matched set   (assumes the pair is matched)
    LAYER 3  pool across the 8 matched sets                  (assumes the sets are comparable)
    LAYER 4  rho of rating against movement                  (assumes selection, not level)

EXCLUSIONS, the same at every layer: unratable words (705), `is_modifier` words
(164, syntagmatic per X_metonymy), and `body_distance == 0` from that scale only.
COVERAGE is printed per prompt because the level is a conditional mean over rated
words and is only as good as the share of mass those words hold.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
SCALES = ["orality", "tactility", "genitality", "incorporation", "body_distance",
          "exposure", "charge", "euphemism", "explicitness"]


def main():
    from scipy import stats
    from analyse import load, masses
    R = load()
    prompts = sorted({k[0] for k in R})
    meta = {p: (R[(p, w)]["pair"], R[(p, w)]["gender"], R[(p, w)]["role"])
            for p, w in R}
    M = masses(prompts)
    rows = []
    for p in prompts:
        lins = sorted(l for (t, l) in M if t == p)
        cov = []
        per = collections.defaultdict(lambda: {"base": [], "aligned": []})
        for l in lins:
            pb, pa = M[(p, l)]
            for arm, dist in (("base", pb), ("aligned", pa)):
                tot = sum(dist.values())
                for s in SCALES:
                    ws = [w for w in dist if (p, w) in R
                          and R[(p, w)].get(s) is not None
                          and not (s == "body_distance" and R[(p, w)][s] == 0)]
                    m = sum(dist[w] for w in ws)
                    if m <= 0 or len(ws) < 10:
                        per[s][arm].append(None); continue
                    per[s][arm].append(sum(dist[w] * R[(p, w)][s] for w in ws) / m)
                    if s == "charge" and arm == "base" and tot > 0:
                        cov.append(m / tot)
        pr, g, role = meta[p]
        print("=" * 96)
        print("  %-18s %-7s [%s]   %s ___" % (pr, g, role, p))
        print("     %d lineages | rated words hold %.1f%% of base mass (IQR %.1f-%.1f)"
              % (len(lins), 100 * st.median(cov),
                 100 * sorted(cov)[len(cov) // 4], 100 * sorted(cov)[3 * len(cov) // 4])
              if cov else "     %d lineages" % len(lins))
        print("     %-14s %8s %8s %9s %10s %8s"
              % ("scale", "base", "aligned", "delta", "p", "up/n"))
        for s in SCALES:
            d = [(a - b) for a, b in zip(per[s]["aligned"], per[s]["base"])
                 if a is not None and b is not None]
            b = [x for x in per[s]["base"] if x is not None]
            a = [x for x in per[s]["aligned"] if x is not None]
            if len(d) < 8:
                print("     %-14s %8s" % (s, "(too few lineages)")); continue
            #: Wilcoxon on an all-zero vector returns nan. That is not a failed
            #: test, it is a scale with NO VARIATION at this prompt -- `exposure`
            #: is 1 everywhere nothing is uncovered -- and must read as such.
            if all(abs(x) < 1e-12 for x in d):
                print("     %-14s %8.2f %8.2f %+9.3f %10s %5s"
                      % (s, st.mean(b), st.mean(a), 0.0, "no var", "0/%d" % len(d)))
                rows.append(dict(prompt=p, pair=pr, gender=g, role=role, scale=s,
                                 base=st.mean(b), aligned=st.mean(a), delta=0.0,
                                 p=None, n_lineages=len(d), up=0))
                continue
            pv = stats.wilcoxon(d).pvalue
            print("     %-14s %8.2f %8.2f %+9.3f %10.2g%s %5d/%-3d"
                  % (s, st.mean(b), st.mean(a), st.mean(d), pv,
                     " *" if pv < .05 else "  ",
                     sum(1 for x in d if x > 0), len(d)))
            rows.append(dict(prompt=p, pair=pr, gender=g, role=role, scale=s,
                             base=st.mean(b), aligned=st.mean(a), delta=st.mean(d),
                             p=pv, n_lineages=len(d),
                             up=sum(1 for x in d if x > 0)))
    json.dump(dict(_what="LAYER 1: per prompt, mass-weighted level per arm and the "
                         "base->aligned delta, Wilcoxon over that prompt's lineages. "
                         "No pooling, no pairing, gender unused.",
                   rows=rows), open(os.path.join(OUT, "levels.json"), "w"), indent=1)
    print("\n-> results/levels.json (%d prompt x scale rows)" % len(rows))


if __name__ == "__main__":
    main()
