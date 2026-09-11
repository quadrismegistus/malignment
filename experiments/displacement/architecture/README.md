---
subject: displacement
kind: question
status: "RUN 2026-09-11 as a metadata lookup over existence/results/selectivity.json plus a direct sum|delta| recompute. Architecture metadata is declared in run.py and sourced per model to roster/models/models.yaml (env.profile) and roster/models/attestations.json. NOT REGISTERED: n is one pure SSM and one linear-attention-only model, and no between-group test is run. norm_change is NOT covered, its CSVs are already aggregated over lineages."
question: Does displacement depend on the attention mechanism, or does it occur in models that compute attention differently or not at all?
headline: "The operation does not need attention. falcon-mamba-7b, which has none, displaces at -0.000124; recurrentgemma-9b, Griffin with local attention only, displaces at -0.000114. The two best-controlled contrasts DISAGREE in sign of difference: AI2's Olmo-Hybrid displaces MORE than its dense sibling (-0.000257 vs -0.000159), Google's recurrentgemma displaces LESS than its same-corpus sibling gemma-2-9b (-0.000114 vs -0.000498). The one non-displacer with an unusual architecture, rwkv-4-7b-pile (+0.000107), is confounded: it is also among the seven weakest movers overall (sum|delta| 552 against a roster median near 1,185)."
---

# architecture

**Does the operation need attention?**

Weatherby's *Language Machines* (2025) locates the poetic function in the transformer's attention mechanism: "the transformer architecture gives us quantitative aboutness" (161-62), and computation and language "share form" as "a demonstrable technical fact". The claim is architecture-specific by construction. He hedges it once, and the hedge is the testable part: attention is "probably just one way, we do not yet know of any others, to make this function computationally manipulable" (155), with a note pointing at Google's Griffin, "RNNs with local attention" (227n26).

That Griffin model is in this census. So is a model with no attention at all. If alignment's content-selective displacement occurs without attention, then the mechanism Weatherby names is not what makes the operation possible, and the transformer demonstrates nothing about language that autoregression had not already.

## Where the metadata comes from

`roster/models/models.yaml` has no architecture field, and it is AUTHORED (hand-edited, no script writes it), so this folder does not add one. What it does have is `env.profile: ssm`, an environment requirement (mamba-ssm and causal-conv1d kernels) carrying its own `why`, which picks out the SSM and hybrid families exactly. The rest comes from `roster/models/attestations.json`, whose `notes` carry sourced architecture prose at `confidence: high`.

`run.py` declares the architecture of every departure from the default and cites the source inline. **The default is a dense transformer with full attention.** Nothing is coded as unknown.

Two axes, because they cross:

    attn    full | full+linear | local+linear | full+ssm | linear | none
    block   dense | moe | ssm | hybrid

`recurrentgemma` is local attention AND linear recurrence; `Olmo-Hybrid` is full attention AND linear attention. A single axis would have to collapse them into the same cell.

## The result

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

    3  ONE VENDOR, THREE BLOCK TYPES (TII, all ~7B)
       falcon-7b          full          dense    -0.000266    1292
       Falcon3-7B-Base    full          dense    -0.000158    1109
       falcon-mamba-7b    none          ssm      -0.000124     948
       Falcon-H1-7B-Base  full+ssm      hybrid   -0.000048    1596

    4  DENSE vs MoE (AI2)
       Olmo-3-1025-7B     full          dense    -0.000159    2045
       OLMoE-1B-7B-0125   full          moe      -0.000388    1686

Contrast 1 is the best control in the roster and it is not ours. AI2 built Olmo Hybrid as a controlled experiment: "we train Olmo Hybrid, a 7B-parameter model largely comparable to Olmo 3 7B but with the sliding window layers replaced by Gated DeltaNet layers", demonstrating the benefit of hybrid models "in a controlled, large-scale setting" (arXiv:2604.03444, Merrill et al., 3 Apr 2026, quoted in `attestations.json`). Same lab, same three-stage pipeline, same data mix, 5.50T against 5.93T tokens. The declared architectural difference is the attention mechanism and nothing else. **Replacing attention layers with linear-attention layers made displacement stronger, not weaker.**

Contrast 2 is attested as sharing a corpus ("RecurrentGemma uses the same training data and data processing as used by the Gemma model family"; "The architecture is Griffin, not Gemma's transformer") and goes the other way by a factor of four.

**Taken together these do not support an architecture effect in either direction.** Two same-lab, same-data contrasts with opposite signs, over one observation each, is what no effect plus lineage-level noise looks like. The defensible claim is the negative one: the operation is not confined to full attention, and the sign of the architecture difference is not stable across the two cases where the confounds are actually controlled.

## Limits, stated

- **n on the side that matters is one and one.** One pure SSM, one linear-attention-only model. `run.py` runs no between-group test and this README makes no distributional claim about architecture classes. These are positions in a distribution of 50.
- **Everywhere except contrasts 1 and 2, architecture is confounded with vendor, scale, vintage, and corpus.** That is why those two lead.
- **Alignment strength varies across the roster by a factor of four** and is not controlled here. The `sum|delta|` column is reported beside every slope for exactly this reason.
- **`norm_change` is not covered.** Its CSVs (`dose,table,lang,target,med_slope,up,dn,n,p`) are already aggregated over lineages, so stratifying it by architecture requires its producer to emit a per-lineage column. Not done.
- **`rate_and_magnitude` writes no results file**, so `sum|delta|` is recomputed directly from `movement_v4` here rather than looked up.
- `rhyme_pull` would be the sharpest test of the Jakobson claim specifically, since it measures the paradigmatic axis directly rather than charge-selectivity. It is a pilot, not a producer, and was not run here.

## Running it

    python run.py > results.txt

Pure lookup and one query. No model loading, no GPU.
