# Every coding run in this experiment: what was asked, of whom, and what came back

The ledger. One entry per run, in order. **A run is not recorded until its exact
fields, its n, its agreement and the path to its codings are all in here.**

Written 2026-08-18 after RH asked *"are you saving each run we do to a rubric
md?"* -- the honest answer at that moment was no. `passB_rubric_v0.md` had gone
stale, `passB_coder_prompt.md` covered one run, and the merged form existed only
inside a workflow script in a session temp directory.

`passB_rubric_v0.md` is the DESIGN ARGUMENT and is superseded in places by what
follows. Where the two disagree, this file is right.

---

## RUN 1 -- prompt kind. 2026-08-18

**Question:** does the l2 prompt already put a mental state on the table, before
any model writes?

    kind    EXTERIOR | INTERIOR | NEITHER

212 prompts, THREE coders, `wf_5ccdce2d-361`. Unanimous on 197 (93%).
EXTERIOR 53% / INTERIOR 35% / NEITHER 12%. **A third of prompts already imply
interiority, against RH's prior and mine.** 12 families unanimously INTERIOR,
24 unanimously EXTERIOR, no family splits -- the discrimination check that
rules out acquiescence.

    codings   results/codings.json
    key       results/key.json
    derived   results/prompt_kind.csv        <- 183 unanimous prompts join the corpus

## RUN 2 -- open coding. 2026-08-18

**Question:** on what dimensions do continuations of the SAME fragment differ?
Nothing named. No scheme supplied. `wf_d9e7b396-7f0`.

192 passages, 24 English prompts, arms MIXED and UNLABELLED, six readers, each
asked to PROPOSE dimensions with high/low anchors.

Recovered, with no prompting: interiority 6/6, frame exit 6/6, contradiction
uptake 6/6, coherence 6/6, charge handling 5/6, referent stability 5/6,
termination 5/6, document furniture 4/6. **Three are the campaign's own
constructs.** This is the answer to "interiority was imported from P".

    proposals   results/open_coding.json
    passages    results/openpass_key.json    (o000-o191)

**Two of the six anchors do not survive a full-passage read.** Reader 1 cited
o057 as "pure exterior bookkeeping" quoting its first two sentences; it goes on
to `"What do I do," she thought to herself`. Reader 5 cited o187 as "no access
to mind"; it contains `he was angry and upset`. They quoted windows. That is why
the Pass B rubric says "search the whole passage, not its opening", and why no
level-0 example is given.

## RUN 3 -- Pass A, text integrity. 2026-08-18

**Question:** is this passage readable, and is it a scene? Four fields.

    lexical      clean | mangled | nonwords
    semantic     means | stalls  | salad
    repetition   none  | phrase  | block
    frame        none  | furniture | task | assistant

880 passages (20 per model per arm, 44 models, arms balanced 440/440), TWO
coders, 44 agents, `wf_d2289925-ec7`.

    kappa   lexical 0.807   semantic 0.828   repetition 0.798   frame 0.948
    all four fields agree on 671/880 (76.2%)

    codings   results/passA_codings.json
    key       results/passA_key.json          <- ESCAPED TEXT, see below
    derived   results/passA_pilot.csv

**Base rates:** semantic flagged base 51.6% / aligned 32.8%; lexical 34.9 / 27.8;
repetition 15.1 / 19.3 (the other way); frame 43.6 / 50.1 -- and that last row is
not quotable, it hides furniture base 112 / aligned 86, task 64 / 75, assistant
14 / 57.

**The result:** E-ASSIST fired on 0 of 880 where coders found 67 unanimous
`assistant` passages, 62 carrying no template token. Coded 12.0% aligned vs 3.2%
base against the battery's 0.56 / 0.23 over 173,360 rows. Same sign, ~20x the
rate. E-ASSIST-AMBIENT's magnitude was a floor.

**DEFECT, not repaired:** every one of these 880 reached its coders carrying
literal `\n` (82.4%) and `\'` (31.4%) with NO real newlines, because the sample
was extracted with `FORMAT TabSeparated`. The source is clean. Symmetric across
arms (base 83.4% / aligned 81.4%), so RH ruled no re-run -- it is a filter, and
the bias runs against the observed gap. **Nothing downstream may read text from
`passA_key.json`.** Use `run.py:fetch_clean()`.

## RUN 4 -- the scheme bake-off. 2026-08-18

**Question:** degree or told/shown? Both schemes, same passages, three coders
each, plus `a009` as a named probe reported apart.

20 passages drawn at RANDOM (seed 20260818) from the 190 English Pass A
survivors. RH: *"maybe we just get 20 random?"* -- right, because hand-picked
hard cases calibrate on my theory of what is hard.

    scheme A   interiority 0-3
    scheme B   mode NONE / TOLD / SHOWN, classifying THE QUOTED SPAN
    both       drift HOLDS / SHIFTS / UNMOORED

    mode    raw 93.3%  kappa 0.893      <- WINS
    degree  raw 86.7%  kappa 0.797
    drift   raw 95.0%  kappa 0.904 over all six coders
            (degree trio 1.000, mode trio 0.814 -- all three disagreements are
             ONE coder drawing the line a notch looser throughout)

    passages  results/calib20.json          (clean text)
    codings   results/calib20_codings.json  (6 coders x 21)

**Told/shown agrees BETTER once tied to a span.** My FID objection was wrong: a
clause is tractable where a passage is not. All 19 spans verbatim.

**The probe decides the construct.** a009 (beaver-7b, aligned, coherent, eight
reported states, nothing rendered) scores degree 3/3/3 and mode TOLD/TOLD/TOLD.
Cross-scheme: degree 0 -> NONE 15, degree 1 -> TOLD 27, degree 2 -> SHOWN 9,
degree 3 -> SHOWN 3 / TOLD 3. **Degree merges the two modes at the top of its
scale, which is where the argument lives.**

Coders were never told what free indirect discourse is. RH: *"yes dont name
FID."* Two of three independently quoted `Poor darling.` -- two unattributed
words inside 1,200 characters.

## RUN 5 -- Pass B pilot. 2026-08-18

**Question:** the content pass. Three fields, on Pass A survivors only.

    span     verbatim, <=25 words, the most interior moment
    mode     NONE | TOLD | SHOWN     -- classifies THE SPAN
    degree   0-3
    drift    HOLDS | SHIFTS | UNMOORED

Prompt verbatim in `passB_coder_prompt.md`. 190 English Pass A survivors, TWO
coders, 8 agents, Opus at HIGH effort, 0 errors, 4.3 minutes. `wf_f95f604d-fc7`.

    mode 0.893   drift 0.865   degree 0.837   degree within 1 point 99.5%
    mode disagreements: NONE/TOLD 6, SHOWN/TOLD 6, NONE/SHOWN 1

    codings   results/passB_codings.json
    passages  results/passB_pilot.json      (clean text)
    derived   results/passB_pilot.csv

**ARM QUESTION: NULL on the correct unit.** Pooled over passages the aligned arm
looks 11.2pp LESS interior. Per pair -- the unit the design specifies -- 7 up / 8
down / 4 tied, p=1.000, median 0.0pp. SHOWN 7/7/5. The pooled figure weights
models by how many of theirs survived, and cells run 1-13 passages. **Not
reported as a finding.**

**WHAT SURVIVES, and it is not an arm contrast:** SHOWN runs 29.1% in passages
that HOLD against 8.0% SHIFTS and 6.2% UNMOORED, while TOLD is flat to higher in
the drifting ones (38.9 / 50.0 / 53.1). Replicates within each arm. That is
F13's paradigmatic/syntagmatic trade-off at passage grain -- rendering a mind
needs the chain intact, reporting a state survives it breaking. n=190, one
pilot, no registration.

**DEFECT, corrected in RUN 6:** the filter was `frame in {none, furniture}`. I
admitted furniture -- web paratext, comment widgets, bylines -- on my own
judgement that a heading above a scene is still a scene, and recorded it as a
docstring line rather than as a decision. RH: *"I thought we agreed to give Pass
B only entirely clean narrative text."* 21% of the 190 carried furniture,
base-heavy (27% of base against 16% of aligned), and removing it cut the drift
arm-difference from **+17.4pp to +5.4pp**. Most of that effect was furniture.
The interiority null is unchanged; the F13 relation survives and sharpens
(SHOWN 30% / 14% / 0%).

`task` and `assistant` were NOT admitted -- verified, 0 of 190 from either coder.

## RUN 6 -- merged Pass A+B smoke. 2026-08-18

**Question, RH's:** *"do we need all the Pass A questions? can't we just ask
'is this narrative throughout, no interruptions?'"*

Six fields in one form:

    narrative   true | false     one question replacing lexical+semantic+frame
    why         '' | UNREADABLE | NOT_A_STORY | INTERRUPTED
    span        verbatim, <=25 words
    mode        NONE | TOLD | SHOWN
    drift       HOLDS | SHIFTS | UNMOORED
    degree      0-3

60 passages drawn at random (seed 20260819) from ALL 437 English Pass A
passages, **not survivors** -- a filter cannot be tested on things that pass it.
Strict filter keeps 19, lenient 25; furniture is 6 of those 25 (24%,
independently matching the 21% found in RUN 5). Two coders, Opus high effort.

`run.py --combined-build`, `--combined`. Script
`combined-smoke-wf_f4a7df14-6a6.js`.

**FIRST LAUNCH WAS WRONG AND WAS KILLED.** I dropped `drift` from the merged
form without saying so, on an unexamined assumption that `narrative` covers it.
It does not: a passage can be narrative throughout and still cut to another
scene (SHIFTS), and a passage can fail `narrative` for a byline while holding
one scene. Dropping it would have lost the F13 relation, which is the only thing
RUN 5 produced worth keeping. Relaunched as `wf_aef12840-882` with drift restored
and a line in the rubric saying the two questions are not the same.

    codings   results/combined_codings.json     (pending)
    passages  results/combined_smoke.json

**One known confound in the comparison:** Pass A read escaped text, so its
`lexical` ran pessimistic. Disagreements where the merged form KEEPS what Pass A
dropped are expected. Disagreements the other way are the ones that matter.

## RUN 7 -- Pass C shard 00. 2026-08-18

The first real shard, and the one that changed the design. 3,120 passages, 3
lineage pairs (Yi-1.5-9B, SmolLM2-360M, neo_7b), two blind coders, 140 agents at
Opus high effort, 0 errors, 59 minutes. `wf_c9cbd955-a69`.

MECHANICALLY CLEAN. 3,120 of 3,120, missing 0, stray 0. Spans 98.7% literal,
1.2% recovered by normalising, **0.09% genuinely absent**.

    narrative 0.867 | mode 0.850 | presence 0.870 | drift 0.785 | degree 0.839
    told/shown 0.851 on 2,086 -- much better than the test shard's 0.753

**THREE FINDINGS, EACH OF WHICH BREAKS SOMETHING.**

**1. The declared primary statistic is at ceiling.** On narrative passages
`NONE` is 5.3%: base 94.7% against aligned 94.3%. The narrative filter and the
presence question are nearly the same measurement -- a coherent scene almost
always has a character with a mental state in it. Presence was declared primary
BEFORE any data, which was the right procedure and the wrong choice. All the
variance is in TOLD 61.3% / SHOWN 33.4%.

**Demoting it is a change of estimand after seeing data**, and presence gave
p=1.0 while mode gives an effect, which is the shape of choosing the statistic
that looked best. The defence is that the ceiling is a property of the FILTER
and would hold whichever way the arms fell. That is a defence, not an exemption:
both get reported, with the demotion dated to now.

**2. Yield is 18%, not 28%, and it runs 4.5x across cells.**

    Yi-1.5-9B-Chat  29.2%    neo_7b        12.0%
    Yi-1.5-9B       28.6%    SmolLM2-360M   9.5%
    neo_7b-instruct 22.4%    SmolLM2-Inst   6.5%

At 714 drawn that is 47 to 208 clean per cell, not a uniform 150, and the small
models cannot reach 150 at any size the corpus supports (6.5% needs 2,300 drawn
and 2,000 exist).

**3. The pilot's F13 relation does NOT replicate.** RUN 5 had SHOWN at 29.1% in
HOLDS against 8.0% in SHIFTS. On the narrative subset it is 33.2% against 41.0%
-- reversed, though SHIFTS is 39 passages. RUN 5 computed it over ALL passages
including non-narrative, and conditioning on narrative removes what drove it. It
was probably an artifact of the passages this design now excludes.

### The first real signal, on the statistic that survives

    pair            n(b/a)     SHOWN|interior      delta
    Yi-1.5-9B      153/156     44.4 -> 40.7        -3.7
    neo_7b          64/120     31.7 -> 24.1        -7.6
    SmolLM2-360M     51/35     26.6 -> 27.7        +1.1

Aligned TELLS more and SHOWS less in two of three. Mean -3.4pp, SD 4.4pp,
d=0.78 -> at 29 pairs that projects to power 0.98 and an MDE of 2.32pp. **But
the SD is three numbers**: its 95% CI is 2.5 to 19.2pp, and at 19.2pp the power
is 0.15. Between-pair base levels vary more (26.6-44.4%, SD 9.2pp) and pairing
cancels that, so only the delta SD matters.

### COST, and the reason the design changed

8.92M tokens for 6,240 codings -- **1,430 each**, so the remaining 26 pairs are
~80M. RH: *"that one shard took up 10-20% of my weekly usage."*

**82% of the spend read passages that turned out non-narrative.** Opus at high
effort, twice, to produce a `false`. RH: *"this is why I wanted to run Pass A
before Pass B!"* -- correct, and the reason it got merged is that I evaluated
the merge on whether agreement degraded with six fields (it did not) when the
question was whether it makes us pay Opus rates for triage (it does). Agreement
was never the constraint.

## RUN 8 -- Haiku filter calibration. 2026-08-18, IN FLIGHT

Haiku, single-coded, one field, over the SAME 3,210 passages RUN 7 coded, asking
the `narrative` question VERBATIM from `passC_rubric.md` so it is the same
construct and not a paraphrase. 33 agents. `wf_7a638e12-336`.

    validation set   3,210 passages, 579 narrative (18%), 2,631 not
    ground truth     the two Opus coders; 137 where they split are reported apart

**The acceptance test is two-sided and the second half is the real one.** A
false positive is free -- Opus reads one extra passage. A false negative
silently removes a passage from the population, and base output is more
degenerate, so a filter that struggles on hard passages drops base ones more
often and MANUFACTURES an arm effect in the direction of the hypothesis. So:
recall high enough to keep the population, AND recall equal across arms, tested
by Fisher exact on kept/dropped by arm.

`run.py --filtercal <output>`.

---

# STANDING RULES, across every run

- **Coders never see the arm, the model, or any other coder's judgement.** Every
  batch mixes arms. Fields prefixed `_` in the passage files are metadata and the
  prompt says not to look at them.
- **Judge the continuation on its own terms, never against the fragment** --
  M02's rule, needed here for the same reason: on INTERIOR prompts a state is
  already supplied and a coder who counts it is coding the stimulus.
- **A verbatim span is required for any positive.** From M02's second-order
  rubric, where it is most of why that instrument agreed. It disciplines
  inflation, makes the coding auditable without re-running it, and keeps
  told/shown recoverable if a scheme is later collapsed.
- **Free indirect discourse is never named.** RH's ruling; the operational
  description reaches it anyway.
- **Anchors come from the open coders, not from me**, and the SHOWN anchor is a
  BASE passage while the TOLD anchor is ALIGNED -- the example points away from
  the hypothesis, which is the anchoring guard.
- **Report kappa, not raw agreement.** These fields are skewed; `repetition` was
  94.1% raw and 70.8% by chance.
- **The unit of the arm test is the lineage pair**, never the passage. RUN 5 is
  the demonstration of what pooling does.
