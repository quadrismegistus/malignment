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

## THIS REGISTERS NO HYPOTHESIS

Like `sex_violence_lexicon`, and for the same reason: a registration that makes no claim about the world cannot be tuned toward a finding, because there is no finding in it to aim at. It declares a selection rule, a population and a set of refusals. It says nothing about what alignment does.

It therefore belongs in `instrument_calibrations/` and **must not** be cited in the hypothesis register.

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

## STOPPING RULE

This is run **once**. If the declared screener later proves unfit in use, that is a new question with its own registration, not a re-run of this one with a different statistic.
