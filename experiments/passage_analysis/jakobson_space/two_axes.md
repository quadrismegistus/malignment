# Both axes at once: alignment moves a model down a human range it already sat inside

**Every number here comes from `results/two_axes.csv`**, 8,145 passages carrying
deepseek surprisal and bge drift on the same row. Reproduce with
`python two_axes.py --csv results/two_axes.csv`.

## THE TABLE

Surprisal at M=200 tokens; drift uncontrolled, for the reasons in `two_axes.py`.
Model rows are medians of per-model medians over 26 base and 27 aligned
checkpoints; human rows are over passages.

    group                       bits/token   mean_drift        n
    MODEL base                      4.4958       0.4617       26 models
    human literary_criticism        4.4543       0.4963      499 passages
    human c20_fiction               4.3558       0.4833      500 passages
    human arxiv_abstracts           4.1581       0.4496      500 passages
    human philosophy                4.0397       0.4521      500 passages
    human dreams                    3.8457       0.4369      476 passages
    MODEL aligned                   3.7298       0.4394       27 models
    human waking_narrative          3.2884       0.4211      500 passages

## 1. THE ARM EFFECT IS ON BOTH AXES, AND IT IS NEARLY UNANIMOUS

Lineage-paired, the model as the unit:

    surprisal   aligned lower in 24 of 24 lineages   sign p = 1.19e-07
    drift       aligned lower in 23 of 24 lineages   sign p = 2.98e-06

Alignment lowers both. It is not that a smoother model wanders more, or that a
more predictable one holds its topic; the same 24 lineages move down on both.

## 2. THE MODELS BRACKET THE HUMAN RANGE ON SURPRISAL

Base is the least predictable text in the set and aligned the second most, and
**the two arms of one technology span almost the whole human spread**: 4.4958 to
3.7298 against a human range of 4.4543 to 3.2884. Alignment moves a model 0.77
bits/token, which is 65% of the distance from literary criticism to a diary.

The one thing that cannot be claimed is base against the two literary corpora --
+0.0414 against literary criticism and +0.1400 against c20 fiction, both of which
flip below M=175 and M=150 respectively (`ref_anchor.py --sweep`). Base against
everything else, and aligned against everything, is stable at every prefix from
60 to 200 tokens.

## 3. THE AXES AGREE AT THE GROUP LEVEL AND NOT WITHIN IT

    r(surprisal, drift), 8 groups        +0.869
    r(surprisal, drift), 8,145 passages  +0.414

So the two measurements are close to interchangeable for ranking a CORPUS and
are not interchangeable for a PASSAGE. A group's typical surprisal predicts its
typical drift; an individual passage's does not, and half the passage-level
variance is elsewhere.

## 4. WHERE THEY DISAGREE, WHICH IS THE POINT OF PUTTING THEM ON ONE ROW

Rank on each axis, 1 = highest:

    group                       surprisal   drift
    MODEL base                          1       3    <- drifts LESS than it surprises
    human literary_criticism            2       1
    human c20_fiction                   3       2
    human arxiv_abstracts               4       5
    human philosophy                    5       4
    human dreams                        6       7
    MODEL aligned                       7       6
    human waking_narrative              8       8

**Base is the biggest divergence in the table.** It is first in local
unpredictability and third in semantic movement: its text is hard to predict
token by token while going less far than either literary corpus. Literary
criticism and fiction invert that -- more predictable word to word, further
travelled across the passage.

That is the two axes doing different work, and it is what a single "quality" or
"entropy" number would hide. Base-model prose is locally surprising and
globally static.

## 5. FENCES

**Base is 26 models and aligned 27**, so an arm row is a median over models, not
a corpus. The human rows are 500 passages each and are not directly comparable in
precision.

**The human anchor is word-controlled at 193 words and the model passages are
uncontrolled**, which is why the surprisal axis is taken at a fixed token prefix
and why 517 passages drop for being under it.

**`mean_drift` is uncontrolled by design**, being length-free (r with n_sents
-0.126, against +0.941 for `path_length`). The accumulating drift metrics are
NOT on this table and should not be added to it without a sentence-count control.

**Drift and surprisal come from different producers and different join keys** --
human by `anchor_id` into `bge_human/drift.jsonl`, model by `text_sha` into
`passages_std.parquet`. Both joins are reported by `two_axes.py`: 2,975 of 3,000
human, 5,687 of 5,687 model.

**The model passages are narrative-coded, and the filter is real**: all 5,687 are
`narrative_A == True` from `interiority_in_passages/results/passC/codings/`, 28
shards, verified cell by cell. That filter removes 54% of the coded corpus
(6,174 True against 7,383 False), so this is a claim about NARRATIVE
continuations and not about model output in general.

**Note for whoever maintains passC**: `interiority_in_passages/ANNOTATIONS.md`
states it lists "every LLM annotation run behind this experiment" and has no
entry for passC, whose `narrative` field this population depends on.

**Everything excluded from the drift axis is excluded from this table.** 3.0% of
the standard population has no drift because it is a single sentence, and that
exclusion is arm-differential and different in kind: base contributes 4,892
long degenerate passages at 3.53 bits/byte on the BLT axis, aligned 5,853
fragments with a median of 55 bytes. Including them would push base FURTHER from
the human corpora, so this table is conservative rather than compromised.
