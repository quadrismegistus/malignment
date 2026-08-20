# PROVENANCE

Copied VERBATIM from the read-only archive `github.com/quadrismegistus/malign-logits`
at commit

    5c4b5ce60b2685dc0e7083ef8aad5ed858e216de

Nothing under `scripts/` has been edited; their paths are the ARCHIVE's, so they do
not run unmodified from here. A run should be a wrapper calling the same design.

sha256-verified against the archive at copy time: **18 of 18 match**.

## Two locations, one rule

`results/` holds what fits (4.7 MB). `data/` is a relative symlink to
`$MALIGNMENT_DATA/selection_and_combination/` holding the three parquets that do
not -- 369 MB, against this repo's 75 MiB commit cap. Git tracks the link as a
mode-120000 blob of the target string, so the pre-commit size hook sees the link
and not the target.

The target is RELATIVE because an absolute one bakes in `/Users/rj416` and breaks
on the other machine, whose user is `ryan`. **`$MALIGNMENT_DATA` is authoritative
and the link is a convenience for the default layout**; a clone without the data
root gets a dangling link, which fails ENOENT -- absence reading as absence.

## The corpus is not here either

`gen_sequences`, `corpus='passage'`: 1,142,944 self rows and 1,142,944 cross rows,
live in ClickHouse. The same table `../predicting_aligned_text/` inherits.

| file | archive path | bytes | sha256 (16) | note |
| --- | --- | ---: | --- | --- |
| `composition_not_level.md` | `meta/M06_generation/findings/composition_not_level.md` | 19712 | `912accaa0ba2e7c3` | the finding |
| `plan_mediation.md` | `meta/M06_generation/plans/plan_mediation.md` | 9060 | `3e0d974cdaaf7c48` | pre-registered BEFORE any producer existed |
| `scripts/m06_mediation.py` | `meta/M06_generation/scripts/m06_mediation.py` | 14432 | `445bd223e26a1bec` | stage 1 (--by-prompt) |
| `scripts/m06_mediation_read.py` | `meta/M06_generation/scripts/m06_mediation_read.py` | 17451 | `357d8684890fede7` | the decomposition |
| `scripts/m06_mediation_corr.py` | `meta/M06_generation/scripts/m06_mediation_corr.py` | 7575 | `65228f471e600dd3` | continuous correlation (Result 2) |
| `scripts/m06_mediation_ctx.py` | `meta/M06_generation/scripts/m06_mediation_ctx.py` | 5795 | `34e716392dd557c5` | per-context control (Result 4) |
| `scripts/m06_mediation_contrast.py` | `meta/M06_generation/scripts/m06_mediation_contrast.py` | 9447 | `4db6450f8bbeeb7d` | PRODUCER DEBT, discharged 2026-08-14 -- the surviving claim had existed in no script |
| `results/mediation_corr_words.parquet` | `meta/M06_generation/results/mediation_corr_words.parquet` | 4287922 | `1ee48b296a0233d7` | per-word scores |
| `results/mediation_pilot.parquet` | `meta/M06_generation/results/mediation_pilot.parquet` | 504678 | `19feccac84a105d5` |  |
| `results/mediation_pairs.parquet` | `meta/M06_generation/results/mediation_pairs.parquet` | 11244 | `2d0f51728bc5da1d` | the 36 pairs |
| `results/mediation_gate.json` | `meta/M06_generation/results/mediation_gate.json` | 7952 | `7af00d8ee3bf5ea5` |  |
| `results/mediation_readings.json` | `meta/M06_generation/results/mediation_readings.json` | 2278 | `412628c6fc20c45d` |  |
| `results/mediation_ctx.json` | `meta/M06_generation/results/mediation_ctx.json` | 360 | `b00e517d13091634` |  |
| `results/mediation_corr.json` | `meta/M06_generation/results/mediation_corr.json` | 1585 | `0ce97ffb309947f2` |  |
| `results/mediation_contrast.json` | `meta/M06_generation/results/mediation_contrast.json` | 2260 | `5bb37f81f63301dc` | the contrast on common support |
| `data/mediation_words_byprompt.parquet` | `meta/M06_generation/results/mediation_words_byprompt.parquet` | 277973063 | `dc545a396eab485c` | Result 4's 848,453 cells |
| `data/mediation_words.parquet` | `meta/M06_generation/results/mediation_words.parquet` | 64908385 | `a09425534f265b96` |  |
| `data/mediation_words_joined.parquet` | `meta/M06_generation/results/mediation_words_joined.parquet` | 44351858 | `c820bf3160846fe2` |  |
