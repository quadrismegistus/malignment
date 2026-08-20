# PROVENANCE

Copied VERBATIM from the read-only archive `github.com/quadrismegistus/malign-logits`
at commit

    5c4b5ce60b2685dc0e7083ef8aad5ed858e216de

sha256-verified at copy time: **8 of 8 match**.

## `archive/` IS REFERENCE, NOT A DEPENDENCY

Nothing in `archive/` is meant to run here, and two of its four files are known
stale rather than merely relocated:

- **`corpus_metrics.py` is v1-era.** Last substantive commit 2026-05-07, in a repo
  running to 2026-08-19 -- so the audit (2026-08-13) analyses a parquet built three
  MONTHS earlier by a script from the project's first quarter. The audit still
  stands, because its defects are properties of the metric DEFINITIONS and those
  did not change; but this is not code to build on.
- **`embedding.py` is superseded by `malignment/vectors.py`** for everything to do
  with embedding. It calls SentenceTransformer directly with no store;
  `vectors.py` is ClickHouse-first, batches its misses, and degrades to
  slow-but-correct on a store failure rather than failing the analysis. What
  `embedding.py` still has that `vectors.py` does not is the 25 lines that matter
  here: `drift_metrics_from_embeddings` and `_split_sentences`.

**So new work reuses the DEFINITIONS and not the machinery.** The definitions are
what must not drift if a new number is to be comparable to the audit's; the
embedding layer is the part where the current repo is better.

## The definitions, quoted so they cannot drift silently

    step_dists[i] = 1 - cos(sv[i], sv[i+1])       consecutive -- ORDER-SENSITIVE
    mean_drift    = mean(step_dists)
    total_drift   = 1 - min(sim_matrix)           the DIAMETER -- order-INVARIANT
    path_length   = sum(step_dists)               == (n_sents - 1) * mean_drift
    directedness  = total_drift / path_length     hence its dependence on n

`ordering`, the audit's recommended replacement for `directedness`, is defined in
`archive/m06_ordering_figs.py`:

    ordering = mean(successive distances) - mean(all pairwise distances)

## Two pieces of producer debt, in opposite directions

**The audit has no producer.** `drift_metric_audit.md` carries no Producers
section; its four defect measurements -- the shuffle test, the ICC decomposition,
the Spearman -0.923, the truncation count -- were computed inline and exist in no
script. By this campaign's own rule that makes them UNAUDITABLE.

**And its producer has no finding.** `m06_ordering_figs.py` is named in no M06
document (one of 19 such scripts of 47), yet it carries the audit's numbers
verbatim AND reports something no finding states: **the arm contrast on `ordering`
is null, 11 up / 14 down in English, p 0.69.** The measure the audit tells you to
use shows no alignment effect, and that fact is currently legible only to someone
who opens a plotting script.

| file | archive path | bytes | sha256 (16) | last commit | note |
| --- | --- | ---: | --- | --- | --- |
| `drift_metric_audit.md` | `meta/M06_generation/findings/drift_metric_audit.md` | 12302 | `efc1a8be542e3aa6` | 2026-08-14 | the finding. NO Producers section -- see below |
| `results/corpus_metrics.parquet` | `data/corpus_metrics.parquet` | 25427374 | `aaeb1589b27f83c3` | 2026-05-07 | 76,214 rows x 26 cols; the audit's evidence |
| `results/corpus_metrics.md` | `data/corpus_metrics.md` | 12877 | `c91db70784262149` | 2026-05-07 | its summary tables |
| `results/crosslingual_ordering_full.json` | `meta/M06_generation/results/crosslingual_ordering_full.json` | 9322 | `c0c28258ab38452e` | 2026-08-15 | the booked `ordering` result |
| `archive/corpus_metrics.py` | `scripts/corpus_metrics.py` | 29877 | `cb852908265f24da` | 2026-05-14 | REFERENCE ONLY -- v1-era |
| `archive/embedding.py` | `malign_logits/embedding.py` | 42058 | `fe7b8d1728a10377` | 2026-07-05 | REFERENCE ONLY -- superseded by malignment/vectors.py |
| `archive/m06_ordering_figs.py` | `meta/M06_generation/scripts/m06_ordering_figs.py` | 13771 | `b3c108d446b16503` | 2026-08-15 | UNDECLARED in every M06 document |
| `archive/m06_crosslingual_ordering.py` | `meta/M06_generation/scripts/m06_crosslingual_ordering.py` | 6333 | `ac1232d631d3fe22` | 2026-08-15 | computes `ordering`; declared in crosslingual_arms.md |
