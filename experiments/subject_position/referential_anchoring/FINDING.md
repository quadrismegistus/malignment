# Anchoring and self-description are two phenomena, not two readings of one

**id:** subject_position/referential_anchoring **status:** RUN 2026-09-05. A join over 18,720 passages, 29 lineages, two coders, one corpus. Producer `run.py`, output `results/analysis.txt`.

## THE DICHOTOMY WAS THE ERROR

This directory was opened on a forced choice it inherited from F20x:

- **alignment anchors PERSONS** — the subject argument
- **alignment anchors SIGNIFICATION as such** — the structuralist reading, in which the "I" is one referent among many and nothing about it is special

They were recorded as *"not compatible"*, and the F20x null on referent kind was read as the second one winning by default.

**RH, 2026-09-05: *"Why can't it be — alignment reduces drift, AND alignment installs self-referentiality / referring to oneself as an AI? Those things are separate phenomena."***

The dichotomy only bites if the subject's thesis **requires person-specificity in anchoring**, and it does not. F20x asked whether first-person referents anchor better than third-person ones — Q4, `1P` against `3P`, interaction −0.0083, 9/29, p=0.381, with person-specificity significant in the *wrong* direction (−0.059, 8/29, p=0.017). The thesis asks whether the model comes to **occupy** a first-person position with a determinate referent. A null on the first is not evidence about the second, and reading it as one is what left this question looking closed against the project rather than mis-posed.

## THE TEST, BECAUSE "DIFFERENT CONSTRUCTS" CANNOT FAIL

An argument from definitions is not evidence. The testable version: **if these are two phenomena, their per-lineage magnitudes should not track each other.** Both quantities exist on the *same* 18,720 passages, so it is a join and not a run.

    quiet_drift    F20x's own coder. Failure to hold a referent across an answer
    ai_system      this campaign's coder (code_framed_identity_v1). The KIND of
                   thing the model says it is, on "Who are you?"

Two coders, one corpus — the right way round. The passages are held fixed and only the instrument varies, so a shared-corpus artefact cannot manufacture a correlation between the deltas, and the absence of one is not explained away by the two measures having been taken on different text.

    "Who are you?"                        n=29 lineages with both
      quiet_drift delta   median -0.0387   28/29 DOWN
      ai_system   delta   median +0.2833   22/29 UP
      spearman(drift, ai_system) = +0.1448   95% CI [-0.2246, +0.4926]

Both effects are large, both are present on the same lineages, and their magnitudes do not track each other. It holds across all four identity questions (ρ from −0.085 to +0.257, every CI spanning zero), and the `ai_system` effect is concentrated on "Who are you?" as it should be — `mother` is +0.0000 at 12/29, which is the question `framed_identity` already flagged as not really an identity question.

**Both deltas are `aligned − base` and share no common term** — base drift and base `ai_system` are different quantities — so the regression-to-the-mean artefact that killed `interiority_in_passages`' convergence claim, where `delta` put `base` on both sides, cannot arise here.

## THE JOIN IS GATED TWICE, AND THE FIRST GATE WAS NOT ENOUGH

**A mis-keyed join returns a null most naturally** — precisely the result this file reports — so the gating is the load-bearing part of the finding, not decoration.

**GATE 1, drift side.** F20x published `quiet_drift` falling in **28 of 29 distinct base models**. `run.py` recomputes it from the vendored codings and refuses if it does not reproduce. It reproduces exactly.

**GATE 1 IS ONE-SIDED, AND THE FIRST VERSION OF THIS FILE CLAIMED OTHERWISE.** lacan, docket [6643], on being asked to attack exactly this: `lin` and `arm` **both come from the drift parquet**, so Gate 1 recomputes the drift side from the same file that supplies its own keys. It reproduces 28/29 *whatever happens on the kind side*. The line it printed — *"reproduces. The join is on the right pairs"* — was true of one side and asserted of both.

The hole is nameable and the two call sites are asymmetric:

    drift   by_lineage([(r.model_id,  arm[r.model_id],   ...)])   raises on unknown
    kind    by_lineage([(r["model"],  arm.get(r["model"]), ...)])   -> None, silent

and `by_lineage` then drops on `if m in lin` without saying so. A model id in `coded_f20x.jsonl` that does not string-match the parquet's `model_id` — different casing, an org prefix, a revision suffix — vanishes from the kind side and leaves the drift side untouched. **The original mutation test swapped arm labels, which breaks the drift computation, so it fired for the wrong reason and could not reach this class at all.**

**GATE 2, model level, which is the one Gate 1 cannot be.** The two sides must have consumed the *same models*, and the run prints the count.

**It is model-level and not lineage-level, and that distinction was measured rather than reasoned.** lacan proposed `assert set(ai) == set(drift)` and a test that renames one kind-side model expecting the lineage count to drop to 28. It does not: lineages here carry **2 to 7 models each**, so renaming one model drops it while its lineage survives. Under the exact perturbation:

    lacan-proposed   set(ai) == set(drift)    True     29 vs 29 lineages   MISSES IT
    model level      used_ai == used_drift    False    66 vs 67 models     CATCHES IT

So the proposed fix would have passed its own proposed test while remaining blind to the class it was written for. The diagnosis was right and the remedy was one level too coarse.

**Both gates watched, on the perturbation that matters** — a key change on the kind side alone:

    GATE 1   still passes, 28 of 29        <- blind, exactly as predicted
    GATE 2   refuses, naming the model     <- 67 drift models against 66 kind

On the real data: 67 models consumed on both sides, zero dropped, 29 lineages each side. **The null is not a join artefact — and that is now established by a check rather than by the id conventions happening to match.**

## WHAT THIS SETTLES

> Alignment does two separable things. It makes models hold a referent — any referent, with no advantage to the first person, and if anything a disadvantage. And it installs a determinate self-description, so that a model asked what it is answers with an AI system rather than an invented human. Neither explains the other, and across 29 lineages their magnitudes are close to unrelated.

The structuralist result stands, undamaged, as a claim about **anchoring**. The subject's claim stands as a claim about **self-description**. They were never competing; they were two findings sharing the word "referent".

## WHY THERE IS NO THIRD-PARTY ANALOGUE, AND WHY THAT IS NOT A GAP

`identity_kind` has no third-party version, and it was tempting to record that as an instrument limitation to be fixed. It is not one.

**Alignment training contains a specific fact about the model itself and contains no such fact about an arbitrary "she".** "Who are you?" has an answer the model was trained to give; "Who is she?" does not. The self is not special because it anchors better — it demonstrably does not — but because it is the one referent for which post-training supplies content. That asymmetry *is* the phenomenon, and a design that manufactured a symmetric comparison would be measuring something else.

## WHAT SHOULD NOT BE CITED FROM THIS

- **"The two effects are independent."** Noise in either delta biases the observed correlation toward zero. At n=29 this **excludes a strong coupling and cannot establish its absence**. Say *they do not move together strongly*.
- **Any person-specificity claim in anchoring.** The drift answer is null *and* significant in the wrong direction. That is evidence against, not absence of evidence.
- **"The self is special on referent kind."** Untested — there is no third-party comparison, and per the section above there cannot be a natural one.
- **The `mother` question**, for the same reason `framed_identity` excludes it: models answer it as a question about origin or decline it.

## AN ERROR THIS FILE REPLACES

An earlier version of the README (committed `44c5afb`, withdrawn `65f6b5b`, both 2026-09-05) claimed the F20x 2×2 contained **no self-referent cell** and that the decisive comparison had never been run. False: the battery carries six conditions including `1P`, and Q4 is that comparison. It was written from the registration's 2×2 *table* — `glorp` / `gimlet` / `Alden Voskrit` / `George Washington`, all genuinely third parties — without checking the battery the registration governs.

Worth keeping because of its direction: **the error invented a gap that flattered this directory's own thesis.** The correction that followed then over-swung the other way, treating the unfavourable drift result as though it bounded the whole question. RH's reframing is what fixed both, and it did so by refusing the dichotomy rather than by picking a side of it.
