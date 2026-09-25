"""Does Figure 5's placement depend on the passage-length rule? -> results/length_rule_test.md

    python -u length_rule_test.py

The paper seat's objection (2026-09-25), before the rule for the template arm is fixed:
the human reference passages are 200 words, and the current model arms carry quadrants.csv's
200-token cut (~150-190 words); the Scorer's own minimum is 40 words. A per-passage median
of a share can move with length. Tested here on the EXISTING f11_l2 narrative passages
(passC's `narrative` = true, joined to f11_l2_full), both arms, the paper seat's 25-pair
pairing (/tmp/placement_floor.py: literary_history's load/decades/smooth/crossings,
roster.lineages/endpoints):

    (a) 200-token rule  the passages quadrants.csv holds today (membership by (model, text))
    (b) 40-word rule    every narrative passage with >= 40 words, scored by the same Scorer

For each rule: per-model medians of concreteness (rh_absconc_median) and inner life (usas_x);
arm = median of per-model medians over the 25 pairs and over the pairs with >= 10 passages in
both arms; where each arm's line crosses the smoothed history (concreteness) or sits against
the historical maximum (inner life); aligned-above-base counts. Plus the within-narrative
slope of each measure on log word count (pooled, and the median of per-model slopes).
Read-only; the extra passages are scored locally, $0.
"""
import ast, glob, json, math, os, statistics as st, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import literary_history as LH  # noqa: E402

PASSC = os.path.join(ROOT, "experiments", "passage_analysis", "interiority_in_passages", "results", "passC", "codings")
FULL = os.path.expanduser("~/malignment-data/f11_l2/f11_l2_full.parquet")
QUAD = os.path.join(ROOT, "experiments", "passage_analysis", "jakobson_space", "results", "quadrants.csv")
CACHE = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc", "length_rule_scored.parquet")
COLS = (("rh_absconc_median", "concreteness", 1), ("usas_x", "inner life", 100))


def codings():
    """pid -> CODER A's fields. A codes all 13,565 passages and is the population
    Figure 5 used (drift_geometry/embed_passages.py: "Coder A is the population; B is
    the overlap"). An earlier version walked the whole file and let coder B's 3,610
    overlap codings overwrite A's, which put 61 A=True/B=False passages outside the
    narrative set and produced the "56 non-narrative passages in quadrants.csv"
    that were never there (corrected 2026-09-25)."""
    C = {}
    for f in glob.glob(os.path.join(PASSC, "*.json")):
        d = json.load(open(f))
        for pid, v in (d.get("A") or {}).items():
            if isinstance(v, dict) and "narrative" in v:
                C[pid] = v
    return C


def pairs_from(mod):
    """The paper seat's pairing, verbatim from /tmp/placement_floor.py."""
    from malignment import roster
    lin_of = {m: b for b, ms in roster.lineages().items() for m in ms}
    eps = roster.endpoints()[0]
    B, A = mod[mod.category == "base"], mod[mod.category == "aligned"]
    out = {}
    for b in sorted(set(B.model)):
        lb = lin_of.get(b)
        if lb is None or lb != b:
            continue
        al = sorted({m for m in A.model if lin_of.get(m) == lb})
        if not al:
            continue
        out[lb] = (b, eps.get(lb) if eps.get(lb) in al else max(al, key=lambda m: (A.model == m).sum()))
    return out


def scored_narrative(models):
    C = codings()
    #: passC keyed most shards by f11_l2_full ids and three models (Yi-1.5-9B, SmolLM2-360M,
    #: neo_7b pairs) by sample.parquet ids -- read BOTH, or those three pairs vanish silently.
    SAMPLE = os.path.join(os.path.dirname(PASSC), "sample.parquet")
    full = pd.concat([pd.read_parquet(FULL, columns=["id", "model", "arm", "text"]),
                      pd.read_parquet(SAMPLE, columns=["id", "model", "arm", "text"])]).drop_duplicates("id")
    full = full[full.id.isin(C) & full.model.isin(models)]
    done = pd.read_parquet(CACHE) if os.path.exists(CACHE) else None
    if done is not None:
        full = full[~full.id.isin(set(done.id))]
        if not len(full):
            return done
    full = full[full.id.map(lambda i: bool(C[i]["narrative"]) and str(C[i]["narrative"]).upper() not in ("FALSE", "NO", "0"))]
    from measure_lltk import Scorer
    S = Scorer()
    rows = []
    for r in full.itertuples():
        nw = len((r.text or "").split())
        if nw < 40:
            continue
        v = S.score(r.text)
        if not v:
            continue
        v.update(id=r.id, model=r.model, arm=("base" if r.arm == "base" else "aligned"), n_words=nw, text_key=r.text)
        rows.append(v)
        if len(rows) % 1000 == 0:
            print("  scored %d" % len(rows), flush=True)
    df = pd.DataFrame(rows)
    if done is not None:
        df = pd.concat([done, df], ignore_index=True)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    df.to_parquet(CACHE)
    return df


def main():
    chad, chi, mod = LH.load()
    P = pairs_from(mod)
    models = {m for p in P.values() for m in p}
    df = scored_narrative(models)
    quad = pd.read_csv(QUAD, usecols=["model", "text"])
    inq = set(zip(quad.model, quad.text))
    df["rule_a"] = [(m, t) in inq for m, t in zip(df.model, df.text_key)]
    L = ["# Figure 5: does placement depend on the length rule?", "",
         "Producer `length_rule_test.py` (read-only; paper seat's objection, 2026-09-25). %d narrative passages of "
         "the 25 pairs' models scored; rule (a) = the %d that quadrants.csv holds (200-token cut), rule (b) = all with "
         ">= 40 words. Median words: (a) %d, (b) %d."
         % (len(df), int(df.rule_a.sum()), df[df.rule_a].n_words.median(), df.n_words.median()), ""]
    for col, lab, scale in COLS:
        hist = LH.decades(chad, chi, col)
        curve = LH.smooth(hist)
        hmax = hist.value.max()
        L += ["## %s (`%s`)" % (lab, col), "", "| rule | pairs | base arm | aligned arm | base placement | aligned placement | aligned > base |", "|---|---|---|---|---|---|---|"]
        for rule, sub in (("(a) 200-token", df[df.rule_a]), ("(b) 40-word", df)):
            pm = sub.groupby(["arm", "model"])[col].median()
            n = sub.groupby(["arm", "model"]).size()
            for floor in (0, 10):
                ps = [(b, a) for b, a in P.values()
                      if ("base", b) in n and ("aligned", a) in n and n[("base", b)] >= floor and n[("aligned", a)] >= floor]
                vb = st.median(pm[("base", b)] for b, _ in ps)
                va = st.median(pm[("aligned", a)] for _, a in ps)
                up = sum(pm[("aligned", a)] > pm[("base", b)] for b, a in ps)
                def place(v):
                    if col == "usas_x":
                        return "%.2f vs max %.2f" % (v * scale, hmax * scale)
                    return "crosses %s" % [round(x) for x in LH.crossings(curve, v)]
                L.append("| %s, floor %d | %d | %.4f | %.4f | %s | %s | %d/%d |" % (rule, floor, len(ps), vb * scale, va * scale,
                                                                                place(vb), place(va), up, len(ps)))
        x = np.log(df.n_words.values.astype(float))
        y = df[col].values.astype(float) * scale
        ok = np.isfinite(y)
        pooled = np.polyfit(x[ok], y[ok], 1)[0]
        per = []
        for m, g in df.groupby("model"):
            gx, gy = np.log(g.n_words.values.astype(float)), g[col].values.astype(float) * scale
            k = np.isfinite(gy)
            if k.sum() >= 20 and np.ptp(gx[k]) > 0:
                per.append(np.polyfit(gx[k], gy[k], 1)[0])
        L += ["", "Slope on log(words), within narrative passages: pooled %+.4f; median of %d per-model slopes %+.4f "
              "(per doubling of length: %+.4f)." % (pooled, len(per), st.median(per), st.median(per) * math.log(2)), ""]
    out = os.path.join(HERE, "results", "length_rule_test.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
