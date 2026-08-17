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
- **Anything reading `p` closely.** `term` sums the model's diffuse tail across 48,197 boundary tokens and multiplies into every `p`. Whether that is cosmetic for ordinary words is unmeasured, and it is a v4 question.

## 6. Testing, of which there is none

The archive shipped Playwright. v3 has no UI test of any kind, and this session shipped three bugs that only the rendered page would have caught: a focus ring drawn over the plot, an aspect ratio measured from the wrong element, and a viewport-relative height that is wrong the moment the page scrolls. All three were found by looking, which does not scale and did not catch them before they were committed.

The cheapest useful test is not a full suite: it is one smoke run that loads each panel against a live server and asserts no console error and a non-empty root. That would have caught none of those three, which is worth saying out loud -- **the class of bug this panel produces is visual, and the honest first test is a screenshot diff, not a DOM assertion.**
