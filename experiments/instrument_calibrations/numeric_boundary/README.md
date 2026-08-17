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

# FINDING 2 — the CJK arm: the RIGHT SET consulted with the WRONG KEY

**And it needed no weights after all.** My first note here said the CJK arm needs
`boundary_mask`, which takes the model's vocab size, so it needs a load. Wrong on
the consequence: `boundary_mask(tok, n)` needs a tokenizer and an **integer**, and
the predicate it applies to each id is four lines that can be asked of the eight
tokens actually present. **Stage 2 is free too, and I said it was not.**

    133 models carry CJK punctuation tokens
     49  ALL marks correctly boundary        SentencePiece family
     84  NONE marked boundary                byte-level BPE -- 63%
      0  PARTIAL
     24  have a token GLUING punctuation to the following word

## `，` IS IN `PUNCT`. THE SET IS NOT THE PROBLEM.

`PUNCT` is a 47-member set and it contains `，。！：、；？` -- every mark tested.
**So the diagnosis at [6420], that full-width marks "are NOT boundaries", is right
about the effect and wrong about the cause**, and the difference decides the fix.

`boundary_mask` tests `s[0]` of the token **as the tokenizer represents it**, and a
byte-level BPE represents `，` as `ï¼Į`:

    Llama-3.1-8B   raw 'ï¼ĮåĽłä¸º'   decoded '，因为'   boundary FALSE
    Qwen2.5-7B     raw 'ï¼Į'         decoded '，'       boundary FALSE
    Mistral-7B     raw '，'           decoded '，'       boundary TRUE

**The correct set, consulted with the wrong key.** Adding members would change
nothing; the lookup never sees a CJK character at all.

**ZERO PARTIAL IS THE CONFIRMATION.** Not one model gets some marks right and
others wrong. It is all-or-nothing per model, which is the signature of a
tokenizer-family property rather than a per-token accident — and it means the
49 that pass are not lucky, they are SentencePiece.

## THE TWO ARMS NEED DIFFERENT REPAIRS, WHICH IS THE OPPOSITE OF WHAT WAS EXPECTED

@malign held the implementation until this was measured, on the reasoning that
*"a lookahead built for the numeric case alone would be the second incompatible
patch on one classifier."* Right to hold, and the measurement says the arms
diverge:

    numeric  the separator IS its own token, and the rule needs to see the
             NEXT token                              -> LOOKAHEAD
    CJK      the separator is its own token too, and the rule needs to decode
             it before testing                       -> DECODE BEFORE THE LOOKUP
    glued    `，因为` is punctuation AND a word in one token, on 24 models
             -> NEITHER REPAIR REACHES IT. No boundary FLAG can represent a
                token that both ends a sentence and begins the next word.

**So they are one question and not one patch.** A context-reading boundary rule
is still the right shape, and it has to do two different things at two different
points, with a residual on 24 models that neither addresses.

## WHAT STAGE 1 DOES **NOT** ANSWER — superseded, see FINDING 2

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

## HOW MUCH DO THE GLUED 24 MATTER — 6.62% OF TOKENS, AND THAT IS EXPOSURE NOT DAMAGE

@malign's [6433] calls the glued case a limit of the boundary-mask abstraction
rather than a bug: it assigns one bit per token and a token that is punctuation
AND a word needs two, since `term = row[b].sum()` is a sum over a boolean mask.
Agreed. So the question left is how often the abstraction is asked to do the
impossible, measured on real stimuli rather than on the probe string.

413 declared Chinese prompts, 8 of the 24 affected models, tokenizers only:

    Aquila2-7B                  10.73%
    SmolLM3 / Llama-3.1 family   6.18%   (identical counts -- one tokenizer)
    pooled                       6.62%   712 glued of 10,762 tokens

**Roughly one token in fifteen on Chinese text.** Not negligible, and not a
corner case.

**BUT THIS IS EXPOSURE, NOT DAMAGE, AND THE DISTINCTION IS THE WHOLE CAVEAT.** A
glued token appearing in a tokenization is not the same fact as a glued token
carrying probability mass at a measured position. **This bounds how often the
abstraction is asked to represent something it cannot; it does not measure how
much any number moves.** That needs the store and is unrun. Quoting 6.62% as an
error rate would be the exposure-for-damage substitution this campaign books.

## QUALIFICATION FROM @dario [6434] — THE CJK DEFECT DOES NOT REACH THE SURFACES

**This section corrects the reach of FINDING 2 above, which overstates it.**

@dario measured the store rather than the tokenizer, and checked coverage FIRST
so the result is a negative and not an absence:

    surfaces in twp_words matching [，。！：、；？]        ZERO
    CJK prompts in twp_words                              416
    models with CJK word rows                             160
    CJK word rows                                   9,143,461
      meta-llama/Llama-3.1-8B   64,979   <- byte-level, one of my 84
      Qwen/Qwen2.5-7B           51,245   <- byte-level, one of my 84
      mistralai/Mistral-7B-v0.1 60,776   <- SentencePiece, one of my 49

**The affected models have deep CJK coverage and produce no punctuation-bearing
surfaces.** Top Llama-3.1-8B surfaces on a CJK prompt are clean words -- `手`
`挣扎` `还是` `眼睛` `封信`.

**So the mask defect is REAL and does not manifest in the word surfaces**, and my
6.62% glued-token figure is further from damage than even the exposure caveat
said. Neither @dario nor I know why; the untested candidate is that CJK
segmentation runs off `data/dict/` rather than off the boundary mask, so a mask
failure cannot produce a glued surface. **Nobody has read that path and I am not
guessing at it here.**

### WHERE THE DEFECT COULD STILL BITE, AND IT IS A TESTABLE PREDICTION

The mask does not only split words -- **it feeds `term = row[b].sum()`.** A mask
that marks nothing as a boundary for a CJK word sums over a near-empty mask, so
boundary mass is under-counted and `p` is depressed without any surface looking
wrong.

@malign's path-aggregation null ruled OUT enumeration as the cause of the CJK
`score_words`/`expand` gap, leaving *"the boundary term or the beam"* [6401]. This
folder has now measured a boundary-term defect that is CJK-specific and
all-or-nothing by tokenizer family. **@dario's test, which is the right one:
does the `score_words`/`expand` CJK gap split 49/84 the same way?** If the
SentencePiece models show no gap and the byte-level ones do, the boundary term is
the cause. **Unrun; it needs weights.**

## SYNTHESIS FROM @malign [6435] — THE CAUSE AND A SYMPTOM FOUND SEPARATELY, SAME DAY

**This supersedes the qualification above on the question of whether the defect
manifests. It does. Not as a glued surface — as DOUBLE-CREDITING.**

`，` id 12831 is in **neither** set:

    static PUNCT lookup   MISSES it   byte-level hands the mask `ï`  (this folder)
    cjk_vocab `cids`      MISSES it   so the dictionary branch never reaches it

So it survives every layer as a **continuation**. And `_account` continues only
through NON-boundary tokens, so `expand` walks straight through it:

    一个   [43340]           '一个'
           [43340, 12831]    '一个，'  -> clean_surface STRIPS the comma
                                       -> credited to 一个 A SECOND TIME

**That closes @dario's negative rather than contradicting it.** No glued surface
appears in `twp_words` because `clean_surface` strips the punctuation before the
surface is keyed. The defect does not store `一个，`; **it stores `一个` twice.**
Clean surfaces, unclean arithmetic.

**@malign found the symptom this morning (`54102a9`, multi-depth crediting) and
this folder found the cause this afternoon, and neither of us saw they were one
thing.**

### BOTH PROPOSED MECHANISMS FOR THE DAMAGE WERE WRONG, INCLUDING THE ONE IN THIS FILE

@dario proposed, and I recorded above, that a near-empty mask starves `term` and
depresses `p`. **Backwards, measured:** a CJK surface's mask marks **48,171 of
49,152 ids (98%)**, because the dictionary branch sets `b[cids] = ~inside`.
`term` is not starved at all.

### AND THE 49/84 TEST CANNOT WORK — STRUCTURAL, NOT A POWER PROBLEM

`score_words` and `expand` both call the **same** `_boundary_for`, so a mask
defect hits both identically and **cancels in their comparison.** That gap is
already attributed to multi-depth crediting plus 1.2e-03 batching.

**The mask defect is invisible instrument-to-instrument and real in ABSOLUTE
values** — which is the harder kind to see, and the reason it survived a day of
two seats looking directly at it.

### WHAT THE FIX WOULD DO IS NOT OBVIOUSLY SIGNED

Marking `，` terminal **stops** the depth-2 credit and **adds** its mass to `term`
at depth 1. Mass moves between accounting routes rather than appearing or
vanishing, so the net effect on a word's `p` depends on the row at each depth.
**Measurable on the 6 of 162 keys where it fires, and to be measured before the
fix is adopted rather than after.** Unrun.

# FINDING 3 — `generate` WALKS PAST BOTH BLOCKERS. The limits are twp's, not the model's.

`--stage beam`. SmolLM2-360M base + Instruct, all 30 `domain == 'class'` prompts
(20 en, 10 zh), 100 samples of 10 tokens at temp=1. **6,000 samples.**

    46,204,000    811,387.54    52,948,650    146,594.68    650,000.00

**Ten-plus characters, past the comma that terminates the word AND past
`MAX_DEPTH` 6.** 4,621 of 6,000 carry a thousands comma.

    boundary rule   `,` terminates       -> `expand` cannot DISCOVER $100,000
    MAX_DEPTH 6     8 tokens             -> `score_words` REFUSES it  ([6440])
    generate        consults NEITHER     -> the model writes it

**Both blockers are properties of the twp EXPANSION, not of the model.** @malign
had recommended restricting to the 40 models where the string fits and withdrew
it on this: *"that accepts a limit that is not the model's."* **The `MAX_DEPTH`
change is not needed for the salary question** and it is the most expensive item
on the v4 table.

## THIS IS NOT A FREE WIN — THE ESTIMAND CHANGES

    twp        EXACT next-token distribution, calibrated, commensurable with
               984,857 stored cells
    generate   SAMPLED, n=100 per prompt, commensurable with NOTHING in the store

For a median, an IQR or a gender gap, sampling at n=100 is the ordinary
estimator. **For anything that must sit beside a stored `p` it is useless.** The
failure mode to guard is a number from one arriving in a sentence with a number
from the other.

## THE ENCODING SPLIT, AND WHY THE FIRST FLAG WAS WRONG

My first pass used one `has_separator` boolean, which counted `5401.00` -- a
DECIMAL, not a thousands separator -- and scored `88K` as a bare truncation when
it is the most compact way to write eighty-eight thousand. Re-parsed by encoding:

    en  n=4000   comma 91.7%   bare  5.5%   decimal 2.3%   K 0.3%
    zh  n=2000   comma 47.7%   bare 40.3%   decimal 7.8%   K 1.1%

**In Chinese the model writes `57900` where in English it writes `57,900`.** So
**the truncation defect's severity is LANGUAGE-DEPENDENT** -- there is often no
separator to truncate at -- while `MAX_DEPTH` bites the same, because the numeral
is multi-token either way. **The two blockers do not co-occur at the same rate
across languages.**

**An 88-tokenizer sweep says what a tokenizer CAN do; this says what a model
DOES**, and they are not the same population.

## OPEN AXIS, @malign's [6442], NOT MEASURED

**Language is not randomly assigned across this roster.** Chinese-heavy models
are a family cluster -- Yi, Qwen, InternLM2, Baichuan2, CT-LLM, MAP-Neo, GLM4,
MiniCPM -- so a defect that bites less in Chinese **bites less on a set of models
selected by provenance**, which correlates with training corpus and with
alignment regime. That is a confound in any cross-family comparison of numeric
prompts and is invisible to a per-tokenizer count and to a per-prompt magnitude
alike.

**Unmeasured, and it may be small.** This arm is ONE family, so it cannot speak
to it at all. Recorded as an open axis rather than left to be discovered later.

# FINDING 4 — the DEPTH arm: a second blocker, and @malign's untested caveat does not bite

`--stage depth`, no weights. 136 tokenizers, `twp.MAX_DEPTH` is 6.

    ALL targets fit            67
    at least one exceeds       69

**`$100,000` token counts: {4: 64, 5: 3, 8: 69} — BIMODAL.** Models either hold
multi-digit tokens or split digits singly, with almost nothing between. **That is
the evidence for @malign's digit-tokenisation-policy hypothesis**, and it is
stronger than a median: a policy split produces two modes, a continuous cause
would not.

## VOCABULARY SIZE DOES NOT PREDICT IT — REPLICATED, AFTER MY OWN BUG SAID OTHERWISE

    $100,000   vocab>=100k median 8.0 (n=72)  |  vocab<100k median 8.0 (n=64)
    $95,000                     7.0           |                    7.0
    $50,000                     7.0           |                    7.0

**@malign's null replicates.** My first run printed 8.0 against 7.0 and I nearly
had a contradiction: the summary line compared `$100,000` in the high-vocab group
against **`$95,000`** in the low-vocab group. **Two different strings, one label.**
Caught by the numbers being interesting, which is the wrong reason to catch
something.

## THE ASSUMPTION @malign FLAGGED AND DID NOT TEST: IT HOLDS

Their argument that infeasibility costs n rather than validity depends on a
lineage's two arms sharing a tokenizer, so an unfittable string removes whole
lineages instead of biasing a within-lineage contrast. They named Tanuki as a
counterexample -- 65,024 against 65,001 -- and said it *"needs checking per pair
rather than asserting."* Checked, on all 50, **by comparing the TOKENISED RESULT
rather than the vocab size**:

    arms AGREE      44
    arms DIFFER      0
    unmeasurable     6   (an arm whose tokenizer would not load)

**Zero.** Tanuki's arms differ in vocab size and tokenise these strings
identically, so the counterexample is real about vocabularies and does not reach
the probes. **The costs-n-not-validity argument stands on all 44 measurable
pairs** -- and it stands because it was checked on the quantity that matters
rather than on the one that was easy to compare.
