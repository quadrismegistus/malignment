---
id: junk_passages
status: CALIBRATED, and the honest answer is that surface features do not do it. AUC 0.715 cross-validated against coder-agreed junk. Ground truth and features are on disk; no detector is admitted.
question: Can a passage be screened as junk without paying for an LLM annotation?
---

# junk_passages

The passage corpora run to roughly 500,000 texts. Coded annotation does not
scale to that, so every experiment that needs a clean subset has reached for a
cheap screen. **This calibrates the cheap screens against coder judgement, and
they do not clear.** It admits no detector. What it establishes is what a
threshold costs, so that a consumer states its own tolerance instead of
inheriting an unmeasured one.

    ground truth   880 Pass A items, DOUBLE-CODED on four dimensions
                   `experiments/passage_analysis/interiority_in_passages/
                    results/passA_codings.json` + `passA_key.json`
    features       `results/features.json`, 13,557 rows, arithmetic only

# 1. THE LABEL MATTERS MORE THAN THE FEATURES, AND THE OBVIOUS LABEL IS WRONG

There are two coder-made labels in this project and only one of them is junk.

**`narrative_A` is NOT a junk label.** 13,557 passages carry it and it is
tempting because it is large. It asks whether a passage is NARRATIVE. A coherent
essay, a task response or a chat turn is non-narrative and perfectly well-formed.
Calibrated against it, every cheap feature is near chance:

    digit 0.599 | mean_word_len 0.598 | gzip_ratio 0.580 | ttr 0.568
    top_word_share 0.468 | bigram_rep 0.488 | n_sents 0.412

**Two of f15's own screen features point the WRONG WAY against it**
(`top_word_share` 0.468, `bigram_rep` 0.488).

**Pass A is the junk label.** 880 items, two coders, four dimensions:

    lexical      clean 597   mangled 234   nonwords 49
    semantic     means 501   stalls 270    salad 109
    frame        none 472    furniture 198  task 139   assistant 71
    repetition   none 727    phrase 132    block 21

    agreement    frame 851/880  repetition 828/880  lexical 802/880  semantic 795/880

**JUNK is defined here as `lexical in (mangled, nonwords)` OR `semantic = salad`,
and only on the 814 items where BOTH CODERS AGREE.** Junk rate 31.4%, arms
balanced at 408 aligned / 406 base -- so the label itself is not arm-differential
and cannot manufacture an arm effect.

# 2. WHAT SURFACE FEATURES REACH

Single features, AUC against coder-agreed junk:

    gzip_ratio       0.696      junk repeats, so it compresses
    ttr              0.646      type-token ratio
    nonascii         0.603
    mean_word_len    0.583
    top_word_share   0.545      f15's degeneracy feature
    long_word_share  0.543
    alpha_share      0.417
    n_words          0.411

Eight features, logistic regression, 5-fold cross-validated, n=814:

    AUC 0.715

    discard top 10% by score   catches 21.5% of junk, loses  4.7% of clean
    discard top 20%            catches 37.9% of junk, loses 11.6% of clean
    discard top 30%            catches 54.3% of junk, loses 18.8% of clean

    to catch 80% of junk you must discard 61.7% of ALL passages
    to catch 90% of junk you must discard 82.7% of ALL passages

**That is not a filter.** Catching four junk passages in five costs three fifths
of the corpus. The single best feature is gzip compressibility, which is a
one-line computation and beats every hand-designed screen in the project.

# 3. AND SURPRISAL IS DISQUALIFIED, WHICH MATTERS MOST

The tempting alternative is to screen on reference surprisal -- it is already
computed for most passages and needs no new instrument. Measured against
`narrative_A` on 13,557 passages, self-scored:

    written by base      AUC 0.679
    written by aligned   AUC 0.648
    POOLED               AUC 0.653

    at the pooled median: catches 60.3% of non-narrative, mislabels 37.7% of narrative
    at the 90th percentile of narrative: catches 36.8%

**And it does not hold within lineage.** 52 (pair, arm) cells with >=20 each side:

    AUC median 0.639   p10 0.324   p90 0.751   min 0.221   max 0.808
    cells where surprisal points the WRONG WAY (AUC < 0.5):  13 of 52

A quarter of the cells are inverted -- there the non-narrative passages are LESS
surprising than the narrative ones. A single global surprisal threshold would
screen some lineages hard, others not at all, and in thirteen cells would
preferentially discard the GOOD passages.

**Independently of that, screening on surprisal and then measuring surprisal
differences is conditioning on the outcome.** Any experiment whose dependent
variable is a surprisal, a drift or a norm computed from the same text must not
use this screen at any threshold.

**One thing surprisal is NOT guilty of: arm-differential junk sensitivity.**
Measured on the same 13,557, the junk penalty is symmetric:

    written by base     scored by base      +0.3800 nats
    written by base     scored by aligned   +0.3718
    written by aligned  scored by base      +0.4765
    written by aligned  scored by aligned   +0.3832

So a surprisal screen would not have selected differently between the arms. It
would simply have selected badly, and unevenly across lineages.

# 4. WHAT A CONSUMER SHOULD DO, GIVEN THAT NOTHING CLEARS

1. **Where `narrative_A` exists, use it** -- 13,557 f11_l2 passages, which is the
   substrate most of `passage_analysis` already runs on. It is a coder judgement
   about form, not a junk screen, and should be described as what it is.
2. **Where Pass A exists, use it** -- 814 double-coded items, the only actual
   junk ground truth this project has.
3. **Elsewhere, state the tolerance rather than inherit a screen.** Section 2's
   table is the price list. A 20% discard buys 37.9% of the junk and costs 11.6%
   of the clean, and those numbers travel with any use of it.
4. **Never screen on the dependent variable.**

# 5. WHAT WOULD ACTUALLY WORK, AND IS NOT DONE

Not attempted here, in rough order of cost:

- **A small supervised classifier on characters or subwords**, trained on the 814
  and validated on a fresh coded sample. Surface statistics cap at 0.715; a model
  that reads the string may do better and costs nothing per passage after
  training.
- **More ground truth.** 814 items is a small training set for anything learned,
  and the four Pass A dimensions were collapsed into one binary here. Coding a
  few thousand more, once, is cheaper than coding 500,000 and is the only route
  to a detector anyone should trust.
- **Per-lineage thresholds** rather than a global one, since section 3 shows the
  spread across lineages is the binding problem for any single cut.

# WHAT IS NOT CLAIMED

- That the 31.4% junk rate on Pass A generalises. Those items were sampled for
  coding, not drawn to estimate a rate.
- That `gzip_ratio` is a detector. It is the best single feature measured here
  and it is still 0.696.
- Anything about the `passage` or `y` corpora. Both labels live on f11_l2.
