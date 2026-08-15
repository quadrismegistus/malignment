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
