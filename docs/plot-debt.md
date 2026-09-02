# Plot debt

Experiments with findings but no figures. Ordered by argumentative priority for the book/CI article, not by folder size.

Status markers: `TODO`, `IN PROGRESS`, `DONE`, `BLOCKED <reason>`.

## displacement/displacement_axis (21 scripts, 0 figures)

The largest experiment in the repo with zero figures. Carries the mass-direction result, the naming comparison, the loo at 50 lineages, and the lift dose reversal.

1. **Per-lineage displacement rate** TODO
   Finding: 62.7% of cells nice-ward, 17/21 lineages replicate, bloomz reversed.
   Figure: dot strip or forest plot, per-lineage displacement rate (%) with z-score, ordered by rate, bloomz highlighted as reversed.

2. **Dose quartiles** TODO
   Finding: displacement rate 2% to 38% monotonic across base_naughty_mass quartiles.
   Figure: stacked bar, 4 quartiles x (churn / displacement / reverse %), n per bar.

3. **Six kinds of displacement** TODO
   Finding: euphemism, referent substitution, modality shift, proceduralisation, semantic escape, outcome reversal.
   Figure: paired slope panel, for each of 6 exemplar frames top 6 fallers + top 6 risers with p_base to p_aligned arrows.

4. **Mass-direction heatmap** TODO
   Finding: per-domain dN sign tests, 25/48 hold under both units.
   Figure: heatmap, domain x scale, color = median dN, glyph = significant under frame/lineage/both.

5. **LOO magnitude comparison at 50 lineages** TODO
   Finding: bge 73% vs named 62% of benchmark, nothing reaches it.
   Figure: grouped bar, model (emp_mean, v6, inst, v6+inst, bge_pc25, named+bge) x median R2, benchmark line at emp_mean. Source: MAGNITUDE_AT_50.md.

6. **Naming gain reversal under lift** TODO
   Finding: naming gain null (p=0.67) under naughty-mass, significant (p=0.015) under lift.
   Figure: paired bar, low/high dose half |dN|/nullabs, old dose vs lift side by side.

7. **Per-domain rho signatures** TODO
   Finding: vocalisation for identity, harm for violence, mundanity for sexual. Kruskal rejects common direction on 10/12 scales.
   Figure: small-multiples heatmap, 4 domains x 12 scales, color = median rho, asterisk = Bonferroni significant.

## displacement/rate_and_magnitude (1 script, 0 figures)

8. **Rate and magnitude by language** TODO
   Finding: English both rate and magnitude rise with dose. Chinese rate rises, magnitude INVERTS (dispersal).
   Figure: faceted slope chart, en vs zh, 3 outcomes (departed, arrived, n_movers), dose on x, per-lineage slopes as faint lines, median bold, sign counts annotated.

9. **Tail excess inversion** TODO
   Finding: tail_excess slope negative in English, positive in Chinese.
   Figure: bar chart, en vs zh median tail_excess slope with sign count.

## displacement/named_under_dose (4 scripts, 0 figures)

10. **Dose interaction on naming** TODO
    Finding: norms recover 8% to 40% of headroom in high-dose stratum; softens to 20% to 34% under lift.
    Figure: grouped bar, low/high dose x predictor (norms, bge, benchmark), % of headroom, lift comparison as second panel.

11. **ICC variance decomposition** TODO
    Finding: ~35% word, ~12% context, ~53% model.
    Figure: stacked bar of three variance components.

## displacement/existence (2 scripts, 0 figures)

12. **Content selectivity by lift** TODO
    Finding: higher-scene words lose more mass (40/50, p=2e-5), selectivity strengthens monotonically with lift (NULL at <0, p=1e-6 at 0.5-1).
    Figure: faceted scatter, 4 lift bands, scene (x) vs delta (y), regression line, sign count in subtitle.

13. **Same-kind landing** TODO
    Finding: freed mass goes to same-kind risers (47/49), +40% more than NONE risers.
    Figure: bar chart, same-kind vs NONE riser mass gain, intermediate scene annotated.

## readout_share (1 script, 0 figures)

14. **State vs readout: magnitude and structure** TODO
    Finding: state carries ~90% of magnitude, readout ~10%, but both carry within-kind structure equally.
    Figure: two-panel stacked bar, (a) magnitude (absolute dN) by component, (b) within-kind ratio by component.

## passage_analysis/surprisal_matrix (2 scripts, 0 figures)

15. **Surprisal matrix** TODO
    Finding: self H falls -0.18, external Q falls -0.14, outsider's excess Q-H RISES +0.04 (19/20 up).
    Figure: paired dot/slope, 20 lineages, three measures (H, Q, Q-H) base to aligned connected.

## passage_analysis/syntagmatic_damage (3 scripts, 0 figures)

16. **Composition vs level** TODO
    Finding: passage effect is composition (-1.31) not level (+0.02); forced continuation shows no downstream propagation.
    Figure: two-panel, (a) stacked bar of composition vs level vs gate, (b) offset curve of forced-word surprisal excess across positions.


## Lower priority (text-only experiments, smaller findings)

- `instrument_calibrations/dose_response` (20 scripts) -- the loaded-word construct and validation. Figures would be calibration plots; not paper-facing.
- `instrument_calibrations/contextual_norms` (4 scripts) -- v6 rating distributions. Supplementary.
- `passage_analysis/passage_norms` -- passage-level norm analysis.
- `passage_analysis/selection_and_combination` -- Jakobson decomposition.
- `passage_analysis/second_order_naming` -- second-order prediction.
- `passage_analysis/predicting_aligned_text` -- aligned text prediction.
- `posttraining_corpus_analysis` (5 sub-folders) -- SFT/DPO corpus analysis.
- `division_of_labour` (3 sub-folders) -- SFT vs DPO share.


## Fences

- A figure without a producer in its own folder does not exist.
- Decompositions print beside aggregates (per-family constituents alongside cross-family numbers).
- The slice goes in the subtitle, on the figure, not in a caption someone will strip.
- A null panel is content, not filler.
- Read the finding's own fences and retractions before drawing from it.
