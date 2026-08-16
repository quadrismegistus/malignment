# Registration — register_shift

**Frozen 2026-08-16, before any movement row was read through the lexicon.** The lexicon itself is still in stage D as this is written: its admitted membership is unknown, its precision and recall are unmeasured, and no word's `delta` has been looked at. Amendments append below, dated, never edited in place.

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
