---
subject: rate_and_magnitude
status: RUN 2026-08-24. 50 endpoint lineages, en and zh separately.
kind: question
question: How MUCH mass moves under alignment, how OFTEN, and does either scale with the frame?
headline: English moves more mass AND more words at transgressive prompts. Chinese moves MORE WORDS but LESS MASS.
---

# rate_and_magnitude

**Named for both quantities because the finding is that they come apart.**

M01 `F_G_rate_magnitude` separated them first and found:

    RATE       does alignment displace MORE OFTEN at transgressive sites?
               NULL -- n=33 pair-sites, p=0.148
    MAGNITUDE  does it displace HARDER?
               CONFIRMED -- d=0.748, p=6e-5

*"Alignment does not displace more often at transgressive sites; it displaces
harder."* `Q_bridge` names the magnitude quantity: `departed`, "how much mass
leaves words at all" — against `tail_excess` for DIRECTION, whether freed mass
"re-lands on nameable substitute words or disperses into the unresolved tail".

**This folder does not measure direction**, and nothing else in
`experiments/displacement/` measured plain magnitude: `displacement_axis` does
magnitude and direction along author-declared pole axes, `displacement_taxonomy`
asks what KIND of movement, `register_shift` asks about one scale.

## WHAT IS NEW: THE CONTINUOUS VERSION

M01 asked it as a BINARY contrast — a transgressive twin against its matched
neutral twin. This regresses three outcomes on a CONTINUOUS base-arm
transgressive level, per lineage, across prompts, unit = the lineage,
sign test over 50 endpoints from `roster.endpoints()`.

    lang  outcome          n   med slope    up/dn        p
    en    departed        50   +0.01107    41/ 9     6e-6
    en    arrived         50   +0.01092    36/14     0.003
    en    n_movers        50   +1.81360    44/ 6    <1e-6
    en    n_fallers       50   +0.77315    39/11     9e-5
    en    n_risers        50   +0.86678    44/ 6    <1e-6
    en    n_fall-n_rise   50   -0.12651    24/26     0.888   NULL
    en    mass/faller     50   -0.00000    25/25     1.000   NULL
    en    mass/riser      50   -0.00189    16/34     0.015
    en    tail_excess     50   -0.00875    12/38     3e-4
    zh    departed        47   -0.01010    10/37     1e-4
    zh    arrived         47   -0.01882     6/41    <1e-6
    zh    n_movers        47   +1.13203    31/16     0.040
    zh    n_fallers       47   -0.22221    20/27     0.382   NULL
    zh    n_risers        47   +1.21460    35/12     0.001
    zh    n_fall-n_rise   47   -1.06453    17/30     0.079
    zh    mass/faller     46   -0.00167     4/42    <1e-6
    zh    mass/riser      47   -0.00745     3/44    <1e-6
    zh    tail_excess     47   +0.01633    38/ 9     2.5e-5

`n_fallers` / `n_risers` are the RATE SPLIT BY DIRECTION. Not `tail_excess`,
which asks WHERE the freed mass lands; this asks whether the extra movement at a
loaded prompt is words LEAVING or words ARRIVING, and what each one carries.

## ENGLISH CONFIRMS M01'S MAGNITUDE AND BREAKS ITS RATE NULL

More mass departs where the base is more transgressive (+0.0111, 41 of 50
lineages). `departed` and `arrived` agree to three decimals (+0.01107 /
+0.01092) — mass conservation, and a check that the statistic behaves.

**But `n_movers` rises steeply too** (+1.81, 44 of 50, p<1e-6). At a
transgressive prompt MORE WORDS move as well as more mass. M01's rate null was
33 pair-sites as a binary twin contrast; this is a continuous slope over 50
lineages and thousands of prompts. **They are not the same test, so this is not
evidence against M01** — but the continuous version does not reproduce the null
and that is stated rather than smoothed.

## CHINESE INVERTS THE MASS AND KEEPS THE RATE

Less mass moves at transgressive prompts (-0.0101 departed, -0.0188 arrived)
while MORE WORDS move (+1.13). **That is a DISPERSAL: many small movements
instead of few large ones.**

It agrees with the asymmetry test in `norm_change`, where M01's "few large
fallers, many small risers" replicates marginally and INVERTS under dose. English
concentrates displacement at loaded prompts; Chinese spreads it.

**Reporting all three outcomes is what makes that legible.** A departed-only
reading would have called the Chinese result a smaller effect rather than a
differently-shaped one.



## SPLITTING THE RATE BY DIRECTION IS WHERE THE TWO LANGUAGES SEPARATE

**ENGLISH: the counts rise TOGETHER and the risers thin out.** `n_fallers`
+0.773 and `n_risers` +0.867 both rise steeply, and their DIFFERENCE is null
(-0.127, 24 up/26 dn, p=0.888) — symmetric. Meanwhile `mass/faller` is exactly
null (25/25, p=1.000) while `mass/riser` FALLS (-0.0019, p=0.015).

So at a transgressive English prompt: more words leave and more words arrive, in
step; **each departing word carries the same mass it always did, and each
arriving word carries less.** The extra mass is spread over more, smaller
risers.

**That is "few large fallers, many small risers" as a DOSE EFFECT.** M01 T §14
found the shape marginally; here the transgressive frame is what produces it —
fallers hold their size while risers multiply and thin.

**CHINESE: only the arrivals increase, and everything shrinks.** `n_fallers` is
null (-0.222, p=0.382) while `n_risers` rises (+1.215, p=0.001), and BOTH
per-word masses fall hard (`mass/faller` -0.0017 at 4 up/42 dn; `mass/riser`
-0.0075 at 3 up/44 dn, both p<1e-6).

So a loaded Chinese prompt does not recruit more departures at all. The same
words leave, each carrying less, and the mass they release is scattered across
more and much smaller arrivals. **Dispersal on both sides of the ledger.**

### WHY THIS IS THE INFORMATIVE CUT

`n_movers` alone said "more words move" in both languages and looked like a
shared effect. Split by direction it is not shared: English recruits departures
AND arrivals symmetrically; Chinese recruits only arrivals. The aggregate hid a
difference in kind.



## DIRECTION: `tail_excess`, AND THE SHARPENING QUESTION IT ANSWERS BY CONSTRUCTION

M01 `N_mass_migration` defines it: does freed mass "re-land on nameable words
above the resolution floor (substitution) or disperse into the unresolvable tail
(diffusion)?" **The comparison is against a proportional-renormalisation null**
— what the distribution would look like if the freed mass were simply spread
over the survivors in proportion to what they already held.

    tail_base   = 1 - sum(p_base)           the theta-censored remainder
    survivors   = 1 - faller_base           what the freed mass could land on
    expected    = tail_base * (1 + departed / survivors)
    tail_excess = tail_aligned - expected

**THAT NULL IS THE CONTROL FOR GENERAL SHARPENING, and it is why the null is a
null rather than a raw difference.** If alignment merely rescaled the
distribution, freed mass would reach every survivor -- the tail included -- in
proportion to its existing share. Subtracting that expectation leaves only the
part that is NOT rescaling. A raw `tail_aligned - tail_base` would confound the
two and is deliberately not computed here. The dose slope adds a second and
independent layer: whether the excess is specific to transgressive frames.

### THE LEVEL REPLICATES M01 IN BOTH LANGUAGES, UNANIMOUSLY

    MARGINAL tail_excess LEVEL   en  -0.170276   0 up/50 dn   p<1e-15
                                 zh  -0.133729   0 up/50 dn   p<1e-15

Negative everywhere, all 50 lineages in each language. That is `O_crosslingual`'s
**"the substitution travels"** — freed mass concentrates on nameable words
rather than dispersing, in English and Chinese alike.

### BUT THE DOSE SLOPE INVERTS BY LANGUAGE

    en  tail_excess  -0.00875   12 up/38 dn   p=3e-4
    zh  tail_excess  +0.01633   38 up/ 9 dn   p=2.5e-5

**English becomes MORE substitutional as the frame loads** — the more
transgressive the base, the further below the proportional null the tail sits.
**Chinese becomes LESS so**, moving toward diffusion.

**The sign of the slope is not the sign of the level.** Chinese remains
net-substitutional throughout (level -0.134); the slope says only that
transgressive frames push it toward the tail relative to neutral ones. Nothing
here shows Chinese crossing into net diffusion, and it should not be read that
way.

### THIS IS THE SAME SPLIT THE OTHER OUTCOMES SHOW

    ENGLISH under load   more mass moves, more words both ways, risers thin,
                         and the mass lands on NAMEABLE WORDS
    CHINESE under load   less mass moves, only arrivals recruit, everything
                         shrinks, and the mass goes to the TAIL

Both languages substitute. Under transgressive load English substitutes harder
and Chinese disperses. Every outcome in this folder tells that story, and
`tail_excess` is the one that says where the mass actually went.

## WHAT IS SHARED, AND NOT COPIED

The dose is the base-arm mass-weighted mean of `k_transgressiveness`, read from
`norm_change`'s `levels_long` — the same predictor, measured before alignment,
so it does not select on the outcome. The lineage roster is
`roster.endpoints()`: 50 pairs, NOT the 153 edges in `movement`, which include
rungs and transitive pairs and would let one base model vote eleven times.

## NOT CLAIMED

- **Direction beyond the tail split.** `tail_excess` says whether mass reached
  nameable words or the tail. It does NOT say WHICH nameable words -- that is
  `displacement_axis`'s and `norm_change`'s question.
- **That the Chinese inversion is understood.** It is measured, twice, on two
  outcomes that agree. Why a language would disperse where the other
  concentrates is not established here.
- **A rate/magnitude contradiction with M01.** Binary twin contrast against
  continuous slope, 33 pair-sites against 50 lineages. Different tests.

## THE DEPLOYMENT FRAME (2026-09-04): THE RATE STRUCTURE INVERTS

`run.py --rule-version 4 --frame prefill` against `--frame raw --match-framed`.
Same 45 pairs, English, lift dose. `base_raw -> aligned_framed`.

                       RAW/45                    FRAMED/45
    departed      +0.01538  35/10  p=2e-4   +0.01520  28/17  p=0.135   -> NULL
    arrived       +0.01123  35/10  p=2e-4   +0.03521  42/3   p<1e-6     3.1x
    n_movers      +2.43     42/3   p<1e-6   +1.79     35/10  p=2e-4     smaller
    n_fallers     +0.97     36/9   p=7e-5   +2.95     42/3   p<1e-6     3.1x
    n_risers      +0.88     41/4   p<1e-6   -1.25     10/35  p=2e-4     REVERSES
    n_fall-n_rise +0.06     23/22  p=1.000  +3.82     42/3   p<1e-6     null -> strong
    mass/faller   +0.00011  25/20  p=0.551  -0.00230  11/34  p=8e-4     null -> neg
    mass/riser    -0.00282  11/34  p=8e-4   +0.00310  33/12  p=2e-3     REVERSES
    tail_excess   -0.00918  11/34  p=8e-4   -0.03152   3/42  p<1e-6     3.4x

**THIS IS THE FIRST PLACE THE FRAME DOES SOMETHING OTHER THAN MAGNIFY.**
`existence` and both `norm_change` tables showed framed as raw pointing the same
way harder, 2x to 14x. Here the RATE structure inverts while the MAGNITUDE
structure amplifies.

### One mechanism, and the whole table is it

Under the frame, dose drives CONCENTRATION rather than dispersal:

  * more words give mass up (`n_fallers` 3.1x)
  * FEWER words receive it (`n_risers` reverses, 41/4 up becomes 10/35)
  * each receiver takes MORE (`mass/riser` reverses, negative becomes positive)
  * less leaks to the tail (`tail_excess` 3.4x, 3/42)

`n_fall-n_rise` states it most cleanly. Raw, a loaded prompt recruits fallers and
risers in equal measure -- an exact null at 23/22, p=1.000. Framed, it recruits
fallers and SHEDS risers, 42/3 at p<1e-6.

### What this does to RM-3, and to the summary this folder has been carrying

RM-3 -- freed mass lands on NAMEABLE words rather than the tail -- was unanimous
raw. Framed it strengthens 3.4x to 3/42. That was predicted from the
concentration reading before the row was read, which is the only reason it is
worth anything as corroboration.

**And "the frame amplifies alignment" is too coarse a summary and should stop
being used.** It amplifies departure and concentration; it REVERSES dispersal.
A folder quoting the amplification results without this one would be describing
a uniform effect that is not uniform.

### Fences

`--match-framed` is not optional: the framed set covers 45 of the 50 pairs, and
the reversal was checked against the matched raw column rather than the 50-pair
one, precisely because a sign flip is what a population difference would most
easily manufacture.

`frame_aligned='prefill'` alone is not the filter -- the population is
`movement.clean_frame_pairs()`, which reads what each template rendered into the
system slot rather than which argument was passed.

EXPLORATORY. Nothing in this section was registered.

## SELF-EDGES: the concentration is the FRAME's, the departure is the WEIGHTS'

`run.py --frame self --arm ...`. base == aligned, unframed against framed:
nothing changes but the template. `--arm` is required; 45 aligned and 8 base are
never pooled.

                     SELF aligned n=45         SELF base n=8
    n_fallers    +0.96  30/15  p=0.036     +1.28  6/2  p=0.289
    n_risers     -0.92  14/31  p=0.016     +0.06  4/4  p=1.000
    arrived      +0.022  34/11  p=8e-4     -0.003  3/5  p=0.727
    tail_excess  -0.017  10/35  p=2e-4     +0.001  4/4  p=1.000
    departed     +0.001  24/21  p=0.766    +0.005  4/4  p=1.000
    n_fall-n_rise +2.09  34/11  p=8e-4     +2.19  7/1  p=0.070   <- SEE BELOW

**The concentration mechanism does not need the weight change.** `n_risers`
reverses on the self-edge (14/31) exactly as it does in the full contrast, and
`tail_excess` strengthens at 10/35. The template alone, on weights nobody
touched during this measurement, already sheds risers under dose.

**And it splits the full result in two.** `departed` is NULL on the aligned
self-edge (24/21, p=0.766) while `arrived` is strong (34/11, p=8e-4). So in the
`base_raw -> aligned_framed` contrast:

    the DEPARTURE gradient comes from the weight change
    the ARRIVAL concentration comes from the frame

That is a cleaner decomposition than the full contrast can give, and it is the
reason to build self-edges at all.

### THE ONE ROW WHERE THE CONTROL IS EQUIVOCAL

`n_fall-n_rise` is +2.19 at 7/1 on the base arm, p=0.070 -- same direction and
similar magnitude to aligned's +2.09 at 34/11. It misses significance at n=8,
but **7/1 is what a real effect looks like with eight lineages**, and this is the
term the section above calls the cleanest statement of the mechanism.

So the balance term may NOT be alignment-specific even though its two components
are, and n=8 cannot settle it. Flagged rather than folded in: every other row of
the control is flat (4/4 on three of them), and this one is not, which is exactly
the row a clean story would want to overlook.

## THE LADDER: DPO RAISES THE LEVEL, IT DOES NOT CHANGE THE DOSE RESPONSE

`ladder.py`. The section above shows the frame alone sheds risers and
concentrates arrival on untouched weights. This asks where on the training
ladder that responsiveness gets installed, over four families with intermediate
checkpoints: Tulu-3 (plus its four SFT data ablations), OLMoE, OLMo-2, Olmo-3.

No intermediate rung has its own lift -- `charge.lifts_per_lineage()` is keyed by
(prompt, base) and covers exactly the 50 endpoint bases. Each rung is therefore
dosed with **its own family's base lift**, the model it descends from, which is
constant within a family and so cannot itself carry a stage difference.

### What is real: the marginal step, 4/4 and large

Paired within prompt, total movers under the frame, SFT -> DPO:

    Tulu-3    20.1 -> 30.5    +10.37   t=30.2
    OLMo-2    23.4 -> 30.4     +7.01   t=30.6
    Olmo-3    25.0 -> 29.0     +3.94   t=19.3
    OLMoE     24.5 -> 27.8     +3.29   t=15.5

**Preference training makes the model move far more words under a chat frame**,
in every family, and the Instruct rung sits on top of DPO rather than beyond it
(OLMo-2 30.4/30.4, Olmo-3 29.0/28.7), which is what a released post-DPO model
should do and is the cheapest available check that this is not noise.

### What is NOT there: a DPO step in dose sensitivity

The bare per-rung slopes need a control first. Total movers falls with lift in
**all sixteen rungs** (t = -2.0 to -5.8): loaded prompts have fewer movable words
to begin with. So a downward `n_fallers` or `n_risers` slope is mostly that
population effect, and only `fall - rise` is free of it. An earlier pass that
read those two columns separately was reading the population, not the rate.

Taken within prompt, where the dose is identical rather than merely matched:

    family      d ddiff    t    which channel
    Tulu-3       -1.166  -2.6   risers  (+0.678, t=2.2); fallers null
    OLMo-2       -0.634  -1.9   fallers (-0.665, t=-2.6); risers null
    OLMoE        -0.275  -1.0   neither
    Olmo-3       +0.628  +1.8   risers  (-0.848, t=-3.6), OPPOSITE SIGN

Signs disagree, and where they agree the channel does not: Tulu moves through
risers, OLMo-2 through fallers, Olmo-3 through risers the other way. Three
families, three mechanisms. **The stage claim has n=4, not n~780** -- the
prompts are the replicate within a family, the families are the replicate for
anything said about SFT versus DPO.

### The consequence for the section above

The reversal this folder reports -- `n_risers` inverting under the frame -- is
already at SFT and preference training leaves its dose structure alone. It is
**not a DPO phenomenon.** DPO changes how much moves, not how movement answers
to the prompt's charge, and those are separable quantities that a marginal
measurement silently pools.

One row worth keeping visible rather than folding in: Tulu `SFT-no-wildchat` is
+0.134 (t=0.4) where the other four SFT ablations sit at +0.62 to +0.82. One
ablation in a noisy column, so nothing is claimed from it, but it is the only
place in the ladder where an SFT data ablation looks unlike its siblings.

EXPLORATORY. Nothing in this section was registered.

## WHICH SFT DATA: WILDCHAT MAKES THE FRAME EFFECT SMALLER AND SHARPER

`ablation.py`. Tulu-3 ships four leave-one-out SFT checkpoints beside the
full-mix one: same base, same recipe, one training source removed. Paired within
prompt over the same 840 prompts, `full mix MINUS the ablated checkpoint`.

    removed       d frame      t   d control      t    d dose      t    d mass      t
    no-math        -0.183   -1.2      -1.752  -13.6    -0.195   -1.1   -0.0042   -3.2
    no-persona     -0.501   -3.2      -1.711  -13.3    -0.113   -0.6   -0.0082   -6.4
    no-safety       0.240    1.4      -1.427  -11.8    -0.038   -0.2    0.0019    1.3
    no-wildchat     1.396    6.8      -0.842   -4.9    -0.684   -2.8    0.0136    7.6

`frame` is self-edge movers; `control` is the same checkpoint's movers against
its base with NO frame on either side; `dose` is the fall-rise lift slope;
`mass` is threshold-free total variation.

**The control is what makes this an experiment.** Every ablation LOWERS it, t
-4.9 to -13.6: remove training data, the checkpoint moves less off its base.
That is a uniform downward pressure with nothing to do with frames, and it is
the null every column has to be read against.

**Only WildChat splits the two columns.** Its removal drops the control like
everyone else's and RAISES frame responsiveness (+1.40, t=6.8) -- the sole
ablation whose frame column moves opposite its control. It is also the only one
whose dose slope clearly falls (-0.684, t=-2.8; the other three are -0.04 to
-0.20, all null).

So WildChat, which is real logged user-assistant conversation, does not install
responsiveness to the frame. **It installs the DISCRIMINATION in it.** Trained on
it, the model revises less under the scene of address and the revision tracks how
charged the site is. Trained without it, the model revises MORE and the revision
stops tracking charge: bigger and blunter.

### The threshold artifact is closed

`n_tot` counts words over theta=0.001, fixed and identical across all five
checkpoints, so a flatter checkpoint piles words near the threshold and inflates
every count for no frame-related reason. Mass (sum|delta|/2 over ALL candidate
words, `still` included) reproduces the ordering exactly, no-wildchat largest at
+0.0136 (t=7.6), a 6.4% rise in displaced total variation. Candidate-set sizes
are 156.1-157.0 across the five, so it is not a wider field either.

### PRIOR ART: WILDCHAT WAS ALREADY THE ODD ARM, AND THE READING ABOVE IS CONTESTED

**This is not the first time WildChat has been singled out, and the section as
first written did not say so.** `malign-logits`
`meta/M01_displacement/findings/U_ladder.md` ran the same five checkpoints in
August on DISPLACEMENT, and `findings/DISPLACEMENT_EVIDENCE.md` §197 states the
result: faller Jaccard against full is `no-safety` 0.534, `no-math` 0.528,
`no-persona` 0.522, **`no-wildchat` 0.340** -- and no-wildchat against each of
the other three is 0.294-0.303 where they sit at 0.486-0.563 with each other.
Two groups, no overlap. Its summary is **"magnitude normal, direction
different."** The frame result here is a different quantity on a different edge,
and it CONVERGES on the same arm. That is corroboration, and it should be quoted
as the second observation of a known singularity, not the first of a new one.
**What is new here is the frame edge and the lift-based dose column**, neither of
which the August work had.

**Three things the prior work already settled**, which this section re-derived
and should have cited:

- **Volume is refuted, with counts.** Safety removes 110,983 and WildChat
  100,000 -- an 11% difference at the two extremes -- while the two removals
  three times larger (persona 284,919, math 334,252) change the operation least.
- **`math` and `persona` OVERLAP.** 334,252 for math includes the three
  personahub math sources (149,960 + 49,980 + 20,000). So `no-math` and
  `no-persona` are not disjoint cuts, and the ambiguity flagged here is
  answered rather than open.
- **The slice definitions are sourced**: Tulu 3, arXiv 2411.15124 §4.1/4.3,
  Tables 7 and 10.

### §197 TESTED THE SAME READING AND ITS NULL IS THE WEAKER INSTRUMENT

§197 anticipated the "WildChat is real user prompts, so this is the operation
depending on logged human wanting" reading and split `no-wildchat`'s divergence
by domain: **flat** -- neutral 0.3656 against transgressive 0.3235, a gap of
-0.042 mid-range of the other arms' -0.038 to -0.059. Its verdict: *"a generally
unusual training run, not one that differs where desire is at stake."*

**That null rests on a binary neutral-vs-transgressive prompt contrast, which is
a `dose`-level split, and `dose` is documented in this repo as the wrong
selector** (`malignment/charge.py`, "THE RESPONSE SATURATES, WHICH MAKES `dose`
THE WRONG SELECTOR"). Frames rated 5-7 carry the highest dose and show
essentially zero response, so a "transgressive" arm selects INTO the flat region:
`corr(effect, dose) = -0.091` against `corr(effect, lift) = -0.261`, and -0.311
inside the unsaturated range. `readout_share` §208 has the mechanism -- headroom
runs +0.38 at frame 2-3 down to **-0.05** at frame 6-7, so the most charged
prompts have nowhere to displace to, and effect peaks at frames 2-4 while dose
climbs monotonically.

**A flat gap across that split is what saturation predicts whether or not
content-discrimination exists.** So §197's null does not override the `d dose`
column here (-0.684, t=-2.8), which is built on LIFT, the instrument that
predicts three times better. The two are not symmetric evidence and the earlier
version of this section, which treated §197 as decisive and marked the reading
contested, over-deflated a result measured with the better instrument.

WHAT REMAINS GENUINELY OPEN. §197 and this section measure different outcomes on
different edges, so neither settles the other by itself. The check worth running
is not §197's split repeated -- it inherits the saturation defect -- but its
outcome (faller Jaccard divergence from full) recomputed against LIFT, on the
raw edge, where a real content-specificity would show up in the quantity §197
already found flat.

### What this cannot be

**One family, one ablation set, no replication available** -- also established
prior, not here. U_ladder searched HuggingFace, arXiv and lab post-training docs
and found no second suite meeting the bar, confirmed these five are the complete
Tulu set (`-no-code-data`, `-no-if-data`, `-no-science-data` were probed for and
do not exist), and recorded the status change from PENDING to **UNAVAILABLE**:
the instrument does not exist in the open-weight ecosystem. Nearest miss is
Meta's MobileLLM-Pro, which ran seven-domain leave-one-out ablations and released
none of the ablated checkpoints.

The 840 prompts give power WITHIN the comparison and no generality beyond it.

This was also predicted in the wrong direction before it ran -- the guess was
that removing user-chat data would LOWER frame responsiveness. It raises it. The
prediction being inverted is recorded because a result that had confirmed the
guess would have been checked less hard than this one was.

EXPLORATORY. Nothing in this section was registered.
