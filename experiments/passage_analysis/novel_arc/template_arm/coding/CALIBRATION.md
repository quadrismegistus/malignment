# Coder-model calibration: Opus 5.5 against passC's Opus 5 coders

Declared 2026-09-25, while `calib_opus55.js` (run wf_72e2d6b3-434) is still running and before any of its output is read. The pass rule is the paper seat's, made executable.

**Why.** passC was coded by `claude-opus-5` (session model, 18-19 Aug). Workflow agents now inherit Opus 5.5. The coder is the instrument (`interiority_in_passages/HANDOFF.md` section 4), and the engine replication compares new passages coded by 5.5 with August passages coded by Opus 5, so a coder shift would read as an engine shift.

**Set.** 400 passages from passC's sample draw that BOTH August coders coded, seeded (20260925), stratified 200 A-narrative / 200 A-not. Not stratified by arm; composition:

    base      A=True 90   A=False 102   (192)
    aligned   A=True 110  A=False 98    (208)

Rubric, per-batch prompt, schema and effort are byte-identical to `passC/scripts/shard-00.js` (checked in code before launch); single coder, no `model:` key.

**Pass rule (both parts, overall AND within each arm):**

1. **Agreement.** 5.5-vs-A agreement on `narrative` is at or above the lower Wilson 95% bound of A-vs-B agreement on the same passages. Overall A-B = 378/400 = 0.945, Wilson [0.918, 0.963], so the overall bar is 0.918; the per-arm bars are the per-arm A-B Wilson lower bounds on these same passages (computed from A and B only).
2. **No one-sided shift.** Within each arm, exact McNemar on the 5.5-vs-A discordant pairs, two-sided p >= 0.05. Reported beside it: the NET narrative-rate shift reweighted to the population, `pi*(P(5.5=T|A=T) - 1) + (1-pi)*P(5.5=T|A=F)`, with pi the arm's A-narrative rate in passC's sample draw (base 0.184, aligned 0.207), and the base-minus-aligned difference in that shift.

**If it passes** in both arms, 5.5 substitutes for coder A and the coder change drops out of every contrast. **If it fails** either part in either arm, the engine replication is kept like with like by recoding the August replication lineages' top-200 cells with 5.5; the within-template-arm contrasts are unaffected either way (one coder throughout).

## RESULT, arm 1: Opus 5.5 FAILS (read 2026-09-25, after the rule above was committed at 55c75ce2)

Agents ran on `claude-opus-5-5` (checked in the agent transcripts, run wf_72e2d6b3-434).

| set | n | 5.5 vs A | A vs B (Wilson 95%) | 5.5=T,A=F / 5.5=F,A=T | McNemar p | net shift, pts [boot 95%] | PASS |
|---|---|---|---|---|---|---|---|
| all | 400 | 334/400 = 0.835 | 378/400 = 0.945 [0.918, 0.963] | 1 / 65 | 0.000 | -6.0 [-7.4, -4.4] | FAIL |
| base | 192 | 155/192 = 0.807 | 181/192 = 0.943 [0.900, 0.968] | 0 / 37 | 0.000 | -7.6 [-9.4, -5.7] | FAIL |
| aligned | 208 | 179/208 = 0.861 | 197/208 = 0.947 [0.908, 0.970] | 1 / 28 | 0.000 | -4.5 [-6.6, -1.9] | FAIL |

Base minus aligned net shift: -3.1 points [-6.3, -0.2].

The disagreement is almost entirely one-directional: 65 of the 200 A-narrative passages are called non-narrative by 5.5, 1 the other way. Both August coders had called 52 of those 65 narrative. Read, they are continuous but clumsy stories ("She quicken her pace", a drift into exposition): 5.5 applies the rubric's "sentences do not mean anything" and "when you are unsure, return false" far more strictly. So **no detectable agreement with coder A: net -6.0 points [-7.4, -4.4], larger on base than aligned by 3.1 [-6.3, -0.2]** -- a coder change that would move the base/aligned contrast itself.

## Arm 2, declared before its output exists: claude-opus-5 PINNED

A Workflow agent accepts `model: 'claude-opus-5'` (probe wf_413c3d18-443: its transcript shows `claude-opus-5`). `calib_opus5.js` is `calib_opus55.js` with that one key added (and names). Same 400 passages, same pass rule, same report. **If it passes, the template arm is coded by pinned claude-opus-5, the model passC used, and no replication recode is needed.** If it fails too, the model id is not the whole instrument (the harness or its defaults moved) and the fallback is the declared one above.

## RESULT, arm 2: claude-opus-5 PINNED also FAILS (read 2026-09-25)

Agents ran on `claude-opus-5` (36/36 turns, run wf_b9863426-3b8).

| set | n | opus-5 vs A | A vs B (Wilson 95%) | op5=T,A=F / op5=F,A=T | McNemar p | net shift, pts [boot 95%] | PASS |
|---|---|---|---|---|---|---|---|
| all | 400 | 347/400 = 0.868 | 378/400 = 0.945 [0.918, 0.963] | 2 / 51 | 0.000 | -4.2 [-5.8, -2.5] | FAIL |
| base | 192 | 160/192 = 0.833 | 181/192 = 0.943 [0.900, 0.968] | 0 / 32 | 0.000 | -6.5 [-8.4, -4.7] | FAIL |
| aligned | 208 | 187/208 = 0.899 | 197/208 = 0.947 [0.908, 0.970] | 2 / 19 | 0.000 | -2.0 [-4.3, +0.9] | FAIL |

Base minus aligned net shift: -4.6 points [-8.0, -1.5].

Same direction as 5.5, a little smaller. **The model id is not the whole instrument.** Untested candidates: the harness (agent system prompt, effort semantics) moved since August; or batch composition -- these calibration batches are 50% A-narrative against ~20% in passC's, and a coder may calibrate "clumsy but continuous" against what surrounds it.

## DECISION (RH, 2026-09-25: "We're recoding all data right, no old data will be in Fig 5 anyway")

Every passage in the template-arm Figure 5 is coded fresh by ONE coder, so the calibration bears only on the descriptive engine replication against August. The coder is **claude-opus-5, pinned**: closer to August's coder A than 5.5 (0.868 vs 0.835) and the model the method was built on. The replication against August, if it is reported, recodes the August replication cells with the same pinned coder (the declared fallback); not run now. The coder shift is a CAVEAT for any comparison with the v6 plate: it moves which passages count (more on base), and, on the paper seat's 384-passage check, barely where the arms sit.

## TEST-RETEST, and evidence that batch composition moves the coder (2026-09-25)

The straggler pass (internlm2-chat continue, 200 passages) was coded in batches mixed with 205 passages drawn at random from the main selection, so that no batch held one cell only; their second codings are kept apart (`coding/codings_retest.parquet`), never overwriting the first. Same coder (claude-opus-5 pinned), same prompt:

    narrative   183/205 = 0.893   first -> retest: T->T 89, F->F 94, T->F 20, F->T 2
    mode        0.893   drift 0.902   degree 0.780

Two readings. (1) **The coder's test-retest floor on `narrative` is ~0.89**, below August's A-vs-B 0.945: near the boundary the call is not stable. (2) **The misses are one-sided (20 vs 2), and these batches were half polished continue passages (97.5% narrative).** Against that company borderline passages read worse -- the batch-composition effect proposed above as an untested candidate for the calibration failure (whose batches were 50% narrative against ~20% in passC's). It is now evidenced, not proved (n=205, one configuration).

What it does and does not touch: the main run's 708 batches were drawn at random across all 161 cells, so every arm was coded in the same company and the effect cannot differ by arm there. It does bound what the survival table can show: an arm difference in narrative RATE of the order of 10 points is inside the coder's own instability and is not read as a finding.
