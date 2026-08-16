# Registration — sex_violence_lexicon

**Frozen 2026-08-16, before any agent was launched.** Amendments append below, dated, never edited in place.

## Why this exists, stated before the result

Every instrument this project already holds fails on the vocabulary the project studies, and each fails differently. `cock` — the original OLMo finding's own example — is absent from RID and from the General Inquirer, and USAS reads it as a bird (`L2`) and a weapon (`G3`). `stabbed` returns `gi=[]`. `k_ratings_en`'s own `_meta` warns that `vulgarity` has variance on 463 of 27,242 words (1.7%), so its zeros are a floor, not a measurement.

**This lexicon is therefore built AFTER seeing the existing ones fail, and on the specific word that failure was noticed on.** That is a selection event and it is recorded here rather than discovered later. What it licenses and what it does not:

- It licenses building an instrument that covers the transgressive tail.
- It does **not** license reporting `cock` as evidence the instrument works. `cock` is the training case (see BURN-IN below).

**AND BURN-IN COSTS THE LEXICON NOTHING.** An earlier draft of rule 4 struck `cock` and `stabbed` from the precision and recall denominators. That was wrong twice over. It was **inert** — precision is measured on controls (words no generator produced) and recall on the random-remainder audit, and a word the generators certainly produce cannot appear in either pool, so the exclusion removed nothing from any denominator it named. And it was **the wrong shape**: it dressed a citation problem as an accounting one, which is how a guard comes to read as protective while constraining nothing. The burn-in words are admitted, counted, and used exactly like every other word. What is barred is quoting them as confirmation.

## The question

Can a blind LLM panel produce a sexual/violent lexicon that (a) covers the transgressive vocabulary present in the twp corpus, including the low-frequency vulgar tail, at (b) a measured false-positive rate and (c) a measured miss rate — rather than an assumed one?

## Population

The vocabulary of `twp_words`: **224,919 distinct words**, all cell counts, no frequency cut. The cut is refused on evidence: at ≥500 cells the vocabulary falls to 13,233 words holding 97% of mass, but that cut drops `cunt` (137 cells), `maim` (132), `vagina` (61), `slut` (71), `horny` (33) — i.e. it removes preferentially the words the instrument exists to catch. **Frequency is correlated with the target, so a frequency cut is a selection on the target.**

`population.json` records the exact vocabulary snapshot (row count, distinct words, ClickHouse query, date).

**SCOPE: ENGLISH ONLY, DECLARED NOT DISCOVERED.** 97,804 of the 224,919 words are pure `[A-Za-z]+`; a large remainder is CJK, because Qwen and the Chinese families generate Chinese. This build labels English and **is blind on Chinese by construction**. Any downstream result using it must either restrict to English output or report the unlabelled share per family — a family whose output is 39% Chinese scored on an English-only field is being measured on the part of itself the instrument can read. A Chinese lexicon is a separate question, not an extension of this one.

## Blindness — the condition that makes this a measurement

**Generators see no corpus data of any kind.** Not the vocabulary, not the prompts, not cell counts, and above all not movement. They are given category definitions and a seed list, and asked to be expansive.

**Raters see a single shuffled stream** in which generated candidates, morphological expansions, hidden negative controls, and random remainder words are indistinguishable by construction — same format, same order randomisation, no provenance field.

**Neither sees `delta`, `p_base`, `p_aligned`, or any prompt.** The failure mode being designed against is a lexicon that predicts falling because it was built from words that fall.

## Design

| Stage | What runs | Overlap |
|---|---|---|
| A generate | N ≥ 4 independent agents, identical brief, no data | full — every agent answers the same brief |
| B intersect | deterministic: keep candidates present in `twp_words`, record cells | — |
| C expand | deterministic: stem/substring expansion over the 224,919-word vocabulary | — |
| D rate | every item rated by exactly 3 agents; plus an ANCHOR block every rater sees | 3-way per item, K-way on anchors |
| E audit | random sample of the unlabelled remainder, through the same rating panel | 3-way |

Controls are injected into stage D at a declared ratio and their identity is held out of the rater input.

## Executable decision rules, declared now

1. **ADMISSION.** A word enters the lexicon for category C iff **≥2 of its 3 raters assign C**. Ties and 1/3 splits are excluded, not broken.
2. **PRECISION GATE.** Hidden negative controls are random words drawn from the vocabulary that no generator produced and that contain no confirmed stem. If the panel labels **>5%** of controls as sexual or violent, the panel is too loose and the lexicon is **NOT ADMITTED** for use — the run is reported as a failed instrument build, not retuned until it passes.
3. **RECALL FLOOR.** Stage E rates a random sample of the unlabelled remainder. The positive rate there, times the remainder size, estimates the miss count. This number is **reported whatever it is**; there is no threshold at which the lexicon is withdrawn for it, because a bounded miss rate is a usable instrument and an unmeasured one is not.
4. **BURN-IN IS A CITATION BAR, NOT A DEDUCTION.** `cock` and `stabbed` — the words whose failure in RID/GI/USAS motivated this build — are rated, admitted, counted and used like any other word; nothing is subtracted anywhere. They are flagged `burn_in: true` in `results/lexicon.json`, and **no write-up may cite them as evidence the instrument works.** "Our lexicon covers `cock`, which USAS reads as a bird" is circular: covering it is the specification, not a test of it. Reporting that it *fails* on a burn-in word is permitted and would be informative.
5. **FREEZE BEFORE USE.** The admitted lexicon is written once with a sha recorded in `results/`. No downstream experiment may cite a lexicon whose sha is not the frozen one. If the lexicon is rebuilt, it gets a new sha and every citing result is re-run or withdrawn.
6. **THE SEEDS ARE PART OF THE INSTRUMENT.** The seed list handed to generators is recorded verbatim in `workflows/`. A word appearing in the seeds is marked `seeded: true` in the output and reported separately, so "the lexicon contains what we told it" is visible rather than inferred.

## The outcome I would rather not see

That the panel's controls come back above 5% — i.e. asked to be expansive, it calls a large fraction of ordinary vocabulary sexual or violent, and the instrument's apparent coverage is just a low threshold. Rule 2 makes that a stop, not a tuning knob.

Second: that stage E finds a high positive rate in the remainder, meaning generate-then-verify missed the tail after all and the label-the-corpus design was necessary. That would be expensive to learn but it is the honest test of the design choice made here, and it is why stage E exists.

## What this registration does NOT cover

The downstream use — whether SFT represses sexual more than DPO represses violent — is a **separate question with its own registration**. It is not run in this directory and its hypotheses are not stated here, so that the instrument cannot be tuned toward them.

---

## Amendments

**2026-08-16, during stage D — the instrument now emits `register`, and that is an output, not a hypothesis.** Stage A returns a register per proposed word (`vulgar/clinical/slang/archaic/euphemistic/plain`); `run.py --stage score` carries it into `results/lexicon.json`, with expansions inheriting their stem's register. No gate, population, or decision rule in this registration changes.

It is recorded here because register is the axis a downstream experiment tests, and the instrument must be able to show that its register labels were fixed **before** any movement was read. Those hypotheses live in `experiments/register_shift/registration.md`, frozen the same day and likewise before any `delta` was touched. **They are deliberately not in this file**: an instrument registration that also declared findings hypotheses would be tunable toward them, which is the whole reason the two are separate.

**2026-08-16, after stage D — rule 2's "false positive" is an UPPER BOUND, not a false-positive rate. Recorded because the rule as written overstates what it measures.**

Rule 2 defines controls as vocabulary words no generator proposed, and treats an admitted control as a false positive. **A control positive is ambiguous by construction:** it is either the raters being too loose (a true FP) or the *generators* having been too narrow (a recall miss that happened to land in the control pool). The rule cannot tell them apart, and I did not notice when writing it.

Both control positives were inspected: **`warworn` and `hitlist`**. Both look genuinely violent. If that reading is right, the true false-positive rate is **0/856** and these two are recall misses, making precision better than reported and recall slightly worse.

**Nothing is recomputed on that reading.** The inspection is mine, post hoc, on two words, and substituting my judgment for the panel's is exactly the move the blind design exists to prevent. The booked figure stays **0.23% (2/856)** and is to be cited as *"false-positive rate ≤ 0.23%"*. The gate — declared at 5% — passes by a factor of 20 under either reading, so no decision turns on it.

**The audit has an unsampled region, also declared late.** Controls and audit words were drawn from a pool that excludes stem-adjacent words, so **4,659 unrated stem-adjacent words were never eligible for the audit** — and those are where inflectional misses would concentrate. The reported miss estimate (~236, Poisson 95% ≈ 29–853) covers the 70,391-word non-adjacent remainder ONLY. It is not a whole-vocabulary recall figure and must not be quoted as one.
