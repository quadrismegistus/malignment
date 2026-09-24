"""The registered tests (registration.md: H1, H2, H3) and declared secondaries.

    python analyse.py                  primary filter: judge story AND pure_story
    python analyse.py --sensitivity a  no-demonym control only
    python analyse.py --sensitivity c  lineages with >= 10 filtered passages per arm
    python analyse.py --write          also write results/tests.csv, results/by_lineage.csv

Unit = the lineage. Per lineage the statistic is aligned minus base; tested by
exact sign test and Wilcoxon signed-rank, two-sided; Holm within each family
({H1a, H1b, H2a, H2b} and H3). H1 is directly standardised over sentence-length
bins, H2 over monosyllable-count bins, as registered. Sensitivity (b), no judge
filter, needs `parse_passages_prosodic.py --subset all` first.

Each text is counted once: national_story's load_raw deduplicates within a
(lineage, arm, demonym) cell only, and 60 texts recur under two demonyms.
Windows the pooling guard skipped (`skipped` set) carry no parse and drop out.
"""
import argparse
import os
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest, wilcoxon

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "syntax_and_rhythm")
LEN_BINS = ([1, 7, 12, 19, 29, 10**6], ["2-7", "8-12", "13-19", "20-29", "30+"])
MONO_BINS = ([-1, 3, 5, 7, 10], ["0-3", "4-5", "6-7", "8-10"])


def load(sensitivity=None):
    P = pd.read_csv(os.path.join(HERE, "results", "by_passage.csv"), low_memory=False).drop_duplicates(["id", "version"])
    keep = P[(P.version == "orig") & (P.overall == "story") & (P.pure_story == True) & (P.error.fillna("") == "")]
    if sensitivity == "a":
        keep = keep[keep.demonym.fillna("") == ""]
    if sensitivity == "c":
        n = keep.groupby(["lineage", "arm"]).size().unstack(fill_value=0)
        keep = keep[keep.lineage.isin(n[n.min(axis=1) >= 10].index)]
    ids = set(keep.id)
    S = pd.read_csv(os.path.join(DATA, "by_sentence.csv"), low_memory=False)
    W = pd.read_csv(os.path.join(DATA, "by_window.csv"), low_memory=False)
    S = S[S.id.isin(ids)].drop_duplicates(["id", "version", "sent_idx"])
    W = W[W.id.isin(ids) & W.num_parses.notna()].drop_duplicates(["id", "version", "win_idx"])
    S["len_bin"] = pd.cut(S.n_words, LEN_BINS[0], labels=LEN_BINS[1])
    W["mono_bin"] = pd.cut(W.num_monosylls, MONO_BINS[0], labels=MONO_BINS[1])
    W["imperfect_s_unstress"] = (W.mviol_s_unstress_allparse_sum > 0).astype(float)
    return P[P.id.isin(ids)], keep, S, W


def paired(stat, test, family, direction):
    """stat: aligned - base per lineage. direction -1 = predicted lower, +1 higher, 0 = undirected."""
    stat = stat.dropna()
    up, dn = int((stat > 0).sum()), int((stat < 0).sum())
    return dict(test=test, family=family, predicted={1: "higher", -1: "lower", 0: "none"}[direction],
                lineages=len(stat), aligned_higher=up, aligned_lower=dn,
                in_predicted_direction=(up if direction > 0 else dn) if direction else np.nan,
                median_diff=stat.median(), p_sign=binomtest(up, up + dn).pvalue if up + dn else np.nan,
                p_wilcoxon=wilcoxon(stat).pvalue if len(stat) >= 6 and (stat != 0).any() else np.nan)


def standardised(df, col, strata):
    """Per lineage: sum_b w_b (aligned_b - base_b), w_b the pooled share of stratum b;
    a stratum missing either arm in a lineage is dropped and that lineage's weights renormalised."""
    df = df.dropna(subset=[col])
    w = df[strata].value_counts(normalize=True)
    m = df.groupby(["lineage", "arm", strata], observed=True)[col].mean().unstack("arm").dropna(subset=["base", "aligned"])
    m["w"] = np.asarray(m.index.get_level_values(strata).map(w), dtype=float)
    return m.groupby("lineage").apply(lambda g: ((g.aligned - g.base) * g.w).sum() / g.w.sum())


def holm(ps):
    order, out, run = ps.sort_values().index, pd.Series(index=ps.index, dtype=float), 0
    for k, i in enumerate(order):
        run = max(run, min(1, ps[i] * (len(order) - k)))
        out[i] = run
    return out


def run(sensitivity=None):
    P, keep, S, W = load(sensitivity)
    So, Wo = S[S.version == "orig"], W[W.version == "orig"]
    lin = keep.groupby(["lineage", "arm"]).mean(numeric_only=True).unstack("arm")
    diff = lambda c: lin[c]["aligned"] - lin[c]["base"]
    rows = [
        paired(standardised(So, "clash_rate", "len_bin"), "H1a clash_rate", "primary", -1),
        paired(standardised(So, "ibi2_cv", "len_bin"), "H1b ibi2_cv", "primary", -1),
        paired(standardised(Wo, "num_parses", "mono_bin"), "H2a num_parses", "primary", -1),
        paired(standardised(Wo, "num_viols_allparse_sum", "mono_bin"), "H2b MTS", "primary", -1),
        paired(diff("dep_relcl"), "H3a dep_relcl", "H3", +1),
        paired(diff("left_head"), "H3b left_head", "H3", -1),
        paired(diff("dep_dist"), "H3c dep_dist", "H3", -1),
        paired(diff("dep_advmod"), "H3d dep_advmod", "H3", -1),
        paired(diff("phrase_cv"), "H3e phrase_cv", "H3", -1),
        paired(diff("sent_len_cv"), "H3f sent_len_cv", "H3", -1),
    ]
    for c, d in [("clash2", -1), ("clash3", -1), ("clash4", -1), ("clash5", -1), ("lapse2_rate", -1), ("alt2", +1)]:
        rows.append(paired(standardised(So, c, "len_bin"), c, "secondary", d))
    rows.append(paired(standardised(Wo, "imperfect_s_unstress", "mono_bin"), "imperfect_s_unstress", "secondary", -1))
    # arrangement: orig - shuffle_pos per passage, aligned vs base over lineages (declared, undirected)
    for c in ["clash_lex_rate", "lapse2_rate", "alt2", "ibi2_cv", "num_parses", "num_viols_allparse_sum"]:
        x = P.pivot_table(index=["id", "lineage", "arm"], columns="version", values=c).reset_index()
        x["eff"] = x["orig"] - x["shuffle_pos"]
        L = x.groupby(["lineage", "arm"]).eff.mean().unstack("arm")
        rows.append(paired(L.aligned - L.base, "arrangement " + c, "arrangement", 0))
    T = pd.DataFrame(rows)
    T["p_sign_holm"] = np.nan
    for fam in ("primary", "H3"):
        i = T.family == fam
        T.loc[i, "p_sign_holm"] = holm(T.loc[i, "p_sign"])
    T.insert(0, "population", {None: "primary", "a": "sensitivity a", "c": "sensitivity c"}[sensitivity])
    head = dict(passages=len(keep), base=int((keep.arm == "base").sum()), aligned=int((keep.arm == "aligned").sum()))
    return T, lin, head


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensitivity", choices=("a", "c"))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    T, lin, head = run(a.sensitivity)
    print("passages %(passages)d (base %(base)d, aligned %(aligned)d)" % head)
    pd.set_option("display.width", 220)
    print(T.drop(columns=["population"]).to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    if a.write:
        tests = os.path.join(HERE, "results", "tests.csv")
        old = pd.read_csv(tests) if os.path.exists(tests) else pd.DataFrame()
        if len(old):
            old = old[old.population != T.population.iloc[0]]
        pd.concat([old, T]).to_csv(tests, index=False)
        if a.sensitivity is None:
            lin.columns = ["%s_%s" % c for c in lin.columns]
            lin.to_csv(os.path.join(HERE, "results", "by_lineage.csv"))


if __name__ == "__main__":
    main()
