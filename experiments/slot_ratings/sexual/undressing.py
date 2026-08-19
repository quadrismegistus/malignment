"""X_metonymy's own undressing pair, at full depth, with the v2 instrument.

    python experiments/slot_ratings/sexual/undressing.py --dry
    python experiments/slot_ratings/sexual/undressing.py

    She slowly took off her ___          F
    He slowly took off his ___           M

This is a NON-DIRECTIONAL pair: she takes off her OWN garment, so it belongs
with `felt_get` and `both_naked`, not with the M->F / F->M cell.

## WHY THE `movement` TABLE AND NOT twp_words_v4_best

These two prompts have 50 endpoint pairs in `movement` and only 8 computable
from `twp_words_v4_best` -- the reverse of the eight slot gender pairs, which
have 33 in twp and ZERO in `movement`. So this pair cannot be pooled with them
and is reported alone. `movement` carries p_base and p_aligned directly.

X reached rho -0.53 to -0.66 here between coder intimacy and net movement, on
four instruments and two model families, and its gender claim (3b) rests on THIS
PAIR ALONE -- every scale predicting more strongly in the female frame by 0.15 to
0.25 of correlation. The eight slot pairs are the powered replication of that
claim; this is the original.
"""

import argparse, collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
FEM = "She slowly took off her"
MAL = "He slowly took off his"
SCALES = ["genitality", "charge", "explicitness", "body_distance", "euphemism",
          "orality", "tactility", "incorporation", "exposure"]


def population():
    from malignment import roster, vectors as V
    ep = sorted(roster.endpoints()[0].items())
    rows = V.rows("SELECT prompt, word, base, aligned, cls, p_base, p_aligned "
                  "FROM movement WHERE prompt IN {ps:Array(String)} "
                  "AND (base, aligned) IN {bs:Array(Tuple(String,String))}",
                  ps=[FEM, MAL], bs=ep)
    mv = collections.defaultdict(collections.Counter)
    mass = collections.defaultdict(dict)
    for r in rows:
        lin = r["base"] + " -> " + r["aligned"]
        mass[(r["prompt"], lin)][r["word"]] = (r["p_base"], r["p_aligned"])
        if r["cls"] == "riser":
            mv[(r["prompt"], r["word"])]["r"] += 1
        elif r["cls"] == "faller":
            mv[(r["prompt"], r["word"])]["f"] += 1
    jobs = sorted(k for k, c in mv.items() if c["r"] + c["f"] >= 1)
    return jobs, mv, mass


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    jobs, mv, mass = population()
    lins = sorted({l for (t, l) in mass})
    print("%s ___   /   %s ___" % (FEM, MAL))
    print("  %d lineage pairs | %d moving (prompt, word) at k>=1 | ~$%.3f"
          % (len(lins), len(jobs), 0.00005 * len(jobs)))
    for t in (FEM, MAL):
        print("     %-26s %4d words" % (t[:26], sum(1 for p, _ in jobs if p == t)))
    if a.dry:
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "undressing_v2.json")
    from task import SexualSlotEN, SCALES_SEX, render
    t = SexualSlotEN(); errs = {}
    res = t.map([render(p, w) for p, w in jobs],
                metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                num_workers=32, errors=errs)
    R = {}
    for (p, w), r in zip(jobs, res):
        if r is None or not r.ratable or r.is_modifier:
            continue
        R[(p, w)] = dict(zone_kind=r.zone_kind, referent_kind=r.referent_kind,
                         net=mv[(p, w)]["r"] - mv[(p, w)]["f"],
                         **{s: getattr(r, s) for s in SCALES_SEX})
    print("  rated %d, usable (ratable, non-modifier) %d, errors %d"
          % (len(jobs), len(R), len(errs)))

    from scipy import stats
    lv = collections.defaultdict(dict)
    for (p, lin), d in mass.items():
        for s in SCALES:
            for i, arm in ((0, "base"), (1, "aligned")):
                ws = [w for w in d if (p, w) in R and R[(p, w)].get(s) is not None
                      and not (s == "body_distance" and R[(p, w)][s] == 0)]
                m = sum(d[w][i] for w in ws)
                if m > 0 and len(ws) >= 10:
                    lv[(p, lin)]["%s_%s" % (arm, s)] = sum(
                        d[w][i] * R[(p, w)][s] for w in ws) / m

    print("\n" + "=" * 92)
    print("LAYER 1 -- per prompt, does the level move? Wilcoxon over lineages.")
    for p in (FEM, MAL):
        print("\n  %s ___" % p)
        print("     %-14s %8s %8s %9s %10s %8s"
              % ("scale", "base", "aligned", "delta", "p", "up/n"))
        for s in SCALES:
            d = [(lv[(p, l)]["aligned_" + s] - lv[(p, l)]["base_" + s]) for l in lins
                 if "aligned_" + s in lv.get((p, l), {}) and "base_" + s in lv.get((p, l), {})]
            b = [lv[(p, l)]["base_" + s] for l in lins if "base_" + s in lv.get((p, l), {})]
            aa = [lv[(p, l)]["aligned_" + s] for l in lins if "aligned_" + s in lv.get((p, l), {})]
            if len(d) < 8 or all(abs(x) < 1e-12 for x in d):
                print("     %-14s %8s" % (s, "no variation" if d else "(too few)")); continue
            pv = stats.wilcoxon(d).pvalue
            print("     %-14s %8.2f %8.2f %+9.3f %10.2g%s %5d/%-3d"
                  % (s, st.mean(b), st.mean(aa), st.mean(d), pv,
                     " *" if pv < .05 else "  ", sum(1 for x in d if x > 0), len(d)))

    print("\n" + "=" * 92)
    print("F minus M gap, LINEAGE as the unit, sign test over %d lineages" % len(lins))
    print("  %-14s %10s %8s %9s | %10s %8s %9s %9s"
          % ("scale", "BASE gap", "signs", "p", "DELTA gap", "up/n", "sign p", "wilcox"))
    saved = []
    for s in SCALES:
        gb, gd = [], []
        for l in lins:
            f, m = lv.get((FEM, l), {}), lv.get((MAL, l), {})
            kb, ka = "base_" + s, "aligned_" + s
            if kb in f and kb in m:
                gb.append(f[kb] - m[kb])
                if ka in f and ka in m:
                    gd.append((f[ka] - m[ka]) - (f[kb] - m[kb]))
        if len(gb) < 8:
            continue
        def sg(v):
            if not v or all(abs(x) < 1e-12 for x in v):
                return None
            pos = sum(1 for x in v if x > 0); n = sum(1 for x in v if abs(x) > 1e-12)
            return (st.mean(v), pos, n, stats.binomtest(pos, n, .5).pvalue,
                    stats.wilcoxon(v).pvalue)
        tb, td = sg(gb), sg(gd)
        if not tb:
            continue
        row = "  %-14s %+10.3f %4d/%-3d %9.2g%s" % (s, tb[0], tb[1], tb[2], tb[3],
                                                    "*" if tb[3] < .05 else " ")
        if td:
            row += " | %+10.3f %4d/%-3d %8.2g%s %8.2g%s" % (
                td[0], td[1], td[2], td[3], "*" if td[3] < .05 else " ",
                td[4], "*" if td[4] < .05 else "")
        print(row)
        saved.append(dict(scale=s, base_gap=tb[0], base_pos=tb[1], base_n=tb[2],
                          base_p=tb[3], delta_gap=td[0] if td else None,
                          delta_pos=td[1] if td else None,
                          delta_sign_p=td[3] if td else None,
                          delta_wilcox_p=td[4] if td else None))
    json.dump(dict(_what="X_metonymy's undressing pair from the `movement` table, "
                         "50 endpoint pairs, sexual_slot_en_v2",
                   n_lineages=len(lins), gap=saved,
                   words=[dict(prompt=p, word=w, **v) for (p, w), v in sorted(R.items())]),
              open(path, "w"), indent=1)
    print("\n-> %s" % path)


if __name__ == "__main__":
    main()
