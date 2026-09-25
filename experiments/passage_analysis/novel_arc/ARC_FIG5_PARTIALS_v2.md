# Partial tests of the Figure 5 measures across the four arms (EXPLORATORY)

Producer `arc_fig5_partials.py v2`: the SLOPE IS FITTED WITHIN ARM (both variables demeaned by arm), then applied to the raw values. Pooled-slope version: ARC_FIG5_PARTIALS.md.
Producer `arc_fig5_partials.py` (method in its docstring). Cells: lineages (of 30) whose raw / prefill / continue arm moves from base in the direction of the unpartialled continue effect, with the two-sided sign test p. Bonferroni over the 30 partialled tests below puts the bar near p 0.001.

Meta-text Spearman with concreteness: emotional words -0.78, cognitive words -0.83, valence (vector) -0.06, arousal (vector) -0.84, dominance (vector) -0.46

| measure | unpartialled | partialled on concreteness | concreteness partialled on it |
|---|---|---|---|
| concreteness | 27 (p 0.000) / 29 (p 0.000) / 30 (p 0.000) | -- | -- |
| emotional words | 23 (p 0.005) / 27 (p 0.000) / 30 (p 0.000) | 20 (p 0.099) / 20 (p 0.099) / 26 (p 0.000) | 27 (p 0.000) / 26 (p 0.000) / 25 (p 0.000) |
| cognitive words | 22 (p 0.016) / 28 (p 0.000) / 29 (p 0.000) | 13 (p 0.585) / 18 (p 0.362) / 17 (p 0.585) | 21 (p 0.043) / 24 (p 0.001) / 29 (p 0.000) |
| valence (vector) | 16 (p 0.856) / 10 (p 0.099) / 19 (p 0.200) | 17 (p 0.585) / 10 (p 0.099) / 21 (p 0.043) | 28 (p 0.000) / 28 (p 0.000) / 30 (p 0.000) |
| arousal (vector) | 26 (p 0.000) / 25 (p 0.000) / 29 (p 0.000) | 19 (p 0.200) / 11 (p 0.200) / 22 (p 0.016) | 25 (p 0.000) / 28 (p 0.000) / 27 (p 0.000) |
| dominance (vector) | 22 (p 0.016) / 27 (p 0.000) / 18 (p 0.362) | 12 (p 0.362) / 19 (p 0.200) / 7 (p 0.005) | 28 (p 0.000) / 25 (p 0.000) / 29 (p 0.000) |
| cognitive + emotional | 25 (p 0.000) / 28 (p 0.000) / 30 (p 0.000) | 17 (p 0.585) / 17 (p 0.585) / 26 (p 0.000) | 22 (p 0.016) / 25 (p 0.000) / 22 (p 0.016) |

## Split-half reliability across the 120 meta-texts (odd vs even passages; Spearman-Brown)

- emotional words: split-half r 0.901, Spearman-Brown 0.948 (n 120 meta-texts)
- cognitive words: split-half r 0.823, Spearman-Brown 0.903 (n 120 meta-texts)
- concreteness (measure_lltk, passage-weighted): split-half r 0.899, Spearman-Brown 0.947 (n 120 meta-texts)

## Reading (agreed with the abstraction seat, 2026-09-25)

- Concreteness separates every arm and survives every reverse partial.
- With the within-arm slope, the emotional-word rise in the CHAT-ASKED arm exceeds what concreteness predicts: 26 of 30 lineages, sign-test p < 0.001, which survives Bonferroni over the 9 list-by-arm cells (0.0056). The raw and prefill cells (20 of 30, p 0.099) do not, so the claim rests on the asked arm alone.
- Word it as the chat-asked arm, not alignment in general. That arm's user turn is 'Continue this text: ' plus the stem (TEMPLATE_ARM.md), against prefill's reply opening on the stem: the difference is being addressed with a request, so part of the excess may be a task-framing effect of the request.
- Cognitive words and vector arousal are accounted for by concreteness in every arm; vector valence is null throughout. Dominance falls in the asked arm (7 of 30, p 0.005), just short of Bonferroni: a lead, and the same arm pairing more emotion with less dominance.
- Reliability rules out a precision artefact at meta-text grain, not at passage grain.
- Not yet reconciled: the 25-pair passage-level decomposition on usas_x (model_placement raw arm, within-passage slope) kept ~60% of the aligned rise after a concreteness partial (20/25 pairs); here the raw arm keeps less. Measure (usas_x vs the v4 emotion list), population (model_placement vs TEMPLATE_ARM), grain (passage vs meta-text) and slope all differ, so both can hold; the write-up needs one sentence saying which differences matter.
