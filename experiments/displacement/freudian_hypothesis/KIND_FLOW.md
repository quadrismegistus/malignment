# Editing `kind_flow.py` — handoff

Written 2026-09-20, for whoever touches this figure next. RH went back to writing at the point where the plate was good enough to sit in the article; what follows is what is settled, what is not, and the ways this file has already gone wrong.

## What the figure is

Three columns. Base kind → aligned kind → what happened to the affect, read blind by `tasks/fates.py` over the charge corpus. The article's plate is `kind_flow_en_either`, exported to `~/Dropbox/Prof/Articles/TheoryMachines/paper/figures/` as `fig-kind-flow-en.{tif,pdf,png,caption.txt}`.

## Running it

The repo venv is required (`pydantic`, `PIL`); bare `python3` fails at the `tasks.fates` import.

```
cd experiments/displacement/freudian_hypothesis
../../../.venv/bin/python -u kind_flow.py --test either \
    --also ~/Dropbox/Prof/Articles/TheoryMachines/paper/figures \
    --as-name fig-kind-flow-en
```

The other three live variants, all of which must be regenerated when the drawing code changes or `results/` goes stale in a way nobody notices:

```
--test either --high-lift --lift-cut positive
--lang zh --test either
--test permutation --high-lift --lift-cut positive
```

Each run writes `.dot`, `.pdf`, `.png` (300 ppi), `.tif` (grayscale, LZW, 300 ppi) and `.caption.txt` into `results/`, under a name that carries **every dimension that changes the figure** — language, lift cut, test. That rule exists because it was once broken: `--test either` and `--test transpose` both wrote `kind_flow_en`, a loop ended on `transpose`, and the wrong figure went to Dropbox captioned as the right one (`00f8dd18`). RH caught it by looking at the Dropbox copy.

## The invariants this file keeps breaking

Four of these have recurred. They are in the source as `#:` blocks at the site; they are here because a fresh session reads a handoff before it reads 800 lines.

**A number on a node must sum from the arrows that reach it.** Four instances so far, each through a different route: full marginal against a filtered render; marginal against tested triples; the selection leaving `feeling arrives` with no arrow at all. The current form is `155 (149 drawn)` where the two differ, and a fate node is emitted only if some arrow reaches it.

**One mark, one meaning.** Fill, line style, and width have each been retired for carrying a second encoding. Width is frequency (sqrt, not log — log put 9.4× of count into 1.6× of width). Arrowhead on 1→2 is the *kind* of evidence; on 2→3 it is significant/not. Line style carries nothing. Do not add a third.

**Significance is not prevalence.** Drawing only the significant onward flow made the figure assert the opposite of its own data: `thing → thing` is none 40, kept 27, gone 14, and only GONE is over-represented. Each edge now draws its largest fate plus any significant one.

**A hand-picked label must resolve to a row.** The thirteen in `EXEMPLARS` were each checked against `fates_corpus_en.jsonl` — edge match, frame exists, `_base` holds the left word, `_aligned` the right — before being wired. Do the same for any addition. The check is a ten-line script and a label that resolves to nothing is a fabricated example.

**The test must see the figure's population.** `kind_permutation` counts every frame with a channel; the figure draws frames with a channel and an affect fate. Pass the drawn rows, or a *q* gets computed on a population the node count does not describe.

## Open — in the order I would do them

**`decorate=true` on the 2→3 edges.** This is the one RH hit directly. Graphviz parks a spline label wherever it likes, and `bottom → chin` ended up nearer the `procedure` node than its own `thing → thing → feeling kept` arrow, which is what prompted "what frame is bottom → chin from?". `decorate=true` draws a leader line from each label to its edge. Try it on the 2→3 block first; it may be enough on its own, and if it is not, `headlabel` with `labeldistance`/`labelangle` puts the text at the arrowhead instead. Check it does not push the plate past 4.8 in.

**Say in the caption what an arrow label IS.** This is the more serious one and it is not cosmetic. `bottom → chin` reads as "bottom became chin" and means "`bottom` is the word the roster most agreed lost probability in this frame, `chin` the word it most agreed gained it". They are two independently ranked heads, not an attested swap. It matters because the charge numbers diverge: `bottom` is 6.0 and `chin` is 2.06, so the pair looks like a collapse, while the group means are 4.14 → 4.05, flat. Every label in the figure carries this, `kill → scream` included, and the hand-picked ones do too. One clause in the caption fixes it.

**`ATTENUATED` is used 3 times in 2,244 frames.** The coder's options are SAME (341), ONE_SIDE (236), RECOLORED (172), NEITHER (1,492), ATTENUATED (3). So `feeling kept 155` means *a feeling is present on both sides*, not *undiminished* — the instrument has an intensity cell and in practice does not use it. Any sentence in the paper reading 155 as the feeling surviving intact claims more than the coder said. Worth a line in the README and worth deciding whether the task prompt is what suppresses it.

**RH has "some other nits", unlisted.** Ask before assuming the plate is finished.

**paper-claude's stage-three encoding.** He asked for word pairs on stage one and counts on stage three; RH's standing instruction is pairs. It is currently pairs on both, which resolves the mixing fault either way. If RH ever prefers the other resolution it is a two-line change in the onward-arrow block.

## Numbers a future session will want and should not re-derive by hand

Over `results/fates_corpus_en.jsonl`, English frames only (the file holds both; `load()` filters on a CJK regex, so a count taken without that filter will not match anything here):

```
2,244  coded
1,695  kind agreed across the two label orders   -> columns one and two
  361  of those the coder found a feeling in
  237  of those on one of the twelve DRAWN edges -> column three
  433  base-side feeling + agreed affect, kind agreement NOT required
  362  of the 433 keep or change it = 83.6%      -> the rate quoted in the text
```

Four nested selections and one that is not nested at all. `corpus_affect()` computes the last two so the caption cannot drift from the rows. paper-claude's note gave 464 for the 433; the rate was right and the denominator was not.

## Related producers

- `path_flow.py` — the triple test (base, aligned, fate) against a fate shuffle, one-sided, BH. `kind_flow` imports `paths()` so there is one implementation.
- `tasks/fates.py` — the coder. `orient()` is where `affect_relation` + `stronger_affect` collapse into the five fates the figure draws.
- `results/fates_corpus_en.md` — the human-readable sheet, and the place the marginals and dose tables live. Anything the figure declines is still there.

## History

`884ecaec` second test · `83a7cd26` two figures, middle column · `00f8dd18` filename carries the test · `33ff488c` significance ≠ prevalence, MIXED restored, sqrt width · `197436b8` the caption was setting the plate width · `4d07486c` caption off the plate, denominators named, grayscale TIFF.
