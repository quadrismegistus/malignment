# PROVENANCE

Every file here was copied VERBATIM from the read-only archive
`github.com/quadrismegistus/malign-logits` at commit

    5c4b5ce60b2685dc0e7083ef8aad5ed858e216de   (2026-08-19)

and nothing in `scripts/` has been edited. **The scripts' internal paths refer to
the ARCHIVE's layout** (`ROOT`, `meta/M06_generation/...`, `data/...`), so they do
not run unmodified from here. That is deliberate: patching them would create a
third variant that is neither the archive's code nor this repo's, and repairing a
historical artifact is a failure mode this campaign has already paid for. To run
anything, write a wrapper in this repo's idiom that calls the same design, and
leave these bytes alone.

Verified by sha256 against the archive at copy time: **20 of 20 match**.

## The corpus is NOT here

`malign_logits.gen_sequences`, `corpus='passage'` -- 1,142,944 rows over 84 models
and 198 prompts, live in ClickHouse. The producers reach it with
`subprocess` + `clickhouse client`, which is also how
`../interiority_in_passages/run.py` does it and which sidesteps the
`malignment.ch` cross-database guard without fighting it.

## What is what

`results/inputs/` is what the producers READ. `results/archive/` is what the
archive's run PRODUCED -- the reproduce target. Keep them apart: the first
question to ask of any rerun is whether it returns `results/archive/`'s numbers,
and that check is only possible while it is obvious which files are which.

| file | archive path | bytes | sha256 (16) | note |
| --- | --- | ---: | --- | --- |
| `scripts/m06_p_on_passages.py` | `meta/M06_generation/scripts/m06_p_on_passages.py` | 18402 | `5ecf42f3e79934d6` | I2/I3/I4/I5 |
| `scripts/m06_p_on_passages_marked.py` | `meta/M06_generation/scripts/m06_p_on_passages_marked.py` | 8625 | `a18e0d6549a90133` | I6 -- the one with the gap |
| `scripts/m06_p_on_passages_sitexword.py` | `meta/M06_generation/scripts/m06_p_on_passages_sitexword.py` | 6077 | `c48ffc5808d86fd0` | I7 -- NOT QUOTABLE |
| `scripts/m06_p_on_passages_ascent.py` | `meta/M06_generation/scripts/m06_p_on_passages_ascent.py` | 7699 | `a85573ca2c2c9fce` | ascent branch, dead |
| `scripts/z_second_order.py` | `meta/M02_frame_exit/scripts/z_second_order.py` | 14386 | `dc68256bafd584bd` | M02 marker instrument, imported by ascent |
| `results/inputs/forced_arms_46reps_drmatch.json` | `data/forced_arms_46reps_drmatch.json` | 9148734 | `89eb642b50d00dd9` | forced-arm corpus; I5 + ascent only |
| `results/inputs/m06_text_flags.parquet` | `meta/M06_generation/data/m06_text_flags.parquet` | 1310441 | `d0ba9d52a0ac3f87` | per-passage screen flags |
| `results/inputs/embed_en_glove.npz` | `meta/M01_displacement/results/k/embed_en_glove.npz` | 6782921 | `7ac07c468f6a6a6c` | GloVe 300d over 6,084 words |
| `results/inputs/axis_en.json` | `meta/M01_displacement/results/k/axis_en.json` | 8128 | `3aa704cef57a58b4` | P's axis; one-axis AUC 0.683 |
| `results/inputs/word_auc_en.tsv` | `meta/M01_displacement/results/k/word_auc_en.tsv` | 195773 | `1ded232d1c205509` | per-word arm AUC |
| `results/inputs/word_auc_en_passageprompts.tsv` | `meta/M01_displacement/results/k/word_auc_en_passageprompts.tsv` | 29229 | `107e37063992f5bd` | same, passage prompts |
| `results/archive/p_on_passages.json` | `meta/M06_generation/results/p_on_passages.json` | 121863 | `c4e82847a2d23d2b` | I2-I5 output |
| `results/archive/p_on_passages_marked.json` | `meta/M06_generation/results/p_on_passages_marked.json` | 3910 | `0d7c06a8d54e3e22` | I6 output + the six-domain table |
| `results/archive/p_on_passages_sitexword.json` | `meta/M06_generation/results/p_on_passages_sitexword.json` | 1852 | `b7f60a230934f5fd` | I7 output |
| `results/archive/p_on_passages_ascent.json` | `meta/M06_generation/results/p_on_passages_ascent.json` | 2515 | `e6caa330dea12575` | ascent output |
| `results/archive/p_on_passages_smoke.json` | `meta/M06_generation/results/p_on_passages_smoke.json` | 348 | `5d4aefd9864509bb` | smoke run |
| `results/archive/p_on_passages_i5_cells.parquet` | `meta/M06_generation/results/p_on_passages_i5_cells.parquet` | 5353191 | `23827d4f39411d82` | per-cell I5 |
| `results/archive/p_on_passages_i6_cells.parquet` | `meta/M06_generation/results/p_on_passages_i6_cells.parquet` | 121227 | `2cd319c54dfeb800` | per-cell I6 |
| `results/archive/p_on_passages_i7_drag.parquet` | `meta/M06_generation/results/p_on_passages_i7_drag.parquet` | 104656 | `d75fb79a4de714f3` | per-cell I7 drags |
| `plan_p_on_passages.md` | `meta/M06_generation/plans/plan_p_on_passages.md` | 11634 | `42d145e7de6f5ed1` | the pre-registration |

## The number to reproduce first

`scripts/m06_p_on_passages_marked.py` produced `results/archive/p_on_passages_marked.json`:

    I6a  aligned MARKED - UNMARKED   +0.00256   1443/1006   p=1e-18
         base    MARKED - UNMARKED   +0.00265   1430/951    p=8e-23
    I6b  DiD                         -0.00015   1187/1194   p=0.90

    six domains: animal betrayal property sexual taboo violence
    (identity and institutional are ABSENT -- that gap is why this folder exists)

If a rerun does not return those, stop and find out why before extending anything.
