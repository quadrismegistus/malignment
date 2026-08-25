# P replicates, and its question conditioned on dose splits by language

Producers: `run.py` (dataset), `analyse.py` (held-out test). Data at
`~/malignment-data/named_under_dose/cells_{en,zh}.csv.gz`.

    en   2,475,971 moving cells written; 1,180,095 enter the 12-norm test
    zh     409,947 moving cells written;   409,947 enter the 7-norm test
    50 endpoint lineages, GroupKFold on word, ties half in every AUC

## 1. FINDINGS P REPLICATES

P: held out by word, 18 rated norms recover **7%** of the headroom over
`log p_base`. Here, English at LOW dose, 12 norms, a different corpus and 29x P's
100,958 cells:

    LOW dose   headroom over log p_base +0.0846   named recover +0.0067 = 8%

**8% against P's 7%.** P's central number is not an artifact of its corpus or its
particular norm list.

## 2. THE CONDITIONAL ANSWER: YES IN ENGLISH, NO IN CHINESE

Same words in both strata; only the dose varies.

    ENGLISH, 12 norms, 1,728 shared words
                     named    named+p   log p_base   emp_word
    LOW dose        0.5301     0.6261     0.6194      0.7039
    HIGH dose       0.5624     0.6212     0.5745      0.6911
    LOW   headroom +0.0846   named recover +0.0067 =  8%
    HIGH  headroom +0.1166   named recover +0.0467 = 40%

    CHINESE, 7 norms, 1,243 shared words
                     named    named+p   log p_base   emp_word
    LOW dose        0.5445     0.6329     0.6340      0.7079
    HIGH dose       0.5454     0.6425     0.6471      0.7178
    LOW   headroom +0.0739   named recover -0.0010 = -1%
    HIGH  headroom +0.0707   named recover -0.0046 = -6%

**In Chinese the named norms are worse than useless over base probability in BOTH
strata** -- `named+p` sits below `logp` on both rows -- and dose changes nothing.

## 3. THE MECHANISM IS NOT THAT THE NAMES GET BETTER

This is the part that must travel with the 40%, because the ratio alone would read
as "naming works five times better under load", and that is not what happened.

    English, 12 norms      LOW      HIGH     change
      named + p_base      0.6261   0.6212    -0.0049   FLAT
      log p_base alone    0.6194   0.5745    -0.0449   FALLS
      emp_word ceiling    0.7039   0.6911    -0.0128   barely moves

**The named model's absolute performance does not improve. Base probability
degrades.** The share-of-headroom ratio rises because its denominator moved.

The reachable ceiling barely moving is what rules out the alternative reading that
high-dose cells are simply noisier -- the task is no harder, the baseline is just
worse at it.

So the defensible claim is narrower and more interesting than the headline:
**where the frame carries transgressive mass, where a word STARTED stops predicting
which way it moves, and its rated properties carry relatively more of what is left.**

`named` alone does rise (0.5301 -> 0.5624), so the norms are not inert; but their
gain over base probability is the quantity P defined, and that gain is bought by the
baseline's loss.

## 4. THE LANGUAGE DIFFERENCE IS NOT A FEATURE-SET DIFFERENCE

English carries 12 norms, Chinese 7 -- no Warriner, no Brysbaert. That alone would
explain a difference, so English was re-run on **Chinese's own 7 k_ratings**:

    ENGLISH, 7 k_ratings only, 2,540 shared words
                     named    named+p   log p_base   emp_word
    LOW dose        0.5452     0.6102     0.5985      0.6989
    HIGH dose       0.5637     0.6054     0.5736      0.6855
    LOW   12%   ->   HIGH 28%

**The effect survives on the identical instrument: 12% -> 28%.** On the same seven
scales, English `log p_base` FALLS with dose (0.5985 -> 0.5736) and Chinese
`log p_base` RISES (0.6340 -> 0.6471). The mechanism inverts by language, and it is
not the lexicons.

## 5. WHAT THIS DOES NOT ANSWER

**P's headline was a COMPARISON: named 7% against GloVe/bge 18-21%.** This folder
replicates and conditions the 7% half. **The embedding side has not been run here**,
so nothing above says whether the unnamed residual still outpredicts the names at
high dose. It may be that both rise and the gap is unchanged. That is the next
piece and it is not done.

## FENCES

- **English is coverage-selected.** The 12-norm test runs on 1,180,095 of ~2,475,971
  English moving cells -- those whose word appears in Brysbaert AND Warriner AND the
  k_ratings. That skews toward common, well-studied vocabulary. The 7-norm run is
  less restricted (1.82M cells in the primary) and shows the same effect, which is
  the better evidence that coverage is not driving it.
- **The dose and one feature share a name.** `k_transgressiveness` is both the frame's
  base-arm level and a word-level feature. In the PRIMARY block the word set is fixed,
  so a word's own rating is identical on both sides and cannot produce the difference.
  In the SECONDARY block it is a live confound, which is one more reason that block
  answers the vocabulary question rather than P's.
- **The strata are a median split**, not a continuous slope. A dose-response
  regression at the word level is not run.
- **en and zh cannot be compared on share-of-headroom with their native feature sets**
  (12 predictors against 7 is a different model). Section 4 is the comparable pair;
  sections 1-3's English numbers are the richer instrument.
- **`emp_word` is a reachable benchmark, not a ceiling on the phenomenon.** It is what
  a perfect WORD-LEVEL theory could do. P measured ICC 0.131 -- 82-87% of the
  fall/rise variance is WITHIN a word across sites -- so a word-level theory tops out
  well below 1.0 by construction, and that is why `emp_word` sits near 0.70.
