---
subject: slot_ratings
status: awaiting more lineages
why: |
  The instruments are built and validated; what is thin is the panel they are read
  against. Per-lineage rho and its sign tests across frames are stable at the
  current n, but anything phrased as prediction or variance explained is bounded by
  lineage count rather than by the scales (see experiments/displacement_axis/README.md,
  "Can the movement be NAMED?"). Treat magnitude claims from this layer as provisional
  until the panel grows; treat direction claims as standing.
blocked_on: more base->aligned lineages in twp_words_v4 / movement
---

# slot_ratings

A contextual rating layer for the slot corpus: every (prompt, word) pair scored
on named scales by an LLM judge, so that probability mass can be projected onto
an interpretable axis instead of an embedding direction.

## Why this exists

`displacement_axis` measures where a model's mass sits on a per-frame axis built
from author-declared pole words, `u = centroid(naughty) - centroid(nice)`. That
is a real direction and alignment moves along it, but its ORIGIN is the midpoint
between two centroids chosen by whoever wrote the frame. Its own README says so:

> 70% is a fact about WHERE THE MIDPOINT FALLS, and the midpoint is defined by
> the pole word choices. Suggestive of the F21 reading, not independent evidence.

A rating has a fixed anchor. `harm = 1` means the same thing whatever pole words
were picked, so a mass-weighted mean of ratings is a LEVEL and not just a
displacement. That is the whole point of this folder, and it is what lets the
base model be measured rather than inferred.

    E[scale | rated] = sum_w p(w) * rating(w) / sum_w p(w)

computed separately on each arm, with no eligibility gate. Because there is no
gate there is no arm A / arm B split here, and the vocabulary differences that
plague gated statistics stop being a free parameter: a word contributes in
proportion to the mass it actually holds.

## Two instruments

    v6              12 general scales    harm, aggression, directedness, makes_better,
                                         makes_worse, interiority, deliberation, superego,
                                         vocalisation, hedged, fit, mundanity
    institutional   13 conflict scales   agency, deference, assertiveness, procedural,
      v3                                 specificity, delay, abstraction, target, collective,
                                         arousal, vocalisation, termination, mediation

They share one field, `vocalisation`, which doubles as a free reliability check:
4,046 (prompt, word) pairs rated by both from independently written prompts agree
at **spearman 0.891, pearson 0.961, 82% exact, mean |diff| 0.25**. The ratings
are a property of the pair, not of the instrument wording.

## THE FINDING, ACROSS TWO DOMAINS

**Pretraining lays down the field. Alignment operates on it rather than creating
it.** The same shape appears in the two domains measured so far, on different
corpora with different instruments.

**identity/** -- the base already carries the group ordering, and alignment
sharpens it. `pray` in raw probability: Christians 0.180, Muslims 0.149, Jews
0.053, every other group at or below 0.016. Spearman between the base and
aligned orderings is **0.970**: the aligned model's ordering IS the base
model's. What alignment adds is amplification on identity-typed content
(between-group SD 0.044 -> 0.065, ratio 1.47, with Christians/Jews/Muslims x1.32
against x0.69 for the other 21 groups) and compression on harm (SD ratio 0.73,
surviving a split-half against regression to the mean). It equalises the groups
on how harmful their distribution is and sharpens them on who they are.

**institutional/** -- the base already stratifies the individual and institutional
positions, on 13 of 13 scales in M03 and F21 at p as low as 1.8e-15, with the
inherited fraction running 70 to 103 percent. And what alignment adds is not a
widening of that gap but a large SYMMETRIC movement: on 52 site-matched prompts,
`procedural` +0.216 / +0.148, `mediation` +0.236 / +0.125, `deference` +0.087 /
+0.081, `termination` **-0.156 / -0.112**, all p <= 0.023. Both parties are made
more procedural, more deferential and less able to end the relationship.
Alignment forecloses exit symmetrically. On top of that sit two small asymmetries
running on different axes: the individual is routed roughly twice as far into
channels (+0.102, p=0.025) and the institution is abstracted roughly twice as far
(-0.110, p<0.001), a particular deed (`fire`, `say`, `mention`) becoming a named
process (`consider`, `prepare`, `advise`).

**The methodological lesson is part of the finding.** Both results were invisible
to gap tests and difference-in-differences, because a difference is null exactly
when both sides move together. The apparatus has to measure the level, and then
the base arm, before any comparison is worth reading.

## Layout

    task.py, run.py, corpus.py     the v6 instrument, its population rule, the 303-frame run
    pos.py (in malignment/)        contextual POS at the slot; only NOUN/VERB/ADJ/ADV are rated
    domain_words.py               raw risers and fallers per domain, no scales
    institutional/                the v3 instrument, F21 / M03 / slot-POV, and the base side
    identity/                     24 groups x 3 frames, both instruments, and the base side
    sexual/                       (in progress)

Each subfolder's README carries its own findings, corrections and caveats. Where
a number here and a number there disagree, **the subfolder is the record**.
