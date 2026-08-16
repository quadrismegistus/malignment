# Registration — screening_base

**Frozen 2026-08-16, before `run.py` was written.** Amendments append below, dated, never edited in place.

## THE SELECTION EVENT, DISCLOSED FIRST BECAUSE IT ALREADY HAPPENED

**An exploratory pass was run before this registration existed.** On 2026-08-16, answering RH's question *"should we default to llama as screener?"*, the analysis below was run informally in a shell against the live store. It showed:

    model                    mean pct   breadth pct   intensity pct
    Falcon3-10B-Base              51%           49%             59%
    Llama-3.1-8B                  96%           92%             82%
    Falcon3-3B-Base               11%           29%              8%

**So this document is not blind and does not pretend to be.** What that costs and what it does not:

- It **does not** license reporting Falcon3-10B-Base as the winner of a pre-registered contest. It was not. It was the outcome of an exploratory query, and the specification below was written knowing that outcome.
- It **does** license freezing the selection rule, the population and the refusals *before a producer exists*, so that the choice acquires a receipt, an exclusion list and a re-runnable derivation instead of resting on a shell transcript.
- The rule below has **no tunable parameter** (see THE RULE). That is deliberate: a threshold chosen after seeing the ranking is a threshold tuned to the answer, and the first draft of this document had one — `|pct - 50| <= 8` — which was picked because it admitted four models and one of them was the preferred one.

**And the preference is declared rather than left implicit.** I would rather Falcon3-10B-Base won: it is the same family as the declared diagnostic pair, it is already cached locally, it is out of `endpoints()` and every chain, and it is measured on 2,663 cells. Those are conveniences, not evidence of representativeness, and none of them appears in the rule.

## THE QUESTION

Which released checkpoint is **representative** of the roster's transgressive-vocabulary behaviour, and should therefore screen slot frames?

Screening asks *can this frame move at all*. It reads one distribution and no contrast, so the hazard is not contamination — selection on `P_base` is a pre-treatment covariate and cannot bias a base→aligned contrast measured after it. The hazard is **unrepresentativeness in either direction**:

    a QUIET screener   rejects frames that are alive in the models actually measured
    a LOUD screener    admits frames that are dead in them

The first is the failure malign named as *M01 in reverse*. The second is the original M01 failure — *"the prompt and slots were just badly chosen ... accidentally lame, not transgressive at all"* — arriving by a different route. **Both are errors of the same kind and a single-sided gate would catch only one.**

## THIS REGISTERS NO HYPOTHESIS — AND STILL NEEDS A REGISTRATION

It makes no claim about the world. It declares a selection rule, a population and a set of refusals, and says nothing about what alignment does. It therefore belongs in `instrument_calibrations/` and **must not** be cited in the hypothesis register.

**But "no hypothesis" is not the same as "no registration needed", and the difference is the whole reason this file exists.** `experiments/README.md` makes a registration required under *two* conditions, not one:

> It is required when the result has **a direction you would be disappointed by**, **or when a different specification could give a different answer you would prefer.**

The first condition does not apply: there is no finding here to be disappointed by. **The second applies exactly**, and this is descriptive work that still needs freezing:

- **The specification IS the searchable thing.** Mean, breadth and intensity give *different winners*. `Qwen3-8B` is 17th percentile on mean and 91st on intensity; a rule built on intensity-median names a model that almost never reaches for a labelled word. Every combining rule — mean of percentiles, sum of deviations, max of deviations, a threshold band — admits a different set. Nothing in the data picks among them.
- **And I have a preferred answer**, declared above: Falcon3-10B-Base, on grounds (same family as the diagnostic pair, already cached, out-of-population) that are conveniences and not evidence.
- **The tell in `experiments/README.md` is met, not evaded.** *"'This one is just descriptive' is exactly what gets said to avoid registering: if you can name an outcome you would rather see, register."* I can name one.
- **And it was nearly searched.** The first draft of THE RULE gated on `|pct − 50| <= 8`, chosen after seeing the ranking, admitting four models of which one was the preferred one. That is a specification search with the search step performed silently. It is recorded here because it happened, not as a hypothetical.

So: no hypothesis, and a registration anyway — because what is at risk is not a claim about alignment but **the rule that picks the instrument every later screening decision runs through.**

## POPULATION

**Prompts.** `{db}.wf_panel` — the 2,189 crossed panel prompts. Not "all prompts": prompt sets are fleet-defined and do not nest, and the universal intersection over all 402 measured models is one prompt.

*Declared limit:* balancing the panel is **not composition-neutral** — it keeps 100% of `taboo` and `property` but 42% of `neutral` and 34% of `contradiction`. A screener chosen on this panel is chosen against that composition, and any later claim that it is representative *of a different corpus* does not follow.

**Models.** Every checkpoint with **≥2,000 of the 2,189** panel prompts measured. On the snapshot date that is **156 of 403** models with any panel cells.

*Why a coverage floor at all:* a model measured on 300 prompts and one measured on 2,180 produce means over different prompt sets, and the difference between them is then partly composition rather than behaviour. 2,000 is ~91% and is declared here rather than chosen later; it is not tuned, and the sensitivity of the result to it is a REPORTED quantity (see OUTPUTS).

**Excluded, and the reason:**

| excluded | why |
|---|---|
| checkpoints below the coverage floor | 247 of 403; their means are over a different prompt set |
| `@revision`-suffixed training checkpoints | a screener must be a released model somebody can name and load; `pythia-6.9b@step28000` is a point in a trajectory |
| nothing else | in particular NO exclusion for being in `endpoints()` or a chain — contamination is not a screening hazard, and excluding on it would silently narrow the pool for a reason that does not apply |

**Instrument.** `{db}.wf_sexviolence`, sha **`d542e7e2bb86bd00`**, 1,063 words (394 sexual, 655 violent, 14 both). Admitted at FP ≤0.23% against a 5% gate, Fleiss κ = 0.929.

**ITS SCOPE LIMIT IS INHERITED AND MUST BE REPORTED.** That lexicon is English-only and blind on CJK by construction, and its registration requires any downstream result to report the unlabelled share per family. The exploratory pass **failed to do this**, and the check that was then written to cover it used a malformed ClickHouse pattern (`[\x{4e00}-\x{9fff}]`) that matched 2,188 of 2,189 prompts where the true count is 1. `\p{Han}` agrees with Python. **The producer must use `\p{Han}` and must report both shares per candidate**, so that a model whose mass sits in vocabulary the instrument cannot see is never read as quiet.

## THE MEASURE, AND WHY IT IS THREE NUMBERS

Per (model, prompt): the summed probability of lexicon-labelled words at the blank, absent counted as **0** rather than dropped. Then per model:

    MEAN       total labelled mass / panel prompts measured
    BREADTH    share of panel prompts carrying ANY labelled mass
    INTENSITY  labelled mass per prompt that carries any

**The mean alone is not sufficient and this is measured, not asserted.** The per-prompt distribution has a median of exactly **0.0000** and a maximum of **0.71**, so the mean summarises a very skewed quantity and mixes breadth with intensity. Two models sit near the middle on the mean for opposite reasons: `Qwen3-8B` is 17th percentile on mean, **2nd on breadth and 91st on intensity** — it almost never reaches for a labelled word and commits when it does. `OLMo-2-0425-1B` is its inverse. **A screener chosen on the mean could be either.**

## THE RULE — no free parameter

> Among the population above, the screening base is the model minimising
> **max(|pct − 50|)** across the three statistics.

Rank percentile is used rather than raw value so the three are commensurable. **The maximum is used rather than the sum or the mean** because the failure being guarded against is being extreme on one axis while average on another, and a sum lets a 90th-percentile intensity be paid for by a 10th-percentile breadth. *Three quantities that cannot be averaged cannot be polled either.*

## REFUSALS — declared before, not chosen after

1. **If the winner's `max(|pct − 50|)` exceeds 25**, no screener is declared and the result is reported as *no representative model exists in this population*. A model that is 25 points off median on any axis is not representative; naming it anyway would be the instrument certifying its own necessity.
2. **If the winner changes under a coverage floor of 1,500 or 2,180**, the choice is reported as **floor-dependent** and the three candidates are named. It is not re-run at a third floor to break the tie.
3. **No frequency cut, no domain filter, no prompt subsetting.** The panel is the panel.
4. **The result does not transfer to pole mass.** This measures a blind general lexicon over a declared corpus; screening in the app measures author-chosen poles on one frame. They are correlated and they are not the same instrument, and any claim that the screener is representative *for pole mass* needs its own measurement.

## OUTPUTS

`results/by_model.csv` — one row per model in the population: the three raw statistics, their percentiles, `max_dev`, coverage, labelled share, CJK share. **Long form, one row per model, so the summary can be re-derived and disagreements surface.**

`results/sensitivity.csv` — the winner under each of the three coverage floors, for refusal 2.

`population.json` — the explicit model ids, the panel prompt count, the lexicon sha, the date.

## THIS IS ONE OPERATIONALISATION OF MEDIAN-NESS, AND OTHERS EXIST HERE ALREADY

RH, 2026-08-16: *"the method you used is one method but there are other measurements of median-ness in this corpus/project, right?"* Yes, and naming them is part of the declaration — a registration that does not say what it chose *among* reads as the only available measure.

| measure | what it uses | population | language |
|---|---|---|---|
| **THIS ONE** | labelled mass, `wf_sexviolence` | 2,189-prompt panel, 156 models | **English only** |
| argmax agreement centrality | `{db}.panel_pairs`, 78,106 pairs | balanced 473 prompts, 399 models | agnostic |
| JS to a corpus centroid | `similarity.js`, full distributions | as above, expensive confirm | agnostic |
| alignment-edge magnitude | `movement_cells.js_total` | the model's own edge | agnostic |

**Two of those are language-agnostic and this one is not**, which is a real disadvantage of the measure chosen and not a footnote: a model whose transgressive mass sits in Chinese vocabulary is invisible to the lexicon and would read as quiet. On the 2,189-prompt panel that risk is near zero — 1 prompt contains CJK and CJK mass is 0.018–0.029% per candidate — but that is a property of *this panel*, not of the measure.

**Why this one anyway:** screening asks whether a frame carrying *transgressive* vocabulary can move, so an instrument that measures transgressive mass directly is closer to the quantity than a general distributional distance. Argmax agreement would name the model most typical in aggregate, which is a different notion of typical and might be typical in ways irrelevant to the poles.

**That is a judgement, not a derivation.** A screener chosen by argmax-agreement centrality would be a legitimate answer to the same question by a different instrument, and if the two disagree that disagreement is a finding rather than an error.

## STOPPING RULE — BINDS THIS MEASUREMENT, NOT THE QUESTION

RH, 2026-08-16: *"i dont think we should treat instrument registrations as binding for all time, just binding for their measurements."* Adopted, and the first draft of this section overreached in exactly that way.

What is frozen: **this specification.** The population, the three statistics, the combining rule, the refusals. Those may not be changed after seeing this producer's output, and this producer is run once — because re-running *this* rule with a different statistic after seeing the answer is the specification search the registration exists to prevent.

What is **not** frozen: the question. Another operationalisation of median-ness — any row in the table above — is a legitimate new question with its own registration, and it does not need this one to have failed first. **This registration claims no priority over them.** If two measures name different screeners, that is information about how "representative" behaves under different instruments, and the right response is to report both rather than to rank the registrations by date.

The practical difference: a later seat may measure this again by another route without arguing that this one is void, and this one may not quietly become the other after the fact.

---

## AMENDMENT 1 — 2026-08-16, AFTER THE RUN

**Appended, not edited in place. THE RULE ABOVE RAN AS FROZEN and its output stands: under `argmin max(|pct − 50|)` the winner is `Aleph-Alpha/Pharia-1-LLM-7B-control-hf` at max_dev 6.1, stable across all three declared coverage floors, refusal 1 not triggered.** That result is preserved in `results/summary.json` and is not being revised.

RH, after seeing it: *"we dont need the exact median do we? just a list of candidates."*

**The objection is correct and it is about the measurement, not the answer.** The max_dev gradient has no natural break — 6.1, 8.1, 9.4, 10.6, 11.3, 11.3, 11.9, 13.2, 13.2, 14.5 — so an argmin over a rank statistic across 155 models manufactures a winner out of a smooth distribution. The distance from rank 1 to rank 3 is 3.3 percentile points. **Naming one model asserts a precision this measurement does not have.**

**SO THE REPORTED FORM CHANGES AND THE RULE DOES NOT.** The output is now a CANDIDATE SET: every model within the **already-declared 25-point ceiling** from refusal 1. That ceiling was frozen before the run, for the stated reason that a model more than 25 points off median on any axis is not representative. Using it to admit rather than only to refuse introduces **no new parameter and no post-hoc threshold** — which is the whole reason it is the boundary used, rather than a break chosen from the observed gradient.

The set is **32 of 155 models (21%)**.

### AND THIS CHANGE ADMITS THE MODEL I SAID I PREFERRED

Declared in the selection event above: I would rather `Falcon3-10B-Base` won. Under the frozen argmin it placed **third** (max_dev 9.4). Under the candidate set it is admitted.

**A specification change made after seeing the result, which moves the author's preferred answer from losing to eligible, is the exact shape of a specification search** — and it does not stop being that shape because the objection came from RH and is correct on the merits. What keeps it honest is not the motive but that the boundary was pre-declared and the losing result is preserved above rather than overwritten. A reader who thinks the band is self-serving can compare it against the argmin winner, which is still in `summary.json`.

**What this does not license:** picking `Falcon3-10B-Base` from the set *because* it was preferred, and calling that the calibration's output. The calibration's output is 32 models. Choosing among them is a separate decision on separate grounds — locality, family, licence, size — and those grounds are engineering conveniences that must be named as such, not laundered through this instrument.

### WHAT THE SET SAYS THAT THE ARGMIN DID NOT

The three statistics are not redundant inside the band. `zephyr-7b-beta` sits at breadth 65% / intensity 36%, `OLMoE-1B-7B-0125-SFT` at breadth 40% / intensity 65% — both admitted, both "median" on the mean, and they behave oppositely. **A screener chosen from this set still has a character**, and the set is the right object to choose from precisely because it makes that visible where a single name hid it.
