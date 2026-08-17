# app TODO

Next steps for `ui/` and the routes in `malignment/serve.py` that feed it. Written 2026-08-17 after surveying the archive's app (`malign-logits/ui/`), which had **21 components across 17 nav sections** against v3's **5 across 3**.

Ordered by whether the thing is broken, missing, or merely absent. Each item says what is measured and what is a guess.

## The archive is not a porting checklist, and that is the main finding

The archive grew one bespoke component per finding: `DisplacementSankey`, `ResistanceTrajectories`, `SurvivalDecay`, `ContradictionChart`, `LogitLensChart`, `TokenShifts`, `TrajectoryChart`, `CrossFamilyHeatmap`, `CensusGrid`, `BeamExplorer`, `PassageExplorer`, `GenerationChart`, `TreeSankey`, `PairsList`, `DisplacementChart`, `DataExplorer`. Seventeen nav entries, each a hand-built view of one result.

**v3 is organized the other way round.** The register is the primary object: an experiment declares itself, produces `results/`, and the app READS them. So the equivalent work here is not seventeen components, it is a small number of generic affordances that make any registered result legible. Porting panel-by-panel would rebuild the thing the register replaced, and most of those components have no data behind them in v3 anyway (checked below).

The exception is `SlotExplorer`, which is an authoring tool rather than a view of a finding. It was ported deliberately and is the one place bespoke work belongs.

## 1. Defects I introduced and have not closed

- **`scripts/ingest_slots.py` does not exist.** `slots.py` cited it as the deliberate step that moves authored items from `$MALIGNMENT_DATA/slots/` into `roster/prompts/slots/`. The citation was wrong and is now marked as such; the script is still the missing half of the authoring loop. Save writes outside the repo and nothing brings it in.
- **The 86 migrated items are invisible to the app.** `roster/prompts/slots/round3.yaml` exists and no route reads it, so the app cannot show what has already been authored. This is what makes the item below worth doing.
- **25 `svelte-check` errors, all pre-existing implicit `any` on callback parameters.** Verified against a clean HEAD worktree rather than assumed. None are new, none are load-bearing, and a UI that typechecks clean is a UI where a real error is visible.

## 2. Slot panel, in rough order of what an author would miss next

- **List and load saved items.** `/slot/saved` exists and returns them; nothing renders it beyond a count. Without this, save is write-only and an author cannot revisit a frame, which is most of what authoring is. Loading an item back into the panel (prompt, tags, domain) is the same route plus a click.
- **Show the round3 86 as a starting library**, once a route reads them. An author writing a new frame should be able to see the ones that exist rather than duplicating them by accident. Note the two pole formats: `round3.yaml` is migrated to lists, the archive original is comma strings, so a reader must handle both.
- **A variant control.** `item_id(prompt, variant=...)` and `/slot/item_id?variant=` both exist server-side and nothing in the UI can reach them. It matters because one prompt can carry two legitimate pole readings (clothing-vs-accessory against underwear-vs-outerwear, both at purity 1.000), and today the second one silently collides with the first.
- **Collapse the word list.** RH had to ask what it was. It is the candidate list, with bar width as probability relative to the top word, and it is also the reliable click target for words that overprint in the scatter. A toggle would let the plot own the page without losing it.
- **Undo a tag.** Mis-clicking is one keystroke and there is no way back except `clear`, which discards everything.
- **Domain is free text with suggestions and nothing sorts by it yet.** The field exists so a later pass can categorize; the later pass is not written.

## 3. Results are rendered as tables, and some of them cannot be read that way

Every registered result renders through `DataTable`. `removal_rates/results/cells.csv` is 273,918 rows. The row cap is honest -- the payload carries `n_rows_total`, `n_rows_returned` and `capped`, and the panel says so -- but a capped table of a quarter-million rows is a receipt, not a reading.

- **A small chart vocabulary chosen by result SHAPE, not by finding.** A two-column numeric result is a scatter; a grouped one is a bar; a model-by-prompt grid is a heatmap. That is a handful of components serving every experiment, present and future, instead of one per finding.
- **This needs no new dependency and probably should not have one.** The archive reached for d3; `SlotExplorer` draws its scatter with plain SVG and is the existence proof that the simple cases do not need a library. Reach for one when a case actually demands it, and say which case.
- **PNG export.** The archive had `ExportButton`. Figures in this project end up in a paper, and a chart that cannot leave the browser gets rebuilt in a producer anyway. Cheap, and it decides whether these panels are for looking or for using.

## 3b. A figures row beside the results row (RH, 2026-08-17)

An experiment folder can hold `figures/` as well as `results/`, and the panel lets you click through the result files only. Add a second row that clicks through the figures the same way.

**Most of the work is already done and the missing piece is a route.** `/experiment` already returns `figures: [...]` -- `serve.py` collects them at the folder walk -- so the UI has the filenames and cannot fetch the images. What is missing:

- a route that serves one figure file, **validated by membership in the manifest the server walked itself**, never by path. That is the same rule the result files follow, and it is what makes `../../etc/passwd` uninteresting rather than filtered
- the mime map already exists for `.png` and `.svg`, but it lives in `_static` for the built app, so it needs lifting or reusing rather than retyping
- a row in `Experiments.svelte`, and a click that shows the image rather than downloading it

**Expect it to render almost nothing at first, and that is worth seeing.** There is exactly **one** figure committed across every experiment folder in the repo today. A row that is empty for five of six experiments is an accurate picture of the plot debt, and a more useful one than a queue file nobody opens -- the panel would make it visible in the place where the results are already being read.

## 3c. Prompts tab — BUILT, with what is left

Shipped 2026-08-17: a sortable table of the 3,120 declared prompts with their categories and four measured columns, and a per-prompt profile behind a click.

**The measured columns were one view, not a computation.** `movement_cells` already had `departed` (mass fallen), `arrived` (mass risen) and `js_total` (total movement) per `(base, aligned, prompt)`; `prompt_movement` groups them by prompt instead of by edge, restricted to `{db}.endpoints` **by join rather than by a hardcoded list**, so the population is whatever the roster declares. `prompt_coverage` adds `n_models`.

**Cached because it is measured slow, and not materialised.** 13.9s over 400,267 cells. `views.py` says materialise only on a measured reason and that is one -- but a materialised table needs a refresh discipline, and a stale one is invisible, which is exactly what cost a day when `{db}.pairs` went stale with every row count still plausible. The cache carries `computed_at` and the panel shows it.

What is left:

- **The `n_pairs` trap has a label and no guard.** Sorting by `movement` without reading `n_pairs` is the most available mistake the table offers, and nothing stops it: a prompt measured on 9 lineages sorts against one measured on 50. A minimum-`n_pairs` filter, or greying rows below a threshold, would make it harder to do by accident.
- **1,760 measured prompts are not in the declared `prompts` table.** The count is on the panel; the prompts themselves are unreachable from it. Whether that gap is a backlog or a definition is not a UI question.
- **`pair_id` groups run to 14 members, so "related frames" is not always a pair.** 2,355 of 3,120 prompts carry one, forming 1,045 groups, and `pair_role` is usually empty -- so the panel cannot say which member is the contrast of which. Populating `pair_role` is a roster job.
- **The profile's endpoint table and the Plots tab do not know about each other.** Clicking a lineage should offer to draw that prompt's slopegraph for it; the plumbing exists on both sides and nothing connects them.
- **Movement columns inherit the aperture caveats.** `departed` and `arrived` are mass sums over differently-apertured arms, and the leak is 96% co-signed. They are not `dN` and are not blocked by that ruling, but a panel that ranks prompts by them is ranking partly by residual behaviour.

## 4. From the archive, with the data check done

Checked against what v3 actually holds (ClickHouse tables and `experiments/*/results/`), because a panel with no data behind it is a request for a fleet, not a UI task.

| archive component | v3 has the data? | verdict |
| --- | --- | --- |
| `CensusGrid` (which model x prompt cells exist) | yes, `twp_cells` | **worth reviving.** It answers "what can I even ask", which is the question a new panel keeps re-answering badly |
| `TokenShifts`, `DisplacementChart` | yes, `movement`, `movement_cells`, `movement_edges` | plausible, but wait for the `dN` convention ruling -- see below |
| `CrossFamilyHeatmap` | partly, `panel_pairs` / `panel_argmax` | plausible as a generic heatmap rather than a bespoke panel |
| `PassageExplorer`, `GenerationChart` | no passage or generation store in v3 | not a UI task |
| `LogitLensChart`, `BeamExplorer`, `TrajectoryChart`, `ResistanceTrajectories`, `SurvivalDecay` | no per-layer, per-beam or trajectory data in v3 | not a UI task |
| `DataExplorer` (ad-hoc table browsing) | n/a | **deliberately not.** `serve.py` has no query endpoint by design: nothing a client sends reaches SQL, and the archive's `/api/data/csv` grew into a second way to define a population |

## 5. Blocked or waiting on someone else

- **Any panel that renders `dN`.** Two conventions are emitted (`dN` and `dN_renorm`) and neither is canonical; where they disagree in sign the pair is not quotable at all, which is 14.8% of prompts at roster scale. A panel that picks one silently would be making a ruling that is RH's. `sign_disagree` is already in the payload, so the panel can refuse rather than choose.
- **Anything reading `p` closely.** `term` multiplies into every `p`. I recorded "48,197 boundary tokens" here from [6387]; malign corrected it at [6390] and the number is a CJK surface -- for a Latin surface mpt marks 28,823 space-initial, 1,247 punct, 155 empty and **2** CJK. The `murm` 0.534 figure is model-specific too (0.0065 on mpt, i.e. correctly near-certain the word continues).
- **What is real is the punctuation boundary, and it is not a defect of ours** -- it is open in the literature, with Pimentel's own code carrying `# ToDo: Should punctuation be a bow as well?` and the mask commented out. Excluding punctuation from the boundary set rescales words DIFFERENTIALLY, so it changes rankings: `kill` 0.93x, `punch` 0.99x, `spit` 0.56x, **`scream` 0.19x, `cry` 0.12x**. It lands hardest on exactly the substitutes the displacement result is about. RH's ruling.

## 6. Testing — there is some now (`ba769ef`)

Playwright, `npm run test:e2e`. Six tests: five panels plus the three-level drill to a pair's word table. Each assertion traces to a defect that shipped on 2026-08-17 rather than to a coverage target, and each was watched failing.

What it catches, in order of cheapness: uncaught page errors (the `each_key_duplicate` crash), failed in-page requests (the broken `<img>` whose URL lacked the `/api` prefix), and screenshot diffs at a 0.5% pixel threshold (the focus ring over the plot, `punch` printed on `cry`).

What it does NOT catch, established by trying: **document-level assets.** Renaming `static/favicon.svg` and running the suite passed, because a favicon is fetched outside the page's request lifecycle. An earlier version of the config claimed otherwise.

Still open:

- **No test presses `draw` on the Plots tab.** A render is ~13s cold and would dominate the suite, so the panel is screenshotted in its pre-draw state. That leaves the plot-render path — the one that broke on the missing plotnine and on the `/api` prefix — covered only by the API-level checks.
- **The baselines are `chromium-darwin` and machine-specific**, which is Playwright's convention and honest, but means the suite is a local guard rather than a CI one until someone decides what CI here would be.
- **`docs/test_howto.py` has no UI equivalent.** The Python side has executable documentation; nothing checks that this file's claims about the app are still true.

## 6b. The original note, kept because it was right

The archive shipped Playwright. v3 had no UI test of any kind, and this session shipped three bugs that only the rendered page would have caught. All three were found by looking, which does not scale and did not catch them before they were committed. **The class of bug this panel produces is visual, and the honest first test is a screenshot diff, not a DOM assertion** -- which is what got built.
