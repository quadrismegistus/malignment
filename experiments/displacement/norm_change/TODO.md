# TODO

## Resolve USAS sense ambiguity here too, the way `existence` now does

Added 2026-09-16 by `lacan`, as a note rather than a change: `plot_fields.py` and `plot_arms.py` were being edited in this folder the same evening, so this is add-beside and nothing here has been touched.

### The defect

`run.py:224` weights a word's USAS categories by even division:

    cats[w] = {c2: 1.0 / len(codes) for c2 in codes}

`examples.py:87` does the same thing for its ranking:

    return sum(1.0 for c in codes if c == a.usas) / len(codes)

So a word with five senses contributes a fifth of itself to four fields it does not mean. Measured on the English rated vocabulary: **2,625 of 7,825 coded types (33.5%) carry more than one fine code, covering 50,638 of 156,475 (prompt, word) observations (32.4%)**, mean 1.39 codes per observation.

**And this folder's version is context-free, which `existence`'s was not.** `cats` is keyed on the word alone, built once per language and reused across every prompt and arm, so there is no context available to disambiguate against even in principle. `existence` at least had the cell.

### Why it lands on this folder's headline

The contested target is `Q2.2 Speech acts`, which the README records as ROBUST on lexical + lift, and whose threshold (README line 759) was "chosen after seeing what it does to one contested target (`Q2.2`)". Speech verbs are exactly where the ambiguity concentrates:

- `express` carries `A4.2+`, `M3`, `N3.8+fn`, `Q1.1`, `Z3c`. A fifth each. Only `Q1.1` is speech.
- `said` carries `Q1.1` and `Q2.1`, so half of every `said` lands outside `Q2.2` by construction.
- `point` carries `A10+` and `Q2.1`.
- `add` and `added` carry only `A2.1 Affect: Modify, change` and `N5+ Quantities`. **USAS has no sense for `add` meaning "say additionally" at all**, so the speech use of a common verb is invisible to this instrument rather than merely mis-weighted.

A `Q2.2` rise measured under even division is therefore a rise in a quantity that is part speech and part arithmetic, and the mixture is not constant across arms if the arms differ in which senses they use.

### What exists to fix it with

`experiments/displacement/existence/results/usas_sense.jsonl`: 2,389 English prompts, 50,670 ambiguous words, one `deepseek-flash` call per prompt glossing each candidate in context and returning the codes from that word's own list that match the gloss. 88.7% resolved, 11.3% abstained, 1 word missing, 0.6% off-list codes dropped.

Producers: `malignment/tasks/code_usas_sense_v1.py` and `experiments/displacement/existence/usas_sense.py`. Consumed by `adjacency.py` through `senses_of()` behind an opt-in `--senses` flag, so no recorded number moved without being asked to.

Effect on the words above:

    see       339 uses    308 -> X3.4 Sight alone      S9 Religion survives in 1
    express    56          54 -> Q1.1 alone
    let      1142        1051 -> S7.4+ Permission alone
    die       124         116 -> L1- alone
    point     145          73 A10+, 32 both, 24 Q2.1   genuinely ambiguous, kept so

### Two things that make this harder here than in `existence`

**The unit does not match.** The annotation is keyed on `(prompt, word)` and `cats` is keyed on `word`. Either `cats` gains a prompt dimension, which changes its shape everywhere it is consumed, or the annotation gets collapsed to a per-word modal sense, which throws away the context that made it worth doing. The second is cheap and the first is correct.

**This folder runs Chinese and `existence` does not.** `fields.usas`'s own docstring records that **zh returns every tag while en returns the ranked first one**. So the 33.5% English figure above is the conservative one, computed after the English lexicon already ranked and truncated, and the zh ambiguity rate will be substantially higher. `usas("kill", lang="en")` gives `['L1-']`; `usas("杀", lang="zh")` gives `A1.5.1, A12-, B2-, E2+` and more. The en and zh ambiguity rates are therefore not comparable as measured, and a bilingual fix needs the sense coder run over the 406 zh prompts before any cross-language claim rests on it.

### Suggested order

1. Measure the size of the problem on this folder's own targets before changing anything: recompute `Q2.2` and `L1-` marginals with ambiguous words excluded entirely, as a bound. If the direction survives dropping them, the fix is a refinement rather than a correction.
2. Thread `(prompt, word)` through `cats`, or record explicitly that a per-word modal sense was used and why.
3. Run the coder over zh before any en/zh comparison.
