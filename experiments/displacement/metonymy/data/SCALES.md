# The old annotation scales, ported 2026-09-18

Five 0-100 scales from `X_metonymy`, RH's design 2026-08-07, ported from
`malign-logits/meta/M01_displacement/results/x_coder_words.csv`. One file per
scale so nothing sits under a neutral name and gets picked up by mistake --
`coder_scale.csv` did exactly that, holding B while the finding uses D.

Each file: `word`, the two model runs, their `mean`, and `n_runs`.

| file | scale | sentences shown? | axis named by | scored |
|---|---|---|---|---|
| `scale_A.csv` | open dimension | **withheld** | the coder | 75/122 |
| `scale_B.csv` | distance from the body | withheld | **us** | 73/122 |
| `scale_Cexp.csv` | explicitness | withheld | **us** | 74/122 |
| `scale_Ccharge.csv` | charge | withheld | **us** | 74/122 |
| `scale_D.csv` | open dimension | **shown, both** | the coder | 74/122 |

## D IS THE ONE THE FINDING AND THE FIGURE USE

`x_plot_intimacy.py` does `D["intimacy"] = D[["D_opus","D_sonnet"]].mean(axis=1)`.
Its reason: D's two runs agree at +0.888 (verified: Spearman 0.889, Pearson
0.903 on 73 words) and it is the scene-derived scale, so its dimension was
named by the coders rather than imposed. **The word "intimacy" on that figure's
axis is the coders' word, not the design's.**

A against D is the priming measurement: same dimension named and correlated
scores would mean the scene adds nothing; different means the scene effect is
quantified. Both sentences were shown to D, never one, because showing only the
female frame would build the gender asymmetry into the instrument meant to
measure it.

## THE FIGURE'S NUMBERS ARE FROM AN OLDER CSV

    at commit b45d6570 (the figure's own commit)   her -0.668 p=8.1e-11   his -0.450 p=5.9e-05
    on disk now                                    her -0.701 p=3.4e-12   his -0.446 p=6.9e-05
    figure caption                                 her -0.67  p=8e-11     his -0.45  p=6e-05

The caption matches the data as it was when the figure was drawn. A later commit
the same day, `feab501e`, changed `x_coder_words.csv` and `her` moved from
-0.668 to -0.701. The figure was never redrawn. **Anyone regenerating it today
gets -0.70, not the -0.67 in the caption.**

## WHY THESE ARE BEING REPLACED

At 50 endpoint lineages the two prompts produce 851 candidate words, 568 moving
in >= 2 lineages, 479 of those NOUN or PROPN. **The old scales cover 73.** 408
of the 479 nouns are unrated, 85%. The new instrument is `../survey.py`; its
wording and review are in `levels_draft.md`.

These files stay because they are the provenance of a published figure, not
because they are the current measurement.
