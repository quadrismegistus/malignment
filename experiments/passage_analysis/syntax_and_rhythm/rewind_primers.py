"""How far do models rewind literary history when they continue a dated poem? EXPLORATORY.

    python rewind_primers.py            -> results/rewind_lookup.csv, rewind_dating.csv, dating_validation.csv

Not registered: designed 2026-09-24 after the continuation and primer aggregates
had been seen. Every continued poem is dated (author_dob + 30, from the
Chadwyck-Healey metadata), so a model's continuation can be placed against the
history of the same corpus, poem by poem.

(1) LOOKUP. The human curve is the poets' own continuations, by 50-year period.
    Same poems, same protocol. For the poems of period P a model's continuation
    level is M(P). Its rewind is the distance from P back to the most recent period
    at or before P whose human level is at least as metrical (for uncertainty:
    H <= M; for uIP: H >= M), interpolated between bin midpoints. If no period
    back to 1600 is as metrical, the rewind is censored ("beyond 1600") and so
    reported. Transparent, but coarse, and bounded by a non-monotonic curve.

(2) METRICAL DATING. A gradient-boosted regression predicts year (author_dob + 30)
    from a text's metrical features: mean uncertainty, tension, uIP, puIP,
    per-constraint tension, the share of windows with a double weak (ternary) or
    double strong, strong-initial windows, and monosyllables per window. It is
    trained on human verse only (the poets' continuations and the 5-line primers),
    cross-fitted by poem: 5 folds grouped by poem, so no poem is dated by a model
    that saw it. Each continuation, human or model, gets a predicted date.
    Rewind per poem = predicted date of the poets' continuation - predicted date
    of the model's. The poets' own rewind is zero by construction; the check is how
    well meter dates human verse at all (R2, MAE). Predictions are compressed toward
    the mean where meter carries little date signal, so rewinds are reported raw
    ("metrical years") and after an isotonic calibration of predicted to true year,
    fitted on the human continuations.
"""
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "syntax_and_rhythm")
GENFORM = os.environ.get("GENFORM_REPO", os.path.expanduser("~/github/generative-formalism"))
LAST = 2000
MODELS = {  # model -> (label, tier, the group its poets' continuation rows are filed under)
    "ollama/llama3.1:8b-text-q4_K_M": ("Llama-3.1-8B base", "base", "ollama/llama3.1:8b-text-q4_K_M"),
    "ollama/mistral:text": ("Mistral-7B base", "base", "ollama/mistral:text"),
    "ollama/llama3.1:8b": ("Llama-3.1-8B aligned", "open aligned", "ollama/llama3.1:8b-text-q4_K_M"),
    "ollama/mistral": ("Mistral-7B aligned", "open aligned", "ollama/mistral:text"),
    "ollama/olmo2:latest": ("OLMo-2", "open aligned", "ollama/olmo2:latest"),
    "gpt-3.5-turbo": ("GPT-3.5", "API", "gpt-3.5-turbo"),
    "claude-3-sonnet-20240229": ("Claude-3-Sonnet", "API", "claude-3-sonnet-20240229"),
    "deepseek/deepseek-chat": ("DeepSeek-chat", "API", "deepseek/deepseek-chat"),
}
CONS = ["w_peak", "w_stress", "s_unstress", "unres_across", "unres_within"]


def load():
    V = pd.read_csv(os.path.join(DATA, "by_window_verse.csv"), low_memory=False)
    V = V[(V.win_idx >= 0) & V.num_parses.notna()].copy()
    V["version"] = V.version.fillna("orig")
    V = V[V.source.isin(["genai_completion", "genai_primer"])]
    m = V.meter.astype(str)
    V["uip"] = ((m == "wswswswsws") & (V.num_parses == 1)) * 100.0
    V["puip"] = (V.uip.astype(bool) & (V.num_viols_allparse_sum == 0)) * 100.0
    V["ww"] = m.str.contains("ww").astype(float)
    V["ss"] = m.str.contains("ss").astype(float)
    V["s_initial"] = m.str.startswith("s").astype(float)
    meta = pd.read_csv(os.path.join(GENFORM, "data/raw/corpus/chadwyck_corpus_metadata.csv.gz"),
                       usecols=["id", "author_dob"], low_memory=False)
    meta["year"] = pd.to_numeric(meta.author_dob, errors="coerce") + 30
    V = V.merge(meta.rename(columns={"id": "poem_id"})[["poem_id", "year"]], on="poem_id", how="left")
    V = V[V.year < LAST]
    V["period"] = (V.year // 50 * 50).astype(int)
    return V


FEATS = ["num_parses", "num_viols_allparse_sum", "uip", "puip", "ww", "ss", "s_initial", "num_monosylls"] + \
        ["mviol_%s_allparse_sum" % c for c in CONS]


#: O/R/S features: the same text scrambled within POS (R) and fully (S). Primers were not
#: scrambled, so a model using these trains on the poets' continuations only.
ORS_BASE = ["num_parses", "num_viols_allparse_sum", "uip"]
ORS_FEATS = ["%s_%s" % (k, v) for k in ORS_BASE for v in ("R", "S", "OminusR", "RminusS")]


def texts(V):
    """One row per text: (who, poem_id) with mean features of the original, O/R/S features where the
    text was scrambled, year, period, windows."""
    V = V.assign(who=np.where(V.source == "genai_primer", "primer",
                              np.where(V.arm == "human", "poets:" + V.group.astype(str), V.model.astype(str))))
    O = V[V.version == "orig"]
    g = O.groupby(["who", "poem_id"])
    T = g[FEATS].mean()
    T["windows"] = g.size()
    T["year"] = g.year.first()
    T["period"] = g.period.first()
    for v, lab in (("shuffle_pos", "R"), ("shuffle_all", "S")):
        s = V[V.version == v].groupby(["who", "poem_id"])[ORS_BASE].mean()
        T = T.join(s.rename(columns={k: "%s_%s" % (k, lab) for k in ORS_BASE}))
    for k in ORS_BASE:
        T[k + "_OminusR"] = T[k] - T[k + "_R"]
        T[k + "_RminusS"] = T[k + "_R"] - T[k + "_S"]
    return T.reset_index()


def lookup(T):
    """Method (1): rewind per (model, period) against the poets' continuation curve."""
    poets = T[T.who.str.startswith("poets:")].groupby("poem_id").agg(period=("period", "first"),
                                                                       num_parses=("num_parses", "mean"), uip=("uip", "mean"))
    H = poets.groupby("period")[["num_parses", "uip"]].mean()
    rows = []
    for m, (lab, tier, _) in MODELS.items():
        x = T[T.who == m]
        for per, g in x.groupby("period"):
            r = dict(model=lab, tier=tier, period=int(per), poems=len(g))
            for k, better in (("num_parses", "lower"), ("uip", "higher")):
                v = g[k].mean()
                r[k] = v
                r[k + "_poets_same_period"] = H.loc[per, k]
                ok = (lambda h: h <= v) if better == "lower" else (lambda h: h >= v)
                if ok(H.loc[per, k]):
                    r[k + "_rewind_years"] = 0.0
                    continue
                pers = [p for p in H.index if p <= per][::-1]      # per, per-50, ... back to 1600
                found = None
                for a, b in zip(pers, pers[1:]):                   # walk back segment by segment
                    ha, hb = H.loc[a, k], H.loc[b, k]
                    if ok(hb):
                        f = (v - ha) / (hb - ha) if hb != ha else 1.0
                        found = (a + 25) + f * ((b + 25) - (a + 25))
                        break
                r[k + "_rewind_years"] = (per + 25) - found if found is not None else np.nan
                r[k + "_censored"] = found is None
            rows.append(r)
    return pd.DataFrame(rows), H


def dating(T, feats=FEATS, primers_in_training=True):
    """Method (2): cross-fitted metrical dating; rewind = date(poets) - date(model), per poem."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.isotonic import IsotonicRegression
    global FEATS_USED
    FEATS_USED = feats
    T = T[T.who.ne("primer") | primers_in_training].dropna(subset=feats + ["year"]).copy()
    human = T.who.eq("primer") | T.who.str.startswith("poets:")
    T["pred"] = np.nan
    poems = T.poem_id.unique()
    rng = np.random.RandomState(20260924)
    fold_of = dict(zip(poems, rng.randint(0, 5, len(poems))))
    T["fold"] = T.poem_id.map(fold_of)
    for f in range(5):
        tr = human & (T.fold != f)
        mdl = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, random_state=0)
        mdl.fit(T.loc[tr, feats], T.loc[tr, "year"], sample_weight=np.sqrt(T.loc[tr, "windows"]))
        te = T.fold == f
        T.loc[te, "pred"] = mdl.predict(T.loc[te, feats])
    hc = T[T.who.str.startswith("poets:")]
    iso = IsotonicRegression(out_of_bounds="clip").fit(hc.pred, hc.year)
    T["pred_cal"] = iso.predict(T.pred)
    from scipy.stats import spearmanr
    val = []
    for name, sub in (("poets' continuations", hc), ("primers", T[T.who == "primer"])):
        if not len(sub):
            continue
        err = sub.pred - sub.year
        val.append(dict(texts=name, n=len(sub), r2=1 - (err ** 2).sum() / ((sub.year - sub.year.mean()) ** 2).sum(),
                        mae_years=err.abs().mean(), spearman=spearmanr(sub.pred, sub.year)[0],
                        pred_sd=sub.pred.std(), true_sd=sub.year.std()))
    rows = []
    for m, (lab, tier, grp) in MODELS.items():
        a = T[T.who == m].set_index("poem_id")
        h = T[T.who == "poets:" + grp].set_index("poem_id")
        j = a.join(h, rsuffix="_poets", how="inner")
        for scope, jj in [("all periods", j)] + [(str(int(p)), g) for p, g in j.groupby("period")]:
            if len(jj) < 20:
                continue
            for kind, col in (("metrical years", "pred"), ("calibrated years", "pred_cal")):
                d = jj[col + "_poets"] - jj[col]
                rows.append(dict(model=lab, tier=tier, scope=scope, kind=kind, poems=len(jj),
                                 rewind=d.mean(), ci95=1.96 * d.std() / np.sqrt(len(jj)),
                                 model_date=jj[col].mean(), poets_date=jj[col + "_poets"].mean(),
                                 true_year=jj.year.mean()))
    return pd.DataFrame(rows), pd.DataFrame(val)


def primer_deltas(T):
    """Continuation minus its own poem's 5-line primer, per poem, for each model and for the poets
    (the poets' delta is the natural drift within a poem); slope of continuation on primer."""
    from scipy.stats import wilcoxon
    M = {"num_parses": "uncertainty", "num_viols_allparse_sum": "tension", "uip": "uIP", "puip": "puIP"}
    pr = T[T.who == "primer"].set_index("poem_id")[list(M)]
    rows = []
    for m, (lab, tier, grp) in MODELS.items():
        a = T[T.who == m].set_index("poem_id")[list(M)]
        h = T[T.who == "poets:" + grp].set_index("poem_id")[list(M)]
        j = a.join(h, rsuffix="_poet", how="inner").join(pr, rsuffix="_primer", how="inner").dropna()
        r = dict(model=lab, tier=tier, poems=len(j))
        for c, k in M.items():
            dm, dp = j[c] - j[c + "_primer"], j[c + "_poet"] - j[c + "_primer"]
            r.update({k + "_primer": j[c + "_primer"].mean(), k + "_delta_model": dm.mean(), k + "_delta_poets": dp.mean(),
                      k + "_p_model_vs_poets": wilcoxon(dm - dp).pvalue,
                      k + "_slope_model": np.polyfit(j[c + "_primer"], j[c], 1)[0],
                      k + "_slope_poets": np.polyfit(j[c + "_primer"], j[c + "_poet"], 1)[0]})
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    V = load()
    T = texts(V)
    primer_deltas(T).round(4).to_csv(os.path.join(HERE, "results", "primer_deltas.csv"), index=False)
    L, H = lookup(T)
    configs = {"base features, poets + primers": (FEATS, True),
               "base features, poets only": (FEATS, False),
               "base + O/R/S features, poets only": (FEATS + ORS_FEATS, False)}
    runs = {name: dating(T, f, p) for name, (f, p) in configs.items()}
    cmp = pd.concat([v.assign(config=k) for k, (_, v) in runs.items()])
    print("dating validation by configuration:\n", cmp[["config", "texts", "n", "r2", "mae_years", "spearman", "pred_sd", "true_sd"]].round(3).to_string(index=False), "\n")
    poets_r2 = lambda v: v.loc[v.texts == "poets' continuations", "r2"].iloc[0]
    best = max(runs, key=lambda k: poets_r2(runs[k][1]))
    print("best configuration:", best, "\n")
    D, val = runs[best]
    D = D.assign(config=best)
    cmp_rewind = pd.concat([d[d.scope == "all periods"].assign(config=k) for k, (d, _) in runs.items()])
    cmp_rewind.round(2).to_csv(os.path.join(HERE, "results", "rewind_dating_by_config.csv"), index=False)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    L.round(3).to_csv(os.path.join(HERE, "results", "rewind_lookup.csv"), index=False)
    D.round(2).to_csv(os.path.join(HERE, "results", "rewind_dating.csv"), index=False)
    val.round(3).to_csv(os.path.join(HERE, "results", "dating_validation.csv"), index=False)
    pd.set_option("display.width", 250)
    print("poets' continuation curve by period:\n", H.round(2).to_string(), "\n")
    s = L.groupby(["tier", "model"]).agg(poems=("poems", "sum"), u_rewind=("num_parses_rewind_years", "mean"),
                                         u_censored=("num_parses_censored", "mean"), uip_rewind=("uip_rewind_years", "mean"),
                                         uip_censored=("uip_censored", "mean"))
    print("(1) lookup, mean over periods (rewind years; censored = share of periods with no human period as metrical back to 1600):\n",
          s.round(2).to_string(), "\n")
    print("(2) dating validation:\n", val.round(3).to_string(index=False), "\n")
    print("(2) rewind, all periods, by configuration (metrical years):")
    print(cmp_rewind[cmp_rewind.kind == "metrical years"].pivot(index="model", columns="config", values="rewind").round(1).to_string())


if __name__ == "__main__":
    main()
