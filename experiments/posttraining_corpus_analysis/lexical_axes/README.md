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

**Monotone in how un-aligned the weaker generator is**, which is the ordering the
structural account predicts. **Held loosely: the base cell is n=330 with an
interval containing 0.5, and the gradient spans 3 points.** The powered
comparison is SFT-only against both-chat. The structural argument carries this,
not the gradient.

## WHAT THAT MEANS BEYOND THIS TEST

**A base-vs-aligned instrument cannot be evaluated on preference data, in
principle.** Preference corpora record choices BETWEEN aligned outputs; they hold
no base-arm text to contrast against. Any future attempt to read alignment's
lexical operation off a preference corpus meets the same wall, and it is a
property of what preference data IS rather than of any particular corpus or
instrument.

**This supersedes A4's genre account**, which was true but not the binding
constraint: even a preference corpus of narrative text would still contain only
aligned-arm responses.

# SUPERSEDED: THE GRAIN AND GENRE ACCOUNTS

M06 established the grain transfer is solved -- `p_on_passages.md`, Spearman
+0.500 (n=600) and +0.444 (n=3,613) from `twp_words` to running text, page
classifier real-minus-null 0.39-0.50 across 232,384 passages. So grain was never
the limit. Genre is real but is downstream of the structural point above.

