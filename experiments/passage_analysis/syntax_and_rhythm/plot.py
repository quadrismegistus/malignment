"""Metrical uncertainty and tension, human and model -> figures/meter-map.html. EXPLORATORY.

    python plot.py

Reads the stored grains (by_window.csv, by_window_verse.csv, by_passage.csv)
and the human baseline, writes figures/meter_points.json (every plotted value, with
standard errors and sample sizes) and figures/meter-map.html (the page, from
figures/meter_map.template.html). Not a registered analysis: the verse side and the
historical placement were added after the registration (README, "Exploratory").

Periods are 50-year bins, 1600-1999; 2000-2049 is dropped everywhere (not a full
half-century, and sparse). Dating:
  human prose    the reparse's `year`: publication year (it carries no author_dob)
  human verse    author_dob + 30, which is what the reparse's `year` already is for
                 poetry (generative-formalism itself bins by bare author_dob, so its
                 periods sit 30 years earlier than these)
  model verse    the period of the poem being continued, by the same rule
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "syntax_and_rhythm")
BASE = os.environ.get("ANTIMETRICALITY_REPARSE", os.path.expanduser(
    "~/Dropbox/Prof/Articles/Antimetricality/data/data.2026.reparse.big_data.parquet"))
GENFORM = os.environ.get("GENFORM_REPO", os.path.expanduser("~/github/generative-formalism"))
PILOT = os.path.expanduser("~/github/malign-logits/meta/M05_emergence/data/rhyme_pilot.parquet")
SMALL = os.path.join(os.path.dirname(BASE), "data.2026.reparse.small_data.parquet")
M = ["num_parses", "num_viols_allparse_sum"]
IP = "wswswswsws"
#: completion models by tier. base/open-aligned pairs share a poets' baseline (group =
#: the base model); the others each carry their own (group = the model).
TIER = {"ollama/llama3.1:8b-text-q4_K_M": ("base", "Llama-3.1-8B"), "ollama/mistral:text": ("base", "Mistral-7B"),
        "ollama/llama3.1:8b": ("open aligned", "Llama-3.1-8B"), "ollama/mistral": ("open aligned", "Mistral-7B"),
        "ollama/olmo2:latest": ("open aligned", "OLMo-2"), "gpt-3.5-turbo": ("API", "GPT-3.5"),
        "claude-3-sonnet-20240229": ("API", "Claude-3-Sonnet"), "deepseek/deepseek-chat": ("API", "DeepSeek-chat")}


def pent(df):
    """uIP: best parse wswswswsws AND the only viable scansion; puIP: also zero violations."""
    ip = (df.meter == IP) & (df.num_parses == 1)
    return ip, ip & (df.num_viols_allparse_sum == 0)
LAST = 2000                                              # periods start < LAST


def summ(df, cluster):
    g = df.groupby(cluster)[M].mean()
    n = len(g)
    se = lambda c: float(g[c].std() / np.sqrt(n)) if n > 1 else None
    out = dict(n_windows=int(len(df)), n_units=int(n), u=float(df.num_parses.mean()),
               t=float(df.num_viols_allparse_sum.mean()), u_se=se("num_parses"), t_se=se("num_viols_allparse_sum"))
    if "meter" in df:
        a, b = pent(df)
        out.update(uip=float(100 * a.mean()), puip=float(100 * b.mean()))
    return out


def tiers(C):
    """One row per completion model: its uIP/puIP against its OWN poets, paired by poem."""
    from scipy.stats import wilcoxon
    C = C.assign(uip=100 * pent(C)[0].astype(float), puip=100 * pent(C)[1].astype(float))
    out = []
    for m, (tier, name) in TIER.items():
        g = C[C.model == m]
        if not len(g):
            continue
        hum = C[(C.arm == "human") & (C.group == g.group.iloc[0])]
        j = g.groupby("poem_id")[["uip", "puip"]].mean().join(hum.groupby("poem_id")[["uip", "puip"]].mean(), rsuffix="_poets", how="inner")
        r = dict(group="tier_model", tier=tier, model=name, label="%s (%s), verse continuations" % (name, tier),
                 source="generative-formalism completions; poets = line_real of the same poems", **summ(g, "poem_id"))
        for k in ("uip", "puip"):
            d = j[k] - j[k + "_poets"]
            r[k + "_poets"] = float(j[k + "_poets"].mean())
            r[k + "_p"] = float(wilcoxon(d).pvalue) if (d != 0).any() else None
        r["n_paired"] = int(len(j))
        out.append(r)
    return out


def scrambles(V, W):
    """Original / within-POS scramble (R) / full scramble (S), one row per text or tier.

    Human: the antimetricality small data's LSA texts (O/R/S = original, randomized
    within POS, fully scrambled; checked on the texts: R keeps the POS sequence, S
    does not). LLM prose: national_story pure stories. LLM verse: the continuations,
    pooled by tier, with the poets' own continuations of the same poems."""
    rows = []

    def row(who, kind, tier, frames):                      # frames: {"O": df, "R": df, "S": df}
        if any(len(df) == 0 for df in frames.values()):
            return
        r = dict(group="ors", label=who, kind_ors=kind, tier=tier, source="O/R/S scrambles")
        for v, df in frames.items():
            a, b = pent(df)
            r.update({"t_" + v: float(df.num_viols_allparse_sum.mean()), "u_" + v: float(df.num_parses.mean()),
                      "uip_" + v: float(100 * a.mean()), "puip_" + v: float(100 * b.mean()), "n_" + v: int(len(df))})
        r.update(t=r["t_O"], u=r["u_O"], uip=r["uip_O"], puip=r["puip_O"], n_windows=r["n_O"], n_units=0)
        rows.append(r)

    if os.path.exists(SMALL):
        sm = pd.read_parquet(SMALL)
        sm = sm[(sm.corpus == "LSA") & (sm.method == "new_nsyll") & (sm.num_sylls_canonical == 10) & sm.num_parses.notna()]
        KIND = {"shakespeare": "human verse", "dibble": "human utility prose", "dickens": "human fiction"}
        for au, g in sm.groupby("author"):
            row(au.capitalize(), KIND.get(au, "human art prose"), "human", {v: g[g.text_type == v] for v in "ORS"})
    VER = {"O": "orig", "R": "shuffle_pos", "S": "shuffle_all"}
    for arm in ("base", "aligned"):
        x = W[W.arm == arm]
        row("LLM prose, " + arm, "LLM prose", arm, {v: x[x.version == VER[v]] for v in "ORS"})
    C = V[V.source == "genai_completion"]
    tier = C.model.map(lambda m: "poets" if str(m).startswith("human:") else TIER.get(m, ("?",))[0])
    for tr, lab in (("base", "LLM verse, base"), ("open aligned", "LLM verse, open aligned"),
                    ("API", "LLM verse, API"), ("poets", "Poets' continuations")):
        x = C[tier == tr]
        row(lab, "human verse" if tr == "poets" else "LLM verse", tr, {v: x[x.version == VER[v]] for v in "ORS"})
    return rows


def points():
    pts = []
    b = pd.read_parquet(BASE, columns=["metagenre", "year", "num_sylls_canonical", "author", "meter"] + M)
    b = b[(b.num_sylls_canonical == 10) & b.year.notna() & (b.year < LAST)]
    b["period"] = (b.year // 50 * 50).astype(int)
    for g in ["Poetry", "Fiction", "Non-Fiction"]:
        x = b[b.metagenre == g]
        key = g.lower().replace("-", "")
        for per, y in x.groupby("period"):
            if len(y) >= 300:
                pts.append(dict(group="human_" + key, label="%s %d–%d" % (g, per, per + 49), period=int(per),
                                source="Antimetricality reparse (10-syll lines)", **summ(y, "author")))
        pts.append(dict(group="human_all_" + key, label="%s, 1600–1999" % g, source="Antimetricality reparse", **summ(x, "author")))

    V = pd.read_csv(os.path.join(DATA, "by_window_verse.csv"), low_memory=False)
    V = V[V.win_idx >= 0]
    V["version"] = V.version.fillna("orig") if "version" in V else "orig"
    Vall, V = V, V[V.version == "orig"]                  # scrambles only for scrambles()
    for per, y in V[V.source == "human_period"].groupby("group"):
        if int(per[:4]) + 30 + 25 < LAST:                # the +30 bin's midpoint must fall before 2000
            pts.append(dict(group="human_chadwyck", label="Chadwyck poems, authors born %s" % per, period=int(per[:4]) + 30,
                            source="generative-formalism sample (dated here by author_dob + 30)", **summ(y, "poem_id")))
    meta = pd.read_csv(os.path.join(GENFORM, "data/raw/corpus/chadwyck_corpus_metadata.csv.gz"),
                       usecols=["id", "author_dob"], low_memory=False)
    meta["p30"] = ((pd.to_numeric(meta.author_dob, errors="coerce") + 30) // 50 * 50).astype("Int64")
    # the by-period figure is the two base/instruct pairs only (their shared poets' baseline)
    PAIR_BASES = ("ollama/llama3.1:8b-text-q4_K_M", "ollama/mistral:text")
    C = V[(V.source == "genai_completion") & V.group.isin(PAIR_BASES)].merge(meta.rename(columns={"id": "poem_id"})[["poem_id", "p30"]], on="poem_id", how="left")
    C = C[C.p30 < LAST]
    AR = {"human": ("poets", "human"), "base": ("base models", "base"), "instruct": ("aligned models", "aligned")}
    for (per, arm), g in C.groupby(["p30", "arm"]):
        pts.append(dict(group="verse_period", period=int(per), arm=AR[arm][1],
                        label="Verse continuations by %s: authors turning 30 in %d–%d" % (AR[arm][0], per, per + 49),
                        source="generative-formalism completions (Llama-3.1-8B + Mistral-7B pairs; poets = line_real)",
                        **summ(g, "poem_id")))
    for arm, g in C.groupby("arm"):
        pts.append(dict(group="verse_overall", arm=AR[arm][1], label="Verse continuations by %s, 1600–1999" % AR[arm][0],
                        source="generative-formalism completions (Llama-3.1-8B + Mistral-7B pairs)", **summ(g, "poem_id")))
    pts.append(dict(group="human_continuation", label="Poets' own continuations, 1600–1999", source="generative-formalism completions (line_real)",
                    **summ(C[C.arm == "human"], "poem_id")))
    Call = V[V.source == "genai_completion"]                    # every model and poets' baseline, all periods
    pts += tiers(Call)
    if os.path.exists(SMALL):
        sm = pd.read_parquet(SMALL)
        sm = sm[(sm.method == "new_nsyll") & (sm.num_sylls_canonical == 10) & sm.num_parses.notna()]
        for au, lab in (("pope", "Pope (verse)"), ("wordsworth", "Wordsworth (verse)")):
            x = sm[(sm.corpus == "AMP") & (sm.author == au) & (sm.genre == "verse")]
            pts.append(dict(group="ref_author", label=lab, source="antimetricality small data (AMP)", **summ(x.assign(poem=0), "poem")))
    names = {"ollama/llama3.1:8b-text-q4_K_M": ("Llama-3.1-8B", "base"), "ollama/llama3.1:8b": ("Llama-3.1-8B", "aligned"),
             "ollama/mistral:text": ("Mistral-7B", "base"), "ollama/mistral": ("Mistral-7B", "aligned")}
    for m, (lin, arm) in names.items():
        pts.append(dict(group="llm_verse", lineage=lin, arm=arm, label="%s %s, verse continuation" % (lin, arm),
                        source="generative-formalism completions (ollama, 4-bit)", **summ(C[C.model == m], "poem_id")))
    Pp = V[V.source == "genai_prompt"]
    for pt, y in Pp.groupby("group"):
        pts.append(dict(group="llm_prompted", arm="aligned", label="Prompted poems: %s" % pt,
                        source="generative-formalism promptings (chat models)", **summ(y, "poem_id")))
    for m, y in Pp.groupby("model"):
        pts.append(dict(group="llm_prompted_model", arm="aligned", label="Prompted poems: %s" % m,
                        source="generative-formalism promptings", **summ(y, "poem_id")))

    if os.path.exists(PILOT):                            # archive pilot, 12 primers: never a result
        sys.argv = sys.argv[:1]
        sys.path.insert(0, HERE)
        import parse_passages_prosodic as pp
        d = pd.read_parquet(PILOT)
        rows = []
        for _, r in d[~d.model.str.startswith("human")].iterrows():
            for w in pp.meter_rows(pp.windows(pp.content_sylls(pp.TextModel(str(r.text))._syll_df))):
                if "num_parses" in w:
                    rows.append(dict(model=r.model, uid="%s|%s" % (r.id_human, r.sample_idx), **w))
        Wp = pd.DataFrame(rows)
        for m, arm in [("allenai/Olmo-3-1025-7B", "base"), ("allenai/Olmo-3-7B-Instruct-SFT", "aligned")]:
            pts.append(dict(group="llm_verse_pilot", lineage="Olmo-3-7B", arm=arm,
                            label="Olmo-3-7B %s verse (PILOT, 12 primers)" % ("base" if arm == "base" else "SFT"),
                            source="malign-logits rhyme_pilot (HF raw generation)", **summ(Wp[Wp.model == m], "uid")))

    P = pd.read_csv(os.path.join(DATA, "by_passage.csv"), low_memory=False).drop_duplicates(["id", "version"])
    ok = set(P[(P.version == "orig") & (P.overall == "story") & (P.pure_story == True)].id)
    W = pd.read_csv(os.path.join(DATA, "by_window.csv"), low_memory=False, usecols=["id", "version", "win_idx", "arm", "lineage", "meter"] + M)
    W = W[W.id.isin(ok) & W.num_parses.notna()].drop_duplicates(["id", "version", "win_idx"])
    Wall, W = W, W[W.version == "orig"]
    pts += scrambles(Vall, Wall)
    for arm in ["base", "aligned"]:
        pts.append(dict(group="llm_prose", lineage="all lineages", arm=arm, label="LLM prose, %s (all lineages)" % arm,
                        source="national_story pure stories", **summ(W[W.arm == arm], "id")))
    for lin in W.groupby("lineage").arm.nunique().loc[lambda s: s == 2].index:
        for arm in ["base", "aligned"]:
            pts.append(dict(group="llm_prose_lineage", lineage=lin.split("/")[-1], arm=arm, label="%s %s prose" % (lin.split("/")[-1], arm),
                            source="national_story pure stories", **summ(W[(W.lineage == lin) & (W.arm == arm)], "id")))
    return pts


def main():
    pts = points()
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    with open(os.path.join(HERE, "figures", "meter_points.json"), "w") as f:
        json.dump(pts, f, indent=0)
    t = open(os.path.join(HERE, "figures", "meter_map.template.html")).read()
    with open(os.path.join(HERE, "figures", "meter-map.html"), "w") as f:
        f.write(t.replace("__DATA__", json.dumps(pts)))
    print("%d points -> figures/meter-map.html" % len(pts))


if __name__ == "__main__":
    main()
