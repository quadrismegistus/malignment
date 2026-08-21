# Entropy is the control, not the result

RH, 2026-08-19: *"What do you want me to do about entropy it's a fact of alignment"*. Correct, and it was in headline position where it does not belong. Entropy collapse under RLHF and DPO is established and widely reported; a table showing that distributions narrow is a table showing the null hypothesis. The measurement stays in the pipeline as a control. It stops being quoted as a finding.

What it did earn is the objection it makes possible, which is the sharpest one available against this whole line of work: **if alignment always concentrates, displacement may be concentration wearing a costume.** On that reading `cock -> beard` is not a substitution at all, it is mode collapse onto whatever the base already preferred, and the raters are characterising an artifact.

## The test, and it separates

156 cells: 6 frames (sexual, institutional, and the four matched identity frames) x their declared endpoint pairs. Per cell, both arms renormalised within their observed word field.

If displacement were concentration, the aligned arm's most likely word would be the base's most likely word, and the cells that collapse hardest would be the cells that move the most mass. Neither holds.

    aligned mode == base mode                    80 of 156
    aligned mode is a DIFFERENT word             76 of 156   (49%, p = 0.81 against 50/50)

Where the mode moves, the word it moves to was typically ranked **3rd to 9th** in the base distribution, not 2nd. On the Israeli action frame it moves on 16 of 24 lineages and 13 of those 16 land on a word the base ranked worse than third.

And the two axes pull apart in the direction that kills the objection:

    group        median dH        median total variation      narrows
    mode kept    -0.430 bits      0.272                       66/80
    mode moved   -0.247 bits      0.371                       52/76

**The cells that substitute collapse LESS and move MORE.** If substitution were a by-product of collapse the relation would run the other way. Among the 118 cells that do narrow, the mode still moves on 52 of them, 44%.

    Pearson r (entropy drop, mass moved) = +0.532 over 156 cells,  r^2 = 0.283

**That figure does not survive a support filter and should not be quoted.** Eleven of the 156 cells have fewer than 40 words measured in both arms, and on such a cell both entropy and total variation are extreme for the same reason: there is almost nothing there. Drop them and the same correlation over the remaining 145 falls to **r^2 = 0.040**. Eleven points carried it from 4% to 28%.

The conclusion is unchanged and in fact stronger -- concentration explains almost none of the mass movement on any cell with real support -- but the number to state is 4% on 145 well-supported cells, not 28% on 156. A correlation that moves by 7x when 7% of the population is removed is a statement about those eleven cells.

## What this changes in how the work is written

- Entropy is reported once, as a control, with the citation that makes it a known quantity. It is never a row in a results table.
- The claim is not that alignment concentrates. It is **what it concentrates onto**, which the literature on mode collapse does not ask, and which on half of these cells is not the base's own preference.
- Any statistic offered as evidence of displacement has to survive this partition. A quantity that vanishes once the mode-kept cells are separated out is measuring collapse.

## Fence

The mode test is a hard threshold on a soft quantity: two words within a rounding error of each other at the top of the base make "the mode moved" an arbitrary call. It is used here because it is the cheapest statement that cannot be produced by concentration alone, not because rank-1 is special. The total-variation column is the continuous version and shows the same split.


# Would ranks be more straightforward

RH, 2026-08-19. Yes, and the argument for it is structural rather than a matter of taste: **a rank is invariant to concentration by construction.** A sharpening that preserves the ordering leaves every rank untouched, so rank movement cannot be manufactured by mode collapse, and the partition above stops being necessary. The objection is answered by the choice of instrument rather than by a post-hoc split.

Measured over the same 156 cells, with the instrument being **Kendall tau over the base's top 20 words on common support** -- top 20 carries a median 70% of base mass, and common support because a word measured in one arm and not the other has no rank there, so imputing one would score coverage differences as reordering:

    population                r2(entropy, MASS moved)   r2(entropy, RANK reordering)
    all 156 cells                      0.283                        0.097
    145 cells, support >= 40           0.040                        0.023

Ranks are the less contaminated instrument on both populations, and they are markedly more stable across the two: the mass figure moves 7x under the filter and the rank figure moves 4x from a base so low it hardly matters. And ranks are not throwing the signal away -- reordering correlates with mass moved at r = +0.70, so the two are measuring largely one thing.

    median top-20 tau        stroking +0.537   union +0.505
                             isr_action +0.405   pal_action +0.416
                             isr_affect +0.632   pal_affect +0.589

tau = 0.5 means a quarter of all pairwise orderings between the top 20 words flipped. It is below 0.5 on 70 of 156 cells, and the action frames reorder hardest.

## What ranks cost, and why this is not either/or

- **They discard magnitude entirely.** `cock` going 35% to 8% and a word going 0.4% to 0.09% can move the same number of places. Magnitude is the whole reason the substitution matters, so the effect size stays in mass.
- **They need a support floor.** Below about 40 words in common the statistic is unstable, and that instability is exactly what produced the eleven-cell leverage above. State the floor and the cells it drops.
- **tau is one number per cell.** It says how much reordered and never what. Every lexical claim -- `cock` to `beard`, `fire` to `terminate`, `threatened` rising -- is a claim about which words and by how much, and no rank statistic can carry it.

So: **ranks for the structural claim, mass for the content claim.** The headline that alignment reorders the field rather than merely sharpening it is a rank result and should be stated in tau. The findings about what it reorders toward are mass results and stay in percentage points, with the support floor and the concentration control declared beside them.
