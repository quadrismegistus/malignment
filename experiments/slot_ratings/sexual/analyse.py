"""The 8 sexual gender pairs, two ways, because they are two questions.

    python experiments/slot_ratings/sexual/analyse.py

## THE TWO QUANTITIES ARE NOT THE SAME AND CAN DISAGREE

    RHO     does the scale predict WHICH words move?  Selection.
            Blind to how much mass moved.
    LEVEL   does the mass-weighted mean of the scale SHIFT from base to aligned?
            Blind to which words did it.

`displacement_axis`'s README records them diverging by an order of magnitude on
this corpus: "individual words move a great deal inside an aggregate that moves
a little -- `fired` 0.252 -> 0.107 sits inside a centroid shift of 1.6% of the
pole gap." A strong rho with a flat level means alignment reorders the tail
without moving the centre; a flat rho with a shifted level means it moves mass
without regard to the dimension. Both are findings and neither implies the other.

And the GENDER question takes a different form in each:

    RHO     is the selection ordered MORE TIGHTLY when the slot is a woman's?
            This is X_metonymy 3b, which found +0.15 to +0.25 of correlation
            stronger in the female frame -- on ONE matched pair. Here: eight.
    LEVEL   does the distribution TRAVEL FURTHER when the slot is a woman's?

## WHAT IS EXCLUDED, AND WHY

  is_modifier      X: modifier insertion (`throbbing`, `huge`) delays the noun
                   rather than replacing it. It is syntagmatic, on M04's axis,
                   and is not substitution. 164 words.
  ratable=false    the rater declined: fragments, template junk. 705 words.
  body_distance=0  the not-applicable code, for actions and states with no place
                   on the body. Dropped from that scale ONLY, not from others.

## THE UNITS

RHO is per (prompt, scale) over words, against net movement across the 33 lineage
pairs -- X's own construction. The gender comparison is then PAIRED over the 8
matched sets, which is what X could not do with one pair.

LEVEL is per (prompt, lineage, arm), mass-weighted, so its unit is the lineage
and the gender comparison is paired within (matched set, lineage).
"""

import collections, json, os, random, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
REPS = 2000
SCALES = ["orality", "tactility", "genitality", "incorporation", "body_distance",
          "exposure", "charge", "euphemism", "explicitness"]


def load():
    d = json.load(open(os.path.join(OUT, "rated_gender_pairs_v2.json")))["rows"]
    R = {}
    for r in d:
        if r["ratable"] and not r["is_modifier"]:
            R[(r["prompt"], r["word"])] = r
    return R


def masses(prompts):
    """p_base and p_aligned per (prompt, lineage, word), from twp_words_v4_best."""
    from malignment import roster, vectors as V
    ep = sorted(roster.endpoints()[0].items())
    ms = sorted({x for p in ep for x in p})
    q = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
               "FROM twp_words_v4_best WHERE prompt IN {ts:Array(String)} "
               "AND model IN {ms:Array(String)} GROUP BY prompt, model",
               ts=sorted(prompts), ms=ms)
    store = collections.defaultdict(dict)
    for r in q:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))
    out = {}
    for t in prompts:
        for b, a in ep:
            pb, pa = store[t].get(b), store[t].get(a)
            if pb and pa:
                out[(t, b + " -> " + a)] = (pb, pa)
    return out


def boot(cells, f, seed=20260819):
    ks = list(cells)
    if not ks:
        return None
    L = sorted({k[0] for k in ks}); P = sorted({k[1] for k in ks})
    obs = f(L, P, cells)
    if obs is None:
        return None
    rng = random.Random(seed)
    reps = [g for g in (f([rng.choice(L) for _ in L], [rng.choice(P) for _ in P], cells)
                        for _ in range(REPS)) if g is not None]
    if not reps:
        return None
    p = min(1.0, 2 * sum(1 for r in reps if (r > 0) != (obs > 0)) / len(reps))
    return obs, sorted(reps)[int(.025 * len(reps))], sorted(reps)[int(.975 * len(reps))], p


def main():
    from scipy import stats
    R = load()
    prompts = sorted({k[0] for k in R})
    meta = {p: (R[(p, w)]["pair"], R[(p, w)]["gender"]) for p, w in R}
    pairs = sorted({v[0] for v in meta.values()})
    print("%d ratable non-modifier words over %d prompts, %d matched pairs\n"
          % (len(R), len(prompts), len(pairs)))

    # ---------------- 1. RHO: does the scale predict WHICH words move ----------
    print("=" * 92)
    print("1. RHO -- scale against net movement, per prompt, over words")
    print("   negative = high-scoring words FALL. X's benchmark on the undressing")
    print("   scene was -0.53 to -0.66 for intimacy.\n")
    rho = {}
    for s in SCALES:
        for p in prompts:
            ws = [(R[(p, w)][s], R[(p, w)]["net"]) for (pp, w) in R if pp == p
                  and R[(p, w)].get(s) is not None
                  and not (s == "body_distance" and R[(p, w)][s] == 0)]
            #: A CONSTANT SCALE HAS NO RHO, and one nan poisons the mean over
            #: pairs. The smoke test predicted this: `orality` is 7 for every
            #: word in `tongue_around` because the tongue is the frame's
            #: instrument, and `exposure` is 1 wherever nothing is uncovered.
            #: Those prompts are DROPPED for that scale and the surviving count
            #: is printed, rather than the scale being reported as nan or, worse,
            #: silently averaged over whatever did resolve.
            if len(ws) < 15 or len({a for a, _ in ws}) < 2:
                continue
            r_ = stats.spearmanr([a for a, _ in ws], [b for _, b in ws])
            if r_.statistic != r_.statistic:
                continue
            rho[(s, p)] = (r_.statistic, r_.pvalue, len(ws))
    print("   %-14s %s" % ("scale", "  ".join("%-9s" % p[:9] for p in
                                              ["FEMALE", "MALE", "paired diff", "p"])))
    saved_rho = []
    for s in SCALES:
        per = []
        for pr in pairs:
            fp = [p for p in prompts if meta[p] == (pr, "female")]
            mp = [p for p in prompts if meta[p] == (pr, "male")]
            if not fp or not mp or (s, fp[0]) not in rho or (s, mp[0]) not in rho:
                continue
            per.append((rho[(s, fp[0])][0], rho[(s, mp[0])][0]))
        if len(per) < 4:
            print("   %-14s %s (only %d of 8 pairs have both sides non-constant)"
                  % (s, " " * 40, len(per)))
            continue
        f = st.mean(a for a, _ in per); m = st.mean(b for _, b in per)
        w = stats.wilcoxon([a for a, _ in per], [b for _, b in per])
        print("   %-14s %+9.3f %+9.3f %+9.3f %9.3f%s   (%d pairs)"
              % (s, f, m, f - m, w.pvalue, " *" if w.pvalue < .05 else "", len(per)))
        saved_rho.append(dict(scale=s, female=f, male=m, diff=f - m,
                              p=w.pvalue, n_pairs=len(per)))

    # ---------------- 2. LEVEL: does the distribution SHIFT --------------------
    M = masses(prompts)
    print("\n" + "=" * 92)
    print("2. LEVEL -- mass-weighted E[scale|rated] per arm, per lineage\n")
    lv = collections.defaultdict(dict)
    for (t, lin), (pb, pa) in M.items():
        for s in SCALES:
            for arm, dist in (("base", pb), ("aligned", pa)):
                ws = [w for w in dist if (t, w) in R and R[(t, w)].get(s) is not None
                      and not (s == "body_distance" and R[(t, w)][s] == 0)]
                mm = sum(dist[w] for w in ws)
                if mm <= 0 or len(ws) < 10:
                    continue
                lv[(t, lin)]["%s_%s" % (arm, s)] = sum(
                    dist[w] * R[(t, w)][s] for w in ws) / mm
    print("   %-14s %19s %19s | %19s"
          % ("scale", "FEMALE base->aligned", "MALE base->aligned", "delta diff f-m"))
    saved_lv = []
    for s in SCALES:
        out = {}
        for g in ("female", "male"):
            cells = {}
            for (t, lin), v in lv.items():
                if meta[t][1] != g:
                    continue
                b, a = v.get("base_" + s), v.get("aligned_" + s)
                if b is not None and a is not None:
                    cells[(lin, meta[t][0])] = a - b
            out[g] = boot(cells, lambda L, P, c: (
                st.mean([c[(l, p)] for l in L for p in P if (l, p) in c])
                if any((l, p) in c for l in L for p in P) else None))
        pc = {}
        for (t, lin), v in lv.items():
            b, a = v.get("base_" + s), v.get("aligned_" + s)
            if b is not None and a is not None:
                pc[(lin, meta[t][0], meta[t][1])] = a - b
        def dd(L, P, c):
            v = [c[(l, p, "female")] - c[(l, p, "male")] for l in L for p in P
                 if (l, p, "female") in c and (l, p, "male") in c]
            return st.mean(v) if v else None
        diff = boot(pc, dd)
        if not out["female"] or not out["male"] or not diff:
            continue
        f, m = out["female"], out["male"]
        print("   %-14s %+8.3f p=%-8.3f %+8.3f p=%-8.3f | %+8.3f p=%.3f%s"
              % (s, f[0], f[3], m[0], m[3], diff[0], diff[3],
                 " *" if diff[3] < .05 else ""))
        saved_lv.append(dict(scale=s, female_delta=f[0], female_p=f[3],
                             male_delta=m[0], male_p=m[3],
                             diff=diff[0], diff_lo=diff[1], diff_hi=diff[2],
                             diff_p=diff[3]))

    json.dump(dict(_what="8 sexual gender matched pairs: rho (selection) and level "
                         "(mass shift), which are different quantities",
                   n_words=len(R), rho=saved_rho, level=saved_lv,
                   rho_by_prompt={"%s|%s" % k: v for k, v in rho.items()}),
              open(os.path.join(OUT, "analyse.json"), "w"), indent=1)
    print("\n-> results/analyse.json")


if __name__ == "__main__":
    main()
