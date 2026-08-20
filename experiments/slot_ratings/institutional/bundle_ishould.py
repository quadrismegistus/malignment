"""All corpora, prompts ending exactly in "I should", pooled. Base, aligned, delta.

    python experiments/slot_ratings/institutional/bundle_ishould.py

Holding the grammatical site FIXED BY SELECTION rather than by design: keep only
prompts whose text ends in "I should", so every cell in the table sits at the
same bare-infinitive slot. That removes the site confound (a finite-verb slot
moves `procedural` +0.221, larger than the position contrast) without relying on
any corpus's own balancing, and it lets F21 and M03 pool since both read the same
`movement` table.

slotpov contributes nothing here: its frames end "so X decided to". That is not a
loss to be worked around, it is the selection doing its job.

Levels are mass-weighted conditional means, E[scale|rated] = sum p(w)r(w)/sum p(w),
per arm. The delta test is the crossed (lineage, prompt) bootstrap, so it accounts
for both model and prompt variance.

## Three quantities the README booked and this file did not emit (added 2026-08-20)

Section 13 reports per-position p values, 95% intervals, and a statistic "paired
within scenario, 24 clusters". None of the three was computed here: the file
derived ONE p, from reps it then discarded, resampling the two positions' prompts
INDEPENDENTLY. That last is not a detail. The unpaired statistic is why the
committed artifact carried `mediation` p=0.056 and `procedural` p=0.104 where the
README books 0.025 and 0.061.

    p_indiv / p_inst          within a position, base against aligned
    ci_*_indiv_minus_inst     the interval on the change in gap, from the
                              existing reps -- the test was always two-sided and
                              the reps were always there
    paired_*                  the difference taken INSIDE a (lineage, cluster)
                              cell holding both positions, so the two sides can
                              never come from different scenes

Each new statistic draws from its OWN `Random`, so the stream feeding
`p_gap_change` is untouched and every pre-existing field reproduces exactly.

SIGN. `gap()` returns inst MINUS indiv. The README reports INDIV MINUS INST.
Everything saved here uses the README's direction, and the interval taken from
`reps` is negated and its ends swapped for that reason.
"""

import collections, glob, json, os, random, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results", "base_side")
SUFFIX = "I should"
REPS = 2000


def main():
    rows, src = [], collections.Counter()
    for c in ("f21", "m03"):
        p = os.path.join(OUT, "%s.json" % c)
        for r in json.load(open(p))["rows"]:
            if r["prompt"].rstrip().endswith(SUFFIX):
                r = dict(r, corpus=c)
                rows.append(r); src[(c, r["position"])] += 1
    prompts = {r["prompt"] for r in rows}
    print("prompts ending %r: %d  (F21 %d, M03 %d)"
          % (SUFFIX, len(prompts),
             len({r["prompt"] for r in rows if r["corpus"] == "f21"}),
             len({r["prompt"] for r in rows if r["corpus"] == "m03"})))
    for pos in ("indiv", "inst"):
        print("   %-6s %d prompts, %d cells"
              % (pos, len({r["prompt"] for r in rows if r["position"] == pos}),
                 sum(1 for r in rows if r["position"] == pos)))
    L = sorted({r["lineage"] for r in rows})
    print("   %d lineages, %d cells total" % (len(L), len(rows)))

    #: A cluster is one scenario. The same `labor_5` carries an `indiv` row and
    #: an `inst` row, which is the pairing section 13 claims and the loop below
    #: did not use.
    pairs = collections.defaultdict(dict)
    for r in rows:
        pairs[(r["cluster"], r["lineage"])][r["position"]] = r
    both = sorted({c for (c, _), d in pairs.items() if "indiv" in d and "inst" in d})
    print("   %d clusters, %d holding both positions" % (len({c for c, _ in pairs}), len(both)))

    def _p(rr, o):
        """Two-sided bootstrap p, the convention the gap test already uses."""
        if not rr or o is None:
            return float("nan")
        return min(1.0, 2 * sum(1 for r in rr if (r > 0) != (o > 0)) / len(rr))

    def _ci(rr):
        if not rr:
            return (float("nan"), float("nan"))
        q = sorted(rr)
        return (q[int(.025 * len(q))], q[min(len(q) - 1, int(.975 * len(q)))])

    scales = sorted({k[5:] for r in rows for k in r if k.startswith("base_")})
    print("\n%-14s | %17s | %17s | %17s"
          % ("", "BASE", "ALIGNED", "DELTA (algn-base)"))
    print("%-14s | %8s %8s | %8s %8s | %8s %8s   %8s"
          % ("scale", "indiv", "inst", "indiv", "inst", "indiv", "inst", "p(gap)"))
    saved = []
    for s in scales:
        lv = {}
        for arm in ("base", "aligned"):
            for pos in ("indiv", "inst"):
                v = [r["%s_%s" % (arm, s)] for r in rows if r["position"] == pos
                     and r.get("%s_%s" % (arm, s)) is not None]
                lv[(arm, pos)] = st.mean(v) if v else None
        if lv[("base", "indiv")] is None or lv[("aligned", "inst")] is None:
            continue
        #: crossed bootstrap on the CHANGE IN GAP, resampling lineages and prompts
        cell = {}
        for r in rows:
            b, a = r.get("base_" + s), r.get("aligned_" + s)
            if b is None or a is None:
                continue
            cell.setdefault((r["lineage"], r["prompt"], r["position"]), []).append(a - b)
        cell = {k: st.mean(v) for k, v in cell.items()}
        lins = sorted({k[0] for k in cell})
        pi = sorted({k[1] for k in cell if k[2] == "indiv"})
        pn = sorted({k[1] for k in cell if k[2] == "inst"})
        def gap(Ls, A, B):
            a = [cell[(l, p, "inst")] for l in Ls for p in B if (l, p, "inst") in cell]
            b = [cell[(l, p, "indiv")] for l in Ls for p in A if (l, p, "indiv") in cell]
            return (st.mean(a) - st.mean(b)) if a and b else None
        obs = gap(lins, pi, pn)
        rng = random.Random(20260819)
        reps = [g for g in (gap([rng.choice(lins) for _ in lins],
                                [rng.choice(pi) for _ in pi],
                                [rng.choice(pn) for _ in pn]) for _ in range(REPS))
                if g is not None]
        pv = min(1.0, 2 * sum(1 for r in reps if (r > 0) != (obs > 0)) / len(reps)) if reps else float("nan")

        #: (a) THE INTERVAL, from the reps computed above and previously thrown
        #: away. Negated and its ends swapped: `gap()` is inst-indiv, this is
        #: indiv-inst.
        _lo, _hi = _ci(reps)
        ci_lo, ci_hi = -_hi, -_lo

        #: (b) WITHIN A POSITION. The README's main-effect table prints a p in
        #: each position column and nothing here produced one.
        r2 = random.Random(20260820)
        def pmean(Ls, Ps, pos):
            v = [cell[(l, p, pos)] for l in Ls for p in Ps if (l, p, pos) in cell]
            return st.mean(v) if v else None
        wp = {}
        for pos, P in (("indiv", pi), ("inst", pn)):
            o = pmean(lins, P, pos)
            rr = [m for m in (pmean([r2.choice(lins) for _ in lins],
                                    [r2.choice(P) for _ in P], pos)
                              for _ in range(REPS)) if m is not None]
            wp[pos] = (o, _p(rr, o)) + _ci(rr)

        #: (c) PAIRED WITHIN SCENARIO. The difference is taken inside a
        #: (lineage, cluster) cell holding both positions, so the two sides are
        #: always the same scene. Its per-position means run over the clusters
        #: holding both, which is why section 13 prints `mediation` inst +0.133
        #: where the pooled value is +0.125: different populations, both correct.
        r3 = random.Random(20260821)
        pc, pdi, pdn = {}, {}, {}
        for (c_, l_), d_ in pairs.items():
            a_, b_ = d_.get("indiv"), d_.get("inst")
            if not a_ or not b_:
                continue
            ka, kb = "aligned_" + s, "base_" + s
            if None in (a_.get(ka), a_.get(kb), b_.get(ka), b_.get(kb)):
                continue
            pdi[(l_, c_)] = a_[ka] - a_[kb]
            pdn[(l_, c_)] = b_[ka] - b_[kb]
            pc[(l_, c_)] = pdi[(l_, c_)] - pdn[(l_, c_)]
        pl = sorted({k[0] for k in pc}); pcl = sorted({k[1] for k in pc})
        def pdiff(Ls, Cs):
            v = [pc[(l, c)] for l in Ls for c in Cs if (l, c) in pc]
            return st.mean(v) if v else None
        pobs = pdiff(pl, pcl)
        preps = [m for m in (pdiff([r3.choice(pl) for _ in pl],
                                   [r3.choice(pcl) for _ in pcl])
                             for _ in range(REPS)) if m is not None]
        plo, phi = _ci(preps)

        di = lv[("aligned", "indiv")] - lv[("base", "indiv")]
        dn = lv[("aligned", "inst")] - lv[("base", "inst")]
        print("%-14s | %8.2f %8.2f | %8.2f %8.2f | %+8.2f %+8.2f   %8.3f%s"
              % (s, lv[("base", "indiv")], lv[("base", "inst")],
                 lv[("aligned", "indiv")], lv[("aligned", "inst")], di, dn, pv,
                 " *" if pv < .05 else ""))
        saved.append(dict(scale=s, base_indiv=lv[("base", "indiv")],
                          base_inst=lv[("base", "inst")],
                          aligned_indiv=lv[("aligned", "indiv")],
                          aligned_inst=lv[("aligned", "inst")],
                          delta_indiv=di, delta_inst=dn, p_gap_change=pv,
                          n_lineages=len(lins), n_prompts=len(pi) + len(pn),
                          #: added 2026-08-20; every field above is unchanged
                          ci_lo_indiv_minus_inst=ci_lo, ci_hi_indiv_minus_inst=ci_hi,
                          boot_delta_indiv=wp["indiv"][0], p_indiv=wp["indiv"][1],
                          ci_lo_indiv=wp["indiv"][2], ci_hi_indiv=wp["indiv"][3],
                          boot_delta_inst=wp["inst"][0], p_inst=wp["inst"][1],
                          ci_lo_inst=wp["inst"][2], ci_hi_inst=wp["inst"][3],
                          paired_delta_indiv=st.mean(pdi.values()) if pdi else None,
                          paired_delta_inst=st.mean(pdn.values()) if pdn else None,
                          paired_diff=pobs, paired_ci_lo=plo, paired_ci_hi=phi,
                          paired_p=_p(preps, pobs),
                          n_clusters=len(pcl), n_paired_cells=len(pc)))
    json.dump(dict(_what="prompts ending 'I should', F21+M03 pooled, mass-weighted "
                         "E[scale|rated] per arm and position",
                   n_prompts=len(prompts), rows=saved),
              open(os.path.join(OUT, "ishould.json"), "w"), indent=1)
    print("\n-> results/base_side/ishould.json")


if __name__ == "__main__":
    main()
