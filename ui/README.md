# ui

The app. A reader for the store and for `experiments/*/results/`.

```bash
python -m malignment.serve          # the API, port 8431
npm install && npm run dev          # the app, port 5173, proxying /api -> 8431
```

Or build once and let the server hand out the built app on a single port:

```bash
npm run build                       # writes ../malignment/ui_dist
python -m malignment.serve          # http://127.0.0.1:8431
```

## The rule

**The app computes nothing.** Every number on screen comes from ClickHouse or
from a committed result file. If a view needs a number that does not exist, the
answer is a producer in `experiments/`, not a query in `serve.py`.

This is the repo's own rule with a port on it. The archive got six different
answers to *"how many representative pairs"* in one afternoon because the
question had six call sites, and an app is the most seductive seventh: it is
interactive, so a convenience rollup reads as display logic rather than as
analysis, and it is the copy nobody greps because it is not in `experiments/`.

**The single exception is `/slot`**, which runs the twp instrument against a
resident checkpoint. That is a measurement, not a rollup of one; it writes
nothing, and the panel says so on its face.

## The three sections

    Experiments   the hypothesis register, then one page per question
    Roster        which models am I comparing
    Slot          what the model wants to say at this blank

A fourth section is a claim that a fourth kind of thing exists. That is a higher
bar than adding a tab, deliberately — the archive ended at 17 equal-weight tabs
and nothing in the interface could say which of them were dead.

**A question page shows three panels in this order, and the order is the
argument:** the README (the claim and its result), the population receipt (what
it was computed over), then the grains (the rows the summary derives from).
`RESULTS.md` §3 asks whether a result can be checked from the artifact alone —
which models, which prompts, what was excluded, does the summary re-derive. That
is those three panels, in that sequence.

## Things that cost something to learn

**Declare the window, always.** `ResultRows` makes `n_rows_total` and
`n_rows_returned` REQUIRED fields, so a table cannot be rendered without the
number that says whether it is complete. `cells.csv` is 273,918 rows and the
default cap is 2,000. A windowed view beside an unwindowed statistic is a
mismatch no reader would suspect, because both are correct and they describe
different populations — there is no error for it and it survives every check.

**Values are printed as the file stores them.** No rounding, no thousands
separators, no `NaN` for a blank. A viewer that renders `0.00366555845` as
`0.0037` is showing something the result file does not say.

**Look at the rendered page.** Two real defects shipped through a clean
type-check and a clean build, and both were caught by rendering:

- a byte formatter divided by 1024 once and called it MB, so a 37 MB file
  displayed as `36270.6 MB`
- the pooled `/slot` path paired one model's residual with a mean over two, so
  `sum(words) + residual` came to `1.0499` instead of 1

Neither raised anything. The code compiled, the types were right, and each
number was individually plausible. **The image catches what you already
believe**, which is exactly what a review of your own code cannot.

**No default model on `/slot`.** A default pool is a population choice, and one
baked into a client is one nobody reports. The archive shipped a client default
that silently overrode the server's, so the app ran a population the server's
own test never exercised.

**`navigator.clipboard` is undefined over plain HTTP to a non-localhost host.**
The dev server binds `0.0.0.0` and is reached over Tailscale, so the
secure-context requirement is not met and `writeText` silently no-ops. The
copy button uses the `execCommand` path and reports failure either way — a copy
button whose failure is invisible is how the archive's went unnoticed for weeks.

## Not here yet

**The bge axis**, which gives the Slot scatter its x. v3 has no
sentence-embedding path, so the scatter is not drawn at all rather than drawn
against a meaningless horizontal. See docket [6360] for the port proposal and
the measurement behind it.
