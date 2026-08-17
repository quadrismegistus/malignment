# prompt_slopes

One prompt, every lineage: what the models put at the blank, before and after.

```
python plot.py "She was so angry she wanted to"
python plot.py "..." --units chains --top 8         # base, sft, pref
python plot.py "..." --words kill,scream,hit        # curated, LABELLED as such
python plot.py "..." --pair "meta-llama/Llama-3.1-8B>allenai/Llama-3.1-Tulu-3-8B"
```

Figures land in `figures/`, named from the parameters, so asking the same question twice overwrites rather than accumulating near-duplicates nobody can tell apart.

## What it is for

**Exploratory.** Type a prompt, get the figure. The point is to be able to ask about a frame that nobody has registered an experiment for, which is what "exploratory" has to mean if it is to mean anything -- and to do it against the committed store rather than by loading models.

## Why this figure could be built now, when a displacement panel could not

**It plots LEVELS, not derived statistics.** Word probability at each rung, per lineage. Two rulings currently block anything that reports `dN`: the convention is unsettled (`dN` and `dN_renorm` disagree in sign on 14.8% of prompts at roster scale) and the leak correction is outstanding (the leak is 96% co-signed with the effect, so `dN` needs a subtractive bound). **Neither touches a level.** A picture of what the models do can be drawn while a statistic computed from what they do is still being argued about.

## The split, and it is the repo's rule rather than a preference

    malignment/movement.py : contrast()     reads the store, returns tidy rows
    experiments/.../plot.py                 turns rows into a picture

Arithmetic lives in the module; this file renders. That is what lets the app request the same figure without a second implementation of the contrast, which is the divergence this repo keeps paying for.

`contrast()` reads **`twp_words`, not `movement`**: `movement` is two columns by construction (`p_base`, `p_aligned`), so a chain with three rungs has no representation in it. `twp_words` is `(model, prompt, word, p)` and handles 2 and N with one query.

## What the chain view shows that the pair view cannot

On `She was so angry she wanted to`, over the 18 declared chains:

    kill      0.0996  ->  0.0512 (sft)  ->  0.0404 (pref)
    scream    0.0508  ->  0.0884 (sft)  ->  0.1045 (pref)

**Most of the displacement is already done by SFT.** The preference step continues it and does not cause it. That is invisible in the 2-rung endpoint view, which shows only the total. Reported here as what the picture shows on one prompt, not as a finding -- `division_of_labour/sft_share` is the registered experiment that owns this question.

## The disciplines, carried from the archive rather than reinvented

Ported from `malign-logits/meta/M01_displacement/scripts/plot_prompt_words.py` (RH's design). **Rewritten in plotnine, not copied** -- the original is matplotlib and the convention of record here is plotnine at 300 dpi. Nothing in a slopegraph with paired intervals needs matplotlib.

- **Word selection is declared and blind to movement.** Default is top-N by mass at the base rung, and the rule is printed in the subtitle. `--words` prints `curated list` instead, because an interval on a word picked *because* it moved is conditioned on that selection.
- **The paired difference is the error bar of the movement.** Marginal intervals can overlap while every lineage moved the same way, so the two largest movers are annotated with the within-lineage paired interval, computed from the same frame the panel draws.
- **Median by default.** Probabilities are heavy-tailed across families and a mean can be one family's obsession. `--stat mean` exists and the choice is in the subtitle either way.

## Two things the panel declares because they are not visible

- **Cells at or below theta are drawn at the floor and counted in the subtitle.** Below theta means smaller than 0.001, not absent, and a slopegraph cannot show the difference.
- **A unit missing any rung is dropped whole and named.** Half a slope is not a slope, and a lineage contributing one endpoint would tilt a median without appearing in the count.

## A defect the rendered image caught and no check would have

The first render printed `punch` on top of `cry` and `go` on top of `slap`. End labels sit where the lines converge, and flat words pile into a band a few thousandths wide. **`geom_text` overlap is invisible to every check that is not the rendered image** -- no assert sees it, and the text-width audits measure against the panel edge rather than against each other. Fixed with a greedy push-apart in data units that moves the text and leaves the points where they are.
