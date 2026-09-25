"""Does Figure 5's interiority measure (USAS X share) predict the blind LLM interiority coder? (2026-09-25)

    ~/github/lltk/.venv/bin/python -u usas_x_coder_benchmark.py
        -> $MALIGNMENT_DATA/interiority_norms/usas_x_passages_dario.parquet   (per passage)
        -> USAS_X_CODER_BENCHMARK.md                                          (this folder)

The abstraction seat built seeded interiority norms (interiority_norms.parquet) and tested them against
the interiority_in_passages coder at passage level: emotion (B) and cognition+emotion (C) axes reach a
Spearman partial of about +0.2 to +0.35 on coder degree controlling for concreteness; cognition (A)
does not. The benchmark any replacement has to beat is the CURRENT panel measure, `usas_x`, on the
same passages. This computes it.

PASSAGES exactly as the seat's interiority_norms_eval.py builds them: coder degree = mean over coders A
and B (and re-codings) in interiority_in_passages/results/passC/codings/*.json; narrative = majority of
the coders' flags; text and prompt from passC/sample.parquet plus f11_l2_full.parquet; English only.

INSTRUMENT: measure_lltk.Scorer, the machinery Figure 5 uses, so `usas_x` and the concreteness control
(`rh_absconc_median`, a passage's mean over its words of Abs-Conc.Median) are the plate's own. A passage
enters the statistics with >= 20 content words (the seat's floor is 20 scored tokens on its own
tokenizer, so the populations are close, not identical; the per-passage file lets the seat rerun its
exact controls).

STATISTICS as the seat's `partial`: Spearman partial by rank residualisation (ranks of x and y regressed
on ranks of the control); within-prompt = ranks demeaned by prompt first; narrative = coder-flagged
narrative passages only. EXPLORATORY.
"""
import collections, glob, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
PASSC = os.path.join(REPO, "experiments", "passage_analysis", "interiority_in_passages", "results", "passC")
F11 = os.path.expanduser("~/malignment-data/f11_l2/f11_l2_full.parquet")
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(SHARED, "usas_x_passages_dario.parquet")
MIN_CONTENT = 20


def passages():
    import pandas as pd
    deg, narr = collections.defaultdict(list), collections.defaultdict(list)
    for f in glob.glob(os.path.join(PASSC, "codings", "*.json")):
        d = json.load(open(f))
        for coder in ("A", "B"):
            for pid, c in d.get(coder, {}).items():
                if isinstance(c, dict) and "degree" in c:
                    deg[pid].append(c["degree"]); narr[pid].append(bool(c.get("narrative")))
    coded = pd.DataFrame({"degree": {k: np.mean(v) for k, v in deg.items()},
                          "narrative": {k: np.mean(v) >= 0.5 for k, v in narr.items()}})
    cols = ["id", "prompt", "language", "text"]
    sample = pd.concat([pd.read_parquet(os.path.join(PASSC, "sample.parquet"), columns=cols),
                        pd.read_parquet(F11, columns=cols)]).drop_duplicates("id").set_index("id")
    P = sample.join(coded, how="inner")
    return P[P.language == "en"]


def partial(x, y, z, groups=None):
    """Spearman partial of x, y given z, by rank residualisation (as the seat's eval)."""
    import pandas as pd
    df = pd.concat([x.rename("x"), y.rename("y"), z.rename("z")], axis=1).dropna()
    r = df.rank()
    if groups is not None:
        r = r - r.groupby(groups.reindex(r.index)).transform("mean")
    Z = np.column_stack([np.ones(len(r)), r["z"]])
    res = lambda v: v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    a, b = res(r["x"].values), res(r["y"].values)
    return float(np.corrcoef(a, b)[0, 1]), len(df)


def within(x, y, groups):
    import pandas as pd
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    r = df.rank()
    r = r - r.groupby(groups.reindex(r.index)).transform("mean")
    return float(np.corrcoef(r["x"], r["y"])[0, 1])


def main():
    import pandas as pd
    from scipy.stats import spearmanr
    from measure_lltk import Scorer
    P = passages()
    print("coded English passages: %d (%d narrative)" % (len(P), int(P.narrative.sum())), flush=True)
    assert len(P) == 13564, len(P)                     # the seat's count
    S = Scorer()
    rows = []
    for i, (pid, r) in enumerate(P.iterrows()):
        v = S.score(r.text or "") or {}
        rows.append(dict(id=pid, usas_x=v.get("usas_x"), rh_absconc_median=v.get("rh_absconc_median"),
                         n_content=v.get("n_content", 0)))
        if (i + 1) % 2000 == 0:
            print("  %d scored" % (i + 1), flush=True)
    D = pd.DataFrame(rows).set_index("id").join(P[["degree", "narrative", "prompt"]])
    os.makedirs(SHARED, exist_ok=True)
    D.reset_index().to_parquet(OUT, index=False)
    ok = D[(D.n_content >= MIN_CONTENT) & D.usas_x.notna() & D.rh_absconc_median.notna()]
    x, y, c = ok.usas_x, ok.degree, ok.rh_absconc_median
    nar = ok.narrative.astype(bool)
    res = dict(
        n=len(ok), n_narrative=int(nar.sum()),
        rho_degree_concreteness=float(spearmanr(y, c)[0]),
        rho_x_concreteness=float(spearmanr(x, c)[0]),
        raw=float(spearmanr(x, y)[0]),
        partial=partial(x, y, c)[0],
        partial_within_prompt=partial(x, y, c, groups=ok.prompt)[0],
        partial_narrative=partial(x[nar], y[nar], c[nar])[0],
        raw_within_prompt=within(x, y, ok.prompt))
    L = ["# USAS X against the blind interiority coder (EXPLORATORY)", "",
         "Producer `usas_x_coder_benchmark.py`. The %d English passages the abstraction seat evaluated its "
         "seeded interiority norms on, scored with `measure_lltk.Scorer` (Figure 5's instrument). %d have at "
         "least %d content words and enter (%d narrative). Coder degree 0-3, mean over coders A and B. Control: "
         "`rh_absconc_median`, the plate's concreteness. Per-passage scores: %s." % (
             len(P), res["n"], MIN_CONTENT, res["n_narrative"], OUT), "",
         "| statistic | value |", "|---|---|",
         "| rho(coder degree, concreteness) | %+.3f |" % res["rho_degree_concreteness"],
         "| rho(usas_x, concreteness) | %+.3f |" % res["rho_x_concreteness"],
         "| rho(usas_x, coder degree), raw | %+.3f |" % res["raw"],
         "| raw, within prompt | %+.3f |" % res["raw_within_prompt"],
         "| partial, controlling concreteness | %+.3f |" % res["partial"],
         "| partial, within prompt | %+.3f |" % res["partial_within_prompt"],
         "| partial, narrative passages only | %+.3f |" % res["partial_narrative"], "",
         "For comparison, the seat's seeded norms on its own tokenisation and concreteness control "
         "(eval_passage_coder.csv): raw / partial / within prompt / narrative -- A_ALL +0.04 / +0.06 / +0.08 / "
         "+0.13; B_ALL +0.18 / +0.31 / +0.24 / +0.17; B_NOUN +0.22 / +0.35 / +0.29 / +0.23; C_ALL +0.09 / +0.20 "
         "/ +0.17 / +0.17; C_NOUN +0.13 / +0.30 / +0.26 / +0.28. Populations and controls are close, not "
         "identical (see the docstring); the seat can rerun its exact controls on the per-passage file."]
    open(os.path.join(HERE, "USAS_X_CODER_BENCHMARK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
