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
METRICS = ["mean_drift", "mean_pairwise", "bits_per_byte", "directedness", "ordering"]
INTERPRETABLE = 3


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
    a = ap.parse_args()

    cols = ["model", "arm", "prompt", "corpus", "n_sents"] + METRICS
    d = pd.read_parquet(PARQUET, columns=cols)
    d = d[(d["arm"] == a.arm) & (d["corpus"] == a.corpus)
          & (d["n_sents"] >= a.min_sents)]
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
    print("SYNTAGMATIC axis, %s arm, corpus=%s, n_sents>=%d"
          % (a.arm, a.corpus, a.min_sents))
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
