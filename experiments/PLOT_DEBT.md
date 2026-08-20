---
subject: plot_debt
status: audited 2026-08-20
question: What has produced results and cannot be looked at?
---

# Plot debt across experiments/

**3,327 result files, 18 figures, and 28 of 32 experiments with results have no figure at all.** That headline is true and it is also misleading, which is the first thing this audit has to say.

## Most of that number is NOT plot debt

Two experiments hold 2,308 of the 3,327 files:

    slot_ratings                              1,262 json  (per-shard ratings)
    passage_analysis/interiority_in_passages  1,046 json  (per-shard codings)

These are raw per-shard codings. **No plot of any kind can bind to them** until a producer aggregates them into something with rows and columns. Counting them as plot debt makes the problem look like a drawing problem when it is a producing one, and it would send a seat to write a figure that has no table to draw.

`slot_ratings` already carries a `plot.py`, which makes the point sharply: the drawing code exists and the aggregate does not.

**So the ladder from `meta/producer-debt.md` applies here unchanged.** A missing producer makes a number unauditable; a missing artifact makes it unreproducible; only then does a missing figure leave a communicated result undrawn. Two of the three largest entries below are on the wrong rung to be called plot debt.

## What is genuinely plot-ready, ranked

The ranking is by what INTERACTIVE plotting buys, not by file count. A result that wants one static plate is not more urgent because it has more rows.

### 1. division_of_labour — three questions, zero figures

    lexical_domains   11 results   by_chain.csv 18 rows, by_chain_domain 558,
                                   by_word 275, mass_destination 4
                                   cells.csv 67,601 for drill-down
    removal_rates      9 results   by_lineage 16, chains 18, sets 5,966
                                   cells.csv 273,918
    sft_share          2 results   by_chain 18, by_chain_domain 558

The question is *which alignment stage carries the displacement*, over 18 chains at base / SFT / pref. **Inherently comparative and inherently browsable**: no single static figure answers it for all 18, and the archive's M05-H found the stages disagree in SIGN (SFT installs the norm signature, DPO buys part of it back, RLVR re-suppresses), which is precisely the shape a reader needs to step through rather than be shown once.

First, and by some distance.

### 2. displacement_taxonomy — the direction finding has no figure

    crosslineage_rows.csv  1,151 rows   prompt, status, operation, model, base/aligned words
    word_groups.csv          989 rows
    categories_traced.csv  1,019 rows
    word_groups/*.txt         40 files  per-prompt pooled vocabularies

40 prompts x 26-29 lineages, each lineage a member, reversed, or unassigned. **Statically this is 40 figures; interactively it is one panel with a prompt selector.** The result it would show -- 27 of 29 lineages reverse the dominant operation somewhere -- currently exists only as numbers in a commit message and two markdown documents.

### 3. displacement_axis — 45 results, 0 figures

    scale_rho.csv       2,389   per prompt x scale
    predict_frames.csv  7,555
    protocol_growth     1,086
    mass_cells          4,402 rows x 56 columns

Per-prompt, per-scale, per-lineage. Was invisible to the register until 2026-08-20 (its producers are named `analyze.py`, `report.py`, so the `run.py` discovery key never matched), which is the likeliest reason nobody drew it.

### 4. instrument_calibrations — thirteen questions, two figures

Mostly small tables: `screening_base/by_model` 56, `generic_axis/per_pair` 13, `prompt_openness/openness` 482, `numeric_boundary/depth` 160. Individually low value; **collectively one small-multiples grid would discharge thirteen debts at once**, and calibrations are exactly the thing a reader wants to scan rather than study.

### Below the line, and honestly so

`salary_probe` (PARKED after a two-lineage pilot, 4-row tables), `posttraining_corpus_analysis/*` (2-16 results each), the passage_analysis questions other than interiority. Real results, small, and no reader is currently blocked on seeing them.

## What this implies about how to draw

The three top entries are all **parameterised**: a prompt, a chain, a scale. That is an argument for the web path (a spec the panel renders, one selector) rather than for forty PNGs. The two largest tables -- `removal_rates/cells.csv` at 273,918 rows and `lexical_domains/cells.csv` at 67,601 -- cannot ship to a browser whole, so the aggregation has to happen in the producer either way.

Which is the case for keeping the figure logic in each experiment's own `plot.py`: the aggregation and the drawing are the same decision, and splitting them puts the choice of what to show in one repo and the choice of what to compute in another.

## The count, for the record

    experiments with results                 32
    of those, with no figure at all          28
    result files                          3,327   (2,308 of them per-shard json)
    tabular results (csv/parquet)            130
    figures                                   18
    experiments carrying a plot.py             3
