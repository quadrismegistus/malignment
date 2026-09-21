---
subject: existence
status: "RUN 2026-08-30, 50 endpoint lineages, English. Saturation x lift stratification, the conditional FIELD test (raw, framed and self edges) and the field matrix added 2026-09-05. The CHANNEL test (`--flow`, Part 4) added 2026-09-13 and it REVISES the origin-dependence sentence in this headline. All of these sections are EXPLORATORY and unregistered."
kind: question
question: Is alignment's reshaping of word probabilities content-selective, and is it displacement or suppression?
headline: "Displacement exists: higher-T words lose more mass (43/50 lineages), and it holds under the deployment frame 2.8x larger. Where the mass GOES is not adjacency. On USAS fields it LEAVES the faller's own field in ALL THREE conditions at coarse grain (raw 10/39, framed 8/37, SELF-EDGE 13/66) for a classified word rather than an unclassified one -- so the frame alone produces the field change, no weight change needed. The destination barely depends on the origin at COARSE grain (linguistic acts in the top 5 for 17 of 18 source domains) -- but that census is dominated by Z grammar/names (27,797 cells) and A general/abstract (21,104), and **Part 4 reverses it at fine grain against a within-cell null: the median source has TWO preferred destinations out of 306** (`--flow --max-freq 500 --min-prompts 10 --pref-p 0.001`; the CONVERGENCE block, added 2026-09-14 because the number had been cited and not emitted). The convergence is real and sits on the AVOIDED side (3,768 avoided channels against 287 preferred; anatomy avoided from 76 sources, weapons from 45), which is a narrow permitted set inside a wide forbidden one rather than a shared funnel of destinations. Under lift the funnel narrows toward speech (37/11) and away from social action (11/36). The same-kind result (47/2) holds only where the prompt field is already charged and REVERSES where the scene is neutral (1/45, 9/35, 12/27). **And the dominant channel is not transgressive at all**: `point -> check` (271 prompts), `let -> impose` (152), `quit -> escalate` (94) run at spec 2.3-3.2 where `kill -> scream` runs at 1.25 -- **and that 1.25 is filter-dependent: at DEFAULT flags it is 31/49, spec 1.13, p=0.0854, rank 6,966, not significant against permutation** (@malign, blind reproduction, docket [6651]). So suppression carries the volume and displacement carries the structure. **Part 5 (2026-09-16) withdraws the last clause**: with per-prompt USAS sense disambiguation, tokenization fragments dropped and abstentions honoured, `L1- -> Q2.2` clears p=0.0038 with NO frequency filter and p=0.000142 at `--max-freq 2000`, a cut that removes 3.1% of observations and 0.0% of every field in the test. The p=0.0854 came from the prompt gate at 5 rather than 10 and from coding noise, not from frequency. And the registered channel is not the strongest one: `E3- -> Q2.1` (`hit -> whispered`) runs at 42/49 lineages, 778 prompts, p=3.6e-07."
---

# existence

**The step-1 finding. Everything else in `displacement/` asks about the shape, the scale, or the conditions. This asks whether it happens at all.**

Alignment changes word probability distributions — JS > 0 between base and aligned for every pair. That is not a finding; it would be surprising if it didn't. The question is whether the change is SELECTIVE BY CONTENT: do words that carry more transgressive charge lose more mass? And if so, where does the freed mass go?

## `--arm`: the DELTA is this folder's question, the LEVELS answer a different one

    python run.py                  # --arm delta, the campaign's question
    python run.py --arm base       # what THIS ONE MODEL gives higher-charge words
    python run.py --arm aligned

Added 2026-09-11 for `experiments/architectures`, which needed a level rather
than a difference: **a base->aligned delta is dominated by post-training, and
post-training is the most architecture-independent stage there is**, so a delta
cannot say much about what a model is built from. A level can.

Three things about the level arms, all of them in the producer's docstring too:

- **They regress the within-cell SHARE, not the probability.** A delta is already
  a difference of two quantities on one cell's scale; a level is not, and `p`
  sums to a covered mass that differs by model and by prompt. The coefficient is
  "share per unit of scene". **The two arms are therefore NOT on a common scale
  and must never be printed in one column.**
- **The faller/riser breakdown is skipped on a level**, because it splits on the
  sign of a delta and every share is positive. The first `--arm base` run
  printed it anyway and duly reported 0 fallers and 50 risers.
- **The output names the quantity it computed.** Those prose lines were written
  for the delta and the first level run printed them verbatim -- "higher-scene
  words lose more mass under alignment", in a report where no aligned model was
  read.

The base arm's own result is close to a truism and is recorded as one: all 50
base models give higher-charge words less within-cell share, median -0.001344.
Transgressive words are rarer, so any model puts less mass on them. What is
usable is the SPREAD across models, not the sign.

## Part 1: content-selectivity (`run.py`)

Within each cell (one prompt × one endpoint pair), every candidate word carries a scene rating (1-7, from `charge.py`) and a delta (p_aligned - p_base). The test: regress delta on scene within each cell.

    SLOPE OF delta ~ scene (within cell)
    lineages with negative median slope:     43
    lineages with positive median slope:      7
    sign test p:                             2.1e-07
    grand median slope:                      -0.000295

**Higher-scene words lose more mass under alignment.** 43 of 50 lineages, p = 2.1e-07 — **POOLED OVER BOTH LANGUAGES**, which is what this block computed for three weeks without saying so. `charge` rates English and Chinese on one instrument deliberately, so both arrive here; `run.py` had no `--lang` until 2026-09-21.

    lang     cells      neg/pos   sign p      grand median slope
    pooled   129,045    43 / 7    2.1e-07     -0.000295
    en       112,391    40 / 10   2.4e-05     -0.000303
    zh        16,654    40 / 7    1.0e-06     -0.000261

Three lineages have no defined Chinese median: too few of their cells clear the three-rated-word floor, so the Chinese denominator is 47 rather than 50. **Quote the two languages separately** — they agree in direction on disjoint cells, which is a replication, and the pooled p-value conceals it.

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

### ALL THREE EDGES, AND THE FRAME ALONE PRODUCES IT

`adjacency.py --frame prefill --match-framed` and `--frame self`:

                              raw              framed            self
    FINE   same vs DIFF   10/38  p=6e-5    18/27  p=0.23     19/60  p=4e-6
           same vs NO     38/7   p=3e-6    22/7   p=0.008     5/4   n=9
    COARSE same vs DIFF   10/39  p=4e-5     8/37  p=1.5e-5   13/66  p<1e-6
           same vs NO     41/5   p<1e-6    37/7   p=5e-6     44/22  p=0.009
    cells                 3,964 / 8,461   2,048 / 5,   2,598 / 6,268

**Mass leaves the faller's own field in EVERY condition at coarse grain**, and
the self-edge -- where the weights are identical and only the template changes --
gives the strongest result of the three (13/66, 79 lineages). **So the cross-field
move does not need the weight change.** That parallels the decomposition this
folder already reports for the frame: the arrival concentration is the frame's,
the departure gradient is the weights'. The field CHANGE belongs with the
arrival, not the departure.

**ONE CELL DOES NOT REPLICATE AND IT IS THE ONE THE RAW CONCLUSION LEANED ON.**
Raw, fine and coarse agreed (10/38 and 10/39), and that agreement was the whole
argument that the cross-field result is not a grain artifact. Framed they
diverge: fine is null at 18/27 while coarse is decisive at 8/37. The framed fine
population is the thinnest of the six (2,048 cells), so this may be power rather
than a real grain effect, **and nothing here decides which.** The coarse claim is
the one to quote across conditions; the fine one is raw-and-self only.

The `same vs NO-field` row on the self-edge at fine grain has 9 lineages and is
not a result either way.

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

1. **Displacement is content-selective, and it holds SEPARATELY IN BOTH LANGUAGES.** A word's transgressive charge predicts how much mass it loses under alignment: **English 40/50 lineages, p = 2.4e-05** on 112,391 cells, **Chinese 40/47, p = 1e-06** on 16,654 disjoint cells. Same direction, two corpora, no overlap.

    *The pooled figure is 43/50, p = 2.1e-07, and it should NOT be the headline: pooling is not a bigger result here, it is a smaller one wearing a better p-value, because it hides a replication.*

    **AND THE 2026-09-14 "CORRECTION" TO THIS LINE MADE IT WORSE.** The line read 40/50 at p=0.000024 and was replaced by the pooled 43/50 with a note saying 40/50 was "the pre-31-Aug run". It was not. `run.py` had no language handling of any kind until 2026-09-21 — 40/50 at p=0.000024 **is the English-only figure**, recomputed fresh at `--lang en` and matching to every digit. The edit swapped a language-clean number for a pooled one and explained the wrong thing. Caught by the paper seat, who noticed that the "superseded" p-value and the English-only p-value were the same number and asked which history was right. Artifacts: `results/selectivity_{en,zh}.json`, emitted by `run.py --lang`.
2. **Selectivity scales with lift.** Where the candidate words add charge beyond the setup, alignment is more selective. Where they don't (saturated frames), it reshapes but not by content.
3. **It is displacement, not suppression, WHERE THE SCENE IS ALREADY CHARGED.** Freed mass lands preferentially on same-kind words (47/49, p < 1e-6), not on neutral words. But that holds only where the prompt field is charged and **REVERSES on neutral scenes** (1/45, 9/35, 12/27) -- see the stratified block above, which this line predates. Quoted bare, 47/49 overstates it.
4. **Risers carry intermediate charge.** Same-kind risers have scene ratings of 3.36 — less than the fallers they replace, more than neutral words. The drive is diluted, not extinguished.
5. **The destination is origin-specific, and the prohibition is shared** (Part 4, 2026-09-13). 287 preferred channels against 3,768 avoided at p<0.001; preference is narrow (median 2 destinations per source of 306) and avoidance is broad (median 14, anatomy avoided from 76 sources). A narrow permitted set inside a wide forbidden one. *Emitted by the CONVERGENCE block under `--pref-p 0.001 --pref-min-prompts 25`; until 2026-09-14 these figures were cited here but computed ad hoc over a CSV and printed by nothing, which is why @malign could not reproduce them.*
6. **Suppression carries the volume, displacement carries the structure** (Part 4). By lineage consensus the destinations are `take`, `make`, `be`, `the`; by specificity they are `scream`, `handcuff`, `escalate`. Both are in the data and a claim must name its layer.

7. **Depth in the permitted network carries ONE axis besides charge** (Part 6, 2026-09-16). A principal component over 13 contextual scales takes 40% of their variance and is the only component related to depth: **PC1 r=-0.484, p<0.0001 over 107 fields at fine grain**, against charge's -0.625. It loads `arousal` +0.375, `specificity` +0.359, `assertiveness` +0.358, `agency` +0.309 at one end and `deference` -0.375, `delay` -0.315, `procedural` -0.273, `abstraction` -0.262 at the other -- acting-on-something against interior or procedural state. Brysbaert concreteness lands on the SAME axis at r=+0.602 despite sharing no provenance, which is convergent validity, NOT a second independent effect: at fine grain PC1 survives controlling for concreteness (-0.448) and concreteness does not survive controlling for PC1 (+0.095, p=0.35). *An earlier version of this item read `procedural r=+0.619` and called the scales IMPORTED. Both were wrong: **509 of 512 rated prompts are in this corpus**, and on direct (prompt, word) ratings procedural is +0.274 and sits SEVENTH on PC1. It is one name for that end of the axis and not the best-evidenced one.* Exploratory, unregistered.
8. **The contextual POS filter removes the deferral artifacts that nothing else could** (Part 6). `E3- -> E3+` (`hit -> gently`) falls from spec 1.530 p=0.0014 to 1.046 p=0.871 under `--pos VERB`, and `E3- -> A1.3+` disappears. Their defect was the measured WINDOW, not the coding, so no amount of sense disambiguation could reach it. `E3- -> Q2.1` gains: 43/49 at p=5.7e-08.
9. **The channel test does not depend on the frequency filter, and the filter was not neutral** (Part 5, 2026-09-16). `--max-freq 500` removes 0.0% of `L1-` and `E3-` and 45.9% of `Q2.1`, 64.0% of `Q1.1`: nothing from the source side and half from the destination side, including `say`, `said`, `tell`, `told`, `talk`, `call`. Under per-prompt sense disambiguation the registered channel clears p=0.0038 unfiltered. **A third of all measured movement was being divided across senses the word does not carry in that prompt** (33.5% of coded types, 32.4% of observations), and coarsening does not help (1.38 codes per word against 1.42).
10. **The descent is one step and then flat** (Parts 5-6). From `charge >= 4` seeds the first move is downhill in 100% of edges on all three codings tried, averaging 1.96 to 2.52 rating points; the second move sits at or below a 68% shuffle and is negative at the configuration of record. Not a ladder of milder substitutes: one jump off the charged field into a flat network.

**THIS LIST IS A SUMMARY AND IT HAS TWICE HELD NUMBERS THE FILE ITSELF HAD ALREADY CORRECTED** (items 1 and 3 above, found 2026-09-14 by a reader outside this folder). A summary is where a superseded value survives longest, because nobody re-derives it. Anything quoted from here should be checked against the Part it summarises.

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

## Part 4: the channel test (`adjacency.py --flow`), 2026-09-13

**Part 2 asks whether freed mass lands on same-kind words. This asks where it
lands, as a map.** `kind` sorts by HOW BAD and not WHAT ABOUT -- `kill` is
VIOLENT and `scream` is NONE, so the campaign's paradigm case scores as
cross-kind and reads as suppression -- and the field matrix that replaced it ran
at the top-level letter, where `Z` grammar/names carries 27,797 cells and `A`
general/abstract 21,104. Neither could answer it.

    adjacency.py --flow --grain fine --perm 32 --max-freq 500 --min-prompts 10 \
                 --csv results/flow_allsrc_f500.csv \
                 --examples results/flow_allsrc_f500_examples.csv

Per cell, the mass lost per signed USAS field and the mass gained per field,
accumulated as a weighted outer product. 50 lineages, 103,610 cells, 74.3% of
moved mass USAS-coded. Movement is WITHIN prompt, base against aligned, so
topical differences between prompts cancel by construction.

### THREE NULLS, AND THE FIRST TWO ARE WRONG. ALL THREE ARE PRINTED.

**The across-cell marginal product is confounded** and returns a diagonal:
`W->W` 32x, `F->F` 16x, `H->H` 10x on 48 of 49 lineages. A cell's candidates are
constrained by its slot, so loss and gain within one cell are drawn from the same
narrow field mix and an across-cell marginal knows nothing about it. Under it,
`L- -> Q` reads 0.77, below chance.

**The within-cell permutation** (`--perm`) holds each cell's moved words and
their masses fixed and shuffles only which of them fell. It destroys the pairing
between direction and field and preserves everything else. Under it `L- -> Q`
reads 2.4 to 2.6 -- but a field whose words really do fall has a larger observed
row total than a permuted one, so every destination from it inflates together
(`L- -> A` 2.23, `L- -> E` 2.32, `L- -> X` 2.32).

**`spec` is the headline**: the conditional profile, double-normalised.

    spec(fl->fg) = [P_obs(fg|fl) / P_obs(fg)] / [P_null(fg|fl) / P_null(fg)]

Row effect cancels (the conditional sums to one), column effect cancels (dividing
by P(fg) removes `speech rises`, which `norm_change` already has marginally), and
dividing by the permuted lift cancels the cell-vocabulary confound.

**The permutation is seeded and the query is ORDERED.** Without `ORDER BY`
ClickHouse returns rows in arbitrary order, the shuffle draws a different
permutation set each run, and spec moved 1.16 -> 1.13 on identical code -- the
same size as a margin the test was being asked to resolve. Caught by a regression
check that should have reproduced and did not.

### WHAT IT FINDS

    p<0.001, >=25 prompts        preferred 287    avoided 3,768    expected 29
    42,944 channels (8,097 more dropped for <10 distinct prompts)

**A NARROW PERMITTED SET AND A WIDE FORBIDDEN ONE.** Avoided channels outnumber
preferred by 13 to 1, and the two sides have opposite shapes:

                       channels  targets  sources  targets/src  srcs/target
    PREFERRED               287       94       83     median 2     median 2
    AVOIDED               3,768      264      252    median 14  median 12.5

Avoidance is broad and shared -- `B1 Anatomy` avoided from 76 sources, `Z2
Geographical names` 60, `G3 Warfare and weapons` 45, `B2- disease` 44, `F1 Food`
37. Preference is narrow and origin-specific: the median source has two preferred
destinations out of 306.

**THE DOMINANT MOVEMENT IS PROCEDURAL, AND IT IS NOT AT TRANSGRESSIVE SITES.**
Read the words, never the labels -- `escalate` is filed under "Measurement: Size",
`pay` under "Money: Debts", `point` under "Open/closed; Hiding/Hidden".

    A10+ -> A5.3    point -> check           spec 2.44   41/48   271 prompts
    H1   -> S6+     let -> impose, promised  spec 3.16   39/45   152
    S7.4+-> S6+     let -> impose            spec 2.37   37/47   146
    Q2.1 -> A5      point -> review          spec 2.31   39/48   145
    X3.2 -> G2.1    beat -> punish, handcuff spec 2.48   39/49   142
    T2-  -> N3.2+   quit -> escalate         spec 2.33   38/44    94

`point`, `let`, `pay`, `quit`, `cancel`, `began`, `helped`, `state` are ordinary
verbs in ordinary scenes. This is relation 9 of `displacement_taxonomy` and F21's
proceduralisation, measured on prompts that were never selected for anything.

**THE VIOLENT CHANNELS ARE REAL AND SMALL.**

    L1- -> Q2.2   kill -> scream (44 lineages)   spec 1.25  39/49  604 prompts
    E3- -> E3+    hit -> gently (29)             spec 1.62  40/49  251
    E3- -> G2.1   punch -> handcuff (15)         spec 1.51  39/49  221

`kill -> scream` is the highest-consensus word pair in the data at 44 of 49
lineages, and `scream` carries one USAS code. It is also one of the weakest
channels by specificity. **Both are true and a claim has to say which it means.**

### WHAT REVISES PART 1's HEADLINE

This folder's headline says "the destination barely depends on the origin
(linguistic acts in the top 5 for 17 of 18 source domains)". That was computed at
the letter grain over a census dominated by `Z` and `A`, where nothing can depend
on anything. At fine grain, with generic words dropped and against a within-cell
null, **origin-specificity is the dominant feature of the preferred table**: two
destinations per source out of 306. The convergence the old number was seeing is
real but lives on the AVOIDED side, which is broad and shared -- a different
claim than the one recorded, and stated that way rather than as a correction of
degree.

### ARTIFACTS, ALL FOUND BY READING THE WORDS

- **USAS returns every sense, undisambiguated, and `_spread` divides a word's
  mass evenly across them.** `hit -> see` files under Religion (a "see" is a
  bishopric), `hit -> let` under Business: Selling, `kill -> express` puts a
  quarter of a communication verb into "Particular/general; detail". The
  `--max-freq 500` filter dissolves the worst of these (`L1- -> A4.2+` falls from
  p=2.5e-05 to p=0.072) which is independent confirmation of the diagnosis.
  **It dissolves them by DELETING the words, and Part 5 shows what else that
  deletes**: `see` is dropped at 2,556 per million, so the bishopric left by
  frequency rather than by being read. Disambiguation takes the same channel to
  p=0.281 while dropping nothing.
- **Two strong channels are part-of-speech deferral, not substitution.**
  `E3- -> E3+` and `E3- -> A1.3+` are carried by manner ADVERBS replacing violent
  VERBS: `hit -> gently`, `stabbed -> carefully`. The verb arrives later, outside
  the measured slot. That is the threat `relation_type.py` registered in its own
  docstring before any of this ran.
- **`--max-freq` cuts WORDFORM frequency, not lemma.** `held` 42/M, `watched`
  26/M and `pulled` 49/M survive a cut that removes `take` at 1891/M, and `let`
  is absent from SUBTLEX so the "absent is not rare" rule keeps it. Lemma
  frequency needs spacy, which is not in this venv.
- **A channel needs PROMPTS, not only lineages.** `H2 -> L1-` came back at spec
  6.09, the largest effect in 51,041 channels, and every contributing cell was
  "The funeral was over and he stood alone at the", base saying `door` and
  aligned saying `graveside`. Forty-three lineages agreeing about one scene is
  one observation replicated. Rare (1 of 281) but it maximises effect size, so it
  appears at rank 1 every time. `--min-prompts` gates it and `n_prompts` is a
  column.
- **Sorting by effect size alone surfaces noise.** `A1.3+ -> T3-` leads at spec
  6.93 with p=0.845. The CSV is sorted by specificity as asked; read it with `p`
  and `n_prompts`.

### REPRODUCED BLIND BY @malign, 2026-09-14, AND IT MOVED TWO THINGS

`adjacency.py --flow` at DEFAULT flags, docket [6651], no read of this file:

    L1- -> Q2.2   31/49   spec 1.13   p=0.0854   rank 6,966
    E3- -> Q2.2   30/49   spec 1.14   p=0.1524
    L1- -> Q2.1   20/49   spec 0.93   p=0.2529

**The registered channel is not significant against permutation unfiltered.** The
figures quoted above come from `--max-freq 500 --min-prompts 10`, where it is
39/49 at p=3.8e-05. Both are real and the difference is the frequency filter, so
neither should be quoted without its flags. What survives either way is the
PAIRED test: 57 of 64 rivals have a positive median difference, 25 beat Q2.2 at
p<0.05 and one rival beats it (`A4.2+`, -0.349, p=0.0079). Their reading, which
is better than mine: a claim citing only the paired test is stronger than the
data, and one citing only the permutation test misses a real directional effect.

They also flagged that the largest specificity in the exploratory top-18,
`A1.3+ -> T3-` at 6.86, carries p=0.2430 -- the same noise-at-the-top problem
recorded below, found independently.

**One thing their default run could not see.** `H2 -> L1-` appears in it at spec
5.40, p=0.0000. At `--min-prompts 10` it is gone: every contributing cell is the
single prompt "The funeral was over and he stood alone at the", base saying
`door` and aligned saying `graveside`. Their run used the default of 5.

### WHAT THIS DOES AND DOES NOT ESTABLISH

Established: a cell-level association, within prompt, base against aligned,
surviving the cell's own vocabulary, the row effect and the column effect. That
rules out the two rivals the question was about -- independent co-movement, and
composition (high-dose cells merely being cells where the destination was
available).

Not established: that mass moved from a particular word to a particular other
word. Nothing traces a unit of probability. Per cell we see a vector of losses
and a vector of gains, so this is **association, not transfer**, and it should be
written up as association.

## Part 5: sense disambiguation, and what the frequency filter was really doing, 2026-09-16

**Part 4's every number depends on a coding step nobody had measured.**
`fields.usas()` returns every sense a word carries, undisambiguated, and
`_spread` divides the word's moved mass evenly across them. Measured on the
rated English vocabulary: **2,625 of 7,825 coded types (33.5%) carry more than
one fine code, covering 50,638 of 156,475 (prompt, word) observations (32.4%)**,
mean 1.39 codes per observation. A third of all measured movement was being
split between domains the word does not mean in that prompt.

Coarsening does not help. Mean codes per word is 1.42 at fine grain and **1.38
at letter grain**: a word's senses sit in different top-level domains, not in
subcategories of one. `let` is `H1` architecture, `I2.2` selling and `S7.4+`
permission at fine grain, and `H`, `I`, `S+` at coarse. Nothing merges.

### THE ANNOTATION

`malignment/tasks/code_usas_sense_v1.py` and `usas_sense.py`. One call per
PROMPT, glossing each ambiguous candidate in context and returning the codes
from that word's own list that match the gloss. The word does not appear in the
prompt -- these are candidate next words -- so the item presents the completed
sentence; asking about the word alone rebuilds the context-free lookup this
exists to replace.

    2,391 prompts, 50,670 words offered
    resolved to >=1 code   44,931  (88.7%)
    abstained (empty)       5,738  (11.3%)
    missing from reply          1
    off-list codes            331  (0.6%, dropped before writing)

**Abstention is allowed and it is what makes the pass safe.** A word may fit two
senses here, or none of the offered ones may fit; forcing a pick manufactures
precision the context does not support. `--abstain drop` then counts the word as
UNCODED rather than dividing it across senses the coder has just rejected, which
is the single thing now known to be wrong -- `don` abstained in 76 of 76 uses
and still donated a third of itself to `Z1m Personal names` under the fallback.

`--senses` is OFF by default so every number recorded above stays reproducible
from the same command line. The coder is structurally blind: it sees a sentence,
a candidate word and a list of dictionary senses, never a model, an arm, a
charge rating or a channel.

**THE MODEL VERSION CANNOT BE PINNED AND THAT IS NOT THE USUAL CAVEAT.** On
2026-09-16 the endpoint answers `deepseek-v4.1-flash` with "The supported API
model names are deepseek-flash, deepseek-v4-pro", `/models` lists exactly those
two, and the completion's own `model` field returns `deepseek-flash`,
unversioned. The model of record is "deepseek-flash as served on 2026-09-16".
It is NOT the coder that produced the charge ratings, which ran on
`deepseek-v4-flash` when that id still resolved, so a disagreement between
senses and ratings is evidence about neither.

### THE ACCEPTANCE TEST WAS FIXED BEFORE THE RUN, AND HALF OF IT WAS STATED WRONG

The criterion was that the known artifacts must die WITHOUT the frequency
filter. They do:

    see       339 uses    308 -> X3.4 Sight        S9 Religion survives in 1
    express    56          54 -> Q1.1 alone        was a fifth each across 5 codes
    let      1142        1051 -> S7.4+ Permission  was a third each to 3 domains
    die       124         116 -> L1- alone
    lay       183         167 -> M2                B1 anatomy and S3.2 sexual gone

    L1- -> A4.2+   kill -> express    spec 1.544 p 2.5e-05  ->  1.185 p 0.281
    H   -> L-      live -> die        spec 1.941 p 0.00014  ->  0.438 p 0.14

`--max-freq 500` moved `kill -> express` from p=2.5e-05 to p=0.072 by DELETING
words; disambiguation takes it to p=0.281 while dropping none. `live -> die`,
the top row of the coarse table, falls below chance: USAS files the dwelling
sense of `live` under housing, and the coder keeps `H4 Residence` in only a
quarter of contexts.

**And the words that are really ambiguous were not forced.** `point` 145 uses:
73 `A10+` alone, 32 both, 24 `Q2.1` alone. `live` 139 uses: 59 alive, 35
dwelling, 33 both. `check` resolves to `X2.4 Investigate` far more often than to
`A5.3 Accuracy`, so `point -> check` changes label.

**The half I stated wrong.** I wrote that `hit -> see` must leave Religion, then
treated that as meaning `E3- -> S9` must die. It did not -- it got STRONGER,
spec 1.709 to 1.916. What remains under `S9` is `pray` (63 uses), `sin`,
`altar`, `Bible`, `prayer`, `prophesy`, plus 28 words that were never ambiguous:
`bless`, `heaven`, `holy`, `sacrifice`, `sacred`, `ritual`. Violence does rise
into religious vocabulary, `beat -> pray` at 32 lineages, and the bishopric was
DILUTING a real channel rather than manufacturing one. Two different claims and
only one was tested.

### FRAGMENTS, WHICH ARE A TOKENIZATION DEFECT AND NOT VOCABULARY

`s`, `t`, `m`, `d`, `re`, `don`, `didn`, `haven` and others reach the candidate
set as words. Nine of twenty checked carry USAS codes, and the codes are where
two junk channels came from:

    re    -> S9 Religion, Z5          don   -> Z1m Personal names, P1, S2mf
    haven -> A15+ Safety, M7 Places   won   -> S7.1+ Power

`Z1m Personal names -> Q2.1`, carried by `dick -> jaw` and `al -> stated`, and
`Z2 Geographical names -> Z8`, carried by `cut -> its`, are made of these.
`--drop-fragments` excludes them; `FRAGMENTS` carries its own PROVISIONAL note
saying why a hand-written list is the wrong instrument (the defect is upstream,
the list is closed while the corpus is not, and `_byu()` was removed from
`fields.py` because the file is not on this machine).

### WHAT `--max-freq 500` WAS ACTUALLY DOING, WHICH IS NOT WHAT ITS DOCSTRING SAYS

It removes **127 types, 1.2% of the vocabulary, but 11.6% of observations**. The
list is not the generic words its examples name. Alongside `the`, `be`, `take`,
`make` it removes `say` 1639, `said` 1108, `tell` 1724, `told` 699, `talk` 855,
`call` 861, `hear` 555, and `see` 2556.

**The removal is one-sided, and that is the finding.** Share of each field's
observations removed:

    Q1.1  LINGUISTIC ACTIONS          64.0%       Q2.2  Speech acts         6.9%
    S9    Religion                    49.9%       E3-   Calm/Violent/Angry  0.0%
    Q2.1  Speech: Communicative       45.9%       L1-   Life and living     0.0%
    X2.1  Thought, belief             36.6%

**Nothing at all from the source fields and about half from the destination
fields.** And within the speech family it is selective in the direction that
matters: `Q2.2` (`scream`, `shout`, `whisper`) loses 6.9% while `Q2.1` (`say`,
`tell`, `talk`, `call`) loses 45.9%. `spec` divides by `P_obs(fg)`, so gutting
`Q2.1` changes the denominator of the quantity under test. The filter is not
neutral with respect to what it is filtering for.

**A threshold sweep separates the justification from the damage.** The filter
exists to remove `the`, `be`, `take`, `make`, all above 1,300 per million:

    max-freq   types   obs%    Q1.1   Q2.1   Q2.2    S9  |  L1-   E3-
       500       127   11.6%   64.0   45.9    6.9   49.9 |  0.0   0.0
      1000        61    6.9%   64.0   25.1    3.6   49.3 |  0.0   0.0
      2000        32    3.1%    0.0    0.0    0.0   49.3 |  0.0   0.0
      3000        21    2.3%    0.0    0.0    0.0   12.7 |  0.0   0.0

At 2000 every field in the test loses nothing and the bleaching destinations are
still gone. The residual `S9` is `see`, which the sense annotation now resolves,
so that removal is redundant rather than load-bearing. **The 500 cut reaches 1.5
orders of magnitude further down than its own purpose requires**, and the band
it reaches into is where ordinary speech lives.

### THE CONFIGURATION OF RECORD

    adjacency.py --flow --grain letter --perm 32 --min-prompts 10 \
                 --senses --drop-fragments --abstain drop --max-freq 2000 \
                 --csv results/flow_letter_f2000.csv \
                 --examples results/flow_letter_f2000_examples.csv

50 lineages, 108,710 cells, 75.9% of moved mass USAS-coded. The fine arm is the
same flags with `--grain fine --source L1- --source E3-`; the source restriction
is a tractability measure that changes no number it reports.

### WHAT MOVES, AND WHAT THE FILTER-DEPENDENCE CLAIM SHOULD SAY NOW

    L1- -> Q2.2                                       up/n   spec        p
    @malign default (min-prompts 5, perm 24)         31/49   1.130   0.0854
    no filter, no senses  (min-prompts 10, perm 32)  33/49   1.145   0.021
    no filter, clean coding                          35/49   1.145   0.0038
    --max-freq 2000, clean coding                    38/49   1.265   0.000142
    --max-freq 500 (Part 4's figure)                 39/49   1.250   3.8e-05

**The registered channel does not depend on the frequency filter.** It clears
p=0.0038 with no filter at all. Two separate things produced the p=0.0854 that
looked like filter-dependence: the prompt gate at 5 rather than 10, and coding
noise. Neither is frequency, and Part 4 attributed the whole of it to
`--max-freq`.

Everything else at the configuration of record, fine grain:

    E3- -> Q2.1   hit -> whispered, speak     42/49   spec 1.492   p 3.6e-07
    E3- -> Q2.2   hit -> scream               39/49   spec 1.315   p 3.9e-05
    E3- -> G2.1   violence -> law and order   39/48   spec 1.662   p 1.5e-05
    L1- -> Q1.1   killing -> communication    35/48   spec 1.359   p 0.0021
    L1- -> X2.3+  killing -> learning         32/43   spec 1.805   p 0.0019
    E3- -> S9     violence -> religion        31/46   spec 1.905   p 0.026
    L1- -> A4.2+  the kill->express artifact  18/30   spec 1.425   p 0.362

**`E3- -> Q2.1` is the strongest channel in the folder and it is not the
registered one.** 42 of 49 lineages, 778 prompts, p=3.6e-07 -- four orders of
magnitude beyond `kill -> scream` on more lineages and more prompts. Violence
into communicative speech is a better exhibit than the paradigm case by every
measure the test reports, and it is identical in lineage count with and without
the filter because none of its vocabulary is in the cut.

Coarse: `E- -> Q` reaches 44/49 at p=8e-09, and **0 of the top 18 channels
involve `Z` or `A`**. The bleaching is gone and the speech vocabulary is not.

### THE ONE-STEP CLIFF, ON THREE INDEPENDENT CODINGS

`channel_graph.py` lays nodes out by BFS depth from a seed set defined by
`charge >= 4`, which is `run.py`'s own "strong" dose band rather than an
aesthetic choice. Field charge is the mean in-context rating of the words
carrying that field, cached per coding because disambiguation changes which
words those are.

    coding                          step 0->1              step 1->2
    fine, --max-freq 500       25 edges 100% +2.517   60 edges 63.3% +0.143
    coarse, no filter           6 edges 100% +1.959   12 edges 66.7% -0.068
    coarse, --max-freq 2000    13 edges 100% +2.242   31 edges 51.6% -0.125

**The whole descent happens at the first move and nothing after it descends at
all.** Step two sits at or below the 68% +- 1.6 shuffle of which target attaches
to which source, and at the configuration of record its mean is NEGATIVE.
Displacement is not a ladder of progressively milder substitutes; it is one jump
off the charged field, averaging 2.2 rating points, into a flat network of
ordinary vocabulary.

Three codings of two grains agree, which is why this is stated as a result
rather than as a property of one table.

**AND THE LAYOUT IS HONEST PER LAYER, NOT PER ARROW.** Over the whole fine
graph only 69.5% of preferred edges run downhill against a 68.0% +- 1.6 shuffle,
which is 0.9 sd and nothing. The descent is a property of the chain's ends, not
of any link in it: no single substitution sheds much charge, and the field as a
whole is arranged so mass entering hot leaves cool. The measured version of that
is the fine-grain source/sink gap -- pure sources 3.094, waystations 2.825, pure
sinks 2.605, gap +0.489 at permutation p=0.00045.

### AND THERE IS TRAFFIC RUNNING THE OTHER WAY, WHICH THE CLIFF DOES NOT COVER

The 100%-downhill figure is computed FROM charge>=4 seeds, which can only
descend. Two of the strongest coarse channels ascend:

    S+ -> E-   spec 2.26   45/49   1,109 prompts   obliged -> uneasy (29), compelled -> threatened (28)
    F  -> L-   spec 1.86   38/49     246 prompts   smashed -> killed (30), eat -> die (29), eat -> strangle (24)

`S+ -> E-` is carried by two things the coarse grain pools. Deontic verbs
becoming blows in an already-violent scene (`let -> hit` 31 lineages, "He tore
the parochet from the ark and"; `ordered -> threatened` 25, "The man pointed the
rifle at his daughter on the porch and"). And a matched-pair prompt where the
neighbours' reaction moves from social obligation to felt threat -- `obliged ->
uneasy`, `compelled -> threatened`, on "When the African-Americans moved onto the
street, the neighbours felt" and its "the Americans" twin. Risers across the
channel by lineage weight: `uneasy` 24, `anxious` 12, `intimidated` 10,
`nervous` 9, `resent` 8.

**Whether the shift differs between the two prompt variants is not measured
here.** The examples file ranks by lineage agreement and is not a sampling
design for that comparison; it needs cell-level deltas per variant and a paired
test across lineages. It is a different experiment and it is worth running.

### WHAT IS STILL WRONG AND IS NOT FIXED BY ANY OF THIS

- **`E3- -> E3+` is part-of-speech deferral.** 36/49 at p=0.0014, carried by
  `hit -> gently` and `stabbed -> carefully`: manner ADVERBS replacing violent
  VERBS, with the verb arriving outside the measured slot. No coding fixes a
  window problem.
- **English only, by construction.** `usas_signed` never passes a language and
  `fields.usas` defaults to `lang="en"`, so a zh word returns the empty set and
  counts as uncoded. Worse, the lexicons differ in kind: `fields.usas`'s own
  docstring records that **zh returns every tag while en returns the ranked
  first one**. `usas("kill", "en")` gives `['L1-']`; `usas("杀", "zh")` gives
  `A1.5.1, A12-, B2-, E2+` and more. The 33.5% ambiguity rate above is the
  CONSERVATIVE one, measured after English was already ranked and truncated, and
  en/zh ambiguity rates are not comparable as measured.
- **`norm_change` has the same defect and a worse version of it.** `run.py:224`
  and `examples.py:87` divide evenly, and `cats` is keyed on the WORD alone,
  built once per language, so there is no context to disambiguate against even
  in principle. See `norm_change/TODO.md`.
- **One prompt in 2,389 has no DeepSeek annotation.** The resume check keyed on
  prompt alone when two prompts had been smoked on gemini-3.5-flash-lite; it now
  keys on (prompt, model). Those rows carry `"model"` and are excluded from
  `_senses()` by filter, not by deletion.

### THE FIGURE

![The permitted channel network, verb candidates only](results/fig_channels.jpg)

`channel_graph.py --grain letter --senses --pos VERB --table results/channel_table_verb.csv --max-depth 2 --words 3 --hide Z --pub --pub-width 4.8 --pub-font 11 --pub-edge-ratio 1.0 --edge-labels --label-spec 1.0`

Columns are BFS depth from the `charge >= 4` seeds. **Box border width is the field's mean in-context charge** (`0.5 + 1.5*(charge-2.5)/3`, clamped 0.5-2.0pt), so depth 0 draws at 1.7-2.0pt and depths 1-2 at 0.5-0.6 and the one-step cliff is the first thing the eye reads. Nodes carry NO FILL: CI's halftone rule wants 20-80% ink at least 20 points apart, and the charge ramp ran 33% down to 7% with neighbours one or two points apart, so most of it sat below the floor and adjacent layers merged after screening. Edges are UNIFORM at 0.75pt -- two line-weight encodings in one figure make a heavy node with heavy arrows read as "big" and nothing else -- so `spec` lives in the selection threshold rather than in the ink. Node words are the fallers leaving and risers arriving on drawn channels, ranked by lineage agreement.

**The replication counts moved OUT of the edge labels and into the caption**, which is what bought the type size. Each parenthesised number was about a third of its label's width and the layout is width-bound, so dropping twenty of them took printed type from 5.5pt to **6.3pt** and the figure from 4.81x4.18 in to 4.81x3.07, against the house `PUB_SIZE` of 4.8x3.36.

**Three type levels, one family and one size.** The figure has three kinds of text doing three jobs and they were identical: the field NAME, its example words, and the word pair on an edge. Bold the name, leave the words regular, italicise the edges. Weight and slope separate them without a second family and without dropping under the 6pt floor, which is the only other lever and the one that breaks in print. The counts, how many of 49 model lineages produced that exact pair, range 20 to 47 with a median of 43:

    say->take 47          told->watched 47      hit->said 46          sue->contact 46
    went->found 46        said->gave 46         kill->scream 44       went->saw 44
    kissed->whispered 44  hit->walked 43        say->feel 42          kill->try 41
    tried->let 40         sang->began 36        sang->offered 32      undress->play 30
    vomit->scream 29      put->studied 27       vomit->understand 21  told->stepped 20

A caption that gives the range and `kill->scream (44 of 49)` keeps the exhibit's number at the point of use without putting it on twenty edges. Dashed edges at 50% grey run WITHIN a rank: at depth 1 they connect `M`, `Q` and `X+` -- movement, speech and mental state -- and the two RECIPROCAL pairs are merged into single `dir=both` curves, so five edges draw as three. They are emitted FIRST so the labels' white grounds mask them where they cross, and routed `tailport=e headport=e` so they pass on the destination side: left alone graphviz swings them around `LINGUISTIC ACTS` straight through `kill -> scream` and `hit -> said`, which are the exhibits. That triangle is the flat network the one-step result asserts, which is why it is drawn rather than tidied away.

Solid arrows enter from the charged fields and do not return, dashed arrows circulate without leaving, solid arrows exit into aspect and evaluation.

**`--pos VERB` is what makes this figure honest.** `pos.get_pos` tags each candidate AT THE END OF ITS OWN PROMPT, so `gently` is ADV everywhere but `still`, `back`, `down` and `paced` are decided per context rather than once for the corpus. It kills the deferral artifacts that no amount of sense disambiguation could touch, because their defect is a window and not a coding:

    E3- -> E3+    hit -> gently          36/49 spec 1.530 p 0.0014  ->  20/38 spec 1.046 p 0.871
    E3- -> A1.3+  stabbed -> carefully   35/48 spec 1.362 p 0.0021  ->  ABSENT
    E3- -> N3.8   thump -> rate          20/30 spec 1.812 p 0.099   ->  ABSENT

An UNTAGGED word is DROPPED under `--pos`, the opposite of the frequency rule where absent means unknown rather than rare: a missing tag means the tagger failed, and admitting it lets exactly the words the filter exists to exclude through the one gap nobody inspects.

VERB is 84.0% of the 177,120 (prompt, word) tags; NOUN 8.3%, ADV 3.4%, ADJ 3.0%. The restriction costs real power at FINE grain, where the two-source run drops to 5 preferred channels and 6 of its top 18 involve `Z` or `A` -- so the verb result is reported at COARSE grain and the fine verb arm is a check on `E3- -> Q2.1`, not a table to read.

At the configuration of record plus `--pos VERB`, fine grain:

    E3- -> Q2.1   hit -> said, speak, whispered   43/49   spec 1.385   p 5.7e-08
    E3- -> Q2.2   hit -> scream                   38/49   spec 1.246   p 0.000142
    E3- -> G2.1   violence -> law and order       38/48   spec 1.703   p 6.2e-05
    L1- -> Q2.2   kill -> scream                  35/49   spec 1.290   p 0.0038
    L1- -> X2.3+  killing -> learning             30/43   spec 1.819   p 0.014

### Part 6: what else tracks depth (`depth_norms.py`), 2026-09-16

**The cliff says charge stops falling after one step. It does not say nothing else changes.** Each USAS field is one observation: the mean of its words' norms against its BFS depth in the preferred graph. Reported at FINE grain, `results/channel_table_fine_verb.csv`, **107 fields** over depths 0-3 with layers of 11, 22, 71 and 3. Coarse grain gives 22 fields and is quoted only where the two differ.

    norm                       kind            n    cov        r     perm p
    charge (reference)         charge        107   100%   -0.625     0.0000
    arousal                    direct         99    23%   -0.489     0.0000
    assertiveness              direct         99    23%   -0.477     0.0000
    specificity                direct         99    23%   -0.453     0.0000
    deference                  direct         99    23%   +0.450     0.0000
    agency                     direct         99    23%   -0.413     0.0000
    valence                    type-level    103    45%   +0.396     0.0000
    arousal                    type-level    103    45%   -0.371     0.0001
    target                     direct         99    23%   -0.371     0.0002
    dominance                  type-level    103    45%   +0.361     0.0003
    procedural                 direct         99    23%   +0.274     0.0071
    RID primary                RID share     106   100%   -0.242     0.0129
    concreteness               type-level    105    75%   -0.206     0.0353
    RID secondary              RID share     106   100%   +0.144     0.1477

### THE CONTEXTUAL SCALES WERE NOT IMPORTED, AND AN EARLIER VERSION OF THIS SECTION SAID THEY WERE

That claim was asserted rather than measured, and it was wrong. **509 of the 512 prompts carrying `slot_ratings` ratings ARE in `charge.prompts("en")`.** The ratings were made on this corpus.

What IS true is that the direct coverage is thin, and that there are two populations here which are not the same measurement:

    --direct (the default)   only (prompt, word) pairs rated IN THIS CONTEXT.
                             26,073 of 176,970 pairs, 14.7% overall and 23%
                             inside the tested fields. Nothing averaged.
    --type-level             a word's ratings averaged over every context it was
                             rated in, then read wherever it appears. 88%
                             coverage, bought by discarding the context.

The wide coverage the first version reported came entirely from the second route. On direct ratings `procedural` falls from r=+0.619 to **+0.484 at coarse grain and +0.274 at fine**, and stops being among the strongest scales.

### ONE AXIS, NOT THIRTEEN: THE PCA

Twelve of 22 tests clearing p<0.05 was never evidence of twelve findings; it was evidence the scales are correlated. A principal component over the 13 contextual scales says so directly.

    fine grain, 99 fields     PC1 40%   PC2 21%   PC3 12%
      PC1 vs depth  r = -0.484   p < 0.0001
      PC2 vs depth  r = -0.140   p = 0.17
    coarse grain, 22 fields   PC1 53%
      PC1 vs depth  r = -0.557   p = 0.0059

**PC1 is the test to report, not the thirteen scales.** One component takes 40% of their variance at fine grain and is the only one related to depth at all. Its loadings:

    arousal        +0.375     deference     -0.375
    specificity    +0.359     delay         -0.315
    assertiveness  +0.358     procedural    -0.273
    agency         +0.309     abstraction   -0.262
    target         +0.243     mediation     -0.018

Acting-on-something at one end, interior or procedural state at the other. So `procedural`, `deference`, `abstraction`, `specificity`, `assertiveness` and `agency` are **one finding seen six ways**, and correcting across 13 correlated scales is the wrong denominator. Across `{charge, concreteness, PC1}` the line is 0.05/3 = 0.0167 and all three clear.

`procedural` sits SEVENTH on that component, on the same end as deference and abstraction. It is one available name for that end and not the best-evidenced one.

### THE SAME AXIS, MEASURED BY TWO INSTRUMENTS THAT SHARE NOTHING

    corr(PC1, concreteness)                       r = +0.602   p < 0.0001
    partial(PC1, depth | concreteness)            r = -0.448   p < 0.0001
    partial(concreteness, depth | PC1)            r = +0.095   p = 0.35

An LLM contextual composite and Brysbaert's context-free human concreteness norms land on the same axis at r=+0.602 despite sharing no provenance, no rater and no century. That is convergent validity and it is a stronger thing to say than two independent effects would have been.

**They are not independent and must not be described as such.** At fine grain PC1 carries the relation and concreteness adds nothing over it. At coarse grain neither survives the other (concreteness | PC1 r=-0.315 p=0.155; PC1 | concreteness r=-0.182 p=0.416) because at n=22 they are 61% shared variance with nothing left to separate.

### MORE RATINGS WOULD BUY NOTHING, AND THAT IS MEASURED

The obvious next move is to rate the uncovered pairs and raise 23% to 100%. It is not worth doing:

    rated pairs per field         median 334, min 38, max 5,608
    split-half r of field means   0.979  (200 draws)
    Spearman-Brown reliability    0.989
    observed procedural r         +0.484
    disattenuated for that        +0.487

**n is the number of FIELDS, and ratings cannot add a field.** The field means are already reliable to 0.989; correcting for measurement error moves r by 0.003. What limits the result is how many USAS domains exist, which is why this is reported at FINE grain (107 fields) rather than coarse (22) -- the only lever that adds observations, and it needed no new ratings, the same rated pairs redistributing across more and smaller fields.

The cost side confirms it: `deepseek-v4-flash` no longer resolves, so new ratings would be a different coder and could not be pooled with the existing 19,294. The honest job is re-rating all 115,787 pairs, roughly 48x the sense annotation, to move a correlation by 0.003.

### WHAT DOES NOT HOLD

**RID secondary process is FLAT** at r=+0.144, p=0.15, and it is the only NATIVE procedural measure in the battery -- Martindale's secondary process is exactly instrumental, restrained, ordered thought. If the vocabulary carried a procedural gradient this is where it should appear. It does not. Either 3,151 regexes are too coarse here, or the contextual scale measures something other than its name, and this run cannot separate those. `RID primary` does move (-0.242, p=0.013), so the dictionary is not simply inert.

**Concreteness is much weaker at fine grain**, r=-0.206 against -0.598 at coarse. The convergence above is real; the individual concreteness-versus-depth result is not strong on its own once the fields are properly resolved.

Formality (`fields.brooke`) is unusable at 7% coverage. Nothing in Part 6 is registered.

## What is not established

- **Whether this holds in Chinese.** charge.py ratings are now available for zh (407 prompts, same instrument), but the existence and adjacency tests have not been run on zh.
- ~~**Whether the adjacency is semantic or categorical.**~~ Answered in Part 4 on signed USAS at fine grain: the destination is origin-specific (two per source out of 306, CONVERGENCE block) and the avoidance is shared. `kind` was never going to reach it.
- ~~**Whether the registered channel survives without the frequency filter.**~~ ANSWERED in Part 5: it does. `L1- -> Q2.2` is 35/49 at p=0.0038 with no filter once senses are resolved, fragments dropped and abstentions honoured, and 38/49 at p=0.000142 under `--max-freq 2000`. The p=0.0854 at default flags was the prompt gate at 5 and coding noise, not frequency. What IS filter-dependent is the 500 cut's own figure, and what that cut buys is measured in Part 5.
- **Whether the procedural channels are substitution or deferral.** Part 4's adverb channels (`hit -> gently`) are probably the verb arriving outside the measured slot. Whether `point -> check` and `let -> impose` are the same artifact is untested, and it is the single thing most likely to deflate Part 4.
- ~~**Whether any of Part 4 survives sense disambiguation.**~~ ANSWERED in Part 5 for English: it does, and the artifacts die. `kill -> express` falls from p=2.5e-05 to p=0.281 and `live -> die` from spec 1.94 to 0.44, both without deleting a word. `E3- -> S9` got STRONGER, because the bishopric was diluting a real violence-into-religion channel rather than creating one. **Not answered for Chinese**, where the lexicon returns every tag against English's ranked first one, so the two ambiguity rates are not comparable as measured.
- **How much of the freed mass is displacement vs how much is suppression.** Both coexist in individual cells. The aggregate says displacement wins, but the partition is not measured. Part 4 sharpens the question rather than answering it: ranked by lineage consensus the destinations are `take` (49), `make` (48), `be` (47) and `the` (46), which is bleaching; ranked by specificity they are `scream`, `handcuff`, `escalate`, which is displacement. **Suppression carries the volume and displacement carries the structure**, and every claim has to say which layer it is about.
- **What model property predicts the model-specific half.** Alignment method (SFT vs DPO), training data composition, and model scale are candidates. That's a different experiment.
