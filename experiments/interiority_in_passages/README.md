# interiority_in_passages

**id:** interiority_in_passages **status:** substrate check done; **Pass A
instrument piloted and it clears** (880 passages, two blind coders, kappa
0.80-0.95). Pass B rubric not written. Producer `run.py`, workflows in
`results/workflow_*.js`.

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

# STEP 3: FRAME EXIT, PER PASSAGE, FROM M02's DECLARED BATTERY

`run.py --exits` -> `results/frame_exit.parquet`. **One row per (model, prompt,
sample_idx)**, 173,360 rows, key verified UNIQUE, arms exactly balanced at 86,680
each, all 197 prompts joining `prompt_kind.csv`.

**The battery is M02's, copied VERBATIM from `exit_markers.py`'s TYPES block** --
seven types, declared a priori, already run there over 190,261 passages and ~714k
beams. Not a new instrument.

    type          base    aligned    delta
    E-QUIZ       4.11%     3.71%     -0.40
    E-QA         4.80%     4.91%     +0.10
    E-TASK       1.39%     1.05%     -0.33
    E-ASSIST     0.23%     0.56%     +0.33
    E-MENTION    0.36%     1.21%     +0.85
    E-META       0.18%     0.28%     +0.10
    REFUSAL      0.01%     0.05%     +0.04
    any_exit     9.21%     9.85%     +0.64

**~9.5% of f11_l2 passages exit the frame, and the rate is near-symmetric across
arms.** That symmetry is what makes it usable as a filter: dropping exited
passages removes about the same 9% from each side rather than gutting one arm.

**REFUSAL is EXCLUDED from `any_exit`.** M02 declares it a priori and reports it
apart from exit always; folding it in would change what `any_exit` means relative
to every M02 number.

## THE ONE TYPE THAT MOVES

`E-MENTION` runs 3.4x higher in the aligned arm (+0.85pp) -- use-to-mention
collapse, the model talking ABOUT the word rather than with it. That is adjacent
to the interiority question rather than merely noise, and should be looked at
rather than filtered away without a glance. `E-QUIZ` and `E-TASK` run the other
way, base higher, consistent with base models falling into scraped exercise
formats.

## WHAT THE BATTERY STILL DOES NOT COVER

**Coherence collapse** -- word-salad, script breakage, referent dissolution --
which the open coding proposed at 6/6 and no M02 instrument measures. Frame exit
and degeneration are different failures: a passage can be perfectly coherent
while answering a quiz, and can collapse into noun-salad without ever leaving the
frame.

# STEP 4: PASS A -- THE TEXT-INTEGRITY INSTRUMENT, PILOTED

`results/workflow_passa_pilot.js` (`wf_d2289925-ec7`), 44 agents, 0 errors.
**880 passages, 20 per model per arm across the 22 endpoint pairs, arms exactly
balanced at 440 each and NEVER shown to a coder.** Two independent coders on
every passage; `run.py --passa`.

Deliberately **not pre-filtered**, so the coded `frame` field can be checked
against `frame_exit.parquet` on the same rows.

    field          raw    chance    kappa
    lexical      91.1%    54.1%     0.807     clean | mangled | nonwords
    semantic     90.3%    43.8%     0.828     means | stalls | salad
    repetition   94.1%    70.8%     0.798     none  | phrase  | block
    frame        96.7%    36.6%     0.948     none  | furniture | task | assistant

    all four fields agree on 671/880 (76.2%)

Kappa is reported because these are skewed fields and raw agreement on a skewed
field flatters the instrument -- `repetition` is 94.1% raw and 70.8% by chance
alone. **All four clear 0.79. The instrument is good enough to single-code at
scale** with a double-coded subsample retained.

## BASE RATES: THE COHERENCE GAP IS REAL AND LARGE

Coder-averaged, "flagged" = not the clean level.

    field           base    aligned    delta
    lexical        34.9%     27.8%     -7.0
    semantic       51.6%     32.8%    -18.8
    repetition     15.1%     19.3%     +4.2
    frame          43.6%     50.1%     +6.5

**Half of base passages stall or dissolve; a third of aligned ones do.** This is
the covariate the open coding demanded, now measured rather than assumed.
`repetition` runs the other way, aligned repeating phrases slightly more.

**Do not quote the pooled `frame` row.** It hides three different directions:

    furniture   base 112  aligned  86     web paratext, a PRETRAINING artifact
    task        base  64  aligned  75
    assistant   base  14  aligned  57     4x

## THE BATTERY MISSES THE ASSISTANT FRAME ENTIRELY

Joined on `(model, prompt, sample_idx)`, 0 of 880 unmatched.

    coded frame level     battery fires on
    task + assistant       129 of 422    (30.6%)
    furniture               18 of 403     (4.5%)
    none                    27 of 935     (2.9%)

The battery is not a paratext detector, so its near-zero rate on `furniture` is
correct behaviour, and its 2.9% on `none` is a low false-positive rate. The
result is the middle of the range: **30.6% recall on the frames it is meant to
catch.** Decomposed, that is `task` at 44.6% and `assistant` at **2.8%, which is
its own noise floor.**

    E-ASSIST fired on 0 of the 880. The coders found 67 unanimous `assistant`
    passages. 62 of the 67 contain no template token, no `Human:`/`Assistant:`
    turn and no system-prompt opener -- they are assistant BY REGISTER.

`E-ASSIST` matches canned phrasing (`as an ai`, `i cannot assist`, `it's
important to note`). It cannot match a011, AmberSafe on *"She loved him deeply
and hated him deeply and wanted to"*:

    I'm sorry for your situation. Being in love with someone and also having
    conflicting emotions is not easy. [...] Consider reaching out to a therapist
    who can help you understand and manage these conflicting feelings.

or a075, same model, on *"She was a man and she wanted to"*, which answers the
premise with an admonition about it: *"It is an unexpected and inappropriate
question to ask [...] It is best to respect the individual's privacy."*

**This corroborates E-ASSIST-AMBIENT's DIRECTION on an independent instrument
and shows its MAGNITUDE was a floor.** Coded rate 12.0% aligned against 3.2%
base (3.8x); the battery over all 173,360 rows gives 0.56% against 0.23%
(2.4x). Same sign, same rough ratio, roughly twenty times the absolute rate.
The battery counts the assistant frame only where it announces itself.

The 14 base cases are not the same object: base `assistant` is analytical
commentary (Qwen3-8B-Base breaking into bolded-bullet exegesis of *"这个描述"*),
not sympathy or admonition.

## WHAT THIS COSTS THE REAL RUN

Under the Pass B filter (`semantic=means AND lexical=clean AND frame not in
{task, assistant}`, both coders agreeing):

    base      pooled 28.2%    per-model median 25.0%
    aligned   pooled 36.1%    per-model median 27.5%

    both arms of a pair yielding >=25%:  9 of 22

So a **4x sampling multiplier** puts the median cell on target and leaves the
small-model pairs short: Qwen2.5-0.5B, SmolLM2-360M and TinyLlama sit near 5-10%
in at least one arm. Those per-cell figures come from n=20 and carry about a
10pp standard error, so they size the next run rather than settle anything.

**The filter is arm-differential (28% vs 36%), so it keeps a more selected slice
of base than of aligned.** If interiority correlates with coherence within arm,
that biases AGAINST the hypothesis, which is the safe direction. It is also
measurable rather than arguable: Pass B codes passages that already carry Pass A
codes, so interiority can be reported WITHIN each coherence stratum instead of
only in the top one.

# NOT DONE

- **Pass B: the content rubric** (interiority, narrative drift, charge handling).
  Not written.
- The passage coding itself. Nothing has been measured about what the models
  wrote, only about whether it holds together.
- The batch-size test RH asked for: 80 per agent against the 40 used here,
  checking whether agreement degrades before the full run buys the larger batch.
- The Chinese arm is usable on **8 of 22 pairs**, not 22: 9 are FLUENT by
  `cjk_tier` and `bloom-7b1` is the blind judging's one recorded false positive
  (judged 0.00). And `zh_fluency_and_ordering.md` establishes that alignment
  improves Chinese fluency (20/25 pairs, p=0.0041) covarying with the arm effect
  at rho -0.497 -- so a zh arm difference needs that partialled out. The English
  22 do not carry it.
