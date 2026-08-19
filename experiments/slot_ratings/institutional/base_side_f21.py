"""Was the base ALREADY proceduralised? F21's claim as a level, not a movement.

    python experiments/slot_ratings/institutional/base_side_f21.py

F21 reports that alignment proceduralises the individual and not the institution,
and that deference is "already present in pretraining", so there is no
emancipatory outside. The second half is a claim about a LEVEL, and every
measurement in this folder so far has been a movement: a rating correlated
against a rise/fall verdict, which is silent about where the distribution sat to
begin with. A word already dominant in the base cannot rise, so a movement
statistic reads an inherited disposition as no effect.

The measure is the one from experiments/slot_ratings/identity/base_side.py: a
mass-weighted conditional mean per arm,

    E[scale | rated] = sum_w p(w) * rating(w) / sum_w p(w)

with no eligibility gate, which also lets arm A and arm B ratings merge, since
the gate that separated them does not apply to a mass-weighted mean.

## THE DECOMPOSITION THIS BUYS

    aligned_gap = base_gap + delta_gap

F21's "already present in pretraining" predicts base_gap carries most of
aligned_gap. Its "proceduralises the individual not the institution" predicts
delta is larger on the individual prompts. The two are separable here and are
reported separately.

## WHAT THIS IS NOT

Not a reproduction of F21's numbers. F21 scored ~21,000 generations on
passage-level dimensions; this scores words in the slot. Same claim, different
object. The position labels are the prompts table's own `subdomain`:
INDIVIDUAL = citizen, worker, tenant, patient; INSTITUTION = agency, mgmt,
landlord, doctor, officer, party.
"""

import collections, glob, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
RESULTS = os.path.join(HERE, "results", "m03")
OUT = os.path.join(HERE, "results", "base_side")


def ratings():
    """Merge BOTH arms: the gate that separated them does not apply here."""
    R = collections.defaultdict(dict)
    n = collections.Counter()
    for f in sorted(glob.glob(os.path.join(
            RESULTS, "rated_f21_slot_institutional_en_v3_arm*.json"))):
        d = json.load(open(f))
        for pr in d["prompts"]:
            for w, r in (pr.get("ratings") or {}).items():
                R[(pr["prompt"], w)].update(r)
                n[d["arm"]] += 1
    print("ratings merged: arm A %d, arm B %d, %d distinct (prompt, word)"
          % (n["A"], n["B"], len(R)))
    return R


def main():
    from malignment import roster, vectors as V
    from scipy import stats
    from run_f21 import prompts
    R = ratings()
    ps = prompts()
    scales = sorted({k for v in R.values() for k in v})
    print("F21 prompts: %d indiv, %d inst | scales %d"
          % (sum(p["position"] == "indiv" for p in ps),
             sum(p["position"] == "inst" for p in ps), len(scales)))
    ep = sorted(roster.endpoints()[0].items())
    ms = sorted({m for pair in ep for m in pair})
    texts = [p["prompt"] for p in ps]
    q = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
               "FROM twp_words_v4_best WHERE prompt IN {ts:Array(String)} "
               "AND model IN {ms:Array(String)} GROUP BY prompt, model",
               ts=texts, ms=ms)
    store = collections.defaultdict(dict)
    for r in q:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))
    print("store: %d prompts x up to %d models" % (len(store), len(ms)))

    rows = []
    for p in ps:
        for b, a in ep:
            pb, pa = store[p["prompt"]].get(b), store[p["prompt"]].get(a)
            if not pb or not pa:
                continue
            rec = dict(prompt=p["prompt"], prompt_id=p["prompt_id"],
                       subdomain=p["subdomain"], position=p["position"],
                       lineage=b + " -> " + a)
            for arm, dist in (("base", pb), ("aligned", pa)):
                for s in scales:
                    ws = [w for w in dist if R.get((p["prompt"], w), {}).get(s) is not None]
                    m = sum(dist[w] for w in ws)
                    if m <= 0 or len(ws) < 10:
                        continue
                    rec["%s_%s" % (arm, s)] = sum(
                        dist[w] * R[(p["prompt"], w)][s] for w in ws) / m
                    rec["cov_%s_%s" % (arm, s)] = m
            rows.append(rec)
    L = sorted({r["lineage"] for r in rows})
    print("rows: %d over %d lineages\n" % (len(rows), len(L)))

    print("=" * 84)
    print("THE DECOMPOSITION. gap = institution minus individual, per lineage.")
    print("A positive base gap means pretraining ALREADY put the institution higher.\n")
    print("  %-14s %9s %9s %9s   %9s %9s   %s"
          % ("scale", "base gap", "algn gap", "delta gap", "p base", "p delta", "inherited"))
    saved = []
    for s in scales:
        bg, ag, dg = [], [], []
        for l in L:
            v = [r for r in rows if r["lineage"] == l]
            def mean(arm, pos):
                x = [r["%s_%s" % (arm, s)] for r in v
                     if r["position"] == pos and r.get("%s_%s" % (arm, s)) is not None]
                return st.mean(x) if len(x) >= 3 else None
            b_i, b_n = mean("base", "inst"), mean("base", "indiv")
            a_i, a_n = mean("aligned", "inst"), mean("aligned", "indiv")
            if None in (b_i, b_n, a_i, a_n):
                continue
            bg.append(b_i - b_n); ag.append(a_i - a_n); dg.append((a_i - a_n) - (b_i - b_n))
        if len(bg) < 8:
            continue
        pb = stats.wilcoxon(bg).pvalue
        pd = stats.wilcoxon(dg).pvalue
        frac = (st.median(bg) / st.median(ag)) if abs(st.median(ag)) > 1e-9 else float("nan")
        print("  %-14s %+9.3f %+9.3f %+9.3f   %9.2g %9.2g   %s"
              % (s, st.median(bg), st.median(ag), st.median(dg), pb, pd,
                 ("%.0f%%" % (100 * frac)) if frac == frac else "-"))
        saved.append(dict(scale=s, n_lineages=len(bg), base_gap=st.median(bg),
                          aligned_gap=st.median(ag), delta_gap=st.median(dg),
                          p_base=pb, p_delta=pd, inherited_frac=frac))

    print("\n" + "=" * 84)
    print("DOES ALIGNMENT MOVE THE INDIVIDUAL MORE THAN THE INSTITUTION?")
    print("Per lineage, the aligned-minus-base delta within each position.\n")
    print("  %-14s %10s %10s %10s %9s" % ("scale", "d indiv", "d inst", "diff", "p"))
    for s in scales:
        di, dn = [], []
        for l in L:
            v = [r for r in rows if r["lineage"] == l]
            for pos, acc in (("indiv", di), ("inst", dn)):
                x = [r["aligned_" + s] - r["base_" + s] for r in v
                     if r["position"] == pos and r.get("base_" + s) is not None
                     and r.get("aligned_" + s) is not None]
                acc.append(st.mean(x) if len(x) >= 3 else None)
        pairs = [(a, b) for a, b in zip(di, dn) if a is not None and b is not None]
        if len(pairs) < 8:
            continue
        w = stats.wilcoxon([a for a, b in pairs], [b for a, b in pairs])
        print("  %-14s %+10.4f %+10.4f %+10.4f %9.2g %s"
              % (s, st.median(a for a, b in pairs), st.median(b for a, b in pairs),
                 st.median(a - b for a, b in pairs), w.pvalue,
                 "INDIV MOVES MORE" if st.median(abs(a) - abs(b) for a, b in pairs) > 0
                 and w.pvalue < 0.05 else ""))
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(_what="mass-weighted E[scale] per (F21 prompt, lineage, arm)",
                   rows=rows, decomposition=saved),
              open(os.path.join(OUT, "f21.json"), "w"), indent=1)
    print("\n-> results/base_side/f21.json (%d rows)" % len(rows))


if __name__ == "__main__":
    main()
