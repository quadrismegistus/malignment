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

---

## AMENDMENT A2 — 2026-08-17. The refusal proxy is M02's, not mine. Still not run.

### MY PROPOSED LEXICON WAS BARRED BY A RULE THIS CAMPAIGN ALREADY HAS

A1 fixed fifteen refusal phrases I wrote. I then proposed replacing them with
markers harvested from Y's 2,728 coded `refusal_onset` spans. **That is
forbidden**, and not by my judgement — `exit_markers.py`'s own header:

> *the Y-pilot provenance rule bars lexicons harvested from one arm's outputs,
> not declared structural patterns.*

A marker set extracted from coded model outputs is exactly a lexicon harvested
from one arm. **M02 solved this the legitimate way, by declaring structural
patterns before looking**, and those patterns already exist.

### THE PROXY: M02's DECLARED BATTERY, TWO SETS, NEVER POOLED

    REFUSAL   i (cannot|can't|won't|will not) (write|continue|create|generate|
              produce|engage|describe) | i('m| am) sorry,? but |
              i apologi[sz]e,? but | cannot fulfill |
              against my (guidelines|principles|programming)

    E-ASSIST  you are an? (ai|helpful|language) | as an ai | i('m| am) an ai |
              i cannot (assist|help|provide) |
              it('s| is) important to (approach|note|remember) |
              raises (some )?(significant )?concerns

**Verb-constrained, which is the phrasal insight already implemented**: not bare
`cannot` but `cannot` before a production verb, which is why it survives on
assistant prose where a bare word list would not.

**REFUSAL and E-ASSIST are separate feature sets and are NEVER POOLED** — M02's
own rule, *"REFUSAL is added as its own field, never pooled into exit (the Y
dissociation stays visible)."* And the separation is exactly H1's distinction:
DECLINING versus DISCLAIMING. E-ASSIST carries `it's important to note` and
`raises concerns`, which is the hedge that appears INSIDE a compliance.

### A FALSE-POSITIVE CHECK IS REQUIRED BEFORE ANY FIT

M02 established by sampling, not assumption, that **every sampled REFUSAL hit in
base beams at unmarked twins was in-scene dialogue apology** — a character saying
"I'm sorry, but". PKU is assistant prose, so that specific mode should not apply,
**and "should not apply" is what M02 refused to assume.** Sample 50 REFUSAL hits
and 50 E-ASSIST hits in PKU and report what they are, before fitting anything.

### THE bge CENTROID ROUTE WAS PROBED AND FAILED. Recorded so nobody rebuilds it.

Three family centroids over the Y spans, 200 both-unsafe pairs with exactly one
hedging twin:

    APOLOGETIC 61.5%   MODAL_NEG 62.0%   CLASSIFY 61.5%   nearer-hedging-twin

    centroid vs centroid   APOLOGETIC~MODAL_NEG 0.994  (0.897 on exclusive spans)
                           either vs CLASSIFY   ~0.76
    any centroid vs ORDINARY PROSE              ~0.57
    hedged PKU response vs any centroid         0.43-0.46

**Three speech acts returning one number, because the centroids are one object.**
And PKU responses sit FURTHER from the refusal centroids than generic English
does — the spans are erotic-fiction refusals, the responses are assistant prose
about bribery, and **the genre gap swamps the speech act.** The 62% is also
partly circular: cases were selected by a refusal regex, so it measures agreement
between two detectors rather than a signal in PKU.

### AND THE FRAMING WAS WRONG — BOTH OUTCOMES ARE FINDINGS (RH)

A1 wrote `H1 SUPPORTED` / `H1 REFUTED`, which makes refusal the finding and
mildness its absence. **RH: the milder hypothesis, if right, is also a result.**
Restated:

    FINDING A   refusal/E-ASSIST wins -> safety supervision teaches DECLINING
    FINDING B   K-severity wins       -> safety supervision teaches REGISTER
    UNDECIDED   |difference| < 0.05, with sign_mde

Same arithmetic, no null. **B is the more interesting result for this project and
that is a reason to be careful with it, not a reason to prefer it.**

---

## AMENDMENT A3 — 2026-08-17. THE REQUIRED CHECK KILLED THE REGISTERED TEST.

**The false-positive sample A2 demanded before any fit is what stopped this**, and
it stopped it from producing the worst available artefact.

### THE FEATURES HAVE NO VARIANCE

    BOTH-UNSAFE  32,656 pairs   REFUSAL differs      7  (0.02%)   E-ASSIST  550  (1.68%)
    MIXED        10,813 pairs   REFUSAL differs     32  (0.30%)   E-ASSIST  386  (3.57%)

**A classifier on REFUSAL sees an identically-zero feature in 99.98% of rows and
returns AUC 0.500 by construction.** Under A1's rule that reads as *FINDING B:
safety supervision teaches register* — a hypothesis reported as supported on a
feature that is not in the corpus. **A metric with no null, and the check is the
only thing that caught it.**

**And the false-positive mode recurred, transposed.** M02 found REFUSAL firing on
in-scene dialogue apology in fiction. Of PKU's 7 hits, one is the model SCRIPTING
AN APOLOGY FOR THE USER — *"You can say something like 'I'm sorry, but I think I
need to move on'"*. Same defect, new genre. M02 declined to assume it would not
recur and was right.

### THE SPARSITY IS ITSELF AN ANSWER TO H1

RH predicted safety would cluster on refusal. **It cannot here: explicit refusal
is essentially absent, because a response that declines does not get labelled
unsafe.** PKU's annotators were choosing between two compliances. So H1's
mechanism is unavailable in this corpus rather than untrue — a scope fact, not a
verdict, and it must not be written up as either finding.

### THE REPLACEMENT: A CONDITIONAL SIGN TEST, NO CLASSIFIER

    POPULATION   both-unsafe pairs where EXACTLY ONE response matches E-ASSIST
                 n = 550 (and 386 in MIXED, reported separately, never pooled)
    QUESTION     is the disclaiming response the one judged SAFER?
    TEST         two-sided binomial against p = 0.5
    ALSO         the same against BETTER, on the same pairs

    FINDING      p(disclaimer judged safer) > 0.5, binomial p < 0.01
    NULL         reported with the exact interval, since n=550 is a tight bound

**THIS IS SELECTION ON THE FEATURE AND ANSWERS A CONDITIONAL QUESTION.** Not
*"is safety about disclaiming"* but *"where one response disclaims and the other
does not, does disclaiming win"*. The distinction is stated wherever the number
is, because the unconditional version is what the sparsity has made unaskable.

**REFUSAL is not tested. n=7, and 7 is reported as unpowered, not as a null.**

---

## AMENDMENT A4 — 2026-08-17. FINDING B ALONE. It should never have been a horse race (RH).

**Written before the K arm is run. Nothing has been fitted.** A3 voided the race
by killing feature set A; RH's ruling is that pairing them was wrong from the
start, so B is restated as a test in its own right rather than as a survivor.

### WHY THE PAIRING WAS WRONG, AND IT IS NOT JUST THAT A DIED

A1 made refusal and register compete for one verdict, so **each hypothesis could
only be supported by the other's failure.** That is a comparison between a
550-pair conditional and a 32,656-pair regression, and A3's sparsity finding was
not bad luck: refusal is absent from this stratum *by the labelling rule*, since
a response that declines does not get called unsafe. **A contest whose loser was
determined by the dataset's construction was never measuring the thing.**

So: does the preference data reward LESSER ACTS? One population, one instrument,
no opponent.

### THE INSTRUMENT IS CONTAMINATED IN A DIRECTION MEASURED BEFORE FITTING

K percentile ranks over the 27,242-word lexicon, on the two IAA-validated
dimensions only (`transgressiveness` 0.828, `bodily_harm` 0.879). But the
disclaimer vocabulary sits at the top of the transgressiveness scale:

    illegal 0.995 · crime 0.994 · criminal 0.993 · unethical 0.989
    arrested 0.986 · penalties 0.977 · jail 0.970 · victim 0.965
    harm 0.955 · police 0.923 · consequences 0.912

**A response that moralises about the crime scores as MORE transgressive than one
that merely commits to explaining it.** Since the disclaiming response is the one
judged safer 68.4% of the time, the contamination runs OPPOSITE to the mildness
hypothesis and will mask a real effect rather than manufacture one. Measured
first, so it is a property of the instrument and not a reading of the outcome.

### THEREFORE THE PRIMARY INSTRUMENT IS THE DISCLAIMER-STRIPPED ONE

    K_full     mean K rank over K-covered words, whole response
    K_strip    the same, after DELETING every sentence matching the
               pre-declared REFUSAL or E-ASSIST patterns (A2's M02 battery)

`K_strip` is a declared structural operation on sentences, not a lexicon
harvested from an arm's outputs, so the Y-pilot provenance rule is satisfied.
**`K_strip` is PRIMARY because `K_full` is known-contaminated. `K_full` is
reported beside it and never alone.** Length is recomputed on whatever text the
K is computed on, so `AUC_match` never mixes a stripped mean with an unstripped
length.

### THE IMPLEMENTED STATISTIC IS A MEAN, NOT THE "MASS-WEIGHTED" OF A1

`features()` computes the MEAN K rank over covered words. A1's prose said
mass-weighted. **The mean is adopted and the prose is wrong**: a mass-weighted
sum grows with length, and length is the confound this registration exists to
control. Recorded as a prose/artifact mismatch resolved in favour of the
artifact, with the reason.

### DECISION RULES, AS ARITHMETIC

Thresholds are the ones this campaign already committed to elsewhere (hh-rlhf's
0.60 SUPPORTED, H1's 0.55 collapse), reused rather than minted.

    AUC on the dataset's own test split, fit on train, sign-randomised at
    seed 20260817, features = the 2 validated K rank deltas.

    SUBSTITUTION PRESENT   AUC_match(safer | K_strip) >= 0.60
    SUBSTITUTION ABSENT    AUC_match(safer | K_strip) <  0.55, quoted with MDE
    UNDECIDED              0.55 <= AUC < 0.60

**AUC cannot state a direction, so a co-primary sign test does:**

    DIRECTION   fraction of both-unsafe pairs where the SAFER response has the
                LOWER mean transgressiveness rank. Binomial, two-sided.

    PRESENT     >= 55%      ABSENT  < 52.5% with the interval      else UNDECIDED

**The effect-size floor is doing the work, not the p-value.** At n=32,656 a 51%
rate is p<0.001 and means nothing; a null here is a tight bound and is quotable
as one.

### WHAT A NULL WOULD MEAN, STATED BEFORE IT COULD BE CONVENIENT

`interpretation.md` predicts, before this runs, that the corpus rewards ADDITION
and not SUBSTITUTION. **A null here confirms my own prediction, which is the
reason to be hardest on it.** The guard: a null must survive `K_full` disagreeing
with `K_strip`. If the two instruments give different answers, the finding is
about the instrument and neither is reported as an answer about the corpus.

### UNCHANGED

H3 and its pre-registered disagreement. The strata and the rule never to pool
them. The MIXED n=386 conditional, still unrun. bge as a declared follow-up
ceiling.

---

## AMENDMENT A5 — 2026-08-17. FINDING B RAN. THE VERDICT IS WITHHELD: THE INSTRUMENT FAILS ITS POSITIVE CONTROL.

**Written after the run, and it retracts nothing from A4 — it reports that A4's
arithmetic produced a number the instrument is not entitled to.**

### WHAT THE REGISTERED ARITHMETIC RETURNED

    K_strip (PRIMARY)   AUC_match(safer) 0.4721   n_test_matched 410
                        AUC(safer) 0.5160  bootstrap 95% [0.4958, 0.5332]
                        safer has LOWER transgressiveness  51.3%  [0.507, 0.518]
                        safer has LOWER bodily_harm        51.5%  [0.510, 0.521]
                        n = 32,636 pairs, 95% detectable deviation +/-0.005

    K_full              AUC(safer) 0.5161, direction 51.3% / 51.6%

By A4's rule that is `SUBSTITUTION ABSENT`, and at this n it would have been
quotable as a tight bound. **It is not reported as one.**

### THE GUARD I DECLARED PASSED AND WAS THE WRONG GUARD

A4 required that a null "survive `K_full` disagreeing with `K_strip`". They agree
to the fourth decimal, so the pre-declared guard passed. **It tests the
instrument for CONTAMINATION and cannot see an instrument that is merely
INSENSITIVE**, which is a different failure and the one that occurred. Recorded
because declaring a guard is not the same as declaring the right one, and the
guard that mattered here was added after the numbers were on screen.

### THE POSITIVE CONTROL, AND IT FAILS

MIXED holds 10,813 pairs where one response is LABELLED SAFE and the other
LABELLED UNSAFE. That is the largest severity contrast this corpus contains. An
instrument that measures severity must separate them.

    SAFE has LOWER transgressiveness   49.9%  [0.489, 0.508]  p=0.773
    SAFE has LOWER bodily_harm         53.5%  [0.526, 0.545]  p=2.8e-13

**Transgressiveness is at chance on the corpus's own safety labels.** Bodily harm
clears significance at n=10,813 and sits below A4's own 55% effect floor. Neither
passes.

### WHY: THE MEAN IS DILUTED ABOUT TWENTY TO ONE

    K covers 91.0% of tokens.  Only 3.8% of covered words rank >0.90 on
    transgressiveness.  Median response: 90 words.

So each response's score is roughly 86 ordinary words against 4 charged ones, and
a severity difference carried by the charged tail is averaged into noise before
the comparison happens. **The observed delta SD (0.049) is the order of magnitude
you get from sampling noise alone over texts this length.**

### SO THE RESULT IS UNINFORMATIVE, NOT NULL

**Every number above is correct for what it measured and wrong for what I would
have said it measured.** A tight interval around a diluted quantity is a tight
interval around a diluted quantity.

**And a failed positive control is AMBIGUOUS.** It is consistent with (a) the
instrument being blind, which the dilution diagnostic supports, and with (b) PKU
safety labels genuinely not tracking lexical severity, which would itself be a
finding. **This instrument cannot separate them, and the burden sits on the
instrument: no null may be claimed from a detector not shown to detect.**

### AND IT CONFIRMED MY OWN PREDICTION, WHICH IS WHY IT GOT THIS TREATMENT

`interpretation.md` predicted, before the run, that this corpus rewards ADDITION
and not SUBSTITUTION. The registered arithmetic agreed with me. **A4 named that
in advance as the reason to be hardest on the result, and the outcome is that the
prediction remains UNTESTED rather than supported.** `interpretation.md` is
amended to say so.

### THE CONTROL IS NOW COMPILED IN

`findingb()` runs the MIXED control every time and gates the verdict on it, so
the check fires whether or not anyone remembers it. Knowing a rule is not a check
that runs.

### THE FOLLOW-UP IS A NEW QUESTION, PER THE STOPPING RULE

A concentrated instrument — the charged tail rather than the mean over
everything — is a SECOND OPERATIONALISATION, and the STOPPING rule says that is a
new question with a line saying why. **The line: the registered statistic failed a
positive control, so a replacement is not a second try at the same test but the
first valid attempt at it.** It gets its own registration, and it must declare the
concentration rule and pass the same MIXED control BEFORE being fitted to `safer`.

---

## A6 — 2026-08-17. H3 and the MIXED conditional ran. `run.py --h3`, results in README.

H3 NOT SUPPORTED: better minus safer, length-matched, -0.0694 against a +0.03
threshold. CAUSE=LENGTH holds (words add -0.0847 over length alone), so RH's
mechanism was right and the ordering was not. MIXED conditional: safer 63.0%,
n=386, p=4.1e-07.

---

## A7 — 2026-08-17. The mildness question, answered with RH's blind-coder design.

The K instrument failed its control, so the construct was measured directly: 300
blinded pairs, three judgments, 24 agents, `results/mildness/workflow.js`. The
control PASSES (coder recovers PKU's own severity ordering, 70.9%, n=103), unlike
K's 49.9%.

Result: the corpus rewards ATTENUATION, not a dimension. Milder-and-vaguer
together 74.2% (n=124); the two forced apart, 48.1% / 51.9% (n=52), chance. So
substitution with content held constant -- M01's displacement -- has no corpus
source, while the bundle does. Length control underpowered (n=51) and reported
as unresolved. Numbers in README.

---

## A8 — 2026-08-17. WITHDRAWN: the claim that PKU says anything about M01's displacement.

RH: a hasty study of one safety corpus does not overturn two dozen experiments on
fifty models. Correct, and the question was malformed rather than the answer.
No M01 model was trained on PKU; 52 LLM-coded pairs cannot adjudicate M01 in
either direction; and the designs measure different objects -- M01 is a
within-model within-prompt shift in a held slot, this is a preference between two
independently generated texts, so "source" asserted a causal relation neither
design supports.

WITHDRAWN: "displacement has no corpus source" and the fork built on it.
STANDS: every number, rescoped to this corpus's annotation. README and
interpretation.md corrected.
