# The faller leaves before the riser — generally, not because it is charged — and it is AMPLIFIED first

**id:** emergence/tuning_order **status:** Q1 and Q3 RUN 2026-09-06 against `REGISTRATION.md` frozen the same day at `6c238ff` (amended §5a). Producers `analyse.py`, `explore_q3.py`, `curves_fk.py`; outputs under `results/`. **Q2 not run.**

## THE SHORT VERSION

1. **Q1 holds.** The faller completes its move earlier than the riser: +0.0910 AUC, 329/505, p<1e-6, t50 3000 against 6000.
2. **Q3 says it is not about charge.** The ordering at increment 0 is indistinguishable from increment >= 1 (spearman -0.019). Departure-before-arrival is a general property of SFT displacement.
3. **DISCOVERED, and the most interesting thing here: 29.5% of fallers are AMPLIFIED at step 1000 before they fall.** Flat across charge. It also confounds the declared statistic, which reads amplification as lateness.
4. **`fuck` reproduces F04 to within a few points; `kill` does not, and F04 missed why.** They are two phenomena, not one.

Every claim below is labelled DECLARED or DISCOVERED per the registration's soft-border rule.

## THE DECLARED RESULT

505 sites — one top faller and one top riser per prompt, fixed at base → `Think-SFT@step43000` and tracked back across all 43 rungs. Prompts are the replicate within one lineage.

    faller AUC   median  +0.8755
    riser  AUC   median  +0.7633
    DIFFERENCE   median  +0.0910   329 up / 176 dn   p < 1e-6   CI [+0.0671, +0.1115]

    t50 (secondary)   faller  3000      riser  6000

**The declared direction holds.** The faller completes half its total movement by step 3000; the riser by 6000. On the paired AUC statistic the faller is earlier in 329 of 505 prompts.

## THE ARTEFACT THAT COULD HAVE PRODUCED IT RUNS THE OTHER WAY

The registration says non-monotonicity is *reported, not corrected*. Reporting it surfaced a threat: **AUC is inflated by overshoot**, so if fallers overshot more than risers the whole effect would be a normalisation artefact rather than an earliness difference. The curves overshoot heavily — median max `f` = 1.19, p99 = 3.43, and 28% dip below −0.10 (they move the *wrong way* first).

    overshoot (max f)   faller median 1.096   riser median 1.387
                        DIFF -0.281   67 up / 438 dn   p < 1e-6

**Risers overshoot more, so the inflation accrues to risers.** The declared effect is therefore *conservative*, and removing the artefact makes it larger, not smaller:

    well-behaved curves only (both max f <= 1.10)
      n=27   faller AUC 0.8569   riser AUC 0.6196
      DIFF median +0.2294   24 up / 3 dn   p=0.00005   CI [+0.0846, +0.3086]

n=27 is small and that interval is wide; it is a robustness check, not a better estimate.

## WHAT DID NOT HOLD: THE SHAPE HALF

The registration's favoured direction was *departure step-like, arrival gradual*. **The order holds; the character does not, on the full panel.** A gradual curve is AUC ≈ 0.5, and the riser sits at **0.7633** — front-loaded too, just less so than the faller. That is disappointing-direction 4 (*lag present, both curves the same shape*) partially realised.

On the well-behaved subset the riser is 0.6196, nearer to linear, so the predicted character difference may be real and obscured by overshoot in the full set. **Not claimed** — n=27, and the subset was chosen after seeing the overshoot pattern.

## THE LARGER PROBLEM, AND IT IS INTERPRETIVE RATHER THAN STATISTICAL

**These are not F04's sites.** Ranked by endpoint fall, the largest movers on this panel are function words on institutional prompts:

    prompt                                faller           riser
    After an officer searched the car...  have    0.919    consider  0.925
    My company laid off my whole team...  have    0.852    file      0.691
    The university says the appeal...     have    0.795    check     0.752
    I was wrongly denied unemployment...  have    0.883    appeal    0.876
    Every time a customer disputes...     be      0.946    check     0.813

`have → consider`, `have → file`, `be → check`. That is a **genre shift into procedural register**, and it is a real and interesting thing for SFT to do — but it is not the claim F04 made. F04's exhibits were `fuck → kiss`, `kill → scream`, `kill → said`: a *charged* word barred and a substitute arriving.

So **Q1 as run establishes an ordering over whatever moves most, and what moves most on this panel is largely syntactic scaffolding.** Whether the ordering holds for charged words specifically is exactly Q3, and it is not answered here. Until it is, this result should not be cited as reproducing F04.

This is a property of the panel, not a defect of the run: the 512 non-verse ladder prompts are dominated by the institutional and contradiction families (106 `other`, 96 `contradiction`, 25 `institutional`, 210 across the `pairs` domains), and the top mover per prompt is selected by raw |delta|, which favours high-frequency words.

## WHAT IS DECLARED AND WHAT IS DISCOVERED

Per §0 of the registration — a soft border, and the distinction is kept rather than the departure prevented.

    DECLARED    the paired AUC test, t50, the non-monotonicity report
    DISCOVERED  the overshoot check and the well-behaved-curve restriction;
                the observation that the top sites are function words on
                institutional prompts

The overshoot check was not pre-specified. It was prompted by the declared non-monotonicity report and it happens to defend the result — which is why it is labelled, and why the well-behaved subset is offered as a check rather than as the headline.

## Q3 — THE ORDERING IS NOT SPECIFIC TO CHARGED WORDS

Moderator: the faller's `scene - frame`, its own increment over its setup (registration §5a). 321 of 507 sites have both an AUC pair and a rated faller; the 186 without are the function-word fallers the content filter never sent to the rater.

    increment    n     med diff   faller AUC   riser AUC    up/dn
    +0         233     +0.1097      0.8774      0.7612    159/74
    +1          44     +0.1108      0.8713      0.7507     29/15
    +2          19     +0.1823      0.9101      0.7069     14/5
    +3          11     +0.1042      0.8335      0.7239      7/4
    +4           7     -0.1800      0.8956      1.0756      3/4

    increment == 0   n=233  +0.1097   p=0.00000   CI [+0.0605, +0.1307]
    increment >= 1   n=85   +0.1193   p=0.00451   CI [+0.0417, +0.1331]
    increment >= 3   n=22   +0.0674   p=0.52347   CI [-0.0956, +0.2948]

    spearman(increment, AUC diff) = -0.0188

**The ordering at increment 0 is indistinguishable from the ordering at increment >= 1.** Departure-before-arrival looks like a general property of SFT displacement rather than something charged words do specially — the opposite of the sharpening the commission wanted.

**The tail null is a BOUND, not a finding.** n=22 with CI [-0.0956, +0.2948] cannot distinguish "no charge effect" from "an effect this panel cannot see". Spearman is uninformative here for a structural reason: eight of ten deciles of the increment are tied at exactly 0, so the rank transform is mostly ties.

## DISCOVERED: THE FALLER IS AMPLIFIED BEFORE IT IS REPRESSED

Not declared, not predicted by anyone, and visible only in the raw curves.

    149 of 505 fallers (29.5%) move UP at step 1000 before falling.

Flat across charge — 32% at increment 0, 34% at >= 1 — so it is a property of early SFT, not of transgression. On `kill` it is stark, and 9 of 13 sites show it:

    He hated her and despised her...   kill  0.2321 -> 0.3174 @1000 -> 0.0687 @5000 -> 0.0293 @43000
    He hated her deeply and wanted...  kill  0.1812 -> 0.2743         -> 0.0727        -> 0.0283
    She hated him and despised him...  kill  0.2204 -> 0.3054         -> 0.0662        -> 0.0486

The risers at those sites (`make`, `be`, `break`) climb steadily throughout with no such excursion.

**AND THIS IS A DEFECT IN THE DECLARED STATISTIC, which only the curves revealed.** For a faller `T` is negative, so an early *rise* makes `f(n)` negative and DEPRESSES the faller's AUC. The statistic reads amplification as lateness. That is why `kill` sites appeared to show arrival-first: they do not, they show departure-after-amplification. **Any AUC comparison on a panel where 29.5% of fallers are amplified first is measuring earliness confounded with amplification**, and Q1's +0.0910 should be read with that attached.

## DISCOVERED: `fuck` AND `kill` DIFFER IN SHAPE, AND `fuck` REPRODUCES F04 EXACTLY

    fuck   pooled  -75% @1000   -96% @5000   -100% @20000     (4 sites)
    F04 reported   -70% @1000   -92% @5000

`fuck` collapses to **zero** by step 2000-3000 and never returns — monotone, immediate, no amplification. That is F04's headline reproduced on independent machinery to within a few points.

`kill` does something else entirely: amplified ~+35% at step 1000, down by 5000, a partial recovery at 8000-12000, settling ~85% below base. F04 described this as "down by 5000 then bouncing back by 20000" and the bump is there — but F04 **missed the initial amplification**, which is the larger part of the shape.

**So the two words F04 treated as one phenomenon are two phenomena.** n=4 and n=13 — individual prompts, not populations, and this is a lead rather than a result.

## WHAT SHOULD NOT BE CITED

- **Q1 as a reproduction of F04.** Different sites, mostly function words. The `fuck` curve IS a reproduction; the Q1 aggregate is not.
- **Q1's +0.0910 without the amplification caveat.** On a panel where 29.5% of fallers rise before falling, AUC measures earliness confounded with amplification.
- **The Q3 tail null as "charge does not matter".** n=22, CI [-0.0956, +0.2948]. It is a bound.
- **The `fuck`/`kill` split as a population claim.** n=4 and n=13 sites.
- **The n=27 subset as the estimate.** It is a robustness check with a wide interval, and its selection rule was chosen after seeing the data.
- **"Arrival is gradual."** It is not, on the full panel: AUC 0.76 against a linear 0.5.
- **Anything about SFT in general.** n=1 lineage, graded C.
- **A level.** Every claim here is about onset, lag and shape; the ladder is `rule_version` 3 throughout and a v3/v4 difference is a uniform level shift.
