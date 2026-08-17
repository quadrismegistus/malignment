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

# A SHARED SHAPE ACROSS THREE CAMPAIGNS. NOT A SOURCE.

Three results describe a similar operation from different sides. **The first two
are model-side, this one is corpus-side, and the relation between them is a
RESEMBLANCE and not a derivation** -- see the category-error section below, which
is the controlling scope for everything in this part of the file. Read what
follows as "these rhyme", never as "this one explains those".

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

## Y NAMED A PUZZLE THAT THIS RESEMBLES, AND DOES NOT ANSWER

`Y_diegetic_superego.md` observes: *"RLHF preference data rewards the assistant
declining. That is the behaviour under direct training, and at this corpus's
scale it is close to absent."* It then calls the in-scene effect "the one nothing
in the training objective names."

In PKU at least, the premise about declining does not hold: explicit refusal
differs on 7 of 32,656 both-unsafe pairs -- 0.02%, because a response that
declines does not get labelled unsafe in the first place (A3). What THIS
preference signal rewards, in that stratum, is never declining. It is the
appended moral frame, at 72.4% against 56.5%.

**That is a fact about PKU's annotation and NOT an account of Y's models, which
were never trained on it.** An earlier version of this section read it as "a
candidate answer to Y's puzzle". **Withdrawn.** U_ladder's safety ablation shows
the operation survives removing the safety corpus outright, so no corpus-content
result explains a model-side behaviour, this one least of all. The resemblance is
worth recording because it tells us the shape is not unique to one measurement.
It is not evidence about mechanism.

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

# A DATASET IS NOT A MODEL: THE CATEGORY ERROR (RETRACTED AND RESTATED, 2026-08-17)

**An earlier version of this section asked whether displacement "has a corpus
source" and answered it from PKU. The question is malformed, and its first
retraction was still too generous to it.**

That retraction gave three CONTINGENT defects — wrong corpus, too few pairs,
mismatched design — each of which implies the question becomes askable once
fixed. **It does not, and RH's objection is categorical: a dataset and a model
are different kinds of object, and treating the model as a readout of its
training data begs the question this entire project exists to ask.**

A model generalises. Whatever is in the preference data reaches behaviour through
an operation that can add what the data never contained and drop what it did.
**The operation IS the object of study.** To ask "is this behaviour findable in
the corpus" is to assume in advance that it is a lookup, which is the one thing
the campaign is trying to characterise rather than presume.

## AND THE CAMPAIGN HAS ALREADY MEASURED THIS, WITH A BETTER DESIGN

`U_ladder.md` ablates each slice out of the training mix and remeasures:

    no-math - no-safety   -0.000664   95% CI [-0.001434, +0.000108]   NO DIFFERENCE

**Removing the safety corpus costs what removing the MATHS corpus costs.**
`no-safety` retains about 90% of the full-mix effect. If displacement were the
safety objective, that arm would collapse; it does not. And `U` locates the work
at SFT — 74% of the ladder's JS, with removal stopping and addition continuing up
the rungs (faller share 49.3% -> 28.6% -> 1.0% across 16 families).

`P_unnamed_axis.md` closes the other side: held out by word, **none of the
eighteen rated norms predicts which way alignment moves a word**, and the unnamed
residual outpredicts every name tried. The model sorts on a direction that no
feature vocabulary we possess — corpus-derived or otherwise — recovers.

**So a corpus-content study was never going to answer this, at any n, on any
corpus.** The one direct experiment on the question removed the safety data and
found the operation still there.

## WHAT WAS STILL WRONG WITH THE FIRST RETRACTION

It closed by saying the corpus-to-model chain "has three links and we hold none
of them", which presents that chain as the right shape and merely unbuilt.
**It is not the right shape.** Even holding all three links, the inference would
run from what a corpus rewards to what a model interiorised, and U's ablation
shows those come apart by construction.

## SO WHAT THE MEASUREMENT ACTUALLY LICENSES

A statement about this corpus's annotation, and nothing past it:

    ADDITION       append a moral frame        68.2%   severity-equal stratum
    MILDER WORDING gentler terms                65.5%   severity-equal, n=113
                                                67.3%   all 300, n=214

**PKU's `safer` label responds to an appended moral frame and to gentler
wording.** A subgroup split suggested the wording effect is really a BUNDLE with
specificity -- 74.2% where the two coincide, 48.1% where they conflict, real
interaction at p=0.0015 -- **but that interaction sits almost entirely in a
21-pair cell, and in the matched comparison the gap is 9.6pp with overlapping
intervals. Reported as a hypothesis, not a finding.** An earlier version of this
file stated it as established; withdrawn. That is a finding about one annotation process. Whether anything
resembling it shaped any model is a separate question with its own requirements.

**The additive and substitutive vocabulary is still useful for describing the two
operations**, and both are visible in this corpus. What it is not is a bridge
between this corpus and M01's models.

## AND THE CORPUS HAS ITS OWN OBJECT, WHICH IS THE BETTER REASON TO STUDY IT

Reading these results as a proxy for the model was the error. **Read as what they
are, they are about an ANNOTATION REGIME**, and that is a political-economy object
in its own right: 28+ crowdworkers at USD 8.02-9.07/hr, in an undisclosed mix with
AI labellers, no inter-annotator agreement reported, producing a preference signal
that rewards a moral frame regardless of what it frames — OPERATIONAL sits at
chance, including a sentence coaching evasion of the police — and rewards bundled
attenuation while having no view on vocabulary alone.

**Both channels are coarse in the same way.** The label responds to the presence
of a mark and to a gestalt impression, and is blind to the fine-grained version of
each. That is a fact about what this labour produced and what it was paid to
produce. It needs no model to be interesting, and it stops being evidence about
one the moment it is asked to be.

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
