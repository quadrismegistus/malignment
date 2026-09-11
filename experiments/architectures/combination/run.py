#!/usr/bin/env python
"""Does the SYNTAGMATIC axis depend on the attention mechanism?

    python run.py
    python run.py --corpus f11_l2 --min-sents 2

## WHY THIS QUESTION EXISTS, AND WHY IT SHOULD HAVE COME OUT THE OTHER WAY

The other questions in this subject all read the PARADIGMATIC axis: which word
goes in a slot. That is the unembedding matrix and the output softmax -- the
hidden state scored against every vocabulary item and normalised against all of
them -- and every model in the census has one, transformer or not. Their nulls
are therefore cheap: they read the architecturally invariant part.

**Attention is a COMBINATION mechanism.** It relates positions within a
sequence, items present together in the chain, Saussure's *in praesentia*. That
is the syntagmatic axis by definition, and it is the one place the census has an
actual reason to expect a difference. `jakobson_space` already measures it:
sentence-to-sentence drift through bge space, cohesion, directedness.

**The prediction was that architecture would show here and it does not.** Stated
before the run and recorded because a failed prediction is worth more than an
unstated one.

## THE JOIN KEY IS `prompt`, NOT `prompt_id`

`prompt_id` is assigned PER MODEL in this parquet: pairwise overlap between any
two of these models is exactly ZERO, and a join on it returns an empty frame
rather than an error. The prompt TEXT overlaps on 147-190. This cost one silent
empty result before it was noticed.

## ONLY THREE OF THE FIVE METRICS CLEAR THEIR OWN NOISE

Measured, across-model spread against the median within-model IQR over prompts:

    mean_drift      1.77x      mean_pairwise   1.95x     bits_per_byte  2.96x
    directedness    0.95x      ordering        0.66x     <- BELOW THE NOISE

`directedness` and `ordering` are reported and then not interpreted. On a first
pass `falcon-mamba-7b` ranked 1/6 and 6/6 on those two and it would have read as
the attention-free model being extreme; it is inside the prompt-to-prompt noise.
`drift_geometry/README.md` separately warns that only the length-free metrics
are comparable at all, which is why the cumulative ones are not here.
"""
import argparse
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

PARQUET = os.path.expanduser("~/malignment-data/jakobson_space/passages_std.parquet")
#: length-free only. The first three clear their noise floor; the last two do not.
#: **`bits_per_byte` IS THE SUPERSEDED EXTERNAL AXIS AND IS LABELLED, NOT READ
#: AS "FLUENCY".** Two facts about it, both from
#: `passage_analysis/jakobson_space/README.md`, which should have been read
#: before this file was written:
#:
#:   1. It is not the generating model's perplexity. It is `itazap/blt-1b-hf`,
#:      one byte-latent reference scoring every row uniformly -- an external
#:      referee's opinion of the TEXT, not the generator's confidence.
#:   2. **It is not the campaign's surprisal axis any more.** That README's
#:      table reads "external BLT per BYTE: BUILT" and "external
#:      deepseek-llm-7b-base per TOKEN: BUILT -- the one to use", under a
#:      heading that says SUPERSEDED. BLT findings still stand on their own
#:      axis (`alignment_smooths.md`, 42/46 lineages); it is simply not the
#:      yardstick to reach for first.
#:
#: **THE DEEPSEEK AXIS CANNOT SERVE THIS QUESTION**, which is why the BLT
#: column is still here. It lives in `results/two_axes.csv` and
#: `results/quadrants.csv`, and of this subject's architecture set those hold
#: only OLMoE-1B-7B-0125, Olmo-3-1025-7B and Falcon3-7B-Base -- one MoE and two
#: dense transformers, no pure SSM, no hybrid, no Griffin, no RWKV. Worse for
#: this question, `quadrants.csv` carries `drift_residual`, drift net of
#: surprisal, which is exactly the fluency-orthogonal measure this folder wants
#: and cannot use for lack of models.
#:
#: `ref_surprisal.py` scores arbitrary text with deepseek and is roundtrip
#: guarded, so extending the axis to these passages is a compute job rather
#: than a new instrument. Until that runs, every number below carrying
#: `bits_per_byte` is a BLT-axis number and says so.
METRICS = ["mean_drift", "mean_pairwise", "bits_per_byte", "directedness", "ordering"]
INTERPRETABLE = 3


#: BOTH ARMS of four non-dense lineages live here as SEPARATE model rows, which
#: is why an arm pairing has to be declared rather than read off a column.
LINEAGES = [
    ("tiiuae/falcon-mamba-7b",        "tiiuae/falcon-mamba-7b-instruct"),
    ("tiiuae/Falcon3-Mamba-7B-Base",  "tiiuae/Falcon3-Mamba-7B-Instruct"),
    ("tiiuae/Falcon-H1-7B-Base",      "tiiuae/Falcon-H1-7B-Instruct"),
    ("allenai/OLMoE-1B-7B-0125",      "allenai/OLMoE-1B-7B-0125-DPO"),
    #: dense controls, same corpus, same slice
    ("allenai/Olmo-3-1025-7B",        "allenai/Olmo-3-7B-Instruct"),
    ("tiiuae/Falcon3-7B-Base",        "tiiuae/Falcon3-7B-Instruct"),
    ("google/gemma-2-9b",             "google/gemma-2-9b-it"),
]


def score_pool(a):
    """Score this subject's passages through `malignment.score.surprisal`.

    **NOT `ref_surprisal.py` standalone, and the difference is reuse.** Both run
    the same model -- `score.REF` is `deepseek-ai/deepseek-llm-7b-base`, which is
    jakobson's reference -- but `score.surprisal` keys on `sha(text)` against a
    shared store that already holds 96,305 scored passages, skips anything
    present, and makes what it adds available to every other question. The
    standalone script writes a private sidecar keyed to one output directory.
    The first version of this file ran the standalone one; 0 of its 5,200
    passages were in the store, so nothing was duplicated, but nothing would
    have been reusable either.

    THE PREFIX IS 50, NOT jakobson's 200. A prefix mean is a length statistic
    if taken over everything, which is why a fixed M exists -- but
    `score.surprisal` DROPS a passage shorter than M rather than shortening the
    window, so M selects on length and length differs by model. At M=200
    `falcon-mamba-7b-instruct` retains 56% and `gemma-2-9b-it` 100%. See
    --prefix.
    """
    import pandas as pd
    from malignment import score
    d = pd.read_parquet(PARQUET, columns=["model", "arm", "prompt", "corpus",
                                          "script", "n_sents", "text", "text_sha"])
    want = [m for pair in LINEAGES for m in pair]
    d = d[(d["model"].isin(want)) & (d["script"] == a.script)
          & (d["corpus"] == a.corpus) & (d["n_sents"] >= a.min_sents)]
    #: a plain concat, not groupby.apply: apply drops the grouping column in
    #: this pandas, and the sample is per model by construction anyway.
    take = pd.concat([g.sample(n=min(a.per_model, len(g)), random_state=20260911)
                      for _, g in d.groupby("model")], ignore_index=True)
    texts = list(take["text"])
    idx = score._index("surprisal")
    todo = sum(1 for t in texts if score.sha(t) not in idx)
    print("%d passages over %d models; %d already in the shared store, %d to score"
          % (len(texts), take["model"].nunique(), len(texts) - todo, todo))
    print("prefix M=%d" % a.prefix)
    out = score.surprisal(texts, m=a.prefix)
    take = take.assign(surprisal=out)
    keep = take.dropna(subset=["surprisal"])
    dst = os.path.join(HERE, "results_surprisal.csv")
    keep[["model", "arm", "prompt", "text_sha", "n_sents", "surprisal"]].to_csv(dst, index=False)
    print("scored %d of %d (None = fewer than M scored tokens), wrote %s"
          % (len(keep), len(take), os.path.basename(dst)))
    return 0


def build_pool(a):
    """Write the deepseek input for this subject. Scored by ref_surprisal.py.

    SHUFFLED AND SEEDED, copying `build_ref_pool.py`'s reason verbatim: a run
    stopped early must be a SAMPLE and not a prefix. One file, so every model is
    scored by one reference on one device in one pass.
    """
    import json
    import random
    import pandas as pd
    d = pd.read_parquet(PARQUET, columns=["model", "arm", "prompt", "corpus",
                                          "script", "n_sents", "text", "text_sha"])
    want = [m for pair in LINEAGES for m in pair]
    d = d[(d["model"].isin(want)) & (d["script"] == a.script)
          & (d["corpus"] == a.corpus) & (d["n_sents"] >= a.min_sents)]
    rows, rng = [], random.Random(20260911)
    for m, g in d.groupby("model"):
        take = g.sample(n=min(a.per_model, len(g)), random_state=20260911)
        for r in take.itertuples():
            rows.append({"id": "%s|%s" % (m, r.text_sha), "pool": "architecture",
                         "model": m, "arm": r.arm, "prompt": r.prompt,
                         "text_sha": r.text_sha, "text": r.text})
    rng.shuffle(rows)
    with open(a.build_pool, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    got = {}
    for r in rows:
        got[r["model"]] = got.get(r["model"], 0) + 1
    print("wrote %d passages over %d models -> %s" % (len(rows), len(got), a.build_pool))
    for m in sorted(got):
        print("   %-36s %5d  %s" % (m.split("/")[-1][:36], got[m],
                                    "/".join(roster_arch(m))))
    print()
    print("now:  python experiments/passage_analysis/jakobson_space/ref_surprisal.py \\")
    print("          --input %s --out $MALIGNMENT_DATA/ref_pool/architecture" % a.build_pool)
    return 0


def roster_arch(m):
    from malignment import roster
    return roster.architecture(m)


def spread(a):
    """Where do the attention-free models fall in the WHOLE distribution?

    The 6-model paired set answers "are these six alike"; it cannot say whether
    a rank is unusual, because six models have no distribution. This ranks every
    base model with enough coverage on a common prompt core.
    """
    import pandas as pd
    from malignment import roster
    m3 = METRICS[:INTERPRETABLE]
    d = pd.read_parquet(PARQUET,
                        columns=["model", "arm", "prompt", "corpus", "script",
                                 "n_sents"] + m3)
    d = d[(d["arm"] == a.arm) & (d["corpus"] == a.corpus)
          & (d["n_sents"] >= a.min_sents) & (d["script"] == a.script)]
    cov = d.groupby("model")["prompt"].nunique()
    models = sorted(cov[cov >= a.min_prompts].index)
    d = d[d["model"].isin(models)]
    share = d.groupby("prompt")["model"].nunique()
    core = set(share[share >= int(len(models) * 0.9)].index)
    d = d[d["prompt"].isin(core)]
    print("%d models with >= %d prompts, %d common-core prompts, %d passages\n"
          % (len(models), a.min_prompts, len(core), len(d)))
    pm = d.groupby(["model", "prompt"])[m3].median().reset_index()
    g = pm.groupby("model")[m3].median()
    order = {c: list(g.sort_values(c).index) for c in m3}
    print("%-26s %-11s %-7s %s" % ("model", "attn", "block",
          " ".join("%9s %5s" % (c[:9], "rank") for c in m3)))
    rows = [(m, roster.architecture(m)) for m in g.index]
    nd = [(m, ab) for m, ab in rows if ab[1] != "dense"]
    for m, (at, bl) in sorted(nd, key=lambda x: g.loc[x[0], m3[0]]):
        print("%-26s %-11s %-7s %s" % (m.split("/")[-1][:26], at, bl,
              " ".join("%9.4f %4d/%d" % (g.loc[m, c], order[c].index(m) + 1, len(g))
                       for c in m3)))
    print("%-26s %-11s %-7s %s" % ("-- median of all %d --" % len(g), "", "",
          " ".join("%9.4f %5s" % (g[c].median(), "") for c in m3)))
    print()
    print("EXTREMES on %s, and every one of them is a DENSE transformer:" % m3[0])
    srt = g.sort_values(m3[0])
    for m in list(srt.index[:3]) + list(srt.index[-3:]):
        at, bl = roster.architecture(m)
        print("   %-28s %-11s %-7s %.4f" % (m.split("/")[-1][:28], at, bl, g.loc[m, m3[0]]))
    print()
    c = g[m3].corr(method="spearman")
    print("AND THE AXIS TRACKS THE BLT REFEREE (the SUPERSEDED external axis;")
    print("deepseek is the campaign's, and covers 3 of this subject's models).")
    print("Spearman across the %d models:" % len(g))
    print("   drift ~ pairwise   %+.3f" % c.loc[m3[0], m3[1]])
    print("   drift ~ bits/byte  %+.3f" % c.loc[m3[0], m3[2]])
    print("A model whose text BLT finds costly also drifts more between")
    print("sentences, so drift ranks models by an external quality judgement")
    print("first. Architecture would have to move that to register at all.")
    print("The clean test is quadrants.csv's drift_residual, drift NET of")
    print("surprisal -- which exists, on deepseek, for 3 of these models.")
    return 0


def main():
    import pandas as pd
    from malignment import roster
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="passage")
    ap.add_argument("--arm", default="base")
    ap.add_argument("--min-sents", type=int, default=3)
    ap.add_argument("--models", default=None,
                    help="comma-separated override of the declared population")
    ap.add_argument("--spread", action="store_true",
                    help="rank the non-dense models against EVERY model with "
                         "enough coverage, instead of the 6-model paired set. "
                         "Drops models under --min-prompts, then keeps prompts "
                         "held by >=90%% of what remains, so the comparison is "
                         "on a common core rather than each model's own mix.")
    ap.add_argument("--min-prompts", type=int, default=150)
    ap.add_argument("--build-pool", metavar="OUT.jsonl", default=None,
                    help="write a deepseek ref pool for THIS subject's models "
                         "and stop. The jakobson deepseek axis cannot reach "
                         "these architectures at any price -- its pool is gated "
                         "on a 58-model blind narrative coding over f11_l2, and "
                         "f11_l2 holds only 3 of this subject's models, all of "
                         "them dense or MoE. So the pool is rebuilt here, "
                         "self-contained: same scorer, same one-model-one-pass "
                         "discipline, NOT joinable to two_axes.csv because the "
                         "corpus and the coding differ.")
    ap.add_argument("--per-model", type=int, default=400)
    ap.add_argument("--score", action="store_true",
                    help="score this subject's passages with the reference model "
                         "THROUGH malignment.score, so the result lands in the "
                         "shared sha-keyed store (96,305 entries already) rather "
                         "than a private sidecar. Same model as jakobson's pass, "
                         "deepseek-llm-7b-base; nothing is rescored.")
    ap.add_argument("--prefix", type=int, default=50,
                    help="mean surprisal over the first M scored tokens. NOT "
                         "jakobson's M=200, and the difference is a confound: "
                         "score.surprisal returns None when a passage has FEWER "
                         "than M tokens, so the prefix SELECTS ON LENGTH, and "
                         "length varies by model. Measured retention at M=200: "
                         "falcon-mamba-7b-instruct 56%%, gemma-2-9b-it 100%% -- a "
                         "44-point differential on the one model that has already "
                         "failed two other screens. At M=50 it is 96%% and 100%%. "
                         "M=200 is right for jakobson, whose human corpora all "
                         "clear it; it is wrong for a cross-MODEL comparison.")
    ap.add_argument("--script", default="en",
                    help="ENGLISH ONLY BY DEFAULT (RH, 2026-09-11). The zh rows "
                         "go through a different pipeline entirely -- stanza-zh "
                         "segmentation and the zh bge variant, against nltk-en -- "
                         "so a sentence is not the same unit on both sides, and "
                         "this campaign already holds that bits/char is not "
                         "comparable across scripts. 48 of 99,786 rows in the "
                         "base/passage set are zh: too few to matter to a median "
                         "and no reason at all to carry.")
    a = ap.parse_args()

    if a.score:
        return score_pool(a)
    if a.build_pool:
        return build_pool(a)
    if a.spread:
        return spread(a)
    cols = ["model", "arm", "prompt", "corpus", "script", "n_sents"] + METRICS
    d = pd.read_parquet(PARQUET, columns=cols)
    d = d[(d["arm"] == a.arm) & (d["corpus"] == a.corpus)
          & (d["n_sents"] >= a.min_sents) & (d["script"] == a.script)]
    #: **THE POPULATION IS NAMED, NOT FILTERED.** Every non-dense architecture
    #: this parquet actually covers, plus dense controls. Taking "every model
    #: with >= 50 prompts" instead admits ~40 checkpoints, and requiring a
    #: prompt shared by ALL of them collapses the paired set from 147 to NINE.
    #: The pairing is the instrument here, so the set is declared.
    #:
    #: recurrentgemma-9b is DELIBERATELY absent and this is the finding that
    #: costs the most: it holds 38 rows at a median of ONE sentence, so drift
    #: is undefined for it, and the attested same-corpus contrast
    #: (gemma-2-9b vs recurrentgemma-9b) CANNOT BE RUN on this dataset. The
    #: best-controlled pair in the subject is the one the data cannot serve.
    #: Olmo-Hybrid, Zamba2, RWKV and falcon-7b are absent from the parquet.
    DEFAULT = ["tiiuae/falcon-mamba-7b",       # none / ssm
               "tiiuae/Falcon-H1-7B-Base",     # full+ssm / hybrid
               "allenai/OLMoE-1B-7B-0125",     # full / moe
               "allenai/Olmo-3-1025-7B",       # full+local / dense
               "google/gemma-2-9b",            # full / dense
               "tiiuae/Falcon3-7B-Base"]       # full / dense
    models = sorted(set(a.models.split(",")) if a.models else set(DEFAULT))
    missing = [m for m in models if m not in set(d["model"])]
    if missing:
        print("not in the parquet: %s" % ", ".join(missing))
    models = [m for m in models if m not in missing]
    d = d[d["model"].isin(models)]
    d = d[d["model"].isin(models)]
    have = d.groupby("prompt")["model"].nunique()
    keep = set(have[have == len(models)].index)
    d = d[d["prompt"].isin(keep)]
    print("SYNTAGMATIC axis, %s arm, corpus=%s, script=%s, n_sents>=%d"
          % (a.arm, a.corpus, a.script, a.min_sents))
    print("%d models, %d prompts held by ALL of them, %d passages\n"
          % (len(models), len(keep), len(d)))
    if not len(keep):
        print("no shared prompts -- are you joining on `prompt` and not `prompt_id`?")
        return 1

    #: per (model, prompt) first, so a model with more samples per prompt does
    #: not get more weight in the model-level median.
    pm = d.groupby(["model", "prompt"])[METRICS].median().reset_index()
    g = pm.groupby("model")[METRICS].median()
    print("%-22s %-11s %-7s %s"
          % ("model", "attn", "block", " ".join("%9s" % m[:9] for m in METRICS)))
    for m, r in g.sort_values(METRICS[0]).iterrows():
        at, bl = roster.architecture(m)
        print("%-22s %-11s %-7s %s"
              % (m.split("/")[-1][:22], at, bl,
                 " ".join("%9.4f" % r[c] for c in METRICS)))
    print()
    print("DOES THE SPREAD CLEAR THE NOISE IT SITS IN?")
    for i, c in enumerate(METRICS):
        across = g[c].max() - g[c].min()
        iqr = st.median([pm[pm["model"] == m][c].quantile(.75)
                         - pm[pm["model"] == m][c].quantile(.25) for m in models])
        flag = "" if i < INTERPRETABLE else "   <- BELOW NOISE, not interpreted"
        print("   %-14s across %.4f   within-model IQR %.4f   ratio %.2f%s"
              % (c, across, iqr, across / iqr if iqr else float("nan"), flag))
    print()
    #: the paired form, which is what actually identifies an outlier.
    piv = pm.pivot(index="prompt", columns="model", values="mean_drift")
    lo = g[METRICS[0]].idxmin()
    print("PAIRED on prompt: how often does each model exceed %s on mean_drift?"
          % lo.split("/")[-1])
    for m in models:
        if m == lo:
            continue
        both = piv[[m, lo]].dropna()
        w = (both[m] > both[lo]).sum()
        print("   %-24s %3d/%3d  (%.0f%%)"
              % (m.split("/")[-1][:24], w, len(both), 100.0 * w / len(both)))
    print()
    print("THE ONE ROBUST BETWEEN-MODEL EFFECT IS A DENSE FULL-ATTENTION MODEL,")
    print("and the attention-free model sits mid-pack on every metric that")
    print("clears its own noise. The prediction in the docstring failed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
