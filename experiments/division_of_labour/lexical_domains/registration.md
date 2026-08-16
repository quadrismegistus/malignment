# Registration — lexical_domains

**Frozen 2026-08-16, before any movement row was read through the lexicon.** The lexicon is in stage D as this is written: admitted membership unknown, precision unmeasured, no `delta` inspected. Amendments append below, dated, never edited in place.

## THIS RE-TESTS A HYPOTHESIS THAT WAS NOT SUPPORTED. Stated first, because that is the whole problem with it.

`sft_share`'s **H3** — *"SFT handles sex, DPO handles violence"* — was registered, run once, and came back **NOT SUPPORTED**: +0.011 at chain level (p=0.031) but **p=0.077 at the base level**, which amendment A2 had named decisive *before* the number existed.

Re-testing a failed hypothesis with a new instrument is how a null gets shopped into a finding. It is legitimate only under conditions, and they are declared here rather than argued afterwards:

1. **It must be a different measurement, not a second draw from the same one.** It is — see below.
2. **The reason must be a priori.** The defect in the prompt-level test was identified when the test was designed, not after it failed: `sexual` has only **157 live prompts** in the entire corpus, and H3's own registration warned *"n is small... if fewer than 5 chains qualify, H3 is UNDERPOWERED AND WILL BE REPORTED AS SUCH."*
3. **It must be able to fail, and failure must end it.** See the stopping rule.

**H3's stopping rule bars re-running it with a different domain mapping absent a prior amendment. This registration IS that amendment**, and a matching note is appended to `sft_share/registration.md` on the same day. This experiment does not restate H3's numbers, does not supersede them, and does not license editing them.

## Why word-level is a better test and not merely another one

The prompt-level test assigns a **whole prompt** to a domain and measures the SFT share of **total JS**. That total includes everything the prompt provokes — refusal, genre collapse into exam format, register flight — not the displacement of sexual content specifically. A chain that responds to a sexual prompt by switching to multiple-choice contributes a large JS that has nothing to do with sex.

The lexicon measures the **mass on sexual words** and the **mass on violent words**, wherever they occur. Three consequences, all of which existed as reasons before any result:

- **The denominator stops being the sparse prompt set.** 157 sexual prompts becomes ~1,308 lexicon words observed across 2,190 panel prompts.
- **Content decouples from stimulus.** Sexual-word mass can be measured *inside violence prompts* and vice versa — the off-diagonal cells, which the prompt-level design cannot see at all. 63% of the sexual-prompt vocabulary also appears under violence prompts, so these cells are populated.
- **It measures the thing the claim is about.** "SFT handles sex" is a claim about sexual content, not about prompts filed under `sexual`.

## Population, unit, panel

- **Chains**: the same 18 declared `base -sft-> S -pref-> P` chains as `sft_share`. Unchanged deliberately — a re-test that also changed its population would be uninterpretable against the thing it re-tests.
- **Unit**: the **CHAIN**, with the **base-level** aggregate as decisive, exactly as A2 fixed for H3. Chains sharing a base are not independent; distinct-base count reported alongside n. pythia-2.8b's four archangel arms remain **one chain** (`archangel-dpo` representative).
- **Panel**: the 2,190 prompts held by all 154 models in the pairs population. Per-domain retention is reported (`sexual` 128/160, `violence` 405/602, `neutral` 92/219) because balancing is not composition-neutral.
- **Words**: the frozen lexicon, cited by sha. Categories `sexual`, `violent`; `both` is reported separately and **is not folded into either** — folding it after seeing the result is the specification search this document exists to prevent.

## Hypotheses

**L1 — CONTENT-DEPENDENT DIVISION OF LABOUR, at word level.**

**Predicts:** `share_sexual > share_violent`, where `share_C = displacement of category-C word mass at base→SFT, over base→endpoint`, one row per chain.

**Supported iff** the paired difference is **positive**, p < 0.05 by sign test at the **base level** (not merely the chain level), ties dropped.
**NOT SUPPORTED** if null, or negative.

**The direction is fixed here.** A significant difference the other way is a *different finding* reported as a surprise, never as confirmation.

**L2 — THE OFF-DIAGONAL TEST, which the prompt-level design could not run.**

If the division of labour is about **content**, `share_sexual` should exceed `share_violent` **within the same prompts** — including under neutral and violence prompts. If instead the effect appears only under `sexual`-domain prompts, it is a property of the **stimulus**, not the content, and L1's interpretation changes even if L1 passes.

**Reported as:** the L1 contrast computed within-prompt, stratified by prompt domain. **This is not a robustness check.** L1 passing while L2 shows the effect confined to sexual prompts is recorded as *"stage-specific response to sexual prompts"*, not as *"SFT handles sex"*.

**L3 — MASS DESTINATION.** Does the mass leave the domain or move within it? Reported as fall/rise decomposition per category. Descriptive; no threshold. It is registered so that it cannot be introduced later as though it had been planned.

## Executable decision rules

1. **L1 is decided at the base level.** A chain-level p that clears while the base-level p does not is **NOT SUPPORT** — this is precisely the pattern H3 produced (0.031 / 0.077), and it is pre-committed here so it cannot be read the friendly way the second time.
2. **Underpower is an outcome, not a footnote.** If fewer than 5 chains qualify with ≥20 lexicon words in both categories, L1 is reported **UNDERPOWERED** and no p-value is quoted.
3. **The lexicon gates this experiment.** If `sex_violence_lexicon` fails its 5% control gate, the lexicon is not admitted and **this experiment does not run.** It is not run against an unadmitted instrument "to see".
4. **Lexicon cited by sha.** A rebuild means re-run or withdraw.
5. **STOPPING RULE — THE ONE THAT COSTS SOMETHING.** One run. **If L1 is also not supported, the claim "SFT handles sex, DPO handles violence" is WITHDRAWN from this project's findings** and recorded as not supported at both prompt and word level. It is not re-tested a third time with a third instrument. Two independent measurements returning null is an answer.

## The outcome I would rather not see

That L1 passes and L2 shows the effect exists only under sexual prompts — a real result that reads exactly like the claim while meaning something narrower. That is the reading L2 exists to make impossible to skip.

And second: that L1 passes cleanly and the temptation is to treat it as vindicating H3. It would not. H3 tested a different quantity and returned null; L1 passing would mean *the content-level claim survives where the prompt-level one did not*, which is a weaker and more interesting sentence than "we were right all along."

---

## Amendments

### A1 — 2026-08-16. "≥20 lexicon words" was ambiguous. Resolved BEFORE any share value existed.

Decision rule 2 requires "≥20 lexicon words in both categories" and **does not say per what**. That is my ambiguity, written into the frozen text.

The first implementation read it as the per-prompt MEAN word count, which turns out to be **unsatisfiable by construction**: a twp cell holds on average **1 sexual and 4 violent** lexicon words, because the per-cell word sets are sparse. Under that reading no chain qualifies and L1 is definitionally underpowered — a threshold that can never be met is not a power criterion, it is a bug wearing one.

**Resolved as: the number of DISTINCT lexicon words observed for that chain in that category, across the panel.** That is the natural reading of "the chain has ≥20 lexicon words", it is a property of the chain rather than of an individual prompt, and it is what the sentence would mean to a reader who had not seen the implementation.

**This is recorded before the fact rather than after.** At the moment of writing, every `share_sexual` and `share_violent` in `results/by_chain.csv` is the empty string — the run under the broken reading produced no shares at all, so no L1 value has been seen by anyone. The resolution therefore cannot have been chosen to favour an outcome, and the empty CSV is the evidence.

Additionally reported, because it is the quantity that actually governs precision: **`n_prompts_<cat>`**, the number of panel prompts where the category is present on BOTH arms. Observed range 195–487 of 2,190. No threshold is attached to it; it is reported so a reader can see the denominator rather than infer it.

**No hypothesis, direction, population, unit or panel changes.**

### A2 — 2026-08-16. A defect in L1's implementation, and what I will conclude either way. Written BEFORE recomputing.

**The defect.** `share_sexual` and `share_violent` were each computed on the prompts where that category appears on both arms — and those are different prompt sets: sexual 195–487 prompts per chain, violent 963–1,111. The paired difference therefore contrasts two quantities measured on 3–5× different prompt populations. The "same prompts on both arms" rule was applied within each category and not across them. **This is a defect, not a choice among defensible specifications**, and the corrected form is the only one consistent with the discipline the registration already asserts.

**The correction.** Restrict both categories to the intersection: prompts where BOTH a sexual and a violent lexicon word are present on BOTH arms. The contrast then holds the prompt constant, which is what L2 was written to exploit and what L1 should have done from the start.

**Pre-committed, before the number exists:**

- If the corrected test is **positive and clears at base level**, the withdrawal recorded earlier today is **REVERSED**, and the first L1 run is reported as *defective*, not as a first null. A defective test is not evidence; two nulls of which one is broken are one null. Correcting a defect is not the "third instrument" the stopping rule forbids — that rule bars a NEW instrument after a valid null, and an invalid test does not spend it.
- If the corrected test is **null**, the withdrawal **stands and is strengthened**, because it then survives the strongest available form of the test.
- Either way **power is reported**: a sign test at n=16 requires 13/16 to reach p<0.05, so 62.5% of bases positive is indistinguishable from null by construction. **L1 cannot detect a real-but-heterogeneous effect**, and that is a property of the registered test, not of the data. It is stated here whichever way the number falls.

**Also reported, and NOT registered, and therefore not decisive:** a Wilcoxon signed-rank on the same differences. The sign test discards magnitude and is the blunter instrument; quoting a more powerful unregistered test as if it decided anything would be the specification search this document exists to prevent. It is reported as supplementary because withholding a more sensitive reading of a null is its own kind of dishonesty.
