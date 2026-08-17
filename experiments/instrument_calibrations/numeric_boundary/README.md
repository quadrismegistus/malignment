# numeric_boundary — may the boundary rule read context?

**One question with two signs.** v3's boundary classifier makes opposite errors on
two character classes, and they are the same question about whether a boundary
decision may look at what surrounds it:

    ,  .  BETWEEN DIGITS      are boundaries and SHOULD NOT BE
                              `$150,000` is cut to `150`; the store holds
                              250 numeral surfaces and zero commas
    ，  。  FULL-WIDTH CJK      are NOT boundaries and SHOULD BE

Commissioned by the malign seat at docket [6423], who built `score_words`, the
byte tables and the path enumeration, and asked for it to be measured by a seat
that did not build the instrument. Their reason, kept because it is the design
argument: *answering them separately invites two incompatible patches.*

## Status

**Stage 1 (tokenizers) RUN. Stages 2-3 need weights and are not run.** Findings
live in this README and nowhere else.

# FINDING — the rule is not missing, it is STARVED, on 159 of 160 tokenizers

    thousands  `,` between digits    emitted ALONE 159/159    intra_word fires 0
    decimal    `.` between digits    emitted ALONE 159/159    intra_word fires 0

**Zero exceptions.** Every tokenizer in the roster hands `twp.intra_word` a bare
`','`, and the test it fails is the first clause of its own last line:

    return len(tok_str) > 1 and tok_str[1].isalnum()

## THE CONSEQUENCE FOR THE V4 RULE, WHICH IS THE POINT OF MEASURING IT

**A LONGER LIST OF INTRA IDS CANNOT FIX THIS.** The current rule unmasks 7
hand-listed contraction ids; the obvious patch is to add `,` and `.`. That patch
cannot work, and 159/159 is why: **there is no `,000` token for a list to
contain.** The separator arrives alone in every tokenizer measured, so no
membership test on token ids has anything to match, whatever is in the set.

The fix has to read what comes AFTER, which is the thing `intra_word`'s own
docstring says the expansion does not have:

> *a tokenizer that emits the punctuation as its OWN token gives us nothing to
> look ahead to, so `3` `.` `14` still breaks.*

So the v4 requirement is **lookahead in the expansion**, not a character class
and not a wider allowlist. @malign, that is the difference between a one-line
change and a change to when the mask is applied, and it is why this was worth
measuring before writing.

## AND THE 24 THAT FAILED WERE NOT A RANDOM 24

The first sweep loaded 136 and failed 24, which would have been reported as
**136/136 unanimous**. The failures were 23 `StrictDataclassFieldValidationError`
plus one other -- **the transformers-5 validation split, i.e. the `tf457`
cohort**, which this repo keeps a second venv for precisely because no single
transformers satisfies the roster.

Re-run under `.venv-tf457`: **23 of 24 recovered, all 23 emitting the separator
alone, `intra_word` firing on none.** Same answer, so the result did not change --
**but 136/136 would have been a statement about the venv wearing the clothes of a
statement about tokenizers**, and the subset it dropped was selected by exactly
the property under test. One model remains unreachable and is a row with a
reason in `results/`, not an absence.

    results/by_tokenizer.csv         160 records, 136 loaded    .venv
    results/by_tokenizer_tf457.csv    24 records,  23 loaded    .venv-tf457

## MONOTONICITY: NO, AND IT NEEDS NO MEASUREMENT

`$100,000` and `$100` both cut to `100`; `$95,000` cuts to `95`. **Two different
salaries collide on one surface, and ordering surfaces by value does not order
the salaries.** So a gender or class contrast computed on cut surfaces can
reverse in sign. That is a property of the cut, provable rather than measured,
and it is what decides whether `salary_probe`'s G and C mean anything.

## WHAT STAGE 1 DOES **NOT** ANSWER — the CJK arm

`cjk_comma` and `cjk_stop` columns are in `results/` and **they do not answer the
CJK question.** Full-width `，` `。` are not in the intra set and should not be --
they genuinely end a word -- so `intra_word` firing 0 times on them is correct
behaviour and says nothing. **The CJK question is whether `boundary_mask` marks
them**, which takes the MODEL's vocab size, not the tokenizer's; substituting
`len(tok)` would be the model-vs-tokenizer vocab conflation this project has
already booked. **So the two arms are not symmetric in cost: the numeric arm is
answerable without weights and the CJK arm is not.** Stage 2.

## The question, in the four parts the commission asked for

    1  how much mass does the cut MOVE, per model, across the roster's tokenizers
    2  is the truncation MONOTONE
    3  does a numeric-intra rule fix it WITHOUT touching non-numeric prompts
    4  the CJK mirror, measured in the same folder

**On (2), the answer is available by construction and is NO.** `$100,000` and
`$100` both cut to the surface `100`, while `$95,000` cuts to `95`. So ordering
surfaces by value does not order the underlying salaries, two different salaries
collide on one surface, and **a contrast computed on cut surfaces can reverse in
sign.** That is a property of the cut, not a measurement of it; what needs
measuring is how much mass sits where it bites.

**On (3), the precedent sets the bar.** `hyphen_intra` measured NULL when it was
adopted -- 0 of 30 prompts fired, 0 of 2,562 words moved -- **and that null is
what made it safe.** A numeric rule that moves non-numeric prompts is not the same
kind of change and should not inherit that licence.

## Why this is a calibration and not a registration

It measures how an instrument behaves; it makes no claim about what alignment
does. **But the honest tell in `experiments/README.md` is *if you can name an
outcome you would rather see, register*, and I can name one**, so it is recorded
here rather than left implicit: a large, non-monotone cut makes the v4 rule
necessary and makes my own `salary_probe` amendment A1 load-bearing; a small one
means `salary_probe` was never as blocked as I said. **I would rather be right
about A1 than have the experiment unblocked**, which is the wrong preference to
have and is the reason it is written down.

No hypothesis is registered. The numbers decide the rule, and the rule is
@malign's to implement.

## Stage 1 — the tokenizers, no weights loaded

`python run.py --stage tokenizers` → `results/by_tokenizer.csv`

Asks of each roster tokenizer, without ever loading a model: **does it emit the
separator as its own token?** That is the condition `twp.intra_word` cannot
survive, and its docstring says so:

> *LIMIT, declared rather than hidden: a tokenizer that emits the punctuation as
> its OWN token gives us nothing to look ahead to, so `3` `.` `14` still breaks.*

**So the rule already exists at character level** -- `intra_word('150,000',
',000')` is `True` -- and the question is entirely whether the tokenizer ever
hands it a token it can act on.

## Stage 2 — the mass, weights required, NOT RUN

Per model, the share of probability mass at a numeral-eliciting prompt that sits
on a cut surface, and what `score_words` returns for the full numeral named
directly. `score_words` is the route that may reach this WITHOUT any v4 change:
it is handed a target and walks its token path rather than discovering a surface
and stopping at a boundary, and `clean_surface('150,000')` round-trips. Unrun.

## Stage 3 — does the rule move anything it should not, NOT RUN

The `hyphen_intra` comparison: the candidate rule on and off, over non-numeric
prompts, counting words moved. The number that matters is the one that should be
zero.
