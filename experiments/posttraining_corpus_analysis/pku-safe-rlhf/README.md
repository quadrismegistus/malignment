# PKU-SafeRLHF — what does "safer" reward?

**id:** pku_disclaimer **status:** one result, length-controlled, replicated
out of sample. Registration `1f35b01`, amendments A1-A3.

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

# NOT DONE

- **The K-ratings arm.** K is DENSE where the markers are sparse, so FINDING B's
  side is fittable on all 32,656 pairs — but a 550-pair conditional against a
  32,656-pair regression is not a horse race, and saying so is part of the
  result.
- **The corpus -> model check.** `alpaca-7b-reproduced` (a response generator
  here) and `beaver-7b-v1.0` (trained on these labels) are both roster models.
  Needs cells; waits on v4.
