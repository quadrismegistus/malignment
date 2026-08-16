# screening_base

**Question.** Which released checkpoints are near the middle of the roster for transgressive-vocabulary mass, and are therefore reasonable models to screen slot frames with?

**Status: RUN, 2026-08-16.** 58 UNTREATED models (49 of the 50 declared bases, plus 9 untreated non-roots), 2,189-prompt panel, lexicon sha `d542e7e2bb86bd00`. **15 candidates.**

**id.** `screening_base`

## Why it matters which model screens

`SlotExplorer` screens candidate frames by showing what one model wants to say at the blank, and that model biases the screen both ways: a **quiet** one rejects frames that are alive in the models actually measured, a **loud** one admits frames that are dead in them. The second is the original M01 failure — *"the prompt and slots were just badly chosen … accidentally lame"* — by a different route.

This is **not** the diagnostic pair and takes a different answer. Screening reads one distribution and no contrast, so contamination is not its hazard: selection on `P_base` is a pre-treatment covariate and cannot bias a base→aligned contrast measured after it. The diagnostic pair (`slots.DIAGNOSTIC_PAIR`) has the opposite requirement and is declared separately.

## Result

**A set, not a winner.** 15 of 58 untreated models sit within 25 percentile points of median on *all three* statistics — `results/candidates.csv`.

| model | mean | breadth | intensity | max dev |
|---|---|---|---|---|
| kanana-2-3b-base | 45% | 53% | 55% | 5.2 |
| CroissantLLMBase | 43% | 52% | 50% | 6.9 |
| kanana-1.5-8b-base | 41% | 45% | 59% | 8.6 |
| RedPajama-INCITE-Base-7B-v0.1 | 47% | 60% | 48% | 10.3 |
| stablelm-2-1_6b | 40% | 38% | 62% | 12.1 |
| Falcon-H1-7B-Base | 36% | 57% | 36% | 13.8 |
| Pharia-1-LLM-7B-control-hf | 38% | 34% | 60% | 15.5 |
| Falcon3-Mamba-7B-Base | 53% | 67% | 53% | 17.2 |

No natural break in the gradient, so ranking within the set is over-reading. Stable across all three coverage floors.

**What falls outside, which is the useful part:**

| | mean | breadth | intensity | max dev | rank |
|---|---|---|---|---|---|
| Falcon3-10B-Base | 33% | 24% | 69% | 25.9 | 17/58 |
| Mistral-7B-v0.1 | 84% | 91% | 71% | 41.4 | 40/58 |
| Llama-3.1-8B | 93% | 81% | 86% | 43.1 | 43/58 |
| Falcon3-3B-Base | 3% | 10% | 3% | 46.6 | 53/58 |

**THE UNTREATED RESTRICTION CHANGED THE ANSWER.** A first run over all 155 models put `Falcon3-10B-Base` third of 32 candidates; restricted to untreated it is 17th and outside the set. That is not noise — 97 of those 155 were aligned checkpoints whose transgressive mass has already been repressed, and removing them raises the median, so a moderate model reads as quiet against it. **The mixed-population run was measuring the wrong thing and admitted the author's preferred model; this one excludes it.**

`Llama-3.1-8B` remains loud on all three and `Falcon3-3B-Base` is the quietest base measured — 3rd, 10th and 3rd percentile. It stays the right *diagnostic* pair and is a bad screener by a wide margin.

## Method

Per (model, prompt), the summed probability of lexicon-labelled words at the blank, absent counted as 0. Then per model: **mean** (mass per panel prompt), **breadth** (share of prompts carrying any), **intensity** (mass per prompt that carries any). Rank-percentile each, and take everything within 25 points of median on the worst axis.

Three statistics rather than one because the per-prompt distribution has a median of exactly **0.0000** and a max of **0.71** — the mean alone mixes breadth with intensity, and two models can reach it from opposite directions.

| | |
|---|---|
| prompts | `{db}.wf_panel`, 2,189 crossed panel prompts |
| models | **untreated** (no ALIGNING op anywhere in ancestry), ≥2,000 panel prompts, no `@revision` checkpoints — 58 |
| instrument | `{db}.wf_sexviolence`, sha `d542e7e2bb86bd00`, 1,063 blind-rated words |

**Untreated, not `population("bases")`.** The screener must be pre-treatment: an aligned model's transgressive mass is what SURVIVED repression, where screening asks what is AVAILABLE to be repressed. But "declared base" means pretrained ROOT, which is too strict — `Falcon3-10B-Base` is `upscale`d and `Falcon3-3B-Base` is `prune`d from the 7B, and `Pharia-1-LLM-7B-control-hf`'s ancestor was never released. `upscale` and `prune` are pretrained-to-pretrained. So the test is on the ops along the ancestry.

**49 of the 50 declared bases are in.** The one missing is `mpt-7b`, which has zero panel cells — a measurement gap, not an exclusion.

**Stable across coverage floors** (1500 / 2000 / 2180) — `results/sensitivity.csv`.

## Limits

- **The lexicon is English-only** and blind on CJK by construction; its registration requires the unlabelled share to be reported downstream. Here that exposure is negligible — 1 of 2,189 panel prompts contains CJK, and CJK mass is ≤0.03% per candidate — but it is a property of this panel, not of the measure. `run.py` uses `\p{Han}`; the pattern `[\x{4e00}-\x{9fff}]` matches 2,188 of 2,189 in ClickHouse and is wrong.
- **The panel is not composition-neutral**: balancing keeps 100% of `taboo` and `property` but 42% of `neutral` and 34% of `contradiction`. Representative *of this panel*.
- **This is one operationalisation of median-ness.** The project holds others that are language-agnostic where this one is not — argmax-agreement centrality over `{db}.panel_pairs` (78,106 pairs, balanced 473-prompt panel), JS to a corpus centroid via `similarity.js`, alignment-edge magnitude via `movement_cells`. A screener chosen by any of those is an equally legitimate answer, and disagreement between them would be informative rather than an error.
- **Does not transfer to pole mass.** This measures a blind general lexicon over a declared corpus; the app screens author-chosen poles on one frame. Correlated, different instruments.
- An exploratory version of this ran before the producer existed, prompted by *"should we default to llama as screener?"*. The numbers were the same; the reason it is written down is that the author's stated preference (Falcon3-10B, on grounds of locality and family) is in the resulting set, and should not be mistaken for something this measured.
