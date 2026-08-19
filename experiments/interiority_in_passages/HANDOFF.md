# HANDOFF: running the Pass C lineage shards

For a session that knows nothing. Everything needed is in this repo or in
`$MALIGNMENT_DATA`; nothing needed is in a Claude session directory.

Written 2026-08-19, mid-run: **3 of 29 lineage pairs coded, 26 to go.**

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

# 6. WHAT THE THREE CODED PAIRS SAY

Yi-1.5-9B, SmolLM2-360M, neo_7b. 3,210 passages, two Opus coders.
Agreement 0.785-0.870 across five fields; told/shown 0.851 on 2,086.

**The amount of interiority does not change.**

    degree, narrative passages   base 1.720 -> aligned 1.750   +0.03   p=1.000
    any interiority              94.7% -> 94.3%                        p=1.000

**And `presence` should be dropped: it is a word list.** 92.6% reproducible by a
bare mental-state-verb regex, which is why it sits at 94% and why "his teeth and
claws only thought of ripping her apart" counts as interiority.

**The finding is an INTERACTION with what the prompt supplies:**

                          mean degree      SHOWN | interior
    EXTERIOR prompts         +0.23              +4.4       2 of 3 pairs
    INTERIOR prompts         -0.18             -13.2       3 of 3 pairs

Alignment adds interiority to prompts that supply none and damps it on prompts
that supply some. The pooled figure is those two cancelling, which is what made
it look like a null. **This is the only 3-of-3 in anything measured.**

Powered for: at ~113 narrative per cell over 26 pairs the interaction MDE is
8.5pp against 17.6pp observed, and the INTERIOR-prompt effect 6.0pp against
13.2pp. The pooled statistic is NOT powered and should not be the target.

## Two things that did not survive

**The pilot's F13 relation.** SHOWN was 29.1% in HOLDS vs 8.0% in SHIFTS;
on the narrative subset it is 33.2% vs 41.0%. The pilot computed it over all
passages including non-narrative.

**Presence as primary.** Declared before data, at ceiling once data arrived.
Demoting it is a change of estimand AFTER seeing numbers and is recorded as such,
dated, with both statistics to be reported. The defence is that the ceiling is a
property of the filter and holds whichever way the arms fall. That is a defence,
not an exemption.

# 7. STOPPING RULE, NOT YET SET

26 shards can be stopped after any one, which is convenient and is also optional
stopping. Decide before looking: run ten, look once, then decide about the
remaining sixteen. Nothing is registered -- eleven exploratory runs with the
hypothesis direction known to the designer throughout.

# 8. THE OTHER DOCS

    plans/RUBRICS.md          THE LEDGER. Eleven runs, exact fields, n,
                              agreement, defects, paths. Read this first.
    plans/passC_rubric.md     THE CODER PROMPT. Between two fenced markers,
                              read at build time. Edit here, never in a script.
    RESUME.md                 the cold-start guide and the settled decisions
    plans/prior_drift_work.md M06 and F13, and the trap between them
    results/passC/rejected/   Sonnet codings, with the reason
