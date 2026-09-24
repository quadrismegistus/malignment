---
subject: metonymy
status: "RUN 2026-09-18, 50 endpoint lineages, English, both took-off frames. Ports the `X_metonymy` finding out of `malign-logits/meta/M01_displacement` and re-runs it at 50 lineages on a new instrument. The word-level test and the figure producer are new here and are EXPLORATORY: nothing in this folder was registered before it was run."
kind: question
question: Inside one scene, does the word alignment moves TO sit further from the body than the word it moves FROM?
headline: "It does, and the ordering replicates at 50 lineages on an instrument built after the original. Unit = the word, statistic = the median of its per-lineage delta over the lineages that carry it, minimum 10 carriers: on the published scale D the correlation between how far out a word sits and how much alignment raises it runs rho +0.726 (n=72, p=5.3e-13) in the her-frame and +0.535 (n=57, p=1.8e-05) in the his-frame, and it is flat across carrier thresholds from 1 to 40. A NEW survey instrument, administered blind over 479 candidate nouns rather than the original's 122-word list, reproduces it independently: +0.524 (n=96) and +0.387 (n=78). Eight of the nine grid rows give the same sign in both frames, but the rows are not nine independent rulers: they inter-correlate at 0.70 to 0.93 and `survey` is the mean of three others, so they are three or four overlapping rankings recovering one ordering. The one null row is scale A, the open dimension named WITHOUT the sentences, and it is null because its two coder runs named opposite axes and their mean cancels; run alone, the Opus run (\"layering depth\") recovers the ordering from the word list alone (rho +0.40 her). What the scene adds is agreement on the axis, not the ordering. The PAIRED cell test -- top faller against top riser at the same cell, 100 cells -- is the weaker of the two and carries the her-frame only (35/50, p=0.0066 on D; 29/49, p=0.25 on his). On the BODY-PART scenes, with `slot_ratings/sexual`'s contextual `body_distance` as the ruler (`body.py`), the same word-level test is positive on 16 of 16 prompts (median rho +0.36) and 11 of 11 gender-paired scenes; there is no non-sexual control. **The figure X.1 needs no new garments**: all 27 + 22 words it draws still move at 50 lineages, every value keeps its sign but two near-zero ones, and `figure.py` recolors it from the producer's own output."
---

# metonymy

**`existence` asks whether alignment moves mass and where it goes across a global taxonomy. This asks a question a global taxonomy cannot answer: inside ONE scene, is the word alignment moves toward further from the center of that scene than the word it moves away from?**

USAS cannot answer it. It scored `penis / trousers / belt / crotch` as diverse because body parts and clothing sit under different letters, so referential distance inside a scene is invisible to it. The ruler has to come from the scene.

The scene is `She slowly took off her ___` and `He slowly took off his ___`. Every candidate in that slot is a wearable, they differ mainly in how close to the body they sit, and the ordering is legible without a theory of it: a blouse is not an intimate garment and a bra is.

## What is ported and what is new

Ported from `malign-logits/meta/M01_displacement` (RH's design, 2026-08-07, read-only archive):

- the scene and the two frames
- the paired cell test and the reason for it (section 4a of the original: correlating a word's score against how often it moved DISCARDS the pairing, and `shirt -> glasses` is a top faller and a top riser at the same cell)
- five coder scales, one file each under `data/`, with `data/SCALES.md` recording what each asked
- the figure geometry, `data/x1_garment_layers_source.svg`

New here:

- 50 endpoint lineages instead of 46
- the word-level test, with the word as the unit and the median of its per-lineage delta as the statistic
- a new survey instrument, `survey.py`, covering 479 candidates instead of the original's 122
- `figure.py`, which recolors the published drawing from the producer's own output and emits a greyscale version

## The unit is not the lineage, and the reason is arithmetic

A word is not present in every lineage. `apologize` moving in 1 of 50 and `have` moving in 50 of 50 both produce one "rate" if you divide by the lineages that carry the word, and the rare word wins -- which is how an earlier pass in `substitution_shape` produced a 35.5% artifact. A word below the store's floor in a cell is ABSENT from that cell, not zero there.

So there are two tests, at two units, and neither is the lineage:

**Paired, unit = the cell.** Per (base, aligned) pair, take the word that lost the most mass and the word that gained the most, and ask whether the riser sits further out. 100 cells, 99 of which carry a D score on both words.

**Word-level, unit = the word.** Statistic = the median of its per-lineage delta over the lineages that carry it. `--min-carriers` (default 10) sets the admission floor. This is the headline.

## The grid

Every scale is converted by the producer to one quantity, `out`, HIGH = further from the body, so the prediction reads the same on all of them: the riser sits further out, and the correlation is POSITIVE. The ported scales run 0 = off the body to 100 = against the skin and are negated; the survey's levels run 0 = against the skin to 4 = carried in the hand and are not.

| scale | what it asked | her paired | her word-level | his paired | his word-level |
|---|---|---|---|---|---|
| `A` | open dimension, sentences **withheld** | 30/50 p=0.2 | n=73 **rho -0.141 p=0.23** | 34/49 p=0.0094 | n=58 **rho +0.056 p=0.68** |
| `B` | distance from the body | 30/50 p=0.2 | n=71 rho +0.620 p=8.0e-09 | 24/49 p=1 | n=56 rho +0.432 p=0.00088 |
| `Cexp` | explicitness | 32/50 p=0.065 | n=72 rho +0.739 p=1.2e-13 | 29/49 p=0.25 | n=57 rho +0.621 p=2.6e-07 |
| `Ccharge` | charge | 33/50 p=0.033 | n=72 rho +0.592 p=4.3e-08 | 25/49 p=1 | n=57 rho +0.364 p=0.0054 |
| `D` | open dimension, sentences **shown** | 35/50 p=0.0066 | n=72 rho +0.726 p=5.3e-13 | 29/49 p=0.25 | n=57 rho +0.535 p=1.8e-05 |
| `exposure` | what removing it uncovers | 15/25 p=0.42 | n=96 rho +0.493 p=3.3e-07 | 14/30 p=0.86 | n=78 rho +0.380 p=0.00061 |
| `position` | where it sits on the body | 12/25 p=1 | n=96 rho +0.451 p=4.0e-06 | 9/30 p=0.043 | n=78 rho +0.384 p=0.00051 |
| `dressing` | when it goes on | 15/25 p=0.42 | n=96 rho +0.549 p=6.8e-09 | 12/30 p=0.36 | n=78 rho +0.340 p=0.0023 |
| `survey` | the three above, pooled | 15/25 p=0.42 | n=96 rho +0.524 p=4.3e-08 | 12/30 p=0.36 | n=78 rho +0.387 p=0.00047 |

**The A row is not a measurement of one axis** -- see the A section below: its two runs point opposite ways and `run.py` negates both as if they pointed like B.

**Nine rows, not nine rulers.** `data/scale_independence_check.md` (largeliterarymodels seat, 2026-09-20) measured the grid's collinearity: Cexp against D +0.926, and B, Cexp, Ccharge and D all at 0.70 to 0.93 with one another on the 71 words they share; exposure against position +0.867 on jev; `survey` correlates +0.83 to +0.94 with its own three components. So the grid is three or four overlapping operationalisations recovering one ordering, not nine instruments concurring, and the agreement should be quoted that way.

Reproduce any row with `python run.py --scale <name>`; the files are `results/words_<scale>.csv` and `results/pairs_<scale>.csv`, one pair per scale because a sweep that wrote to one filename would leave the last ruler's numbers under the default run's name.

### The word-level test does not depend on the threshold

Scale D, and the survey beside it:

| `--min-carriers` | her (D) | his (D) | her (survey) | his (survey) |
|---|---|---|---|---|
| 1 | n=74 +0.730 | n=67 +0.406 | n=160 +0.349 | n=132 +0.228 |
| 5 | n=73 +0.726 | n=61 +0.405 | n=121 +0.455 | n=95 +0.315 |
| 10 | n=72 +0.726 | n=57 +0.535 | n=96 +0.524 | n=78 +0.387 |
| 20 | n=66 +0.709 | n=53 +0.538 | n=75 +0.531 | n=59 +0.450 |
| 40 | n=50 +0.721 | n=37 +0.475 | n=49 +0.620 | n=35 +0.450 |

Every cell is significant at p<0.01. The default of 10 is not a threshold the effect needed.

### The paired test is the weaker one and only the her-frame carries it

On the scale the published figure used, the her-frame runs 35/50 (p=0.0066) and the his-frame 29/49 (p=0.25). On the survey scales the paired test loses most of its cells -- the two-coder veto admits 181 of 479 words, so only 55 of 100 cells carry a score on BOTH the faller and the riser -- and it is null or negative there. **The word-level and paired tests are not interchangeable and this folder's headline is the word-level one.**

## `A` against `D`: the scene settles the axis, not the ordering

The registration asked the coder for an open dimension twice: once with the sentences withheld (`A`) and once with both sentences shown (`D`). A is the only null in the grid. **This section used to read that null as the coder not producing the ordering from the word list alone. That reading is wrong**, and `scale_a_check.py` (-> `results/scale_a_check.md`) shows why.

A's two runs did not name one dimension. From `malign-logits/meta/M01_displacement/results/x_coders/A_{opus,sonnet}.json`:

| run | dimension it named | 100 means | raw rho with Δ, her | his |
|---|---|---|---|---|
| `A_opus` | "Layering depth: how far from the skin the item sits" | outermost, removed first | **+0.396** (p=0.00058) | +0.218 (p=0.10) |
| `A_sonnet` | "How much of the body the item covers, or how large/bulky it is" | full-length garment over other clothing | −0.354 (p=0.0023) | −0.395 (p=0.0022) |
| `mean`, as `run.py` uses it | -- | -- | +0.141 (p=0.23) | −0.056 (p=0.68) |

The runs agree at +0.064 on the 71 words the ported scales share. `A_opus` runs OPPOSITE to the other ported scales (100 = outermost, where B-D put 100 against the skin), which is why it correlates −0.846 with B, and it is the source of the −0.838 the independence check could not reconcile. `run.py` negates A with B-D, so `A_opus` enters the mean with the wrong sign and `A_sonnet`, a different axis, cancels what is left. **The null is two opposite signals averaged, not the absence of a signal.** The archive already recorded this: `x_coder_analysis.py` excluded A from the headline grid as "two models improvising, not an instrument". The port kept it as a row and lost the reason.

What the comparison does show: without the scene, one coder (Opus) found the ordering unprompted, as layering depth, and it predicts the deltas in the finding's direction in the her-frame (+0.40). The other chose size, a different axis. With both sentences shown, the two runs converge on one dimension, intimacy of exposure, and agree at +0.89. **So the scene is what makes coders agree on the axis; it is not what makes the ordering available.** That is a weaker claim than the old one and a better-founded one, and it removes the worry that the ordering is a product of showing the coder the sentences.

`A` is kept in the grid and in `run.py` unchanged, because it is the provenance of the original comparison, but it should not be quoted as a ruler or as a null.

## The new instrument

`survey.py` administers one gate and three degree scales over `candidates()`, which is a POS filter on the whole moving vocabulary and not a list of movers. The coder was never told which words moved, on either instrument. Wording, drafts and the two review passes are in `data/levels_draft.md` and `data/levels_review*.md`.

Two arms see one item. `state_text()` is the single renderer, so the jev cache key's state and the text arm's prompt are byte-identical and a cross-arm check is string equality.

**The gate is off the scales.** An earlier draft listed NOT_AN_OBJECT first on every scale, which makes it position 0 of an ORDERED array: a `Score` interpolates, so a word could come back four-tenths of the way from not being a thing to uncovering nothing, and position 0 means the opposite thing on different scales. One `Choice`, asked once, categorical.

**All three scales run low = intimate, high = peripheral,** so the substantive prediction is ONE direction on all three. An earlier draft documented the direction backwards, before any data.

**No level exemplar is a candidate word.** `blouse`, `briefs`, `camisole`, `cummerbund`, `waistcoat`, `cardigan` and `umbrella` all were, at various drafts; `umbrella` sat at p=0.00097 against a floor of 0.00100. The exemplar list is now GENERATED from the level arrays and checked against the candidate set rather than asserted: 16 exemplars, zero overlap.

### The veto gate, and why it doubled the agreement

jev accepts BPE fragments as garments and deepseek does not. 58 words jev placed in the worn set deepseek called NOT_A_WORD -- 40 of them jev called GARMENT outright (`blaz`, `kimon`, `knick`, `legg`, `trou`, `underp`, `shir`) -- and **zero** went the other way. A word enters the scale only if BOTH arms place it in the worn set:

| scale | all 479 rows | deepseek engaged, 322 | the 181 that pass the veto | the 141 it fails |
|---|---|---|---|---|
| exposure | +0.339 | **+0.427** | **+0.809** | +0.100 |
| position | +0.405 | **+0.493** | **+0.911** | −0.014 |
| dressing | +0.347 | **+0.505** | **+0.753** | +0.225 |

**THE ALL-479 COLUMN IS NOT A BASELINE AND SHOULD NOT BE QUOTED AS ONE.** deepseek writes 0/0/0 on all three scores in 154 of its 157 NOT_A_WORD rows, 98%; jev never zeroes on any gate outcome. So a third of that column is one arm's refusal convention correlated against the other arm's real values. The baseline is the rows where deepseek actually answered, and the veto's lift is 0.43 to 0.51 up to 0.75 to 0.91, not 0.34 up to 0.91.

The disagreement is a fragment problem, not a scale problem: on words both arms accept as things, the two coders agree at 0.75 to 0.91, and on the words the veto discards they agree at about zero.

### What the veto costs, and what cannot be measured here

Of the 298 words the veto discards, **147 (49%) go because the coders DISAGREED**, not because both said no. So half its cost is selection on inter-coder agreement rather than fragment removal.

On this list that cost is near zero, because what it discards carries no signal: the 58 fragment disagreements agree at +0.055 / +0.051 / +0.036, and the 89 taxonomic ones at +0.173 / +0.084 / +0.279.

**But the 89 are not clean words two coders read differently.** They are `bel`, `bur`, `col`, `bathing`, `cold`, `cowboy`, `body`, `cover`, `cloths`: jev reading a fragment or a modifier in-frame as a garment while deepseek routes it to OTHER_NOUN rather than NOT_A_WORD. The 58 and the 89 are one failure wearing two labels, 147 of 479, so the fragment story is larger than the headline number and not smaller.

Which means **the cost of the veto is not measured here, rather than measured and found cheap.** This list holds no stratum of clean, gradable words that two coders merely disagree about, so it cannot say what the veto would discard on a corpus made of those. The list that makes the veto obviously worth running is the same list that makes its cost unmeasurable.

**The pilot did not catch it, and that is a lesson about the pilot.** `PILOT` was built half fragments and half real words precisely to test this, with `bathro` against `bathrobe` named in the code as the check that mattered most. jev rejected all five fragments -- `bathro`, `apr`, `t`, `bl`, `g` -- and deepseek agreed on all ten items. Five for five, and the hazard appeared anyway at 479.

What separates the two sets is not the kind of truncation, since `bathro` -> bathrobe and `legg` -> leggings are the same shape. It is where the string came from. **The pilot fragments are strings I typed; the run fragments are actual BPE tokens the model emitted in that slot with real probability mass**, so they carry a learned embedding and in-frame usage statistics that a hand-truncation does not. The gate passed the synthetic test and failed the real one. A hand-built fragment is not the same stimulus as a vocabulary fragment, and a gate validated on the former is not validated.

**And the rate is a property of the item list, not of jev.** 58 of 479 is 12% of the items and 58 of 327 is 18% of what jev placed in the worn set, but the item list is drawn from a next-token vocabulary and is enriched for fragments by construction: jev itself called 98 of 479 NOT_A_WORD, 20%. A dictionary-derived list would give a different error rate. The DIRECTION generalises, zero reverse cases in 479; the magnitude does not.

## The figure

`figures/x1_garment_layers.svg` and `figures/x1_garment_layers_gray.svg`, produced by `figure.py` from `results/words_D.csv`.

The drawing is ported and its geometry carries the argument -- each garment is drawn at the layer it is worn at, so the scale is the PICTURE and not a number on an axis. `figure.py` rewrites three things and nothing else: every garment's fill, its swatch and printed value, and the strings that quote the roster size. The colormap was recovered from the published file rather than guessed (`shoes +2.58 -> #053061`, `coat +0.57 -> #3e8cc0`, `hat -0.04 -> #fbe6da` all reproduce to within a rounding step) and is `RdBu` at `t = 0.5 + 0.5*sign(d)*min(1,|d|/1.2)**0.62`.

**No new garments are needed.** All 49 drawn words still move at 50 lineages. Every value keeps its sign except two that sit within a rounding step of zero: his `coat` -0.11 -> +0.12 and his `boots` +0.05 -> -0.02. The two largest movers are unchanged in rank and close in size (her `shoes` +2.58 -> +2.65, his `glasses` +1.28 -> +1.41).

`python figure.py --audit` prints the case for that, restricted to words a coder placed on a scale, because the moving vocabulary at this slot also contains `____`, `black` and bare determiners. The words the drawing leaves out that would rank highest among the ones it draws:

| frame | word | median Δ | carriers | would rank |
|---|---|---|---|---|
| her | `blouse` | 0.241 | 49 | 11 of 27 |
| her | `gown` | 0.140 | 50 | 17 of 27 |
| her | `bikini` | 0.123 | 34 | 18 of 27 |
| his | `cap` | 0.235 | 50 | 9 of 22 |
| his | `helmet` | 0.235 | 50 | 9 of 22 |
| his | `trousers` | 0.170 | 47 | 13 of 22 |

None of them changes the shape. `blouse`, `cap`, `helmet` and `trousers` are the four a redrawing would be worth doing for, and all four fall, which is the direction the existing drawing already shows for their layer.

## Two orderings, and they are not the same question

`run.py` emits both. `median_delta_pp` is MAGNITUDE; `fall_rate` and `rise_rate` are CONSISTENCY, the share of the lineages carrying a word in which it moves that way. A word can top the magnitude table on a minority of lineages moving a lot: `clothes` has the second-largest median fall in the her-frame and falls in only 29 of 50, while `skirt` falls in 41 and ranks sixth.

**The two rankings come apart, and not symmetrically.** The most consistent her-frame FALLERS are small movers (`belt` 88% at -0.083, `panties` 85% at -0.190) and the biggest fallers are inconsistent. The most consistent RISERS are the biggest risers: `shoes` rises in 70% of its lineages at +2.650 and `glasses` in 68% at +1.092, and they lead both tables. So the return is large and agreed, while the withdrawal is either large or agreed but rarely both.

**`--nouns` is not a garment filter.** The contextual POS prefilter (`survey.candidates()`, run at the end of each frame) removes the 109 adjectives -- `black`, `white`, `leather`, `wet` -- which is why they appear in the unfiltered word table and in NO survey scale. It does not remove `night`, `head`, `hair`, `hand` or `sweat`, which tag NOUN in frame and top the consistency table; the survey's GATE is what removes those, and the veto-passed worn set (181 words) is the filter that gets to garments. All three are available: the raw table, `--nouns`, and the `scored_veto` column in `results/scales.csv`.

### Is the drawing a fair picture of the slot?

Two different answers, and they should be quoted separately.

**By mass, yes: the 27 drawn garments hold 47.4% of the slot's probability at base and 44.5% after alignment.** Nearly half of what the model does in that position is on the page.

**By movement, less so: they hold 35% of the total |median Δ| across the 496 words that move (his: 31% of 422).** The rest is spread thin over hundreds of small words.

**No big-moving garment noun is missing from the her-frame.** The top 12 movers are all drawn except two artifacts -- `____`, a blank-fill string at 3 carriers, and `fedora` at 2. The first genuinely missing word with real support is `blouse`, rank 15, |Δ| 0.241 over 49 carriers.

Two things the drawing cannot show and a reader should know about:

- **Modifiers fall too, and they are large.** `black` (-0.284), `white` (-0.242) and `long` (-0.154) all sit in the her-frame top 20, on 50 carriers each. They are not garments, so a garment picture has no slot for them, but they are not noise either.
- **The his-frame is missing three high-carrier garments**: `cap` (-0.235, 50), `helmet` (-0.235, 50) and `trousers` (-0.170, 47). With `hat` at -0.482 that makes headgear a consistent faller in the male frame, which the drawing shows through one word instead of four.

Nothing outside the drawing runs against the direction it shows. Of the undrawn words with 20 or more carriers, 9 rise in the her-frame and 8 in the his-frame, all of them by less than +0.12 pp, and the largest are `seatbelt`, `headphones`, `sneakers` and `headset` -- peripheral or carried things, which is the side the figure already puts the risers on.

## The other layouts: `--two-body`

    python figure.py --two-body mass        # figures/x1_garment_mass_gray.svg
    python figure.py --two-body movement    # figures/x1_garment_movement_gray.svg

X.1 shades a DIFFERENCE on one body. Both of these draw the her-frame body TWICE, base on the left and aligned on the right, and differ only in what the shading means.

### `movement`: the left body wears what alignment takes off

The left body is shaded by how far each garment FALLS, the right by how far it RISES, and a garment that does not move that way is left blank AND UNLABELLED on that side. **21 of the 27 garments fall and 6 rise**, so the right body comes out nearly bare: `coat` (+0.76), `gloves` (+0.32), `jacket` (+0.11), `boots` (+0.09), and the two that carry it, `shoes` (+2.65) and `glasses` (+1.09). Everything on the torso and everything under it is blank on that side.

`--min-move` drops a garment whose |median Δ| is below it, from the DRAWING as well as the labels, pieces and all, so the layer goes rather than being left blank. At `--min-move 0.1` the her frame loses `hat` (-0.082), `tie` (-0.035), `watch` (-0.019), `belt` (-0.083), `socks` (-0.051), `heels` (-0.077) and `boots` (+0.092), leaving 20 garments of which 15 fall and 5 rise. `boots` sits 0.008 under the cut, and the source drew a boot on one foot and a shoe on the other, so removing it would leave one foot bare. When `boots` is not drawn the producer mirrors the shoe across the body's axis and gives the twin to `shoes`, so the figure keeps a pair. Nothing about the measurement changes: both shapes carry one word's one number.

Two drawing fixes travel with the two-body layouts. **`STROKE` puts every line in the drawing on one weight**, 1.4, the garments' own. The source runs seven -- garments at 1.2 to 1.6, the head at 3.2, the arms at 4.5, the spine at 5.0, the legs at 5.5 -- and at those weights a limb reads as a filled dark layer rather than as a limb, so the eye sorts the picture by stroke weight before it reaches the fills, which are the only thing carrying a number. And `BORDER_OPACITY` lifts every line in the drawing off the page at 0.45 -- garments, head, arms, legs, the smile. The drawing is a coordinate system, not a subject: the only thing here carrying a number is the fill, and a solid black contour around a near-white garment competes with it. The label swatches and the legend keep full weight, because those are the key.

**`LAYER_SWAP` is a correction to the drawing, not to the data.** The source nests the torso outward as top, shirt, sweater, jacket, robe, coat, which puts a robe OUTSIDE a jacket. A robe is indoor and sits nearer the skin; a jacket is outerwear. The two-body layouts swap which word owns which shape, which fixes the ordering without touching a coordinate: the label pointing at the outer shape now reads `jacket` and the one pointing at the inner reads `robe`. `--no-layer-swap` keeps the published nesting. `build()` is a faithful recolour of X.1 and is left alone, so the figure of record keeps the layering it was published with.

One ramp serves both bodies, so a fall and a rise of the same size print the same grey. That costs the falls their contrast -- the biggest fall is 0.55 pp against a biggest rise of 2.65 -- and **the asymmetry is the thing the layout exists to show**: the withdrawal spreads over twenty garments while the return concentrates on two. A per-body ramp would hide exactly that.

### `--ci`: the format the journal will take

    python figure.py --two-body movement --min-move 0.1 --ci        # two files
    python figure.py --two-body movement --min-move 0.1 --ci --ci-both

**The format was measured off a printed issue, not taken on trust.** Weatherby and Justie, "Indexical AI", *Critical Inquiry* 48 (2022): 381-415, has seventeen figures. Trim is 6.58 x 9.58in, the body column 4.33 x 7.36in, and every full-measure figure in it is placed at 4.25 to 4.33in. **So 4.33in is the printed column and 4.8in is the submission ceiling, not the width anything appears at.** The tallest placed image is 6.14in, on a page of its own with its caption; a figure sharing a page with text gets 7.36in less whatever the caption takes, so **about 7.0in is the working maximum height**. Its own captions set at about 7.6pt and the small-caps FIGURE N at 5.7pt, which is where the 6pt floor comes from.

`--ci-width` overrides the column; the default stays 4.8, which is what the rest of the paper's figures are drawn to, and the table below gives both. No title, caption or legend goes inside the image; the journal sets those and the garment labels carry the key anyway. The crop is MEASURED from the content rather than guessed, and the achieved figures are printed on every run so a bad estimate shows up instead of clipping silently.

**One box serves the pair.** The two arms label different garments, so cropping each to its own content would give two files at two scales, and a reader setting them side by side would get two different-sized bodies. The arm that is not being drawn is measured as well and discarded.

If the type lands below 6pt the producer scales every font up once and rebuilds. Bigger type widens the box, which shrinks the scale, so the fixed point is approached from below and a 3% margin clears it in one step; if it still does not, the run says `WILL NOT FIT` rather than shipping 5.9pt.

**Both bodies in one 4.8in figure does not fit, and that is a measurement, not an opinion.** The width is set by the label text, not by the drawing, and two bodies means two label columns:

| | box | at 4.33in | at 4.80in |
|---|---|---|---|
| `movement`, one arm | 740 x 728 | 4.33 x 4.26 in, **6.1pt**, fits | 4.80 x 4.72 in, 6.8pt, fits |
| `mass`, one arm | 832-870 x 728 | 3.62 in, 5.8pt, **fails** | 4.20 in, 6.1pt, fits |
| `movement`, both arms | 1877 x 728 | 1.68 in, 5.3pt, **fails** | 1.91 in, 5.4pt, **fails** |

So the CI figures ship as a pair of files at one scale, and only the `movement` layout clears the floor at the printed column. `--ci-both` is kept because the question is worth being able to re-ask if the measure changes.

#### The house style, and where this figure departs from it

`malignment.figure` holds the house publication constants in one place, and `prompt_slopes/plot.py` and `existence/channel_graph.py` both read it. This producer now reads it too, for the face:

| | house | here |
|---|---|---|
| family | `pub_font()` -> **Helvetica** | **Helvetica**, via the same resolver |
| size | `PUB_FONT_PT` = **9**, ONE size for every piece of text | **7.7 and 6.8**, two sizes |
| width | `PUB_SIZE` = **4.8** in | 4.8 in |

**The face is the same.** The mechanism differs and the difference favours this producer: in matplotlib a font it cannot find is not an error -- it substitutes DejaVu Sans and warns into a stream nobody reads, which is why the house has a resolver. An SVG `font-family` is a fallback CHAIN the renderer walks, so naming a stack is correct behaviour rather than a silent substitution, and the EPS converts type to outlines, freezing whatever this machine resolved.

**The size is not.** Two departures, both deliberate and both printed on every run so they cannot be forgotten:

- **Not 9pt.** 27 labels at 9pt put this figure at 5.6in wide against a 4.8in column. `channel_graph.py` records the same departure for the same reason: declare the size you actually print rather than declare the house size and ship something else.
- **Not one size.** The word sits at 7.7pt and its number at 6.8pt, because the hierarchy is doing work -- the reader finds the garment first and reads the number second.

Note also that `PUB_SIZE` takes the CI column as 4.8in on RH's own measurement, where the Weatherby and Justie issue measures 4.33in. 4.8 is kept because the rest of the paper's figures are drawn to it; `--ci-width 4.33` prints at the measured column, where the type falls to 6.1pt and still clears the floor.

#### `--ci-export`

    python figure.py --two-body movement --min-move 0.1 --ci --ci-export

Writes `.png`, `.tif` and `.eps` beside each `.svg`, all at one size: **1440 x 1352 px at 300 dpi = 4.800 x 4.507 in**, EPS box 345.600 x 324.432 pt. The EPS is vector with the type converted to paths, so it is the one to send if the journal will take it.

Two things the export has to do that the tools do not do by themselves. `rsvg-convert -d 300 -p 300` sets the RENDER dpi and still writes 72 into the PNG's `pHYs` chunk, which is the number a production desk reads, so the pixel width is pinned instead and the dpi written afterwards with `sips`. And cairo rounds `%%BoundingBox` up to whole points and emits no `%%HiResBoundingBox`, so a placed EPS would be up to a point wider than the figure; the exact box is added by hand.

The TIFFs are 7.6 MB each and are not committed; the SVG is, and one command regenerates them.

**Stacking the two bodies vertically does not rescue it either.** Two panels are 740 x 1456 units, and at 4.33in wide that prints 8.52in tall against a 7.0in working maximum. Cropping every scrap of vertical white gets to about 1320 units, still over the 1196 the aspect allows.

#### The unit, which the numbers do not announce

**`-0.41` is 0.41 PERCENTAGE POINTS, not 41%.** `pants` holds about 0.92% of the slot at base and about 0.39% after alignment; the median per-lineage change is -0.41 points of probability, or -0.0041 as a proportion. Read as a percentage of `pants` itself the fall would be about 58%, which is a different and much larger number. The axis names the unit -- "Fall in probability from base to aligned (percentage points)" -- and nothing else does. Writing the numbers as `-0.41%` would NOT imply points: a reader takes it either as a relative fall of 0.41% (the real one is about 58%) or as an absolute 0.41%, which is close enough to where `pants` lands that the misreading survives contact with the figure.

### `mass`: two distributions instead of a difference

Shades each garment by the share of the slot it actually holds in that arm; the difference survives as the signed number in the label, so nothing the original said is lost.

The ramp is white to black on `(share/10%)**0.45`, because the slot spans 0.12% (`tie`) to 9.08% (`clothes`), a factor of 76.

What the layout makes visible that X.1 does not: `shoes` goes 5.99% -> 9.30% and becomes the darkest thing on the page, while `clothes` goes 9.08% -> 6.23% and stops being it. The two bodies otherwise look alike, which is also true and is the reason the difference figure exists.

What it hides: proportionally large moves at the pale end. `panties` loses 69% of its mass (0.54% -> 0.17%) and `underwear` 73% (0.24% -> 0.06%), and at that end of the ramp both still read as almost-white.

**Greyscale is a different encoding, not a desaturation.** Converting RdBu to luminance maps the two ends to nearly the same mid-grey, so falls and rises would print identically. `--gray` runs a PIECEWISE monotone ramp -- falls take a pale band, rises a dark one, with a visible luminance step at zero -- and rewrites the legend and caption to say light and dark instead of red and blue. The sign survives the printer even where the magnitude does not.

## The body-part scenes: `body.py`

    python body.py        # -> results/body.md, results/body_words.csv

**The garment ordering generalises to the scenes whose slot takes a body part, on a ruler built elsewhere.** `slot_ratings/sexual` rates every (prompt, word) in context with `sexual_slot_en_v2`, and its `body_distance` (1 = the genitals ... 7 = off the body; 0 = not a place, excluded) and `genitality` are this folder's ruler for bodies. `body.py` runs `run.py`'s word-level test on them unchanged: unit = the word, median per-lineage delta over >= 10 carrying lineages, 50 endpoints. The prompts are a rule, not a list: every English prompt the instrument rated whose slot is a possessive (`... his` / `... her`), tested where >= 10 words are admitted.

| ruler | unit | positive | p | median rho |
|---|---|---|---|---|
| body_distance | prompt | **16 of 16** | 3.1e-05 | +0.362 |
| body_distance | scene (gender pair) | 11 of 11 | 0.00098 | +0.324 |
| genitality (negated) | prompt | 15 of 15 | 6.1e-05 | +0.243 |
| genitality (negated) | scene | 10 of 10 | 0.002 | +0.203 |

Strongest: `She grabbed his` +0.63, `...began to suck his` +0.59, `He unzipped her` +0.54, `He wrapped his tongue around her` +0.52. Weakest: `His fingers traced down her neck and along her` +0.04, `He reached down and touched her` +0.13. The took-off frames qualify by the rule but have 4 admitted words on this instrument; they are what `run.py` on scale D is for.

Three things bound it:

- **It was glimpsed before it was committed.** An uncommitted pass on 14 hand-picked prompts, same statistic, came first. That pass did not drop `body_distance = 0` or `is_modifier` words, and on it `She turned over after the massage and he saw her` ran the wrong way (-0.20); with the instrument's own exclusions it is +0.34. The exclusions are the instrument's convention (`slot_ratings/sexual` drops modifiers; 0 is defined as not applicable), not chosen here, but the flip is what they do and it is recorded.
- **No non-sexual control.** The instrument rates no non-sexual scene whose slot takes a body part (`held his` in a hospice, `blood poured from his`), so a general alignment preference for hands and faces is not excluded. That control needs new rating.
- **`slot_ratings/sexual` Layer 1 already showed the prompt-level version** (mass-weighted mean scale per arm, 33 lineages: `body_distance` up on 8 of 16 prompts, 0 down). This is the word-level version at 50 lineages, on a larger prompt set.

## What this does not settle

The original's section 4 withdrew an inference from this ordering to contiguity as against resemblance, on the ground that at `took off her ___` every candidate is a wearable so resemblance is present too. Both channels were measured independently there (rho -0.148, p=0.44), so the ordering result stands on its own and does not depend on resemblance being absent. **This folder measures the ordering. It does not adjudicate the relation.**

Nothing here was registered before it was run.
