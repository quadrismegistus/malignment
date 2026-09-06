# Q1: the faller leaves before the riser arrives — but on this panel both are front-loaded, and the sites are not F04's

**id:** emergence/tuning_order **status:** Q1 RUN 2026-09-06 against `REGISTRATION.md` frozen the same day at `6c238ff`. Producer `analyse.py`, output `results/q1.txt`. Q2 and Q3 not run.

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

## WHAT SHOULD NOT BE CITED

- **This as a reproduction of F04.** Different sites, mostly function words. See above.
- **The n=27 subset as the estimate.** It is a robustness check with a wide interval, and its selection rule was chosen after seeing the data.
- **"Arrival is gradual."** It is not, on the full panel: AUC 0.76 against a linear 0.5.
- **Anything about SFT in general.** n=1 lineage, graded C.
- **A level.** Every claim here is about onset, lag and shape; the ladder is `rule_version` 3 throughout and a v3/v4 difference is a uniform level shift.
