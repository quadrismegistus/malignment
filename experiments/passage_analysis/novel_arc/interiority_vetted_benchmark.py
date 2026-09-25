"""The precision and vetted interiority lists against the blind coder, beside the lists they replace. (RH, 2026-09-25)

    ~/github/lltk/.venv/bin/python -u interiority_vetted_benchmark.py   -> INTERIORITY_VETTED_BENCHMARK.md
    ~/github/lltk/.venv/bin/python -u interiority_vetted_benchmark.py --categories
        -> INTERIORITY_VETTING_CATEGORIES.md: the vetted clean X list with each removal category added back

Same passages, counting rule, control and statistics as `interiority_xe.py --lists` (imported, not
reimplemented): share of content words whose modernised surface form or lemma is on a list, each word
counted once, Spearman partial on coder degree controlling the plate's concreteness. Lists are BASE WORDS
only: the passages are modern model prose, modernised before lookup, so spelling variants cannot match.

  precision  = interiority_precision.py consensus keep (precision_keep_v2.csv)
  vetted     = interiority_vetting.py keep_vetted (precision_keep_v2_vetted.csv)

GAPS. A paired bootstrap over passages (resampling passages, recomputing both partials on each draw)
gives a 95% interval for the DIFFERENCE between two measures on the same passages, which the earlier
readout said a gap under ~0.03 needed. EXPLORATORY; the coder and the raters are both LLMs.
"""
import os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
N_BOOT, SEED = 1000, 20260925


def lists():
    import pandas as pd
    import interiority_xe as IX
    L = IX.word_lists()
    K = pd.read_csv(os.path.join(SHARED, "precision_keep_v2_vetted.csv"))
    assert len(K) == 15099, len(K)
    b = K[K.spelling_of.isna()]
    out = {"usas_x (panel now)": None, "clean X (1,526)": L["clean X (1,526)"],
           "clean X + candidates (3,687)": L["clean X + candidates (3,687)"]}
    for col, lab in (("keep", "precision"), ("keep_vetted", "vetted")):
        cx, ca = set(b.form[(b.source == "cleanx") & b[col]]), set(b.form[(b.source == "cand") & b[col]])
        out["clean X, %s (%s)" % (lab, format(len(cx), ","))] = cx
        out["candidates, %s (%s)" % (lab, format(len(ca), ","))] = ca
        out["clean X + candidates, %s (%s)" % (lab, format(len(cx | ca), ","))] = cx | ca
    #: booked sizes (INTERIORITY_PRECISION.md, INTERIORITY_VETTING.md)
    assert "clean X, precision (1,054)" in out and "clean X, vetted (872)" in out and "candidates, vetted (1,077)" in out, list(out)
    return out


def boot_diff(ok, a, b, B):
    """95% paired-bootstrap interval for partial(a) - partial(b) on the same passages."""
    rng = np.random.default_rng(SEED)
    idx = np.arange(len(ok))
    d = []
    for _ in range(N_BOOT):
        s = ok.iloc[rng.choice(idx, len(idx))].reset_index(drop=True)
        d.append(B.partial(s[a], s.degree, s.rh_absconc_median)[0] - B.partial(s[b], s.degree, s.rh_absconc_median)[0])
    return np.percentile(d, [2.5, 97.5])


def main():
    import pandas as pd
    from scipy.stats import spearmanr
    import interiority_xe as IX
    import usas_x_coder_benchmark as B
    P = B.passages()
    assert len(P) == 13564, len(P)
    Ls = lists()
    scored = {k: v for k, v in Ls.items() if v is not None}
    X = IX.XE()
    rows = []
    for i, (pid, r) in enumerate(P.iterrows()):
        rows.append(dict(id=pid, **(IX.list_shares(X, r.text or "", scored) or {})))
        if (i + 1) % 3000 == 0:
            print("  %d scored" % (i + 1), flush=True)
    D = pd.DataFrame(rows).set_index("id").join(P[["degree", "narrative", "prompt"]])
    D = D.rename(columns={"usas_x_old": "usas_x (panel now)"})
    ok = D[(D.n_content >= B.MIN_CONTENT) & D.rh_absconc_median.notna()].copy()
    c, y, nar = ok.rh_absconc_median, ok.degree, ok.narrative.astype(bool)
    #: the earlier readout's numbers, unchanged (INTERIORITY_LISTS_BENCHMARK.md)
    assert abs(B.partial(ok["usas_x (panel now)"], y, c)[0] - 0.370) < 0.0005
    assert abs(B.partial(ok["clean X (1,526)"], y, c)[0] - 0.388) < 0.0005
    L = ["# Precision and vetted interiority lists against the blind coder (EXPLORATORY)", "",
         "Producer `interiority_vetted_benchmark.py`. Same %d coded English passages as INTERIORITY_LISTS_BENCHMARK.md, "
         "%d with at least %d content words (%d narrative); coder degree 0-3; control the plate's concreteness; counting "
         "rule `interiority_xe.list_shares`. Base words only (modern prose, modernised before lookup). The first three "
         "rows reproduce the earlier readout." % (len(P), len(ok), B.MIN_CONTENT, int(nar.sum())), "",
         "| measure | raw | partial (concreteness) | partial within prompt | partial narrative | rho with concreteness | median share |",
         "|---|---|---|---|---|---|---|"]
    for col in Ls:
        x = ok[col]
        L.append("| %s | %+.3f | %+.3f | %+.3f | %+.3f | %+.3f | %.3f |" % (
            col, spearmanr(x, y)[0], B.partial(x, y, c)[0], B.partial(x, y, c, groups=ok.prompt)[0],
            B.partial(x[nar], y[nar], c[nar])[0], spearmanr(x, c)[0], float(x.median())))
    vx = [k for k in Ls if k.startswith("clean X, vetted")][0]
    px = [k for k in Ls if k.startswith("clean X, precision")][0]
    vc = [k for k in Ls if k.startswith("clean X + candidates, vetted")][0]
    L += ["", "## Paired differences in the partial (95%% paired bootstrap over passages, %d draws)" % N_BOOT, "",
          "| comparison | difference | 95% interval |", "|---|---|---|"]
    for a, b_ in ((vx, "clean X (1,526)"), (vx, "usas_x (panel now)"), (px, "clean X (1,526)"), (vx, px), (vc, vx)):
        diff = B.partial(ok[a], y, c)[0] - B.partial(ok[b_], y, c)[0]
        lo, hi = boot_diff(ok, a, b_, B)
        L.append("| %s minus %s | %+.3f | %+.3f to %+.3f |" % (a, b_, diff, lo, hi))
    open(os.path.join(HERE, "INTERIORITY_VETTED_BENCHMARK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def categories():
    """Which vetting removals cost agreement with the coder: vetted clean X plus one category back at a time."""
    import pandas as pd
    import interiority_xe as IX
    import interiority_vetting as V
    import usas_x_coder_benchmark as B
    P = B.passages()
    assert len(P) == 13564, len(P)
    K = pd.read_csv(os.path.join(SHARED, "precision_keep_v2_vetted.csv"))
    b = K[K.spelling_of.isna() & (K.source == "cleanx")]
    vetted, prec = set(b.form[b.keep_vetted]), set(b.form[b.keep])
    assert (len(vetted), len(prec)) == (872, 1054)
    short = {r: "%d. %s" % (i + 1, r.split(" (")[0]) for i, r in enumerate(V.REMOVE)}
    lists = {"vetted": vetted, "precision": prec}
    for r, ws in V.REMOVE.items():
        back = set(ws.split()) & prec                    # the category's clean X members
        lists["+" + short[r]] = vetted | back
    for w in ("see", "feel", "felt", "want", "wanted"):   # the three biggest by token mass, singly
        lists["+ " + w] = vetted | {w}
    X = IX.XE()
    rows = [dict(id=pid, **(IX.list_shares(X, r.text or "", lists) or {})) for pid, r in P.iterrows()]
    D = pd.DataFrame(rows).set_index("id").join(P[["degree", "narrative", "prompt"]])
    ok = D[(D.n_content >= B.MIN_CONTENT) & D.rh_absconc_median.notna()]
    y, c, nar = ok.degree, ok.rh_absconc_median, ok.narrative.astype(bool)
    base = B.partial(ok.vetted, y, c)[0]
    assert abs(base - 0.307) < 0.0005, base              # INTERIORITY_VETTED_BENCHMARK.md
    L = ["# Which vetting removals cost agreement with the coder? (EXPLORATORY)", "",
         "Producer `interiority_vetted_benchmark.py --categories`. Vetted clean X (872) with the clean X members of "
         "one removal category added back (categories as in interiority_vetting.py), and five single words. Same "
         "passages, rule and control as INTERIORITY_VETTED_BENCHMARK.md; the partial of the full precision list "
         "(1,054) is the ceiling the vetting fell from.", "",
         "| list | words back | partial (concreteness) | gain over vetted | partial narrative |", "|---|---|---|---|---|"]
    for k, ws in lists.items():
        pk = B.partial(ok[k], y, c)[0]
        L.append("| %s | %d | %+.3f | %+.3f | %+.3f |" % (k, len(ws - vetted), pk, pk - base, B.partial(ok[k][nar], y[nar], c[nar])[0]))
    open(os.path.join(HERE, "INTERIORITY_VETTING_CATEGORIES.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    categories() if "--categories" in sys.argv else main()
