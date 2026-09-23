# slot_pos

**What part of speech does each prompt's slot summon, and is `directedness` just that?** RH, 2026-09-23. Exploratory: a stratifier that other questions read (`freudian_hypothesis/feature_pairs.py --slot`, the Figure 4 within-verb check), not a registered result.

    python -u run.py     -> results/prompt_pos_en.csv, results/summary.txt

## The stratifier: `results/prompt_pos_en.csv`

One row per English prompt (2,578). Each UPOS's share of the above-theta mass, per lineage and then the median over the 50 base→endpoint lineages, on each side. The UPOS is CONTEXTUAL, tagged on prompt + word, from `words_long_v4`.

    pos_base, purity_base          argmax of the base profile and its share
    pos_aligned, purity_aligned    the same on the aligned side
    switch                         1 where they differ (81 prompts)
    base_<UPOS>, aligned_<UPOS>    the full profiles

**Stratify on the BASE side.** Grouping on the aligned side would let alignment choose the stratum it is then measured in.

Base-side dominant POS: VERB 1,839 prompts (median purity 0.79), PRON 430 (0.69), NOUN 144 (0.92), ADP 45, AUX 38, other 82. The largest switch is PRON→VERB (20 prompts).

## Directedness is not part of speech, and a third of it is the frame

The `v6` rubric is filed under two disjoint keys, `v6` and `slot_rating_en_v6`. Reading both gives 135,114 rated (prompt, word) pairs over 2,182 prompts. The first run read only the second key and saw a fifth of the rows; the paper seat caught the error, which its own producer had shared.

- The word's UPOS explains 0.022 of the variance and the slot's dominant POS 0.008. VERB and NOUN rate alike (means 2.49 and 2.51); ADV (1.15) and ADJ (1.64) rate low.
- **Prompt identity explains 0.325**, or 0.289 among verbs at verb slots. The same verb is rated differently in different frames.
- At the prompt level, mass-weighted directedness rises with the slot's base VERB share: Spearman 0.36 over 2,182 prompts. A frame-family contrast in directedness therefore needs verb share as a control.

Not tested yet: valency. "scream" rates 1 and "scream at her" rates 7, so transitivity is the likely word-level carrier.
