---
subject: contextual_norms
status: Chinese arm opened; comparability characterised, not established
---

# Contextual norms: the POS pass, the rating manifest, and the Chinese arm

Three producers, one dependency chain:

    pos_pass.py       contextual POS for every (prompt, word) in twp_words_v4
    priority.py       what to rate next, filtered by that POS
    rate.py           runs the v6 instrument over a manifest tier (was rate_zh.py)
    rebuild_tables.py repairs the POS tables the interrupted run damaged

**This folder commissions the ratings; it does not analyse them.** The consumer is
`experiments/displacement/named_under_dose/predict.py`, which reads them through
`fields.contextual_norms`. Two defects found there sent work back here and are the
reason the manifest looks the way it does now -- see section 5.

## 1. THE POS PASS

`pos.get_pos(words, prompt)` over **2,751,990 (prompt, word) pairs** in
`twp_words_v4`, en then zh, warming the stash and writing
`~/malignment-data/contextual_norms/pos_{en,zh}.csv.gz`.

    en  1,958,577 pairs   VERB 979,107 (50%)   content 86%
    zh    793,413 pairs   VERB 406,294 (51%)   content 84%

**Why it exists.** `priority.py` filtered ratability on BARE words via
`is_function_word`, which is the unreliable path -- spaCy alone calls `strangle` a
NOUN and `the` a PRON -- and it left `"` atop the Chinese tier and `out`/`back` in
the English one. Contextual POS is the correct filter and is the SAME decision
`named_under_dose --verbs-only` makes, so the manifest cannot commission ratings the
analysis then drops.

Two hazards recorded rather than fixed. `pos.tagger_id` reads `nlp.meta["name"]`,
which is `core_web_sm` for BOTH models, so the stash cannot distinguish an English
tag from a Chinese one; it is safe only because the prompt sets are disjoint. And
the first run died on a refused ClickHouse connection at 1,250/2,612 prompts --
`q()` now retries with backoff and re-raises after the last attempt.

**The resume damaged its own output tables**, in two ways neither of which showed as
an error: the English table gained ~1.02M duplicate rows, and the Chinese table had
4-column rows appended to a 3-column smoke-test header, so `DictReader` misparsed
every real row and the file read as **1% VERB against the run's own 406,294**. The
tell was the file totals disagreeing with what the run printed. `rebuild_tables.py`
rebuilds positionally with the POS field validated against the UPOS set; the
damaged originals are kept as `*.DAMAGED.csv.gz`.

## 2. THE MANIFEST

**96,221 rateable VERB pairs** over 2,166 prompts, ranked by tier then by how many
lineages the pair moves on.

    tier 1  zh                10,804 pairs    382 prompts   1,664 words
    tier 2  en high-dose      34,304          569           2,289
    tier 3  en general        51,113        1,215           2,419

Full English coverage would be ~480,000 unrated pairs, about 22x what exists, and it
is the wrong target: most of the tail moves on one lineage and carries a single noisy
label. The ordering is by what a rating would RESOLVE. The headline the ratings were
wanted for is already settled -- see `named_under_dose` -- so tier 2 exists because
the DOSE conditioning is not, and the instrument under-covers exactly the loaded
frames the question needs.

## 3. THE CHINESE ARM, AND A CLAIM I GOT WRONG

An earlier version of `priority.py` said the Chinese arm was BLOCKED because
`SlotRatingENv6` is "English-only by name and by content". **That was inferred from
the class name and from `slot_prompts()` containing no CJK, never tested, and it is
false.** The name described the corpus the task had been run on, not a constraint on
what it can rate.

`rate.py` ran the unmodified instrument over tier 1: **10,666 pairs, 380 prompts,
0 errors**, written to `experiments/slot_ratings/results/v6zh/` so `_slot_index`
registers them as a SEPARATE instrument -- Chinese content rated with English glosses
is a different measurement from English v6 until someone shows otherwise, and
`contextual_norms(prompt, instrument="v6zh")` selects them deliberately.

    slot_prompts():  916 prompts, 382 with CJK   (was 534 / 0)
    v6zh:            10,804 rows, 7,724 ratable (71%)

### The comparability check, and what it found

Raw, the Chinese ratings look shifted: `fit` -1.18 and `mundanity` -0.92 against
English, and ratable 71% vs 91%. **It is segmentation, not drift.**

    chars      n     ratable%     fit     mundanity        EN v6:  91%  5.80  4.25
    1       4,024       42%       3.10      2.69
    2       6,393       89%       5.47      3.68
    3+        387       92%       6.28      4.21

Multi-character segments match English almost exactly. The gap is carried entirely by
single-character jieba segments -- bound morphemes that genuinely do not form a
coherent action, which is what the rater says about them in its own `reading` field:
*"the sentence is incomplete and the word `为` does not form a coherent action"*.
Excluding fragments, `fit` -1.18 -> -0.28 and `mundanity` -0.92 -> -0.54.

**Two DIFFERENT scales then grow**, and these are not explained:

    interiority   EN 1.75   ZH 2.78   +1.03
    deliberation  EN 1.35   ZH 2.07   +0.72

Plausibly vocabulary composition -- disyllabic Chinese verbs lexicalise mental states
(`了解`, `知道`, `考虑`) where English slots draw action verbs -- but that is a
hypothesis, not a measurement. **Consequence: no Chinese LEVEL goes beside an English
one on these scales.** Within-language contrasts are unaffected.

**What is NOT established is cross-language comparability**, and it cannot be
established from the data as it stands: `pair_id`, `kernel_id` and
`archive_prompt_id` all span ZERO cross-language groups, and all 457 zh prompts sit
in family `flat` beside 811 unrelated en ones. A matched study needs the
correspondence reconstructed first. Exact agreement is not the target; absence of
systematic offset is.

## 4. WHAT THE CHINESE ARM RETURNED

**These numbers are the RE-RUN after the leak in section 6 was fixed.** The first
version of this section quoted +0.1070 / +0.1189 / +0.0971 and claimed the named
ratings beat the embedding at low dose. Those were contaminated by `consistency`, a
function of the outcome, and are struck.

`named_under_dose/predict.py --lang zh --contextual v6zh --match-population
--verbs-only`, 89,917 shared cells, twelve scales named explicitly:

                        ctx_v6zh/trees          norms/trees          ratio
    POOLED         +0.0889 [.0843,.0952]   +0.0348 [.0136,.0664]     2.6x
    LOW dose       +0.0918 [.0808,.0976]   +0.0197 [-.0097,.0473]    4.7x
    HIGH dose      +0.0814 [.0705,.0855]   +0.0195 [.0019,.0371]     4.2x

**The grain finding is not English-specific, and it is the one result that has
survived every correction today.** Chinese word-level norms sit at zero -- one range
crosses it -- while the same vocabulary asked at the site is 2.6-4.7x that, ranges
disjoint at every stratum.

**The named-beats-embedding claim is DEAD, not merely withdrawn.** Clean:

    LOW dose   ctx_v6zh +0.0918 [.0808,.0976]   bge +0.0923 [.0760,.1063]   TIED
    HIGH dose  ctx_v6zh +0.0814 [.0705,.0855]   bge +0.0947 [.0462,.1255]   bge ahead

The leak was worth about +0.018 of fake signal, which was the whole of the apparent
win. Nothing here shows a named instrument beating a distributional one.

**Chinese dose is unresolved**: +0.0918 -> +0.0814, ranges just overlap. And unlike
English, the Chinese arm has NO dose-correlated coverage problem -- tier 1 took every
zh pair at k>=5, so zh was uniformly annotated from the start.

### Fences

- **The pooled headroom is NEGATIVE (-0.0103) and that is a POOLING ARTIFACT.** Within
  strata it is +0.0454 and +0.0459. Pooling inflates `log p_base` from ~0.68 to 0.7408
  because base probability correlates with dose, so the pooled fit gets
  between-stratum signal the stratified fits cannot. An earlier reading of mine
  treated the pooled line as "P's metric is undefined in Chinese"; it is defined and
  positive within strata.
- **The `% headr` column is not quotable.** Increments are measured up from the
  shuffle (~0.49) and the headroom from `log p_base` (~0.68), so the ratio exceeds
  100% routinely and reached 377% here. Read the raw increments.
- **The dose contrast is unresolved**, in Chinese as in English: ctx falls
  +0.1189 -> +0.0971 but the ranges overlap.
- **zh is 7 word-level norms against en's 12** (no Warriner, no Brysbaert), so the
  word-level rows are not the same model across languages.

## Data

`experiments/slot_ratings/results/v6zh/` is committed (6.3 MB, 380 files) -- it is
instrument output bought with API spend, not derived data that regenerates for free.
Also cached at `~/github/largeliterarymodels/data`. The POS tables and the manifest
live in `~/malignment-data/contextual_norms/`.

## 5. TWO DEFECTS THE ANALYSIS SENT BACK, AND WHAT THE MANIFEST DOES NOW

Both were errors in how ratings were COMMISSIONED, found only when
`named_under_dose` tried to use them.

**Coverage was correlated with dose.** Tier 2 commissioned 34,304 pairs at
top-quartile `k_transgressiveness` -- so contextual coverage became 21.8% at low dose
against 63.6% at high, and a low-vs-high contrast then confounds dose with WHICH
PROMPTS GOT RATED. Selecting on the variable you intend to condition on is the
outcome-selection error one step removed. `--uniform` is the fix: every unrated pair
above `--min-lineages` regardless of dose.

**`--pos VERB` deleted prompts rather than thinning them.** A noun-slot frame
contributes no verb cells and vanishes entirely:

    prompts under 20% verbs   en 451 of 2,612   zh 56 of 407
    already-rated en prompts in that group: 111

The English ones are the salary probes, the Chinese ones the sexual-domain
anatomical slots -- sites the displacement argument specifically cares about. It also
destroyed a diagnostic: restricting the analysis to prompts rated BEFORE any
dose-based selection kept **2 of 1,815 prompts**, because the originals are largely
noun slots and had already been filtered away. `--pos content` is now the default;
VERB remains correct for the one table that replicates Findings P, and wrong
everywhere else. The POS-proxy problem that motivated verbs-only is fixed by
STRATIFYING on POS, not by discarding four fifths of the tagset.

**Current manifest**: `priority.py --uniform --pos content --min-lineages 5`
-- 72,467 pairs over 2,270 prompts, routed per prompt to `v6` or `v6zh` by language.

## 6. A LEAK THAT REACHED PUBLISHED NUMBERS

`_slot_index` treats EVERY numeric field in a rating record as a scale. The first
version of `rate.py` wrote `n_lineages` and `consistency` as numbers --
and `consistency` is the share of a pair's lineages agreeing on direction, a function
of the OUTCOME. It became a predictor. It also broke the English pool, because the
303 pre-existing v6 files lack those keys and every cell from them was dropped for an
incomplete scale set (coverage 19.9% -> 1.9%).

Consequence, now corrected in 951 files: the Chinese contextual result fell from
+0.1070 to **+0.0889**, and the claim that named ratings beat the embedding at low
dose (+0.1189 vs +0.0923) collapsed to a **tie** (+0.0918 vs +0.0923). That claim was
leakage, not a finding.

The pre-existing v6 files carry the same hazard from the other side -- `v6_net`,
`v6_rise`, `v6_fall`, `v6_net_rate` are all exposed as scales. `predict.py` now names
its twelve scales explicitly and refuses any key matching
`net|rise|fall|eligible|present|lineage|consist`. **A denylist of known bookkeeping
fields silently admits every new one; naming what you want is the only version that
holds.**
