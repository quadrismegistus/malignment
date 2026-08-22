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

    H5    alignment increases SECONDARY-PROCESS thinking (RH, 2026-08-22)
          rid_conceptual_secondary UP, rid_primordial_primary DOWN
          NOT inherited -- the first RID measurement on any passage of this
          corpus, and the one closest to the project's Freudian frame

RH's H2 and H3 are separate claims and are registered separately: a valence MEAN
can rise while its SPREAD narrows, or either can move alone. H3 is the plan's
inherited C.H1 in spread form; H2 is new.

Secondary, NO DIRECTION: arousal, dominance. Dominance is the campaign's
twice-dead scale and rides as the negative control it has become.

## COVERAGE, MEASURED ON 60 REAL PASSAGES BEFORE ANY CONTRAST

Coverage decides which sources can carry a passage MEAN and which are rates
only, so it was measured first rather than discovered in the results:

    usas        98.9%     brysbaert  98.9%     k         97.4%
    gi          89.4%     warriner   67.3%     wordnet   63.4%
    rid         50.2%     brooke     11.9%   <- SPARSE, rate only

**H4 has TWO instruments and Brooke is the weaker one.** Brooke reaches 11.9%
of content words at the median against `k_register_level`'s 93.5%, and it is a
mean of +1/-1 over a 1,029-word seed list, not a scale -- so it must be read as
a rate with its denominator attached, and a null on it is a statement about
power rather than about register. `k_register_level` is primary here.

**The `NOT ESTABLISHED` rider on `k_register_level` does NOT bar it, and an
earlier version of this file said it did.** The rider records IAA 0.597 against
Claude Haiku 4.5, which is agreement between two coders of the same kind.
`experiments/displacement/register_shift/registration.md` (section on the two
instruments) supplies the external corroboration that agreement lacks: `k_` and
the displacement lexicon's independently-built register labels agree at
**Spearman rho = 0.645 (n=480, p=1e-57)**, with vulgar-vs-clinical separating at
**AUC 0.976** and clinical-vs-plain at 0.715, the two having been built months
apart by different procedures with neither seeing the other. That is the same
standard being applied to every other instrument in this folder. The rider
still bars quoting a k_register LEVEL as a formality measurement; it does not
bar a paired arm contrast on ranks, which is what H4 is.

**Warriner at 67.3% is the one to watch for the arm comparison.** A third of
content words are absent from it, and absence is not random -- proper nouns are
not in the norms and NNP runs about 7 per 1000 words lower in the aligned arm.
So the coverage differential is expected, travels as description, and is never
corrected for.

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
  * `k_register_level` carries IAA 0.597, which bars quoting an absolute
    formality level. It is NOT barred from paired arm contrasts: it is
    externally corroborated at rho 0.645 / AUC 0.976 against the
    displacement lexicon (see H4 above). Do not restate the older,
    stricter rider without reading that corroboration.
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
