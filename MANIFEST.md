# MANIFEST — what crossed over, when, and why

Append-only. **Every file that arrives records the reason it arrived, on the day
it arrived.** The old repo's failure was not that it held dead code; it was that
nothing arrived with a reason, so nothing could ever be shown not to belong —
371 dead UI files and 42 superseded findings sat beside live code because no
rule would have caught them. This file is that rule.

If you cannot write the reason, the file does not come.

## 2026-08-15

| file | from | why |
|---|---|---|
| `malignment/ch.py` | `malign_logits/ch.py`, unchanged | The one way to ask ClickHouse a question. Earned its existence in evidence: a 2026-08-14 survey found 85 files touching CH and 69 shelling out themselves, repeating three defects the campaign had already paid for — silent row drops, hand-rolled TSV escaping, and a serialisation format acting as a population definition. `JSONEachRow` dissolves all three. |
| `roster/models.json` | extracted from `MODEL_FAMILIES` + `model_curated.json` + `registry_extra_models.json` | THE authored roster. Hand-edited; no script writes it. Round-trip verified lossless against the old repo's 64 families × 10 fields, 0 differences. |

## Not brought, and the reason

| not brought | why |
|---|---|
| `cache.py` (1,548 lines) | The stash is working state, not the corpus. ClickHouse holds every tabular measurement — twp_words 95M, movement 77M, logit_probs 1.7B. What the stash uniquely holds is 76 GB of dense embeddings and 11 GB of parsed docs, which are blobs, not rows. If those are needed, a blob reader arrives then, with its reason. |
| `model_registry.json`, `lineage_map_models.json`, `base_aligned_pairs.json`, `lineage_representative_pairs.txt` | Four artifacts that produced six different answers to "how many representative pairs" on 2026-08-15. Replaced by one table and one query. |
| `logit_probs` (CH, 1.7B rows, 7.13 GiB) | **Abandoned mid-ingest and unused.** RH, 2026-08-15: *"we gave up on storing logit_probs in CH part way through"* and *"we basically never use logits, everything is on twp."* Measured: 123 of 401 models, 2,648 of 4,413 prompts, and per-model coverage ranges from 2,583 prompts (Olmo-3-Think) to 103 (croissant). A query across it answers about whichever models finished. **1.7B rows reads as authoritative and is 31% of the roster** — the same shape as a July run-spec still stamping status. The raw `.f16` dumps behind it (39 directories on /Volumes/diderot) are archive. |
| `meta/` (505 scripts) | The working record of waves 1–2. Stays in the archive until wave 3 needs a specific one. |
| `ui/` (371 files, 2 touched in 30 days), `findings/` (45 files, 42 cited by nothing) | Dead. |

## 2026-08-15, later

| file | from | why |
|---|---|---|
| `malignment/movement.py` | `malign_logits/movement.py` | The movement RULES and arithmetic — `Rule`, `CANONICAL`/`LENS`/`DRAW`, `movement()`, `decompose`, `js_terms`. 81 `meta/` scripts import it, the most of any module. Kept for its computation, not its accessor: `word_probs` reads a cell at a time, and the access pattern moved to SQL over a precomputed table. |
| `malignment/produce_movement.py` | new | Drives those rules across every DERIVING edge the roster declares and writes the `movement` table. The population is the roster, so a new edge in `models.yaml` enters on the next run with no pair list to maintain. |

## Brought and dropped within the hour

| file | why it came, why it went |
|---|---|
| `malignment/ch_read.py` | Came as `movement`'s ClickHouse read path — a bulk prefetch justified by a real measurement (192 ms/cell point-query vs 0.097 ms/cell bulk). Went because RH: *"ch_read wrote that docstring before we had the movement tables in CH — grep for scripts that query movement from CH, that's the new method."* 16 archive scripts query the 77M-row `movement` table directly; SQL over a built table does not need a prefetch. **346 lines that solved a problem the design had already moved past.** |

## Not brought, with the reason measured rather than assumed

| not brought | why |
|---|---|
| `registry.py` (721 lines) | SUPERSEDED, not deferred. `base_of`, `parent_of`, `children_of`, `variants_of`, `all_bases`, `stage_of`, `base_aligned_pairs`, `nickname`, `info` are all queries against `checkpoints`/`edges` now. Its three `DPO_EQUIVALENT_RULINGS` were carried into `roster/models.yaml` first — a ruling in a Python dict dies with the file. |
| `fields.py` (813 lines, 41 importers) | Looked free: zero module imports. It is not. It needs 8.6 MB of lexicons under `meta/M01_displacement/lexicons/` AND **two paths outside the repository** — `~/Dropbox/.../norms_sources` and `~/Dropbox/Prof/Code/osp/worddb.byu.txt`. So it is not reproducible from a clone, and a missing lexicon returns no counts rather than an error: an absent thing indistinguishable from a measured zero. When it comes, the lexicons want a privileged `lexicons/` beside `roster/`, and the external paths want an explicit absent-state. |
| `twp.py` (1,279 lines) | MEASUREMENT, not analysis — it runs with a model on a GPU and produces the jsonl this repo ingests. `RULE_VERSION 3`, `dict_sha b16011275c42955c`, CJK prefix trie, mojibake channel, four-way residual: "roughly seventy lines of accumulated rulings". Needed only to make NEW measurements, i.e. the 104 markedness prompts. Comes with `models.py` when that runs. |
| `cell.py`, `step.py` (471 lines) | Exist largely to make a key-value store usable per-cell. With ClickHouse primary a cell is a WHERE clause. Attempt last, expecting them to shrink rather than port. |

---

# STILL TO DO — and why each is not done yet

**This section is in MANIFEST.md and not in a MIGRATION.md, deliberately.** Two
documents about migration state are two sources of truth, and the one that drifts
is whichever gets updated less. What came, what did not, and what remains are
three answers to one question.

## Blocking nothing, waiting on a decision

| item | state | why not yet |
|---|---|---|
| ~~`roster/prompts/`~~ **DONE 2026-08-15** | 2,888 prompts admitted; `prompts.py` reads `pairs/`, `generated/`, `flat/` on the fly, keyed by `prompt_id`, refusing duplicates. Original reason kept: | 2,888 prompts arrived as ~11 populations, and which population a prompt came from is part of its provenance. Split by source, with the loader refusing a prompt that appears in two files — otherwise the multi-source precedence problem is recreated in the authored layer. |
| the 104 markedness prompts | **PARTLY UNBLOCKED — recheck 2026-08-15** | `twp_cloud` is the SOLE source of 104 catalogue prompts (~9,900 cells) including the arm that makes the marked/unmarked contrast computable at all: `'He held her underwater until she stopped'` has 249 models, `'...started'` has 0. Excluded because `rule_version` is NULL. **The fix is to re-measure under rule 3, not to widen the gate** — which needs `twp.py` and `models.py`, i.e. a GPU. **RECHECKED 2026-08-15: the marked arm is no longer empty.** 'stopped' 340 models, 'started' 95, and all 95 hold BOTH arms — so the contrast is computable at n=95 rather than not at all, on rule-3 cells (nothing else can be in `twp_words`). The remaining work is EXTENDING 95 → 340, not creating the arm. Re-stated because the row as written would have sent someone to re-measure prompts that already have data: **a blocked-status file is only useful if the block is re-tested, and this one was recorded when it was true.** 50 prompts in the store are held by <100 models. |

## Needs work before it can come

| item | why |
|---|---|
| `fields.py` (813 lines, 41 importers) | Ported code would need three things fixed first: the `~/Dropbox` paths are now repo-relative (`lexicons/`), but a missing source still DEGRADES rather than refusing, and the BYU lemmatiser should be spaCy — free, already installed with `en_core_web_sm` + `zh_core_web_sm`, and CONTEXTUAL where BYU is type-level. BYU's POS column is loaded and never read, so the swap is lemma-for-lemma. |
| ~~`twp.py` + `models.py`~~ **PORTED 2026-08-15** | `dict_sha` verified `b16011275c42955c` unchanged; `models.py`'s `from . import *` untangled to explicit imports; `runners.py` drives them. Original note: measurement, not analysis: they run a model on a GPU and produce the jsonl this repo ingests. Needed for the 104 re-measurement and nothing else yet. `models.py` opens with `from . import *`, which needs untangling. |
| `cell.py`, `step.py` (471 lines) | Attempt LAST, expecting them to shrink rather than port. They exist to make a key-value store usable per-cell; with ClickHouse primary a cell is a WHERE clause. If most of those lines evaporate, that is the answer rather than a failure. |

## Found here, owed to another seat

### SmolLM3-3B is an M05-shaped ladder we are not using, and its recipe is a DAG

Noted 2026-08-15 while auditing the roster. **This is a note, not a claim on M05** — that is another seat's directory and this records what the roster and the cards say so the decision can be made on evidence rather than rediscovered.

`HuggingFaceTB/SmolLM3-3B-checkpoints` is a **revision container of 133 branches**, verified against the refs API, not a checkpoint:

| group | n | what |
|---|---|---|
| `stage1/2/3-step-*` | **118** | pretraining intermediates, 94.4B tokens apiece (86 / 19 / 13, matching the card's own stage table; 118 × 94.4B ≈ 11.1T against a stated 11.2T) |
| `lc-*-to-*-step-*` | 10 | long-context extension |
| `it-*` | **4** | `it-mid-training`, `it-SFT`, `it-soup-APO`, `it-LC-expert` |
| `main` | 1 | |

**The 118 are the M05-type object; the 4 are not.** M05's unit is "the checkpoint within a single training run — the time axis", and its phase 2 (the pretraining ladder, F24's open TODO) currently rests on **OLMo alone**. A claim about the order in which operations install, derived from one training run, is a claim about that run. SmolLM3 is a second complete pretraining ladder — different lab, different corpus, 3B rather than 7B. The 4 post-training refs are stage ENDPOINTS, one per stage, not a trajectory; they are an M01-shaped contribution (four states to compare) and should not be described as an M05 ladder.

**M05's README needs its population named either way.** It states "no family anywhere releases preference-stage trajectories (agent survey, 2026-08-10, `data/model_revisions.json`)". That file holds **8 entries and SmolLM3 is not among them**. The literal claim survives — `it-soup-APO` is an endpoint, not a trajectory through APO — but "no family anywhere" is not what a survey of 8 establishes. The adjacent sentence, that OLMo base + Think-SFT is "the closest thing any vendor releases to a continuous pretraining-to-post-training run", deserves the same re-check: SmolLM3 puts pretraining, long-context and post-training in ONE repo, where OLMo's join crosses two.

**Why the roster does not represent the pipeline, and cannot yet.** The recipe is not the chain it looks like. From the blog: *"Take each APO checkpoint and create a model 'soup'. Combine the model soup with a mid-training checkpoint that has strong long-context performance"*, at *"a linear merge with weights of 0.9 and 0.1"*. So:

    base → it-mid-training → it-SFT → it-soup-APO ─┐
                                                    ├─ merge 0.9/0.1 → SmolLM3-3B
           (long-context mid-training checkpoint) ──┘

**The final model has TWO parents.** Three things block declaring it:

- `merge` is not in `DERIVING` or `RELATING`. It is not in the op vocabulary at all.
- **`par[child] = parent` is a single-parent map** (`roster.py`, `produce_movement.py`). A second parent does not error — it silently overwrites the first, and the lineage walk then reports whichever edge was read last. This is a schema limit that would fail quietly, which is the kind this repo exists to stop.
- `it-LC-expert` exists as a released revision but **the main card never mentions it**; the blog says they merged rather than shipping a separate expert. Its role is undocumented at card level.

What the roster holds today is a defensible 3-node compression, not the pipeline: `Base --sft--> -checkpoints(it-SFT) --apo--> SmolLM3-3B`. The `sft` edge is correct because the roster pins `revision: it-SFT` and the corpus measured exactly that (`twp_cells.revision = 'it-SFT'`, 2,579 cells). The `apo` edge is the best available label for SFT→final given no APO node exists, and it is imprecise: the LAST operation is a merge, not APO.

**Corpus state, updated 2026-08-16: 2 of 4 post-training rungs measured** (`it-SFT`, and `it-soup-APO` measured locally on this Mac — 2,653 cells, 55.5 min at 1.26 s/cell, no cloud). 0 of 118 pretraining. `it-mid-training` and `it-LC-expert` remain unmeasured.

**What the APO rung showed, and why it matters beyond SmolLM3.**

    Base   -sft->      it-SFT        0.1023
    it-SFT -apo->      it-soup-APO   0.0137
    APO    -instruct-> SmolLM3-3B    0.0115
    Base -> APO   (cumulative)       0.1098
    Base -> final (cumulative)       0.0909

**The final merge moves the model BACK toward its base** — cumulative displacement *falls* from 0.1098 to 0.0909, so the 0.9/0.1 soup with the long-context mid-training checkpoint undoes ~17% of what alignment accumulated. The DAG described above is not a bookkeeping nicety; it is visible in the metric, and it is why `instruct` on that last edge is a compression rather than a description.

**F25's "APO signature" does not survive the measurement.** The classifier asserts *"transparent: argmax preserved from base (APO signature)"* — written when the roster held no measured APO checkpoint. Argmax preserved across the preference step:

| edge | preserved | edge JS |
|---|---|---|
| dpo (archangel) | **95.3%** | 0.0002 |
| apo (SmolLM3) | 86.9% | 0.0137 |
| dpo (OLMo-3) | 77.8% | 0.0301 |
| dpo (Tulu-3) | 75.4% | 0.0418 |
| dpo (OLMo-2) | 70.5% | 0.0580 |
| dpo (Amber) | 48.5% | 0.1697 |

APO sits **inside** the DPO range, and archangel's DPO is *more* transparent than APO. Preservation against edge JS gives **r = −0.966 (n=6)**: transparency tracks how far a step moves the distribution, not which algorithm moved it. **n=1 for APO**, so this does not refute an APO-specific mechanism — it removes the evidence that there was one, and names the amplitude confound any future test must beat. Whoever owns F25 should decide whether the claim is withdrawn or re-specified; it is recorded here because the measurement happened here. Declaring the real nodes would make that gap visible instead of hiding it behind one pinned revision — `movement` only builds pairs with both arms present, so declared-but-unmeasured nodes cost nothing and show up as absent rather than as nothing.

**One card-vs-source conflict to resolve before anyone cites a token count:** the model card says midtraining on **140B** reasoning tokens; the blog says **35B** from OpenThoughts3 and Llama-Nemotron. Not reconciled here.

Also worth its own line: SmolLM3 is our **only APO instance** in 157 checkpoints, and the F25 classifier already asserts an *"APO signature: argmax preserved from base (transparent)"* — a claim never measured against an actual APO checkpoint. `it-SFT → it-soup-APO` would test it directly, on the one family where the parent is released.

## Deliberately never coming

| item | why |
|---|---|
| `registry.py` (721) | Superseded. Every method is a query now. Its three DPO-equivalent rulings were carried into `roster/models.yaml` first. |
| `cache.py` (1,548) | The stash is working state. ClickHouse holds every tabular measurement. |
| `lineage.py` (286) | `lineage` and `depth` are derived columns; `same_base` is a view. |
| `ch_read.py` (346) | Brought and dropped the same hour — a bulk prefetch for an access pattern that moved to SQL. |
| `logit_probs` / the `.f16` dumps | 1.7B rows at 31% model coverage, and unused. |
| `meta/` (505 scripts), `ui/` (371 files), `findings/` (45, 42 uncited) | The archive's job. |

## What would tell us this migration is finished

Not a file count. **An analysis that ran in the old repo, re-run here, agreeing.**
Until one does, everything above is scaffolding that has never been asked a
question it could get wrong.
