---
kind: question
subject: drift_geometry
question: What can the geometric drift metrics mean, and do they track what a reader calls staying in the scene?
status: RUN 2026-08-20 (ported)
grain: page
requires: |
  stanza (>=1.14) plus its `en` tokenize model, and sentence-transformers for
  BAAI/bge-m3 via malignment.slot_axis. NEITHER IS IN requirements.txt, and that
  is not an oversight to fix here: that file declares itself DERIVED from the
  imports of `malignment/*.py` by AST walk, so an experiment's dependency is out
  of its scope by construction. About eleven third-party packages are undeclared
  across experiments/ on the same grounds -- scipy, plotnine, pyarrow, pydantic,
  sklearn, matplotlib, wordfreq, datasets, nltk, stanza, sentence-transformers.
  A clone can import the package and run no experiment. Recorded here rather than
  patched, because hand-editing requirements.txt would be undone by the next
  regeneration and would hide the real gap.
headline: "the metrics track the coded judgment"
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
- **It is 92% noise at the passage level** — ICC 0.082, against `mean_surprisal`'s 0.371. Reliability by unit: 0.082 per passage, 0.211 per 3-sample cell, **0.988 per pair. Classify pairs, not passages.** *But read the correction immediately below before quoting the 0.082.*
- **`directedness` IS sentence count.** Spearman −0.923, R² 0.795 against 1.681/n. The entire apparent ordering — abstracts most "directed", diary entries most "wandering" — is that abstracts have 3.7 sentences after truncation and diary entries 6.1.
- **The 75-word truncation analyses 46% of each generation** while RETAINING FEWER passages (86.1%) than no truncation (95.1%).

Its ruling: use `mean_drift` over `total_drift`, and for shape use the within-passage **ordering** contrast, which is n-controlled by construction.

### The audit corrected its own headline a day later, and that correction is about US

`drift_metric_audit.md` carries an addendum dated 2026-08-14: **"defect 2 was SCOPED TOO WIDELY — '92% noise' is the instrument, not the metric."** The 0.082 was measured with `paraphrase-multilingual-MiniLM-L12-v2` on the F15 passage population. The same decomposition with **`BAAI/bge-m3` on `f11_l2`**:

    lang regime  metric        ICC
    zh   trunc   mean_drift   0.567
    en   full    mean_drift   0.521
    en   trunc   total_drift  0.454
    zh   trunc   total_drift  0.449

**Four to six times the reliability.** Its corrected claim: reliability is a property of the *(corpus, embedder, truncation)* triple and must be measured per instrument, never inherited.

**That configuration — bge-m3 on f11_l2 — is exactly the one this folder uses.** So the headline number does not apply to anything measured here, and an earlier version of this README quoted it twice while mentioning the correction zero times. The addendum was in the ported file all along; the summary dropped it, which is how a withdrawn claim outlives its withdrawal.

## The open question this folder exists for

**The audit compared the metrics against each other and never had an external criterion.** `../interiority_in_passages/` has one: 13,565 passages coded HOLDS / SHIFTS / UNMOORED by blind Opus readers, 3,610 of them double-coded.

    HOLDS 12,099 | SHIFTS 2,835 | UNMOORED 2,241

So: **does `mean_drift` track what a reader calls staying in the scene, and does `total_drift` fail to?** If it does, that is independent confirmation of the audit's ruling by an instrument the audit did not have. If neither tracks, the geometric family is not measuring scene-holding at all — also worth knowing.

**The design is forced by the audit's own findings, and the obvious version of it is the wrong one.** A per-passage correlation is exactly the analysis ICC 0.082 predicts will classify near-randomly, so a null there would be unidentifiable — metric doesn't measure it, or metric too noisy at this unit. Instead:

- **group means, not per-passage correlation.** One passage's drift is mostly noise; the MEAN over 12,099 HOLDS passages is not. Ask whether mean `mean_drift` differs across the three coded classes.
- **hold `n_sents`**, because defect 3 is that directedness is sentence count and UNMOORED passages are plausibly just longer.
- **test within arm**, because interiority finds aligned passages HOLD more and the audit notes drift falls under alignment — pooling lets the arm manufacture the association.
- **use coder agreement as a purity filter** on the 3,610 double-coded passages.

## RUN 2026-08-20: the metrics track the coded judgment

`drift_metrics.py` → `results/drift_by_passage.csv`, `drift_vs_coding.py` → `results/drift_vs_coding.json`. HOLDS vs SHIFTS, within narrative, 5,808 passages over 27 lineage pairs:

    metric          diff     boot 95% CI      per-pair   sign p
    mean_drift   +0.0208  [+0.014,+0.028]      24/27    4.9e-05
    total_drift  +0.0315  [+0.025,+0.040]      27/27     1.5e-08
    ordering     -0.0101  [-0.013,-0.007]      25/27     5.7e-06
    directedness -0.0187  [-0.027,-0.012]      24/27     4.9e-05
    n_sents      +0.9851  [+0.50,+1.49]        22/27     0.0015

**The length confound is present and is not the explanation.** Narrative SHIFTS passages carry ~1 more sentence, so part of `total_drift` is mechanical — but non-narrative shows NO length difference (CI spans zero, p=0.061) and the effect is as strong there: `total_drift` +0.0296 at **29/29 pairs**. Holds in both arms.

**What this establishes is VALIDITY, which is not what the audit or its addendum measured.** The audit measured metric properties; the addendum measured reliability. Neither had an external criterion. This one does: a blind reader at kappa 0.904, and the geometry agrees with them across every lineage pair.

**So the four defects stand and the construct is vindicated, and those are compatible.** Order-invariance is still true — reproduced here 500/500. `directedness` is still sentence count. What was wrong was the register: a per-instrument reliability figure written as a property of the metric family, in a document whose framing ("the entire apparent ordering is void") reads as over-braking after finding an error. The idea was sound; the v1 instrument was weak. Swap MiniLM for bge-m3 and the same construct measures well.

**The one ruling now unsupported is the preference for `mean_drift` over `total_drift`.** Against the only external criterion available, `total_drift` separates the classes most consistently — 27/27 and 29/29 pairs — despite being the metric the audit criticised hardest. Its per-passage noisiness and its order-invariance are both still real; they simply do not stop a group mean from separating.

`PROVENANCE.md` carries the metric definitions verbatim so a new number stays comparable to the audit's.

## Where the code comes from, and where it does not

`archive/` is REFERENCE, not a dependency. **`corpus_metrics.py` is v1-era** (last substantive commit 2026-05-07, three months before the audit that reads its output) and **`embedding.py` is superseded by `malignment/vectors.py`**, which is ClickHouse-first, batches its misses, and degrades to slow-but-correct rather than failing the analysis. New work takes the 25 lines of metric DEFINITION from the archive and the embedding from the current repo.

Sentence vectors go to `$MALIGNMENT_DATA` as parquet rather than ClickHouse: nobody queries an individual sentence vector, the reusable artifact is the per-passage metrics, and the bare-word table's own docstring forbids mixing spaces.

## Two pieces of producer debt, pointing opposite ways

**The audit has no producer** — no Producers section, its four measurements computed inline, which by this campaign's rule makes them unauditable. They ARE recomputable from `results/corpus_metrics.parquet`, which is why it was ported.

**And its producer has no finding.** `archive/m06_ordering_figs.py` is named in no M06 document — one of 19 such scripts out of 47 — yet carries the audit's numbers verbatim and reports something no finding states: **the arm contrast on `ordering` is null, 11 up / 14 down in English, p 0.69.** The measure the audit recommends shows no alignment effect, and that is currently legible only to whoever opens a plotting script.
