---
id: readout_share
question: When alignment displaces a distribution, does it change the representation the model arrives at or the readout that turns it into words?
status: RUN 2026-08-30 — readout and state contribute COMPARABLY (joint regression 0.59 vs 0.65, R2 0.75; 0.74 vs 0.77, R2 0.98 on clean pairs). The earlier "Llama is the lone readout counter-case" is WITHDRAWN — see A5.
opened: 2026-08-29
---

# Readout share

**The question.** A transformer's last operation is a readout: a final normalisation and an unembedding matrix that turn the residual stream into a distribution over the vocabulary. Alignment could displace a charged distribution by changing the state that arrives at that readout, or by changing the readout itself. These are separable, and nothing in the campaign had separated them.

They are separable because the two arms of a pair share a tokenizer and a hidden size, so a base model's residual stream can be pushed through its aligned sibling's readout and vice versa. Four combinations, at every layer:

```
h_base    x readout_base       the base model
h_base    x readout_aligned    base state, aligned readout
h_aligned x readout_base       aligned state, base readout
h_aligned x readout_aligned    the aligned model
```

## The measure

`task_charge` rates every candidate word in a completed scene 1-7 (sha `78d73c40f097761f`). For a set of rated words with masses `p_w` at some layer,

    T = sum(scene_w * p_w) / sum(p_w)

**Normalising by the covered mass is what makes this comparable across a swap.** An unnormalised sum falls whenever the distribution concentrates anywhere else, so it would read every sharpening as displacement. `T` is the mean transgressiveness of what the model is reaching for, conditional on it reaching for one of the rated words at all.

The full alignment effect is `T(h_a, W_a) - T(h_b, W_b)`; negative means the aligned arm is less transgressive. The readout swap is `T(h_b, W_a) - T(h_b, W_b)`, the state swap is `T(h_a, W_b) - T(h_b, W_b)`, and their shares are each divided by the full effect.

**The two shares do not sum to 100% and are not meant to.** This is not a decomposition — `T` is not additive over the two substitutions, and the numbers below show the interaction directly: gemma-2-9b's state swap is -0.126 against a full effect of -0.036, while its readout swap runs the *other way* at +0.051. Swapping both is not swapping each in turn.

`readout` is the final norm and the unembedding together. They are also swapped separately, as `unembed_only` and `norm_only`, so the matrix's contribution can be told apart from the normalisation's.

## Population

16 pairs have residual streams archived on both arms. Seven survive to a readable result; the exclusions are in `population.json` with a reason each.

| excluded | why | n |
|---|---|---|
| `bloom-7b1`, `Falcon-H1-7B-Base` | the two arms' sidecars hold different prompt lists | 2 |
| `deepseek-llm-7b-base`, `MiniCPM5-1B-Base` | the aligned arm is not in the local model cache | 2 |
| `RedPajama-INCITE-Base-7B` | no recognised unembedding tensor name | 1 |
| `llm-jp-3-7.2b`, `neo_7b` | fewer than 8 single-token rated words per cell | 2 |
| `granite-3.0-8b-base`, `falcon-mamba-7b` | final-layer coverage 0.10 and 0.00 | 2 |

**Every rated prompt in each sidecar, not a top-N by dose.** The sidecars hold 115 prompts, 59 of which carry `task_charge` ratings; all 59 are used. 13 of the 16 sidecars hold the same 115 prompts, so the pairs are read on a common set (Croissant's holds 60, bloom's 62, Falcon-H1's 33).

**AND THE POOLED FIGURE IS MOSTLY ABOUT UNCHARGED PROMPTS.** The median dose over the 59 is 2.11 and only 5 sit above 4.0. Pooling charged with uncharged shrinks every pair's effect three- to fivefold and drops five of seven below the gates: `recurrentgemma-9b` goes from -1.32 on the top-6 to -0.255 pooled. That is dilution, not disagreement, and it is why `results/by_pair_band.csv` is the grain to read.

Single-token vocabulary only. Receipts in `population.json`, including the charge file's sha (`dd981d8b0843fd6b`), the instrument sha, and the archive manifest's.

## Claim

**The readout and the state contribute comparably, and neither dominates. The split varies continuously across lineages rather than separating one counter-case from a rule.**

The estimator is a regression across pairs, not a per-pair ratio. A ratio needs every pair to clear a floor on its own denominator, which excluded 24 of 32 pairs; a slope needs none of them to.

```
                              readout    state      R2     n
full ~ readout                 +0.011              0.000   25
full ~ state                              +0.321   0.361   25
full ~ readout + state         +0.592    +0.653    0.747   25

dropping the 3 most extreme readout terms
full ~ readout + state         +0.809    +0.670    0.849   22

pairs where both terms share the sign of the effect
full ~ readout + state         +0.744    +0.770    0.980    9
```

**THE SIMPLE REGRESSIONS ARE SUPPRESSED AND MUST NOT BE QUOTED.** `corr(readout swap, state swap) = -0.706`: a pair with a large readout swap tends to have a state swap pushing back, so each term's relationship to the effect is masked when the other is omitted. Read alone, the readout looks inert (slope +0.011, R2 0.000); held against the state it carries a coefficient of the same size as the state's. Across all three specifications the pair is 0.59/0.65, 0.81/0.67, 0.74/0.77.

**And a per-pair share is only a quantity where the two terms agree in sign.** In 15 of 25 pairs they oppose and partly cancel, which is what produced shares of 509%, 470% and 293% — a large readout term offset by a large opposite state term, divided by whatever survived. Restricted to the 9 pairs where both push the same way:

```
llama-7b              full -0.073   readout -0.077  106%   state -0.025
kanana-2-3b-base      full -0.153   readout -0.135   88%   state -0.028
neo_7b                full -0.192   readout -0.148   77%   state -0.098
deepseek-llm-7b-base  full -0.046   readout -0.034   74%   state -0.012
Llama-3.1-8B          full -0.392   readout -0.281   72%   state -0.165
kanana-1.5-8b-base    full -0.522   readout -0.264   51%   state -0.424
CT-LLM-Base           full -0.142   readout -0.050   35%   state -0.086
Lucie-7B              full -0.251   readout -0.033   13%   state -0.225
TinyLlama-1.1B        full -0.083   readout -0.000    0%   state -0.078
```

A continuum from 0% to 106%, with **Llama fifth of nine at 72%**. Its readout swap in absolute terms is -0.281, **z = -0.71** against a mean of -0.091 and sd 0.268 — fifth of 25, exceeded by Olmo-Hybrid-7B (-0.661) and MiniCPM5-1B (-0.373). Nothing about it is unusual in size; its high ratio came from a moderate denominator.

**The final normalisation still contributes nothing anywhere.** `unembed_only` reproduces the readout swap to the third decimal in every pair.

## Is the decomposition well-posed? Yes.

A 2x2 swap gives four corners of a surface and cannot say whether the surface is flat, so the readout/state split had two readings a swap cannot separate: two distinct changes that compensate, or ONE change to the composed map projected onto two non-orthogonal axes, which would manufacture the -0.706 anti-correlation as an artifact. `run.py --interpolate` grids `T(h_b + a(h_a - h_b), W_b + b(W_a - W_b))` over a=b=0,0.25,0.5,0.75,1.

**The surface is planar.** Median R2 fitting `T ~ a + b*alpha + c*beta` is **0.984**; adding `d*alpha*beta` buys **0.006**.

```
pair                 state only   readout      sum     joint   sub-additive
Llama-3.1-8B             -0.165    -0.281   -0.446    -0.392        12%
kanana-1.5-8b-base       -0.424    -0.264   -0.688    -0.522        24%
Lucie-7B                 -0.225    -0.033   -0.258    -0.251         3%
gemma-2-9b               -0.376    +0.060   -0.316    -0.229        28%
neo_7b                   -0.098    -0.148   -0.247    -0.192        22%
CT-LLM-Base              -0.086    -0.050   -0.136    -0.142        -4%

median state -0.195, readout -0.099, ratio 2.0:1
```

So the axes ARE separable and the question has an answer per lineage. Within a pair the two changes are near-additive and mildly **redundant** — doing both achieves ~20% less than the sum, because they partly accomplish the same thing. That is overlap, not opposition, and it is a different phenomenon from the -0.706 anti-correlation, which is **across** lineages: different training runs allocate the work differently. Reading the between-pair fact as a within-pair mechanism was an error.

**gemma-2-9b is the sharp case**: its readout swap is **+0.060**. Its aligned unembedding, applied to its own base state, makes the distribution *more* transgressive. All its displacement is in the state, with the readout pulling against it.

## Is the metonymic slide state-carried or readout-carried? BOTH.

malign [6568] measured, at the output, that when a transgressive word loses mass the freed mass lands preferentially on SAME-KIND words (VIOLENT->VIOLENT, SEXUAL->SEXUAL) rather than on neutral ones: 47 of 49 lineages, same-kind risers gaining 40% more than NONE risers (+0.0133 vs +0.0095) and carrying intermediate charge (scene 3.36 vs 2.23). That is the metonymic slide with the control it always lacked.

The output composes state and readout. Running the same statistic under each swap separately, over lift-selected prompts (`frame < 5`, `lift > 0.3`) and cells with 12+ single-token rated words:

```
contrast    same-kind        NONE    ratio    n cells    pairs with ratio > 1
full         +0.01265    +0.01000    1.26x       1991    20 of 24, median 1.20x
state        +0.01799    +0.01456    1.24x       1703    18 of 24, median 1.27x
readout      +0.00585    +0.00400    1.46x       1757    18 of 23, median 1.41x
```

**The same-kind preference is present in BOTH components, and marginally stronger in the readout.** The slide is not constituted upstream and then merely rendered — the unembedding has its own within-kind preference.

**This is where the readout's small share becomes load-bearing.** It carries ~10% of the MAGNITUDE of displacement and as much of the STRUCTURE of the slide as the state does. A component can be a tenth of the effect and a full participant in its shape, and a decomposition that reports only magnitude will miss that.

Two restraints on how far it goes. The effect here is **weaker than malign's** — 20/24 at 1.26x against their 47/49 at 1.40x — because this measures single-token rated words at the final layer where they measure the movement store's full word set; a weaker instrument on a subset, not a replication. And the readout's higher ratio sits on **smaller absolute gains** (+0.00585 against +0.01799), so it is a ratio over a third of the mass, which is the shape that broke the per-pair shares in A5.

## What this says about "superficial" and "downstream"

**Against Weatherby's "downstream," on the literal reading.** RLHF "is downstream from the core model" (*Language Machines* p. 150) is a pipeline metaphor, and taken literally it predicts a transformation applied to the output of an unchanged core — a readout change with the representation intact. The median allocation is **2:1 toward the state**, on a surface flat enough (R2 0.984) that the decomposition is not too blurry to read. It does not touch his premise, which is true: GPT-2 had competence before RLHF. It complicates the inference from that premise to treating alignment as posterior.

**H2 is the stronger evidence and this is corroborative**, from an instrument that can see what patching cannot: patching holds the readout at base by construction, so it can show alignment reaches deep but never that the readout is not where the rest lives.

**Against LIMA, weakly, and it should not be leaned on.** The Superficial Alignment Hypothesis is about knowledge and capabilities versus "which subdistribution of formats" (Zhou et al., p. 2). A readout-localised effect would have looked like format; a state change is harder to call format. But "the final-layer residual differs" is not "knowledge and capabilities differ," and `west-base-beat-aligned`, `lin-urial-unlocking-spell` and `raghavendra-revisiting-superficial` are better aimed at that claim.

**Worth recording: the withdrawn headline supported both.** 90% readout, a 6% perturbation of the final matrix, the thought untouched, is exactly what Weatherby and LIMA predict. The error ran against this paper's thesis, and it still took prompting to break.

## The H2 join: two instruments, one counterfactual

H2's `ceiling` is recovery with ALL blocks aligned and the head held at base — structurally the same counterfactual as this experiment's state swap, reached by patching weights rather than by reading a stored state. Its metric is not `T`:

    den = {i: la[i] - lb[i]}            over tokens where |la - lb| > 1e-3
    rec(lp) = median_i (lp[i] - lb[i]) / den[i]

the median per-token fraction of the base->aligned LOG-PROB gap a hybrid reproduces. `readout_share` recomputes exactly that on its four combinations, joined to H2 on `(pair, prompt)` — the frozen 611 includes H2's 231 for this reason. **3,627 cells, 17 pairs, 214 shared prompts.**

```
final-OOD cut   cells   state rec   readout rec     sum   sp(ceiling, state)
none             3627       0.901         0.105   0.995               +0.285
< 3.0            3163       0.897         0.100   0.993               +0.296
< 2.0            2726       0.892         0.100   0.993               +0.303
< 1.5            2180       0.895         0.096   0.995               +0.291
```

**THE DECOMPOSITION CLOSES.** State + readout = **0.99 of the log-prob gap**, unmoved by the denominator threshold (67-100% of tokens kept) or by gating on the cross-read. At the output, alignment is exhaustively a change to what arrives plus a change to what renders it, with no residual and no interaction worth naming. The state carries **~0.90**, the readout **~0.10**.

**AND TWO INSTRUMENTS AGREE ON THE SAME COUNTERFACTUAL.** `sp(ceiling, state recovery) = +0.29-0.30` per cell, and the per-pair medians match: CT-LLM 0.886/0.887, Mistral 0.906/0.900, TinyLlama 0.917/0.905, Lucie 0.976/0.926, Llama 0.845/0.764. Different repos, different machinery, same number. Nothing in the campaign had a cross-instrument check for this.

**The per-pair readout share is NOT recoverable from this design.** It runs -14.7 (Amber) to +1.33 (Yi) across 16 pairs; the extremes are ratio artifacts, and `|readout recovery|` correlates +0.297 with H2's final-layer cross-read OOD — the term explodes exactly where the cross-read is not interpretable. Gating on final-layer OOD does not rescue Amber, because H1's gate is per-layer worst-case and Amber fails that. The pooled cell-level median is the estimator that survives.

**A withdrawal.** An earlier version of this section reported `sp(ceiling, readout) = -0.354` on 5 pairs as support for "the readout carries what patching cannot recover." On 17 pairs it is **-0.08**. That is the third time a 5-to-15-point correlation from this directory has collapsed under power, and it should be read as the standing caution rather than a fresh discovery each time.

## Does alignment change what the model understands? No.

The state carrying ~0.90 licenses "the aligned model arrives somewhere different" and NOT "the aligned model understands the scene differently" — the last-layer final-position state is saturated with next-token information, so the change may be wholly one of disposition.

A 7-way linear probe on `frame_kind` (SEXUAL / VIOLENT / COERCIVE / DEGRADING / ILLICIT / OTHER / NONE), trained on **base** states and tested on the **aligned** states of held-out prompts:

```
pair              base CV    base -> aligned    chance     n
Llama-3.1-8B        0.670              0.632     0.245   552
Mistral-7B-v0.1     0.637              0.633     0.243   507
CT-LLM-Base         0.594              0.579     0.250   539
Lucie-7B            0.602              0.525     0.256   472
gemma-2-9b          0.671              0.607     0.252   532
```

**Content transfers.** The same linear directions read the aligned state as well as the base state — Mistral 0.633 against 0.637. Alignment does not degrade the representation of what kind of scene it is.

Causally, decomposing `d = h_a - h_b` onto the content subspace, onto the span of the rated words' own unembedding rows, and the remainder, then feeding `h_b + d_x` back through the base readout:

```
pair               n   full dT   content   readout     rest   dim c   dim w
Llama-3.1-8B      66    -0.052     0.082     0.999   -0.123       7      74
Mistral-7B-v0.1   67    -0.051     0.027     0.750    0.073       7      68
CT-LLM-Base       66    +0.066     0.086     1.030   -0.067       7      66
Lucie-7B          58    -0.110     0.063     0.979   -0.136       7      56
gemma-2-9b        86    -0.123     0.136     1.002   -0.000       7      79
```

**The readout column is close to TAUTOLOGICAL and must not be quoted as a finding.** `d_rest` is orthogonal to every `W[w]` for the rated words, so by construction it cannot move their logits except through the softmax denominator and the RMSNorm nonlinearity. The ~1.0 says only that those indirect channels contribute nothing.

**And the content column does not survive its null.** Against a random subspace of equal rank on the same cells, content gives **-0.034** where random gives **-0.001**, and two subsamples disagree in sign (+0.082 at n=66, -0.034 at n=22). No detectable contribution.

What is solid: the delta is **enriched in content directions without acting through them** — 4.25% of `||d||^2` in a 7-of-4096-dimensional subspace against 0.17% expected at random, a 25x enrichment causing nothing measurable. Alignment moves the state along content-carrying directions, content stays readable, and the displacement comes from elsewhere.

## Population and selection

Prompts are selected on **lift, not dose**: `frame < 5 AND lift > 0.5`, where `lift = dose - frame`, 102 of the frozen 611. Exposed as `charge.lift()`.

**Dose is close to useless as a selector and the frame is why.** `corr(effect, dose) = -0.091` against `corr(effect, lift) = -0.261`, and `-0.311` inside the unsaturated range. **Lift is not headroom**: `corr(lift, 7 - dose) = -0.004` and `corr(effect, 7 - dose) = +0.091`, so distance from the ceiling is a different quantity and an uninformative one. A frame already rated 6.4 has candidate words no more transgressive than the setup: headroom runs +0.38 at frame 2-3 down to **-0.05** at frame 6-7, so the highest-dosed prompts have nowhere to displace to. Effect peaks at frames 2-4 and falls away above 5 while dose climbs monotonically, which is why a linear fit across the whole range returns nothing.

Simulated over the existing run, selection rules give:

| rule | prompts | cov>0.30 | readable | median effect |
|---|---|---|---|---|
| all 611 | 593 | 21 | 1 | -0.025 |
| dose >= 4 (what was frozen on) | 181 | 19 | 1 | -0.022 |
| headroom > 0.3 | 197 | 21 | 6 | -0.052 |
| frame<5 and headroom>0.5 | 102 | 25 | 8 | -0.085 |

## What this rebuilt, and what it is not in competition with

**`twp_head_swap.py` already existed.** `malign-logits/scripts/twp_head_swap.py` runs the same four combinations — `S_b H_b`, `S_a H_a`, `S_a H_b`, `S_b H_a` — and was built at this seat's prompting (docket [5222].2). It measured `||dW_U||/||W_U|| = 6.56e-02` for Llama; this run independently gets 6.3e-02. **This directory did not search for it before rebuilding it**, which is recorded in A3 rather than quietly fixed.

It also carries a gate this run did not originally implement. From H1: *"Where a head swap is used, it is only interpretable if the cross-read stays in distribution. Llama passes; Amber fails — its cross-read is 5x sharper than the true one."* That gate is now `lens.Readout.shape_at` and every pair passes it (perplexity ratios 0.57–1.84 against 5x for exclusion; Llama 1.12/0.97, among the closest to identical shape). The negative control matters as much as the result: it catches the input-embedding readout (15.13 bits against a native 5.01) and **passes a row-permuted unembedding with a ratio of exactly 1.00**, because entropy is permutation-invariant. It certifies shape, not meaning.

**H1/H2 are not a rival result to this one, and I first reported them as if they were.** The patch holds the head, embeddings and final norm at base throughout — `twp_patch_weights.py`: *"THE HEAD AND EMBEDDINGS ARE HELD AT BASE THROUGHOUT"*; `twp_patch_depth.py`: *"the readout is held fixed by construction"*. **It cannot attribute anything to the readout.** Its "alignment is distributed through the stack, not concentrated at the readout" is a statement about where block effects sit, with the readout's contribution structurally excluded. The two instruments answer different questions.

They also ran on **disjoint prompt sets**: H2's battery is 231 matched minimal pairs ("squeezed the rabbit in her grip" against "cradled"), this directory's sidecars are the `f11_` contradiction set. Zero overlap. So the apparent disagreement was an instrument blind to the readout, on different material.

**The joinable prediction.** H1's patch recovers 6–16% from the last two blocks and 55–73% from everything below, leaving 11–39% unrecovered — and the readout is exactly what patching can never recover. If readout share is real it should predict per-pair patch under-recovery. Same pairs, two instruments, one falsifiable link. Not yet run; it needs this experiment on H2's prompts, which is what the frozen 611 is for.

## The depth result, and F05

**Alignment is a final-layers operation in every pair.** Onset, F05's shape — the first layer at which the gap holds its final sign and reaches half its final magnitude — with a coverage floor of 0.20:

```
gemma 0.83 | recurrentgemma 1.00 | CT-LLM 1.00
Llama 1.00 | Falcon3 1.00 | glm 1.00

F05: SFT 0.92, DPO 0.96, RLVR 0.98
```

**This is a replication of F05 on targets it did not use.** F05's revision (2026-07-01, 405,248 rows, 40 families) selected targets as data-driven movers — words chosen because they moved, which conditions on the outcome. `task_charge`'s ratings are blind to both arms. The onset comes out the same.

**But F05 is itself corrected by H2**, and an earlier version of this README reported replicating it without saying so. H2 (23 pairs, 231 prompts) finds half the representational change accrued by ~60% of depth, `repr_L50/N` median 0.594, with only 21% of cells accruing in the last quarter — Llama at 0.625. That is a causal measure over blocks; the onset here is an observational measure of when the output distribution over rated words separates. Both can hold: a representation shifting gradually up the stack whose readable output difference nonetheless lands late. **Where the two are read as one claim, the causal one governs.**

**And the depth axis is orthogonal to the share axis.** Llama (99% readout) and recurrentgemma (18%) both onset at 1.00; gemma (-14%) at 0.83, the earliest. Same timing, different substrate — late-and-readout and late-and-state are both available, at the same depth. F05 established when; this establishes that "when" does not determine "what on".

## The coverage floor is not a detail

**Below three-quarters of the stack the lens puts essentially no mass on the rated words, in every model.**

```
                       0.00    0.25    0.50    0.75    0.88    0.94    1.00
gemma-2-9b            0.009   0.015   0.060   0.540   0.704   0.742   0.797
recurrentgemma-9b     0.000   0.000   0.000   0.000   0.000   0.000   0.720
CT-LLM-Base           0.004   0.046   0.053   0.716   0.692   0.685   0.866
Llama-3.1-8B          0.002   0.001   0.010   0.212   0.224   0.260   0.662
Falcon3-7B-Base       0.001   0.005   0.003   0.052   0.362   0.718   0.605
glm-4-9b-hf           0.001   0.001   0.003   0.139   0.082   0.060   0.556
```

`recurrentgemma-9b` is exactly 0.000 until the final layer. A `T` computed there is a ratio of two vanishing numbers, and an onset statistic will happily cross its threshold on it. Without the floor:

```
                     floor 0    0.05    0.10    0.20
Llama-3.1-8B            0.22    0.97    0.97    1.00
glm-4-9b-hf             0.06    0.80    0.97    1.00
Falcon3-7B-Base         0.54    1.00    1.00    1.00
gemma-2-9b              0.43    0.71    0.79    0.83
```

**Llama moves from 0.22 to 1.00.** An unfloored run of this instrument reports that alignment begins a fifth of the way up the stack and contradicts F05; the disagreement is entirely the missing floor. This is why `layer_probs` returns the full probability vector rather than a scalar — the caller can compute coverage at every depth and is not able to avoid seeing it.

## What this is not

**Not a mechanism.** "The state carries it" says the residual stream arriving at the last layers already differs; it says nothing about which earlier component changed it. The sidecars hold the final position only, so nothing here can attribute the state change to attention, MLP, or a particular layer's output.

**Not first-token-only by choice.** The sidecars are the final position of the prompt, so the lens gives `p_L(first token | prompt)`. Multi-token words need a forward pass per continuation token. On Llama-3.1-8B, single-token words are 87% of rated words and 87% of base mass; on the low-coverage pairs that share is much worse, which is what `coverage` records.

**Not powered.** 59 prompts per pair, of which 19 carry dose above 3, on three pairs clearing both gates. The within-pair band replication is the strongest thing here; three pairs is not a population.

**Not free of the tokenizer.** A word enters `T` only where that model spells it as one token after that prompt, and **words a tokenizer splits average 0.47–0.82 higher on scene** — the exclusion selects against the marked tail. Within a pair it cancels (both arms share a tokenizer). Across pairs it does not, so the cross-model ranking was rerun on a **common vocabulary**: 3,576 word-cells single-token in all seven tokenizers, 59 shared prompts.

| pair | per-model vocab | common vocab |
|---|---|---|
| Llama-3.1-8B | 99% | **89%** |
| recurrentgemma-9b | 18% | **29%** |
| CT-LLM-Base | 23% | **23%** |

The ordering survives; Llama stays three-to-one clear. The common set equalises the bias rather than removing it — `strangle` is dropped for everyone — and only the chain rule recovers those words.

**Not a claim that Llama is unusual as a model.** It is the counter-case *in this measure on these prompts*. The archive is 16 pairs of the roster's ~50, selected by whichever v2 run happened to write sidecars.

## Reproducing

```
.venv/bin/python -u run.py                       every archived pair, every rated prompt
.venv/bin/python -u run.py --device mps --verify-device      ~2.7x, checked against CPU
.venv/bin/python -u run.py --top 12               a DOSE-STRATIFIED draw, not a head
.venv/bin/python -u run.py --floor 0.0           reproduce the unfloored onsets above
```

`--device mps` is opt-in and `--verify-device` recomputes the first cell of every pair on CPU before trusting it; agreement across all pairs was 0 to 1.4e-06. The default is CPU because it is already ~1 min/pair.

Ratings come from `malignment/charge.py`, not from this directory; the run cross-checks its own tensor `T` against `charge.T` on the first cell of every pair and raises above 1e-4. Reads the `.f32` sidecars under `$MALIGNMENT_HIDDEN` (default: the read-only `malign-logits` archive). Models are never loaded — safetensors memory-maps, so pulling an unembedding out of a 37GB checkout is a partial read. Lens machinery is `malignment/lens.py`.

## Amendments

**A1, 2026-08-29.** The first version of this measurement ran on Llama-3.1-8B alone and reported 90% readout as the result. That is the outlier. Recorded here because the direction of the correction matters: a single pair gave a clean, theoretically attractive answer — repression at the point of utterance, the state untouched — and the population reversed it. The attractive reading survives for exactly one model.

**A3, 2026-08-29.** This instrument was rebuilt without searching for `twp_head_swap.py`, which already implemented it, and it was reported for two turns without H1's cross-read-in-distribution gate. The gate, once implemented, passes for every pair — so nothing here is retracted for it — but the sequence is the finding: an instrument re-derived from scratch reproduced a prior figure to within 4% (`dW` 6.3e-02 against 6.56e-02) and neither the agreement nor the prior work was noticed until asked. `CAMPAIGN.md`'s method ledger exists for this.

**A6, 2026-08-30.** *"The metonymic slide is constituted in the state, with the readout merely rendering it"* — proposed here, tested here, refuted here. The same-kind landing statistic is 1.24x under the state swap and 1.46x under the readout swap. Recorded because it is the first check this directory designed in order to CONFIRM something rather than to break something, and it broke it anyway; the seven before it were all prompted by RH.

**A5, 2026-08-30. THE HEADLINE IS WITHDRAWN.** Every previous version of this document said the state carries displacement and Llama-3.1-8B is a lone counter-case at 86-99% readout. Three compounding errors:

- **The estimator.** A per-pair ratio, `readout / full`, on 15 of 25 pairs where the two terms have opposite signs and partly cancel. That is not a decomposition of anything, and it produced shares of 509%, 470% and 293% which read as findings.
- **The comparison.** Llama's readout term is ordinary in absolute size, z = -0.71, fifth of 25. Its high ratio was a moderate denominator, not a large numerator.
- **The prompts.** The f11 contradiction set that gave 88-99% is one narrow population; on headroom-selected prompts Llama is 72% and fifth of nine.

RH caught the first two by asking whether the readout term was an absolute outlier or a small denominator. **The correction runs the same direction as my three previous ones on this question, which is the pattern worth recording**: each time the error inflated a clean, theoretically attractive result — repression at the point of utterance, the state untouched — and each check that broke it had to be prompted.

**A4, 2026-08-30.** Run on the frozen 611 (40 pairs, `--store live`). **Llama replicates at 86% readout in the dose 3-4 band, n=154, coverage 0.65** — a different prompt population from the f11 set that gave 88-99%, so the counter-case is not a property of contradiction stems. `m-a-p/neo_7b`, measurable for the first time after the in-context tokenisation fix, is second at 58%; `kanana-1.5-8b-base` gives 49% and 36%.

**But the frozen list is a worse instrument than the borrowed one, and that is my error.** It was designed for dose spread and category balance and never checked for effect size. Of 32 pairs run: 11 fail coverage, 20 have too small an effect to apportion, 1 clears both pooled. Median full effect over the 21 coverage-passing pairs is **-0.027** (16 of 21 negative — direction right almost everywhere, magnitude tiny), against -1.32 for the best f11 pair. The f11 contradiction stems constrain the continuation hard, so mass concentrates on a few charged verbs; the 611 are longer and more specific and the distributions are diffuse. The list fixed what it was built to fix — one shared population across pairs, category coverage, llm-jp and neo_7b measurable at all — and cost the thing I did not think to preserve.

**The results in `results/` predate the corrected share gate.** `BAAI/Aquila2-7B`'s band row shows a readout share of **-410%**: it clears `MIN_FULL` at -0.180, but its readout swap runs *against* its full effect, and a magnitude floor on a denominator says nothing about whether the numerator belongs to the same phenomenon. The gate now requires sign agreement per component. That row is not a quantity and should be read as `--`; the underlying components in the CSV are unaffected.

**A2, 2026-08-29.** The first full run used the six highest-dose prompts per pair and reported five qualifying pairs at 25% readout pooled. Expanding to all 59 rated prompts drops that to three qualifying pairs at 39% pooled. **Neither number was wrong and neither is the finding** — the per-pair shares are stable (Llama 88 to 99, recurrentgemma 17 to 18, CT-LLM 12 to 23) and what changed is how much uncharged material is averaged in. The band grain was added in response and supersedes both pooled figures. A top-N-by-dose selection is also a selection into the saturated region, so `--top` is now a dose-stratified draw.
