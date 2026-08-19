"""Every "I should" matched pair, sign test by lineage, individually and by domain.

    python experiments/slot_ratings/institutional/ishould_per_pair.py

The site is held fixed BY SELECTION: only prompts ending "I should", so every
cell sits at the same bare-infinitive slot and F21 and M03 pool (both read the
`movement` table). The unit is the LINEAGE and the test is a two-sided sign test
on the per-lineage gap, run three ways:

    per PAIR      each matched scenario alone
    per DOMAIN    pairs grouped by the scene's domain, gaps averaged within a
                  lineage before testing, so the unit stays the lineage
    pooled        all pairs averaged within a lineage

Reported together because a pooled null can be cancellation across pairs that
disagree in sign, and a pooled significance can be one pair carrying the rest.
That is the defect the sexual study surfaced and it is not visible from a pooled
statistic alone.

DOMAIN comes from the corpus: F21's is the `prompt_id` scene token (govt,
housing, labor, medical, police, political); M03's is the kernel's own `domain`
field per scenario.
"""

import collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results", "base_side")
KERNEL = ("/Users/rj416/github/malign-logits/meta/M03_proceduralization/"
          "m03_kernel_full.json")
SCALES = ["procedural", "deference", "mediation", "agency", "arousal", "abstraction",
          "specificity", "termination", "collective", "assertiveness", "target",
          "delay", "vocalisation"]


def domains():
    """cluster -> domain, for both corpora, from the corpus's own labels."""
    out = {}
    k = json.load(open(KERNEL))
    for sc in (k if isinstance(k, list) else list(k.values())[0]):
        for stx in ("I_final",):
            out["%s|%s" % (sc["scenario_id"], stx)] = sc.get("domain") or "?"
        for cid in (sc["cells"] if isinstance(sc["cells"], dict) else {}):
            parts = cid.split("_")
            if parts[0] in ("indiv", "inst"):
                out["%s|%s" % (sc["scenario_id"], "_".join(parts[1:]))] = \
                    sc.get("domain") or "?"
    return out


def main():
    from scipy import stats
    DOM = domains()
    rows = []
    for c in ("f21", "m03"):
        for r in json.load(open(os.path.join(OUT, "%s.json" % c)))["rows"]:
            if r["prompt"].rstrip().endswith("I should"):
                dom = (r["cluster"].rsplit("_", 1)[0] if c == "f21"
                       else DOM.get(r["cluster"], "?"))
                rows.append(dict(r, corpus=c, domain=dom))
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["cluster"], r["lineage"])][r["position"]] = r
    clusters = sorted({c for c, _ in by})
    CD = {r["cluster"]: (r["corpus"], r["domain"]) for r in rows}
    full = [c for c in clusters
            if any("indiv" in by[(c, l)] and "inst" in by[(c, l)] for _, l in by if _ == c)]
    print("'I should' prompts: %d | matched pairs with both sides: %d | lineages: %d"
          % (len({r["prompt"] for r in rows}), len(full), len({l for _, l in by})))
    print("  by corpus: %s" % dict(collections.Counter(CD[c][0] for c in full)))
    print("  by domain: %s" % dict(collections.Counter(CD[c][1] for c in full)))

    def sg(v):
        if not v or all(abs(x) < 1e-12 for x in v):
            return None
        pos = sum(1 for x in v if x > 0); n = sum(1 for x in v if abs(x) > 1e-12)
        return pos, n, stats.binomtest(pos, n, .5).pvalue, st.mean(v)

    def gaps(cs, s):
        """per lineage, the gap averaged over the clusters in `cs`."""
        gb, gd = collections.defaultdict(list), collections.defaultdict(list)
        for c in cs:
            for (cc, l), d in by.items():
                if cc != c or "indiv" not in d or "inst" not in d:
                    continue
                a, b = d["inst"], d["indiv"]
                kb, ka = "base_" + s, "aligned_" + s
                if a.get(kb) is not None and b.get(kb) is not None:
                    gb[l].append(a[kb] - b[kb])
                    if a.get(ka) is not None and b.get(ka) is not None:
                        gd[l].append((a[ka] - b[ka]) - (a[kb] - b[kb]))
        return ([st.mean(v) for v in gb.values() if v],
                [st.mean(v) for v in gd.values() if v])

    saved = {"per_pair": [], "per_domain": [], "pooled": []}
    print("\n" + "=" * 100)
    print("PER PAIR -- sign test over that pair's lineages")
    print("  %-22s %-9s %-9s %s"
          % ("pair", "corpus", "domain", "  ".join("%-13s" % s[:13] for s in
                                                   ["procedural", "deference", "mediation", "arousal"])))
    for c in full:
        cells = []
        for s in ["procedural", "deference", "mediation", "arousal"]:
            gb, _ = gaps([c], s)
            t = sg(gb)
            cells.append("%+6.3f %2d/%-2d%s" % (t[3], t[0], t[1], "*" if t[2] < .05 else " ")
                         if t else "%-13s" % "-")
        print("  %-22s %-9s %-9s %s" % (c[:22], CD[c][0], CD[c][1],
                                        "  ".join("%-13s" % x for x in cells)))
        for s in SCALES:
            gb, gd = gaps([c], s)
            tb, td = sg(gb), sg(gd)
            if tb:
                saved["per_pair"].append(dict(
                    pair=c, corpus=CD[c][0], domain=CD[c][1], scale=s,
                    base_mean=tb[3], base_pos=tb[0], base_n=tb[1], base_p=tb[2],
                    delta_mean=td[3] if td else None, delta_pos=td[0] if td else None,
                    delta_p=td[2] if td else None))

    for label, groups in (("PER DOMAIN", {d: [c for c in full if CD[c][1] == d]
                                          for d in sorted({CD[c][1] for c in full})}),
                          ("POOLED", {"ALL": full,
                                      "F21 only": [c for c in full if CD[c][0] == "f21"],
                                      "M03 only": [c for c in full if CD[c][0] == "m03"]})):
        print("\n" + "=" * 100)
        print("%s -- gaps averaged within a lineage, sign test over lineages" % label)
        print("  %-14s %6s %26s | %26s"
              % ("group", "pairs", "BASE gap (inst - indiv)", "DELTA gap"))
        for g, cs in groups.items():
            if not cs:
                continue
            print("  %s  (%d pairs)" % (g, len(cs)))
            for s in SCALES:
                gb, gd = gaps(cs, s)
                tb, td = sg(gb), sg(gd)
                if not tb:
                    continue
                row = "     %-14s %+9.3f %4d/%-3d %9.2g%s" % (
                    s, tb[3], tb[0], tb[1], tb[2], "*" if tb[2] < .05 else " ")
                if td:
                    row += " | %+9.3f %4d/%-3d %9.2g%s" % (
                        td[3], td[0], td[1], td[2], "*" if td[2] < .05 else "")
                print(row)
                saved["per_domain" if label == "PER DOMAIN" else "pooled"].append(dict(
                    group=g, n_pairs=len(cs), scale=s, base_mean=tb[3], base_pos=tb[0],
                    base_n=tb[1], base_p=tb[2], delta_mean=td[3] if td else None,
                    delta_pos=td[0] if td else None, delta_p=td[2] if td else None))
    json.dump(dict(_what="'I should' matched pairs, sign test by lineage, per pair, "
                         "per domain, and pooled", **saved),
              open(os.path.join(OUT, "ishould_per_pair.json"), "w"), indent=1)
    print("\n-> results/base_side/ishould_per_pair.json")


if __name__ == "__main__":
    main()
