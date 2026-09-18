---
subject: metonymy
status: "RUN 2026-09-18, 50 endpoint lineages, English, both took-off frames. Ports the `X_metonymy` finding out of `malign-logits/meta/M01_displacement` and re-runs it at 50 lineages on a new instrument. The word-level test and the figure producer are new here and are EXPLORATORY: nothing in this folder was registered before it was run."
kind: question
question: Inside one scene, does the word alignment moves TO sit further from the body than the word it moves FROM?
headline: "It does, and the ordering replicates at 50 lineages on an instrument built after the original. Unit = the word, statistic = the median of its per-lineage delta over the lineages that carry it, minimum 10 carriers: on the published scale D the correlation between how far out a word sits and how much alignment raises it runs rho +0.726 (n=72, p=5.3e-13) in the her-frame and +0.535 (n=57, p=1.8e-05) in the his-frame, and it is flat across carrier thresholds from 1 to 40. A NEW survey instrument, administered blind over 479 candidate nouns rather than the original's 122-word list, reproduces it independently: +0.524 (n=96) and +0.387 (n=78). Eight of the nine rulers give the same sign in both frames; the one null is scale A, the open dimension the coder named WITHOUT seeing the sentences, which is the priming comparison the original registration set up and is the scale the finding does not rest on. The PAIRED cell test -- top faller against top riser at the same cell, 100 cells -- is the weaker of the two and carries the her-frame only (35/50, p=0.0066 on D; 29/49, p=0.25 on his). **The figure X.1 needs no new garments**: all 27 + 22 words it draws still move at 50 lineages, every value keeps its sign but two near-zero ones, and `figure.py` recolors it from the producer's own output."
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

## `A` against `D` is the original's own priming check, and it fires

The registration asked the coder for an open dimension twice: once with the sentences withheld (`A`) and once with both sentences shown (`D`). Identical scores would mean the scene adds nothing to the ranking. A is the only null in the grid, in both frames, and D is the strongest ported scale in both. Suggested reading, not asserted: the ordering the finding measures is one the coder produces when shown the scene and does not produce from the word list alone. What that says about the construct is a separate question from whether the ordering exists -- the survey instrument, built later and shown both frames as named fields, reproduces it.

## The new instrument

`survey.py` administers one gate and three degree scales over `candidates()`, which is a POS filter on the whole moving vocabulary and not a list of movers. The coder was never told which words moved, on either instrument. Wording, drafts and the two review passes are in `data/levels_draft.md` and `data/levels_review*.md`.

Two arms see one item. `state_text()` is the single renderer, so the jev cache key's state and the text arm's prompt are byte-identical and a cross-arm check is string equality.

**The gate is off the scales.** An earlier draft listed NOT_AN_OBJECT first on every scale, which makes it position 0 of an ORDERED array: a `Score` interpolates, so a word could come back four-tenths of the way from not being a thing to uncovering nothing, and position 0 means the opposite thing on different scales. One `Choice`, asked once, categorical.

**All three scales run low = intimate, high = peripheral,** so the substantive prediction is ONE direction on all three. An earlier draft documented the direction backwards, before any data.

**No level exemplar is a candidate word.** `blouse`, `briefs`, `camisole`, `cummerbund`, `waistcoat`, `cardigan` and `umbrella` all were, at various drafts; `umbrella` sat at p=0.00097 against a floor of 0.00100. The exemplar list is now GENERATED from the level arrays and checked against the candidate set rather than asserted: 16 exemplars, zero overlap.

### The veto gate, and why it doubled the agreement

jev accepts BPE fragments as garments and deepseek does not. 58 words jev placed in the worn set deepseek called NOT_A_WORD -- 40 of them jev called GARMENT outright (`blaz`, `kimon`, `knick`, `legg`, `trou`, `underp`, `shir`) -- and **zero** went the other way. A word enters the scale only if BOTH arms place it in the worn set:

| scale | all 479 rows | the 181 that pass the veto |
|---|---|---|
| exposure | rho +0.339 | **+0.809** |
| position | rho +0.405 | **+0.911** |
| dressing | rho +0.347 | **+0.753** |

The disagreement is a fragment problem, not a scale problem: on words both arms accept as things, the two coders agree at 0.75 to 0.91.

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

Two drawing fixes travel with the two-body layouts. The body strokes were drawn at a garment's weight, so at 4.5 the arms read as a filled dark layer rather than a limb; `THIN` takes the two arms to 2.4 and leaves the legs alone, since they sit inside trousers and want their weight. And `BORDER_OPACITY` lifts the garments' own outlines off their fills at 0.45, so six nested rectangles read as depth rather than as six drawn boxes.

**`LAYER_SWAP` is a correction to the drawing, not to the data.** The source nests the torso outward as top, shirt, sweater, jacket, robe, coat, which puts a robe OUTSIDE a jacket. A robe is indoor and sits nearer the skin; a jacket is outerwear. The two-body layouts swap which word owns which shape, which fixes the ordering without touching a coordinate: the label pointing at the outer shape now reads `jacket` and the one pointing at the inner reads `robe`. `--no-layer-swap` keeps the published nesting. `build()` is a faithful recolour of X.1 and is left alone, so the figure of record keeps the layering it was published with.

One ramp serves both bodies, so a fall and a rise of the same size print the same grey. That costs the falls their contrast -- the biggest fall is 0.55 pp against a biggest rise of 2.65 -- and **the asymmetry is the thing the layout exists to show**: the withdrawal spreads over twenty garments while the return concentrates on two. A per-body ramp would hide exactly that.

### `mass`: two distributions instead of a difference

Shades each garment by the share of the slot it actually holds in that arm; the difference survives as the signed number in the label, so nothing the original said is lost.

The ramp is white to black on `(share/10%)**0.45`, because the slot spans 0.12% (`tie`) to 9.08% (`clothes`), a factor of 76.

What the layout makes visible that X.1 does not: `shoes` goes 5.99% -> 9.30% and becomes the darkest thing on the page, while `clothes` goes 9.08% -> 6.23% and stops being it. The two bodies otherwise look alike, which is also true and is the reason the difference figure exists.

What it hides: proportionally large moves at the pale end. `panties` loses 69% of its mass (0.54% -> 0.17%) and `underwear` 73% (0.24% -> 0.06%), and at that end of the ramp both still read as almost-white.

**Greyscale is a different encoding, not a desaturation.** Converting RdBu to luminance maps the two ends to nearly the same mid-grey, so falls and rises would print identically. `--gray` runs a PIECEWISE monotone ramp -- falls take a pale band, rises a dark one, with a visible luminance step at zero -- and rewrites the legend and caption to say light and dark instead of red and blue. The sign survives the printer even where the magnitude does not.

## What this does not settle

The original's section 4 withdrew an inference from this ordering to contiguity as against resemblance, on the ground that at `took off her ___` every candidate is a wearable so resemblance is present too. Both channels were measured independently there (rho -0.148, p=0.44), so the ordering result stands on its own and does not depend on resemblance being absent. **This folder measures the ordering. It does not adjudicate the relation.**

Nothing here was registered before it was run.
