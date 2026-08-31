# Which decoder and frame let BOTH arms write a story?

Producer: `run.py`. Data: `sweep.jsonl` (120 rows), run by malign on a rented
4090, docket [6576], $0.65. Standalone -- torch and transformers only.

Replicating Rettberg & Wigers (2025), who generated 11,800 national stories from
gpt-4o-mini, with the arm they lack: base against aligned. They have one aligned
model and no counterfactual, which is why their second peer reviewer (Kang) can
ask in print why the plot structure is there and the authors cannot answer.

## THE HEADLINE: TEMPERATURE IS THE LEVER, top_p IS NOT

Share of repeated 8-grams, n=5 per cell:

                        t0.8/p0.95   t0.8/p1.00   t1.0/p0.95
    base     raw_plain       0.532        0.183        0.000
    base     raw_count       0.466        0.559        0.099
    aligned  raw_plain       0.075        0.166        0.008
    aligned  raw_count       0.299        0.161        0.078

Raising temperature to 1.0 all but eliminates repetition IN BOTH ARMS. Holding
temperature at 0.8 and moving `top_p` does nothing consistent -- base
`raw_plain` gets WORSE and `raw_count` gets better.

**This refutes the recommendation this experiment was built to confirm.** The
plan was temperature 0.8, because it is Rettberg's setting, with `top_p=0.95`
carrying coherence. 0.8 is what drives the base arm into loops. Running the
roster on the planned setting would have produced a base arm made largely of
repetition and, on the evidence of every other reading error in this pilot,
reported it as a fact about base models.

The zero is real, not an empty-string artifact: generations of 352-2,652 words,
`distinct3` 0.969-0.994, `rep16` also 0.000. The registers differ audibly.

    t1.0  "...a cold, hard dread came over me as I"
    t0.8  "...he was glad that the boy was so happy. He said that he had been
           very foolish, and that"

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

