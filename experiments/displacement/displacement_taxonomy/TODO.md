# TODO

## Figures for the paper

These are the static (plotnine, 300 dpi) figures the paper needs from this folder. The interactive web vizzes exist but are not paper figures. All are currently undrawn and would need registrar promotion from `plot-debt.md` before a seat can draw them.

- **The paired metagraph, static.** The web viz at `figures/pairmeta.data.json` shows 101 components coloured SITE red / CONTROL blue with mixed-colour hubs. A static version for the paper should show the same layout with the role mixing visible, captioned with the purity null (p = 0.38-0.50).

- **The site+neutral metagraph, static.** `figures/siteneut_meta.data.json` with the blue singletons floating at the edges. Captioned with the purity result (p < 0.001) and the singleton rate (18-20 of 29 neutrals ungrouped).

- **The ten relations table.** `TAXONOMY.md` as a formatted table: relation name, n components, domains, rating signature (top 2-3 scales), crosses-to-controls yes/no. This is the reference for the paper's taxonomy section.

- **A single-pair exhibit.** One pair (probably pistol/wallet, the strongest) shown as two per-frame operation graphs side by side: the site with `Arrested Discharge` at 27 models and the control with `Transfer to inspection` at 24. Captioned with the transgressive mass of each (52.7% vs 3.2%). This is the image that makes the matched-pair design concrete for a reader.

## Possible further work

- **Prompt-without-text meta-relation pass.** Run the same grouping task without showing the prompt sentence, to test whether the raters' operation descriptions alone carry the relation. Flagged by RH as a follow-up; the prompted version is the baseline to compare against.

- **More matched pairs.** 13 more qualifying pairs are available under the current threshold (23 total, 10 run). Reversals leaned toward sites at 7 of 8 (p 0.070, uncorrected); more pairs could settle this. 115 pairs qualify at the mean threshold, but only 23 at the worst-arm threshold.

- **Sexual pairs.** The mass measure cannot select sexual-coercion pairs because the transgression is contextual (unwanted touch) rather than lexical (no single word in the tail of any axis). A contextual selector using `slot_ratings sexual v2` would be needed.

- **Tulu ablations.** The 7 Tulu variants have full coverage on all 35 frames and are the only causal handle on which training stage produces which operation. Unstarted.
