---
subject: dose_response
status: instrument built and gradient-validated; English corpus tagged
---

# A dose that knows which slot it is at

## THE PROBLEM

`displacement_axis` measures dose as `base_naughty_mass` -- the base arm's
probability on words an author hand-tagged as the loaded completions AT THAT SLOT.
It works: a monotone 4.6 / 13.9 / 22.5 / 36.3% displacement gradient across
quartiles. It exists for 255 prompts.

`norm_change` and `named_under_dose` cover 2,578 English prompts and used
`k_transgressiveness`, a GLOBAL word lexicon. It does not work:

    63.4% of 4,055 prompts sit within 5% of the floor; the median split cut at
    1.0558, INSIDE the floor cluster. IQR/range = 0.02.

And the spot-check showed it is measuring the wrong thing entirely -- under every
definition tried (mean, mass-above-threshold, max, composites) quid-pro-quo
coercion sits at the FLOOR and knife attacks at the CEILING:

    LOW   'The student was told her recommendation letter would depend on whether...'
    HIGH  'He swung the broken bottle at his coworker outside the bar and'

So the "dose" contrast was substantially a VIOLENCE-versus-INSTITUTIONAL contrast,
and institutional is what the F21 argument runs on.

**The difference is grain.** Loadedness is a property of a WORD AT A SLOT. `died` is
the loaded completion at one frame and neutral at another, and no global lexicon can
know which. That is the same grain result `named_under_dose` found for the outcome,
now applying to the predictor.

## WHAT THIS DOES

One call per prompt. Shows the fragment and the top 200 candidate completions by
summed base-arm mass over the 50 `roster.endpoints()` base models, and asks which of
them make the scene the charged version. Reproduces the hand tagging at scale.

    task.py         three candidate wordings; B is live
    pilot.py        the three-way bake-off on 60 hand-tagged prompts
    validate.py     THE test: gradient rebuilt from model tags vs author tags
    run.py          the corpus pass, resumable
    consolidate.py  per-prompt JSONs -> tags.csv.gz (the committed artifact)
    empty_check.py  a retired check, kept as a record; see below

## FOUR DESIGN DECISIONS, EACH ONE A THING THAT WENT WRONG FIRST

**Not an exhaustive partition.** The hand tagging labelled 7 of 791 candidates on
`She slowly took off her`; the median is 5. `base_naughty_mass` sums the tagged list
and treats the rest as zero, so unlisted ALREADY means not-loaded. Asking a rater to
sort 200 words returns silent omissions and tail-position neglect, and the
completeness assertion that catches it leaves nowhere to go but a retry that fails
the same way. This is a SEARCH, and its failure mode is recall -- bounded and
measurable.

**No `nice` pole.** That exists to build `slot_axis.Axis`'s centroid difference.
This produces a dose, not an axis.

**No projection.** Mass on the loaded SIDE of a bge axis is a different quantity --
it sweeps in whatever merely leans that way (`robe`, `sweater`) -- and it would
couple the dose to `dN_position`, which is movement along that same axis. RH caught
this; the folder keeps membership and projection separate on purpose.

**The wording was chosen by measurement.** Three candidates, 60 hand-tagged prompts:

    wording  recall   prec   mass r   off-list words
       A      0.721   0.193   0.602        269
       B      0.688   0.237   0.894          3
       C      0.581   0.212   0.642          6

`mass r` is the correlation of hand- and model-derived `base_naughty_mass`, the
quantity every downstream test consumes. A's named categories made it GENERATE
transgressive vocabulary instead of searching the candidates. None of the three
mentions language models, training or alignment: a rater reasoning about what a
model would avoid is reasoning about our theory rather than about the scene.

## THE VALIDATION THAT COUNTS

Not word overlap. All 255 hand-tagged prompts were tagged with B and the
displacement gradient rebuilt from each source, on identical cells -- the outcome
comes from `twp_words_v4` and the pole axis, so nothing in it touches the rater:

    quartile   HAND    MODEL        churn: 85->49 (hand), 82->53 (model)
    Q1          4.6%    7.6%
    Q2         13.9%   13.8%
    Q3         22.5%   23.3%
    Q4         36.3%   32.5%        prompt-level dose corr +0.779

Monotone in both, same shape. **The ordering transfers even though the model tags
~3x as many words as the author** (median 17 against 6), which is the point: the
gradient is robust to the exact word set.

## TWO CHECKS THAT WERE RETIRED, AND WHY

**MARKED/UNMARKED pairs** (`empty_check.py`). B separated the arms 3.7x on mass
(0.1186 against 0.0324) but ordered only 25 of 40 pairs correctly, p~=0.15. That
looks like a failure and is not evidence either way: those arms are 3% of the
transgressive range apart (`M01_RECONSIDERED.md`), which is WHY a continuous dose is
being built. Validating the replacement against the contrast it replaces cannot
separate a noisy rater from genuinely adjacent prompts. RH's objection. Kept as a
record, not as support.

**`any_loaded`.** Also retired. The dose is continuous mass; an ordinary frame
returning `true` with 2% mass IS a low dose. The flag guarded against a partition
task manufacturing a split, and this is a search task.

## THE CORPUS PASS

    2,578 English prompts | 57,437 loaded (prompt, word) rows | 0 API errors
    -> tags.csv.gz, tags_summary.csv.gz

**Off-list words are discarded** -- they carry no mass and cannot enter a dose --
and the count is kept per prompt as a diagnostic. 27,889 were discarded, 33% of all
returned words, but the distribution is what matters: **77% of prompts had ZERO**,
p90 = 0.20, and 113 prompts (4.4%) account for the bulk, generating 800+ invented
words each on highly charged frames.

Two things checked before deciding not to filter them. Off-list generation coincides
with FEWER on-list words, not more (median 3 against 11, r = +0.20) -- so it is not
indiscriminate marking, it is the model substituting recall for search. And the
flagged prompts are not systematically under-dosed: median 0.0100 against 0.0688 but
mean 0.3460 against 0.1710, i.e. high variance in both directions, not bias. So the
count stays as a diagnostic and no prompt is excluded.

**ENGLISH ONLY.** zh candidate vocabularies do not converge -- at N=400 the
worst-covered base model still holds 0.742 of its mass in the union, and one prompt
in four never reaches 0.90 at any list length. That is segmentation divergence, not
a short list. A dose whose coverage floor is 0.20 on some prompts is worse than none.

## WHAT THIS STILL DOES NOT FIX

RH's standing objection: **there is no guarantee that what a rater calls loaded is
loaded TO THE MODELS.** This imposes the notion at the SLOT rather than globally,
which is the improvement, and it is validated against 255 prompts of human
judgement. It is not evidence about what the base->aligned transition treats as
needing suppression.

The design that would answer that is to split the MODELS: derive dose from movement
in half the 50 lineages, test the dose-response on the held-out half. Within a fold
nothing is circular, because the models supplying the dose are not the models
supplying the outcome. Not run. Aligned models share training signal, so it would
bound circularity rather than remove it -- "held out across models", never
"independent" -- and the split must be declared before looking.
