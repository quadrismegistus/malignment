"""LAYER 2: pair the two sides of a matched set, blocked on lineage.

    python experiments/slot_ratings/sexual/layer2.py

Adds ONE assumption to layer 1: that the two members of a matched set are
comparable, so their difference is meaningful. The block is the LINEAGE -- the
same base->aligned model pair sees both prompts -- giving 33 paired observations
per set, and the test is a crossed (lineage x set) bootstrap so neither model nor
scene variance is averaged away.

TWO CONTRASTS, NEVER POOLED, because they are not the same comparison:

    M->F  vs  F->M    5 sets. The slot holds the OTHER person's body, and the
                      only change is whose. `She unzipped his ___` invites
                      `cock`; `He unzipped her ___` invites `skirt`.
    F     vs  M       3 sets. The slot holds the speaker's OWN action or state.
                      No object, so no organ is invited either way.

Layer 1 found no genitality asymmetry when these were pooled; that was the
directional cells cancelling against the non-directional ones.

TWO VOCABULARIES, reported side by side:

    full     every rated word. The difference includes WHICH WORDS EXIST and how
             they are weighted. This is the phenomenon as it stands.
    shared   only words present on BOTH sides of the set, which hold 67-99% of
             each side's mass (median ~90%). Any difference left is WEIGHTING
             alone: given the same words, does the model lean differently?

Where both agree the effect is weighting; where only `full` shows it the effect
is availability. This is the check that had no power on the identity groups (4
common words) and has real power here.
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


def boot(cells, f, seed=20260819):
    L = sorted({k[0] for k in cells}); P = sorted({k[1] for k in cells})
    obs = f(L, P, cells)
    if obs is None:
        return None
    rng = random.Random(seed)
    reps = [g for g in (f([rng.choice(L) for _ in L], [rng.choice(P) for _ in P], cells)
                        for _ in range(REPS)) if g is not None]
    if not reps:
        return None
    return (obs, sorted(reps)[int(.025 * len(reps))], sorted(reps)[int(.975 * len(reps))],
            min(1.0, 2 * sum(1 for r in reps if (r > 0) != (obs > 0)) / len(reps)))


def levels(R, M, meta, restrict=None):
    """E[scale|rated] per (prompt, lineage, arm); `restrict` limits the word set."""
    out = collections.defaultdict(dict)
    for (t, lin), (pb, pa) in M.items():
        ok = restrict[meta[t][0]] if restrict else None
        for s in SCALES:
            for arm, dist in (("base", pb), ("aligned", pa)):
                ws = [w for w in dist if (t, w) in R and R[(t, w)].get(s) is not None
                      and not (s == "body_distance" and R[(t, w)][s] == 0)
                      and (ok is None or w in ok)]
                m = sum(dist[w] for w in ws)
                if m > 0 and len(ws) >= 8:
                    out[(t, lin)]["%s_%s" % (arm, s)] = sum(
                        dist[w] * R[(t, w)][s] for w in ws) / m
    return out


def contrast(lv, meta, direction, a, b, sets, label):
    from scipy import stats
    print("\n  %s   (%d matched sets)" % (label, len(sets)))
    print("     %-14s %20s %8s | %20s %8s | %19s %8s"
          % ("scale", "BASE  %s-%s" % (a, b), "p", "ALIGNED %s-%s" % (a, b), "p",
             "DELTA gap", "p"))
    res = []
    for s in SCALES:
        cell = {}
        for (t, lin), v in lv.items():
            pr = meta[t][0]
            if pr not in sets or direction[t] not in (a, b):
                continue
            for arm in ("base", "aligned"):
                k = "%s_%s" % (arm, s)
                if k in v:
                    cell[(lin, pr, arm, direction[t])] = v[k]
        def gap(arm):
            def f(L, P, c):
                v = [c[(l, p, arm, a)] - c[(l, p, arm, b)] for l in L for p in P
                     if (l, p, arm, a) in c and (l, p, arm, b) in c]
                return st.mean(v) if v else None
            return f
        def dgap(L, P, c):
            v = []
            for l in L:
                for p in P:
                    ks = [(l, p, ar, g) for ar in ("base", "aligned") for g in (a, b)]
                    if all(k in c for k in ks):
                        v.append((c[(l, p, "aligned", a)] - c[(l, p, "aligned", b)])
                                 - (c[(l, p, "base", a)] - c[(l, p, "base", b)]))
            return st.mean(v) if v else None
        bb, aa, dd = boot(cell, gap("base")), boot(cell, gap("aligned")), boot(cell, dgap)
        if not (bb and aa and dd):
            continue
        print("     %-14s %+8.3f [%+5.2f,%+5.2f] %8.3f%s | %+8.3f [%+5.2f,%+5.2f] %8.3f%s | %+8.3f %8.3f%s"
              % (s, bb[0], bb[1], bb[2], bb[3], "*" if bb[3] < .05 else " ",
                 aa[0], aa[1], aa[2], aa[3], "*" if aa[3] < .05 else " ",
                 dd[0], dd[3], "*" if dd[3] < .05 else ""))
        res.append(dict(scale=s, base_gap=bb[0], base_p=bb[3], aligned_gap=aa[0],
                        aligned_p=aa[3], delta_gap=dd[0], delta_p=dd[3]))
    return res


def main():
    from analyse import load, masses
    from gender_pairs import DIRECTION, DIRECTIONAL, PAIRS
    R = load()
    prompts = sorted({k[0] for k in R})
    meta = {p: (R[(p, w)]["pair"],) for p, w in R}
    M = masses(prompts)
    nond = sorted({PAIRS[p][0] for p in prompts if PAIRS[p][0] not in DIRECTIONAL})
    #: shared vocabulary per matched set
    shared = {}
    for pr in {v[0] for v in meta.values()}:
        ps = [p for p in prompts if meta[p][0] == pr]
        if len(ps) == 2:
            shared[pr] = {w for (t, w) in R if t == ps[0]} & {w for (t, w) in R if t == ps[1]}
    saved = {}
    for name, restrict in (("FULL VOCABULARY", None), ("SHARED VOCABULARY ONLY", shared)):
        lv = levels(R, M, meta, restrict)
        print("\n" + "=" * 104)
        print("%s" % name)
        saved[name] = {
            "directional": contrast(lv, meta, DIRECTION, "M->F", "F->M", DIRECTIONAL,
                                    "M->F  minus  F->M   (slot = the other person's body)"),
            "nondirectional": contrast(lv, meta, DIRECTION, "F", "M", set(nond),
                                       "F  minus  M   (slot = own action or state)")}
    json.dump(dict(_what="LAYER 2: paired within matched set, blocked on lineage, "
                         "crossed (lineage x set) bootstrap. Two contrasts, two "
                         "vocabularies.", results=saved),
              open(os.path.join(OUT, "layer2.json"), "w"), indent=1)
    print("\n-> results/layer2.json")


if __name__ == "__main__":
    main()
