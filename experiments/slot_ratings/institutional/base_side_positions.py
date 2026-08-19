"""Was the base already proceduralised? All THREE position corpora, as levels.

    python experiments/slot_ratings/institutional/base_side_positions.py
    python experiments/slot_ratings/institutional/base_side_positions.py --corpus m03

## THIS SUPERSEDES base_side_f21.py, WHICH USED THE WRONG POPULATION

`base_side_f21.py` read `twp_words_v4_best` and got 8 lineages. `run_f21.py` and
`run_m03.py` read the `movement` table, which holds all 50 endpoint pairs, so the
level measure was being decomposed against movement results computed on a
different and much larger population. `movement` carries `p_base` and
`p_aligned` directly and sums to 0.76-0.93 of the distribution per cell, so it is
both the correct source and the better one. Numbers here replace those.

## WHY ONE CORPUS IS NOT ENOUGH, AND THESE THREE IN PARTICULAR

The three differ in how they control the grammatical site, which is a first-order
confound: changing `I should ___` (bare infinitive) to `...and I ___` (finite
verb) moves `procedural` by +0.221, LARGER than the position contrast itself.

    F21       24 prompts   MIXED sites (`I should`, `We should`, `I said`).
                           Position and site are confounded. Cannot separate.
    M03      252 prompts   Site held fixed by frame specification, and POSITION
                           is crossed with PERSON (I/we) and MODAL (absent /
                           final / final_ought / medial). The gap is computed
                           WITHIN each (person, modal) stratum, so the site
                           difference cannot carry it. `absent` is a finite-verb
                           slot, so it is a stratum, never pooled with the rest.
    slotpov   12 prompts   Both sides end at the IDENTICAL site, `so X decided
                           to`, by construction. Smallest, cleanest.

Agreement across three corpora with different site exposure is the evidence.
F21 on its own cannot tell a position effect from a site effect.

## THE MEASURE

    E[scale | rated] = sum_w p(w) * rating(w) / sum_w p(w)

per arm, no eligibility gate, arms A and B merged. Then

    aligned_gap = base_gap + delta_gap

F21's "deference already present in pretraining" predicts base_gap carries most
of aligned_gap. Its "proceduralises the individual not the institution" is a
claim about delta and is reported separately.
"""

import argparse, collections, glob, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(SLOT))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results", "base_side")
KERNEL = ("/Users/rj416/github/malign-logits/meta/M03_proceduralization/"
          "m03_kernel_full.json")


def merge(paths):
    """The three runners each chose a different container for the same payload.

    f21      {"prompts": [{prompt, ratings}]}
    m03      {"cells":   [{prompt, ratings}]}
    slotpov  {"pairs":   [[matched_set, [{prompt, ratings}, ...]]]}

    So walk the structure for anything carrying both keys rather than naming a
    container. Assuming one shape is how this returned 0 scales on the first run
    and printed an empty table instead of failing.
    """
    R = collections.defaultdict(dict)
    def walk(o):
        if isinstance(o, dict):
            if "prompt" in o and isinstance(o.get("ratings"), dict):
                for w, r in o["ratings"].items():
                    R[(o["prompt"], w)].update(r)
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for f in paths:
        walk(json.load(open(f)))
    if not R:
        raise SystemExit("merge() found no (prompt, ratings) in %d files" % len(paths))
    return R


def corpus_f21():
    from run_f21 import prompts
    R = merge(sorted(glob.glob(os.path.join(
        HERE, "results", "m03", "rated_f21_slot_institutional_en_v3_arm*.json"))))
    items = [dict(prompt=p["prompt"], position=p["position"], stratum="all")
             for p in prompts()]
    return items, R


def corpus_m03():
    R = merge(sorted(glob.glob(os.path.join(
        HERE, "results", "m03", "rated_slot_institutional_en_v3_m03_*_arm*.json"))))
    k = json.load(open(KERNEL))
    items = []
    for sc in (k if isinstance(k, list) else list(k.values())[0]):
        cells = sc["cells"]
        for cid, txt in (cells if isinstance(cells, list) else cells.items()):
            parts = cid.split("_")
            if parts[0] not in ("indiv", "inst"):
                continue
            #: PERSON and MODAL become the stratum, so the position gap is only
            #: ever taken between cells that share a grammatical site.
            items.append(dict(prompt=txt, position=parts[0],
                              stratum="_".join(parts[1:]), scenario=sc["scenario_id"]))
    return items, R


def corpus_slotpov():
    from run_slotpov import pairs as povpairs
    R = merge(sorted(glob.glob(os.path.join(
        HERE, "results", "slotpov", "rated_slot_institutional_en_v3_arm*.json"))))
    items = []
    for ms, v in povpairs():
        for i in v:
            items.append(dict(prompt=i["prompt"], position=i["position"], stratum=ms))
    return items, R


#: EACH CORPUS USES THE SOURCE ITS OWN PRODUCER USED. run_f21 and run_m03 read
#: the `movement` table; run_slotpov computes movement on the fly from
#: twp_words_v4_best, and its 12 slot prompts have ZERO rows in `movement`
#: (checked, not assumed). Using one source for all three would have silently
#: dropped slotpov, which is the corpus with the cleanest site control.
CORPORA = {"f21": (corpus_f21, "movement"), "m03": (corpus_m03, "movement"),
           "slotpov": (corpus_slotpov, "twp")}


def levels(items, R, source="movement"):
    """E[scale|rated] and coverage per (prompt, lineage, arm)."""
    from malignment import roster, vectors as V
    ep = sorted(roster.endpoints()[0].items())
    texts = sorted({i["prompt"] for i in items})
    scales = sorted({k for v in R.values() for k in v})
    if source == "movement":
        rows = V.rows("SELECT prompt, base, aligned, word, p_base, p_aligned "
                      "FROM movement WHERE prompt IN {ps:Array(String)} "
                      "AND (base, aligned) IN {bs:Array(Tuple(String,String))}",
                      ps=texts, bs=ep)
    else:
        ms = sorted({m for pair in ep for m in pair})
        q = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                   "FROM twp_words_v4_best WHERE prompt IN {ts:Array(String)} "
                   "AND model IN {ms:Array(String)} GROUP BY prompt, model",
                   ts=texts, ms=ms)
        store = collections.defaultdict(dict)
        for r in q:
            store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))
        rows = []
        for t in texts:
            for b, a in ep:
                pb, pa = store[t].get(b), store[t].get(a)
                if not pb or not pa:
                    continue
                for w in set(pb) | set(pa):
                    rows.append(dict(prompt=t, base=b, aligned=a, word=w,
                                     p_base=pb.get(w, 0.0), p_aligned=pa.get(w, 0.0)))
    acc = collections.defaultdict(lambda: collections.defaultdict(float))
    for r in rows:
        k = (r["prompt"], r["base"] + " -> " + r["aligned"])
        acc[k]["_mass_base"] += r["p_base"]
        acc[k]["_mass_aligned"] += r["p_aligned"]
        rt = R.get((r["prompt"], r["word"]))
        if not rt:
            continue
        for s, v in rt.items():
            if v is None:
                continue
            acc[k]["b_" + s] += r["p_base"] * v
            acc[k]["bm_" + s] += r["p_base"]
            acc[k]["a_" + s] += r["p_aligned"] * v
            acc[k]["am_" + s] += r["p_aligned"]
    meta = {i["prompt"]: i for i in items}
    out = []
    for (p, lin), d in acc.items():
        rec = dict(prompt=p, lineage=lin, position=meta[p]["position"],
                   stratum=meta[p]["stratum"],
                   mass_base=d["_mass_base"], mass_aligned=d["_mass_aligned"])
        for s in scales:
            if d.get("bm_" + s, 0) > 0:
                rec["base_" + s] = d["b_" + s] / d["bm_" + s]
                rec["cov_base_" + s] = d["bm_" + s] / max(d["_mass_base"], 1e-9)
            if d.get("am_" + s, 0) > 0:
                rec["aligned_" + s] = d["a_" + s] / d["am_" + s]
                rec["cov_aligned_" + s] = d["am_" + s] / max(d["_mass_aligned"], 1e-9)
        out.append(rec)
    return out, scales


def gaps(rows, scales, min_per_side=1):
    #: min_per_side=1 because slotpov's stratum is a matched PAIR: exactly one
    #: prompt per side by construction. Requiring 2 emptied that corpus and
    #: printed a blank table rather than failing -- 32 lineages, 384 cells, and
    #: no rows. F21 has one stratum holding 12 prompts a side and M03 has 7
    #: strata holding 18, so neither is affected by the looser floor.
    """Per lineage: inst minus indiv, averaged over strata that hold BOTH sides."""
    from scipy import stats
    L = sorted({r["lineage"] for r in rows})
    res = []
    for s in scales:
        bg, ag, di, dn = [], [], [], []
        for l in L:
            v = [r for r in rows if r["lineage"] == l]
            sb, sa, ei, en = [], [], [], []
            for stx in sorted({r["stratum"] for r in v}):
                w = [r for r in v if r["stratum"] == stx]
                def m(arm, pos):
                    x = [r["%s_%s" % (arm, s)] for r in w if r["position"] == pos
                         and r.get("%s_%s" % (arm, s)) is not None]
                    return st.mean(x) if len(x) >= min_per_side else None
                bi, bn = m("base", "inst"), m("base", "indiv")
                ai, an = m("aligned", "inst"), m("aligned", "indiv")
                if None in (bi, bn, ai, an):
                    continue
                sb.append(bi - bn); sa.append(ai - an)
                ei.append(an - bn); en.append(ai - bi)
            if not sb:
                continue
            bg.append(st.mean(sb)); ag.append(st.mean(sa))
            di.append(st.mean(ei)); dn.append(st.mean(en))
        if len(bg) < 6:
            continue
        dg = [a - b for a, b in zip(ag, bg)]
        res.append(dict(
            scale=s, n=len(bg), base_gap=st.median(bg), aligned_gap=st.median(ag),
            delta_gap=st.median(dg), p_base=stats.wilcoxon(bg).pvalue,
            p_delta=stats.wilcoxon(dg).pvalue,
            base_pos=sum(1 for x in bg if x > 0),
            d_indiv=st.median(di), d_inst=st.median(dn),
            p_movediff=stats.wilcoxon(di, dn).pvalue,
            inherited=(st.median(bg) / st.median(ag)) if abs(st.median(ag)) > 0.05 else None))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=sorted(CORPORA))
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    allres = {}
    for name in ([a.corpus] if a.corpus else ["slotpov", "f21", "m03"]):
        fn, source = CORPORA[name]
        items, R = fn()
        rows, scales = levels(items, R, source)
        L = sorted({r["lineage"] for r in rows})
        print("\n" + "=" * 86)
        print("%s [%s]: %d prompts, %d strata, %d lineages, %d cells, %d scales"
              % (name.upper(), source, len({i["prompt"] for i in items}),
                 len({i["stratum"] for i in items}), len(L), len(rows), len(scales)))
        cov = [r["cov_base_procedural"] for r in rows if r.get("cov_base_procedural")]
        if cov:
            print("   rated share of movement mass, procedural: median %.3f "
                  "(IQR %.3f-%.3f)"
                  % (st.median(cov), *[sorted(cov)[int(len(cov) * q)] for q in (.25, .75)]))
        res = gaps(rows, scales)
        print("\n   %-14s %3s %9s %9s %9s %9s %9s %9s"
              % ("scale", "n", "base gap", "algn gap", "delta", "p base", "p delta", "inherit"))
        for r in sorted(res, key=lambda r: r["p_base"]):
            print("   %-14s %3d %+9.3f %+9.3f %+9.3f %9.2g %9.2g %9s"
                  % (r["scale"], r["n"], r["base_gap"], r["aligned_gap"], r["delta_gap"],
                     r["p_base"], r["p_delta"],
                     ("%.0f%%" % (100 * r["inherited"])) if r["inherited"] else "-"))
        print("\n   DOES ALIGNMENT MOVE THE INDIVIDUAL MORE?")
        print("   %-14s %10s %10s %9s" % ("scale", "d indiv", "d inst", "p"))
        for r in sorted(res, key=lambda r: r["p_movediff"])[:6]:
            print("   %-14s %+10.4f %+10.4f %9.2g %s"
                  % (r["scale"], r["d_indiv"], r["d_inst"], r["p_movediff"],
                     #: SIGNED, not abs(). An earlier version compared magnitudes,
                     #: which labelled "the individual falls further" identically
                     #: to "the individual rises further" and so reported agency as
                     #: replicating on all three corpora when M03's sign is
                     #: opposite to the other two.
                     "INDIV PUSHED FURTHER" if r["d_indiv"] - r["d_inst"] > 0
                     and r["p_movediff"] < .05 else
                     "INST PUSHED FURTHER" if r["p_movediff"] < .05 else ""))
        allres[name] = dict(n_lineages=len(L), n_cells=len(rows), results=res)
        json.dump(dict(_what="mass-weighted E[scale] per (prompt, lineage, arm) "
                             "from the `movement` table; gap taken within stratum",
                       rows=rows, results=res),
                  open(os.path.join(OUT, "%s.json" % name), "w"), indent=1)
    json.dump(allres, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print("\n-> results/base_side/{f21,m03,slotpov}.json + summary.json")


if __name__ == "__main__":
    main()
