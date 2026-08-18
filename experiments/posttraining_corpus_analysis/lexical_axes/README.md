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

# THE LIMIT IS GENRE, NOT GRAIN -- M06 ALREADY MEASURED THE GRAIN TRANSFER

A3 recorded this test as crossing two grains -- `twp_words` next-token
probabilities against bag-of-words counts -- and treated that as the reason the
null is weak. **That is wrong, and M06 had already measured it.**

`meta/M06_generation/findings/p_on_passages.md` (producer `m06_p_on_passages.py`,
232,384 passages, 41 pairs):

    same prompts, same models, both grains   Spearman +0.500   n=600 words
    canonical-vector context                         +0.444    n=3,613
    page classifier, real minus null mean    0.387 - 0.499     k=25..200

> *"Half the distributional ranking survives temperature-1 sampling and ~200
> tokens of autoregression, on identical prompts and models: grain is the only
> thing that varies."*

**So the vector DOES survive the trip from distribution to running text.** What it
does not survive here is the move from FICTION CONTINUATIONS to ASSISTANT PROSE
about laundering money.

**And that failure is already on record in this collection.** `pku-safe-rlhf` A2
probed three bge refusal centroids against PKU responses and found the responses
sat FURTHER from the refusal centroids than generic English did, because "the
spans are erotic-fiction refusals, the responses are assistant prose about
bribery, and **the genre gap swamps the speech act**." Two instruments, same
boundary.

**The properly specified null: the alignment axis is legible across grains within
a genre and does not reach assistant prose.** That is a sharper and more useful
claim than "the axes are unrelated", and it predicts where a transfer WOULD work
-- a preference corpus of narrative text, which none of the five is.

M06's finding is `status: draft`, `grade: ungraded`, single pass, and not
audit-grade until a second seat reproduces it. Quoted with that fence.

