---
id: readout_share
question: When alignment displaces a distribution, does it change the representation the model arrives at or the readout that turns it into words?
status: RUN 2026-08-29 — the state carries it, 81% pooled; Llama-3.1-8B is the lone counter-case at 88% readout
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

**The two shares do not sum to 100% and are not meant to.** This is not a decomposition — `T` is not additive over the two substitutions, and the numbers below show the interaction directly: gemma-2-9b's state swap is 216% of its full effect while its readout swap is *negative*. Swapping both is not swapping each in turn.

`readout` is the final norm and the unembedding together. They are also swapped separately, as `unembed_only` and `norm_only`, so the matrix's contribution can be told apart from the normalisation's.

## Population

16 pairs have residual streams archived on both arms. Seven survive to a readable result; the exclusions are in `population.json` with a reason each.

| excluded | why | n |
|---|---|---|
| `bloom-7b1`, `Falcon-H1-7B-Base` | the two arms' sidecars hold different prompt lists | 2 |
| `deepseek-llm-7b-base`, `MiniCPM5-1B-Base` | the aligned arm is not in the local model cache | 2 |
| `RedPajama-INCITE-Base-7B` | no recognised unembedding tensor name | 1 |
| `llm-jp-3-7.2b`, `neo_7b` | fewer than 8 single-token rated words per cell | 2 |
| `granite-3.0-8b-base`, `falcon-mamba-7b` | final-layer coverage 0.11 and 0.00 | 2 |

Of the seven readable, **five have displacement to apportion** — a full effect of at least -0.15. `Falcon3-7B-Base` (+0.320) and `glm-4-9b-hf` (-0.033) do not, and a share is not computed for them: glm's readout swap divided by its full effect is 1086%, which is arithmetically correct and not a fact about the model.

Six prompts per pair, the highest-dose in the sidecar; 230 distinct rated words; single-token vocabulary only. Receipts in `population.json`, including the charge file's sha and the archive manifest's.

## Claim

**Alignment predominantly changes the state, not the readout — and one model in five does the opposite.**

```
                       cov      dW     full   readout        state       onset
CroissantLLMBase      0.38   0.018   -0.230   -0.036  16%   -0.198  86%   0.96
gemma-2-9b            0.84   0.110   -0.238   +0.026 -11%   -0.515 216%   0.76
recurrentgemma-9b     1.00   0.030   -1.320   -0.220  17%   -0.920  70%   1.00
CT-LLM-Base           0.92   0.037   -0.525   -0.064  12%   -0.457  87%   0.97
Llama-3.1-8B          0.77   0.063   -0.455   -0.401  88%   -0.156  34%   0.92

pooled (weighted by effect)          -0.695  25%   -2.246  81%
median per pair                              16%           86%
```

Four of the five sit at 17% readout or below, one of them negative. **Llama-3.1-8B at 88% is the lone counter-case**, and it is a real one, not a coverage artefact: its final-layer coverage is 0.77 and its two unembeddings differ by 6.3%, less than gemma's 11.0%.

**The final normalisation contributes nothing anywhere.** `norm_only` is +0.008 summed across five pairs, and `unembed_only` reproduces the full readout swap to the third decimal in every case. Where the readout carries anything it is the unembedding matrix, and the matrices are barely perturbed: `mean|W_a - W_b| / mean|W_b|` runs 1.8% to 13.3%.

## The depth result, and F05

**Alignment is a final-layers operation in every pair.** Onset, F05's shape — the first layer at which the gap holds its final sign and reaches half its final magnitude — with a coverage floor of 0.20:

```
Croissant 0.96 | gemma 0.76 | recurrentgemma 1.00 | CT-LLM 0.97
Llama 0.92 | Falcon3 1.00 | glm 1.00

F05: SFT 0.92, DPO 0.96, RLVR 0.98
```

**This is a replication of F05 on targets it did not use.** F05's revision (2026-07-01, 405,248 rows, 40 families) selected targets as data-driven movers — words chosen because they moved, which conditions on the outcome. `task_charge`'s ratings are blind to both arms. The onset comes out the same.

**And the depth axis is orthogonal to the share axis.** Llama (88% readout) onsets at 0.92; recurrentgemma (17% readout) at 1.00; gemma (-11%) at 0.76, the earliest. Same timing, different substrate — late-and-readout and late-and-state are both available, at the same depth. F05 established when; this establishes that "when" does not determine "what on".

## The coverage floor is not a detail

**Below three-quarters of the stack the lens puts essentially no mass on the rated words, in every model.**

```
                       0.00    0.25    0.50    0.75    0.88    0.94    1.00
CroissantLLMBase      0.000   0.000   0.000   0.000   0.245   0.144   0.310
gemma-2-9b            0.008   0.000   0.041   0.596   0.809   0.841   0.836
recurrentgemma-9b     0.000   0.000   0.000   0.000   0.000   0.000   0.865
CT-LLM-Base           0.000   0.044   0.034   0.775   0.784   0.823   0.915
Llama-3.1-8B          0.003   0.001   0.007   0.311   0.291   0.401   0.753
Falcon3-7B-Base       0.006   0.006   0.003   0.082   0.659   0.917   0.671
glm-4-9b-hf           0.001   0.001   0.003   0.385   0.151   0.083   0.588
```

`recurrentgemma-9b` is exactly 0.000 until the final layer. A `T` computed there is a ratio of two vanishing numbers, and an onset statistic will happily cross its threshold on it. Without the floor:

```
                     floor 0    0.05    0.10    0.20
Llama-3.1-8B            0.20    0.80    0.81    0.92
glm-4-9b-hf             0.05    0.85    0.85    1.00
CroissantLLMBase        0.52    0.94    0.96    0.96
gemma-2-9b              0.29    0.74    0.75    0.76
```

**Llama moves from 0.20 to 0.92.** An unfloored run of this instrument reports that alignment begins a fifth of the way up the stack and contradicts F05; the disagreement is entirely the missing floor. This is why `layer_probs` returns the full probability vector rather than a scalar — the caller can compute coverage at every depth and is not able to avoid seeing it.

## What this is not

**Not a mechanism.** "The state carries it" says the residual stream arriving at the last layers already differs; it says nothing about which earlier component changed it. The sidecars hold the final position only, so nothing here can attribute the state change to attention, MLP, or a particular layer's output.

**Not first-token-only by choice.** The sidecars are the final position of the prompt, so the lens gives `p_L(first token | prompt)`. Multi-token words need a forward pass per continuation token. On Llama-3.1-8B, single-token words are 87% of rated words and 87% of base mass; on the low-coverage pairs that share is much worse, which is what `coverage` records.

**Not powered.** Six prompts per pair on five pairs. The pooled and median shares agree, and four of five pairs point the same way, but this is a characterisation of an available archive, not a test.

**Not a claim that Llama is unusual as a model.** It is the counter-case *in this measure on these prompts*. The archive is 16 pairs of the roster's ~50, selected by whichever v2 run happened to write sidecars.

## Reproducing

```
.venv/bin/python -u run.py                       every archived pair
.venv/bin/python -u run.py --pairs meta-llama/Llama-3.1-8B --top 12
.venv/bin/python -u run.py --floor 0.0           reproduce the unfloored onsets above
```

Reads `$MALIGNMENT_DATA/dose_response/charge_en50_flash.jsonl` and the `.f32` sidecars under `$MALIGNMENT_HIDDEN` (default: the read-only `malign-logits` archive). Models are never loaded — safetensors memory-maps, so pulling an unembedding out of a 37GB checkout is a partial read. Lens machinery is `malignment/lens.py`.

## Amendments

**A1, 2026-08-29.** The first version of this measurement ran on Llama-3.1-8B alone and reported 90% readout as the result. That is the outlier. Recorded here because the direction of the correction matters: a single pair gave a clean, theoretically attractive answer — repression at the point of utterance, the state untouched — and the population reversed it. The attractive reading survives for exactly one model.
