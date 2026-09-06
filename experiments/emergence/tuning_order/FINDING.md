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
field, not out of it:**

    "She knelt down in front of him and began to suck his"
      F manhood  0.0121 -> 0.0057        the euphemism FALLS
      R shaft    0.0141 -> 0.0211        the anatomical word RISES
      R erect    0.0064 -> 0.0211

    "She slowly took off her"
      F top      0.0246 -> 0.0013
      R scarf / socks / silk             other garments

That is register shift, not repression — and in the first case toward the
blunter word.

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

## DISCOVERED: THE FALLER IS AMPLIFIED BEFORE IT IS REPRESSED

    149 of 505 fallers (29.5%) move UP at step 1000 before falling.

Flat across charge (32% at lift 0, 34% at >=1). On `kill` it is stark — 9 of 13 sites — and it is why `kill` looked like arrival-first under the AUC statistic. F04 saw the later recovery ("bouncing back by 20000") but **missed the amplification**, which is the larger part of the shape.

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
- **A charge modulation at either grain.** Word level rho=+0.0384 (p=0.090); prompt level rho=+0.0001 (p=0.998), terciles differing by 15 steps on 5,341. State the bound as a fraction, not as a p.
- **F04's exhibits.** `fuck -> kiss` is refuted, `kill -> scream` holds only on the anger prompts, `kill -> said` is untestable here. Only the GENERAL claim replicates.
- **The Q1 AUC numbers for anything.** Kept above as a record of what the selection cost.
- **The timing result as DISPLACEMENT.** Fallers and risers have the same median charge (+0.000 both). The two-phase timing is established; that mass moves from charged to uncharged words is NOT, except weakly on the sexual subset where 66% of prompts have a sexual riser anyway.
