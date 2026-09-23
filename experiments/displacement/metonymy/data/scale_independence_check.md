# Inter-scale correlation — the check that was agreed and is not in the README

From largeliterarymodels-claude, 2026-09-20. Computed from `results/scales.csv`
(479 rows, 181 veto-passing) and `data/scale_*.csv` (71 words shared across all
five ported scales). Spearman throughout.

**The headline is not affected.** It rests on D alone, and collinearity among
*other* scales cannot touch a correlation D has with the deltas. What is
affected is the robustness claim — "eight of the nine rulers give the same sign
in both frames" — which counts rulers as if they were independent.

---

## 1. The S2 rewrite worked. The pair that did not separate is a different one.

The pilot was supposed to report whether `position` and `dressing` had come
apart after S2 was rewritten as body region with the layering language
removed. They did:

| jev | rho |
|---|---|
| position vs dressing | **+0.584** |
| exposure vs dressing | +0.619 |
| exposure vs position | **+0.867** |

`position` vs `dressing` at 0.584 is comfortably under the ~0.9 I named as
"the rewrite did not work". That rewrite is a success and should be recorded
as one.

The 0.867 is `exposure` vs `position` — S1 against S2, the pair your draft-2
note predicted would separate on the belt-versus-dress logic ("a belt sits
adjacent and uncovers nothing; a dress sits mid-distance and uncovers
substantially"). On jev, over 181 words, that prediction does not hold. 75% of
shared variance.

On deepseek the three are flatter and uniformly collinear:

| deepseek | rho |
|---|---|
| exposure vs position | +0.782 |
| exposure vs dressing | +0.764 |
| position vs dressing | +0.744 |

So the two coders do not agree about the *structure* of the scale set even
where they agree about the words: jev separates dressing-order from the other
two and deepseek does not. Worth a line, because it means "the survey has
three scales" is true of one coder more than the other.

## 2. The pooled `survey` row is not a ninth ruler

It is the mean of the three, and it correlates with its own components at:

| | exposure | position | dressing |
|---|---|---|---|
| jev | +0.913 | +0.886 | +0.826 |
| deepseek | +0.900 | +0.879 | +0.937 |

Reporting `survey` in the grid beside `exposure`, `position` and `dressing`
lists one quantity four times. That is defensible as a summary row if it is
labelled as one, but it should not enter a count of rulers.

## 3. The ported scales are collinear too

On the 71 words all five share, using the raw stored columns:

| pair | rho |
|---|---|
| Cexp vs D | **+0.926** |
| Ccharge vs D | +0.809 |
| Ccharge vs Cexp | +0.787 |
| B vs D | +0.738 |
| B vs Ccharge | +0.744 |
| B vs Cexp | +0.704 |
| A vs B | **−0.838** |
| A vs Ccharge | −0.602 |
| A vs D | −0.524 |
| A vs Cexp | −0.394 |

`Cexp` and `D` at 0.926 are very nearly the same ranking.

## 4. What the count should say instead

Nine rows, but not nine rulers. B, Cexp, Ccharge and D inter-correlate at
0.70–0.93; exposure and position at 0.87; `survey` is a function of three of
the others. A generous reading is **three or four effectively independent
rankings**, not nine, and the agreement across them is correspondingly less
surprising than nine-of-nine sounds.

This does not weaken the finding. It changes what the grid is evidence *of*:
not nine independent instruments concurring, but one ordering that several
overlapping operationalisations recover — which is still the thing the section
is trying to show, and is a claim the numbers above support directly. State
the dimensionality and the sentence gets stronger, because a reader who
computes these correlations themselves will otherwise discount the whole grid.

## 5. One thing I cannot resolve from outside, and you should check

`A` correlates with `B` at **−0.838** on the shared 71 words. Whatever the
sign convention, that is a strong relationship: A and B are largely the same
ranking, inverted.

But A is the null in the word-level test (−0.141 her, +0.056 his) while B is
strong (+0.620, +0.432). If A ≈ −B as rankings, then after the producer's
uniform negation A's correlation with the deltas should be roughly ±0.6, not
≈0. Near-zero is not what either orientation predicts.

Three possibilities and I cannot tell them apart without reading `run.py`'s
conversion:

1. the producer handles A's orientation separately and correctly, and the
   near-zero is real — in which case A's relationship to B is not the
   monotone one this number suggests, and it is worth saying why;
2. A is stored in the opposite orientation and is being negated with the
   others, which would corrupt A's `out` — but that predicts a strong
   negative, not a null;
3. the word sets differ enough that the A–B correlation and the B–delta
   correlation genuinely do not compose (A n=73, B n=71 in the word-level
   test, 71 shared across all five here).

(3) is the likeliest and the cheapest to check. It matters because A carries
the priming argument: "the coder produces this ordering when shown the scene
and does not produce it from the word list alone" is harder to sustain if A
and B are the same ranking up to sign. Recompute the A-versus-delta
correlation on exactly B's word set and see whether the null survives.
