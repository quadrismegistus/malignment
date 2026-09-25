"""USAS E (emotion) through the same precision-first rating as X. (RH, 2026-09-25: "follow same procedure more or less for both")

    .venv/bin/python -u interiority_precision_e.py --items      count the pool, print, write nothing
    .venv/bin/python -u interiority_precision_e.py --pilot      two batches, printed
    .venv/bin/python -u interiority_precision_e.py --run        passes 1 and 2 -> precision_e_ratings_v2.parquet
    .venv/bin/python -u interiority_precision_e.py --fill       re-rate forms a pass lost -> precision_e_ratings_v2_fill*.parquet
    .venv/bin/python -u interiority_precision_e.py --tiebreak   pass 3 where passes 1 and 2 disagree
    .venv/bin/python -u interiority_precision_e.py --consensus  -> precision_e_keep_v2.csv, INTERIORITY_PRECISION_E.md

WHY. X's lists took their emotion vocabulary only as NEIGHBOURS of X; 29% of USAS E's token mass over
arc_fiction was covered and 53% had never been rated (sad, hate, misery, relief, suffering...). The
emotion panel carries the eighteenth-century peak, so E gets the X procedure.

ITEMS, in the X procedure's shape:
  - SEEDS: every USAS E word, primary sense in any POS entry (the abstraction seat's usase_seeds.csv,
    1,562; the same rule as X's seeds);
  - CANDIDATES: the seat's period-model neighbours of E (usase_neighbours_candidates.csv, the X script
    run with --field E), pooled under X's rule -- corpus count >= 500 and >= 5 seeds in some century
    (X also required the seeds to be non-perception; E has no such subfield unless the seat's check says so);
  - MorphAdorner variants of both, shown as "(old spelling of: X)", as in interiority_precision.py.
  A form ALREADY RATED by interiority_precision.py (15,099 forms) is not re-rated: it keeps that
  consensus, since the task, prompt, model and anchors are identical.

THE TASK is interiority_precision.py's, imported unchanged (system prompt, schema, deepseek-v4-flash at
temperature 0, 40 forms a call, the four anchors in every batch; every call carries the echo line
X's fills added ("Return each form EXACTLY as given"), because without it the pilot lost 31 of 80 old
spellings to modernised echoes, two shuffled passes, fills, a tie-break
where the passes disagree, anchor-flipped tie-break batches dropped, ties rejected). RH's hand removals
there were made for INTERIORITY; they are recorded here as a flag and NOT applied, pending RH's decision
for the emotion list (happy, fear, love). EXPLORATORY.
"""
import collections, os, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import interiority_precision as P                          # noqa: E402

SHARED = P.SHARED
SEEDS = os.path.join(SHARED, "usase_seeds.csv")
CAND = os.path.join(SHARED, "usase_neighbours_candidates.csv")
OUT = os.path.join(SHARED, "precision_e_ratings_v2.parquet")
OUT3 = os.path.join(SHARED, "precision_e_ratings_v2_pass3.parquet")
FILLS = [os.path.join(SHARED, "precision_e_ratings_v2_fill%s.parquet" % s) for s in ("", "2", "3", "4")]
KEEP_CSV = os.path.join(SHARED, "precision_e_keep_v2.csv")
MIN_COUNT, MIN_SEEDS = 500, 5


def items():
    """-> [(form, spelling_of or None, source)], source in seed | cand | variant:<...>; forms rated in v2 excluded."""
    import arc_interiority as A
    prior = set(pd.read_csv(P.KEEP_CSV).form) | set(P.ANCHORS)
    s = pd.read_csv(SEEDS)
    seeds = {w.lower() for w in s.word if isinstance(w, str) and w.isalpha()}
    c = pd.read_csv(CAND)
    pool = c[(c["count"] >= MIN_COUNT) & (c.n_seeds >= MIN_SEEDS)]
    cand = {w.lower() for w in pool.neighbour if isinstance(w, str) and w.isalpha()} - seeds
    base = {w: "seed" for w in seeds}
    base.update({w: "cand" for w in cand})
    var = collections.defaultdict(set)
    for line in open(A.MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            v, m = p[0].lower(), p[1].lower()
            if m in base and v not in base:
                var[v].add(m)
    out = [(w, None, src) for w, src in sorted(base.items()) if w not in prior]
    out += [(v, ", ".join(sorted(ms)), "variant:" + "+".join(sorted({base[m] for m in ms})))
            for v, ms in sorted(var.items()) if v not in prior]
    info = dict(seeds=len(seeds), cand_pool=len(cand), base=len(base), variants=len(var),
                already_rated=len(base) + len(var) - len(out), to_rate=len(out),
                anchors_in_pool=sorted(set(P.ANCHORS) & (set(base) | set(var))))
    return out, info


def main():
    its, info = items()
    print(info)
    if "--items" in sys.argv:
        return
    if "--pilot" in sys.argv:
        rows, miss, extra, nerr = P.rate(P.make_batches(its, echo=True)[:2], workers=2)
        d = pd.DataFrame(rows)
        print("pilot: %d rows, %d missing, %d extra, %d failed" % (len(d), miss, extra, nerr))
        print(d.sort_values(["keep", "kind"]).to_string(index=False))
    elif "--run" in sys.argv:
        assert not os.path.exists(OUT), "refusing to overwrite " + OUT
        rows, miss, extra, nerr = P.rate(P.make_batches(its, echo=True))
        pd.DataFrame(rows).to_parquet(OUT, index=False)
        print("-> %s: %d rows; %d missing, %d extra, %d failed calls" % (OUT, len(rows), miss, extra, nerr))
    elif "--fill" in sys.argv:
        dest = next(x for x in FILLS if not os.path.exists(x))
        d = rated()
        d = d[~d.anchor]
        of = {f: o for f, o, _ in its}
        pool = [f for f, _, _ in its if f not in P.ANCHORS]
        rows, stats = [], []
        for ps in (1, 2):
            got = set(d[d.pass_ == ps].form)
            sub = [(f, of[f], None) for f in pool if f not in got]
            if not sub:
                continue
            r, miss, extra, nerr = P.rate(P.make_batches(sub, passes=(ps,), seed=P.SEED + 10 + ps, echo=True))
            rows += r
            stats.append("pass %d: %d lost, %d still missing, %d extra, %d failed calls" % (ps, len(sub), miss, extra, nerr))
        if not stats:
            print("nothing lost; no fill written")
            return
        pd.DataFrame(rows).to_parquet(dest, index=False)
        print("-> %s\n  " % dest + "\n  ".join(stats))
    elif "--tiebreak" in sys.argv:
        assert not os.path.exists(OUT3), "refusing to overwrite " + OUT3
        d = rated()
        w = d[~d.anchor].pivot_table(index="form", columns="pass_", values="keep", aggfunc="first").dropna()
        dis = set(w.index[w[1] != w[2]])
        of = {f: o for f, o, _ in its}
        rows, miss, extra, nerr = P.rate(P.make_batches([(f, of[f], None) for f in sorted(dis)], passes=(3,), seed=P.SEED + 3, echo=True))
        pd.DataFrame(rows).to_parquet(OUT3, index=False)
        print("-> %s: %d forms; %d missing, %d extra, %d failed calls" % (OUT3, len(dis), miss, extra, nerr))
    elif "--consensus" in sys.argv:
        consensus(its, info)


def rated():
    #: each row carries its file: fills reuse (pass_, batch) numbers, so a batch is (src, pass_, batch)
    return pd.concat([pd.read_parquet(x).assign(src=os.path.basename(x)) for x in [OUT] + FILLS if os.path.exists(x)])


def consensus(its, info):
    """interiority_precision.consensus's rules, over this pool."""
    d = pd.concat([rated()] + ([pd.read_parquet(OUT3).assign(src=os.path.basename(OUT3))] if os.path.exists(OUT3) else []))
    key = list(zip(d.src, d.pass_, d.batch))
    a = d[d.anchor]
    flipped = a[a.form.map(P.ANCHOR_KEEP) != a.keep]
    fb = set(zip(flipped.src, flipped.pass_, flipped.batch))
    #: X saw anchor flips only in its tie-break (2 of 73). Here two MAIN-run batches flipped as well, both
    #: with the reject-everything signature (pass 1 batch 162 kept 0 of 44, batch 433 kept 1 of 44): a batch
    #: whose anchors moved has lost calibration and does not vote, wherever it sits. Capped, so a drifting
    #: rater cannot be cleaned into agreement by discarding its batches.
    main_b = {k for k in set(key) if k[1] in (1, 2)}
    tb_b = {k for k in set(key) if k[1] == 3}
    fb_main, fb_tb = fb & main_b, fb & tb_b
    assert len(fb_main) <= 0.01 * len(main_b), ("too many main-run batches lost calibration", len(fb_main), len(main_b))
    assert len(fb_tb) <= 0.05 * max(len(tb_b), 1), ("too many tie-break batches lost calibration", len(fb_tb), len(tb_b))
    lost_forms = set(d[pd.Series([k in fb for k in key], index=d.index).values & ~d.anchor.values].form)
    d = d[[k not in fb for k in key]]
    anc = d[d.anchor].groupby("form").keep.agg(lambda s: sorted(set(s)))
    for x, want in P.ANCHOR_KEEP.items():
        assert anc.get(x) == [want], ("anchor moved", x, anc.get(x))
    d = d[~d.anchor]
    #: dreaded and regretted are E words AND the keep-anchors; make_batches never shows an anchor as an
    #: item, so their rating is their anchor rating, stable by the assert above (kind emotion, as rated)
    anc_in = [f for f, _, _ in its if f in P.ANCHORS]
    for f in anc_in:
        r = pd.DataFrame([dict(form=f, pass_=0, batch=-1, keep=P.ANCHOR_KEEP[f], kind="emotion",
                               competing_sense=None, anchor=False)])
        d = pd.concat([d, r])
    g = d.groupby("form")
    n = g.keep.size()
    K = pd.DataFrame({"keep": g.keep.agg(lambda s: bool(sum(s) * 2 > len(s))),
                      "kind": g.kind.agg(lambda s: collections.Counter(s).most_common(1)[0][0]),
                      "competing_sense": g.competing_sense.agg(lambda s: next((x for x in s if x), None)),
                      "n_ratings": n})
    src = {f: s for f, _, s in its}
    of = {f: o for f, o, _ in its}
    K["source"] = [src[f] for f in K.index]
    K["spelling_of"] = [of[f] for f in K.index]
    K["rh_removed_for_interiority"] = [f in P.RH_REMOVED for f in K.index]
    assert not os.path.exists(KEEP_CSV), "refusing to overwrite " + KEEP_CSV
    K.reset_index().rename(columns={"index": "form"}).to_csv(KEEP_CSV, index=False)
    agree = d[d.pass_.isin([1, 2])].pivot_table(index="form", columns="pass_", values="keep", aggfunc="first").dropna()
    base = K[K.spelling_of.isna()]
    L = ["# USAS E through the precision-first rating (EXPLORATORY)", "",
         "Producer `interiority_precision_e.py`. %s. Task, prompt, model and anchors are interiority_precision.py's, "
         "imported unchanged; forms it already rated keep its consensus and are not here. Per form: %s." % (
             ", ".join("%s %s" % (k, v) for k, v in info.items()), KEEP_CSV), "",
         "- pass 1 vs pass 2 agreement on keep: %.1f%%" % (100 * float((agree[1] == agree[2]).mean())),
         "- ties rejected, precision first: %d" % int((g.keep.sum() * 2 == n).sum()),
         "- batches dropped because an anchor flipped: main run %d of %d, tie-break %d of %d; %d forms lost one "
         "rating to them and are decided by the rest" % (len(fb_main), len(main_b), len(fb_tb), len(tb_b), len(lost_forms)), "",
         "| | forms | kept | kept % |", "|---|---|---|---|"]
    for lab, sub in (("E seeds", base[base.source == "seed"]), ("E neighbour candidates", base[base.source == "cand"]),
                     ("MorphAdorner variants", K[K.spelling_of.notna()])):
        L.append("| %s | %d | %d | %.1f%% |" % (lab, len(sub), int(sub.keep.sum()), 100 * float(sub.keep.mean()) if len(sub) else 0))
    L += ["", "Kept base words by kind: " + ", ".join("%s %d" % (k, int(v)) for k, v in base[base.keep].kind.value_counts().items()),
          "", "RH's interiority removals among these forms (flagged, not applied): " + ", ".join(sorted(K.index[K.rh_removed_for_interiority]))]
    open(os.path.join(HERE, "INTERIORITY_PRECISION_E.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
