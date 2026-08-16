# How results are stored

RH, 2026-08-16, before any result was recomputed in this repo:

> *"every result records the model and prompt population from which it worked — explicitly somewhere and also by storing results in long-form by model and prompt rather than only summary statistics"*

Two rules. Both are about the same failure: **a number that cannot say what it was computed over cannot be checked, corrected, or reused.**

---

## 1. THE STORED THING IS LONG FORM. SUMMARIES ARE VIEWS.

One row per **(model, prompt)** at minimum — per (model, prompt, word) where the metric has that grain. A mean is derived at read time and never stored as the only record.

**This is already how `movement` works, and that is the model to copy:**

    movement          (pair, prompt, word)   53.7M rows   STORED
    movement_cells    (pair, prompt)                      VIEW
    movement_edges    (pair)                              VIEW

`views.py` argues it out: *"They are not three datasets — they are one dataset at three grains… A stored rollup can disagree with its source. That is the failure this repository is a response to."* ClickHouse aggregates tens of millions of rows in well under a second, so a rollup costs nothing to recompute and everything to store.

**What the grain buys, concretely, from this repository's own history:**

- The dolphin artefact was **12.7×** and it *reversed an ordering* — the most-displaced model became the least. Visible because per-cell rows existed to inspect; a stored mean would have moved and said nothing about why.
- The SFT/DPO division-of-labour result rested on a DPO population that changed from 22 to 17 edges. With long form it is a re-query; with stored summaries it is a re-run of everything.
- `js_fall + js_rise + js_still + js_tail == js_total` is checkable **per cell**, and the ledger `arrived − departed + mass_still + resid_delta == 0` caught a defect in 12,389 of 249,858 cells. Neither identity exists at summary grain.

**A summary may be materialised only when a measured timing says a view is too slow for something real, and the timing goes in the commit.** A materialisation justified by a number is maintainable; one justified by a habit is the thing that drifts.

## 2. EVERY RESULT NAMES ITS POPULATION — AS A RULE *AND* AS MEMBERSHIP.

Not one or the other:

- **The rule** so the population can be rebuilt, and so a reader can see what it would include tomorrow.
- **The membership** — the explicit ids — so the rule can be checked, and so a later change to the rule is visible as a diff rather than as a silently different answer.

`roster/models/POPULATION.md` is the worked example for models: the rule in prose, `python -m malignment.population` as its executable form, and the derived list as its receipt, with *"if they disagree, the file is wrong."*

**Why both.** The archive kept four population artifacts — `model_registry.json`, `lineage_map_models.json`, `base_aligned_pairs.json`, `lineage_representative_pairs.txt` — and got **six different answers to "how many representative pairs" in one afternoon**. Each was a list without a rule. Conversely a rule with no membership cannot be audited: `landed_v3` globbed a directory while its data came from the store, and nothing tied them, so a checkpoint could report landed and hold no cells.

### What a population declaration must carry

| field | why |
|---|---|
| model ids | the explicit membership |
| prompt ids **and texts** | 2,888 admitted prompt_ids collapse to 2,806 unique TEXTS — 82 ids share text, and the store keys on text. Counting by id and joining by text is two populations wearing one number. |
| the rule, as runnable code | so it can be rebuilt |
| `rule_version` + `dict_sha` | which INSTRUMENT produced the cells. A rule bump makes different data; the twp key already carries both for exactly this reason. |
| what was EXCLUDED, and why | absence and refusal are the same shape in a table |
| date | populations move; ours moved six times on 2026-08-15/16 |

### Exclusions are part of the declaration

A result computed over 49 lineages when 52 roots exist must say which three left and why — here: `phi-4`, `Pharia-1-LLM-7B-control-hf`, `Teuken-7B-instruct-commercial-v0.4`, all aligned models whose pretrained ancestor was never released. **A population is defined as much by its refusals as by its members**, and a refusal nobody recorded reads later as an oversight.

The same applies to prompts: `Prompts.all()` returns 2,783 live rows, and 105 are struck (93 RETIRED, 10 MIXED, 2 DISPUTED). A result over "the prompts" must say which sense — and this repo shipped for a day with the status gate dropped, silently reinstating rows a previous seat had withdrawn.

## 3. THE TEST

Before a result is quotable, it must be possible to answer, **from the stored artifact alone and without asking the person who ran it**:

1. Which models? Which prompts? Which instrument (`rule_version`, `dict_sha`)?
2. What was excluded, and for what stated reason?
3. Can the summary be re-derived from stored rows, and does it match?

If any answer requires a memory, a shell history, or a script that no longer runs, the result is not yet a result.
