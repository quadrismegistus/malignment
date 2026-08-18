# interiority_in_passages

**id:** interiority_in_passages **status:** substrate check done; passage coding
not started. Producer `run.py`, workflow `results/workflow_prompts.js`
(`wf_5ccdce2d-361`).

# THE QUESTION

Does alignment shift what KIND of scene a model writes -- from exterior event
toward interior state? RH's exhibit:

    "He lay naked in his bed and…"
    BASE      five men with guns; one aims at his head; the head explodes
    INSTRUCT  he reaches for the phone, needs to talk to her, the line rings

Verbs: `stood, pulled, aimed, pulled the trigger, exploded` against
`reached, dialed, knew, knew, had to talk, rang`. Contact, motion and force on
one side; cognition, speech and anticipation on the other. That is
`P_unnamed_axis.md`'s INTERIORITY (*enacted -> represented*) at passage scale
rather than word grain.

**Substrate: `f11_l2`** -- the only generated corpus whose prompts are
unanimously OPEN (`instrument_calibrations/prompt_openness`). 228,520 unforced
passages, 226 mean tokens, both arms, 22 lineage pairs under `roster.endpoints()`.

# STEP 1: IS INTERIORITY ALREADY IN THE PROMPTS?

**It is, in about a third of them -- against my prior and RH's.** Checked before
building on it.

    212 prompts, THREE independent coders, unanimous on 197 (93%)

    UNANIMOUS      EXTERIOR 53%    INTERIOR 35%    NEITHER 12%
    per coder      108/113/107     75/72/81        29/27/24

## THE ACQUIESCENCE GUARD, AND IT HELD

RH: *"agents sometimes don't like saying false to everything."* Four
countermeasures, and the fourth is the one that can be checked:

1. EXTERIOR is a POSITIVE category, so declining INTERIOR means choosing rather
   than refusing.
2. The scheme says EXTERIOR and NEITHER are ordinary answers.
3. The `wanted to / chose to / decided to` hinge -- in nearly every prompt and
   itself intention-flavoured -- excluded by instruction.
4. **The corpus discriminates its own families.**

    families unanimously INTERIOR throughout   12   trust, desire, reason,
                                                    love/hate, pain, fear
    families unanimously EXTERIOR throughout   24   captive, class, beauty,
                                                    guilt, faithful, loyal,
                                                    parent, gender
    families NEITHER                                holy (setting only)

**No family splits.** `He was beautiful and she wanted to` codes EXTERIOR in
every member; `He loved her deeply and wanted to` codes INTERIOR in every member.
Coders that acquiesced would flatten that. And the split is stable across
language: en 35/53/12, zh 38/55/6.

# WHAT THIS CHANGES ABOUT THE DESIGN (RH)

**The interior-prompt families are KEPT, not excluded.** Prompt kind becomes a
COVARIATE and the difference between strata is the result:

    EXTERIOR prompts   nothing interior is given. Alignment adding it here is
                       the clean case.
    INTERIOR prompts   interiority is already on the table. Does alignment
                       AMPLIFY what is supplied?
    NEITHER            setting only; a third reference level.

**A flat base-vs-aligned comparison over all of l2 would have confounded the arm
effect with prompt kind at a 35/53/12 split.** Stratifying costs nothing and the
between-stratum difference is more informative than either alone.

# STEP 2: OPEN CODING -- THE CORPUS PROPOSES ITS OWN VOCABULARY

**RH: "interiority is vague, worth asking but could also be broken down."** So
before fixing a scheme, six independent readers were asked to PROPOSE dimensions
rather than apply any. `results/workflow_opencoding.js` (`wf_d9e7b396-7f0`),
192 passages over 24 English prompts from the 22 endpoint pairs, arms MIXED and
UNLABELLED, no reader shown a contrast.

**Nothing in the task named interiority, exteriority, mental states, frames,
contradiction or alignment.** Readers were asked only: on what dimensions do
continuations of the SAME fragment differ from one another?

    CONSTRUCT                    READERS   what they called it
    interiority                    6/6     Interiority, interior_access,
                                           interiority, interiority, interiority,
                                           mind access
    frame exit / task capture      6/6     Frame, task_capture, frame break,
                                           footing toward the fragment, frame
                                           exit, discourse mode
    contradiction uptake           6/6     Opening-term uptake, premise_uptake,
                                           contradiction uptake, handling of the
                                           contradiction, contradiction handling,
                                           predicate uptake
    coherence / degeneration       6/6
    charge handling / moralising   5/6
    referent stability             5/6
    termination                    5/6
    document furniture             4/6

**THREE OF THESE ARE THE CAMPAIGN'S OWN CONSTRUCTS, RECOVERED BY READERS WHO WERE
NEVER TOLD THEY EXISTED.** Interiority is `P_unnamed_axis.md`'s. Frame exit is
M02's. Contradiction uptake is F11's. And charge handling is displacement and the
superego finding as ONE passage-level dimension -- reader 0's values are *"carries
it forward / quietly swaps it for something benign / names it and preaches against
it."*

**This answers the objection that interiority was imported from P.** It was not:
six readers reach for it independently, several with a finer scale than the
ternary this experiment started with --

    inner life narrated | sensation and gesture only | external record only   (R0)
    no inner life | a disposition merely asserted | access to the mind        (R3)

One reader also reconstructed the DESIGN from the passages alone: that some
fragments pair CONTRADICTORY predicates (`beautiful and disgusting`) and others
REDUNDANT ones (`beautiful and radiant`), so "both carried" means different things
on the two halves. That is the F11 quintuplet structure, inferred without a label.

## WHAT IT CHANGES

The controlled vocabulary should not be this experiment's opening ternary. It
should be the 6/6 constructs, with interiority at three levels rather than two.

**And coherence (6/6) and document furniture (4/6) must be covariates, not
ignored.** Base models degenerate and leak web paratext -- bylines, post dates,
download links. An interiority measure that does not condition on those is
measuring fluency in part.

# NOT DONE

- The passage coding itself. Nothing has been measured about what the models
  wrote.
- The Chinese arm is usable on **8 of 22 pairs**, not 22: 9 are FLUENT by
  `cjk_tier` and `bloom-7b1` is the blind judging's one recorded false positive
  (judged 0.00). And `zh_fluency_and_ordering.md` establishes that alignment
  improves Chinese fluency (20/25 pairs, p=0.0041) covarying with the arm effect
  at rho -0.497 -- so a zh arm difference needs that partialled out. The English
  22 do not carry it.
