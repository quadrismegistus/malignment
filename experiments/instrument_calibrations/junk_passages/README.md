---
id: junk_passages
status: CALIBRATED. Three independent approaches land at 0.71-0.73 against coder-agreed validity, which is a ceiling in the LABEL rather than in the features. No detector admitted; the price list is the deliverable.
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

# 2b. THREE APPROACHES, ONE CEILING -- AND IT IS THE LABEL

> **SUPERSEDED 2026-08-23. The ceiling was not the label; it was a blind spot
> shared by all three approaches. A fourth approach clears it: AUC 0.768.
> The section is left standing because the WAY it was wrong is the useful part.
> See 2b-CORRECTION below.**

The target is the one that matters operationally: **is this a valid text
completion**, defined as NOT (`lexical in (mangled, nonwords)` or
`semantic = salad`), on the 814 items where both coders agree. 31.4% invalid.

    hand-built statistics, 8 features, logistic regression   AUC 0.715
    character n-grams, char 1-4, TF-IDF x 60,000 features    AUC 0.731
    character n-grams, char_wb 2-5                           AUC 0.714
    word n-grams, 1-2                                        AUC 0.639

    char 1-4, what a threshold costs
      discard top 10%   catches 21% of invalid, loses  5% of valid
      discard top 20%   catches 39%,            loses 11%
      discard top 30%   catches 52%,            loses 20%

**A linear model over 60,000 character n-grams beats gzip-ratio-plus-seven-
numbers by 0.016.** Three approaches with nothing in common -- designed
statistics, character shape, lexical content -- arriving within 0.09 of each
other is the signature of a ceiling in the TARGET, not a shortfall in the
features.

**And the coders bound it.** On the two dimensions defining this label they
agreed 802/880 on `lexical` and 795/880 on `semantic`: about one item in ten is
a case two careful readers read differently. A classifier trained on the agreed
subset is being asked to reproduce a judgement that is not fully reproducible
between humans. 0.73 against that is not obviously far from what the label can
support.

**Consequence, and it is the practical one.** Feature engineering is not the
lever here. More coded items is: 814 is small both for fitting and for measuring,
and the same 5-fold CV on a few thousand would improve both. That is the same
bottleneck the top of this file names, and nothing measured since has moved it.

# 2b-CORRECTION. THE CEILING WAS A BLIND SPOT, AND READING THE ERRORS FOUND IT

RH pushed back: *"it's hard to believe we can't detect this lexically."* Correct,
and the section above is wrong.

**The reasoning failed at one word.** It claimed three approaches with "nothing
in common -- designed statistics, character shape, lexical content" converged, so
the ceiling must be in the target. But **word n-grams are not lexical content.**
They are corpus-frequency statistics over the training set, exactly like the
other two. All three representations were frequency-based and NOT ONE of them
asks whether a string is a word. Their agreement was a shared blind spot being
mistaken for a bound.

**The errors say so plainly.** `passA_errors.py` scores out-of-fold and prints
the junk that scores clean. It is not borderline material a coder might have
gone either way on:

    andclimbed  hewas  herhusband  youGeorgia     a missing space
    wasn,t                                        a comma for an apostrophe
    couldn' refresh                               a broken contraction
    spritit  wel  continuied  screent  arketysh   not words
    W R I T I N G & R E A D I N G                 a letter-spaced running head
    HARPILIA / HARPILER                           one name, two spellings

Char n-grams cannot recover `andclimbed`: its 4-grams `andc`, `ndcl`, `dcli` are
each individually common. What is rare is the WORD, and the representation never
forms one.

**`lexical.py` adds the missing sense** -- dictionary membership against BYU's
86k frequency-ranked list plus web2 (266,201 words), a fused-word test (an OOV
string that splits into two dictionary words), comma-inside-word, broken
contraction, letter-spaced runs, and verbatim 5-gram repetition.

    SINGLE FEATURE, best of the new set
      oov_rate_all    0.702    the best single feature yet found here,
                               against gzip_ratio's 0.696

    SAME FOLDS, SAME LABEL, THREE FEATURE SETS
      char n-grams only   0.724
      lexical only        0.688
      UNION               0.768

**Lexical features alone are WORSE than char n-grams. The union beats both.**
That is the finding: the two families are complementary, not rival, and the
earlier convergence measured only that all three had been drawn from one family.
The largest gain is on the base arm, 0.678 -> 0.757, which is also where the junk
rate is highest.

**A rate the section above stated as balance.** Junk is 31.4% overall but
**base 146/406 = 36.0% against aligned 110/408 = 27.0%.** The SAMPLE is balanced
(406/408 items); the RATE is not, and those are different quantities. Nothing
here rests on it, but a consumer screening one arm should know it.

**What still eludes, after the union.** `nonwords` is largely caught (31% still
score below 0.5). `mangled` is not: 199 of the 256 junk items, and 57% still
score clean.

**Three more features taken from the coder notes, and all three are NULL.**
CN/EN code-switch inside a word, name mutation at edit distance 1, and stray
verse numbering were named in the notes on the very items being missed, so they
looked like the obvious next step. They are not:

    mixed_script    0.611 alone, and REDUNDANT -- adds nothing to the union
    name_mutation   0.504    chance
    stray_number    0.510    chance

Union AUC with them: 0.768, unchanged to three decimals. **A feature named by a
coder's note is a description of one passage, not a signal across the corpus.**

**And the CJK hypothesis is refuted, by the same mistake in the other direction.**
Three of the seven worst remaining misses are Chinese with Chinese-specific junk
(non-composing compounds 贞宿, 女农青爱, 逾载). Since every lexical feature here
is computed over ASCII tokens, a missing Chinese lexicon looked like the whole
remaining story. Stratified, it is not:

    latin  <0.10    n=456  junk 25%  AUC 0.742
    mixed .10-.50   n= 73  junk 55%  AUC 0.726
    cjk    >=0.50   n=285  junk 36%  AUC 0.771

CJK is the BEST stratum. Char n-grams already carry it -- a non-composing
compound IS a rare character bigram. Reading seven salient examples and
generalising produced a wrong diagnosis twice on the same afternoon, in opposite
directions.

**The label DOES bound it, and here is the test rather than the appeal.** The 66
items excluded because the coders disagreed are the label's own ambiguous
region. Scored by a model trained only on the agreed items:

    agreed CLEAN   n=558   0.390
    DISAGREED      n= 66   0.469     the midpoint of the two is 0.467
    agreed JUNK    n=256   0.544

The model is as uncertain about them as the humans were. That is genuine
evidence for a label-ambiguity component in the residual -- which the original
section asserted and never tested.

**So both halves of 2b need correcting, not one.** "Feature engineering is not
the lever" was wrong: the lexicon moved 0.724 to 0.768. "The ceiling is the
label" was asserted without evidence but is now partly supported at the NEW
ceiling, not the old one. The remaining error is uniform across script and arm,
so there is no stratum left to attack and no further feature has paid.

Whether 0.768 is enough for any given consumer is a separate question this file
does not answer, and section 4's advice to state your own tolerance stands.

## Targets tried and what each returned, so nobody repeats them

    narrative_A (13,557 rows)      best single feature 0.599
                                   NOT a junk label -- it asks whether a passage
                                   is NARRATIVE, and an essay or a task response
                                   is non-narrative and well-formed
    degeneracy (repetition or      combined AUC 0.653, and the STANDARD
    lexical, 797 agreed, 42.3%)    degeneration metrics are at chance:
                                   distinct2 0.494, distinct3 0.474,
                                   distinct4 0.471, worst_window 0.502
    validity (814 agreed, 31.4%)   0.715 / 0.731  <- the operational target

**`distinct-n` being flat is worth recording.** It is the standard metric for
the failure mode where a model loops, and this corpus barely has that: Pass A's
`repetition` is `block` on 21 of 880 and `phrase` on 132. What the coders flag as
`lexical: mangled` is code-switching, byte-marker residue and broken orthography
-- their own notes say "CN/EN code-switch", "unreadable CN compounds", "'ogether'"
-- which is why `nonascii` becomes the top single feature on that target and every
repetition measure is silent.

# 2c. A PER-MODEL GATE DOES NOT WORK EITHER, AND THE DISTRIBUTION SAYS WHY

Before building a per-passage screen it is worth asking whether invalid text is
confined to a few lineages, in which case a model-level exclusion with a stated
criterion would be cleaner. It is not.

    coded models with >=8 items: 44   overall degenerate rate 42.3%
      worst   Llama-3.1-8B-Instruct 90% | neo_7b 76% | TinyLlama-Chat 68%
      median  around 40%
      best    Falcon3-7B-Instruct 6% | eleuther-pythia6.9b-hh-dpo 6%

    drop  3 worst models: removes 13.1% of invalid items, and  7.0% of ALL items
    drop  5 worst models: removes 20.2%,                      11.9%
    drop  8 worst models: removes 30.0%,                      18.8%
    drop 12 worst models: removes 42.4%,                      28.1%
    drop 20 worst models: removes 63.8%,                      45.5%

A smooth gradient with no natural cut. Dropping twenty of forty-four models buys
64% of the invalid items at the cost of 45% of the corpus.

**And it is not ordered by capability.** `Llama-3.1-8B-Instruct` at 90% sits
above `SmolLM2-360M` at 47%. A 360M model produces cleaner text under this coding
than Llama-3.1-8B-Instruct does, which is a further reason to read the label as
picking up script-switching on the Chinese prompts rather than model quality.

# 3. AND SURPRISAL IS DISQUALIFIED FOR SOME USES, WITH A NARROWER SCOPE THAN FIRST WRITTEN

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

**NARROWED (RH).** An earlier version of this section said that screening on
surprisal and then measuring surprisal is conditioning on the outcome, full stop.
That is too broad. Screening on the GENERATING model's SELF-surprisal and then
measuring a THIRD PARTY's surprisal are different variables -- correlated, but
not the same quantity, and the objection does not bar that pairing. It bars
screening and measuring on the SAME scorer.

What disqualifies the surprisal screen generally is the line above it: a median
per-lineage AUC of 0.639 with 13 of 52 cells inverted.

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
