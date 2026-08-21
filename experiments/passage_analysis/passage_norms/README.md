# passage_norms

**Does the word-level signature survive to the page?** M06's Plan C
(`malign-logits/meta/M06_generation/plans/plan_c_affect.md`, drafted 2026-08-13,
never run) at passage grain, on this repo's corpus and instrument.

Named for the object. `affect_at_length` was the alternative and undersells the
battery: Brysbaert concreteness is half of it and is not affect, and the K scales
add vulgarity, register, transgressiveness and bodily harm. It would also name a
framing that goes stale if the bridge fails, which the plan explicitly allows.

## THE HYPOTHESES ARE INHERITED, AND THAT IS THE POINT

Both restate findings this campaign already has at WORD grain. They are not new
predictions and must not be reported as though a confirmation were independent
evidence.

    C.H1  aligned prose is LESS EMOTIONALLY EXTREME
          valence_extremity = passage mean of |valence - 5| over content words
          inherited from Registration C (+0.025, p 0.0012) and E (19/25 lineages)

    C.H2  aligned prose is LESS CONCRETE
          concreteness_brysbaert_mean over content words
          inherited from K (z -17.1 / -18.8) and the M05 de-concretization arc

Secondary, NO DIRECTION: arousal, dominance. Dominance is the campaign's
twice-dead scale and rides as the negative control it has become.

## WHY IT IS A BRIDGE AND NOT A REPETITION

C/E/K measured which words gain and lose probability AT NEXT-TOKEN POSITIONS.
This measures the words that actually ended up ON THE PAGE across a whole
continuation. **The bridge can fail, and a failure is a finding.** Q taught this
campaign that frames reverse between zooms, so a null here locates where
de-extremification lives rather than refuting the word-level result. Declared
before the run, four-cell style, per the plan.

## THE INSTRUMENT IS ALREADY BUILT AND IS NOT REBUILT HERE

`malignment.fields` owns the lookup: `fields.norms()` for Warriner V/A/D and
Brysbaert concreteness, `fields.k()` for the seven K coder scales,
`fields.lemma()` for the lemma policy. That policy is the reason the module
exists -- `lexicons/fields/README.md` records that surface-form lookup sends
`found` to *establish*, `felt` to the fabric and `saw` to the cutting tool, and
`found` is the corpus's single most frequent riser. A policy in one importable
place is a policy; retyped per analysis it is several.

So this folder holds a producer and a contrast, and no lexicon plumbing.

## THE RIDERS TRAVEL VERBATIM

From `fields.py` and the plan's Amendment 1, and none of them is optional:

  * The K scales are ONE MODEL's judgments at ONE frozen instrument. The `k_`
    prefix is load-bearing and they are never presented beside the human norms
    as the same kind of object.
  * `k_register_level` is NOT ESTABLISHED -- descriptor only, never evidence.
  * `k_vulgarity` is a sparse indicator (variance on 463 of 27,242 words).
    Floors are not nulls.
  * RANKS NOT LEVELS: levels shift between instrument versions at stable order,
    so paired arm contrasts are permitted and absolute thresholds are not.
  * `k_concreteness_mean` beside `concreteness_brysbaert_mean` is a built-in
    convergence check -- word-level r 0.88.

## TWO THINGS THE PLAN REQUIRES THAT A MEAN WOULD HIDE

**Coverage is reported per passage and per arm.** A passage below 50% coverage
on an instrument leaves that instrument's contrast, with the exclusion rate
travelling as description -- because coverage is EXPECTED to differ by arm.
Proper nouns are absent from the norms and NNP runs 7 per 1000 words lower in
the aligned arm, so a coverage difference is a property of the text, not a
defect, and hiding it would silently reweight the comparison.

**Distributions, not only means** (Amendment 2, RH's caution). Sparse norms live
in the tail: one `kill` against none barely moves a 185-word passage mean. So the
producer stores a lossless 7-cell count vector per K scale and 16-bin histograms
for the continuous norms, and the mean is one read of several rather than the
record.

## STATUS

Folder opened. Producer not yet written, nothing run, no numbers.
