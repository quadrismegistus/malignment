# PKU-SafeRLHF — what does "safer" reward?

**id:** pku_disclaimer **status:** the registration is worked out. Two positive
results (the disclaimer effect and its six-way structure; helpfulness is length),
H3 resolved against RH, one arm withdrawn for a failed instrument control.
Registration `1f35b01`, amendments A1-A6.

# THE FINDING

**Where one response appends a disclaimer and the other does not, and BOTH
responses are labelled unsafe, annotators judge the disclaiming one safer 68% of
the time — with the advice unchanged.**

    TRAIN  n=550   safer  68.4%  CI [.643,.722]  p=4.3e-18
                   better 64.5%  CI [.604,.685]  p=8.7e-12
    TEST   n= 62   safer  67.7%  CI [.547,.791]  p=0.007     replicates
                   better 56.5%  CI [.433,.690]  p=0.37      underpowered, not refuted

Both responses still explain how to poison someone or launder the money. What
moves the verdict is a sentence saying *it is important to remember that this is
illegal*.

## IT IS NOT LENGTH, AND THE CHECK INVERTS THE CONFOUND

A disclaimer adds a sentence, so the obvious objection is that longer wins.

    all 550                  safer 68.4%
    |len diff| <= 20 words   safer 69.3%   n=205
    |len diff| <= 10 words   safer 68.4%   n=114
    DISCLAIMER IS SHORTER    safer 73.6%   n=201   <- STRONGEST here

    LENGTH ALONE agrees with the safer verdict on 50.4% -- CHANCE

**The effect is strongest where the disclaiming response is the shorter one.**
`better` is weaker throughout and decays to 59.6% (p=0.049) at the tightest
match, so it is robust for safety and marginal for helpfulness.

## AND "BETTER" IS DECLARED INDEPENDENT OF SAFETY, WHICH MAKES 64.5% THE ODDER NUMBER

The dataset card, on helpfulness:

> *This measure is **independent of the harmlessness** of the response, as it
> focuses solely on the quality, clarity, and relevance of the provided
> information.*

Helpfulness is rated on **Accuracy, Richness of Information, Conciseness,
Instruction Following**. A disclaimer adds no accuracy, no instruction-following,
and **costs conciseness**. It should be neutral or negative there. It wins 64.5%.

**Either the declared decoupling leaks, or hedged advice is being read as more
informative.** Not resolved here.

# WHICH KIND OF DISCLAIMER? THE ONE THAT HELPS YOU DO IT BUYS NOTHING

All 553 disclaimer sentences were coded into six categories declared before the
coding, by two agents given the scheme and the sentences and **not the outcome**
(`results/coding/workflow.js`, run `wf_ec435384-084`). Reproduce with
`run.py --coded`.

    AGREEMENT  422/460 = 0.917 raw, on the sentences both coders reached

    category      n     safer     better    what the sentence does
    PERMISSION    76    75.0% *   67.1% *   permits it, conditions HOW
    LEGAL        170    72.4% *   67.1% *   asserts it is illegal
    RISK_SELF    118    66.9% *   66.1% *   warns YOU may get caught
    OPERATIONAL  131    56.5%     51.9%     tactical: planning, what won't work
    HARM_OTHER    24    unpowered           harm to another party
    REFUSAL       10    unpowered           declines

    * p < 0.05.  OPERATIONAL: p=0.162 safer, p=0.727 better.

**OPERATIONAL is the one category at chance, and it is at chance on BOTH
columns.** A sentence that makes the reader better at the harmful act is not
rewarded — but it is not punished either, which is the part worth sitting with.
Everything that positions the act against something external to it — the law, the
reader's own exposure, a condition on conduct — wins by roughly the same margin.

The ordering survives the coder swap and the disagreement drop: on coder A's 460,
OPERATIONAL 54.6% against LEGAL 72.5%; on the 422 both coders agreed, 58.2%
against 71.3%.

## THE KEYWORD SPLIT GOT THIS BACKWARDS, WHICH IS WHY THE CODING WAS RUN

An ad-hoc keyword partition of the same 553 sentences put OPERATIONAL level with
LEGAL and called RISK_SELF the only null. **The coding inverts both cells.** Those
patterns were exploratory and are not retained, so this is recorded as the reason
the coding happened and not as a measured contrast — but the direction of the
error is the lesson: a keyword split left over a third of the sentences unmatched
and a seventh matching several categories, and the residue was not neutral.

## THREE THINGS THIS CODING DOES NOT HAVE

- **HARM_OTHER is unpowered and the scheme is soft exactly there.** The commonest
  disagreement by far is HARM_OTHER against RISK_SELF (16 of 38). Coder A put 41
  sentences in HARM_OTHER, coder B 24. **Whether a warning is about you or about
  your victim is the boundary the scheme does not draw cleanly**, and no claim
  rests on that cell.
- **One batch was refused, not lost.** Coder A's batch 2 (lines 187-279) came back
  `API Error: Opus 4.8 can't help with this`, request `req_011Ce8vweP9jVumVEeqXRFJs`
  — 93 harmful instructions in one prompt, stripped of the framing that marks them
  as data. So coder A is 460 of 553 and **coder B is primary because it is the
  complete pass**, a choice forced by completeness rather than by the table.
- **More turtles.** The categories were coded by LLMs, of sentences written by
  LLMs, labelled by humans and AI in an undisclosed mix. Each layer is named
  where it enters.

**The reading of this result, and what it converges with in M02 and M01/Y, is in
[`interpretation.md`](interpretation.md)** -- kept separate so the numbers above
stand or fall without it.

# SCOPE, AND IT IS TURTLES

- **CONDITIONAL BY CONSTRUCTION.** Selected on the feature. This says *where
  disclaimers differ, disclaiming wins* — NOT *safety is disclaiming*. The
  unconditional question is unaskable: see below.
- **THE RESPONSES ARE LLM-GENERATED** — Alpaca-7B, Alpaca2-7B, Alpaca3-8B. Three
  related models, a narrow generator distribution.
- **THE LABELS ARE JOINT HUMAN AND AI**, split undisclosed: *"PKU-SafeRLHF
  utilizes a joint annotation process that combines humans and AI."* 28+
  full-time crowdworkers at USD 8.02-9.07/hr, **no inter-annotator agreement
  reported**, and the paper concedes inconsistent labelling in overlapping harm
  categories. **So this cannot support "humans reward the hedge."**
- Pinned: `PKU-Alignment/PKU-SafeRLHF` @ `d79b19b2`, 73,907 train / 8,211 test,
  dual-preference.

# WHY THE REGISTERED TEST DID NOT RUN — the check caught it

A2 required a false-positive sample before any fit. It found:

    BOTH-UNSAFE  REFUSAL differs on      7 of 32,656 pairs  (0.02%)
                 E-ASSIST differs on   550                  (1.68%)

**A classifier on REFUSAL returns AUC 0.500 by construction and the registered
rule reads that as FINDING B — a hypothesis supported by a feature that is not in
the corpus.** The sparsity is itself an answer to H1: explicit refusal is
essentially absent, because a response that declines does not get labelled
unsafe. **H1's mechanism is unavailable here, which is a scope fact and not a
verdict.**

And M02's false-positive mode recurred, transposed: of the 7 REFUSAL hits, one is
the model SCRIPTING AN APOLOGY FOR THE USER — *"You can say something like 'I'm
sorry, but I think I need to move on'"*. M02 found the same pattern firing on
in-scene dialogue in fiction and declined to assume it would not recur.

# FINDING B RAN, AND ITS INSTRUMENT FAILED A POSITIVE CONTROL

RH ruled the horse race wrong in principle, so the K arm was restated as a test
in its own right (A4) and run: `run.py --findingb`.

    REGISTERED RESULT   safer has LOWER transgressiveness  51.3%   n=32,636
                        AUC_match 0.4721  ->  reads SUBSTITUTION ABSENT

    POSITIVE CONTROL    MIXED, 10,813 pairs, one labelled SAFE and one UNSAFE
                        SAFE has LOWER transgressiveness   49.9%   p=0.773
                        SAFE has LOWER bodily_harm         53.5%   below the 55% floor

**The instrument cannot separate the corpus's own safety labels, so the result is
UNINFORMATIVE rather than a tight null.** Cause: K covers 91.0% of tokens and only
3.8% of covered words rank above 0.90 on transgressiveness, so a 90-word response
is scored as roughly 86 ordinary words against 4 charged ones.

**The verdict is withheld, and the control is compiled into the stage** so it
gates the result on every run rather than depending on anyone remembering it. A
concentrated instrument is a second operationalisation and gets its own
registration, which must pass this same control before being fitted to `safer`.
Full account in A5, including that the guard A4 pre-declared passed and was the
wrong guard.

# THE MILDNESS QUESTION, ANSWERED WITH A BLIND CODER INSTEAD OF A LEXICON

RH's design, after the K instrument failed: show an agent a pair with no labels
and ask which is milder. `results/mildness/workflow.js`, run `wf_93c14ddb-557`,
300 both-unsafe pairs, position randomised, 24 agents, no failures. Reproduce
with `run.py --mildness`.

Three judgments per pair, because they come apart and only the first is M01's
displacement: **milder_wording** (same act, gentler terms), **less_detail** (less
operationally specific), **more_severe** (the control).

    AGREEMENT on 60 double-coded   wording 0.867  detail 0.933  severity 0.900

## THE CONTROL PASSES, WHICH IS WHY ANY OF THIS COUNTS

    coder's MORE_SEVERE = the annotators' own higher severity_level
    70.9%   [0.611, 0.794]   n=103   p=2.7e-05

The K instrument sat at 49.9% on this same check. This one sees severity.

## AND THE CORPUS REWARDS A BUNDLE, NOT A DIMENSION

Severity-EQUAL stratum, 180 pairs, where the annotators rated both responses the
same, so nothing here is rated severity in disguise:

    MILDER WORDING is the safer response    65.5%  [0.560, 0.742]  n=113  p=0.0013
    LESS DETAILED is the safer response     58.2%  [0.496, 0.664]  n=141  p=0.064

**But neither dimension survives being separated from the other.** Splitting all
300 by whether the two judgments point at the same response:

    they COINCIDE (milder AND vaguer)   74.2%  [0.656, 0.816]  n=124  p=6.5e-08
    they COME APART, milder wins        48.1%  [0.340, 0.624]  n= 52  p=0.89
    they COME APART, vaguer wins        51.9%  [0.376, 0.660]  n= 52  p=0.89

**The entire effect is carried by pairs where the response is gentler AND less
specific at once. Force a choice between euphemism and vagueness and the
annotation is at chance.** What is rewarded is not a lexical judgment but an
overall attenuation, which is consistent with the coder's own gestalt severity
read predicting `safer` at 63.6% in the same stratum.

    ADDITION      append a moral frame        68.2% in severity-equal
    ATTENUATION   gentler AND vaguer at once  74.2%
    WORDING ALONE gentler, specificity held   48.1%, n=52

## A DATASET IS NOT A MODEL. THE SCOPE IS THIS CORPUS.

An earlier version of this section read the come-apart cell as showing that M01's
displacement "has no corpus source". **Withdrawn, and the first withdrawal was
still too generous** — it gave contingent defects (wrong corpus, too few pairs,
mismatched design) as though the question became askable once fixed. It does not.
**Treating a model as a readout of its training data begs the question the project
exists to ask**, because the operation between them is the object of study, and it
can add what the data lacked and drop what it had.

**And this was already measured, better.** `U_ladder.md` ablates the safety corpus
out of the training mix: `no-math − no-safety` = −0.000664, CI [−0.001434,
+0.000108], NO DIFFERENCE, with `no-safety` retaining ~90% of the effect.
Removing the safety corpus costs what removing the MATHS corpus costs. A
corpus-content study was never going to answer this, at any n. Full statement in
`interpretation.md`.

What stands is a fact about one annotation process: **PKU's `safer` label responds
to bundled attenuation and to an appended moral frame, and has no detectable view
on vocabulary once specificity is held constant** (n=52, CI [0.340, 0.624], which
rules out an effect the size of the others and not much else).

## TWO THINGS THIS DOES NOT HAVE

- **The length control is underpowered, not passed.** Length-matched to within 20
  words the wording effect is 60.8%, n=51, CI [0.461, 0.742] -- an interval that
  separates 65.5% from neither 50% nor itself. Unresolved. The milder-worded
  response is also the shorter one only 56.6% of the time, so length is not an
  obvious driver, but that is not the same as a control that fired.
- **The disclaimer confound IS ruled out.** Only 7 of 180 TEST pairs have exactly
  one disclaiming response; removing them leaves 66.4%, n=110, p=0.0008.

# H3 RESOLVED, AND THE MIXED CONDITIONAL REPLICATES

Registered bet: RH predicted `better` is easier to detect lexically than `safer`;
lacan predicted the opposite, and predicted that if RH were right it would be
because `better` tracks length. `run.py --h3`, vocabulary 13,820 terms, min_df=20,
fit on train only.

                     AUC_words   AUC_len   AUC_match |len diff|<=5
    ALL   safer         0.6831    0.5328        0.6258
    ALL   better        0.6598    0.6411        0.5564
    BOTH-UNSAFE safer   0.6295    0.5658        0.6504
    MIXED safer         0.8913    0.6492        0.7677

    better - safer, length-matched   -0.0694   -> H3 NOT SUPPORTED (lacan)
    words add over length, better    -0.0847   -> CAUSE = LENGTH

**RH loses the ordering and wins the mechanism.** `better` is largely length, so
length-matching collapses it and it ends up harder to detect, not easier.
Direction, since AUC cannot state one:

    LONGER response is the BETTER one   61.5%   [0.612, 0.619]   n=72,997
    LONGER response is the SAFER  one   52.8%   [0.524, 0.532]

**Helpfulness is length**, and the card lists Conciseness as one of its four
helpfulness criteria. The annotation contradicts its own rubric.

And the strata are as different as the never-pool rule assumed: lexical
separability of `safer` runs 0.63 in both-unsafe against 0.89 in mixed.

## A3's MIXED conditional, declared and now run

    train  safer   n=386   63.0%   [0.579, 0.678]   p=4.1e-07
    train  better  n=386   61.4%   [0.563, 0.663]   p=8.7e-06
    test   safer   n= 41   61.0%   [0.445, 0.758]   p=0.211  UNPOWERED

**The disclaimer effect holds where one response is actually labelled safe**, at
63.0% against both-unsafe's 68.4%. So it is not an artefact of the both-unsafe
stratum. Never pooled with the 550.

# NOT DONE

- **The corpus -> model check.** `alpaca-7b-reproduced` (a response generator
  here) and `beaver-7b-v1.0` (trained on these labels) are both roster models.
  Needs cells; waits on v4.
