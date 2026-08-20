---
subject: drift_geometry
question: What can the geometric drift metrics mean, and do they track what a reader calls staying in the scene?
status: ported 2026-08-20; new analysis NOT yet run
grain: page
---

# drift_geometry

**Two different things in this repo are called "drift" and they are not the same object.**

    HERE          geometric. Computed from SENTENCE EMBEDDINGS of a passage:
                  mean_drift, total_drift, path_length, directedness, ordering.
    ../interiority_in_passages/   CODED. A blind Opus judgment per passage,
                  HOLDS / SHIFTS / UNMOORED, raw 95.0%, kappa 0.904.

Nothing in the audit below reaches interiority's H3, and the reason is worth stating rather than assuming: interiority's drift is a coder reading in order (so order-sensitivity is constitutive), at kappa 0.904 (so not noise-limited), with no directedness and no truncation, aggregated to the lineage pair — which is what the audit tells you to do anyway.

## What the audit established

`drift_metric_audit.md`, migrated verbatim. Four defects, each measured rather than argued:

- **`total_drift` is ORDER-INVARIANT.** It is `1 − min(pairwise cosine)`, the DIAMETER of the passage's sentence set — identical to four decimals after shuffling, every time, while `mean_drift` changes every time. It measures semantic SPREAD, not trajectory, so **an order-invariant axis cannot distinguish a metonymic chain from an undirected scatter of the same diameter.**
- **It is 92% noise at the passage level.** ICC 0.082, against `mean_surprisal`'s 0.371 and `mean_drift`'s 0.141. A minimum over ~10 pairwise similarities among ~5 sentences is the noisiest thing constructible from few units. Reliability by unit: **0.082 per passage, 0.211 per 3-sample cell, 0.988 per pair. Classify pairs, not passages.**
- **`directedness` IS sentence count.** Spearman −0.923, R² 0.795 against 1.681/n. The entire apparent ordering — abstracts most "directed", diary entries most "wandering" — is that abstracts have 3.7 sentences after truncation and diary entries 6.1.
- **The 75-word truncation analyses 46% of each generation** while RETAINING FEWER passages (86.1%) than no truncation (95.1%).

Its ruling: use `mean_drift` over `total_drift`, and for shape use the within-passage **ordering** contrast, which is n-controlled by construction.

## The open question this folder exists for

**The audit compared the metrics against each other and never had an external criterion.** `../interiority_in_passages/` has one: 13,565 passages coded HOLDS / SHIFTS / UNMOORED by blind Opus readers, 3,610 of them double-coded.

    HOLDS 12,099 | SHIFTS 2,835 | UNMOORED 2,241

So: **does `mean_drift` track what a reader calls staying in the scene, and does `total_drift` fail to?** If it does, that is independent confirmation of the audit's ruling by an instrument the audit did not have. If neither tracks, the geometric family is not measuring scene-holding at all — also worth knowing.

**The design is forced by the audit's own findings, and the obvious version of it is the wrong one.** A per-passage correlation is exactly the analysis ICC 0.082 predicts will classify near-randomly, so a null there would be unidentifiable — metric doesn't measure it, or metric too noisy at this unit. Instead:

- **group means, not per-passage correlation.** One passage's drift is mostly noise; the MEAN over 12,099 HOLDS passages is not. Ask whether mean `mean_drift` differs across the three coded classes.
- **hold `n_sents`**, because defect 3 is that directedness is sentence count and UNMOORED passages are plausibly just longer.
- **test within arm**, because interiority finds aligned passages HOLD more and the audit notes drift falls under alignment — pooling lets the arm manufacture the association.
- **use coder agreement as a purity filter** on the 3,610 double-coded passages.

Nothing above has been run. `PROVENANCE.md` carries the metric definitions verbatim so a new number stays comparable to the audit's.

## Where the code comes from, and where it does not

`archive/` is REFERENCE, not a dependency. **`corpus_metrics.py` is v1-era** (last substantive commit 2026-05-07, three months before the audit that reads its output) and **`embedding.py` is superseded by `malignment/vectors.py`**, which is ClickHouse-first, batches its misses, and degrades to slow-but-correct rather than failing the analysis. New work takes the 25 lines of metric DEFINITION from the archive and the embedding from the current repo.

Sentence vectors go to `$MALIGNMENT_DATA` as parquet rather than ClickHouse: nobody queries an individual sentence vector, the reusable artifact is the per-passage metrics, and the bare-word table's own docstring forbids mixing spaces.

## Two pieces of producer debt, pointing opposite ways

**The audit has no producer** — no Producers section, its four measurements computed inline, which by this campaign's rule makes them unauditable. They ARE recomputable from `results/corpus_metrics.parquet`, which is why it was ported.

**And its producer has no finding.** `archive/m06_ordering_figs.py` is named in no M06 document — one of 19 such scripts out of 47 — yet carries the audit's numbers verbatim and reports something no finding states: **the arm contrast on `ordering` is null, 11 up / 14 down in English, p 0.69.** The measure the audit recommends shows no alignment effect, and that is currently legible only to whoever opens a plotting script.
