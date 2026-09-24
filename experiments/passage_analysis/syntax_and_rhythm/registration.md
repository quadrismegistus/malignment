---
subject: syntax_and_rhythm
status: FROZEN 2026-09-24 (RH approved), before the full run. Registered LIGHT. Four primary hypotheses, six syntax predictions, one undirected declared contrast; everything else exploratory.
question: Does alignment change the syntax and rhythm of narrative prose, or only its content?
unit: the lineage
---

# syntax_and_rhythm: a LIGHT registration

## What this registration is for

RH, 2026-09-24: *"my research practice in digital humanities is not to consider registrations binding on what I will report and write."*

So this file does not constrain what gets reported, written or emphasised. It records which analyses and directions were declared **before the full data was seen**, so a reader can weigh a declared result differently from one found by looking. The same licence as `displacement/norm_change`: any feature, subset or grain may be explored and reported. What this file adds is that an exploratory result is labelled as one, and a declared hypothesis that failed stays visible as a failure.

## Unit, population, test

    UNIT         the lineage (base -> aligned endpoint). 37 lineages as of 2026-09-24.
    POPULATION   national_story's own population, via parse_passages_prosodic.py (see README):
                 load_raw(min_words=150, drop_escapes=True) + _paired, raw frame.
                 PRIMARY FILTER: judge overall == "story" AND pure_story == True.
                 All demonyms pooled (the no-demonym control is thin: 733 texts).
    STATISTIC    per lineage, aligned minus base, on the stratified means defined per hypothesis
    TEST         paired over lineages: exact sign test and Wilcoxon signed-rank, two-sided.
                 A lineage with no passages in one arm after filtering drops out, and is listed.
    FAMILIES     {H1a, H1b, H2a, H2b} one family, Holm-corrected; H3 a second family, Holm-corrected.
    INSTRUMENT   prosodic with keep_parse (PR #194, including the spaCy SPACE-token fix);
                 producer instrument tag syntax_and_rhythm-v1; exact prosodic git sha in population.json.

**Sensitivity analyses (declared, directionless):** (a) the no-demonym control only; (b) no judge filter; (c) excluding lineages with fewer than 10 filtered passages in either arm.

## H1: alignment improves rhythm in the Liberman & Prince sense

RH's prediction: *"fewer clashes in the stress grid, i.e. more well-formed, correctly spaced stress grids. Parsed by sentence and stratified for analysis by sentence length."*

Grain: `by_sentence.csv`, `version == "orig"`. The grid is prosodic's own `grid_data` height rule (lexical levels 1–3, phrasal levels 4–5 from `gstress`), defined in the producer docstring.

| # | Hypothesis | Measure | Direction |
|---|---|---|---|
| **H1a** | fewer grid clashes | `clash_rate`: clashes at levels 2–5 per syllable | aligned LOWER |
| **H1b** | more evenly spaced beats | `ibi2_cv`: CV of intervals between stressed syllables | aligned LOWER |

**Stratification by sentence length.** Bins in words: 2–7, 8–12, 13–19, 20–29, 30+. For each lineage and arm, take the mean in each bin. The lineage statistic is Σ_b w_b · (aligned_b − base_b), where w_b is the pooled share of sentences in bin b across all lineages and both arms. A bin in which a lineage lacks either arm is dropped, and that lineage's weights are renormalised. Per-bin sign counts are reported beside the pooled statistic.

Secondary, directional but outside the Holm family: per-level clashes `clash2`–`clash5` (each lower), `lapse2_rate` (lower), `alt2` (higher).

## H2: alignment improves metrical parsing

RH's prediction: *"alignment improves metrical parsing (ambiguity down, violations down)"*, on the antimetricality draft's method (Heuser, Kiparsky & Anttila, Aug 2026, §§2–4), with a historical human baseline.

Grain: `by_window.csv`, `version == "orig"`. Windows are 10-syllable, cut at word boundaries, non-overlapping, lowercase and unpunctuated. They use the 2020 constraint set (w_peak, w_stress, s_unstress, unres_across, unres_within) with resolution s ≤ 2, w ≤ 2. This is identical to `data.2026.reparse.big_data.parquet`: on two baseline lines the parse counts were reproduced exactly (3 and 4).

| # | Hypothesis | Measure | Direction |
|---|---|---|---|
| **H2a** | less metrical uncertainty | `num_parses` (viable scansions per window) | aligned LOWER |
| **H2b** | less metrical tension | `num_viols_allparse_sum` (MTS per window) | aligned LOWER |

The lineage statistic is the mean over windows, stratified by `num_monosylls` (0–3, 4–5, 6–7, 8–10) with the same direct-standardisation rule as H1. The draft shows monosyllable count predicts metricality, and aligned text uses fewer monosyllables (smoke 2: 5.5 vs 5.9 per window).

Secondary: `imperfect_s_unstress`, the share of windows with any `*s/unstressed` tension (the draft's §4 measure), aligned LOWER; per-constraint tension, exploratory.

**Human baseline, descriptive, no test.** Each arm's window distribution is placed against the reparse baseline by metagenre (Poetry, Fiction, Non-Fiction) and 50-year period, 1600–2015. The comparison is LLM narrative prose against human Fiction. Under H2, aligned prose sits nearer to Poetry and to late-period Fiction than base prose does. In the draft's terms, alignment would make prose less antimetrical.

## H3: alignment changes clause construction

Six syntax predictions. Their directions were suggested by smoke test 1 (Disclosures), which saw 72 passages. That is too few passages to be a result, and too few lineages to be worth holding back: all 37 lineages, including the six the smoke test drew on, count toward H3, as toward everything else. They are predictions, tested like H1 and H2; the disclosure says where they came from.

Grain: `by_passage.csv`, `version == "orig"`, lineage mean over passages.

| # | Measure | Predicted direction |
|---|---|---|
| H3a | `dep_relcl` (relative clauses per 100 words) | aligned HIGHER |
| H3b | `left_head` (share of dependents preceding their head) | aligned LOWER |
| H3c | `dep_dist` (mean dependency distance) | aligned LOWER |
| H3d | `dep_advmod` | aligned LOWER |
| H3e | `phrase_cv` (CV of punctuation-phrase length) | aligned LOWER |
| H3f | `sent_len_cv` (CV of sentence length) | aligned LOWER |

## Declared contrast without a direction: arrangement or word choice

Each passage is also measured with its content words permuted within POS class (`shuffle_pos`) and across the passage (`shuffle_all`). Punctuation stays fixed and the original sentence boundaries are imposed, so sentence lengths are identical. For the lexical-grid measures (`clash_lex_rate`, `lapse2_rate`, `alt2`, `ibi2_cv`) and the H2 measures, the **arrangement effect** is `orig − shuffle_pos` per passage, compared aligned vs base over lineages.

No direction is registered. If an H1/H2 difference persists in `shuffle_pos` it is a word-choice difference; if it appears only in `orig` it is an arrangement difference. Both are findings, and they are different ones. The design follows the antimetricality small data's original/randomized/scrambled types.

## Disclosures: what was seen before this was written

1. **Smoke test 1** (prosodic session, 2026-09-24): 6 lineages (Olmo-3-1025-7B, Mistral-7B-v0.1, Llama-3.1-8B, granite-3.0-8b-base, Falcon3-7B-Base, llama-7b) × 6 no-demonym pure stories per arm, drawn from judged_stories_v2. Aligned vs base: `dep_relcl` up in 6/6 lineages, `left_head` up in 0/6, `dep_advcl` and `dep_prep` up in 5/6, `dep_advmod` up in 1/6, `dep_dist` up in 1/6, `phrase_cv` up in 1/6, `sent_len_cv` up in 3/6 (d −0.57). Stress measures null. A best-parse violation score (DEFAULT six-constraint meter, not H2's) was slightly HIGHER for aligned (1.39 vs 1.33, 4/6 lineages): **evidence leaning against H2**, seen before it was registered.
2. **Smoke test 2** (this producer's `--smoke`, 36 passages, 3 per cell, 12 cells): arm means were printed. `orig`, aligned vs base: `clash_rate` 0.380 vs 0.382, `clash_lex_rate` 0.339 vs 0.333, `alt2` 0.647 vs 0.631, `ibi2_cv` 0.393 vs 0.400, `num_parses` 4.18 vs 4.13, MTS 10.52 vs 10.19, `imperfect_s_unstress` 0.79 vs 0.74. **H1 mixed, H2 leaning against**, on a sample too small to test.
3. RH asked for "10-word slices". This registration uses the draft's 10-**syllable** windows, the protocol of the 468K baseline. The small data's n-word windows (`new_ngram`, 5 words per the antimetrical data README) are not implemented; adding them would be an amendment.

## Amendments

Append only, with date and reason.
