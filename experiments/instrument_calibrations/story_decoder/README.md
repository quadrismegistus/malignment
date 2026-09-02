---
kind: calibration
status: RUN
headline: "THE TWO ARMS WANT OPPOSITE DECODERS"
---

# Which decoder and frame let BOTH arms write a story?

Producer: `run.py`. Data: `sweep.jsonl` (120 rows), run by malign on a rented
4090, docket [6576], $0.65. Standalone -- torch and transformers only.

Replicating Rettberg & Wigers (2025), who generated 11,800 national stories from
gpt-4o-mini, with the arm they lack: base against aligned. They have one aligned
model and no counterfactual, which is why their second peer reviewer (Kang) can
ask in print why the plot structure is there and the authors cannot answer.

## THE HEADLINE: THE TWO ARMS WANT OPPOSITE DECODERS

Full 2x2 over temperature x top_p, 160 generations. USABLE means not salad
(function-word share below 0.25), not looping (rep8 at or above 0.15), and no
escape into assistant register.

                    t0.8/p1.0  t0.8/p.95  t1.0/p.95  t1.0/p1.0
    base usable          2/10       2/10       8/10      10/10
    base loop            8/10       8/10       2/10       0/10
    base salad           0/10       0/10       0/10       0/10

    aligned usable      26/30      24/30      24/30      11/30
    aligned salad        0/30       0/30       3/30      17/30
    aligned loop         4/30       5/30       1/30       1/30

    POOLED usable       28/40      26/40      32/40      21/40

**Base needs temperature 1.0 or it loops. Aligned needs top_p 0.95 at that
temperature or it turns to salad.** Each parameter fixes one arm's failure and
neither fixes both, so `t=1.0/p=0.95` is a compromise rather than an optimum --
it is the best available at 80% usable, and it is still the worse setting for
the aligned arm considered alone.

**top_p=0.95 does nothing at temperature 0.8** (more repetition in 6 of 8 cells,
pooled median rep8 0.0129 against 0.0030) and everything at 1.0, where dropping
it takes aligned salad from 3/30 to 17/30. An earlier version of this file
concluded from the 0.8 contrast alone that top_p was inert. The cell that
settles it, (1.0,1.0), was missing from the first sweep -- a hole in the design
of this experiment, not in the run -- and was added on docket [6579].

## THE MEASURES DISAGREE BY CONSTRUCTION, AND MUST

No single number separates the three failures. Validated against samples read by
eye:

                     dist3         fn_en         rep8
    good prose       0.881-0.969   0.408-0.443   0.000-0.016
    repetition loop  0.432         0.555         0.478
    token salad      0.997-0.998   0.098-0.162   0.000

**Salad is maximally non-repetitive**, so rep8 and distinct3 score it PERFECT --
the setting with the worst salad in this corpus (t1.0/p1.0, 17/30 aligned) has
the lowest repetition of any cell. And the repetition loop carries the HIGHEST
function-word share of anything measured, because a repeated clause is dense in
function words. An analysis using either measure alone inverts.

`distinct3` in particular has a healthy BAND and not a direction -- but the band
is unreliable at the top, because long varied literary prose also scores 0.97+.
Use `fn` for salad and `rep8` for loops; do not threshold `distinct3` alone.

## WHAT HELD

**Escape into assistant register is aligned-only.** Service formulas, meta
commentary, list markers or emoji in the last fifth of the text:

    base, any frame        0/30
    aligned raw            6/30
    aligned prefill        1/30
    aligned chat           0/30

A base checkpoint never does it. An aligned one does it in the frame with no
turn to end, and mostly stops once given one. That is the mechanism: the model
reverts to assistant register when there is nothing to be inside.

**A turn guarantees termination.**
    chat + prefill         60/60 ended on eos
    aligned raw            15/30 ended on eos
    base raw               8/30 ended on eos

**The arms fail disjointly.** Base repeats and never escapes; aligned escapes
and barely repeats. A single "degeneration rate" would average two different
failures into one meaningless number.

## THE DESIGN THIS SETTLES

    cell 1   base      raw       A {D} Story\n(1500 words)\n\nIt was a
    cell 3   aligned   prefill   THE SAME STRING, in the assistant turn,
                                 with an EMPTY user turn
    bridge   aligned   raw       the same string, raw
    cell 2   aligned   chat      Write a 1500 word potential {D} story.

    cells 1, 3, bridge   t=1.0, top_p=0.95
    cell 2               t=0.8, top_p=1.0   (Rettberg's exact call)

Cell 2 keeps their setting because it WORKS there: rep8 0.007, 5/5
terminated, 1203 words against their 1,415-word median. The failure was never in
the chat frame.

**The bridge is load-bearing, not tidy.** Cells 1 and 3 differ in the arm AND
the turn wrapper. Measured locally at matched cap, the wrapper's own effect on
length (-597 words, t=2.20) was LARGER than the arm's (-354, t=-0.93, sign
unstable between n=3 and n=10). A two-cell comparison would have reported a
1,000-word alignment effect that is mostly a wrapper effect sitting on an arm
effect indistinguishable from zero.

**Empty user turn, not "Hi." and not "Continue."** "Hi." is a greeting and
warrants a short reply; it produced 30-560 word stubs that were nearly read as
evidence about instructionless generation. "Continue this text:" is measured in
this campaign at ~80% of alignment's own effect.

## NOT ESTABLISHED

- **The arm effect on length.** t=-0.93 and the sign flipped between n=3 and
  n=10; the base distribution is bimodal (216-999 and 2113-2678 words), so small
  samples land in one mode or the other.
- **Generality.** One model family, one demonym. "Raise the temperature to
  reduce repetition" runs against the usual advice and should not enter a
  finding on n=5 in one family. Two more families on `raw_count` at the two
  decoders would settle it: 4 cells, not 24.

## WHAT THE INSTRUMENTS GOT WRONG, WHICH IS THE REUSABLE PART

Four measures written for this pilot produced wrong readings, and all four
looked like results:

    a function-word ratio    missed ALL THREE real failure modes and rated the
                             worst repeater the CLEANEST text in the pilot,
                             because repeated clauses are function-word dense
    bare `you|your`          reported assistant escape in a BASE folktale --
                             "I will go with you to my father's house"
    `happy to`               same, on "was happy to have their father back". A
                             service formula is diagnostic only when COMPLETE
    n=3                      inverted the sign of the headline length effect

Three of the four pushed AGAINST the hypothesis, which is luck and not method.
What caught every one of them was reading the text beside the number. The rows
therefore carry the full text and four INDEPENDENT measures, never a verdict, so
any of it can be recomputed when the next measure turns out to be wrong -- which
is how the flags in `sweep.jsonl` were recomputed here, since it was produced
before two of these fixes.

