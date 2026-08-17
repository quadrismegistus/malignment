# Generic axis: is a bare minimum naughty/nice vector sufficient?

The slot axis is built from the author's tags. Tagging is the expensive step in authoring an item, and it is the step that makes `s(w)` a property of `(item, word)` rather than of a word. This measures what a generic lexical antonym pair would buy or lose, over all 86 items of `round3_slots.yaml`.

Run: `python run.py`. Writes `results/{per_item,per_item_pair,per_pair,summary}.csv|json`.

## The answer

**A pooled lexical axis recovers about 89% of the reliability tagging buys. A single antonym pair is a lottery.**

The `best single` column is the best by RAW COSINE, which is *not* the column the table ranks on: `violent-gentle` is 5th of 12 on score correlation, where the best is `immoral-moral` at r = 0.691 (0.83 of ceiling). Both are shown deliberately, because which pair looks best depends on which measure you read, and that is the point of the section below.

|                                       | pooled 12 pairs | best by cosine (`violent-gentle`) | bare `naughty-nice` | worst (`explicit-innocent`) |
| ------------------------------------- | --------------- | ------------------------------ | ------------------- | --------------------------- |
| (a) cos to bare declared centroid diff | 0.155           | 0.148                          | 0.115               | -0.007                      |
| (b) cos to framed declared axis        | 0.296           | 0.282                          | 0.226               | 0.048                       |
| correlation of the resulting scores    | 0.740           | 0.656                          | 0.669               | 0.209                       |
| as a fraction of the instrument's own ceiling | **0.89** | 0.79                           | 0.81                | 0.25                        |

## The two halves of that table disagree, and the disagreement is the finding

The raw cosines say a lexical pair is nearly orthogonal to the declared axis. The score correlations say it recovers most of what tagging buys. **Both are correct.** A 1024-dim cosine counts every direction equally, including the ~1010 along which no candidate in the item varies; only the axis's component inside the span of the item's own words can affect any score. Reading the raw cosine alone would condemn an axis that ranks correctly.

So the cosine asked for is reported, and it is not the readable scale. `pearson` is the same quantity restricted to the subspace that can affect a score, and it is what the table above ranks on.

## The ceiling, without which no cosine here means anything

A cosine of 0.6 against the declared axis is unreadable until you know what the declared axis scores against **itself**. Split each item's tags in half, build an axis from each half, score every word with both:

    cos       0.608    the raw direction cosine between the two half-axes
    pearson   0.828    correlation of the two scorings
    spearman  0.685    correlation of the two orderings

measured on the 54 of 86 items with at least 4 words a side. **The declared axis agrees with itself at r = 0.828, not 0.95.** A third of the variance in `s` is resampling noise over which words the author happened to list. Every number in this folder is read against that.

The worst item is `nn_handunderher_chin-blouse` at 0.423, five words a side.

## Three things that qualify the result

- **Pooling beats picking.** The 12-pair pooled axis beats every single pair on every measure. Single pairs run from 0.74 of ceiling down to 0.25, and you cannot tell in advance which is which: `explicit-innocent` is the worst here and reads as the most on-topic for a battery that is half sexual.
- **Framing is doing real work and is separable from tagging.** `cos(bare, framed)` on the *declared* axis is 0.706, so about a third of the declared axis comes from the prompt rather than the words. A lexical pair embedded in the frame roughly doubles its cosine over the bare version. Whatever else changes, the poles have to be embedded in the item's prompt.
- **The origin fails, not the direction.** Sign accuracy on declared pole words is 0.816 under the generic origin and 0.890 when the generic *direction* is given the declared origin. Since scores shift by a constant under a change of origin, `spearman` is untouched by this and only the sign split suffers.

## What this does and does not license

**It does not license replacing author tags.** Purity, defectors and `MISTAGGED` are properties of a declared pole set and have no generic equivalent; an author who tags is also declaring what they think the item is about, which is a claim this cannot make for them.

**It does license the axis on untagged prompts.** Corpus prompts have no poles and never will, and a pooled lexical axis on them is now a measured instrument rather than a guess. `../rank_vs_cardinal` uses it for exactly that.

**And it does not touch `dN`.** Both origins are the midpoint of their own poles, so `s(origin) = 0` by construction and the origin term drops out of `sum dP(w)s(w)` exactly. The origin costs `N` as a level and the sign colouring in a panel. It costs movement nothing. This is asserted, not argued: check 1 of `python -m malignment.slot_axis`.

## Notes on reproduction

- `SLOTS` is an absolute path to a named file, never a glob.
- Framed vectors go through `slot_axis.embed_cached` and land in the shared `|slot-word` store, so this run warms it for the app. **Bare vectors are deliberately not stored** -- a bare word's key would be the word alone, and the namespace is documented as words *in a prompt frame*. Merging the two is unrecoverable.
- Split-half uses 20 resamples per item at seed 20260817, recorded in `summary.json`.
- Items with fewer than 4 words on a side report `nan` rather than being dropped, and the count of measurable items is printed and stored.
