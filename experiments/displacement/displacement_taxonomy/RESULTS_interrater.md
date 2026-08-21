# Two raters on one table: what a single coding is worth

84 cells coded twice, independently, under instrument r4, on byte-identical tables. Runs `wf_ac532329-ef4` (rater 1) and `wf_63d63445-e10` (rater 2). Every one of the 318 codings before this was a single rater, so nothing in the project had a reliability estimate behind it.

## The number

    a_words   median Jaccard 0.800   mean 0.765
    b_words   median Jaccard 0.833   mean 0.806
    zero overlap on 1 cell of 84 in each column
    relation count agrees on 60 of 84; means 2.63 against 2.58
    confidence  r1 17/63/4 high/medium/low   r2 13/69/2

Two blind agents given the same table pick largely the same words.

## THE DISTINCTION THAT BOUNDS EVERY USE OF IT

**0.80 is WORD agreement, not CONSTRUCT agreement.** It says two raters point at the same words. It does not say they named the same relation, and they demonstrably need not: on the eleven stroking cells carrying three codings, raters have selected overlapping words and described them as different constructs.

    a single coding is a RELIABLE guide to which words carry a difference
    and an UNVALIDATED guide to what the difference is

So a validation of the form *did the rater pick out the words the instrument was meant to surface* is supported at 0.80. A validation of the form *did the rater get the interpretation right* is not supported at all yet. Construct agreement needs the harmonisation pass, where it comes free: put both raters' relations in and see whether the harmoniser assigns them to one construct.

## The zero-agreement cell is the instrument working

`unzipped/rwkv-raven-7b` shows 8 words. Rater 2 declined to read it, kind *rank order essentially unmoved*. Rater 1 read a naming distinction into it. On the evidence rater 2 is right.

`NONE IS A LEGITIMATE ANSWER` was in the template and a rater used it. Nine of 84 cells got a low or refusing read, and those are the cells to trust most rather than least -- a guard nobody has been observed using is a belief rather than a check.

## CORRECTION: there is no table-size effect

Reported on 2026-08-19 and wrong. I quoted agreement by size quartile as `0.857 / 0.889 / 0.800 / 0.723` and described it as falling with table size. **Those four numbers rise and then fall, and I read a trend into them that they do not make.** The cell-level correlation is:

    r(agreement, words shown) = -0.000   over 84 cells

Zero. The quartile pattern was frame composition leaking into size bins. Sent to malign and to RH before it was checked; withdrawn in both places.

## Union agreement is low and UNEXPLAINED

By frame:

    isr_affect 0.908   stroking 0.889   unzipped 0.857   isr_action 0.853
    isr_trait 0.812    pal_action 0.812   pal_affect 0.750
    pal_trait 0.718    union 0.637

It is not size: union spans 13-37 words at median agreement 0.637, while the 67 non-union cells in that same band sit at 0.833.

I offered a mechanism -- that union's verbs (`fire terminate discipline suspend investigate`) form a graded sequence rather than two poles, so where a rater cuts is a judgment. **That account failed its only test.** If some frames are harder, an independently measured difficulty signal should order the same way. v3 confidence is such a signal: different raters, different presentation, different wave.

    r(r4 agreement, v3 confidence) across frames = +0.132

Nothing. And it fails in the one place the story needed: **union has the second-highest v3 confidence, 2.50 of 3, and the lowest agreement.** Raters were confident on union. A mechanism predicting hesitation where they were confident is refuted, not weakly supported.

Recorded as unexplained. n = 11 union cells.

## What the episode is worth keeping

Both of these came from malign asking whether I would have predicted the ordering beforehand. I would not have, and I did not.

- **An explanation produced after seeing the number is worth nothing until it predicts something else**, and the cheap test is whether an independently measured quantity orders the same way. It took ten minutes and should have been run before the mechanism was offered rather than after being asked for it.
- **"Union agreement is low, I do not know why" is a stronger position than a story that has failed its only test.** A named mechanism feels like more knowledge than an unexplained number and is less, because it forecloses the search.
