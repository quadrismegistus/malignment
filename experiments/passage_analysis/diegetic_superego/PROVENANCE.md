# PROVENANCE

Copied VERBATIM from the read-only archive `github.com/quadrismegistus/malign-logits` at commit

    5c4b5ce60b2685dc0e7083ef8aad5ed858e216de

Nothing under `scripts/` has been edited. Their internal paths refer to the ARCHIVE's layout, so they do not run unmodified from here; that is deliberate, and a run should be a wrapper calling the same design rather than a patched copy.

sha256-verified against the archive at copy time: **8 of 8 match**.

## NOT COPIED, AND THIS ONE MATTERS

`y_confirmatory_coded.jsonl` is **143.9 MB** -- the confirmatory codings the
finding rests on, and nearly double this repo's 75 MiB commit cap. Behind it sit
the raw passage shards under the archive's `data/raw/passage_corpus/`, which run
to gigabytes. Both stay in the archive:

    malign-logits meta/M01_displacement/results/y_confirmatory_coded.jsonl
    malign-logits registrations/y_annotation_manifest.jsonl   (17.4 MB)

So **what is here reproduces the ANALYSIS, not the coding**. `y_diegetic.py` reads
the confirmatory file directly, so it does not run from this repo without it. The
pilot codings ARE here and are what a reader can check the shape of the thing
against.

| file | archive path | bytes | sha256 (16) | note |
| --- | --- | ---: | --- | --- |
| `scripts/y_diegetic.py` | `meta/M01_displacement/scripts/y_diegetic.py` | 8135 | `fd46df91b0ef71f5` | the producer |
| `Y_diegetic_superego.md` | `meta/M01_displacement/findings/Y_diegetic_superego.md` | 16346 | `0d30774aec86721e` | the finding |
| `results/y_diegetic.log` | `meta/M01_displacement/results/y_diegetic.log` | 7284 | `6100335cd79a332a` | the run log |
| `results/y_guilt_heterogeneity.json` | `meta/M01_displacement/results/y_guilt_heterogeneity.json` | 9625 | `719e427b25504358` |  |
| `results/y_v3_regression.jsonl` | `meta/M01_displacement/results/y_v3_regression.jsonl` | 68713 | `8751ddf0ffe2709e` |  |
| `results/y_pilot_coded.jsonl` | `meta/M01_displacement/results/y_pilot_coded.jsonl` | 1422087 | `59ed0693c7dc46dc` | pilot codings |
| `results/y_pilot_coded_v2.jsonl` | `meta/M01_displacement/results/y_pilot_coded_v2.jsonl` | 2026788 | `5d3bbe7ac7ee234f` |  |
| `results/y_pilot_coded_v3.jsonl` | `meta/M01_displacement/results/y_pilot_coded_v3.jsonl` | 1127554 | `830db8d24391a09e` |  |
