# screening_base

**Question.** Which released checkpoints are near the middle of the roster for transgressive-vocabulary mass, and are therefore reasonable models to screen slot frames with?

**Status: RUN, 2026-08-16.** 155 models, 2,189-prompt panel, lexicon sha `d542e7e2bb86bd00`. **32 candidates.**

**id.** `screening_base`

## Why it matters which model screens

`SlotExplorer` screens candidate frames by showing what one model wants to say at the blank, and that model biases the screen both ways: a **quiet** one rejects frames that are alive in the models actually measured, a **loud** one admits frames that are dead in them. The second is the original M01 failure — *"the prompt and slots were just badly chosen … accidentally lame"* — by a different route.

This is **not** the diagnostic pair and takes a different answer. Screening reads one distribution and no contrast, so contamination is not its hazard: selection on `P_base` is a pre-treatment covariate and cannot bias a base→aligned contrast measured after it. The diagnostic pair (`slots.DIAGNOSTIC_PAIR`) has the opposite requirement and is declared separately.

## Result

**A set, not a winner.** The candidates are the 32 of 155 models within 25 percentile points of the median on *all three* statistics — `results/candidates.csv`. The top of it:

| model | mean | breadth | intensity | max dev |
|---|---|---|---|---|
| Pharia-1-LLM-7B-control-hf | 54% | 56% | 53% | 6.1 |
| stablelm-2-1_6b | 56% | 58% | 54% | 8.1 |
| Falcon3-10B-Base | 51% | 49% | 59% | 9.4 |
| Llama-3.1-Tulu-3-8B-SFT | 45% | 57% | 39% | 10.6 |
| Olmo-3-1025-7B | 42% | 53% | 39% | 11.3 |
| Qwen3-8B-Base | 39% | 38% | 58% | 11.9 |

**There is no natural break in the gradient** — 6.1, 8.1, 9.4, 10.6, 11.3, 11.3, 11.9, 13.2 — so ranking these against each other is over-reading. Any of them is a defensible screener; the set is the answer.

**For contrast, the two models actually under discussion:**

| | mean | breadth | intensity | max dev | |
|---|---|---|---|---|---|
| Llama-3.1-8B | 95% | 92% | 82% | 45.5 | rank 128/155 — **loud on all three** |
| Falcon3-3B-Base | 11% | 29% | 8% | 42.3 | rank 109/155 — **quiet on all three** |

So Llama-3.1-8B is a poor screener, and Falcon3-3B is a poor screener while remaining the right diagnostic pair. Both are outside the candidate set by a wide margin, which is the useful thing this measured.

**Inside the band the three statistics still differ**, and that is worth reading before choosing: `zephyr-7b-beta` is breadth 65% / intensity 36%, `OLMoE-1B-7B-0125-SFT` is breadth 40% / intensity 65%. Both are "median" on the mean and behave oppositely.

## Method

Per (model, prompt), the summed probability of lexicon-labelled words at the blank, absent counted as 0. Then per model: **mean** (mass per panel prompt), **breadth** (share of prompts carrying any), **intensity** (mass per prompt that carries any). Rank-percentile each, and take everything within 25 points of median on the worst axis.

Three statistics rather than one because the per-prompt distribution has a median of exactly **0.0000** and a max of **0.71** — the mean alone mixes breadth with intensity, and two models can reach it from opposite directions.

| | |
|---|---|
| prompts | `{db}.wf_panel`, 2,189 crossed panel prompts |
| models | ≥2,000 of those prompts measured, `@revision` checkpoints excluded — 155 of 403 |
| instrument | `{db}.wf_sexviolence`, sha `d542e7e2bb86bd00`, 1,063 blind-rated words |

**Stable across coverage floors** (1500 / 2000 / 2180) — `results/sensitivity.csv`.

## Limits

- **The lexicon is English-only** and blind on CJK by construction; its registration requires the unlabelled share to be reported downstream. Here that exposure is negligible — 1 of 2,189 panel prompts contains CJK, and CJK mass is ≤0.03% per candidate — but it is a property of this panel, not of the measure. `run.py` uses `\p{Han}`; the pattern `[\x{4e00}-\x{9fff}]` matches 2,188 of 2,189 in ClickHouse and is wrong.
- **The panel is not composition-neutral**: balancing keeps 100% of `taboo` and `property` but 42% of `neutral` and 34% of `contradiction`. Representative *of this panel*.
- **This is one operationalisation of median-ness.** The project holds others that are language-agnostic where this one is not — argmax-agreement centrality over `{db}.panel_pairs` (78,106 pairs, balanced 473-prompt panel), JS to a corpus centroid via `similarity.js`, alignment-edge magnitude via `movement_cells`. A screener chosen by any of those is an equally legitimate answer, and disagreement between them would be informative rather than an error.
- **Does not transfer to pole mass.** This measures a blind general lexicon over a declared corpus; the app screens author-chosen poles on one frame. Correlated, different instruments.
- An exploratory version of this ran before the producer existed, prompted by *"should we default to llama as screener?"*. The numbers were the same; the reason it is written down is that the author's stated preference (Falcon3-10B, on grounds of locality and family) is in the resulting set, and should not be mistaken for something this measured.
