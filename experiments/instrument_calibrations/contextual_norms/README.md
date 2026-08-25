---
subject: contextual_norms
status: Chinese arm opened; comparability characterised, not established
---

# Contextual norms: the POS pass, the rating manifest, and the Chinese arm

Three producers, one dependency chain:

    pos_pass.py    contextual POS for every (prompt, word) in twp_words_v4
    priority.py    what to rate next, in tier order, filtered by that POS
    rate_zh.py     runs the v6 instrument over the Chinese tier

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

`rate_zh.py` ran the unmodified instrument over tier 1: **10,666 pairs, 380 prompts,
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

`named_under_dose/predict.py --lang zh --contextual v6zh --match-population
--verbs-only`, 89,917 shared cells:

                        ctx_v6zh/trees          norms/trees          ratio
    POOLED         +0.1070 [.1005,.1113]   +0.0348 [.0136,.0664]     3.1x
    LOW dose       +0.1189 [.1081,.1228]   +0.0197 [-.0097,.0473]    6.0x
    HIGH dose      +0.0971 [.0833,.1159]   +0.0195 [.0019,.0371]     5.0x

**The grain finding is not English-specific.** Chinese word-level norms sit at zero
(one range crosses it); the same vocabulary asked at the site is 3-6x that, ranges
disjoint at every stratum. English gave 4.7x.

**And at low dose the named ratings BEAT the embedding**, which has not happened
anywhere else in this work:

    LOW dose   ctx_v6zh +0.1189 [.1081,.1228]   bge +0.0923 [.0760,.1063]   disjoint
    HIGH dose  ctx_v6zh +0.0971                 bge +0.0947                 tied

In English, GloVe stayed ahead of contextual naming everywhere. P's "the unnamed
residual outpredicts every name we have tried" has a boundary, and it is a language
boundary rather than a grain one.

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
