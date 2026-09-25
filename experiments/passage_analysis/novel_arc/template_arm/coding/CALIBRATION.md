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
