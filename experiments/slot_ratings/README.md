---
subject: slot_ratings
status: "OPEN. The panel is NO LONGER the constraint -- all three questions ran at 20-33 lineages because their producers took the panel from a pilot cell list, not from the data; repointed at roster.endpoints() and movement_v4 on 2026-09-05/06 and all three now run at 50."
kind: subject
headline: "Pretraining lays down the field. Alignment operates on it rather than creating it."
grain: word
why: |
  THE PANEL WAS NEVER THIN IN THE DATA (2026-09-06). Every question here read its
  lineage list from displacement_axis/results/pilot3/cells.jsonl -- 21 endpoint
  pairs -- while the store held all 50 for the same prompts. identity ran at 20,
  sexual at 33, the slot POV study at 12. All three are now at 50. What follows
  was written when that was believed to be a data limit and is kept for the rest
  of its argument.

  The instruments are built and validated; what is thin is the panel they are read
  against. Per-lineage rho and its sign tests across frames are stable at the
  current n, but anything phrased as prediction or variance explained is bounded by
  lineage count rather than by the scales (see experiments/displacement/displacement_axis/README.md,
  "Can the movement be NAMED?"). Treat magnitude claims from this layer as provisional
  until the panel grows; treat direction claims as standing.
blocked_on: more base->aligned lineages in twp_words_v4 / movement
edges: |
  ALL THREE QUESTIONS NOW RUN ON THREE EDGES (2026-09-06), via
  movement.endpoint_edges / endpoint_edge_where:

      raw      base_raw    -> aligned_raw       50   alignment
      framed   base_raw    -> aligned_framed    45   alignment AND the frame
      self     aligned_raw -> aligned_framed    45   the frame ALONE

  Every producer takes --edge and every output filename carries it. The
  populations are 45 and 45 but not the same 45: framed is keyed on the BASE of
  an endpoint pair, self on the ALIGNED model, and both are the clean-slot subset
  (clean_frame_pairs, see its docstring for the rule and the two wrong versions).

  THE THREE QUESTIONS ANSWER THE FRAME DIFFERENTLY AND THAT IS THE RESULT:

      identity     group structure SURVIVES. 64 of 66 raw-significant room cells
                   keep their sign on framed, 54 stay significant.
                   Muslims/deference +0.132 raw, +0.142 framed, +0.133 self.
      POV          the asymmetry DOES NOT. 6 of 8 raw-significant scales go
                   non-significant on framed; only vocalisation/self survives
                   Bonferroni over the 33 tests.
      sexual       the gender null HOLDS on all three, and so does the selection
                   direction.

  A structural reason to expect identity vs POV, recorded as NOT predicted before
  the run: a per-lineage group contrast holds the frame constant across the groups
  being compared, so a frame that moves every group together cannot produce or
  destroy it. The POV study instead asks whether a gap between two prompt
  positions survives, and the frame moves those two positions.

  WHAT THE FRAME DOES TO THE DATA: it concentrates the distribution and that
  lands on the FLAT words -- risers hold near a sixth on every edge while fallers
  go 34% -> 50%.

  THE FRAMED CELLS WERE NEVER TOPPED UP (frame='prefill' is pass-1 only) and the
  raw ones are, so a raw-vs-framed WORD COUNT is not like for like. Pass-1 on
  both sides the median is 108 -> 87, not the 129 -> 81 first written here.

  It does not reach the verdicts, and the check that shows so is not a word
  count: CLASSIFICATION IS INVARIANT TO TOPUP. The faller test is the ratio
  Q < 0.5*P, satisfied by a sub-theta Q whether stored small or absent (0 of
  7,550 raw fallers would flip), and a topped-up P is sub-theta by construction
  so it cannot make a riser eligible. Topup REMOVES false risers -- 2,604 words
  clear delta only if their base probability is taken as 0.

  A GATE ON THE ALIGNED SIDE IS NOT COMPARABLE ACROSS EDGES. run_slotpov arm A
  gates on the base side (raw on all three) and is; arm B gates on the aligned
  side, so it gates on the concentrated distribution itself and its populations
  are not the same object.
todo:
  - name: no identity-specific or violence-specific instrument
    what: |
      Two per-domain instruments exist -- sexual/task.py (sexual_slot_en_v2, 9
      scales) and institutional/task.py (slot_institutional_en_v3, 13). There is
      no identity/ and no violence/. Those two domains are read with v6, the
      general instrument.
    why_it_matters: |
      It is a confound sitting exactly on top of a finding. In the mass results
      the named scales match or beat the declared pole axis in institutional and
      violence and lose to a matched embedding in identity, and the reading on
      offer is that alignment's institutional operation runs along dimensions
      somebody wrote down while its identity operation is unlegislated corpus
      residue. "Our identity scales are bad" predicts the same pattern, and the
      instrument coverage runs in the direction of the finding: institutional and
      sexual get bespoke instruments, identity gets a general one.
      NOT SYMMETRIC BETWEEN THE TWO MISSING ONES. v6's harm / aggression /
      directedness descend from SCALES_V3 and SCALES_V4, which were developed on
      violence frames (the "She was so furious she wanted to" grid), so violence
      has partial ancestry in the general instrument. Identity has none. Identity
      is the only domain with no instrument tuned to it at any point, and it is
      the domain where the named scales lose.
    what_would_settle_it: |
      Build an identity instrument the way institutional/task.py was built, rerun
      loo_all.py and mass_direction.py on the same frames. If named still loses to
      bge in identity with a purpose-built set, the asymmetry is about alignment.
      If it closes, it was about our scales. Violence second, and cheaper, since
      it is already half-covered.
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
