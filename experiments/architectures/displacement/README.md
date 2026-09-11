---
subject: architectures
kind: question
status: "RUN 2026-09-11 as a lookup over displacement/existence/results/selectivity.json plus a direct sum|delta| recompute from movement_v4. NOT REGISTERED. A DELTA instrument, and therefore weak evidence about architecture: see the caveat below and the subject README."
question: Does alignment's content-selective displacement depend on the attention mechanism?
headline: "Every architecture in the roster displaces except one, and the exception is confounded. falcon-mamba-7b has no attention and displaces at -0.000124; recurrentgemma-9b, Weatherby's own cited counter-architecture, at -0.000114. The two best-controlled contrasts DISAGREE in sign. rwkv-4-7b-pile (+0.000107) is the one non-displacer and is also among the seven weakest movers overall, so architecture is not identified against alignment strength here."
---

# displacement

**Does the content-selective displacement measured by `displacement/existence` depend on the architecture it runs on?**

This is a DELTA instrument and that is its weakness, not a detail: alignment is the most architecture-independent stage in the pipeline, so a convergent delta across the roster substantially records convergent post-training. The `similarity` question beside this one asks the same thing at base, where the answer is better founded.

## The charge instrument: what it showed, and why it is the weakest of the three



Content-selectivity slope from `existence` (negative means higher-charge words lose more mass, which is the operation). Roster grand median -0.000295, 43 of 50 lineages negative.

    model                    attn           block        slope      sum|d|
    Falcon-H1-1.5B-Base      full+ssm       hybrid    -0.000442        1566
    OLMoE-1B-7B-0125         full           moe       -0.000388        1686
    Olmo-Hybrid-7B           full+linear    hybrid    -0.000257        1303
    Zamba2-7B                full+ssm       hybrid    -0.000152         477
    falcon-mamba-7b          none           ssm       -0.000124         948
    recurrentgemma-9b        local+linear   hybrid    -0.000114        1933
    Falcon-H1-7B-Base        full+ssm       hybrid    -0.000048        1596
    rwkv-4-7b-pile           linear         dense     +0.000107         552
    -- roster median --                               -0.000295        1185

**Every architecture in the roster displaces except one, and the exception is confounded.** `falcon-mamba-7b` computes no token-token attention of any kind and displaces. Weatherby's own cited counter-architecture, Griffin, displaces. The hedge in (155) is the correct sentence; the surrounding claim is not.

`rwkv-4-7b-pile` is the only non-displacer among the eight. RWKV-4's WKV operator is time-decaying channel-wise linear attention with no token-token dot product ([A Survey of RWKV](https://arxiv.org/html/2412.14847v1)), so it would be the clean case for an attention requirement if the reading held. It does not hold: rwkv-raven-7b is one of seven non-displacing lineages whose median `sum|delta|` is 878 against 1,265 for a sample of twelve displacers. The seven barely move at all. A model that was hardly aligned cannot show a content-selective alignment effect, and architecture is not identified against alignment strength here.

## The matched contrasts, and why they disagree



    1  CONTROLLED BY DESIGN (AI2)
       Olmo-3-1025-7B     full          dense    -0.000159    2045
       Olmo-Hybrid-7B     full+linear   hybrid   -0.000257    1303

    2  SAME PRETRAINING CORPUS (Google)
       gemma-2-9b         full          dense    -0.000498    2261
       recurrentgemma-9b  local+linear  hybrid   -0.000114    1933

    3  ONE VENDOR, FOUR CORPORA (TII, all ~7B) -- WEAK, NOT A CONTROL
       falcon-7b          full          dense    -0.000266    1292
       Falcon3-7B-Base    full          dense    -0.000158    1109
       falcon-mamba-7b    none          ssm      -0.000124     948
       Falcon-H1-7B-Base  full+ssm      hybrid   -0.000048    1596

    4  DENSE vs MoE (AI2)
       Olmo-3-1025-7B     full          dense    -0.000159    2045
       OLMoE-1B-7B-0125   full          moe      -0.000388    1686

Contrast 1 is the best control in the roster and it is not ours. AI2 built Olmo Hybrid as a controlled experiment: "we train Olmo Hybrid, a 7B-parameter model largely comparable to Olmo 3 7B but with the sliding window layers replaced by Gated DeltaNet layers", demonstrating the benefit of hybrid models "in a controlled, large-scale setting" (arXiv:2604.03444, Merrill et al., 3 Apr 2026, quoted in `attestations.json`). Same lab, same three-stage pipeline, same data mix, 5.50T against 5.93T tokens. The declared architectural difference is the attention mechanism and nothing else. **Replacing attention layers with linear-attention layers made displacement stronger, not weaker.**

**Contrast 3 is not the vendor control it looks like, and should not be reported as one.** One lab is not one corpus, and the attestations say so: `falcon-7b` is RefinedWeb-English and RefinedWeb-French; `Falcon3-7B-Base` is a single 14T-token run over "web, code, STEM, and curated high-quality and multilingual data"; `falcon-mamba-7b` is 5.8T with "carefully selected data mixtures"; `Falcon-H1` is different again. Four models from one lab, four corpora. It is weaker than contrast 1 and weaker than contrast 2.

Contrast 2 is attested as sharing a corpus ("RecurrentGemma uses the same training data and data processing as used by the Gemma model family"; "The architecture is Griffin, not Gemma's transformer") and goes the other way by a factor of four.

### A reading that makes the two contrasts agree, POST HOC and unregistered

The two swaps are not the same manipulation in opposite directions. They remove different halves of the attention mechanism.

    contrast 1   Olmo-Hybrid KEEPS full attention and loses its SLIDING-WINDOW
                 layers (replaced by Gated DeltaNet).   local removed
                 -0.000159 -> -0.000257                 displacement UP
    contrast 2   recurrentgemma is Griffin: sliding-window attention plus
                 RG-LRU, so it has local attention and NO global attention.
                 -0.000498 -> -0.000114                 global removed
                                                        displacement DOWN

Read on the local/global axis rather than the presence/absence axis, **both contrasts point the same way**: global attention supports displacement, local attention does not, and removing local attention may even free capacity for it. `falcon-mamba-7b`, which has neither, sits low at -0.000124, and `rwkv-4-7b-pile`, which has neither, is the one non-displacer.

**This is post hoc on two contrasts of one model each, generated after seeing the signs, and it is not a finding.** Across vendors it already breaks: `gemma-2-9b` has full global attention and is the strongest displacer here at -0.000498, while `Olmo-3-1025-7B` also has full global attention and sits at -0.000159, so vendor and corpus swamp it the moment the comparison leaves a matched pair. It is recorded because it is cheap to state, it is falsifiable, and `rhyme_pull` across these same models would test it: if global attention is what carries the operation, the same ordering should appear on the paradigmatic instrument. **It has to be written down before that fleet runs or it is worthless.**

**Taken together these do not support an architecture effect in either direction.** Two same-lab, same-data contrasts with opposite signs, over one observation each, is what no effect plus lineage-level noise looks like. The defensible claim is the negative one: the operation is not confined to full attention, and the sign of the architecture difference is not stable across the two cases where the confounds are actually controlled.

## Limits, stated



- **n on the side that matters is one and one.** One pure SSM, one linear-attention-only model. `run.py` runs no between-group test and this README makes no distributional claim about architecture classes. These are positions in a distribution of 50.
- **Everywhere except contrasts 1 and 2, architecture is confounded with vendor, scale, vintage, and corpus.** That is why those two lead.
- **Alignment strength varies across the roster by a factor of four** and is not controlled here. The `sum|delta|` column is reported beside every slope for exactly this reason.
- **`norm_change` runs on 45 pairs, not existence's 50.** Its README (line 995) makes `--match-framed` non-optional, because raw at n=50 beside framed at n=45 differs partly by which labs ship a chat template. All 12 architecture models are in the 45, so nothing here is lost to it, but the two instruments are not quite the same population.
- **`rate_and_magnitude` writes no results file**, so `sum|delta|` is recomputed directly from `movement_v4` here rather than looked up.
- `rhyme_pull` would be the sharpest test of the Jakobson claim specifically, since it measures the paradigmatic axis directly rather than charge-selectivity. It is a pilot, not a producer, and was not run here.

## Running it



    python run.py > results.txt

Pure lookup and one query. No model loading, no GPU.
