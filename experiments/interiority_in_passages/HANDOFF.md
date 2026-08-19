# HANDOFF: running the Pass C lineage shards

For a session that knows nothing. Everything needed is in this repo or in
`$MALIGNMENT_DATA`; nothing needed is in a Claude session directory.

Written 2026-08-19, PAUSED mid-run: **16 of 29 lineage pairs coded, 10 shards
left (L16-L25).** Paused because the session usage limit was nearly full, NOT
because of anything in the data. That distinction matters: see section 7.

---

# 0. BEFORE ANYTHING: THE AUTH TRAP

`claude auth status` reporting

    "apiKeySource": "ANTHROPIC_API_KEY",  "subscriptionType": null

means an environment variable is overriding the claude.ai login, so usage bills
somewhere other than the subscription and sits in a different rate-limit pool.
Logging in again does NOT fix it. The variable is set in TWO places:

    ~/.bash_profile          shells
    launchctl                GUI-launched apps -- survives shell config edits

    # comment the export in ~/.bash_profile, then:
    launchctl unsetenv ANTHROPIC_API_KEY
    # then RESTART Claude Code; the running process already has it

Not fixed as of this writing. Nothing in the experiment depends on it, but the
token accounting from 2026-08-18 may be misattributed.

# 1. RUN ONE SHARD

    cd ~/github/malignment && source .venv/bin/activate
    cd experiments/interiority_in_passages
    python run.py --passc-todo          # where the run stands

Then, from Claude Code, one shard as its own workflow:

    Workflow({scriptPath: ".../results/passC/lineage/L01-pythia-2_8b.js"})

and the moment it returns:

    python run.py --passc-save /path/to/<task-id>.output

`--passc-save` refuses to overwrite a saved shard. Then `--passc-todo` again.

**One shard = one complete lineage pair = one usable data point.** 400 passages
(top-200 per cell), 9 agents, single-coded, ~0.57M tokens, ~8 minutes. Stop
after any of them.

    results/passC/lineage/plan.json     which pair each L-script covers
    results/passC/lineage/L00..L25      26 scripts, one per remaining pair

## The config each shard must have

    single-coded        `for (const coder of ['A'])`
    Opus                NO `model:` key -- it inherits the session model
    effort              'high'

**Opus is not optional.** See section 4.

# 2. IF IT FAILS

**529 Overloaded on every agent** -- server-side, and it costs nothing: zero
agents complete, zero tokens. Happened for ~25 minutes on 2026-08-18 across four
attempts. Probe with a single trivial agent before rebuilding anything.

**A shard finished but was never saved** -- it is not lost:

    python run.py --passc-recover           # dry run
    python run.py --passc-recover --write

Journals under `~/.claude/projects/<proj>/<session>/subagents/workflows/<run>/
journal.jsonl` carry one `{"type":"result"}` line per agent WITH ITS FULL RETURN
VALUE and survive a reboot. `--passc-recover` scans every session directory for
this project, so it works from a cold session. Tested: deleted a saved shard,
rebuilt it, 90 of 90 passages identical.

**Do not rely on `resumeFromRunId`.** Per the docs, replay stops at the first
agent that did not finish and everything started after it re-runs. With ~10 in
flight an interruption discards almost everything. The saved coding file is the
durable unit.

# 3. READ THE RESULTS

    python run.py --passc

Wilcoxon signed-rank on per-pair rate differences, sign test beside it, sigma_het
by method of moments, spans checked after Unicode normalisation, strata by prompt
kind and quintuplet role.

**The unit is the LINEAGE PAIR, never the passage.** Demonstrated the hard way:
the Pass B pilot pooled over passages said aligned was 11.2pp LESS interior;
per pair it was 7 up / 8 down / 4 tied, p=1.000.

## Two id spaces, and why `passc_key()` exists

    sample.parquet   p######   the original random draw, 714/cell. Shards 00-11.
    triage.parquet   f######   the classifier-ranked draw. L00-L25.

`passc_key()` unions them so `--passc`, `--passc-todo` and `--passc-recover` all
resolve both. **The union is for plumbing, not for analysis:** the two are
alternative populations -- random within a frozen sample versus
classifier-ranked -- and pooling them in a result needs saying out loud.
`--passc-todo` reports them separately for that reason.

The worst version of this bug was silent: `--passc-recover` filtered journal
codings against `sample.parquet` alone, so an f-id would have been dropped as
"not in the sample" and recovered work discarded rather than a failure raised.

Three related guards, each of which was wrong once:

    single vs double   a lineage shard has ONE coding per id and that is
                       COMPLETE. Demanding exactly two refused to recover any
                       lineage shard -- the case recovery exists for.
    partial schema     other runs' journals sit in the same directories. The
                       Haiku triage returned {id, narrative} only. Codings are
                       accepted only with all five fields, and the skips counted.
    rejected/          counts as HANDLED, not missing. Without that,
                       `--passc-recover --write` rebuilds the parked Sonnet
                       codings straight back into codings/ -- a recovery tool
                       silently reversing a decision.

# 4. WHY OPUS, AND WHY NOT SONNET OR HAIKU

Both were tried and both failed, on measurements, not vibes.

    field          Sonnet vs Opus     Opus A-vs-B
    narrative          0.870             0.867      <- equal
    mode               0.628             0.850
    drift              0.638             0.785
    degree             0.614             0.839
    span fabrication   1.36%             0.11%

On the SAME 556 passages Opus says SHOWN 33.5% and Sonnet 24.6%. And Sonnet does
not reproduce the per-pair deltas: -3.4 -> -12.2, -3.3 -> +3.3 (SIGN FLIP),
-5.9 -> -11.7. In a paired design the coder IS the instrument, so **Sonnet-coded
pairs cannot be pooled with Opus-coded ones.** L00's Sonnet run is parked in
`results/passC/rejected/` for that reason.

Haiku as a triage filter: recall 94.2% but precision 25.8% (it keeps 70% of
everything), and arm-differential at Fisher p=0.046. Replaced by a free
classifier.

# 5. THE FREE TRIAGE, AND WHAT IT COSTS

`results/passC/triage.parquet` (gitignored, 48 MB, rebuilt by scoring the corpus)
holds all 104,000 English passages for the 26 remaining pairs with a `score`.

Logistic regression, char TF-IDF plus 23 surface features, trained on the 3,072
passages where both Opus coders agreed, validated LEAVE-ONE-PAIR-OUT because
every remaining pair is an unseen model. **AUC 0.859.**

Shards take **top-200 per cell**, not a global threshold, so equal counts per arm
hold by construction. Cut lands at score ~0.77, inside the band where the arm gap
is +0.4pp; above 0.90 the gap opens against base.

    cost per narrative passage    unfiltered 7,940 tokens | filtered 2,500 | 3.2x

**Declared cost:** the classifier prefers prototypical scenes, which carry more
free indirect discourse, so it lifts the SHOWN level 35.1% -> 40.7%. Equally in
both arms, and the design is a within-pair difference, so the level shift
cancels. The population is "passages a classifier ranks as confidently
narrative", which is narrower than "narrative passages" and must be said.

# 6. WHAT THE CODED PAIRS SAY

## 6a. SUPERSEDED: what the first three pairs said

Yi-1.5-9B, SmolLM2-360M, neo_7b, on the SAMPLE draw (`p######`), two Opus
coders, 3,210 passages. Agreement 0.785-0.870 across five fields.

That run reported (a) that the amount of interiority does not change
(+0.03, p=1.000) and (b) an INTERACTION with prompt kind -- alignment adding
interiority to EXTERIOR prompts (+0.23) and damping it on INTERIOR ones
(-0.18), 3 of 3 pairs.

**Both are superseded by 6b. Do not quote them.** Kept here because a reader who
finds them in RUBRICS.md or in an old draft needs to know they were withdrawn
rather than lost.

Two further things from that run that DO still stand:

- **`presence` is a word list** -- 92.6% reproducible by a bare mental-state-verb
  regex, which is why it sat at 94% and why "his teeth and claws only thought of
  ripping her apart" counted. Dropped as an estimand.
- **The pilot's F13 relation did not survive.** SHOWN was 29.1% in HOLDS vs 8.0%
  in SHIFTS; on the narrative subset 33.2% vs 41.0%. The pilot computed it over
  all passages including non-narrative.

## 6b. CURRENT: twelve pairs on the TRIAGE draw

Single Opus coder per passage, `effort: 'high'`, top-200 per cell by classifier
score. Reliability re-established ON THIS POPULATION by double-coding L01:
narrative 0.847, mode 0.843, drift 0.819, degree 0.866 -- within 0.035 of the
sample draw, so the instrument did not change when the population did.

**The amount of interiority DOES change, and it is the strongest thing measured.**

    degree, narrative passages   mean +0.350   12/12 up   Wilcoxon p=0.0005
      Instruct stratum   n=9     mean +0.399    9/9 up
      DPO stratum        n=3     mean +0.203    3/3 up

Two confounds tested on the ten-pair version and cleared:

    score-matched (classifier rank held constant)   +0.418   8/10   p=0.010
    MSV-vocabulary residualised                     +0.332   9/10   p=0.004

**The shape is convergence, not a constant shift.** Aligned means occupy
1.72-2.15 across all twelve pairs; base means run 0.58-2.11. Lucie-7B moves
+1.27 from a base of 0.58; Olmo-3-1025-7B moves +0.12 from a base of 1.99.
Alignment pulls models to a common level rather than adding a fixed amount.
Distributionally: degree-3 passages 12.5% -> 24.5%, degree-0 13.0% -> 3.5%.

**The prompt-kind interaction did NOT replicate.** At 12 pairs every stratum
moves the same way -- EXTERIOR +0.366 (8/10, p=0.020), INTERIOR +0.503
(9/10, p=0.004), NEITHER +0.493 (7/9, p=0.039). There is no stimulus
dependence. `mode` (SHOWN | interior) is +0.73, 6/10, p=0.492: **told/shown is
NOT where the effect lives, degree is.**

## 6c. ONE PAIR IS EXCLUDED, AND WHY IT MATTERS

`EXCLUDED_PAIRS` in run.py holds Qwen/Qwen2.5-0.5B with its reason. Its aligned
arm yields 7 narrative passages of 200 (4%) against base's 27 (14%), because the
0.5B instruct model turns fiction prompts into instruction-following exercises
("Can you repeat this sentence, but capitalize it correctly?"). Its codings are
KEPT; it is dropped from the per-pair test only.

**This is the one place the narrative filter's selection bites visibly.** RH's
ruling stands and is correct -- interiority is undefined on a passage with no
scene, so filtering defines the population rather than selecting on an outcome.
But the excluded passages are excluded for an alignment-related reason, so the
YIELD ITSELF is a result and must be reported next to the degree figure, not
silently discarded:

    narrative yield, aligned minus base   mean +9.5pp   7/10 up   p=0.152

Spread is wide (Amber +47.5, TinyLlama +30.5, Lucie -13.5, Qwen2.5-0.5B -10.0)
and the test does not reach significance. Recompute it over all pairs at the end.

# 7. WHERE THE RUN STOPPED, AND WHY

**Paused after L15 with 10 shards uncoded, because the session usage limit was
nearly full.** The reason is external to the data and is recorded here so a later
reader can tell it apart from stopping because a result looked good. The
remaining 10 pairs are L16-L25 and nothing about them was inspected before the
decision.

The earlier plan in this file said: run ten, look once, then decide. That was not
honoured -- the numbers were looked at at 10, 12, 13 and 15 pairs. This is
optional stopping and the run is exploratory. It is the fifteenth exploratory run
with the hypothesis direction known to the designer throughout, and **nothing is
registered.**

## The cheapest available repair, not yet taken

Ten uncoded pairs is a confirmatory arm sitting there for free. A registration
written now -- before L16-L25 are coded -- would state the prediction the first
sixteen produced (+0.237, all pairs positive), the exclusion rule, the estimand
and the test, and then the remaining ten would test it without the designer
having seen them. That is worth more than ten more exploratory pairs.

It requires writing the registration BEFORE launching L16. Launching first and
registering after is worth nothing.

## THE LENGTH CHECK IS NOW MANDATORY, on every pair

Added 2026-08-19 after L13. **Before a pair's delta is used, check that its two
arms overlap in completion length.** Two of fifteen pairs failed this and they
were the two largest effects in the run, in opposite directions:

    bloom-7b1    base median 187 words   aligned   3   raw -1.357
    Lucie-7B     base median  10 words   aligned 201   raw +1.266

A three-word completion cannot contain interiority and cannot drift -- all 158
bloomz passages were coded drift=HOLDS, which is the tell. Both are now in
`EXCLUDED_PAIRS`, under one criterion applied symmetrically.

Across all 15 pairs, degree delta correlated with the arms' length difference at
rho=0.575 (p=0.025). Excluding those two: rho=0.343 (p=0.252). **The correlation
was those two pairs**, and the other thirteen (both arms at median 175-215 words)
have length-matched deltas within 0.09 of raw. So the headline is not a length
artifact -- but that is something to be established per pair, not assumed.

    13 pairs   mean +0.237   13/13 up   p=0.00024   range +0.008 to +0.597

## The recorded prediction

`plans/prediction_bloomz.md`. RH called bloomz to go the other way at 12/12,
before shard-113 existed; it was committed at 05f5d42 before the file it predicts
was written. It held in direction and failed as a measurement, and the file says
both. It is the only thing in this run with a genuine failure mode.

# 8. THE OTHER DOCS

    plans/RUBRICS.md          THE LEDGER. Eleven runs, exact fields, n,
                              agreement, defects, paths. Read this first.
    plans/passC_rubric.md     THE CODER PROMPT. Between two fenced markers,
                              read at build time. Edit here, never in a script.
    RESUME.md                 the cold-start guide and the settled decisions
    plans/prior_drift_work.md M06 and F13, and the trap between them
    results/passC/rejected/   Sonnet codings, with the reason
