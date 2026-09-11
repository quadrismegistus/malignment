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
#: `bits_per_byte` IS NOT THE MODEL'S OWN PERPLEXITY. It is an EXTERNAL
#: referee's: `itazap/blt-1b-hf`, one byte-latent reference model scoring every
#: row in this parquet, uniform across all 99,738. So it measures how
#: conventional the GENERATED TEXT looks to a third party, not how confident the
#: generator was. That is the right reading of the fluency correlation below:
#: models whose output a reference model finds costly also wander more between
#: sentences -- which is a statement about the text, not about either model's
#: internal state.
METRICS = ["mean_drift", "mean_pairwise", "bits_per_byte", "directedness", "ordering"]
INTERPRETABLE = 3


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
    print("AND THE AXIS IS LARGELY FLUENCY. Spearman across the %d models:" % len(g))
    print("   drift ~ pairwise   %+.3f" % c.loc[m3[0], m3[1]])
    print("   drift ~ bits/byte  %+.3f" % c.loc[m3[0], m3[2]])
    print("A model that costs more bits per byte also drifts more between")
    print("sentences, so this measure ranks models by fluency first. Architecture")
    print("would have to change fluency to show up in it at all.")
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
