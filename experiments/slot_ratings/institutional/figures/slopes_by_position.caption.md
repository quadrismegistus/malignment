`slot_ratings/institutional`, section 13. Produced by `plot.py slopes_by_position`
from `results/base_side/ishould.json`.

## Why the y axis is centred rather than shared or free

Levels run 1.00 (`harm`) to 5.86 (`fit`). A shared axis flattens every slope to
nothing. A free axis per panel is worse: it rescales each panel to its own range,
so `harm` moving 0.003 draws as steep as `directedness` moving 0.267, and the
reader compares slopes that are not comparable.

Centring each panel on its own midpoint over one shared +-0.5 domain keeps
y-units-per-pixel constant across all 24, so a steeper line really is a bigger
movement. The window was chosen from the data rather than picked: 23 of 24 scales
span under 0.60 and `mediation` needs 0.945, so +-0.5 clips nothing. An assert
refuses any scale that would exceed it, so a re-run on different numbers fails
rather than silently cropping a line.

The grey number at each panel's top left is the absolute range across all four
points. `harm` reads 1.00-1.00: it is pinned at the floor and has nowhere to go,
which is why its two lines sit on top of each other.

## Why `~` exists, and why it is not a p-value threshold

`mediation`'s interval excludes zero by 0.0003 and `procedural`'s includes it by
0.005. They are equally unstable and any threshold puts them on opposite sides.

This study's README books `mediation` at p=0.025; this producer's own bootstrap
draw gives 0.050. Both are honest draws of the same quantity -- the point
estimates are identical -- so the mark says BOUNDARY rather than picking one.

The cut is `near / width`, how close the nearer endpoint sits to zero relative to
how uncertain the estimate is, and 0.05 falls in a measured gap rather than being
chosen: `mediation` 0.0015, `procedural` 0.0317, then nothing until `vocalisation`
at 0.1523, with every decisive null above 0.30. An earlier version used an
absolute distance and marked `harm`, `aggression` and `collective` -- intervals a
hair wide around zero, so every endpoint is near it. Those are decisive nulls,
the opposite of a boundary.

**`abstraction` is the only difference here that is not fragile.**

## Fences

- Ratings cover 0.242 of base mass and 0.296 of aligned mass, so the two arms are
  averaged over different fractions of the distribution. The gap is uniform
  across scales and positions.
- `agency`, `specificity`, `assertiveness` and `arousal` are pairwise 0.62-0.83
  over 14,196 rated rows and are ONE axis drawn four times. Four panels moving
  together is one finding, not four.
- Panels are ordered by individual minus institution, so the fanning ones come
  first. After `abstraction` the reader scans 23 near-parallel panels, which is
  the finding rather than a gap in it.
