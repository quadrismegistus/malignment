# RESUME: picking Pass C up in a new session

For a context that knows nothing. Everything needed is in this repo or in
`$MALIGNMENT_DATA`; nothing needed is in a Claude session directory.

    cd ~/github/malignment && source .venv/bin/activate
    cd experiments/interiority_in_passages
    python run.py --passc-todo

That one command tells you where the run stands. Everything below explains it.

---

# 1. WHAT THIS EXPERIMENT IS ASKING

Does alignment change what KIND of scene a model writes -- from exterior event
toward interior state? RH's exhibit, one prompt, two models:

    BASE      stood, pulled, aimed, pulled the trigger, exploded
    INSTRUCT  reached, dialed, knew, had to talk, rang

That is `P_unnamed_axis.md`'s INTERIORITY (*enacted -> represented*) at passage
scale. Substrate is `f11_l2`, the only generated corpus whose prompts are
unanimously OPEN.

**Read `plans/RUBRICS.md` before touching anything.** It is the ledger: every
coding run so far with its exact fields, n, coders, agreement, and defects. Six
runs are recorded. It exists because the design changed six times and the
reasons are not reconstructible from the code.

# 2. THE STATE, AND WHICH FILES ARE LOAD-BEARING

    plans/passC_rubric.md          THE CODER PROMPT. run.py reads the text
                                   between the two fenced markers and embeds it
                                   verbatim in every shard. Edit this file and
                                   the next shard uses it. Never edit a
                                   generated script.

    results/passC/sample.parquet   THE FROZEN SAMPLE. 41,412 English passages,
                                   714 per cell, 29 lineages, 58 models, arms
                                   20,706/20,706. Seed 20260818; rebuilding is
                                   byte-identical (sha 37c0b1cadda4a212).

    results/passC/corpus_manifest.json
                                   Points at the FULL population, which lives
                                   OUTSIDE the repo:
                                   $MALIGNMENT_DATA/f11_l2/f11_l2_full.parquet
                                   228,520 rows, 72.7 MB, sha recorded here.
                                   Default $MALIGNMENT_DATA is ~/malignment-data.

    results/passC/scripts/*.js     The shard workflows. GENERATED -- regenerate
                                   rather than edit.
    results/passC/plan.json        Which lineages each shard covers.
    results/passC/codings/*.json   Saved shard results. THE ONLY DURABLE RECORD
                                   OF CODING WORK. One file per shard.

**No ClickHouse is needed to continue.** The sample is the file. `run.py --passc-*`
touches the database only for `--passc-sample` and `--passc-corpus`, both of
which are already done and should not be re-run.

# 3. HOW TO CONTINUE

    python run.py --passc-todo        # per-coder coverage, stray ids, what is left
    python run.py --shards 6          # regenerate scripts for ONLY what is left

`--shards` subtracts everything already in `codings/`, so it is safe to re-run
and it never re-issues coded ids. Then launch each script as its own workflow:

    Workflow({scriptPath: ".../results/passC/scripts/shard-00.js"})

Six separate top-level invocations, not one. The agent concurrency cap is
`min(16, cores-2)` PER WORKFLOW -- 10 on this machine -- so six shards give 60
concurrent agents. The cap is set by local CPU count and the work is API calls,
which is why routing around it is worth doing.

**Save each shard the moment its workflow returns:**

    python run.py --passc-save /path/to/<task-id>.output

It refuses to overwrite an existing shard file. Then `--passc-todo` again.

## Sizing, so you know what you are launching

    535 of the frozen 714 per cell = 31,030 passages = the n=150 target
    x 2 coders = 62,060 codings, ~1,382 agents at 45 per batch
    ~11.7K tokens in and ~2.7K out per agent  ->  ~16M in, ~3.7M out

Raising n later means raising `--per-cell-now` toward 714. Ids are taken in the
sample's own order, so that ADDS ids and never disturbs coded ones. **Any
extension must be uniform across all cells.** Extending only where the effect
looked promising is the one thing that would compromise this design.

# 4. IF A SHARD FINISHED BUT WAS NEVER SAVED

Workflow artifacts are keyed by SESSION UUID and a new session has a new one.
This run was built in session `cdbe9c9e-a018-45bf-95e9-6bf81e96e908`.

    ~/.claude/projects/<proj>/<uuid>/workflows/scripts/     survives reboot
    ~/.claude/projects/<proj>/<uuid>/subagents/workflows/<run>/journal.jsonl
                                                           per-agent results
    /private/tmp/claude-502/<proj>/<uuid>/tasks/*.output    the return value,
                                                           LOST ON REBOOT

If a `.output` survives, `--passc-save` it. If not, do nothing special: rerun
`--shards` and that shard's ids come back as TODO. **The cost of a lost shard is
recoding it, and nothing else is corrupted** -- which is the entire reason the
run is sharded.

# 5. DECISIONS ALREADY MADE. DO NOT RE-LITIGATE THESE.

Each cost an argument. `plans/RUBRICS.md` has the evidence.

- **29 lineages, not `roster.endpoints()`'s 22.** Endpoints picks one aligned arm
  per base and wanted arms this corpus does not have, dropping 7 whole lineages
  -- including the only three base-vs-DPO contrasts and Mistral->zephyr. "Every
  lineage with both arms present" is a rule with no discretion in it.
- **Aligned is not one thing**: Instruct for 25, DPO for 3, zephyr for 1. A
  DECLARED STRATUM, not a nuisance.
- **`mode` (NONE/TOLD/SHOWN) is primary, not the 0-3 degree scale.** Measured:
  mode kappa 0.893 against degree 0.797 on the same random 20. Degree merges the
  two modes at the top of its range, which is where the argument lives.
- **Free indirect discourse is NEVER named to a coder.** RH's ruling. The
  operational description reaches it anyway -- two of three coders independently
  quoted `Poor darling.`, two unattributed words inside 1,200 characters.
- **`narrative` excludes `furniture`.** Admitting web paratext was a defect: it
  was 21% of the Pass B set, base-heavy, and carried most of a drift result that
  fell from +17.4pp to +5.4pp once removed.
- **Wilcoxon signed-rank on per-pair rate differences is the test.** NOT a sign
  test -- the statistic is a rate difference measured identically in every pair,
  so magnitudes are comparable and discarding them is pure power loss. RH:
  *"why do you keep proposing sign tests and throwing away magnitude."*
- **The unit is the LINEAGE PAIR, never the passage.** Demonstrated the hard way:
  the Pass B pilot's passage-level pooling said aligned was 11.2pp LESS interior;
  per pair it was 7 up / 8 down / 4 tied, p=1.000.
- **English only.** Stage 1 is English on 29 pairs. Chinese is a separate
  replication on the 8 `cjk_tier` FLUENT pairs, and an English-designed rubric
  is a different instrument on Chinese.
- **`charge` and `why` are cut.** Charge because this corpus has no transgression
  in it; `why` because it agreed at 0.773 and fed nothing.

# 6. WHAT IS NOT DONE

- **The report.** Wilcoxon on per-pair rate differences, alignment stage as a
  stratum, prompt kind (EXTERIOR/INTERIOR/NEITHER) and quintuplet role as
  crossed strata, and sigma_het estimated from the first shards.
- **Nothing is registered.** Six exploratory runs, the hypothesis direction known
  to the designer throughout. The arm question came back NULL on the correct
  unit in the pilot, so there is no result being protected -- which makes now the
  cheapest moment to register, before the numbers exist.
- **The embedding comparison.** Recompute `mean_drift` and M06's `ordering` on
  the coded rows and set them beside the human `drift`. See
  `plans/prior_drift_work.md` -- and note the trap recorded there: M06's stored
  `sample_idx` is the ALPHABETICAL RANK of the text within its cell, not the
  corpus's sample_idx, so joining on it lands in the right cell and the wrong
  row.
- **Stage 2, Chinese**, on the 8 fluent pairs.
