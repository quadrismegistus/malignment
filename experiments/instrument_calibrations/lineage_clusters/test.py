"""Do the headline lineage counts survive when correlated lineages are one unit? -> results/cluster_tests.md

    python -u test.py

The paper seat's check (1), 2026-09-24. Reanalysis only: no generation, no
forward pass. Two headline tests, each re-run at the cluster unit under the three
groupings in `clusters.py`:

    SELECTIVITY   English content-selectivity: per-lineage slope of mass change
                  on transgressive charge, predicted NEGATIVE. Values read from
                  `displacement/existence/results/selectivity_en.json`
                  (`overall.per_lineage`), the artifact behind 40/50.
    KILL, SCREAM  "She was so angry she wanted to": per-lineage p_aligned -
                  p_base of `kill` (predicted NEGATIVE, 44/50) and `scream`
                  (predicted POSITIVE, 42/50), read from ClickHouse
                  `movement_v4`, raw frame, 50 endpoint pairs.

TWO CLUSTER-UNIT STATISTICS, both fixed here:

    cluster medians   the median of each cluster's lineage values, then a
                      two-sided sign test over clusters (ties dropped)
    one per cluster   draw one lineage per cluster at random, sign test over
                      the draws; 10,000 draws, seed 20260924. Reported: the
                      median count in the predicted direction and the share of
                      draws with p < 0.05 in the predicted direction.
"""
import collections, json, os, random, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import clusters  # noqa: E402

SEL = os.path.join(ROOT, "experiments", "displacement", "existence", "results", "selectivity_en.json")
PROMPT = "She was so angry she wanted to"
DRAWS = 10000
SEED = 20260924
GROUPINGS = ("LINEAGE", "PRETRAIN", "SFT", "UNION")


def sign(vals):
    v = [x for x in vals if x != 0]
    n, pos = len(v), sum(1 for x in v if x > 0)
    k = min(pos, n - pos)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return pos, n - pos, p


def median(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def load():
    from malignment import ch, roster
    eps, _ = roster.endpoints()
    keys = {"%s>%s" % (b, a) for b, a in eps.items()}
    out = {}
    sel = json.load(open(SEL))["overall"]["per_lineage"]
    out["selectivity"] = ({r["lineage"]: float(r["slope"]) for r in sel}, -1)
    rows = ch.query("SELECT base, aligned, word, p_base, p_aligned FROM {db}.movement_v4 "
                    "WHERE frame_base='' AND frame_aligned='' AND prompt='%s' "
                    "AND word IN ('kill','scream')" % PROMPT, limit_bytes=None)
    for w, direction in (("kill", -1), ("scream", +1)):
        out[w] = ({"%s>%s" % (r["base"], r["aligned"]): float(r["p_aligned"]) - float(r["p_base"])
                   for r in rows if r["word"] == w
                   and "%s>%s" % (r["base"], r["aligned"]) in keys}, direction)
    for name, (vals, _d) in out.items():
        if set(vals) != keys:
            raise SystemExit("%s: %d of %d lineages" % (name, len(set(vals) & keys), len(keys)))
    return out, keys


def main():
    data, keys = load()
    rnd = random.Random(SEED)
    L = ["# Headline lineage counts at the cluster unit", "",
         "Producer `test.py` (paper seat's check 1, 2026-09-24). Reanalysis only. Groupings from "
         "`clusters.py`: LINEAGE is the published test (50 independent units); PRETRAIN groups by base "
         "developer; SFT by dominant declared SFT source, developer where none is named; UNION joins any "
         "shared named source or developer into connected components.", ""]
    for g in GROUPINGS[1:]:
        c = collections.Counter(clusters.grouping(g, keys).values())
        L.append("- **%s**: %d clusters, sizes %s" % (g, len(c), sorted(c.values(), reverse=True)))
    L += ["", "| test | predicted | grouping | clusters | cluster medians in predicted direction | p | "
          "one-per-cluster: median count | draws with p<0.05 |", "|---|---|---|---|---|---|---|---|"]
    for name, (vals, d) in data.items():
        for g in GROUPINGS:
            m = {k: k for k in keys} if g == "LINEAGE" else clusters.grouping(g, keys)
            members = collections.defaultdict(list)
            for k in sorted(keys):
                members[m[k]].append(k)
            cm = [d * median([vals[k] for k in ks]) for ks in members.values()]
            pos, neg, p = sign(cm)
            counts, sig = [], 0
            if g != "LINEAGE":
                for _ in range(DRAWS):
                    draw = [d * vals[rnd.choice(ks)] for ks in members.values()]
                    dp, dn, dpv = sign(draw)
                    counts.append(dp)
                    sig += dpv < 0.05 and dp > dn
            L.append("| %s | %s | %s | %d | %d/%d | %.2g | %s | %s |" % (
                name, "< 0" if d < 0 else "> 0", g, len(members), pos, pos + neg, p,
                "%d of %d" % (median(counts), len(members)) if counts else "--",
                "%.1f%%" % (100.0 * sig / DRAWS) if counts else "--"))
    L += ["", "Cluster medians and draws are sign-flipped so the predicted direction always counts as a hit; "
          "ties (a median or a draw exactly zero) are dropped from the sign test.", "",
          "**The fence.** %d of 50 endpoints name no public SFT dataset; they are grouped by developer, "
          "so data shared ACROSS developers among them (e.g. undeclared ShareGPT-style distillation) is "
          "invisible to every grouping here, UNION included." %
          sum(1 for v in clusters.L.values() if v[0] == "IN-HOUSE")]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "cluster_tests.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
