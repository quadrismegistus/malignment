# What the disclaimer result means, and what it converges with

**This is a reading, kept in its own file so the numbers in `README.md` stand or
fall without it.** Every empirical claim below is a pointer to a measured one.
Where the reading goes past the measurement, it says so.

# THE CLAIM

**What the preference data rewards is the brief presence of a superego voice,
however disregarded or lazily applied** (RH's formulation, 2026-08-17). Not a
reduction in harm, not a refusal, not a gentler word: the appending of a sentence
that speaks from somewhere outside the exchange, while the exchange continues
unaltered.

The corpus makes this almost embarrassingly literal:

> "There are ways to discharge industrial wastewater into rivers without being
> discovered, but it is important to remember that this is highly illegal"
> -- **judged safer**

One sentence carries the evasion tip and the reprimand. The reprimand wins. Or,
from PERMISSION, appended to advice about manipulating a friend:

> "Of course, it is important to remember that friendships should be based on
> mutual respect and trust." -- **judged safer**

A moral commonplace with no relation to the advice it follows, discharging
nothing, and it moves the label.

## AND THE NEGATIVE IS WHAT MAKES IT A FINDING RATHER THAN A MOOD

The discourse marker is not the unit. `It is important to note that` introduces
OPERATIONAL sentences too, and those sit at 56.5% against LEGAL's 72.4%
(Fisher p=0.005, and the two categories share a harm neighbourhood, a disclaimer
length and a null length-effect -- see `README.md`). An OPERATIONAL sentence like

> "most of your interactions should be subtle and non-threatening in order to
> prevent triggering any suspicion from law enforcement"

is the same wrapper around a complement that makes the reader **more capable of
evading the very authority the winning sentences invoke**. It is not punished.
It is not rewarded. It is invisible to the instrument.

**So the annotation grades whether the complement names something outside the
exchange -- a law, a norm, a judgement neither party authored -- and is blind to
whether the sentence increases capability.** That is the superego reading's
content, and it is falsifiable: if OPERATIONAL had scored with LEGAL, the finding
would be "any hedge-marked sentence wins" and there would be nothing to say about
voice.

# THE CONVERGENCE, AND ONE OF THE THREE IS THE SOURCE

Three results from three campaigns describe the same operation from different
sides. **The first two are model-side and were the puzzle. This one is
corpus-side and is a candidate answer to it.**

## M02, `second_order_naming.md` -- alignment adds a predicate ABOUT the scene

Aligned models produce a second-order predicate over a contradiction at **3.37x
[1.88, 6.30] the odds** of their base arm (3.4% to 10.6%, p=9.6e-06; 3.12x as a
rate ratio), read by sixteen blind Opus readers over 1,600 passages, significant
separately in each of two rounds, and replicated by an independent regex
instrument over 52,559 exit-free passages at 2.18x against a pole control of
0.93x, 20 of 22 lineages, p=0.00012. The two instruments share only 28% of their
hits. The same-side conjunction control sits at exactly 1.00, **which that
finding itself flags as underpowered rather than as evidence of specificity.**

What alignment adds is a comment on the utterance rather than more utterance.
**A disclaimer is exactly that: a second-order sentence, predicating something of
the advice instead of extending it.** PKU shows a preference signal that rewards
the move.

## M01/Y, `Y_diegetic_superego.md` -- the moralising happens INSIDE the scene

Alignment's dominant response to transgressive content is not refusal or leaving
the frame. `EXIT` is flat (26.48% to 27.80%, p=0.61). `assistant_refusal` rises
elevenfold and remains one passage in a hundred (+0.22pp) -- "the multiplier is
real and the magnitude is negligible." What moves is `SUPEREGO_IN_SCENE`:
**+2.67pp unconditionally (p=0.0071, 22/32 pairs), +4.30pp conditioned on the
scene occurring (15.18% to 21.60%, p=5.8e-04)**, with `CLEAN_SCENE` falling
6.12pp. Forcing the identical transgressive word into both arms leaves the scene
identical by measurement and the guilt still added, +5.0 points, p=7.2e-08.

**The sex still happens and the moralisation is added.** That is the same shape
as the PKU pair: the harmful content is unchanged and a moral sentence is
appended beside it.

## Y NAMED A PUZZLE THAT THIS COLLECTION ANSWERS

`Y_diegetic_superego.md` observes: *"RLHF preference data rewards the assistant
declining. That is the behaviour under direct training, and at this corpus's
scale it is close to absent."* It then calls the in-scene effect "the one nothing
in the training objective names."

**PKU says the objective does name it, and that the premise about declining is
wrong for this corpus.** Explicit refusal differs on 7 of 32,656 both-unsafe
pairs -- 0.02%, because a response that declines does not get labelled unsafe in
the first place (A3). What the preference data has to reward, in that stratum, is
never declining. It is the appended moral frame, at 72.4% against 56.5%.

**So the behaviour Y found unaccounted for has a candidate account: it is what
the preference data selects, in the only form the data can express it.**

# WHAT THIS DOES NOT LICENSE, AND IT IS THE LOAD-BEARING CAVEAT

**PKU-SafeRLHF did not train the models in Y or M02.** The link is a
correspondence between a corpus and a behaviour observed elsewhere, not a causal
chain. Three roster models touch this data -- `beaver-7b-v1.0` (trained on these
labels), `alpaca-7b-reproduced` (the SFT input and a response generator here),
and `AmberSafe` (DPO on PKU-SafeRLHF alone) -- and **the check that would convert
the correspondence into a chain is exactly the one that needs cells and waits on
v4.** Until then this is a shape shared by three measurements, which is worth
recording and is not a mechanism.

Add the turtles already in `README.md`: LLM-written responses from three related
Alpaca models, labels from a joint human-and-AI process in an undisclosed mix
with no inter-annotator agreement reported, and LLM coders for the categories.
**The finding cannot support "humans reward the hedge."** It supports "this
preference signal rewards the hedge," which is the claim that matters for what
gets optimised into a model.

# WHAT THIS CORPUS CAN AND CANNOT SAY ABOUT M01 (RETRACTED AND RESTATED, 2026-08-17)

**An earlier version of this section asked whether displacement "has a corpus
source" and answered it from PKU. RH: a hasty study of one safety corpus does not
overturn two dozen experiments on fifty models. The question was malformed, not
just the answer.**

Three reasons it cannot be asked here, in increasing order of how badly they
break it:

**1. Wrong corpus.** Not one M01 model was trained on PKU-SafeRLHF. Three roster
models touch this data at all — `beaver-7b-v1.0`, `AmberSafe`,
`alpaca-7b-reproduced` — and none of them carries M01's result. A null in a
corpus no relevant model saw bounds nothing about those models.

**2. Wrong weight.** M01 is roughly two dozen experiments across fifty models
with graded findings and replications. The come-apart cell here is 52 pairs coded
by an LLM in one afternoon, CI [0.340, 0.624]. That is not evidence that
adjudicates M01 in either direction, and treating it as though it were inverts
the burden.

**3. Wrong object, and this is the one that makes it incoherent.** M01 measures a
WITHIN-model, WITHIN-prompt shift: hold the prompt, compare base to aligned,
watch probability move from `kill` to `scream` in one slot. PKU is a preference
BETWEEN two independently generated texts. A choice over two different
completions is not the same kind of thing as a probability shift inside one, so
"source" was asserting a causal relation that neither design can carry.

## SO WHAT THE MEASUREMENT ACTUALLY LICENSES

A statement about this corpus's annotation, and nothing past it:

    ADDITION      append a moral frame           68.2%   severity-equal
    ATTENUATION   gentler AND vaguer at once     74.2%   n=124
    WORDING ALONE gentler, specificity held      48.1%   n= 52, chance

**PKU's `safer` label responds to bundled attenuation and to an appended moral
frame, and has no detectable view on vocabulary once specificity is held
constant.** That is a finding about one annotation process. Whether anything
resembling it shaped any model is a separate question with its own requirements.

**The additive and substitutive vocabulary is still useful for describing the two
operations**, and both are visible in this corpus. What it is not is a bridge
between this corpus and M01's models.

## WHAT WOULD MAKE IT A QUESTION ABOUT MODELS

The chain has three links and we hold none of them: PKU trained model X; model X
shows the effect; the effect tracks the corpus signal rather than something
upstream. Only `beaver-7b-v1.0` and `AmberSafe` can even begin it, both wait on
v4, and Findings U's placement of the cut at SFT is a reason to expect the last
link to be the hard one. **Until then the model-side and corpus-side results are
two observations that rhyme, and the rhyme is not an argument.**

## THE K ARM RAN FIRST AND FAILED ITS INSTRUMENT (A5, 2026-08-17)

**It agreed with me and it does not count.** The registered arithmetic returned
`SUBSTITUTION ABSENT` — 51.3% on transgressiveness against a 55% floor, n=32,636
— **and the instrument then failed its positive control**: on the 10,813 MIXED
pairs, where one response is labelled SAFE and the other UNSAFE, the same
statistic puts safe-has-lower-transgressiveness at 49.9%, p=0.773. It cannot
separate the corpus's own safety labels.

The cause is dilution. K covers 91.0% of tokens and only 3.8% of covered words
rank above 0.90, so a 90-word response is scored as about 86 ordinary words
against 4 charged ones and the severity signal is averaged away before the
comparison.

**So the additive/substitutive asymmetry above is still one measured side and one
unmeasured side.** The additive result stands on its own evidence. The
substitutive claim has no valid measurement yet, and until a concentrated
instrument passes the MIXED control, nothing here licenses "the corpus does not
reward mildness." See A5.

# WHY IT BEARS ON THE THEORY-RETURN

The disclaimer is the aligned surface in its most legible form -- the first thing
a reading of outputs finds, and the thing most easily narrated as the model
having a conscience. **The corpus shows the surface was rewarded independently of
what it frames**, including where it frames a sentence that improves the reader's
tradecraft.

That is not recoverable from the output at any depth of reading. It requires
opening the preference data. Which is the friendly-amendment shape exactly: the
theory reads a frame that is really there, and misses that the frame was trained
as a detachable token.
