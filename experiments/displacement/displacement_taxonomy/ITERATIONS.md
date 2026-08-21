# Every presentation we tried, and what killed each one

The measurement never changed. Only what is put in front of the rater changed, thirteen times, over 2026-08-18/19 with RH. Recorded because several variants look obviously right until a specific cell breaks them, and the breaking cell is rarely the one you are looking at.

**Two calibration cells are used throughout.** `stroking / Llama-3.1-8B -> Instruct` (pass-1, sharp contrast, `cock -> beard`) and `reached / CT-LLM-Base -> CT-LLM-SFT-DPO` (the only topped-up pair in the store, high head agreement, `penis -> gun`). Several designs pass on one and fail on the other, which is the whole reason both are here.

## The two axes every variant is choosing between

    MEMBERSHIP   which column a word goes in
    ORDER        what sorts within a column
    FILTER       which words appear at all
    DISPLAY      what number, if any, is printed

Most failures came from choosing MEMBERSHIP and ORDER on different quantities.

---

## 1. v3 -- percentages, blocks from the movement rule

    HIGHER UNDER B / HIGHER UNDER A, words from movement(CANONICAL),
    sorted by |delta|, shown as `1.5% -> 10.8% (+9.3)`, up to three relations

205 codings. Works. Two defects, both found by RH:

- **The vocabulary is the units.** Over 29 stroking cells: 155 uses of `points, mass, probability, share, concentration` against 55 order words. Raters do arithmetic on what they are shown and report in it.
- **"Up to three" is a target, not a ceiling.** 27 of 29 cells returned exactly three relations, two returned one, **none returned two**. One rater wrote that its third relation was *"at best a hairline and I would not defend it if the numbers were resampled"* and submitted it anyway.
- Structural, found later: the two blocks are **disjoint by construction**, so every cell reads as a wholesale swap. The A/B designs below show the two arms actually share most of their head.

## 2. r1 -- ranks, common support, base's top 20

    positions not percentages; no relation count offered

Vocabulary fixed instantly: 155 mass words -> **2**. Relation counts spread 15/12/2.

**Killed by what common support silently drops.** A word measured in one arm only has no rank, so it vanishes. Those are the ELIMINATED and CREATED words. Median cell loses 42 base-only words carrying 7.5% of base mass; Llama 24.5%, Olmo-3 41.0%. On Llama the invisible words were `dick shaft member hard erection crotch erect` against `mustache goatee fur` -- the entire finding. Its 29 codings came back with bland kinds because the evidence had been removed before they saw it. **They characterised the truncation correctly.**

## 3. r2 -- + a block for arm-exclusive words

Words present in one arm only, listed with their position in the arm that has them and none in the other. Honest, free, and it cannot distinguish `crotch` (0.40% -> 0.0001%, eliminated) from `mobile` (0.29% -> 0.0752%, merely sub-theta). Both read as absent. See section 12 on why that number does not exist to be shown.

## 4. r3 -- + the union of both arms' top 20 (RH)

Base-anchored selection can only show FALLS: a word the aligned arm created sits deep in the base and never reaches the cut. Hid `rifle` 63->13, `pocketbook` 103->14, `toolbox` 60->18 while showing `gun` and `pistol`. Median 5 words recovered per lineage, up to 9. **Kept in every later variant.**

## 5. Head block + movers block

    THE LIKELIEST COMPLETIONS (positions 1-12 either arm)
    THE LARGEST MOVES (elsewhere in the ranking)

Answers "the rater never sees the actual most likely words" and "the biggest moves are invisible" at once. **Rejected by RH**: it abandons the A/B group structure the schema is built on, and the caption on the second block made an evaluative claim (`none of these is a likely completion`) that the geometry does not support -- `pocketbook` sits at rank 14 of 197.

## 6-7. A/B columns, each arm's own top N

    6. sorted by own-arm likelihood      7. sorted by movement

6 reads naturally and buries the story at line 10. 7 opens each column with the displacement. Both showed something v3 could not: **the columns overlap heavily** -- 11 of 16 words are top-16 under both arms. The two models mostly agree; they differ at the margins.

## 8. All words above theta, membership by rank direction, sort by rank diff (RH)

Column A = above theta in A and ranked higher in A; column B likewise. 86 and 61 rows.

- **The theta filter self-screens.** `bat`, which I had called tail noise, is below theta in base and above it in aligned, so it appears only in the column of the arm where it clears the floor. 51 of 52 excluded words are below theta in BOTH arms.
- **Killed by tiny-mass domination.** Column B leads `motorcycle +110, pocketknife +106, fishing +101` on 0.06-0.09% base mass, while `gun` -- 10.21pp gained, ends up rank 1 -- sits ninth of ten.

## 9. Sort by mass, show nothing at all (RH)

Two ordered word lists, no numbers anywhere. Semantically the cleanest thing we produced: `boxers briefcase bag penis cock trousers` against `gun pistol duffel wallet box pocketbook rifle`.

**Killed by scale blindness.** 90 and 56 words, tail differing by ~0.001pp, in the same typeface as a head differing by 4.8pp. Order encodes the falloff; nobody scanning a wrapped list feels it. This is v3's over-reading problem in a stronger form -- the backpack relation was built on 0.9pp, and here there is no signal at all against building one on 0.001pp.

## 10. Membership by mass, order by own-arm rank

    HIGHER UNDER A: 2. boxers (B has it 10) ...

The numbering gaps are elegant -- reading down column A gives `2, 3, 7, 8, 10...` and every gap is a word that went to the other column, so agreement is legible with nothing extra printed.

**Killed by pass-1 data, silently.** A word absent from the other arm has no rank there, so own-arm-rank ordering sorts it to the end. On Llama that pushed all seven eliminated words and all four created ones past the cut. **It works on topped-up cells and hides the finding on the cells we actually have** -- the worst possible failure shape.

## 11. Membership + order by mass, display ranks, 1% floor

    cock  1 -> 34  -33      beard  7 ->  1   +6
    penis 2 -> 41  -39      chin  11 ->  2   +9
    dick  - ->  -    -      mustache - -> -   -

Right on both calibration cells. Median 20 words per cell (range 12-34) at a 1% floor; 5% leaves two words. `- -> -` says *not in that arm's field at all*, which is stronger than a number and removes the need for r2's separate block.

**Its one flaw**: membership is mass, the printed number is rank, and on ~5% of shown words those disagree -- `pack 24 -> 15 (+9)` sitting under HIGHER UNDER A. Median 1 word per cell, 12 of 30 cells have none. See 13.

## 12. All-rank: 1% mass floor only, membership and order both rank diff (RH)

Coherent at last -- the quantity that decides the column is the quantity printed. Arm-exclusive words have no rank diff and are placed at the extreme of their column, which is what they are.

**Killed by arithmetic, not taste.** Rank difference is ceilinged by starting position: a word at rank 5 cannot move more than +4 places. So `gun` -- biggest mass gain in the cell, ends up rank 1 -- scores +4 and lands ninth of ten, while `pocketbook` gains 1.06pp, moves 89 places and leads. No rank-difference sort can ever put `gun` first.

## 13. All-rank with rank RATIO

Same as 12, ordered by `rank_A / rank_B` instead of the difference. Proportional movement, so `5 -> 1` (5.0x) and `103 -> 14` (7.4x) are comparable.

    reached  B: pocketbook 7.4x, gun 5.0x, pistol 5.0x, rifle 4.8x, toolbox 3.3x
    Llama    A: [7 out of field], cock 34.0x, penis 20.5x

Leads with the right words on both cells and stays fully all-rank. Two known properties: ratios are volatile at the very top (`1 -> 2` scores 2.0x, same as `10 -> 20`), and `belt` lands under A on rank grounds though its mass rose, which is correct by this design's own definition.

## The two words that break coherence, and why they are real

Where membership is mass and display is rank, a small set contradicts. Both mechanisms are findings, not defects:

    SURVIVOR BY ATTRITION   pack   1.259% -> 1.184% (flat)   rank 24 -> 15
                            its neighbours collapsed: jacket 1.31->0.28,
                            shorts 1.26->0.46, black 1.26->0.32, t 1.26->0.70
    OVERTAKEN LEADER        belt  11.593% -> 11.959% (rose)  rank  1 ->  2
                            gun gained 10.2pp and went past it

One per column on `reached`; **zero on Llama**. The effect only appears where the distribution redistributes heavily. Current disposition: exclude from the panel and print the count, because a row whose number contradicts its heading teaches the rater to distrust the layout -- but never drop it silently.

## What is settled

- Percentages produce the mass vocabulary. Ranks do not. 155 -> 2 over the same 29 cells.
- A relation cap is a target. Offer no number.
- Common support silently deletes the eliminated and the created words; only topup fixes it, and only for cells that have been through it.
- Union of both arms' top N, never one arm's.
- MEMBERSHIP and ORDER must be the same quantity, or the column contradicts its own heading.
- Order by a RATIO if ordering by rank, or the head of the distribution can never lead.
- A 1% mass floor, in the arm that favours the word.
- Calibrate on a high-contrast cell. `reached` has high head agreement and made every design look equally flat; `Llama` separates them immediately.

## Still open

- Whether to exclude or mark the contradiction words (section 13).
- 12/13 versus 11: all-rank coherence against mass ordering. 13 is coherent and 11 is more direct about what moved; they agree on both calibration cells at the head and diverge in the tail.
- Nothing above has been run at scale. Only v3 (205 codings) and r1 (29) have raters behind them; every variant from 3 onward is judged on rendered tables, not on what raters did with them.
