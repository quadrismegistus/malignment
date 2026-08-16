# The base-model population

**STATUS: DESCRIPTIVE, NOT FROZEN.** RH deferred the freeze on 2026-08-16 ("let's deal with freeze later"). This file states the RULE that defines the population and records the shaping it has already undergone; it does not yet fix membership. When a freeze is declared it will consist of stamping the derived list here on a named date — the rule below is what would be frozen, and it already exists, which is the part that takes work.

---

## The rule, which is what actually gets frozen

A **base model** is a checkpoint that is:

1. a **root** — no incoming `DERIVING` edge in `roster/models/models.yaml`; and
2. **corroborated as pretrained** — either attested `method: pretrain` in `attestations.json`, or explicitly `pretrained: false` and therefore *excluded*; and
3. **measured** — it has cells in `malignment.twp_cells`.

Nothing here is typed by hand. The list below is derived by that rule, and `malignment.roster` reports condition 2 on every build (`roots corroborated as bases: N/N`). **A freeze pins HOW, not WHAT** — a list without its rule cannot be rebuilt, and a rule without its list cannot be checked, so both are recorded and they must agree.

## What shaping happened first, and why that is disclosed

**A freeze cannot stop shaping that already happened.** It can only say when it stopped and what it did. The population moved a great deal on 2026-08-15/16, every change for a stated reason, and a reader is entitled to see the trajectory rather than the endpoint:

| change | effect | why |
|---|---|---|
| phi-4 → phi-4-reasoning → -reasoning-plus edged | lineages **55 → 53** | found twice independently: JS 0.0142 on the similarity screen, then the card said *"finetuned from Phi-4"* |
| falcon-mamba-7b → Falcon3-Mamba-7B-Base edged | **53 → 52** | *"Continue Pretrained from Falcon-Mamba-7b, with another 1500 Gigatokens"* |
| gpt-sw3 nodes removed | **52 → 51** | declared as nodes AND `unavailable`; RH permanently denied access, 0 cells |
| Teuken-instruct-commercial edge removed | 51 → 51, +1 orphan | its card names `base-v0.4`, a 4T checkpoint of the run whose 6T endpoint we hold |
| phi-4, Pharia-control, Teuken-commercial marked `pretrained: false` | **bases 52 → 49** | roots, but already-aligned models whose pretrained ancestor was never released |
| MPT recovered from mirrors | **49 → 50** | `mosaicml/*` withdrawn; weights corroborated across 7 independent uploaders |

**Three of those changes REDUCED the count and one raised it.** The reductions were found by looking for defects; the addition came from RH noticing a surviving mirror. Neither direction was chosen to reach a number, and the 50 is a coincidence that arrived last — `gpt-sw3` would have been a different 50th and was removed the same day for being unmeasurable.

## What the population is NOT

- **Not 53.** That is the count of graph *roots*; three are aligned models whose base was never released (`microsoft/phi-4`, `Aleph-Alpha/Pharia-1-LLM-7B-control-hf`, `openGPT-X/Teuken-7B-instruct-commercial-v0.4`). A root is not necessarily a base, and the default runs the wrong way: a checkpoint *becomes* a root when an edit removes its edge.
- **Not 50 independent pretraining runs.** Three are continuations or distillations of checkpoints not held here — `Yi-1.5-9B` (continual on Yi), `OLMoE-1B-7B-0125` (annealed from an 0924 branch), `google/gemma-2-9b` (distilled from an unnamed internal teacher). They are independent *observations in this population*; they are not fresh runs. **50 base models, 47 fresh pretraining runs.**
- **Not the unit for "alignment does X".** That unit is the lineage with its recipes averaged (n = 49 measured, 50 with MPT). Bases are the *denominator*; recipes are the *treatment*.

## What would legitimately change it after the freeze

- A base becoming **measurable** that was not (`gpt-sw3`, if Sweden ever approves).
- A **new open-weight base+aligned family** released after the sweep.
- A **corroborated derivation** showing two current bases are one lineage — the phi-4 case, which would *reduce* it.

## What would NOT

- Reclassifying an existing `pretrained: false` model to reach a number. All three are one edit from making 51, and all three would be wrong.
- Adding an uncorroborated mirror. MPT qualifies because seven independent uploaders agree on the weights; a single-mirror model does not.
- Adding a base with no measured aligned descendant. It would inflate the denominator of a claim about alignment while contributing nothing to the numerator.

## The list

Generated, not typed:

    python -m malignment.population

Re-run it against this file. **If they disagree, the file is wrong** — the rule is the authority and the list is its receipt.
