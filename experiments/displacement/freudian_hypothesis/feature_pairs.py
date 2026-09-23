"""Which COMBINATIONS of rated features does alignment move, and does the
direction change with charge? -> results/feature_pairs/<cut>.md, SWEEP.md;
~/malignment-data/norm_change/feature_pairs/<cut>.json

    python -u feature_pairs.py                     sweep every cut in CUTS
    python -u feature_pairs.py --cut fixed:4/6     one cut
    python -u feature_pairs.py --rebuild           re-read the movement table

**EXPLORATORY, AND SAID SO ON PURPOSE.** Written by the paper seat
(TheoryMachines) on 2026-09-23 at RH's request, as a fishing expedition over
pairs of scales: "I don't care if it's a fishing expedition. I like fishing."
Nothing here is registered. A result from this file becomes quotable only when
it is rerun under a cut declared before looking, or when it recurs across the
whole sweep (see SWEEP.md), and even then it is a pointer to a registered test,
not the test.

## WHY PAIRS

`departing_arriving.py` profiles the moved mass one scale at a time, and one
scale at a time is how `v6:aggression` came back flat (+0.011, 21/50) while
`v6:vocalisation` rose. A flat scale can hide two opposite movements in two
kinds of word, and only a second scale can separate them: `directedness` nets
to zero because drive frames lose targets while grievance and intimacy frames
gain them (paper seat, 2026-09-23). So every pair of scales is crossed into
four cells, and each cell is followed separately.

## THE STATISTIC IS THE LEDGER'S

Per lineage, over the English movement rows rated on BOTH scales of a pair:

    arriving share of the cell   sum(d, d > 0, in cell) / sum(d, d > 0)
    departing share of the cell  sum(|d|, d < 0, in cell) / sum(|d|, d < 0)
    flow                         arriving share - departing share

then a sign test over lineages (ties dropped), and Benjamini-Hochberg over
EVERY test in one cut (all pairs x four cells x four bands). Shares and not raw
mass, because the aligned arm is more peaked and a larger share of it sits above
the store floor (the window diagnostic in `departing_arriving.py`: arriving over
departing is 1.97 by raw mass), so raw gains exceed raw losses almost
everywhere and mean nothing.

Bands are lift tertiles cut over the movement rows (`charge.lifts_per_lineage`,
keyed on prompt and base); "all" includes rows with no lift.

## THE CUT IS A CHOICE, SO IT IS SWEPT

A scale enters a cell as HIGH or LOW, and where the line falls decides what a
cell contains. At Warriner valence 6 "unpleasant" takes in every neutral word,
and "have", "take" and "put" carry the cell; at a stricter line the cell holds
scream, cry, uneasy. So the cut is a parameter:

    fixed:C/W     HIGH = rating >= C on the 1-7 scales, >= W on Warriner's 1-9
    quant:Q       HIGH = rating > the Q-quantile of that scale's rated rows,
                  MASS-WEIGHTED by |d|, so a scale piled at 1 splits above 1

`SWEEP.md` counts, for every reversal, how many cuts find it. A reversal is a
cell whose flow is significant (q < 0.05) with opposite signs on the lowest and
highest lift thirds, each at |median| >= MIN_EFFECT. Near-empty cells (vulgarity
x anything) produce sign-test "reversals" around a median of 0.000, which is why
the effect floor exists.

## WHAT THIS CANNOT SHOW

- **Two instruments are mixed.** `inst:*` (slot_institutional_en_v3) covers
  2,511 prompts; `v6:*` (slot_rating_en_v6) another set; `k:*` and `w:*` are
  type-level. A pair is measured only on rows rated on both, so pairs differ in
  population, and a cell of one pair is not comparable with a cell of another.
- **Cells are not independent.** Four cells of one pair share denominators;
  pairs sharing a scale share rows. BH here controls a rate over dependent tests
  and is a screen, not a licence.
- **English only.** The zh arm is a quarter of the evidence per cell.
"""
import argparse, collections, csv, gzip, itertools, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
CACHE = os.path.expanduser("~/malignment-data/norm_change/feature_pairs_cache.npz")
OUT = os.path.join(HERE, "results", "feature_pairs")
#: the per-cut JSON is ~2 MB a file, so it lives outside the repo (RH: large
#: files go to ~/malignment-data); the .md reports stay here
OUT_DATA = os.path.expanduser("~/malignment-data/norm_change/feature_pairs")

CTX = ["harm", "aggression", "directedness", "vocalisation", "interiority",
       "deliberation", "superego", "hedged", "makes_better", "makes_worse",
       "fit", "mundanity"]
INST = ["arousal", "procedural", "agency", "assertiveness", "abstraction",
        "specificity", "deference", "termination", "mediation", "target",
        "collective", "delay"]
K = ["bodily_harm", "transgressiveness", "concreteness", "register_level",
     "vulgarity", "charge", "valence"]
W = ["valence", "arousal", "dominance"]
FEATS = (["v6:" + s for s in CTX] + ["inst:" + s for s in INST]
         + ["k:" + s for s in K] + ["w:" + s for s in W])
NF = len(FEATS)
IS_W = np.array([f.startswith("w:") for f in FEATS])

CUTS = ["fixed:3/5", "fixed:4/5", "fixed:4/6", "fixed:5/6", "fixed:5/7",
        "fixed:6/7", "quant:0.5", "quant:0.67", "quant:0.8"]
BANDS = {"all": None, "low": 0, "mid": 1, "high": 2}
MIN_ROWS = 100000      # a pair rated jointly on fewer rows is skipped
MIN_LIN = 25           # a cell needs this many lineages with both sides defined
MIN_EFFECT = 0.005     # |median| floor for a reversal, both thirds
Q = 0.05
N_WORDS = 10


def build():
    """The movement table joined to every rating, cached. -> dict of arrays"""
    from malignment import fields as F, roster, charge
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    idx = F._slot_index()
    lpl = charge.lifts_per_lineage()
    ctxc, kc = {}, {}

    def ctxvec(pr, w):
        v = ctxc.get((pr, w))
        if v is not None:
            return v
        v = np.full(len(CTX) + len(INST), np.nan, dtype=np.float32)
        by = idx.get((pr, w)) or {}
        #: **THE v6 RUBRIC IS FILED UNDER MORE THAN ONE INSTRUMENT NAME.**
        #: `_slot_index` names an instrument from the file or its directory, and
        #: the v6 ratings sit under "v6" (114,524 pairs, the name
        #: `departing_arriving.py` reads) and "slot_rating_en_v6" (21,544), which
        #: do not overlap. The first sweep of this file read only the second and
        #: so measured every v6 cell on a fifth of the rows. Both are read here,
        #: "v6" first. `v6full` and `v6_wide` are left out: separate runs whose
        #: equivalence to these has not been checked.
        for insts, names, off in ((("v6", "slot_rating_en_v6"), CTX, 0),
                                  (("slot_institutional_en_v3",), INST, len(CTX))):
            g = next((by[i] for i in insts if by.get(i)), {})
            for i, s in enumerate(names):
                x = g.get(s)
                if isinstance(x, (int, float)) and not isinstance(x, bool):
                    v[off + i] = x
        ctxc[(pr, w)] = v
        return v

    def kvec(w):
        v = kc.get(w)
        if v is not None:
            return v
        v = np.full(len(K) + len(W), np.nan, dtype=np.float32)
        k = F.k(w) or {}
        for i, s in enumerate(K):
            if s in k:
                v[i] = float(k[s])
        wn = F.word_norms(w) or {}
        for i, s in enumerate(W):
            if s in wn:
                v[len(K) + i] = float(wn[s])
        kc[w] = v
        return v

    L, LF, D, X, WID, FN = [], [], [], [], [], []
    lin_ix, word_ix = {}, {}
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs:
                continue
            d = float(row["delta"])
            if d == 0:
                continue
            pr, w = row["prompt"], row["word"]
            L.append(lin_ix.setdefault(row["base"], len(lin_ix)))
            lf = lpl.get((pr, row["base"]))
            LF.append(np.nan if lf is None else lf)
            D.append(d)
            WID.append(word_ix.setdefault(w, len(word_ix)))
            FN.append(row["is_function"] == "1")
            X.append(np.concatenate([ctxvec(pr, w), kvec(w)]))
    if len(lin_ix) != 50:
        raise SystemExit("expected 50 endpoint lineages, matched %d" % len(lin_ix))
    data = {"L": np.array(L, np.int32), "LF": np.array(LF), "D": np.array(D),
            "X": np.vstack(X), "WID": np.array(WID, np.int32), "FN": np.array(FN, bool),
            "words": np.array(sorted(word_ix, key=word_ix.get), dtype=object),
            "lineages": np.array(sorted(lin_ix, key=lin_ix.get), dtype=object),
            "feats": np.array(FEATS, dtype=object)}
    np.savez_compressed(CACHE, **data)
    return data


def load(rebuild=False):
    if rebuild or not os.path.exists(CACHE):
        return build()
    z = np.load(CACHE, allow_pickle=True)
    if list(z["feats"]) != FEATS or "FN" not in z.files:
        return build()
    return {k: z[k] for k in z.files}


def thresholds(data, cut):
    """Per-feature HIGH line for a cut. -> (thr array, strict bool)"""
    kind, arg = cut.split(":")
    if kind == "fixed":
        c, w = (float(x) for x in arg.split("/"))
        return np.where(IS_W, w, c).astype(np.float32), False
    q = float(arg)
    X, wt = data["X"], np.abs(data["D"])
    thr = np.empty(NF, np.float32)
    for i in range(NF):
        m = ~np.isnan(X[:, i])
        x, ww = X[m, i], wt[m]
        o = np.argsort(x)
        cw = np.cumsum(ww[o]) / ww.sum()
        thr[i] = x[o][np.searchsorted(cw, q)]
    return thr, True


def sign_p(k, n):
    from scipy.stats import binomtest
    return float(binomtest(k, n).pvalue) if n else 1.0


def run_cut(data, cut):
    L, D, X = data["L"], data["D"], data["X"]
    NL = int(L.max()) + 1
    LF = data["LF"]
    ok = ~np.isnan(LF)
    lo, hi = np.quantile(LF[ok], [1 / 3, 2 / 3])
    band = np.where(~ok, -1, np.where(LF <= lo, 0, np.where(LF <= hi, 1, 2)))
    thr, strict = thresholds(data, cut)
    rated = ~np.isnan(X)
    with np.errstate(invalid="ignore"):
        H = np.where(rated, (X > thr) if strict else (X >= thr), False)
    pos = np.where(D > 0, D, 0.0)
    neg = np.where(D < 0, -D, 0.0)

    def flows(mask, cell, ncell):
        l, c = L[mask], cell[mask]
        key = l.astype(np.int64) * ncell + c
        ap = np.bincount(key, weights=pos[mask], minlength=NL * ncell).reshape(NL, ncell)
        an = np.bincount(key, weights=neg[mask], minlength=NL * ncell).reshape(NL, ncell)
        tp, tn = ap.sum(1, keepdims=True), an.sum(1, keepdims=True)
        with np.errstate(invalid="ignore", divide="ignore"):
            out = ap / tp - an / tn
        out[(tp[:, 0] == 0) | (tn[:, 0] == 0)] = np.nan
        return out.T

    def summ(v):
        v = v[~np.isnan(v)]
        if len(v) < MIN_LIN:
            return None
        u, dn = int((v > 0).sum()), int((v < 0).sum())
        return {"median": float(np.median(v)), "up": u, "down": dn,
                "n": int(len(v)), "p": sign_p(min(u, dn), u + dn)}

    single, cells, masks = {}, {}, {}
    for i, f in enumerate(FEATS):
        for bn, b in BANDS.items():
            m = rated[:, i] if b is None else rated[:, i] & (band == b)
            single.setdefault(f, {})[bn] = summ(flows(m, H[:, i].astype(np.int64), 2)[1])
    for i, j in itertools.combinations(range(NF), 2):
        both = rated[:, i] & rated[:, j]
        if both.sum() < MIN_ROWS:
            continue
        cell = H[:, i].astype(np.int64) * 2 + H[:, j].astype(np.int64)
        for bn, b in BANDS.items():
            m = both if b is None else both & (band == b)
            fl = flows(m, cell, 4)
            for qd in range(4):
                lab = "%s=%s & %s=%s" % (FEATS[i], "hi" if qd >= 2 else "lo",
                                        FEATS[j], "hi" if qd % 2 else "lo")
                cells.setdefault(lab, {})[bn] = summ(fl[qd])
                masks[lab] = (i, j, qd)
    tests = [(lab, bn) for lab, d in cells.items() for bn, v in d.items() if v]
    ps = np.array([cells[l][b]["p"] for l, b in tests])
    o = np.argsort(ps)
    qv = np.empty(len(ps))
    qv[o] = np.minimum.accumulate((ps[o] * len(ps) / np.arange(1, len(ps) + 1))[::-1])[::-1]
    for (l, b), qq in zip(tests, np.minimum(qv, 1.0)):
        cells[l][b]["q"] = float(qq)

    reversals = []
    for lab, d in cells.items():
        a, z = d.get("low"), d.get("high")
        if (a and z and a["q"] < Q and z["q"] < Q
                and np.sign(a["median"]) != np.sign(z["median"])
                and min(abs(a["median"]), abs(z["median"])) >= MIN_EFFECT):
            i, j, qd = masks[lab]
            ex = {}
            for bn, b in (("low", 0), ("high", 2)):
                m = rated[:, i] & rated[:, j] & (band == b)
                m &= (H[:, i] == (qd >= 2)) & (H[:, j] == bool(qd % 2))
                ex[bn] = top_words(data, m)
            reversals.append({"cell": lab, "low": a, "high": z, "words": ex})
    reversals.sort(key=lambda r: max(r["low"]["q"], r["high"]["q"]))
    return {"cut": cut, "thresholds": dict(zip(FEATS, map(float, thr))),
            "strict": strict, "lift_cuts": [float(lo), float(hi)],
            "n_tests": len(tests), "n_q05": int((qv < Q).sum()),
            "single": single, "cells": cells, "reversals": reversals}


def top_words(data, mask):
    """The words that carry a cell's movement. -> {"gains": [...], "losses": [...]}

    **NET, NOT GROSS, AND NO FUNCTION WORDS.** Ranked by gross moved mass the
    first sweep put "have", "then", "found" and "said" at the head of every
    cell: frequent words that gain in some lineages and lose in others, whose
    churn is large and whose direction is nothing. Each word is ranked by its
    NET change summed over lineages and prompts in the cell, gainers and losers
    separately, and `is_function` words are left out of the examples (not out
    of the statistic).
    """
    m = mask & ~data["FN"]
    net = np.bincount(data["WID"][m], weights=data["D"][m], minlength=len(data["words"]))
    up = np.argsort(net)[::-1][:N_WORDS]
    dn = np.argsort(net)[:N_WORDS]
    return {"gains": [[str(data["words"][k]), round(float(net[k]), 2)] for k in up if net[k] > 0],
            "losses": [[str(data["words"][k]), round(float(net[k]), 2)] for k in dn if net[k] < 0]}


def fmt(x):
    return "%+.3f (%d/%d, q=%.0e)" % (x["median"], x["up"], x["down"], x["q"])


def write(res):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT_DATA, exist_ok=True)
    tag = res["cut"].replace(":", "_").replace("/", "-")
    json.dump(res, open(os.path.join(OUT_DATA, tag + ".json"), "w"), indent=1)
    lines = ["# feature_pairs, cut `%s`" % res["cut"], "",
             "EXPLORATORY; see the producer's docstring. %d tests, %d at q < %.2f. "
             "Lift thirds cut at %+.3f and %+.3f." % (res["n_tests"], res["n_q05"], Q,
                                                     *res["lift_cuts"]), "",
             "## Reversals (low third against high third, |median| >= %.3f)" % MIN_EFFECT, ""]
    for r in res["reversals"]:
        lines += ["### %s" % r["cell"], "",
                  "low %s | high %s" % (fmt(r["low"]), fmt(r["high"])), ""]
        for bn in ("low", "high"):
            for side in ("gains", "losses"):
                lines.append("- %s, %s: %s" % (bn, side, ", ".join(
                    "%s %.1f" % (w, v) for w, v in r["words"][bn][side])))
        lines.append("")
    open(os.path.join(OUT, tag + ".md"), "w").write("\n".join(lines))


def sweep_report(results):
    count = collections.defaultdict(list)
    for res in results:
        for r in res["reversals"]:
            count[r["cell"]].append((res["cut"], r))
    lines = ["# feature_pairs sweep", "",
             "EXPLORATORY. For each reversal, the cuts that find it, and the words "
             "under the cut where it is strongest. Cuts: %s." % ", ".join(r["cut"] for r in results),
             ""]
    for cell, hits in sorted(count.items(), key=lambda kv: -len(kv[1])):
        best = min(hits, key=lambda h: max(h[1]["low"]["q"], h[1]["high"]["q"]))
        cut, r = best
        lines += ["## %s: %d of %d cuts" % (cell, len(hits), len(results)), "",
                  "cuts: %s" % ", ".join(h[0] for h in hits), "",
                  "at `%s`: low %s | high %s" % (cut, fmt(r["low"]), fmt(r["high"])), ""]
        for bn in ("low", "high"):
            for side in ("gains", "losses"):
                lines.append("- %s, %s: %s" % (bn, side, ", ".join(
                    "%s %.1f" % (w, v) for w, v in r["words"][bn][side][:8])))
        lines.append("")
    open(os.path.join(OUT, "SWEEP.md"), "w").write("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cut", action="append", help="one or more cuts; default: all of CUTS")
    ap.add_argument("--rebuild", action="store_true", help="re-read the movement table")
    a = ap.parse_args(argv)
    data = load(a.rebuild)
    print("%d movement rows, %d lineages" % (len(data["D"]), len(data["lineages"])),
          file=sys.stderr)
    results = []
    for cut in a.cut or CUTS:
        res = run_cut(data, cut)
        write(res)
        results.append(res)
        print("%-12s tests %d, q<%.2f %d, reversals %d"
              % (cut, res["n_tests"], Q, res["n_q05"], len(res["reversals"])), file=sys.stderr)
    if len(results) > 1:
        sweep_report(results)


if __name__ == "__main__":
    main()
