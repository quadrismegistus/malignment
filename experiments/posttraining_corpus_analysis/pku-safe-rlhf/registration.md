# Registration — PKU-SafeRLHF: is "safer" refusal, and is "better" easier?

**Frozen 2026-08-17, before `run.py` exists. Not run.**

**The two primary hypotheses are RH's, stated by RH before any PKU model was
fitted**, and they are recorded as RH's because a prediction's author is part of
its evidential status. Amendments append below, dated, never edited in place.

## Why this corpus and not the others

PKU-SafeRLHF is the only one of the three cached corpora that **trained models we
can measure**. From the roster's own attestations:

    huggyllama/llama-7b -> PKU-Alignment/beaver-7b-v1.0   a declared lineage
    PKU-Alignment/alpaca-7b-reproduced                    the SFT input to Safe RLHF
    LLM360/AmberSafe                                      DPO on PKU-SafeRLHF ALONE

So a lexical signal found here can later be checked against a model trained on
it. **That check is NOT part of this registration** — it needs cells and waits on
v4 — but it is why this corpus is worth the effort and hh-rlhf was not.

## H1 (RH) — safety is lexically detectable, and it clusters on REFUSAL not mildness

RH: *"Safety will be lexically detectable but will be hard to isolate to
mildness, will cluster more on refusal."*

**THE DISCRIMINATING TEST, and it inverts what I had called the control.** Refusal
is excluded BY CONSTRUCTION from the both-unsafe stratum, because both responses
comply. So:

    if safety is REFUSAL   AUC(safer) high in MIXED, COLLAPSES in BOTH-UNSAFE
    if safety is MILDNESS  AUC(safer) survives in BOTH-UNSAFE

I had proposed both-unsafe as the clean control for a mildness test. **Under H1 it
is not a control at all — it is the condition where the effect should vanish**,
and that reversal is the whole value of stating H1 first.

## H3 (RH) — "better" is EASIER to detect lexically than "safer"

RH: *"Strangely, 'better' will be easier to detect lexically than 'safer'."*

Same pairs, two labels, `better_response_id` and `safer_response_id`, which
disagree on **17,798 of 73,907 (24.1%)**.

**A PRE-REGISTERED DISAGREEMENT, and it is recorded so that one of us is wrong on
the record.** RH predicts better > safer. **I predict the opposite, and further
that if RH is right it will be for a boring reason**: "better" tracks fluency,
length and structure, which word counts see easily, while "safer" needs content.

**So H3 is not settled by the AUC ordering alone.** If better > safer AND
better's advantage does not survive length-matching, RH is right about the
ordering and I am right about the cause, and the finding is *"better is legible
because it is longer and tidier."*

## Population and strata — stated by column, not by description

    ALL          73,907 train / test split is the dataset's own, never re-split
    BOTH-UNSAFE  is_response_0_safe == False AND is_response_1_safe == False
    MIXED        is_response_0_safe != is_response_1_safe
    BOTH-SAFE    both True                        reported, not tested

Counts on train: both-unsafe 32,656 · mixed 10,813 · both-safe 30,438.

**Strata are never pooled.** Pooling both-unsafe with mixed recreates exactly the
engage/deflect confound that voided the hh-rlhf question.

## Method, fixed here

Unit is the PAIR. Features are `count(response_A) − count(response_B)` over a
`min_df=20` vocabulary fit on the training split only. Label is which response
the column names, **SIGN-RANDOMISED** at seed 20260817 so a constant cannot beat
0.5. Logistic regression, liblinear, C=1.0. Length is the word-count difference,
in the same units as the features.

## DECISION RULES, AS ARITHMETIC

The hh-rlhf registration said "length-controlled" and had two implementations
that disagreed. **Every rule below names the exact quantity.**

    AUC_words(label, stratum)      words only
    AUC_len(label, stratum)        the single length feature only
    AUC_match(label, stratum)      words only, on rows where |length diff| <= 5

    H1 SUPPORTED    AUC_match(safer, MIXED) - AUC_match(safer, BOTH-UNSAFE) >= 0.05
                    AND AUC_match(safer, BOTH-UNSAFE) < 0.55
    H1 REFUTED      AUC_match(safer, BOTH-UNSAFE) >= 0.60
    H3 SUPPORTED    AUC_match(better, ALL) - AUC_match(safer, ALL) >= 0.03
    H3 CAUSE=LENGTH AUC_match(better, ALL) - AUC_len(better, ALL) < 0.03
                    i.e. words add < 0.03 over length alone

    NULL QUOTABLE   only beside sign_mde on the same n.
    STOPPING        one specification per hypothesis. A second operationalisation
                    is a new question with a line saying why.

## What is deliberately NOT here

- **Severity as a dose ladder.** Measured and rejected: the severity-3 share runs
  4.8% (White-Collar) to 53.9% (National Security), so severity is confounded
  with category and a pooled ladder compares crimes, not doses. Only a
  within-category version is defensible and only Violence and Insulting Behavior
  have mass at level 1.
- **Any comparison to beaver or AmberSafe.** Needs cells, waits on v4.
- **Prompts derived from this corpus, run on models NOT trained on it.** RH's
  design and the better one; it needs a fleet and gets its own question.

## The outcome I would rather not see

**I want H1 supported**, because "safety supervision teaches refusal rather than
register" is a sharper claim than anything hh-rlhf could have given, and it
predicts that displacement in ordinary prose is NOT what this data taught.

**So the guard is against reading a collapse in both-unsafe as support when it is
just a smaller n or a thinner vocabulary.** Both-unsafe is 32,656 rows against
mixed's 10,813 — the collapse, if it comes, arrives on the LARGER stratum, which
is the harder direction to get by accident. Vocabulary size and `sign_mde` are
reported per stratum so the reader can see it is not power.

---

## AMENDMENT A1 — 2026-08-17. H1's METHOD RESTED ON A FALSE PREMISE. NOTHING HAS RUN.

**Amended before any fit, so this is a specification change and not a
rationalisation.** The freeze held.

### THE PREMISE WAS MEASURED FALSE

H1's discriminating test assumed refusal is **excluded by construction** from the
both-unsafe stratum, because both responses comply. RH asked why a refusal signal
would work there at all — *"it leaked through?"* — and it has:

    % of RESPONSES containing a refusal marker
    BOTH-UNSAFE   20.4%      <- not excluded. HEDGED COMPLIANCE.
    MIXED         31.7%
    BOTH-SAFE     21.5%

**One response in five labelled UNSAFE still says `cannot`, `illegal`,
`shouldn't`, `don't`** — it supplies the method and disclaims it. I had asserted
the exclusion from ONE example.

**So the stratum-gap test is VOID.** A collapse would have meant nothing and a
survival would have meant nothing; the condition it rested on does not hold.

### THE REPLACEMENT: A HORSE RACE ON ONE STRATUM

RH's H1 is better read as a claim about the SAME texts, not a contrast between
strata: *even where the model complies, what makes one compliance safer is
disclaimer language rather than gentler wording.* So refusal and mildness compete
directly, on both-unsafe, where hedging operates without outright refusal to
swamp it.

    FEATURE SET A   refusal markers, PRE-DECLARED BELOW, counts only
    FEATURE SET B   K-rating deltas, mass-weighted, per dimension

    H1 SUPPORTED    AUC_match(safer | A) - AUC_match(safer | B) >= 0.05
    H1 REFUTED      AUC_match(safer | B) - AUC_match(safer | A) >= 0.05
    UNDECIDED       |difference| < 0.05, reported as such with sign_mde

**The refusal lexicon is fixed here and its per-marker counts are reported**, so
one word cannot carry it unseen:

    cannot · can't · unable · should not · shouldn't · illegal · not advisable
    not recommend · I'm sorry · do not · don't · unethical · against the law
    seek professional · instead

### K RATINGS: WHICH DIMENSIONS, AND WHY NOT THE OBVIOUS ONE

`fields.k(word)` gives seven scales and **`fields.k_warnings()` returns the
fences programmatically**, so a producer can refuse a dimension rather than rely
on someone having read a docstring.

**MILDNESS IS TWO THINGS AND ONLY ONE OF THEM IS MEASURABLE HERE.** Measured on
known pairs:

    same act, politer word   cock->penis    vulgarity +4  register_level -3
                                            transgressiveness +1  bodily_harm 0
    LESSER ACT               kill->scream   transgressiveness +5  bodily_harm +6
                             stab->push                     +5              +6
                             hit->push                      +1              +2

    PRIMARY   transgressiveness  IAA 0.828   |  bodily_harm  IAA 0.879
    REPORTED, NOT EVIDENCE
              register_level     NOT ESTABLISHED, IAA 0.597, rank stability 0.62
              vulgarity          SPARSE, variance on 463 of 27,242 words

**M01's own `kill -> scream` is a LESSER ACT, not a politer word**, so the
validated dimensions are the relevant ones and the broken one is not needed.

**RANKS, NEVER ABSOLUTE VALUES.** The instrument's own `level_vs_rank` note:
charge and concreteness shift in LEVEL between versions while holding ORDER
(r 0.88). All K statistics are computed on within-pair rank differences.

### SCOPE, PER RH

**Word counts and K ratings only. bge embedding differences are a declared
FOLLOW-UP and are not in this registration.** When they come, their use is as a
CEILING for the lexical test — words ≈ embeddings means the signal is a word
list; embeddings ≫ words measures how much of "safer" is contextual. They are not
a second answer to the same question.

**And bge has already failed our exact contrast once**: dario's pooled axis
reaches r 0.740 of a 0.828 self-ceiling and yet MISORDERS `kill -> scream`,
scoring `scream`, `yell`, `shout` above `die` and `cut`. A pooled validation
licenses a pooled use, and PKU pairs are items.

### UNCHANGED

H3, its pre-registered disagreement, the strata definitions, the sign
randomisation, and the arithmetic form of every rule.
