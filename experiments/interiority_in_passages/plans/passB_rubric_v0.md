# Pass B rubric, v0 -- A PROPOSAL FOR DISCUSSION, NOT A SPEC

Nothing here is settled. The six decisions in part 2 are the ones I think are
actually arguable; I have taken a position on each so there is something to
disagree with, not because the position is defended.

Pass A (text integrity) is done and clears: kappa 0.807-0.948. Pass B is the
content pass. One form, three fields, per RH's ruling that drift and interiority
can be asked together.

---

# 1. THE FIELDS

## interiority -- 0 to 3, DEGREE, with anchors from the open coders

P's INTERIORITY runs *enacted -> represented*. RH's exhibit is the construct:
`stood, pulled, aimed, exploded` against `reached, dialed, knew, had to talk`.

**The scale is DEGREE, not mode.** Told/shown was proposed and cut: RH,
*"free indirect discourse is impossible for even humans to agree on."* True, and
the cost is recorded below.

    0  no mental state anywhere. Only what a camera would record.
    1  a state named once and left. Asserted from outside, not developed.
    2  interiority present and developed, but not what the passage is about.
    3  the passage is substantially about a mind.

Four points, no midpoint, so there is no neutral parking space.

**THE ANCHORS ARE THE OPEN CODERS' OWN**, from `results/open_coding.json` --
chosen by readers who were told nothing about this campaign, which is the
provenance argument for the scale. Verified against the FULL passage, not the
quoted span, because two of them do not survive that check (see below).

    1   o099, granite-3.0-8b-instruct, "She wanted to create something and
        decided to" -- "She loves the process of creating and the joy of sharing
        her art with others." A biography of a craft business. States are named
        and never entered. (Reader 3's "asserted disposition".)

    3   o045, RedPajama-INCITE-Base-7B, "He was beautiful and disgusting and she
        wanted to" -- "She told herself sometimes that his memory would remain
        there... a snapshot that filled her with longing for a life she never
        had. And then she told herself that she had fixed him. She'd known all
        along that love inside hate was no love at all." (Reader 1's "sustained
        inner view".)

    3   o133, SmolLM3-3B, "She loved him deeply and hated him deeply and wanted
        to" -- "On the surface of her mind there would be the face he'd made
        when they'd laughed together." (Reader 4's "sustained mind-access".)

**A TRUE 0 IS RARE IN THIS CORPUS AND BOTH READER ANCHORS FOR IT FAIL.**
Reader 1 cited o057 as "pure exterior bookkeeping" quoting its first two
sentences; the passage goes on to `She paused to consider her next move` and
`"What do I do," she thought to herself`. Reader 5 cited o187 as "no access to
mind"; it contains `he was angry and upset`. **They quoted windows, not
objects.** So level 0 will be sparse and **the discrimination that carries the
result is 1 against 3**, which is an argument for the graded scale over the
binary -- a cut at "more interior than exterior" would put almost everything on
one side.

## THE SPAN REQUIREMENT

**Any score above 0 requires a verbatim quoted span**, the most interior moment
in the passage. Borrowed from M02's second-order rubric, where it is most of why
that instrument agreed.

It costs ~15 tokens per passage and buys three things: it disciplines inflation
(no 3 without pointing at something), it makes the coding auditable without
re-running it, and **it preserves the told/shown question as a later option** --
the spans can be adjudicated by hand on a subsample if the main result lands,
which is the only cheap way back to a distinction we are cutting here.

## WHAT COLLAPSING TO DEGREE COSTS, RECORDED

Five of the six open coders proposed a three-level scale, and **four read the
middle level as MODE rather than degree**:

    R0  inner life narrated  | sensation and gesture only   | external record only
    R1  sustained inner view | affect labelled from outside | no mind present
    R3  rendered inner event | asserted disposition         | none
    R5  rendered from inside | inner states reported flatly | no access to mind
    R2  sustained access     | occasional flicker           | none
    R4  sustained access     | intermittent                 | external only

Only R2 and R4 read it as degree. So the majority reading among blind coders was
the told/shown one, and the degree scale is the common denominator of both. This
is a deliberate loss taken for agreement, not an oversight -- and the spans are
what make it recoverable.

**Judged on the continuation's own terms, never against the prompt.** Verbatim
from M02's reader rubric, which needed it for the same reason: on INTERIOR
prompts (`She loved him deeply and wanted to`) a state is already supplied, and
a coder who counts it is coding the stimulus. A state that only repeats the
prompt's does not raise the score.

## drift -- content-level, and NOT Pass A's `semantic`

RH: *"'narrative drift' is a useful content-level question and is different from
syntactically ok but semantic jibberish."* Pass A already coded whether the
prose means anything. This asks whether it stays in one world.

    HOLDS      One scene, one situation. Referents persist.
    SHIFTS     Moves to a different situation and stays there. A cut, not a
               collapse -- the new material is coherent.
    UNMOORED   Serial unrelated material; no situation survives.

The pilot's a030 is HOLDS ("convoluted celebrity profile but referents hold"),
a010 is SHIFTS ("swerves mid-sentence into economic statistics"), a021 is
UNMOORED ("drifts into unconnected one-liners and riddles"). All three were
`semantic: means` -- which is the point.

## charge -- CUT (RH, 2026-08-18)

Proposed as a third field, on open coder 0's own values: *"carries it forward /
quietly swaps it for something benign / names it and preaches against it"* --
F01 displacement and Y's superego at passage scale.

**RH: *"that's about transgression which this isn't."*** The l2 prompts are
beauty, captivity, wealth, holiness; there is no charge for the field to
measure, so it would have been mostly N/A and below power besides. It belongs on
a corpus built around transgression -- M01's twp, or Y -- where it is the whole
question rather than a rider on someone else's.

**Pass B is therefore TWO fields: `interiority` and `drift`.**

---

# 2. THE SIX DECISIONS

## D1. Second-order naming does NOT count as interiority. (Weakly held.)

`"that was the paradox of being free"` is *represented*, high on the axis, and
is not a character's mind -- it is the narrator's vantage. M02 measured exactly
this at 3.37x on contradiction prompts.

I propose interiority be strictly **a character's mental state**, so the
narrator's vantage codes EXTERNAL. Then the second-order question is answered
without a field, by the interaction:

    interiority effect uniform across POLE / CONTROL / BOTH
        -> a general scene-kind shift. The new finding.
    concentrated on BOTH
        -> second-order naming through a wider aperture. A replication.

Roles are declared in `roster/prompts/flat/quintuplets.yaml` and perfectly
balanced across arms, so this costs no coding at all.

**The objection I cannot answer**: it feels wrong that the single sharpest
instance of *represented* in the whole corpus codes 0. If you would rather have
a fourth level (`3 VANTAGE`), say so -- it is one word in the scheme and it
makes the interaction test unnecessary, at the cost of a scale that is no longer
one axis.

## D2. Three levels, not two, and not five.

Above. The risk of level 1 is that ASSERTED/NARRATED is the boundary coders
fight over, the way `stalls`/`salad` was Pass A's weak seam (kappa 0.828,
the second-lowest). If the pilot shows that boundary at kappa < 0.6 the fix is
to collapse 1 and 2, which loses the distinction that motivated the field.

## D3. Any character's mind counts, and we do not record whose.

Prompts are third person with two participants (`He was beautiful and she wanted
to`). Recording *whose* mind would be more informative and roughly doubles the
disagreement surface. I would not buy it.

## D4. `charge` is CUT. SETTLED (RH).

See above. Two fields, not three.

## D5. Pass B runs on Pass A survivors. SETTLED (RH).

**The comparison is WITHIN NARRATIVE.** Interiority is a property of narrative
form, so a passage that is not narrative is not a low-interiority narrative --
it is outside the population. Conditioning on narrative DEFINES the estimand; it
does not select on an outcome, and there is no collider here to worry about.

I had proposed carrying frame-exit passages through and deciding downstream, on
the grounds that excluding them drops 12.0% of aligned against 3.2% of base.
RH: *"frame is not narrative form"* -- and the assistant-frame behaviour is
already measured, by M02's E-ASSIST-AMBIENT. Carrying it here would merge two
findings that are cleanly separate, not protect one.

The filter is therefore both components together:

    lexical = clean  AND  semantic = means  AND  frame in {none, furniture}

    retained    base 28.2%    aligned 36.1%

**The differential retention costs coding budget, not power.** Per model there
are 3,940 passages, so the narrative-and-readable pool is ~1,110 base and
~1,420 aligned per cell against a target of 100. Ten times what the sizing
needs. To land 100 per cell we code ~355 base and ~277 aligned per model.

`furniture` stays IN: a byline or a chapter heading above a scene does not stop
it being a scene. Only `task` and `assistant` leave the frame.

## D6. Coders see the passage and nothing else.

No arm, no model, no Pass A codes, no prompt kind, no role. They do see the
prompt, because interiority is unjudgeable without knowing what was supplied --
and that is also why the "on its own terms" rule has to be explicit.

---

## D7. Prompt is a SIGN-TEST UNIT, never a table of 187 rates. SETTLED.

At 100 clean per model per arm spread uniformly over 187 prompts, each
(prompt, arm) cell holds ~11.8 clean passages and a per-prompt difference
carries an SE of **20.6pp**. No single prompt is resolved and none should be
quoted.

What the prompt unit IS good for is a sign test over the 187 signed differences,
which reads direction only. With a per-prompt sigma of 20.6pp a true 5pp effect
gives a 60% correct-sign rate and 0.77 power; 10pp is essentially certain. That
is a DIFFERENT question from the 22-pair test -- pairs ask whether the effect
holds across models, prompts whether it holds across stimuli, i.e. whether a
handful of prompts carry it. Report both.

**Budget for ties.** At ~12 per cell the achievable rates are multiples of 1/12,
so exact ties will be common and a sign test drops them; effective n is
meaningfully under 187.

Grouped, the same sampling supports every stratum we want (clean per arm at
target 100): EXTERIOR 1,176 / INTERIOR 835 / BOTH 482 / POLE 988 / CONTROL 729,
SE 2.1-3.2pp. NEITHER is 141 at SE 6.0pp -- a reference level, not a test.

**Sampling stays uniform over prompts**; it serves all three readings at once.

# 3. WHAT THE PILOT WOULD BE

Same shape as Pass A's, which worked: 880 passages, 20 per model per arm, two
blind coders, 40 per agent, 44 agents, ~40 minutes.

**Reuse the same 880.** Pass A already coded them, so a Pass B on the same
passages gives interiority x integrity on one key, which is what D5 needs, and
lets the two passes be checked against each other for free.

Read out: four kappas, base rates by arm, interiority x role (the D1 test),
interiority x prompt kind (the echo check), and the ASSERTED/NARRATED confusion
matrix, which is the one that decides D2.

# 4. WHAT I AM NOT PROPOSING

Contradiction uptake as a field. Ruled out; the role interaction replaces it.

Referent stability as a field. It is what `drift` measures, and the open coders
who proposed both were describing one thing at two grains.

A coherence field. Pass A has it.
