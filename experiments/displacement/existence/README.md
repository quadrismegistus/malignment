---
subject: existence
status: "RUN 2026-08-30, 50 endpoint lineages, English. Saturation x lift stratification, the conditional FIELD test and the field matrix added 2026-09-05; those sections are EXPLORATORY and unregistered."
kind: question
question: Is alignment's reshaping of word probabilities content-selective, and is it displacement or suppression?
headline: "Displacement exists: higher-T words lose more mass (43/50 lineages), and it holds under the deployment frame 2.8x larger. Where the mass GOES is not adjacency. On USAS fields it LEAVES the faller's own field (10/38 fine, 10/39 coarse) for a classified word rather than an unclassified one (38/7), and the destination barely depends on the origin -- linguistic acts is in the top 5 for 17 of 18 source domains. Under lift the funnel narrows toward speech (37/11) and away from social action (11/36). The same-kind result (47/2) holds only where the prompt field is already charged and REVERSES where the scene is neutral (1/45, 9/35, 12/27)."
---

# existence

**The step-1 finding. Everything else in `displacement/` asks about the shape, the scale, or the conditions. This asks whether it happens at all.**

Alignment changes word probability distributions — JS > 0 between base and aligned for every pair. That is not a finding; it would be surprising if it didn't. The question is whether the change is SELECTIVE BY CONTENT: do words that carry more transgressive charge lose more mass? And if so, where does the freed mass go?

## Part 1: content-selectivity (`run.py`)

Within each cell (one prompt × one endpoint pair), every candidate word carries a scene rating (1-7, from `charge.py`) and a delta (p_aligned - p_base). The test: regress delta on scene within each cell.

    SLOPE OF delta ~ scene (within cell)
    lineages with negative median slope:     43
    lineages with positive median slope:      7
    sign test p:                             2.1e-07
    grand median slope:                      -0.000295

**Higher-scene words lose more mass under alignment.** 43 of 50 lineages, p = 2.1e-07.

**This block said 40/10 and p=0.000024 until 2026-09-03.** Those were the numbers
of a run before the one that wrote `results/selectivity.json` on 31 Aug, and the
prose was never brought forward with the artifact. Re-run to settle it rather
than to choose between them: 43/7 exactly, reproducing the stored JSON to the
digit. The direction never moved; the sign count and the p-value did.

The faller/riser breakdown sharpens it:

    risers only     49 neg / 1 pos   p < 1e-6   med = -0.000336
    fallers only     7 neg / 43 pos  p < 1e-6   med = +0.000130

Among risers, the less transgressive ones gain more — alignment promotes the milder alternatives. Among fallers, the more transgressive ones fall less steeply — a floor effect (words near zero can't fall further).

### Stratified by dose

Content-selectivity holds at every dose level up to 5, then goes null at the extreme:

    band             cells  neg/pos          p   med slope
    1-2 (neutral)    36094   46/4      < 1e-6   -0.000584
    2-3 (mild)       26145   39/11     0.00009   -0.000241
    3-4 (moderate)   20887   37/13     0.00094   -0.000291
    4-5 (strong)     14784   34/16     0.015     -0.000231
    5-7 (extreme)    14481   31/19     0.119      NULL

The null at 5-7 is the saturation: frames already rated 6+ have candidate words no more transgressive than the setup, so there is nothing for alignment to selectively target.

### Stratified by lift

The gradient is monotonic. As lift increases (words add more charge beyond the setup), alignment is MORE content-selective:

    lift band        cells  neg/pos          p   med slope
    < 0 (no lift)    12184   31/19     0.119      NULL
    0-0.5 (low)      82848   41/9      6e-6    -0.000293
    0.5-1 (moderate) 14951   42/8      1e-6    -0.000446
    1-2 (high)        2408   41/9      6e-6    -0.000614

Selectivity scales with what the words contribute. Where they contribute nothing (lift < 0), alignment reshapes but not by content.

## THE DEPLOYMENT FRAME: it survives, 2.8x larger

`run.py --frame prefill`. The aligned arm measured inside its chat template
rather than bare, against the same raw base -- `base_raw -> aligned_framed`.

    same 45 pairs              RAW          FRAMED
    lineages negative          39 / 45      41 / 45
    grand median slope         -0.000276    -0.000780
    sign test p                1e-6         < 1e-6

**Content-selectivity is not an artifact of measuring the aligned arm bare.**
Putting it in the frame a user actually meets strengthens the effect, in the same
direction `instrument_calibrations/frame_prefill` finding 15 reports for the arm
contrast at large, where raw understates by 1.74x.

### Three things that make this readable, and none is optional

**THE CONTRAST IS ASYMMETRIC.** 43 of 50 bases ship no chat template, so there is
no framed base to compare against. This is not the same test conducted inside the
frame; it is the DEPLOYED arm against the BARE one, and it changes two things at
once by design, because in deployment they are never separate.

**THE POPULATION IS 45, NOT 50, AND THE RAW COLUMN ABOVE IS RUN ON THE SAME 45.**
`--match-framed` exists for exactly that: read against the 50-pair raw headline,
a framed difference would be partly which labs ship a template. Two pairs are
excluded because their system slot carries text no empty message can remove
(SmolLM3-3B's metadata block, Llama-3.1-8B-Instruct's `Cutting Knowledge Date`),
and three because they are unframed.

**`frame_aligned='prefill'` ALONE IS NOT THE FILTER.** `system_mode` records the
argument passed to the producer, not the treatment the model received, and the
two disagree in both directions -- Qwen at `system_mode='empty'` still renders a
151-character persona, gemma at `default` renders no system turn at all. The
population comes from `movement.clean_frame_pairs()`, which reads what each
template actually RENDERED into the system slot
(`roster/models/chat_renders.json`).

    results/selectivity_framed.json      the framed run
    results/selectivity_raw_on45.json    raw on the same pairs
    results/selectivity.json             the 50-pair raw headline, unchanged

## THE FRAME WITH THE WEIGHTS HELD FIXED (`--frame self`)

Self-edges: `base == aligned`, unframed against framed. Nothing changes but
whether the prompt is wrapped in a chat template. 45 aligned models -- every one
in the framed population, so this column spans the same models as the other two
-- and 8 base models as the control.

    contrast                        content-selective   same-kind landing
    base_raw    -> aligned_raw       43/50   p=2e-7      42/44   p<1e-6
    base_raw    -> aligned_framed    41/45   p<1e-6      45/45   p<1e-6
    aligned_raw -> aligned_framed    40/45   p<1e-6      45/45   p<1e-6
    base_raw    -> base_framed        4/4    p=1.000      8/8    p=0.0078

### What the four rows say, without interpretation

**Alignment displaces on its own** -- row 1, no frame anywhere.
**The chat frame displaces too** -- row 3, no weight change anywhere.
**But only on weights alignment has touched** -- row 4 is null on content.
**Together they displace more** -- row 2, about 2.8x row 1.

Neither effect is a weakened version of the other. If raw displacement were the
same pattern at lower gain, per-word `delta` would correlate near 1 between the
raw and framed conditions. It correlates at **median r = 0.574** over 20
lineages (range 0.009 to 0.79), so about two thirds of the variance is not
shared: the frame changes WHICH words move, not only how far.

The precise form is an INTERACTION. The frame's effect on displacement is
conditional on aligned weights; alignment's effect is present without the frame.

### THE DISSOCIATION, which is the result

    frame alone            content-selective?   same-kind landing?
      aligned  n=45        40/45  p<1e-6        45/45  p<1e-6
      base     n= 8         4/4   p=1.000        8/8   p=0.0078

**Content-selectivity needs aligned weights. Same-kind landing does not.**

Base models reproduce the same-kind pattern perfectly -- 8 of 8 -- while showing
no content-selectivity whatever. Semantically adjacent words are substitutes in
any language model, so any perturbation redistributes mass among them. Adjacency
is a property of the LEXICON. What alignment supplies is the DIRECTION: that the
words losing mass are the higher-charge ones.

This qualifies Part 2 below. `47/49 same-kind` is real and is less diagnostic
than it looks, because a base model under a template it never saw reproduces it
without any alignment involved.

### NEVER POOLED, and why the producer prints the split

Pooled, content-selectivity reads 44/9 at p=1e-6 and would have been written up
as "the frame displaces by content". The 8 base models were being carried by the
45. RH ruled against pooling before the run; the arm split is printed by `run.py`
and `adjacency.py` rather than left to whoever opens the JSON, because a pooled
number that has assumed its own conclusion does not announce itself.

### Fences on the control

**n=8 is permanent.** A base self-edge needs a base with a chat template and only
8 exist in the roster.

**Those 8 are the strangest template cases there are.** Qwen ships base templates
deliberately; `neo_7b` and `Tanuki-8B-base` carry templates byte-identical to
their aligned siblings; `llama-7b` renders Llama-2 format on a Llama-1 model that
never saw it. Three of eight arguably measure "the wrong template applied".

**The cells are valid but narrower.** Checked, not assumed: `conservation` 1.0
and `mojibake` ~0 on all 8, so no leakage or garbage. But every base loses 10-26%
of its candidate words under the frame, so the control is a narrower distribution
and not a clean null. Read it beside its own `n_words`.

**So 4/4 is a WEAK null** -- consistent with no effect and with an effect too
small to see at n=8. The 8/8 same-kind result is the stronger of the two control
readings, since a unanimous sign test at n=8 is p=0.0078 on its own.

## Part 2: displacement vs suppression (`adjacency.py`)

**Also run framed.** `adjacency.py --frame prefill` and `--match-framed`, the
same two flags and the same three fences as Part 1 above:

    same 45 pairs                 RAW          FRAMED
    same-kind gains more          42 / 44      45 / 45
    none-kind gains more           2            0
    same-kind median delta        +0.013634    +0.017398
    none-kind median delta        +0.009593    +0.010550
    same/none ratio                1.42x        1.65x

Unanimous under the frame, and the gap widens. Both lineages that ran the wrong
way raw flip to same-kind.

**Read the 45/45 with its denominator.** Qualifying cells fall from 13,049 to
6,227, because a cell needs a rated non-NONE top faller AND both a same-kind and
a none-kind riser, and the framed arm supplies that combination less often. So
this is unanimity on half the data, not unanimity on more of it.

**AND THE RAW COLUMN IS 44 LINEAGES, NOT 45.** `archangel_sft-dpo_pythia2-8b`
has ONE qualifying cell raw and clears the threshold framed, so the
`n_cells < 10` guard drops it from one column and keeps it in the other:

    archangel_sft-dpo_pythia2-8b   raw n=1 cell   framed n>=10

`--match-framed` matches the PAIRS and cannot match which lineages survive a
per-lineage minimum, because that depends on how many cells each arm supplies.
The 42+2 in the table sums to 44 for this reason and not because a lineage tied
-- there are no exact ties in either column, checked. It is one lineage on one
cell either way, so it moves nothing; it is recorded because a sign count that
silently changes its denominator between two columns is the thing a reader would
otherwise take as given.


### THE SAME-KIND RESULT REVERSES WHERE THE PROMPT'S FIELD IS MOSTLY NEUTRAL

**The population guard above tests PRESENCE, not BALANCE.** A cell qualifies if it
has both a same-kind and a none-kind riser, which correctly excludes a fully
saturated prompt -- but a prompt with 60 VIOLENT candidates and 3 NONE ones
qualifies, and in it "same-kind wins" is nearly arithmetic.

**And this test selected on neither dose nor lift, where Part 1 above selects on
both.** No reason for the difference was ever recorded. The stratification now
lives inside `adjacency.py` rather than in a separate script, so it uses the same
per-cell means and per-lineage medians as the headline and cannot drift from it.

    saturation = share of a prompt's rated words carried by its top non-NONE kind

RAW, `base_raw -> aligned_raw`. Headline for this population: **47/2**.

    sat  lift   lineages  cells   same med   none med   up/dn        p
    lo   L-lo         46   1021    0.00838    0.01396    1/45   0.00000
    lo   L-mid        44    737    0.01061    0.01481    9/35   0.00011
    lo   L-hi         39    750    0.01123    0.01366   12/27   0.02370
    mid  L-lo         48   1719    0.01177    0.00989   37/11   0.00022
    mid  L-mid        47   1404    0.01550    0.01056    43/4   0.00000
    mid  L-hi         44   1196    0.01620    0.01080    38/6   0.00000
    hi   L-lo         48   3759    0.01262    0.00703    48/0   0.00000
    hi   L-mid        46   1444    0.01469    0.00664    46/0   0.00000
    hi   L-hi         28    386    0.01741    0.00792    27/1   0.00000

FRAMED, `base_raw -> aligned_framed`, `--match-framed`. Headline: **45/0**.

    sat  lift   lineages  cells   same med   none med   up/dn        p
    lo   L-lo          7     83   (too few lineages to sign-test)
    lo   L-mid        10    114    0.01251    0.02073     1/9   0.02148
    lo   L-hi         27    422    0.01801    0.02227   11/16   0.44207
    mid  L-lo         41    569    0.01895    0.01124    35/6   0.00000
    mid  L-mid        28    348    0.02358    0.01376    23/5   0.00091
    mid  L-hi         34    464    0.02199    0.01285    25/9   0.00904
    hi   L-lo         45   2318    0.01604    0.00723    45/0   0.00000
    hi   L-mid        44    759    0.01796    0.00767    44/0   0.00000
    hi   L-hi          6     66   (too few lineages to sign-test)

**The pooled 47/2 is a fact about prompts whose field is already charged.** Where
the scene is mostly neutral the effect does not weaken, it REVERSES: raw 1/45 at
low lift, 9/35 at mid, 12/27 at high -- all three bands, p from 1e-5 to 0.024.
Framed reproduces it wherever the cell is thick enough to test (1/9, p=0.021).

Lift MODERATES the reversal without flipping it: within low saturation the
same/none gap closes monotonically as lift rises (1/45 to 9/35 to 12/27), so
charge pushes toward same-kind landing but cannot produce it in a neutral field.

So freed mass does not seek semantic neighbours. **It lands where the prompt has
put the words.** Where same-kind material is scarce, the behaviour is
suppression, decisively. That is a second reason the 47/2 is less diagnostic than
it reads, independent of the base-model one recorded above -- and unlike that
one, this reverses rather than merely failing to discriminate.

### THE POPULATION DOES NOT SHIFT, AND AN EARLIER VERSION OF THIS SECTION SAID IT DID

Qualifying cells by saturation band, over the FULL populations:

    condition   qualifying cells      lo     mid      hi
    raw                   14,684     19%     35%     46%
    framed                 6,227     19%     26%     55%
    self                   9,114     19%     27%     54%

**The low-saturation band -- the one where the effect reverses -- is 19% in all
three conditions.** So the strengthening from raw 47/2 to framed 45/0 is NOT
explained by the framed contrast shedding the band that runs the other way. There
is a real mid-to-hi shift of about nine points, and it is much smaller than a
composition account of the framed result would need.

**A previous version of this section claimed lo fell 20% -> 12% -> 4% across the
three conditions and concluded that part of "unanimous under the frame" was
composition.** That was arithmetic over the printed TABLE ROWS, which include
only lineage-by-stratum combinations holding at least ten cells. Summing a
display is not a census: the self condition has 9,114 qualifying cells, not the
537 that version quoted. The composition claim is WITHDRAWN.

### THE SELF-EDGE STRATIFIED TABLE IS THE BASE ARM ONLY

`charge.lifts_per_lineage(b)` is keyed by `(prompt, base)` and covers exactly the
50 endpoint BASES. On a self-edge `base == aligned`, so an aligned self-edge asks
for the lift of an aligned model, which has no entry -- **and the whole aligned
arm drops out of the stratified table silently**, leaving the 8 base-arm
lineages. That is what the single surviving cell reports:

    hi   L-lo   8 lineages   290 cells   0.00911 vs 0.00530   8/0   p=0.0078

Eight lineages, which is the base arm exactly. The unstratified self-edge
headline (45 aligned / 0, 8 base / 0, never pooled) is unaffected -- it uses no
lift. **Only the stratified view is restricted, and it does not announce it.**
Stratifying aligned self-edges needs the lift of the lineage ROOT rather than of
the model itself, which is the convention `data_ablations/ladder.py` already uses
for intermediate checkpoints. NOT YET DONE.

### A COUNT IN THIS FOLDER DOES NOT RECONCILE

Part 2 above states qualifying cells falling "from 13,049 to 6,227". The framed
number reproduces exactly; the raw one does not -- this run finds 14,684, and
`adjacency.py`'s own riser-group line prints n=14,685. Recorded rather than
silently corrected, because which of the two is stale has not been established.

### THE CONDITIONAL FIELD TEST: MASS LEAVES THE FIELD IT CAME FROM

`adjacency.py` now runs the same comparison on USAS semantic fields as well as on
`kind`. **Conditioning on the top faller's own field is the part `norm_change`
cannot supply**: that folder gives the MARGINAL shift over 50 lineages (aggression
down, speech and sensation up, raw and framed), and a marginal shift cannot
distinguish "each aggression word's mass went to speech" from "unrelated words
moved in both fields". That distinction is displacement against suppression.

    comparison                          lineages   up/dn          p
    -- FINE (232 USAS codes)
       same-field vs DIFF-field              48    10/38   0.000062
       same-field vs NO-field                45    38/ 7   0.000003
       cells: 3,964 across 49 lineages
    -- COARSE (21 top-level domains)
       same-field vs DIFF-field              49    10/39   0.000038
       same-field vs NO-field                46    41/ 5   0.000000
       cells: 8,461 across 50 lineages

**Freed mass leaves the faller's own semantic field and lands in a different one
-- but in a CLASSIFIED word, not an unclassified one.** Both halves are decisive
and they point opposite ways, which is what makes the result informative: this is
neither adjacency nor scatter. It is directed substitution ACROSS fields.

**THE GRAIN IS CONTROLLED.** USAS has 232 fine codes against `kind`'s six, so a
cross-field result could be nothing but resolution. At the top-level letter --
21 domains, comparable in coarseness to the harm taxonomy -- the answer is
unchanged (10/39 against 10/38). The move is a fact about the movement, not about
the ruler.

**What this does to "semantically adjacent but safer".** The SAFER half stands
(49/0 at +1.61 where the field is not saturated). The ADJACENT half does not
survive in the field sense: mass does not stay in the domain it left. What
`kill -> scream` names is a domain CHANGE -- "Life and living things [-]" to
"Speech acts" -- with the scene and the affect preserved and the act replaced.
`displacement_taxonomy`'s relation 2 is the right description and "adjacency" is
the wrong word for it.

**Do not read this against the 47/2 same-kind result as a contradiction.** The
two tests select different populations -- one needs a non-NONE top faller with
both same-kind and none-kind risers, the other a field-carrying top faller with
both same-field and diff-field risers -- so they are not two measurements of one
quantity and the dissociation between them is not established here.

EXPLORATORY. Not registered. The USAS grain cut is the only control run on it.

### WHICH FIELDS SUBSTITUTE FOR WHICH: IT IS A FUNNEL, NOT A MATRIX

`field_matrix.py`. Having established that mass leaves the faller's field, this
asks where it goes. **The baseline is the entire question.** Against a global
base rate the diagonal dominates -- body->body x8.2, food->food x14.6,
architecture->architecture x19.7 -- and that is prompt composition, not routing: a
body-scene prompt offers mostly body words, so its fallers and risers are both
body words. Baselined instead on **the base distribution's own mass over that
cell's candidates**, the ratio asks whether mass went somewhere MORE than the
prompt's own vocabulary made likely, and **the diagonal disappears from every
row**.

    faller domain          cells   strongest destinations (x availability)
    Z grammar/names        27797   X 1.40  E 1.37  Q 1.22  S 1.18
    A general/abstract     21104   Q 1.38  X 1.33  S 1.27  E 1.24
    M movement             17104   B 1.26  Q 1.22  X 1.20  S 1.13
    Q linguistic acts       9728   B 1.27  X 1.27  S 1.15  T 1.14
    X psychological         5184   K 1.67  S 1.36  Q 1.31  T 1.13
    S social                4970   Q 1.38  K 1.26  E 1.24  X 1.23
    B the body              3459   Q 1.22  X 1.20  T 1.11  Z 1.07
    E emotion               2843   K 1.52  Q 1.29  T 1.18  X 1.13
    L life & living         1996   Q 1.85  K 1.27  T 1.23  B 1.21
    I money                 1738   Q 1.40  X 1.37  T 1.13  B 1.11
    G govt & public         1455   Q 1.37  X 1.24  T 1.15  B 1.14
    Y science                785   X 1.43  O 1.36  E 1.29  Q 1.21

**The destination barely depends on the origin.** Over 18 source domains:

    in the top 5 destinations of...        is the strongest destination for...
      Q linguistic acts   17 of 18           Q linguistic acts   7
      X psychological     16 of 18           K entertainment     5
      S social            13 of 18           X psychological     3

Whatever the mass was, it moves toward **speech, mental states and social
action**. That is why the conditional test finds it leaving its own field: it is
not being routed to a neighbour, it is being routed to one destination.

### DOSED BY LIFT: the SPEECH destination intensifies, the social one decays

Same availability baseline, split by the prompt's lift:

    band       cells   mean Q enr   mean X enr   mean S enr      L->Q
    L-lo       71495        1.264        1.289        1.172     1.220
    L-mid      17544        1.397        1.189        1.110     1.801
    L-hi        6710        1.544        1.275        1.104     2.654

With the LINEAGE as the unit -- enrichment in `L-hi` minus `L-lo`, sign test,
a lineage contributing only where both bands clear 30 weighted cells for it:

    Q enrichment, any source     48 lineages   37/11   p=0.000222   CONFIRMED
    S enrichment, any source     47 lineages   11/36   p=0.000346   CONFIRMED
    X enrichment, any source     47 lineages   21/26   p=0.560      null
    L -> Q enrichment             1 lineage     1/ 0   p=1.000      UNTESTABLE

**The funnel is not uniform under dose.** The more charged the site, the more of
the freed mass goes to SPEECH (37 of 48 lineages) and the LESS goes to social
action (11/36 the other way). Psychological states are flat. So the destination
set narrows toward the linguistic as charge rises.

**AND THE MOST QUOTABLE NUMBER IN THE TABLE DOES NOT SURVIVE ITS OWN UNIT TEST.**
`L -> Q` -- the killing domain to linguistic acts, 1.22 to 2.65 -- is the cell
this campaign has been describing since `kill -> scream`, and pooled it looks
like the strongest dose effect here. Only ONE lineage carries enough `L` cells in
both bands. The pooled ratio is real arithmetic over the corpus and it is not
evidence about lineages, and it should not be quoted as the dose-response of
`kill -> scream`. What IS supported is the same shape one level up: sources in
general route to speech more as lift rises.

`norm_change` reached the marginal version of this independently -- *"vocalisation
is DOSE ONLY, flat marginally and among the steepest slopes in the folder under
dose"*, +0.386 at p=9e-5 on the contextual instrument. The conditional version
here agrees on the direction and adds that it is at the expense of the social
destination, not of the psychological one.

EXPLORATORY. Not registered. Rows below 500 weighted cells are not printed, and
`P education`, `C arts` and `W world` never reach it.

### WHERE THE DISPLACEMENT CLAIM STANDS: THE TWO HALVES SEPARATE

"Mass falls to a semantically adjacent but SAFER word" is two claims, and they
are supported in different, non-overlapping regimes.

**SAFER** -- scene rating of the top faller minus the mass-weighted scene of the
risers. Continuous, and testable WITHIN a saturated prompt, since a violent field
still runs `strangle` 7.00 down to `run` 1.95:

    sat   lineages   cells   median diff    up/dn        p
    lo          49    6450       +1.6087     49/0   0.000000
    mid         49    9670       +0.4144     49/0   0.000000
    hi          40   46655       -0.0019    14/26   0.081

**ADJACENT** -- the same-kind test above: unanimous at hi, reversed at lo.

**So the composite sentence is never demonstrated in one place by this
instrument.** Where landing is same-kind it is not safer; where it is safer it is
not same-kind.

### AND THE KIND TAXONOMY IS THE WRONG INSTRUMENT FOR "ADJACENT"

`kind` sorts by HOW BAD, not by WHAT ABOUT. The campaign's own paradigm case of
displacement fails its test: on `She was so angry she wanted to`, `kill` is
VIOLENT at 6.98 and `scream` is NONE at 2.54, so **"kill -> scream" is CROSS-kind
here and scores as suppression.** Six harm categories cannot represent semantic
adjacency, and `displacement_taxonomy` exists because they cannot.

That folder's ten blind-coded relations contain both regimes -- **1. LATERAL SWAP
INSIDE ONE REGISTER** (same kind, "no change in register, harm, or aggression",
flat on all scales but directedness) and **2. BLOW BECOMES UTTERANCE** (physical
displaced by vocal, harm -1.20). The correspondence to the hi and lo bands is
close enough to be worth stating and IT WAS TESTED AND DID NOT HOLD.

### THE RISERS ARE THE SAME WORDS IN BOTH BANDS

Rated risers only, 20 endpoint pairs, top 12 by mass:

    lo   found, said, began, placed, have, handed, whispered, looked, made, watched, took, asked
    hi   said, found, have, take, whispered, began, watched, took, left, pulled, made, walked

Share of rated riser mass going to a fixed 36-word vocalisation list: **lo 7.5%,
mid 8.7%, hi 8.1%.** Flat. So the low band is NOT "blow becomes utterance", and
the mapping above is withdrawn as a hypothesis that failed its first test.

**What the two lists show instead is that the destination barely depends on the
field.** The same generic narrative verbs absorb the mass either way. That argues
against routing-to-a-semantic-neighbour and toward something closer to
`TAXONOMY.md` relation 7, BLEACHED CONTINUATION -- though nothing here tests that
relation directly and it should not be quoted as if it did.

**What this leaves standing.** The SAFER half is solid and large where the field
is not already saturated (49/0 at +1.61). The ADJACENT half, as operationalised
by harm category, is a fact about field composition rather than about routing.
The right instrument for adjacency is `displacement_taxonomy`'s coded relations.
**NOT an embedding distance** (RH): `scream` is not near `kill` in embedding
space however well the substitution reads, because the adjacency at work is
scenic and narrative -- same situation, same affect, different act -- and
distributional similarity does not encode it. Both the harm taxonomy and
embedding distance fail the paradigm case, in opposite directions.

### THREE AGGREGATIONS, AND TWO OF THEM WERE WRONG

Recorded because they gave three different answers to one question and the first
two were reported before the third was run:

1. All raw edges in the store, median of per-cell medians. Low band 33/55
   reversed. **Wrong population** -- 88 edges including ladder rungs and
   transitive ones, which is pseudo-replication.
2. Endpoint pairs, all deltas pooled per lineage. Low band 24/24, an exact null.
   **Wrong aggregation** -- `adjacency.py` takes a MEAN per cell and a MEDIAN
   over cells, and pooling cancelled the reversal against the recovery.
3. Endpoint pairs, `adjacency.py`'s own accumulation. Low band 1/45, 9/35, 12/27.
   **Reported.** It is the only one that shares a code path with the headline.

The lesson is the one this folder keeps relearning: a summary statistic is an
undeclared choice, and a re-implementation is a different instrument until it is
checked against the original line by line.

FENCES. Saturation bands are equal thirds, lift bands cut at 0.5 and 1.2; neither
was pre-declared. Eighteen cells across the two tables, so single p-values near
0.02 are not much after correction -- the 1/45 and the 48/0 do not need it.
Lift is English-only, so the stratified tables drop Chinese cells the headline
keeps. Self-edges are run separately. EXPLORATORY, not registered.

Content-selectivity says alignment targets transgressive words. The next question is WHERE THE FREED MASS GOES. Three hypotheses:

- **Displacement** (Freudian): mass redirects to semantically adjacent words in the same domain. "kill" → "scream" — same anger frame, lower charge. The drive is not extinguished; it finds an adjacent outlet the censor permits.
- **Suppression** (behaviorist): mass moves to neutral words. "kill" → "said". The response is simply extinguished.
- **Diffusion**: mass scatters uniformly. No preference for any target.

The test: for each cell's top faller, note its `kind` (SEXUAL, VIOLENT, COERCIVE, etc). Among the risers, compare mass gained by same-kind vs NONE-kind words.

    SAME-KIND vs NONE-KIND risers (median delta per lineage)
    lineages where same-kind risers gain MORE:    47
    lineages where none-kind risers gain MORE:     2
    sign test p:                                  < 1e-6

**47 of 49 lineages.** Freed mass lands preferentially on words of the same kind as the faller. That is displacement, not suppression.

The mass gained and the scene ratings of each group:

    same-kind risers:  delta +0.0133   scene 3.36
    diff-kind risers:  delta +0.0097   scene 3.77
    none-kind risers:  delta +0.0095   scene 2.23

Same-kind risers gain 40% more mass than NONE risers. They carry intermediate charge (3.36) — less than the faller, more than neutral. The charge is diluted, not eliminated.

Diff-kind risers carry the HIGHEST scene ratings (3.77) but gain less mass than same-kind. The charge stays within its domain rather than jumping to whatever is most transgressive elsewhere.

### Examples

**VIOLENT frame:** "She was so angry she wanted to" (Aquila2-7B)

    FALLER:  kill         VIOLENT  scene=7.0   p: 0.551 → 0.058
    RISER:   rip          VIOLENT  scene=4.0   p: 0.000 → 0.026
    RISER:   stab         VIOLENT  scene=7.0   p: 0.001 → 0.020
    RISER:   throw        VIOLENT  scene=3.0   p: 0.003 → 0.014
    RISER:   cry          NONE     scene=2.0   p: 0.002 → 0.279
    RISER:   scream       NONE     scene=2.0   p: 0.026 → 0.204

`kill` loses 49 points of probability. The violent alternatives (`rip`, `stab`, `throw`) gain, but the largest single gainer is `cry` — a NONE word. Displacement and partial suppression coexist in a single cell. The aggregate test says displacement wins across the roster; individual cells can show either or both.

**SEXUAL frame:** "At home, he climbed into her bed while she was half asleep and" (Yi-1.5-9B)

    FALLER:  kissed       SEXUAL   scene=5.0   p: 0.043 → 0.015
    RISER:   whispered    SEXUAL   scene=3.0   p: 0.023 → 0.131
    RISER:   gently       SEXUAL   scene=3.0   p: 0.005 → 0.019
    RISER:   snuggled     NONE     scene=2.0   p: 0.008 → 0.020

`kissed` → `whispered`. The sexual charge is preserved — the scene is still intimate — but softened from explicit contact to speech. The substitution is within the domain at a lower intensity.

**COERCIVE frame:** "A line worker keeps filing safety complaints about the cutting li..." (Amber)

    FALLER:  have         COERCIVE scene=3.0   p: 0.168 → 0.000
    RISER:   recommend    COERCIVE scene=3.0   p: 0.001 → 0.124
    RISER:   suggest      COERCIVE scene=3.0   p: 0.001 → 0.066
    RISER:   understand   NONE     scene=2.0   p: 0.002 → 0.109

`have` (as in "have them stop") is completely eliminated. `recommend` and `suggest` rise — same institutional frame, same coercive charge, but the stance shifts from directive to advisory.

## What is established

1. **Displacement is content-selective.** A word's transgressive charge predicts how much mass it loses under alignment (40/50 lineages, p = 0.000024).
2. **Selectivity scales with lift.** Where the candidate words add charge beyond the setup, alignment is more selective. Where they don't (saturated frames), it reshapes but not by content.
3. **It is displacement, not suppression.** Freed mass lands preferentially on same-kind words (47/49, p < 1e-6), not on neutral words. The charge redirects within the semantic domain.
4. **Risers carry intermediate charge.** Same-kind risers have scene ratings of 3.36 — less than the fallers they replace, more than neutral words. The drive is diluted, not extinguished.

## Part 3: the variance decomposition

Direction (riser vs faller) is not stable across models. The same word on the same prompt goes both ways across lineages — measured on 68,252 (word, prompt) pairs with 5+ lineages:

    level                              consistency
    word alone (all prompts + models)     0.35
    word + prompt (across models)         0.47

Only 9.7% of (word, prompt) pairs are unanimous; 62% are near-50/50. This means:

- **~35% of direction is word-level** — some words tend to fall regardless. Word-level predictors (norms at 7%, embeddings at 18-21%) are reaching into this third.
- **~12% is context-level** — the same word moves differently on different prompts. In-context ratings (scene) can reach this but carry no model information.
- **~53% is model-specific** — how this alignment pipeline treated this word on this prompt. "Kill" falls on OLMo and rises on Qwen for the same prompt. No word property can predict this; it's a property of the alignment training, not the vocabulary.

This explains why the existence test (Part 1) succeeds and scene-as-a-predictor fails: the existence test measures WITHIN-CELL slopes (one model, one prompt, relative ordering holds), while prediction asks across cells where model-specific variance dominates. See `named_under_dose/FINDINGS.md` §5 for the full analysis.

## What is not established

- **Whether this holds in Chinese.** charge.py ratings are now available for zh (407 prompts, same instrument), but the existence and adjacency tests have not been run on zh.
- **Whether the adjacency is semantic or categorical.** `kind` is a coarse tag (7 values). Two VIOLENT words may be semantically distant ("kill" and "arrest"). Embedding-based adjacency would be a finer test.
- **How much of the freed mass is displacement vs how much is suppression.** Both coexist in individual cells. The aggregate says displacement wins, but the partition is not measured.
- **What model property predicts the model-specific half.** Alignment method (SFT vs DPO), training data composition, and model scale are candidates. That's a different experiment.
