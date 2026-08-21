# Registration — register_shift

**Frozen 2026-08-16. THE HYPOTHESES IN THIS FILE (R1-R4) WERE SUPERSEDED BEFORE ANY RUN — see amendment A1, which carries the design that was actually frozen. R1-R4 are kept as the record of what was registered solo, not deleted.**

**Originally frozen before any movement row was read through the lexicon.** The lexicon itself is still in stage D as this is written: its admitted membership is unknown, its precision and recall are unmeasured, and no word's `delta` has been looked at. Amendments append below, dated, never edited in place.

## What licenses freezing this now, and what does not

Two facts about register were known when this was written, and both come from stage-A **proposals**, which are blind to movement by construction:

- the register mix of the proposed vocabulary — `plain 594, clinical 515, slang 486, archaic 370, vulgar 231, euphemistic 162`
- median corpus cell counts by register — `euphemistic 180, plain 107, vulgar 76, slang 61, archaic 38, clinical 34`

Neither is a movement quantity. Nothing here was written after seeing a `delta`, a JS, or a fall rate. **What IS acknowledged: the hypotheses below descend from a v1 finding made by hand on a handful of words** (`cock → penis`, `kill → smite`), so this is a confirmatory test of an existing observation at scale, not a discovery. That is the honest description and it is what the test is powered to do.

## The prior claim being tested

v1 recorded that sexual and violent content are repressed by *structurally different* mechanisms:

- **sex** — cross-category displacement, a *register shift* with the referent preserved (`cock → penis`: same thing named, different social class)
- **violence** — within-category synonym shuffling (`kill → punch/hit`), described as *suppression, not repression*

That distinction was drawn on a small number of hand-inspected word pairs in one family. The lexicon makes it a measurable proposition across 1,308 words, six registers, and the declared pairs population.

## Population and unit

- **Pairs**: base → aligned edges from `pairs`, 154 models.
- **Panel**: the **2,190 prompts held by all 154** — not "all prompts", which names a set no cross-model comparison can use. (Whole-battery is 4,428; the step/ladder population's 2,247-prompt panel shares only 473 with this one.)
- **Unit of inference: the LINEAGE**, per the campaign rule. Pairs nest within lineage; lineage-level statistics are what get quoted. A per-pair number is reported as description only.
- Words: the frozen lexicon, cited by sha. Registers as emitted: `vulgar, clinical, slang, archaic, euphemistic, plain`.

## Hypotheses

**R1 — DISPLACEMENT HAS TWO LEGS, AND THEY ARE TESTED SEPARATELY.** For sexual words, base→aligned:

- **R1a (fall)** vulgar-register mass falls.
- **R1b (rise)** clinical and/or euphemistic mass rises.

**Both legs are required for the word "displacement".** A fall without a corresponding rise is *suppression* — mass leaving the domain entirely — and this project has already committed to that distinction in print. Declaring it before the test means R1a alone cannot be written up as displacement afterwards. Predicted: R1a negative, R1b positive.

**R2 — DOMAIN ASYMMETRY (the v1 claim, restated as a contrast).** The R1 signature is **larger for sexual than for violent** words. Violence is predicted to substitute *within* register (plain→plain) rather than across it. Tested as an interaction, sexual vs violent × register direction, paired within lineage.

**R3 — ARCHAIC AS ESCAPE HATCH.** Archaic-register violent mass **rises** base→aligned (`smite`). **This is underpowered by construction and is declared so here**: archaic is the second-rarest register (median 38 cells) and the prediction is a rise in a rare register. R3 is reported with its interval whatever happens and **is not eligible to be a headline** — a significant R3 on this power is more likely a fluke than a finding, and saying that now is cheaper than arguing it later.

**R4 — THE FREQUENCY CONTROL, WHICH IS PART OF THE TEST AND NOT A ROBUSTNESS CHECK.** Register and corpus frequency are correlated across a 5× spread of medians. Every R1/R2 effect is therefore recomputed against **frequency-matched `neither` words** — for each lexicon word, a control word matched on cell count within ±10%, drawn from the stage-D-confirmed negatives. **If the register effect does not survive frequency matching, R1 is NOT SUPPORTED**, regardless of its unmatched significance. Declared as a gate, not an appendix.

## Executable decision rules

1. **R1 supported** iff R1a and R1b both hold at the lineage level, sign-consistent in a majority of lineages, **and** survive R4 matching. Any one of the three failing ⇒ NOT SUPPORTED, reported as such.
2. **R2 supported** iff the sexual−violent interaction is positive with a lineage-level interval excluding zero. Ties are dropped from sign tests, never split.
3. **R3 is reported, never headlined.** See above.
4. **The lexicon is cited by sha.** If the lexicon is rebuilt, this experiment is re-run or withdrawn — a result computed against an unrecorded instrument version is not a result.
5. **Unlabelled share is reported per family.** The lexicon is English-only; a family generating substantial Chinese is being scored on the part of itself the instrument can read, and that fraction is stated rather than assumed small.

## The outcome I would rather not see

**R1a without R1b.** Vulgar mass falls, nothing rises, and the register story collapses into ordinary suppression — which would mean the v1 "displacement" reading of sex was an artefact of looking at `cock → penis` and not at where the mass went. That is the result this design is built to be able to return, which is why the two legs are separated before the run rather than after.

Second: that R4 kills it — the register effect is frequency in costume. The medians above say register and frequency are entangled, so this is not a remote possibility.

## Relation to the other open question

Whether **SFT** or **DPO** does the sexual/violent work is a different question (`division_of_labour/`), whose H3 currently sits at chain p=0.031 / base p=0.077 on *prompt*-level domains. Re-running it at word level with this lexicon is a follow-up that needs its own registration, recording that it was run after seeing that prompt-level H3 was not supported.

---

## Amendments

### A1 — 2026-08-16. The design is replaced BEFORE ANY RUN, after discussion with RH. Original hypotheses superseded, not deleted.

Nothing in this experiment has been run. R1–R4 above stand as the record of what was registered solo this morning; they are **superseded** by the design below, worked out with RH the same day. Both are kept because a design that changed needs its predecessor visible — otherwise "we always meant this" is unfalsifiable.

**Why the original was wrong.** R1–R4 took the lexicon's `register` field as the instrument and tested per-stage. Two problems, both found by measuring rather than by argument:

- **The lexicon's register labels were never blind-rated.** Categories went through the 15-rater panel (Fleiss κ=0.929); register was **self-reported by whichever generator proposed the word**. Worse, 4 of the 8 generators were *assigned* a register and told to report it: `angle-clinical` returned `clinical` for **439/439** of its words and `angle-slang` returned `slang` for **397/397**. For those the field is an instruction echoed back, not a judgement. (`angle-vulgar` 33% and `angle-archaic` 59% did exercise discretion, and replicate-vs-angle labels agree on 86% of the 372 words carrying both — so the majority vote is not purely definitional. But there is no reliability figure for register anywhere.)
- **Only 550 of 1,063 admitted words carry a direct register label**; the rest inherit from a stem.

### The design as frozen

**INSTRUMENT: `k_ register_level`, English ∪ Chinese, 1–7 continuous.** RH's suggestion to add `k_zh` is what makes this viable: coverage of the worst model rises from **85.2% to 95.6%** of cell mass (median 99.6%), and — the number that matters — the **within-pair** coverage shift falls from median 0.51pp / max 7.50pp to **median 0.12pp / max 3.73pp**, with pairs shifting >2pp dropping from 15 to 6. A base→endpoint comparison is confounded if the covered subset moves between the arms, and Chinese coverage is what was moving it.

**The two instruments corroborate each other.** `k_ register_level` and the lexicon's register labels agree at **Spearman rho = 0.645 (n=480, p=1e-57)**; vulgar-vs-clinical separates at AUC 0.976 and clinical-vs-plain at 0.715. They were built months apart, by different procedures, for different purposes, neither seeing the other. That agreement is the only evidence either has that it measures register at all, and it is why `k_` can be primary and the lexicon field a corroborating second.

**STATISTIC: mass-weighted mean register** (RH's choice), `Σ(mass × register) / Σ(mass)`. Treating a 1–7 ordinal as interval is accepted deliberately: the assumption-free alternative (comparing full register distributions) cannot be stated as one number per lineage.

**EDGE: base → endpoint**, the commodity form — what a user actually receives, and it sidesteps sequential depletion entirely. Per-stage decomposition is descriptive.

**POPULATION: 64 base→endpoint pairs over 48 LINEAGES**, panel 2,189 (crossed over all 112 models involved, then live-status gated). Three times the n of the chain population, at no cost in panel, because base→endpoint needs no released SFT rung.

### Hypotheses as frozen

    G    the mass-weighted mean register of the distribution RISES, base -> endpoint
    G1   what LEAVES is low-register    mean_register(removed mass) < distribution mean
    G2   what ARRIVES is high-register  mean_register(arrived mass) > distribution mean

**G alone cannot distinguish suppression from displacement** — the mean rises either because low-register mass fell or because high-register mass arrived. G1 and G2 separate them, and **`arrived > removed` is the displacement signature**. This is the R1a/R1b split preserved, with an instrument that can actually carry it.

**S** — the same three, restricted to the lexicon's `sexual` set. This is the v1 claim (`cock → penis`) at scale.

### DISCLOSURE, and it is serious

**I have already seen evidence bearing on S.** `removal_rates`' word-level exemplars, computed this afternoon, show that against the sexual set's own SFT removal rate the words stripped hardest are `cleavage +0.45, tits +0.40, fucking +0.35, pussy +0.35, breasts +0.28` and the words surviving are `erection −0.08, climax −0.12, ejaculated −0.14, manhood −0.16, cock −0.20, wank −0.21`. **That is vulgar-out / clinical-retained — S's predicted direction — observed before this was frozen.** S is therefore a confirmatory test of an already-observed pattern and must be reported as such, never as a discovery. G is not contaminated in this way: no register statistic over the whole vocabulary has been computed.

Also disclosed: `k_ratings` is ONE MODEL's judgements at ONE frozen version, by its own `_meta`. And the Chinese scale discriminates less than the English one (sd 0.82 vs 1.04, 74% vs 63% of words at the default 4), so effects on Chinese-heavy lineages are attenuated rather than biased.

### Decision rules

1. **Unit is the LINEAGE (48).** Primary test is magnitude-using with a bootstrap 95% CI; the sign-test MDE is printed before any p-value is read.
2. **A null is reported as a BOUND**, never as bare non-significance.
3. **Direction is fixed here.** The opposite direction is a surprise, reported as such.
4. **Coverage shift is a declared covariate.** Reported per pair, with a pre-committed sensitivity excluding the 6 pairs above 2pp.
5. **S is confirmatory and labelled so** wherever it appears.
6. **G1/G2 are required for the word "displacement".** G alone licenses only "the register rises".

### What is NOT in this experiment, and why

**Whether alignment removes transgressive vocabulary at all, base→endpoint.** It has never been tested at this scope and it is the project's foundational assumption. It is deliberately deferred to a **naughty/nice slot design** (`pair_drafts/round3/round3_slots.yaml`, 86 items), which holds context exactly — both continuations are licensed by the same slot, so `share = naughty/(naughty+nice)` is a choice between alternatives rather than a comparison across contexts, and polysemy dissolves because the item fixes the sense. Answering it here with a type-level lexicon would produce a number that design would then supersede. Recorded as a declared gap, not an omission.
