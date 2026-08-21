`slot_ratings/sexual`. Produced by `plot.py gender_slopes` from
`results/gender_pairs.json`.

Eight gender-swapped matched pairs -- the same scene with the gender swapped --
over 33 lineages and 11 matched sets carrying both genders. Gender is WHOSE BODY
THE SLOT CONTENT ATTACHES TO, not the grammatical subject: `She unzipped his ___`
is a male slot.

## What it shows

Alignment moves the two genders the same way. The lines run near-parallel on
every scale, so the gap alignment found is the gap it leaves: the base is
asymmetric and the change in that asymmetry is not. `hedged` is the only panel
whose change clears p<0.05 (+0.010, p=0.032), and it is one result among twelve
scales tested, so it is a lead rather than a finding.

## Why the p and not a star

`gender_pairs.json` books `delta_p` and no interval. A binary mark on a bootstrap
p is a coin flip wherever the value sits near the cut, so the p is printed and
the reader judges. The institutional slopegraph can distinguish a boundary case
because its artifact carries intervals; this one cannot, and says so rather than
implying a cleanliness it has not measured.

## The estimator, because the levels are recomputed

The artifact books per-gender DELTAS and not the levels behind them, so the
levels are recomputed and asserted against those deltas -- they reproduce to
5.6e-16. Three things had to match: the pairs are the matched sets carrying both
genders, the unit is the (lineage, pair) cell averaged before the mean over
cells, and a row counts only if BOTH arms are present for that scale. The last
looks pedantic and is not: coverage differs by arm, and including one-armed rows
stops mean-of-differences equalling difference-of-means. With only the first two
the reconstruction is out by up to 5.8e-3 -- small enough to look like rounding.

## Fences

- v6 scales only. The institutional scales that carried the sharpest results
  elsewhere (`mediation`, `procedural`, `deference`) are not measured on these
  frames.
- Eight pairs and 33 lineages is modest power; a null here bounds an effect
  rather than excluding it.
- The gender contrast averages over five role types (object, agent, target,
  experiencer, patient). At this n there is no room to test role by gender.
