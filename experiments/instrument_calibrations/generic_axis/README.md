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

## A POOLED r LICENSES A POOLED USE. It does not license a per-item substitution.

**This is the sharpest limit on the headline number and it is not visible in it** (found by malign, [6381], re-derived here). On the `kill -> scream` item -- naughty `kill, die, cut, murder, hurt, stab`, nice `scream, cry, yell, shout` -- the pooled lexical axis does not merely underperform the declared axis, it MISORDERS the poles:

    frame: 'She was so angry she wanted to'      pooled 12-pair lexical axis

        murder   +0.1078   naughty
        stab     +0.0951   naughty
        hurt     +0.0928   naughty
        kill     +0.0824   naughty
        yell     +0.0804   NICE      <- above
        shout    +0.0725   NICE      <- above
        scream   +0.0474   NICE      <- above
        die      +0.0463   naughty
        cut      +0.0107   naughty
        cry      +0.0059   nice

    naughty-mean - nice-mean  +0.0210        pairwise correct 18/24 (75%)

Screaming scores naughtier than dying. **This is not a defect in the axis; it is the axis working as specified.** It is a general naughty/nice direction, and `scream, cry, yell, shout` are not nice in any general sense -- they are nice ONLY relative to killing. The item's poles are locally relative and a global direction cannot see that.

The r = 0.740 above is pooled over 86 heterogeneous items, and **a pooled validation licenses a pooled use**. Any single item can sit anywhere in that distribution, and this one sits below the point where the axis can carry the contrast at all: malign's declared axis separates the same poles at +0.3904 with 32/32 pairwise, about 13x stronger.

**So an axis needs a SEPARATION GATE before its answer is read, not after.** Malign's producer now prints the gate first and only admits axes that clear it, on the reasoning that reading the answer first is how a gate becomes a rationalisation -- it would have excluded this axis whichever way its count fell. Anything in this repo substituting the lexical axis for tagging on a SPECIFIC item should do the same, and this folder does not supply that gate.

## The tagged battery cannot yet be measured on its own frames

The axis is `embed(prompt + sep + word)`, so the framing is part of the axis. Checked against the local store: of the 86 `round3_slots.yaml` prompts, **2 have any twp record and 84 do not**. Malign hit the same wall from the other side -- the declared `kill -> scream` item's prompt is *"She was so FURIOUS she wanted to"*, which has zero cells anywhere in the roster, so their re-derivation used *"so ANGRY"*: a declared pole set on an undeclared framing, which is a reproduction of the claim rather than a measurement of the declared item.

**This folder is unaffected**, because it compares axes to each other and never runs a model. It bounds what comes next: nothing can measure the tagged items on their own prompts until those prompts are declared and run.

## What this does and does not license

**It does not license replacing author tags.** Purity, defectors and `MISTAGGED` are properties of a declared pole set and have no generic equivalent; an author who tags is also declaring what they think the item is about, which is a claim this cannot make for them.

**It does license the axis on untagged prompts.** Corpus prompts have no poles and never will, and a pooled lexical axis on them is now a measured instrument rather than a guess. `../rank_vs_cardinal` uses it for exactly that.

**And it does not touch `dN`.** Both origins are the midpoint of their own poles, so `s(origin) = 0` by construction and the origin term drops out of `sum dP(w)s(w)` exactly. The origin costs `N` as a level and the sign colouring in a panel. It costs movement nothing. This is asserted, not argued: check 1 of `python -m malignment.slot_axis`.

## Notes on reproduction

- `SLOTS` is an absolute path to a named file, never a glob.
- Framed vectors go through `slot_axis.embed_cached` and land in the shared `|slot-word` store, so this run warms it for the app. **Bare vectors are deliberately not stored** -- a bare word's key would be the word alone, and the namespace is documented as words *in a prompt frame*. Merging the two is unrecoverable.
- Split-half uses 20 resamples per item at seed 20260817, recorded in `summary.json`.
- Items with fewer than 4 words on a side report `nan` rather than being dropped, and the count of measurable items is printed and stored.
