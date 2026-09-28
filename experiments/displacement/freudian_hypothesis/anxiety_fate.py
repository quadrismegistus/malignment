"""Freud's vicissitudes of the barred affect, by the words that arrive. -> results/anxiety_fate.md, .json

    python -u anxiety_fate.py            print
    python -u anxiety_fate.py --write

Declared 2026-09-28 before it ran (RH: "anger -> fear is Freud's 'becomes anxiety'
vicissitude ... yes run that"). `feeling_carry.py`'s type arm found ~68% of the mass leaving
anger words lands on AFFECTLESS words, and that `kill` (doer anger) -> `scream` (doer fear) is
anger -> fear on the word-alone rating: the anxiety fate, not a failed carry. This asks
whether that fate is systematic, and whether it exceeds what the scene already supplies.

## THE UNIT AND THE RATINGS

Per (lineage, charged English prompt), 50 endpoint lineages, barred = act >= 4 departing
words, as the rest of this folder. Every word's TYPE `doer_feeling` from
`slot_ratings/affect/type_task.py` (the person who performs or undergoes it); unratable
words (function words) are out of every side; the >= 80% coverage gate on barred, arriving
and the scene's non-barred base mass, as `feeling_carry.py`'s type arm.

## THE FATES OF THE BARRED MASS, by the barred mass's dominant named feeling X

    SUPPRESSION    arriving mass on affectless words (doer_feeling none)
    KEPT           arriving mass on words of feeling X
    ANXIETY        arriving mass on FEAR words, X != fear
    RECOLOURED     arriving mass on another named feeling

## THE TEST, AGAINST THE SCENE

Per cell with X != fear: fear's share of the AFFECTIVE arriving mass minus fear's share of the
scene's AFFECTIVE non-barred base mass (p_base-weighted). Per lineage the mean over cells
(>= 10 cells); median over lineages, two-sided sign test, ties dropped. > 0: the arrivals turn
to fear beyond the scene's own fear -- the anxiety vicissitude. The same contrast for KEPT (X's
share among affective arrivals minus among the scene's affective words) is reported beside it.

Reported beside: among AFFECTIVE arrivals only, their IN-CONTEXT feeling (affect task, where
rated), so the reading "scream in an anger scene is anger's outlet" is visible next to the
word-alone "scream is fear".
"""
import argparse, collections, csv, gzip, json, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
TYPE = os.path.expanduser("~/malignment-data/affect_proportionality/type_feeling.parquet")
CTX = os.path.expanduser("~/malignment-data/affect_proportionality/affect_proportionality.parquet")
OUT = os.path.join(HERE, "results", "anxiety_fate")
MIN_ACT, COVER = 4.0, 0.80
NAMED = ["anger", "fear", "desire", "grief", "disgust", "shame", "tenderness", "joy"]


def sign_p(v):
    v = [x for x in v if x != 0]
    n = len(v); k = sum(1 for x in v if x > 0); k = min(k, n - k)
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n) if n else float("nan")


def summ(v):
    v = [x for x in v if x == x]
    if len(v) < 4:
        return None
    q = st.quantiles(v, n=4)
    return dict(median=st.median(v), iqr=[q[0], q[-1]], pos=sum(x > 0 for x in v), neg=sum(x < 0 for x in v), n=len(v), p=sign_p(v))


def compute():
    import pyarrow.parquet as pq
    from departing_arriving import norms
    from malignment import roster
    F, _ = norms()
    tf, unrat = {}, set()
    for r in pq.read_table(TYPE).to_pylist():
        if r["ok"]:
            (tf.__setitem__(r["word"], r["doer_feeling"]) if r["ratable"] else unrat.add(r["word"]))
    ctxf = {}
    for r in pq.read_table(CTX).to_pylist():
        if r["ok"] and r.get("echo_ok") and r["word"] and r.get("ratable"):
            ctxf[(r["prompt"], r["word"])] = r["feeling"]
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    Z = lambda: dict(t=0.0, c=collections.Counter(), ctx=collections.Counter())
    cell = collections.defaultdict(lambda: dict(b=Z(), a=Z(), s=Z()))
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            w = r["word"]
            if w in unrat:
                continue
            d = float(r["delta"]); x = act(w); barred = x is not None and x >= MIN_ACT
            c = cell[(r["base"], r["prompt"])]; fe = tf.get(w)
            sides = []
            if barred and d < 0:
                sides.append(("b", -d))
            elif not barred and d > 0:
                sides.append(("a", d))
            if not barred:
                sides.append(("s", float(r["p_base"] or 0)))
            for side, m in sides:
                c[side]["t"] += m
                if fe:
                    c[side]["c"][fe] += m
                    if side == "a" and fe != "none":
                        cf = ctxf.get((r["prompt"], w))
                        if cf:
                            c[side]["ctx"][(fe, cf)] += m
    fates = collections.defaultdict(lambda: collections.Counter())   # X -> fate -> mass
    anx, kept = collections.defaultdict(list), collections.defaultdict(list)
    ctx_of_affective = collections.Counter()
    ncell = 0
    for (lin, pr), c in cell.items():
        if c["b"]["t"] <= 0 or c["a"]["t"] <= 0 or c["s"]["t"] <= 0:
            continue
        if not all(sum(c[k]["c"].values()) >= COVER * c[k]["t"] and sum(c[k]["c"].values()) > 0 for k in "bas"):
            continue
        b = c["b"]["c"]
        named = {f: v for f, v in b.items() if f != "none"}
        if not named:
            continue
        ncell += 1
        X = max(named, key=named.get)
        a = c["a"]["c"]; at = sum(a.values())
        aff_a = {f: v for f, v in a.items() if f != "none"}; ta = sum(aff_a.values())
        fates[X]["suppression"] += a.get("none", 0) / at
        fates[X]["kept"] += a.get(X, 0) / at
        fates[X]["anxiety" if X != "fear" else "kept_fear"] += (a.get("fear", 0) / at) if X != "fear" else 0
        fates[X]["recoloured"] += sum(v for f, v in aff_a.items() if f not in (X, "fear")) / at
        fates[X]["cells"] += 1
        sc = {f: v for f, v in c["s"]["c"].items() if f != "none"}; ts = sum(sc.values())
        if ta > 0 and ts > 0:
            if X != "fear":
                anx[lin].append(aff_a.get("fear", 0) / ta - sc.get("fear", 0) / ts)
            kept[lin].append(aff_a.get(X, 0) / ta - sc.get(X, 0) / ts)
        for k, v in c["a"]["ctx"].items():
            ctx_of_affective[k] += v
    A = summ([st.fmean(v) for v in anx.values() if len(v) >= 10])
    K = summ([st.fmean(v) for v in kept.values() if len(v) >= 10])
    fate_tab = {X: {k: (v / f["cells"] if k != "cells" else v) for k, v in f.items()} for X, f in fates.items()}
    return dict(n_cells=ncell, anxiety_vs_scene=A, kept_vs_scene=K, fates=fate_tab,
                ctx_of_affective={"%s|%s" % k: v for k, v in ctx_of_affective.items()})


def report(r):
    f = lambda s: "--" if not s else "%+.3f [%+.3f, %+.3f] +%d/-%d of %d, p=%.2g" % (s["median"], s["iqr"][0], s["iqr"][1], s["pos"], s["neg"], s["n"], s["p"])
    L = ["# Freud's vicissitudes of the barred affect, by the words that arrive", "",
         "Producer `anxiety_fate.py` (declared in its docstring before it ran). Word-alone `doer_feeling`; %d gated cells whose barred mass carries a named feeling." % r["n_cells"], "",
         "- **ANXIETY beyond the scene** (barred feeling X != fear; fear's share of AFFECTIVE arrivals minus its share of the scene's affective words): %s" % f(r["anxiety_vs_scene"]),
         "- **KEPT beyond the scene** (X's share of affective arrivals minus its share of the scene's affective words): %s" % f(r["kept_vs_scene"]), "",
         "Fates of the barred mass, by its dominant named feeling X (mean share of arriving mass per cell):", "",
         "| X (barred) | cells | suppression (affectless) | kept (X) | anxiety (fear) | recoloured (other) |", "|---|---|---|---|---|---|"]
    for X in NAMED:
        t = r["fates"].get(X)
        if not t:
            continue
        L.append("| %s | %d | %.2f | %.2f | %s | %.2f |" % (X, t["cells"], t.get("suppression", 0), t.get("kept", 0),
                 "--" if X == "fear" else "%.2f" % t.get("anxiety", 0), t.get("recoloured", 0)))
    L += ["", "Affective arrivals, word-alone feeling against IN-CONTEXT feeling (mass, where the affect task rated them):", "",
          "| alone \\\\ in context | " + " | ".join(NAMED + ["none"]) + " |", "|---|" + "---|" * (len(NAMED) + 1)]
    M = collections.defaultdict(dict)
    for k, v in r["ctx_of_affective"].items():
        x, y = k.split("|"); M[x][y] = v
    for x in NAMED:
        tot = sum(M[x].values())
        if tot > 0:
            L.append("| %s | %s |" % (x, " | ".join(("**%.2f**" if y == x else "%.2f") % (M[x].get(y, 0) / tot) for y in NAMED + ["none"])))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    r = compute(); md = report(r); print(md)
    if a.write:
        json.dump(r, open(OUT + ".json", "w"), indent=1); open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
