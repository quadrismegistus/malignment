# What leaves, leaves early; what arrives, arrives late — regardless of content

**id:** emergence/tuning_order **status:** RUN 2026-09-06 against `REGISTRATION.md` frozen the same day at `6c238ff` (amended §5a). Producers `analyse.py`, `explore_q3.py`, `f04_spirit.py`, `curves_fk.py`, `timing.py`, `q2.py`; outputs under `results/`. **All three registered arms run.**

## THE RESULT

Over **15,529 word-instances** on 507 prompts, every faller and every riser, timed by the centre of mass of their per-step movement:

    faller  t_move median 15,126 steps
    riser   t_move median 19,796 steps

    per-prompt lag   median +5,341 steps   506 of 507 prompts   p < 1e-6
                     CI [+5,198, +5,462]

**506 of 507.** F04's core temporal claim — departure precedes arrival — holds, on far better evidence than F04 had: 43 rungs against 10, all words against three hand-picked pairs, and the confounds tested rather than assumed.

### It is not an artefact of the faller/riser asymmetry

Fallers are bounded below by zero and start with higher mass by construction (`CANONICAL` needs `min_prob=0.003` in the base arm; a riser can start near nothing). Either could produce this mechanically. Neither does:

    CONTROL 1  timing against starting mass
      faller  start>=0.02 t=14,916 | start<0.005 t=15,234    flat
      riser   start>=0.02 t=19,173 | start<0.005 t=19,993    flat

    CONTROL 2  fallers that NEVER reach the floor (final >= 0.005)
      n=1,241  t=15,817  against risers 19,796               gap persists

    CONTROL 3  matched on total variation, deciles 2-10
      +5,102 +4,211 +4,836 +4,890 +4,997 +4,720 +4,240 +4,309 +4,099
      matched median +4,778 steps

Not the floor, not starting mass, not magnitude.

## AND IT IS NOT ABOUT TRANSGRESSION

    by the faller's kind        NONE +4,865 | SEXUAL +5,651 | VIOLENT +5,687
                                COERCIVE +5,799 | ILLICIT +5,265 | OTHER +5,495

    by the faller's lift        word-level spearman +0.0384, n=1,957, z=1.7
                                lift<=0 lead +5,118 | lift>=2 lead +6,114

**The same phenomenon at every charge level and every kind.** Charge adds perhaps a thousand steps at rho=0.038 — reported as **no established modulation**, not as a weak effect.

So the commission's hoped-for reading does not survive. It wanted the ordering to BE the temporal signature of repression: a charged word barred, a substitute arriving later. What is here is that **SFT reorganises its distribution in two phases regardless of content** — what leaves, leaves early; what arrives, arrives late. Transgression rides on a general mechanism rather than having one of its own.

That is a stronger claim than the commission asked for, and a different one.

## ALL THREE REGISTERED ARMS ARE NOW RUN, AND TWO OF THEM ARE NULLS

    Q1  does the faller move before the riser          HOLDS (weak instrument;
                                                       the timing arm supersedes)
    Q2  prompt-level lift as a moderator               NULL, tightly bounded
    Q3  the faller's own charge as a moderator         NULL

**Q2, and it is a bound rather than an absence of evidence:**

    prompt-level charge.lift vs the TIMING lag
      n=469   spearman rho +0.0001   p=0.998
      low-lift tercile   +5,341 steps
      high-lift tercile  +5,356 steps        difference 15 steps

    the same on the declared AUC lag
      n=467   spearman rho +0.0430   p=0.354

**15 steps on a 5,341-step effect is 0.3%.** At n=469 that constrains any
prompt-level charge modulation to under about 1% of the phenomenon's size. Quote
it as that fraction, never as "p=0.998".

**Q3, stated the same way**, and correcting a shorthand that misled: the
word-level figure is `rho = +0.0384` — an EFFECT SIZE near zero — and its
significance is separately `p = 0.090`. Both fail, independently. An earlier
version of this file wrote "rho=0.038" in a position where it read as a p-value.

So charge does not modulate the ordering at either grain: not the prompt's
overall lift, not the faller word's own increment.

## WHY CHARGE DOES NOT MODULATE: THE FALLERS ARE NOT MORE CHARGED THAN THE RISERS

RH, 2026-09-06: *"can we look at examples of NONE and SEXUAL falling and rising
at the same times to make sense of the transgressiveness null."* The examples
explain it, and the explanation undercuts the framing rather than qualifying it.

**Matched on timing, a charged and an uncharged faller are the same event:**

    SEXUAL  fuck   "He was beautiful and ugly and she wanted to"   0.0114 -> 0 @2000
    NONE    plead  "She was guilty and she began to"               0.0149 -> 0 @2000

`plead` is not transgressive. It is MARKED — low-frequency, literary — and it
collapses exactly as `fuck` does, with both prompts' risers being generic
cognitive verbs (`think`/`realize`/`explain`, `see`/`understand`). The operation
looks like marked vocabulary out, generic vocabulary in, with transgression one
case of markedness rather than a category of its own.

**And on explicitly sexual prompts the movement is often WITHIN the sexual
field, not out of it.**

**CORRECTED 2026-09-06, and the correction reverses the reading.** An earlier
version of this section quoted two rows — `manhood` falling, `shaft` rising —
and concluded the movement went "toward the blunter word". **It goes the other
way.** Read from two rows rather than the full cell; RH asked for the whole
prompt and the whole prompt says the opposite. The complete set, base ->
Think-SFT in `movement` (v3):

    FALLERS                             RISERS
    dick       0.0855 -> 0.0020  -98%   member    0.0098 -> 0.0229  +134%
    penis      0.0628 -> 0.0035  -94%   erect     0.0064 -> 0.0208  +225%
    big        0.0278 -> 0.0082         shaft     0.0141 -> 0.0207
    prick      0.0228 -> 0.0083         hard      0.0199 -> 0.0307
    balls      0.0155 -> 0.0067         rigid     0.0013 -> 0.0070
    manhood    0.0121 -> 0.0057         erected   0.0000 -> 0.0049
    throbbing  0.0111 -> 0.0050         male      0.0000 -> 0.0038
    long       0.0082 -> 0.0024
    massive    0.0046 -> 0.0000
    swollen    0.0044 -> 0.0000

**The DIRECT names fall** — `dick`, `prick`, `balls`, and the clinical `penis`
too — **and the PERIPHRASTIC ones rise**, `member` and `shaft`. That is
`cock -> penis` register shift, the campaign's own documented pattern, and the
opposite of what the two-row reading said.

A second axis was missed entirely, and it is cleaner than the first:

    falling adjectives  big, long, massive, swollen, throbbing   size / tumescence
    rising adjectives   hard, erect, erected, rigid              rigidity, clinical state

So the movement is naming-the-organ -> describing-its-state, and sensory
description -> clinical description.

    "She slowly took off her"
      F top      0.0246 -> 0.0013
      R scarf / socks / silk             other garments

**Measured over the whole panel, the assumption the question rests on is false:**

    per prompt, mean lift of fallers against risers    n=412
      faller median +0.000    riser median +0.000    DIFFERENCE +0.000

    prompts WITH a sexual faller                      n=38
      faller +1.000  riser +0.354  DIFF +0.360  27/11  p=0.014
      and 25 of the 38 (66%) ALSO HAVE A SEXUAL RISER

**Fallers are not, in general, more charged than risers.** So Q2 and Q3 were not
underpowered: they asked whether a property that does not differ between the two
classes predicts the gap between them. A null was the only available answer.

This bounds what the whole question can claim. **"Displacement" presumes a charged
word leaving and a less charged one arriving.** On this panel that holds only on
the sexual subset, weakly (+0.36 of a 1-7 scale), and even there two-thirds of
prompts have a sexual riser. The timing result is real and large; calling it
displacement is a separate claim that this panel does not support.

## THE AXIS: WHICH FALLERS LEAVE FIRST — AND WHY THE EARLIER NULLS WERE INSTRUMENT-BOUND

RH, 2026-09-06: *"specific bodily vocabulary falling to abstract proceduralised
psychologised vocabulary is what we've discovered of alignment generally across
lineages — so here we're rediscovering it within SFT checkpoint time."*

**This is a different quantity from Q2/Q3 and does not overturn them.** Those
asked whether charge predicts the LAG BETWEEN fallers and risers. This asks, among
FALLERS, which leave first — a graded ordering within one class. Producer
`axis.py`; negative rho means the higher the scale, the EARLIER the word leaves.

    TYPE-LEVEL (fields.norms)          v6 CONTEXTUAL              INSTITUTIONAL v3
    k_charge            -0.122 *       v6_fit          -0.102 *   assertiveness -0.081 *
    warriner_valence    +0.108 *       v6_makes_worse  -0.081 *   arousal       -0.079 *
    warriner_arousal    -0.093 *       v6_directedness -0.074 *   target        -0.073 *
    k_transgressiveness -0.078 *       v6_vocalisation -0.053 *   specificity   -0.070 *
    brysbaert_concrete  -0.062 *       v6_aggression   -0.053 *   agency        -0.055 *
    k_bodily_harm       -0.054 *       v6_mundanity    +0.051 *   vocalisation  -0.051 *
    k_vulgarity         -0.033 *       v6_harm         -0.034 *
      n = 4,462-8,478                    n = 5,003                  n = 3,847

**Charged, aggressive, concrete, harmful, apt, specific words leave EARLY.
Mundane, abstract, positive words leave LATE.** Read across the three, never
down one: no single |rho| exceeds 0.16, and the evidence is that instruments
sharing no machinery name one axis.

Nulls worth keeping: `v6_superego` (-0.013), `v6_interiority` (+0.011) and
`v6_deliberation` (-0.002) do NOT order the fallers, so this is not a general
"psychological words behave differently" effect.

### AND THIS EXPLAINS THE Q2/Q3 NULLS AS AN INSTRUMENT BOUND

Type-level `k_charge` orders faller timing at **-0.122**. `charge.py`'s
contextual `scene`/`lift` — the registered instrument — gives **+0.038**, on the
same words. The difference is a ceiling, and it is exact:

    "She knelt down in front of him and began to suck his"   frame = 7 (max)

    word      euphemism  explicitness  genitality        movement
    dick          1           7            7         0.0855 -> 0.0020
    cock          1           7            7         0.4321 -> 0.5100
    shaft         5           7            7         0.0141 -> 0.0207
    member        6           7            7         0.0098 -> 0.0229

`scene` rates the completed act, so on a frame-7 prompt **every** candidate
scores 7 and `lift = scene - frame` is exactly 0 for all of them. The instrument
sees `dick` and `shaft` as identical while the model treats them as opposites.
Measured corpus-wide: at frame=7, 100% of words have lift 0 (9 prompts, 117
words); the effect is total there and narrow overall.

**Only `sexual_v2_euphemism` discriminates**, and it runs with the movement —
direct terms (1-2) fall, periphrastic (5-6) rise. `explicitness` and
`genitality` are pinned at 7 exactly as `scene` is.

So Q2 and Q3 are not evidence that charge is irrelevant to SFT timing. They are
evidence that the registered instrument is saturated on the prompts where charge
varies most. **The bound is on the instrument, not on the world**, and it is why
this section uses type-level and v6 scales instead.

### WHAT IS TRIVIAL HERE AND WHAT IS NOT

**Trivial:** that words falling across lineage endpoints also fall on this
ladder. The ladder IS base->aligned decomposed into 43 steps, so the trajectory
necessarily lies along the endpoint displacement. An earlier draft of this
section tested M03's `say -> consider` and `pushed -> whispered` pairs and
reported their ordering as a recapitulation; that was circular. `say` is a faller
here (42 of 48) and `consider` a riser (62 of 63), so their +2,235-step gap is
the general faller-before-riser effect and nothing more. Restricted to prompts
where both are the SAME class it is n=3 and reverses.

**Not trivial:** that the axis orders the fallers among THEMSELVES in time. That
is not entailed by the endpoint difference, and it is what the table above
measures.

## DISCOVERED: A ONE-TIME EXCURSION AT THE FIRST TRANSITION

**This claim has shrunk twice under testing and the history is kept, because the
first version is what a reader would otherwise cite.**

    v1  "149 of 505 fallers (29.5%) move UP at step 1000 before falling"
        -- no null, no localisation. OVERSTATED.
    v2  the rate is barely asymmetric; the MAGNITUDE is
    v3  and it happens at ONE transition and never recurs

### The null it did not have: risers do it too

    moves the WRONG way at step 1000
      fallers rising first    149 of 505 = 29.5%
      risers dipping first    114 of 504 = 22.6%
      rate asymmetry 6.9pp    z=2.49  p=0.013

**So 29.5% is mostly baseline volatility.** A word's mass wobbles; nearly a
quarter of risers dip before rising. The rate difference is real but modest.

### What IS asymmetric is the SIZE of the excursion

Excursion measured as `|d(1000)| / |total movement|`:

    fallers median 0.158  p90 0.507
    risers  median 0.052  p90 0.369

    paired within prompt (faller excursion - riser excursion)
      n=504  median +0.1211  376 up/128 dn   p<1e-6
      restricted to prompts where BOTH go wrong way
      n=42   median +0.1214   32 up/10 dn    p=0.00094

**When a faller goes the wrong way it goes about three times further**, and that
survives conditioning on both words misbehaving — so it is not the rate
difference in disguise.

### And it happens ONCE, at the only transition that crosses a regime boundary

Wrong-way share at each rung transition, increments >= 0.001:

    transition        fallers   risers
    base -> 1000       28.7%     20.3%    <- the only asymmetric one
    1000 -> 2000       24.2%     23.7%
    2000 -> 3000       32.2%     34.1%    risers higher
    4000 -> 5000       37.9%     41.0%    risers higher
    6000 -> 7000       37.3%     46.8%    risers higher
    20000 -> 21000     52.2%     50.3%

**Never recurs.** At every later transition the two classes misbehave equally
and often risers more. The rising baseline (24% -> ~50%) is increasing noise as
late-training movements shrink.

So the claim is: **the first 1,000 steps of SFT move a substantial share of
eventual fallers in the wrong direction, at ~3x the riser baseline, once.**

### THE TEST THAT COULD STILL KILL IT, AND WHY THE OBVIOUS VERSION IS WRONG

`base -> 1000` is the only transition crossing from a pretrained model into a
fine-tuned one, so the excursion may be about **regime change** rather than about
fine-tuning.

The obvious control -- run the same on the pretraining ladder's first rung --
does not work. RH, 2026-09-06: *"the first rung of pretraining is still learning
how to speak."* At `stage1-step1000` the model barely has syntax (M05 puts syntax
at 128-256, reasoning at 3000, discourse at 80000), so it is not comparable to
fine-tuning a fluent model.

**The control that does work is already in the store.** `allenai/Olmo-3-1025-7B`
carries 43 rungs including **stage3 at 1000-step spacing on a fully-trained
model** -- same spacing, same fluency, different operation. That gives three
regime entries and a within-stage baseline:

    stage1-final -> stage2-step1000     pretraining mixture change
    stage2-final -> stage3-step1000     annealing
    Olmo-3-1025-7B -> Think-SFT@1000    fine-tuning     28.7% vs 20.3%
    twelve within-stage3 transitions    the flat baseline

    all three entries show it   -> regime change, not fine-tuning
    only SFT shows it           -> fine-tuning specifically
    within-stage3 shows it too  -> it is what 1000-step spacing looks like

NOT RUN. It needs one `rung_movement.py` pass on the other ladder and no new twp.
`stage1-step10000` is broken (212 rows / 3 prompts against 2,272 elsewhere) and
must be excluded rather than read as a gap.

## WHAT THE SELECTION COST: THE DECLARED ARM WAS A WEAK INSTRUMENT

The registration declared **AUC of the normalised progress curve**, on the **top faller and top riser per prompt**. Both choices were mine and both were bad, and the finding is kept here because the size of the loss is the lesson.

    DECLARED  (top word per prompt, AUC)   +0.0910   329/505    p<1e-6
    DISCOVERED (all words, t_move)         +5,341    506/507    p<1e-6

**The pairing was never required by the question.** "Does the faller move before the riser" compares two DISTRIBUTIONS of timings; it needs no faller matched to a particular riser. Matching them discarded 14 of every 15 observations and imported a selection rule that favoured high-frequency function words — `have`, `was`, `be` — so the declared arm largely measured a genre shift into procedural register (`have -> consider`, `be -> check`) rather than displacement.

**And AUC was the wrong statistic**, for a reason only the raw curves revealed: it needs a signed total in the denominator, so a faller that AMPLIFIES before falling gets a negative `f(n)` early and reads as LATE. It scored the amplification as lateness. `t_move` weights by |movement| wherever it happens.

Two things reported earlier in this file's history are **withdrawn as selection artefacts**:

- *"the ordering is stronger for SEXUAL fallers"* (+0.2135 against VIOLENT's +0.1022). It does not survive using all words: +5,651 against +5,687.
- *"Q3's charge null was an artefact"* — briefly claimed on a binned prompt-level ladder, then refuted at word level (rho=+0.038). **Q3's null broadly stands.** What the selection destroyed was the size of the MAIN effect, not the charge result.

RH, whose four questions produced the correct arm: *"isn't this just the top riser/faller still? How do we scale this up? Do we need word-pairs? Are we measuring within prompts as we should be?"*

## F04's THREE EXHIBITS: ONE HOLDS, ONE IS REFUTED, ONE IS PROMPT-SPECIFIC, ONE IS UNTESTABLE

**CORRECTED after RH asked which prompt was being traced.** An earlier version of
this section pooled `fuck` mass across four prompts and reported "-75% @1000,
-96% @5000 ... reproduces F04 to within a few points". **Pooling mass across
different prompts is the wrong aggregate** — one prompt carried 48% of the
pooled base, so the pooled number was largely that prompt. Per prompt the
pattern is in fact TIGHTER than pooling suggested:

    fuck, per prompt      @1000   @5000   @43000
      man and a woman      -82%   -100%    -100%
      beautiful/disgusting -74%   -100%    -100%
      took off clothes     -71%    -93%     -97%
      alone in the house   -80%   -100%    -100%
      MEDIAN               -77%   -100%    -100%

**And the comparison to F04 cannot be made.** F04 states `fuck` at **0.027 at
base**; none of these four prompts is at 0.027 (0.0118, 0.0195, 0.0458, 0.0190),
and F04 does not say which prompt or whether it pooled. So the DIRECTION and
rough magnitude agree and the arithmetic is unverifiable. "Reproduces to within a
few points" is withdrawn.

### `fuck -> kiss` — REFUTED

F04: *"`kiss` — the dominant displacement target — rises over step 5000-15000."*
At the four sites where `fuck` falls:

    kiss   base 0.0013 -> 0.0020 @43000     trivial, both near zero
           base 0.0220 -> 0.0128            FALLS -42%
           base 0.0671 -> 0.0272            FALLS -59%
           base 0.0048 -> 0.0013            FALLS -73%

**`kiss` falls alongside `fuck`.** What actually rises at those sites is `touch`
(0.047 -> 0.163), `know` (0.053 -> 0.122), `love` (0.006 -> 0.020) and `play`
(0.024 -> 0.049). The displacement is real; the named target is wrong.

### `kill -> scream` — HOLDS, BUT ONLY ON THE ANGER PROMPTS

    scream over 11 kill sites:  rises at end 5/11
                                median base 0.0062 -> 0.0059  (flat)

    where it rises clearly:
      "He was so angry he wanted to"    0.0104 -> 0.0254   2.4x
      "She was so angry she wanted to"  0.0320 -> 0.0658   2.1x

**Both are the anger prompts.** On `He hated her deeply and wanted to`, `scream`
is not a plausible substitute for `kill` and it does not rise. F04 generalised
what is a prompt-specific substitution — which is what hand-picking a word pair
and reading it off one figure will do.

### `kill -> said` — UNTESTABLE HERE

`said` returns **no rows at any rung** on the `kill` sites: it never clears theta
in either arm there. F04's "said x4.5 on violence prompts" cannot be checked on
this panel.

### What DOES hold

`fuck` collapses to **zero** by step 2000-3000 and never returns — monotone,
immediate, no amplification — at all four sites. F04's general claim, that
sexual repression is immediate and phase-transition-like, replicates. Its
specific displacement pairs mostly do not.

`kill` does something else entirely: amplified ~+35% at step 1000, down by 5000, a partial recovery at 8000-12000, settling ~85% below base. F04 described this as "down by 5000 then bouncing back by 20000" and the bump is there — but F04 **missed the initial amplification**, which is the larger part of the shape.

**So the two words F04 treated as one phenomenon are two phenomena.** n=4 and n=13 — individual prompts, not populations, and this is a lead rather than a result.
## WHAT SHOULD NOT BE CITED

- **Anything about SFT in general.** n=1 lineage, graded C — the store holds exactly one SFT ladder.
- **Anything about DPO or RLVR.** This ladder is SFT only, which matters because the campaign's existing work puts violence repression at DPO.
- **The timing result as a DECLARED finding.** The registered statistic was AUC; `t_move` is the discovered arm and supersedes it on merit, not on registration.
- **This section's rho values individually.** None exceeds 0.16; the claim is the agreement across three unrelated instruments, not any one row.
- **Q2/Q3 as evidence that charge is irrelevant.** They used a saturated instrument. Type-level charge orders faller timing at -0.122.
- **A charge modulation at either grain.** Word level rho=+0.0384 (p=0.090); prompt level rho=+0.0001 (p=0.998), terciles differing by 15 steps on 5,341. State the bound as a fraction, not as a p.
- **F04's exhibits.** `fuck -> kiss` is refuted, `kill -> scream` holds only on the anger prompts, `kill -> said` is untestable here. Only the GENERAL claim replicates.
- **"29.5% of fallers amplify" as a finding.** It is 29.5% against a 22.6% riser baseline, and the rate asymmetry is 6.9pp. The magnitude asymmetry is the result; the rate is nearly the null.
- **The excursion as a property of SFT time.** It occurs at ONE transition, the one crossing into fine-tuning, and never recurs. Whether it is about fine-tuning or about regime change is untested.
- **The Q1 AUC numbers for anything.** Kept above as a record of what the selection cost.
- **The timing result as DISPLACEMENT.** Fallers and risers have the same median charge (+0.000 both). The two-phase timing is established; that mass moves from charged to uncharged words is NOT, except weakly on the sexual subset where 66% of prompts have a sexual riser anyway.
