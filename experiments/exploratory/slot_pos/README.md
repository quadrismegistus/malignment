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

Base-side dominant POS: VERB 1,877 prompts (median purity 0.78), PRON 271 (0.55), NOUN 145 (0.92), DET 96, AUX 45, ADP 45, other 99. 87 prompts switch dominant POS; the largest groups are PRON→DET (10), VERB→AUX (8) and PRON→VERB (8). `results/switchers_en.md` lists them with their movers (`switchers.py`).

**spaCy tags a slot-final article as PRON**: "the" was 28% of the PRON mass at PRON-dominant slots, and "a" another 4%. `run.py` remaps the/a/an to DET. Before the fix, PRON→VERB looked like the main switch (20 prompts); most of that was the article. Possessives and demonstratives stay as tagged.

`results/prompt_kind_en.csv` (`prompt_kind.py`) gives each prompt's dominant `charge.py` kind: the per-word modal kind, weighted by base mass (median over lineages), NONE included. Across 2,112 prompts with kind ratings: NONE 1,063, COERCIVE 379, VIOLENT 281, OTHER 155, ILLICIT 105, SEXUAL 99, DEGRADING 30. `charged_share` is bimodal (median 0.15, q75 0.99): a prompt's mass is either almost uncharged or almost entirely one charged kind.

## Figure 4 within strata (`fig4_strata.py`)

This is the statistic behind the z plate (`norm_change/norms_levels_z.py`): lineage mean of the move, median over the 50 lineages, in the pooled norm sd. Each (stratum, band) gets a sign test with BH over the 14 plate rows. Lift cuts are the published ones. The pooled stratum must reproduce `norms_levels_z_en.json` or nothing is written. `--by pos` was also checked against a run through `norms_levels_z.build` itself, and the two agree to 1e-9.

- **Verb slots (1,495 prompts, purity ≥ 0.6): no significant cell changes sign in any band.** Relative to the pooled plate, four cells change significance: `k_register_level` on all prompts (+0.017, 28/22) and `k_concreteness` on high lift (18/32) lose it; `k_transgressiveness` on low lift and `warriner_dominance` on all prompts gain it.
- **Noun slots (130 prompts)**: no significant sign disagreement. The v6 action scales are not meaningful at noun slots, so read only the k and Warriner rows there.
- **By kind**: DEGRADING (30 prompts) reverses on valence, dominance, makes_better and makes_worse; aligned completions there go more negative and less dominant. ILLICIT reverses on vocalisation, becoming less vocal where the pooled plate goes more vocal. Only 10 of the 30 DEGRADING prompts are verb slots, so the DEGRADING reversal lives mostly outside verb slots.
- **Kind × POS** (strata of ≥ 20 prompts): SEXUAL verb slots gain directedness (all prompts 36/14, high lift 34/16), against a pooled plate that is flat to negative. ILLICIT verb slots lose vocalisation. SEXUAL noun slots go more concrete on low lift.

## Directedness is not part of speech, and a third of it is the frame

The `v6` rubric is filed under two disjoint keys, `v6` and `slot_rating_en_v6`. Reading both gives 135,114 rated (prompt, word) pairs over 2,182 prompts. The first run read only the second key and saw a fifth of the rows; the paper seat caught the error, which its own producer had shared.

- The word's UPOS explains 0.022 of the variance and the slot's dominant POS 0.008. VERB and NOUN rate alike (means 2.49 and 2.51); ADV (1.15) and ADJ (1.64) rate low.
- **Prompt identity explains 0.325**, or 0.289 among verbs at verb slots. The same verb is rated differently in different frames.
- At the prompt level, mass-weighted directedness rises with the slot's base VERB share: Spearman 0.36 over 2,182 prompts. A frame-family contrast in directedness therefore needs verb share as a control.

Not tested yet: valency. "scream" rates 1 and "scream at her" rates 7, so transitivity is the likely word-level carrier.
