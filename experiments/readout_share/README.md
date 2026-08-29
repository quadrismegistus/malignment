---
id: readout_share
question: When alignment displaces a distribution, does it change the representation the model arrives at or the readout that turns it into words?
status: RUN 2026-08-29 — the state carries it; Llama-3.1-8B is the lone counter-case at 88-91% readout, replicated in two dose bands
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

**Alignment predominantly changes the state, not the readout — and one model in five does the opposite.**

The effect lives entirely in the charged frames, so the bands are the result and the pooled row is context:

```
                      dose 1-2        dose 2-3        dose 3-4        dose 4-7
                       n=28            n=12            n=14            n=5
gemma-2-9b           -0.01           -0.03           -0.01     --   -0.25  -14%
recurrentgemma-9b    -0.04           -0.03           -0.41    14%   -1.56   16%
CT-LLM-Base          -0.09           -0.09           -0.64    12%   -0.36   33%
Llama-3.1-8B         -0.04           -0.13           -0.34    88%   -0.42   91%
Falcon3-7B-Base      +0.01           +0.04           +0.27     --   +0.21    --
```

Below dose 3 nothing moves in any pair (-0.01 to -0.13 across 40 of the 59 prompts). Above it the effect appears and the shares become readable, and **the readout share is stable across the two charged bands within each pair** — Llama 88% then 91%, recurrentgemma 14% then 16%, on disjoint prompt sets. That is an internal replication of the split, which the earlier six-prompt run could not offer.

Pooled over all 59 prompts, the three pairs clearing both gates give:

```
                       cov      dW     full   readout        state       onset
recurrentgemma-9b     0.97   0.030   -0.255   -0.045  18%   -0.138  54%   1.00
CT-LLM-Base           0.90   0.037   -0.244   -0.055  23%   -0.184  75%   1.00
Llama-3.1-8B          0.65   0.063   -0.162   -0.160  99%   -0.035  22%   1.00

pooled 39% readout / 54% state; median per pair 23% / 54%
```

**Llama-3.1-8B is the lone counter-case**, and it is not a coverage artefact: its two unembeddings differ by 6.3%, less than gemma's 11.0%, and its 88%/91% holds in both charged bands.

**The final normalisation contributes nothing anywhere.** `norm_only` is +0.000 summed across the qualifying pairs, and `unembed_only` reproduces the full readout swap to the third decimal in every case. Where the readout carries anything it is the unembedding matrix.

## The depth result, and F05

**Alignment is a final-layers operation in every pair.** Onset, F05's shape — the first layer at which the gap holds its final sign and reaches half its final magnitude — with a coverage floor of 0.20:

```
gemma 0.83 | recurrentgemma 1.00 | CT-LLM 1.00
Llama 1.00 | Falcon3 1.00 | glm 1.00

F05: SFT 0.92, DPO 0.96, RLVR 0.98
```

**This is a replication of F05 on targets it did not use.** F05's revision (2026-07-01, 405,248 rows, 40 families) selected targets as data-driven movers — words chosen because they moved, which conditions on the outcome. `task_charge`'s ratings are blind to both arms. The onset comes out the same.

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

**A2, 2026-08-29.** The first full run used the six highest-dose prompts per pair and reported five qualifying pairs at 25% readout pooled. Expanding to all 59 rated prompts drops that to three qualifying pairs at 39% pooled. **Neither number was wrong and neither is the finding** — the per-pair shares are stable (Llama 88 to 99, recurrentgemma 17 to 18, CT-LLM 12 to 23) and what changed is how much uncharged material is averaged in. The band grain was added in response and supersedes both pooled figures. A top-N-by-dose selection is also a selection into the saturated region, so `--top` is now a dose-stratified draw.
