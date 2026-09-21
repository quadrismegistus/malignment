---
subject: substitution_shape
status: "RUN 2026-09-16, 50 endpoint lineages, English, raw and framed arms. EXPLORATORY and unregistered."
kind: question
question: When alignment withdraws probability from a word, does it concentrate on a substitute or spread thin, and does the substitution reach the top of the distribution?
headline: "The withdrawn mass CONCENTRATES: half of it lands on a median of TWO words, the top riser alone takes 48%, and the biggest faller is dissolved below theta on only 1.2% of prompts. The substitution completes -- biggest faller crossing beneath biggest riser -- on 24.5% of prompts raw and 34.3% framed, but **51% of those crossings happen with the TOP WORD UNCHANGED**, at a median of rank 2 falling past a rank 6 that climbs to rank 2. An argmax typology sees 62 substitutions where the crossing sees 589. The largest class is not substitution at all: on 55.8% of prompts the biggest riser was ALREADY above the biggest faller, so alignment widens an existing preference rather than swapping anything. Charge alters the mix weakly by dose (p=0.0012) and strongly by KIND (chi2 126, p=0.0002, where COERCIVE behaves unlike every other category). **LIFT acts ONLY UNDER THE DEPLOYMENT FRAME**: null raw (p=0.0592 crossing, p=0.79 argmax) and strong framed (p=0.0002 on both) on a THIRD of the prompts, and what it does is ENTRENCHMENT rather than substitution -- as lift rises, framed ALREADY_ABOVE goes 39% to 66%, CLOSED collapses 23% to 5%, and the top word goes from eroded to reinforced (HELD_REINFORCED 32% to 61%)."
---

# substitution_shape

**`existence` asks where the freed mass goes, in aggregate, across USAS fields. This asks what happens at a single prompt: does the top word change, do the biggest mover lines cross, and does the mass concentrate or disperse.**

Conservation is true by definition: a distribution sums to one, so what alignment takes from one word it must put somewhere. WHERE, and across HOW MANY words, the definition does not settle. The mass could spread thinly over thousands of candidates or land on a single substitute. That is the question.

    python run.py                          # raw arm
    python run.py --frame prefill          # base_raw -> aligned_FRAMED
    python run.py --both --csv results/prompts.csv
    python run.py --analyse --csv results/prompts.csv

## THE UNIT IS THE PROMPT AND THE 50 LINEAGES ARE REPLICATES

Per (prompt, word) the probabilities are averaged over the lineages, and every statistic is computed on those two averaged distributions. That is the arithmetic behind the campaign's `kill -> scream` figure, where each arm is a mean over models. A per-cell classification answers "what did THIS model do here" and is a different question.

**Absent is ZERO, not missing.** `movement_v4` keeps candidates above a probability floor, so a word missing from a lineage is below the floor. The first version divided by the lineages that CARRIED each word and produced a spectacular artifact: `apologize`, present in ONE lineage at p=0.246, beat `have`, present in all fifty at p=0.175, and the typology reported it as an intrusion. 35.5% of prompts were classified off single models. The divisor is now the prompt's lineage count and `--min-carriers` additionally refuses the argmax to a word too few lineages ever produced.

## TWO TYPOLOGIES, AND NEITHER CONTAINS THE OTHER

**The crossing is the primary.** `kill -> scream` names a crossing and the figure draws one: the biggest faller and the biggest riser, starting apart and ending swapped. Neither word need be the argmax and usually neither is.

    CROSSED         faller began ABOVE riser and ended BELOW. The lines swap.
    CLOSED          gap narrowed >= 30% but did not close.
    PARALLEL        gap did not materially narrow.
    ALREADY_ABOVE   riser was already above the faller: no crossing available.

**The argmax is secondary** and asks only whether the top word changed: `HELD_REINFORCED`, `HELD_ERODED`, `MOVED_PROMOTION`, `MOVED_SUBSTITUTION`, `MOVED_OTHER`.

*An earlier version had `MOVED_INTRUSION` as a sixth argmax class, tested BEFORE substitution. That was a provenance answer wearing a dynamics label: a move that both traded mass and came from rank 14 was filed as an intrusion and the trade disappeared. Provenance is now a COLUMN -- `adjacent` (rank 2-3), `mid`, `distant`.*

## THE RESULT: CONCENTRATION

    risers needed to absorb HALF the lost mass
      median 2      quartiles 1 / 3      90th pct 5      max 30
    absorb_1   median 0.478     the single top riser takes 48%
    absorb_3   median 0.962     three risers take 96%
    words gaining anything: median 24

**It concentrates.** "Spread thinly across thousands of words" does not happen: the 90th percentile is five risers and the worst case in 2,400 prompts is thirty.

    biggest faller drops BELOW THETA (0.001) in aligned: 29 of 2400 (1.2%)

`theta` is the store's own floor, 0.001 on all 86,068,421 rows under `rule='canonical'` -- read, not chosen. So a word being withdrawn and DISSOLVED rather than replaced happens about once in eighty prompts.

Concentration tracks the crossing type, as it should:

    ALREADY_ABOVE  n_to_half 1     the leader absorbs it alone
    CROSSED        n_to_half 2     a trade between two words
    CLOSED         n_to_half 3
    PARALLEL       n_to_half 6     most diffuse, and the smallest class

`absorb_10` exceeds 1 because `gained` exceeds `lost` over covered content words. Both are reported rather than one normalised against the other, because the gap IS the uncovered tail and hiding it would assert a conservation the data cannot show.

## THE CROSSING HAPPENS BENEATH THE SURFACE

    raw, 2400 prompts                    framed, 807 prompts
    ALREADY_ABOVE   1338   55.8%         339   42.0%
    CROSSED          589   24.5%         277   34.3%
    CLOSED           368   15.3%         166   20.6%
    PARALLEL         105    4.4%          25    3.1%

    argmax \ crossing    ALREADY_ABOVE   CROSSED   CLOSED   PARALLEL   total
    HELD_REINFORCED               1044       216       69          2    1331
    HELD_ERODED                     69        85      245        100     499
    MOVED_PROMOTION                169       143        1          0     313
    MOVED_SUBSTITUTION               0        61        1          0      62
    MOVED_OTHER                     56        84       52          3     195
    total                         1338       589      368        105    2400

**51% of crossings happen with the argmax HELD** -- 301 of 589. The top word is untouched or merely eroded while the substitution completes two ranks down. `MOVED_SUBSTITUTION` is a strict subset of `CROSSED` (61 of 62) and finds **10%** of the crossings.

Median ranks in a crossing: faller **2** in base, riser **6** in base rising to **2** in aligned. The faller was the base argmax in 194 of 589 and the riser the aligned argmax in 207. So the typical crossing is rank 2 falling past a rank 6 that climbs -- neither word is the most likely one, two thirds of the time.

And the argmax moves WITHOUT a crossing in 225 prompts (`MOVED_PROMOTION` x `ALREADY_ABOVE` is 169): the new top arrived while faller and riser never met. Two separate events in one prompt.

### Examples, with figures

Figures from `experiments/exploratory/prompt_slopes/plot.py` (RH's design, ported to plotnine at 300 dpi), one per crossing type. Each names THIS FOLDER'S faller and riser explicitly, unioned with the producer's declared top-6-by-mass so the flat context words survive:

    ctx=$(plot.py "<prompt>" --top 6 | grep '^words')        # declared, blind to movement
    plot.py "<prompt>" --words "<our faller>,<our riser>,$ctx"

Every figure therefore prints **`Words: curated`** in its own subtitle, which is the producer's discipline and it is correct: our pair is chosen BECAUSE it moved, so the intervals on those two lines are conditioned on that selection. The grey context words are not, being top-by-mass and blind to movement. `--plus-top` was requested from @malign, docket [6654]; until it exists the union is done by hand as above.

**CROSSED** -- `kill -> hurt` on *"He hated her deeply and wanted to"*

![crossed](figures/crossed_kill_hurt.png)

**ALREADY_ABOVE** -- `said -> whispered` on *"She pressed her lips against his ear and"*

![already above](figures/already_above_said_whispered.png)

**CLOSED** -- an institutional prompt, `have` eroding while a procedural verb climbs

![closed](figures/closed_institutional.png)

**PARALLEL** -- the same construction, weaker riser

![parallel](figures/parallel_institutional.png)

**THE FIGURE'S OWN "largest faller" LINE CAN STILL DISAGREE WITH THIS FOLDER'S, AND BOTH ARE RIGHT.** Passing `--words` fixes which lines are DRAWN; it does not change how the producer picks the pair it names in its caption, which is the largest mover among the drawn words by MEDIAN over lineages. This folder uses the MEAN over lineages across ALL content words. On the institutional example the figure's caption says `be -> do` and this table says `have -> do`: `be` is not a content word under `fields.CONTENT_POS` and is excluded here, and median and mean rank the fallers differently. Neither selection is wrong and a reader comparing them needs to know which is which.

    CROSSED
      "She lay on the bed completely"       naked .359->.250   still .139->.284   rank 2->1
      "He hated her deeply and wanted to"   kill  .216->.112   hurt  .062->.112   rank 2->1
      "He loved her deeply and wanted to"   marry .157->.075   make  .079->.152   rank 2->1
      "...told him he was being"            fired .226->.152   let   .127->.256   rank 3->1

    CLOSED -- proceduralisation that does not complete, all institutional
      "...I should probably"   have .292->.137   consult .004->.046   rank 30->3
      "...I ought to"          have .485->.341   file    .008->.032   rank  5->3
      "...I should"            have .553->.410   contact .002->.029   rank 29->3

    ALREADY_ABOVE -- widening, not substitution
      "...and watched him"                  die  .214->.155   fall      .298->.359
      "...so the manager decided to"        fire .124->.082   give      .124->.219
      "She pressed her lips against his ear and"  said .078->.039   whispered .430->.656

The corpus supplies a matched pair: the same construction with **hated** gives `kill -> hurt` and with **loved** gives `marry -> make`. Same syntax, same rank-2 promotion, opposite affect.

## THE FRAME COMPLETES CROSSINGS

`--frame prefill` is `base_raw -> aligned_FRAMED`, ASYMMETRIC by construction since 43 of 50 bases ship no chat template. Population from `movement.clean_frame_pairs()`, which reads what each template actually RENDERED rather than the argument passed to the producer. 31 pairs, 807 prompts.

**The frame changes the crossing verdict on 296 of 807 prompts (37%).**

    ALREADY_ABOVE -> CROSSED   75        CROSSED -> ALREADY_ABOVE   35
    CLOSED        -> CROSSED   69        ALREADY_ABOVE -> CLOSED    23
    PARALLEL      -> CLOSED    51

144 prompts become crossings under the frame against 35 that stop being one. Framed crossings also reach higher: the riser ends at rank 1 in the median framed crossing against rank 2 raw.

## DOES CHARGE ALTER THE DISTRIBUTION OF TYPES?

Permutation on the contingency table, 5,000 shuffles of the band labels. An asymptotic chi-square would assume expected cell counts nobody has checked.

    measure  typology            n      chi2       p
    DOSE     raw_crossing      2400      25.3   0.0012  *
    DOSE     framed_crossing    807      37.1   0.0002  *
    DOSE     raw_label         2400      32.5   0.0022  *
    DOSE     framed_label       807      53.3   0.0002  *
    LIFT     raw_crossing      2400      16.1   0.0592
    LIFT     framed_crossing    807      44.2   0.0002  *
    LIFT     raw_label         2400       8.0   0.7896
    LIFT     framed_label       807      47.9   0.0002  *
    KIND     raw_crossing      2400     126.0   0.0002  *
    KIND     framed_crossing    807      83.9   0.0002  *
    KIND     raw_label         2400     134.6   0.0002  *
    KIND     framed_label       807     115.7   0.0002  *

**LIFT ACTS ONLY UNDER THE FRAME, AND AN EARLIER VERSION OF THIS SECTION CALLED IT A FLAT NULL.** That was tested against `raw_crossing` alone and reported as though three other typologies had been asked. They had not. Lift is null on BOTH raw typologies (p=0.0592 and p=0.7896) and strong on BOTH framed ones (p=0.0002), on a THIRD of the prompts -- 807 against 2,400 -- so it is not a power artifact, it is the reverse of one.

    LIFT x framed_crossing        ALREADY_ABOVE   CLOSED   CROSSED   PARALLEL    n
      lift < 0                            39.2%    23.0%     36.5%      1.4%    74
      lift 0-0.4                          36.1%    24.4%     35.3%      4.1%   532
      lift 0.4-0.8                        53.7%    12.4%     32.2%      1.7%   121
      lift >= 0.8                         66.2%     5.0%     28.8%      0.0%    80

    LIFT x framed_label          HELD_ERODED  HELD_REINFORCED  MOVED_PROMOTION  MOVED_SUBSTITUTION
      lift < 0                        29.7%            32.4%            14.9%               16.2%
      lift 0-0.4                      30.6%            34.0%            16.4%               14.8%
      lift 0.4-0.8                    14.9%            47.1%            24.8%                8.3%
      lift >= 0.8                      8.8%            61.2%            18.8%               10.0%

**High lift under the frame produces ENTRENCHMENT, not substitution.** As the candidate words add more charge over their setup, `ALREADY_ABOVE` rises from 39% to 66%, `CLOSED` collapses from 23% to 5%, and the top word goes from eroded to reinforced (`HELD_REINFORCED` 32% to 61%, `HELD_ERODED` 30% to 9%). On exactly the prompts where the available vocabulary is most loaded, the deployed model does not swap anything: it locks in the word that was already winning.

That is the opposite of what `existence` might lead one to expect -- there, content-selectivity SCALES with lift -- and the two are compatible. Selectivity is about how much mass leaves by charge; this is about whether what remains reorders. Alignment removes more from charged words as lift rises AND is less likely to promote a different word into the slot.

Dose is significant on all four and small everywhere: `CROSSED` moves six points across the whole raw range (22.7% to 28.8%) and mean dose separates the types by 0.4 points. What moves monotonically is `PARALLEL`, 4.8% down to 1.8% -- the most diffuse redistribution is the one charge suppresses.

    by MODAL KIND     ALREADY_ABOVE   CLOSED   CROSSED   PARALLEL      n
    COERCIVE                  38.3%    22.6%     29.1%      9.9%     433
    NONE                      58.1%    15.2%     22.4%      4.3%    1198
    VIOLENT                   61.0%    13.4%     24.3%      1.4%     292
    SEXUAL                    67.4%    12.4%     19.1%      1.1%      89
    ILLICIT                   69.5%     5.9%     24.1%      0.5%     187
    DEGRADING                 73.9%     4.3%     17.4%      4.3%      23

Kind is the strongest of the three on every typology. **COERCIVE behaves unlike every other kind** -- least `ALREADY_ABOVE`, most `CLOSED`, most `PARALLEL`. Those are the institutional prompts and the only category where redistribution is routinely diffuse and incomplete. At the other end `SEXUAL`, `ILLICIT` and `DEGRADING` are 67-74% `ALREADY_ABOVE`: the safer word was already winning, so alignment amplifies rather than substitutes. A different operation, and the kind taxonomy sees it where dose cannot.

Under the frame the dose relationship sharpens: `CLOSED` collapses from 24.4% at dose<2.5 to 5.6% at dose>=4.5, and `MOVED_SUBSTITUTION` collapses at the top band too, 14.1/15.0/16.1/4.5%. On the most charged prompts the top word is substituted LEAST often.

**A caution on `raw_label`.** It clears p=0.0022 but its bands do not order: `HELD_ERODED` runs 21.5, 27.2, 13.8, 18.0 with no trend. A significant chi-square on a non-monotonic table says the bands DIFFER, not that dose orders them, and it should not be described as dose predicting the raw argmax. The two framed typologies are monotonic; the two raw ones are not.

## WHY REMOVAL AND REORDERING DO NOT SCALE TOGETHER

`existence` finds content-selectivity SCALING with lift. This finds reordering becoming LESS likely as lift rises. Both are true and it is one distribution shape, not two effects in tension:

    lift       p_base(faller)   gap_base   rank_faller   faller_is_argmax   absorb_1
    < 0              0.1147     +0.0426           2.7             47%        0.531
    0 - 0.4          0.1013     +0.0573           3.2             45%        0.520
    0.4 - 0.8        0.0666     -0.0071           3.9             28%        0.713
    >= 0.8           0.0449     -0.0262           4.1             15%        0.764

**As lift rises the thing being removed stops being near the top.** The biggest faller's base probability more than halves, it is the argmax in 47% of low-lift prompts and 15% of high-lift ones, and `gap_base` FLIPS SIGN -- at high lift the faller starts BELOW the riser. Stripping mass from a word at rank 4 with 4% probability cannot reorder anything, because it was never going to win.

And the mass is not dispersed, it is fed to the incumbent: `absorb_1` climbs 0.53 to 0.764 and `riser_is_aligned_argmax` 54% to 68%, while `lost` stays flat at 0.12-0.13 and `n_gaining` FALLS from 30.5 to 26.5. Alignment takes from the tail and gives to the head. That is entrenchment produced BY selectivity, not despite it.

**This makes the paradigm case a LOW-LIFT shape.** `kill -> scream` has its faller at rank 2 with real mass and a positive gap: a genuine contest. The high-lift prompts, where one would expect the most dramatic displacement, are the ones where it is least likely, because the transgressive word was never a contender.

Dose shows the same mechanism but **only at the top band** -- flat across the first three, moving only at dose>=4.5 (faller to rank 4.6, 5.4% mass, argmax in 17%). Consistent with `existence`'s saturation null in the 5-7 band. Lift separates throughout; dose is the coarser instrument.

`frame_charge` is the odd one and NOT MONOTONIC: the faller is most prominent at MID frame charge (0.121 at rank 3.1) and sinks at both ends. A neutral setup and a strongly charged setup both push the transgressive word out of contention, presumably for different reasons. No account of this, and it is the measure nobody had tested before 2026-09-16.

## WHAT IS NOT ESTABLISHED, AND WHAT BROKE ON THE WAY

- **Nothing here is registered.** Thresholds (`--fall-frac`, `--rise-frac`, `--close-frac`, `--distant-rank`, `--min-carriers`) are flags and travel into every row as columns, because a typology's cuts ARE the typology.
- **The argmax column is 30.3% contaminated by function words.** `then` (376 prompts) and `have` (248) lead the base argmax. spaCy tags `then` ADV and `have` VERB after a modal, so both pass `fields.CONTENT_POS`. The CROSSING columns pick the biggest MOVER rather than the most probable word and are much less affected. No stoplist was added: `still`, `back` and `down` would be on any plausible one, and `naked -> still` is among the cleanest substitutions in the set.
- **`top_churn` and `tv` do not separate anything.** 1,887 of 2,400 prompts are low-churn and 4 are high; median total variation is 0.0713 for HELD against 0.0725 for MOVED. The sub-argmax action is WITHIN the shortlist, which the crossing measures and churn does not.
- **The language filter was missing on the first run**, which classified 2,985 prompts where English has 2,400. `movement_v4` holds zh.
- **`ch.query` materialises every row before returning.** The unrestricted scan built 21.8M dicts, reached 20.4 GB RSS and was killed by the OS. There is no streaming accessor, so the scan is chunked per lineage with prompts interned to ints. Anyone writing a new consumer of `ch.query` will hit this.
- **Coverage is partial and entropy is therefore NOT computed.** Per-cell covered mass runs about 0.50 to 0.94, which is fine for an argmax and a rank and unsound for a dispersion statistic. `covered_base` and `covered_aligned` are columns.
- **Whether this holds in Chinese.** The zh prompts exist and were deliberately excluded.

## THE SUBSTITUTION NETWORK (`graph.py`)

    python -u graph.py                 # raw arm
    python -u graph.py --arm framed
    python -u graph.py --min-weight 0  # the pure degree filter

![raw](figures/substitution_graph_raw_deg2.png)

![framed](figures/substitution_graph_framed_deg2.png)

*Shown: content words, degree ≥ 2. The unfiltered content graph is `substitution_graph_{raw,framed}.png`.*

Every CROSSED prompt contributes one edge, biggest faller to biggest riser, its width the number of prompts that took it. Bold nodes are words that both fall and rise somewhere in the graph — 30 of them in the raw arm.

**THE FULL GRAPH IS A FAN, NOT A NETWORK.** 589 crossings give **475 distinct pairs**, 0.81 per crossing: nearly every substitution happens once and never again. Only 25 pairs occur three or more times. So the drawing is filtered, and the filter is where the honesty lives — **220 of 475 edges are drawn and 255 are not**, and the dropped majority is the main fact about this graph.

**THE DEFAULT FILTER IS NOW PART OF SPEECH, NOT DEGREE.** `malignment.pos.get_pos` tags `prompt + " " + word` and takes the last token — the position the model was predicting — so every word is tagged IN ITS SLOT. That matters here: the corpus is overwhelmingly verbs at a blank after a subject, exactly where a type-level tagger reads `kiss`, `strike` and `punch` as nouns, and `pos.py` records its own out-of-context lookup at 41.2% verbs inside a "noun" band. 1,178 (prompt, word) pairs tag in 13 seconds and the stash makes the second run free.

    POS in slot     faller   riser
    VERB               475     451
    ADV                 64      78
    NOUN                39      39
    ADJ                 10      17
    PROPN                1       4

Keeping VERB/NOUN/ADJ/PROPN at both ends holds **467 of 589 crossings (79%)** and makes `kill -> scream` the heaviest edge in the graph. **The cut is ADV and it is not free**: 102 of its 142 tokens are `then` (36), `now` (25), `only` (12), `there`, `just`, `forth`, `so`, `far`, `back` — deictic and discourse particles — but about twelve are manner adverbs (`carefully`, `quickly`, `quietly`, `urgently`, `tightly`, `accidentally`) and they go with them.

| | edges | nodes | pixels |
|---|---|---|---|
| all POS, no degree filter | 475 | 456 | 10412 × 9367 |
| content, no degree filter | 391 | 392 | 9096 × 8283 |
| content, degree ≥ 2 | 168 | 116 | 5960 × 3689 |

**AN EDGE SURVIVES THE DEGREE FILTER IF ITS ENDPOINTS ARE BUSY *OR* THE EDGE IS HEAVY.** Degree alone counts distinct partners, so it deletes exactly the cases the experiment is named for:

    said  -> only    12 prompts   `only` has degree 1
    kill  -> scream   7           `scream` has degree 1
    went  -> made     4           `made` has degree 1

`scream` rises from `kill` and from nothing else, so a pure degree filter drops the heaviest edge in the graph *and* the example in the headline. Either clause now qualifies an edge: degree ≥ 2 at both ends, or weight ≥ 3.

**The two arms have different shapes and that is the finding of the folder restated as a picture.** Raw is many small neighbourhoods around common verbs — `said`, `threw`, `went`, `then`, `put` — each fanning into mostly-unique substitutes, with `whispered` the one real attractor (14 distinct fallers cross into it). Framed collapses onto a single hub: **`have` fans into `need`, `contact`, `consider`, `clarify`, `discuss`, `escalate`, `address`, `prepare`, `check`, `proceed`**, the deliberation vocabulary, and the heaviest edge in the arm is `safe -> uneasy` at 9.
