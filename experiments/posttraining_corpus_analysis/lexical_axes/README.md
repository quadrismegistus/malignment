# lexical_axes — does the model's alignment axis predict corpus preference?

**id:** lexical_axes **status:** step D run from `run.py`. **RH's prediction
(FAIL or NARROW PASS) CONFIRMED on the corrected vector.** One claim withdrawn
(A3). Registration `6625ec2`, A1-A3.

# THE RESULT: FOUR FAIL, ONE NARROW PASS

Zero free parameters. The word vector comes entirely from
`meta/M01_displacement/results/k/word_auc_en.tsv`; nothing is fitted on any
corpus, so overfitting is unavailable as an explanation.

    population        raw score   LENGTH alone   rho(score,len)   LENGTH-NORMALISED
    hh-harmless          45.2%        42.1%          0.843            50.8%  FAILS
    hh-helpful           56.0%        58.8%          0.856            50.1%  FAILS
    pku-unsafe           46.9%        45.0%          0.751            50.9%  FAILS
    pku-mixed            45.0%        38.5%          0.769            54.9%  NARROW
    ultrafeedback        53.3%        54.7%          0.917            47.8%  FAILS

**The raw score was LENGTH.** It correlates with token count at rho 0.75-0.92,
length alone predicts as well or better in four of five, and matched to within 20
words the raw score sits at 50.6 / 50.3 / 50.5 / 54.0 / 47.5 -- chance.

Removing the declared assistant-register words changed nothing (within 0.7pp
everywhere), so the register confound A2 guarded against never arose. **The
confound that did arise was the one A2 did not name.**

# A3 CORRECTION: THE "NO NEGATIVE POLE" CLAIM WAS MY OWN FILTER

An earlier version of this file reported that the model-side vector has no
base-leaning pole, and offered that as independent corroboration of `U_ladder`'s
removal-stops gradient. **Both are withdrawn.**

`k_word_auc.py` line 227 computes `roc_auc_score(y, C[:, j])`, so **auc is
DIRECTIONAL** -- below 0.5 is base-leaning -- and the script's own effect measure
is `abs(auc - .5) > .15`, two-sided. The first run filtered `auc > 0.568` and so
**deleted all 2,013 base-leaning words**, then reported their absence.

    4,106 words | 2,013 BELOW 0.5 | 2,087 above
    most base-leaning: went .104, told .110, KILL .112, put .118, get .122,
                       threw .126, go .137, say .151, know .159   (n_models 92)

`kill` sits at 0.1115 on the full 92-model roster. **M01's displacement is in the
vector exactly where it should be.** `run.py` now carries a refusing assert,
because a one-sided vector produces entirely plausible output.

# THE RESULT STANDS ON THE CORRECTED VECTOR

`python run.py --predict`, weight = `auc - 0.5`, |effect| > 0.10, 1,618 words
(888 aligned-leaning, 730 base-leaning).

    population        raw    DENSITY   rho(raw,len)   len-matched      verdict
    hh-harmless     56.9%      51.0%        -0.888         51.6%       FAILS
    hh-helpful      44.4%      51.5%        -0.883         51.4%       FAILS
    pku-unsafe      51.7%      49.6%        -0.422         48.5%       FAILS
    pku-mixed       58.4%      53.4%        -0.488         51.6%       NARROW
    ultrafeedback   49.8%      52.2%        -0.514         51.1%       FAILS

**RH's pre-registered prediction -- FAIL or NARROW PASS -- holds on the corrected
vector.** Four fail, one narrow.

**The raw score is still length, now inverted.** rho runs -0.42 to -0.89 because
the base-leaning words are high-frequency (`went, told, get, go, say, know`), so
a longer text scores more negative. The registered statistic is the per-token
mean and the length-matched replicate sits at 48.5-51.6% throughout.

Two raw figures flipped sign under the correction -- hh-harmless 45.2% -> 56.9%,
hh-helpful 56.0% -> 44.4% -- which is what a deleted pole does and is why the
first run's numbers should not be cited.

# THE REAL LIMIT (RH): THERE IS NO BASE-GENERATED ASSISTANT PROSE

**A4 said the limit is genre. It is narrower and more structural than that.**

The vector is a BASE-vs-ALIGNED contrast. **Base models do not produce assistant
prose at all** -- there is no base-arm version of "I'd be happy to help with
that." And every response in every preference corpus comes from an
instruction-tuned generator: Alpaca variants in PKU, Anthropic's models in
hh-rlhf, llama-2-chat / wizardlm / falcon-instruct / gpt-4 / bard in
UltraFeedback.

**So both sides of every pair sit on the aligned pole, and the axis is asked to
discriminate inside a region where one of its poles cannot occur.** The null was
structural. It was not available to be discovered.

## THE ONE EXCEPTION, AND IT POINTS THE RIGHT WAY

UltraFeedback's generator list contains `pythia-12b`, a base model, on **268 of
~80,000 completions (0.3%)**, plus `alpaca-7b` and `starchat` which are SFT-only
with no preference stage. `python run.py --basepole`:

    stratum                    n     accuracy   95% CI            p
    base on one side          330      54.8%    [0.493, 0.603]   0.088
    SFT-only on one side   11,744      54.0%    [0.531, 0.549]   4.4e-18
    both chat/instruct     46,993      51.7%    [0.513, 0.522]   3.6e-14

**WITHDRAWN AS CORROBORATION (A6, RH).** Pythia is the campaign's outlier for how
LIGHT its alignment is, so the "base on one side" cell is built on the one family
where the contrast being tested is known to be near-absent:

    all 53 ladder edges      median JS 0.1087
    pythia-6.9b base>pref              0.0190   25th percentile
    archangel sft>pref                 0.0030    2nd percentile
    all six pythia edges          0.0030-0.0190  bottom quartile
    their faller shares           0.000-0.060    against U's 49.3% median at base>sft

**Pythia's whole base-to-preference edge moves about a sixth of the median edge
and removes essentially nothing.** So the stratum is not a test of "the base pole
present"; it is a test on the checkpoint family least marked by the axis. Already
underpowered at n=330 with an interval containing 0.5, and now on the wrong
exemplar.

**The structural argument stands entirely without it.** It does not need a
gradient: the composition fact -- 0.3% base-model completions, both sides of
every pair aligned -- is the whole of it.

## THE "IN PRINCIPLE" CLAIM IS WITHDRAWN (A7, RH)

An earlier version said a base-vs-aligned instrument cannot be evaluated on
preference data **in principle**. **That is wrong, and RH's objection is the
decisive one: preference data is how base models BECOME aligned models.**

The error was conflating two relations. "The corpus holds no base-arm text" is
about TEXT CLASSIFICATION -- can the axis tell base-written from aligned-written
prose. That was never the relevant question. **Preference data does not contain
the base pole; it specifies the direction of travel away from it.** If alignment
moves probability from `kill` to `scream` and the corpus rewards responses with
less `kill` and more `scream`, corpus direction and model movement agree, with
every response coming from an aligned generator throughout.

**So what survives is a POWER argument, not a structural one**: the
chosen-vs-rejected variation may be small relative to the base-to-aligned
distance, leaving the axis little to grip. That is empirical and checkable, and it
is a much weaker claim than the one it replaces.

**And the relation should if anything be STRONGER than correlation.** For a model
actually trained on corpus C, C is causally upstream of that model's axis. The
proper test is therefore not "does the corpus contain base text" but:

    take a model trained on C, compute its own base->aligned word movement,
    and correlate that against C's chosen-vs-rejected word deltas

UltraFeedback has several such students in the roster with base counterparts --
`OLMo-2-0425-1B-DPO`, `OLMoE-1B-7B-0125-DPO`, `Llama-3.1-Tulu-3-8B-DPO`,
`zephyr-7b-beta`. **That test needs cells and is the one worth queueing**; it is
also the version that does not repeat A9's category error, because the causal
claim is licensed by the training relation rather than assumed from resemblance.

# SUPERSEDED: THE GRAIN AND GENRE ACCOUNTS

M06 established the grain transfer is solved -- `p_on_passages.md`, Spearman
+0.500 (n=600) and +0.444 (n=3,613) from `twp_words` to running text, page
classifier real-minus-null 0.39-0.50 across 232,384 passages. So grain was never
the limit. Genre is real but is downstream of the structural point above.


# --genvector: THE SAME NULL FROM A SECOND, INDEPENDENT VECTOR

RH's design, and the control is the DESIGN not the prompts: **same prompts, same
n, two arms.** `run.py --genvector`, unforced NARR passages from
`malign_logits.gen_sequences`, 42 base/aligned pairs, 607,902 word cells.

    rate(w, pair, arm) = count / tokens        NORMALISED WITHIN ARM FIRST
    delta(w, pair)     = rate_aligned - rate_base
    weight(w)          = share of pairs with delta > 0, minus 0.5
    unit               = THE PAIR (42), not the row

Three vectors from one contrast, partitioned by prompt stratum, on a shared
3,416-word comparison vocabulary.

    population       vector    acc    len-matched   verdict
    hh-harmless      MARKED   52.6%      52.3%      FAILS
                     UNMARKED 51.3%      51.4%      FAILS
    hh-helpful       MARKED   50.9%      51.0%      FAILS
                     UNMARKED 52.4%      52.1%      FAILS
    pku-unsafe       MARKED   50.9%      49.7%      FAILS
                     UNMARKED 49.8%      49.0%      FAILS
    pku-mixed        MARKED   57.2%      56.3%      NARROW
                     UNMARKED 54.5%      55.1%      NARROW
    ultrafeedback    MARKED   51.8%      51.1%      FAILS
                     UNMARKED 52.5%      51.8%      FAILS

**MARKED minus UNMARKED runs +0.9, -1.1, +0.7, +1.2, -0.7 -- ±1.2 points with an
inconsistent sign. The transgression stratum changes nothing.**

**AND THE DENSITY CONSTRUCTION IS NOT LENGTH-CONFOUNDED**, unlike the twp vector:
matched and unmatched agree to within 0.6pp everywhere. Normalising within arm
before differencing is what did that.

## WHY THIS MATTERS MORE THAN THE FIRST NULL

The twp vector and this one are **independently derived from different substrates**
-- next-token distributions at fixed sites against running text at 256 tokens --
and they agree: near chance everywhere, `pku-mixed` the lone narrow pass at
54.9% (twp) and 55.6% (generations). **A null replicated across grains is worth
more than either null alone.**

`pku-mixed` is the stratum where one response is LABELLED safe and the other
unsafe rather than both graded. Aligned-register density tracking the labelled-safe
response there is close to tautological and is reported, not interpreted.

## THE STRATA ARE NOT A CLEAN TRANSGRESSION CONTRAST, PER RH

MARKED/UNMARKED are NOT minimal pairs: **a one-word swap changes the scene, and
the transgressive half was agent-written and is bland.** They are strata that
differ in transgressiveness on average. The question they answer is only whether
that difference changes the result. It does not.

**What this therefore cannot say:** that transgression is irrelevant to the axis.
Only that this particular stratification, on this corpus, moves nothing.

## WHAT IS NOT AVAILABLE, AND IT BOUNDS THE WHOLE APPROACH

Generation space is **NARR-only**: 144 prompts / 180,448 unforced rows in
`passage`. Every other slot lives in `beam_fc` at TEN TOKENS (unusable for word
counts) or at n<=14. `INDIV`/`INST` has no passage generations at all.

**So the slot axis -- the campaign's live construct -- cannot be studied in
generated text**, and neither can the F21 institutional contrast. Testing either
needs new generations at passage length, which is a run and not an analysis.
