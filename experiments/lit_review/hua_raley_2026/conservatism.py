#!/usr/bin/env python
"""CLAIM 2: does the narrowing need the KL tether? Entropy and support per stage.

    python conservatism.py

## THE CLAIM

    "The mathematics of alignment builds the conservatism in."   (section 2)

## WHAT BEARS ON IT

Whether narrowing appears at a stage that HAS NO KL TETHER. SFT is plain
cross-entropy on demonstrations -- no reference-model penalty of any kind. PKU's
ladder separates the two:

    huggyllama/llama-7b -> alpaca-7b-reproduced     SFT,  NO KL
    alpaca-7b-reproduced -> beaver-7b-v1.0          Safe RLHF, EXPLICIT KL

## WHY NOT `sum|delta|`

**Because it answers a different question and this file exists because that
mistake was made here first.** `sum|delta|` measures how much mass moved. The
claim is about CONTRACTION -- entropy down, support collapsed, tail depopulated.
A stage can move mass hard and stay exactly as broad. The first version of this
entry read "the SFT stage moves twice as far" as "the conservatism is installed
at SFT", and that inference is not available from that statistic.

So: entropy in bits, and effective support `1 / sum(p^2)`, both on the scored
distribution, differenced per prompt and reported as medians.

## THE FENCE

Both are computed over `twp_words_v4_best`, which is theta-truncated. These are
"within what we score" and NOT absolute -- the true tail is not measured, which
matters here because the tail is precisely what the claim is about.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

MODELS = {"llama-7b": "huggyllama/llama-7b",
          "alpaca(SFT)": "PKU-Alignment/alpaca-7b-reproduced",
          "beaver(RLHF)": "PKU-Alignment/beaver-7b-v1.0"}
STAGES = [("llama -> alpaca   (SFT, NO KL)", "llama-7b", "alpaca(SFT)"),
          ("alpaca -> beaver  (RLHF, KL)", "alpaca(SFT)", "beaver(RLHF)"),
          ("llama -> beaver   (both)", "llama-7b", "beaver(RLHF)")]


def stats(model, prompts):
    """{prompt: (entropy_bits, effective_support, tail_mass_beyond_top5)}."""
    import numpy as np
    from malignment import vectors as V
    out = {}
    for i in range(0, len(prompts), 80):
        for r in V.rows("SELECT prompt, groupArray(p) ps FROM twp_words_v4_best "
                        "WHERE model={m:String} AND prompt IN {ps:Array(String)} "
                        "GROUP BY prompt", m=model, ps=prompts[i:i + 80]):
            p = np.sort(np.asarray(r["ps"], dtype=float))[::-1]
            p = p[p > 0]
            if len(p) < 2:
                continue
            out[r["prompt"]] = (float(-(p * np.log2(p)).sum()),
                                float(1.0 / (p ** 2).sum()),
                                float(p[5:].sum()) if len(p) > 5 else 0.0)
    return out


def main():
    import numpy as np
    from malignment import vectors as V
    ps = [r["prompt"] for r in V.rows(
        "SELECT prompt FROM twp_words_v4_best WHERE model={m:String} "
        "GROUP BY prompt ORDER BY prompt LIMIT 800", m=MODELS["beaver(RLHF)"])]
    S = {k: stats(v, ps) for k, v in MODELS.items()}
    sh = [p for p in ps if all(p in S[k] for k in MODELS)]
    print("CLAIM 2 -- conservatism per stage, %d prompts" % len(sh))
    print("entropy in bits; effective support = 1/sum(p^2); tail = mass beyond top-5")
    print()
    print("%-32s %11s %14s %12s" % ("stage", "median dH", "d eff.support", "d tail"))
    for name, a, b in STAGES:
        dh = np.median([S[b][p][0] - S[a][p][0] for p in sh])
        ds = np.median([S[b][p][1] - S[a][p][1] for p in sh])
        dt = np.median([S[b][p][2] - S[a][p][2] for p in sh])
        print("%-32s %+11.4f %+14.3f %+12.5f" % (name, dh, ds, dt))
    print()
    for k in MODELS:
        print("   level %-14s H=%.3f  eff.support=%.1f"
              % (k, np.median([S[k][p][0] for p in sh]),
                 np.median([S[k][p][1] for p in sh])))
    print()
    print("READING: both stages narrow, and on ENTROPY the KL-penalised stage")
    print("narrows slightly more -- so the claim is not refuted. But the stage")
    print("with NO tether produces the larger collapse of effective support.")
    print("The tether is not NECESSARY for the conservatism.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
