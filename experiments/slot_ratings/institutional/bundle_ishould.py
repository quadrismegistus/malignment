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
                          n_lineages=len(lins), n_prompts=len(pi) + len(pn)))
    json.dump(dict(_what="prompts ending 'I should', F21+M03 pooled, mass-weighted "
                         "E[scale|rated] per arm and position",
                   n_prompts=len(prompts), rows=saved),
              open(os.path.join(OUT, "ishould.json"), "w"), indent=1)
    print("\n-> results/base_side/ishould.json")


if __name__ == "__main__":
    main()
