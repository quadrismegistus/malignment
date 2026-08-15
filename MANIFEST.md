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
