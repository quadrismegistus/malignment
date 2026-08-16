---
id: DOL
question: Which alignment stage carries the displacement, and does the answer depend on content domain?
status: NOT RUN — registration frozen, awaiting the measurement queue
opened: 2026-08-16
---

# Division of labour

**The question.** Given a lineage with separately released stages (base → SFT → preference → RLVR), how much of the total displacement is already present at the SFT checkpoint, and does that share differ by the **content domain** of the prompt?

## Why it is being recomputed rather than cited

Two recorded claims rest on a population that no longer exists.

- *"SFT and DPO divide labour by content type. SFT handles sex… DPO handles violence"*
- *"OLMo's SFT does ~90% of the work"*

Since they were written, **four edges we called DPO turned out not to be** — `beaver-7b-v1.0` (Safe RLHF), `internlm2-chat-7b` (Online RLHF), `MiniCPM5-1B` (On-Policy Distillation), `RedPajama-INCITE-7B-Chat` (plain SFT) — and one that was called SFT is DPO (`stablelm-2-1_6b-chat`). The DPO population went **22 → 17 declared edges**. A `GROUP BY relation` over the corrected roster is a different computation, not a refresh.

A first pass on 2026-08-16 already put the second claim at **76–77%** for Olmo-3's Instruct branch, not ~90%, with a median of **78%** across 26 chains. That pass is superseded by this experiment; it is recorded here only so the direction of the correction is not lost.

## The measure, and what it is not

    share = js_mean(base → SFT) / js_mean(base → endpoint)

**This is a ratio of cumulative distances, NOT a decomposition.** JS does not partition across rungs — `js(base→SFT) + js(SFT→DPO) ≠ js(base→DPO)` — so "SFT does 78% of the work" is shorthand for *"the SFT checkpoint sits 78% of the way out"*. Reporting it as a share of an additive total claims something the metric cannot support.

It can also **exceed 100%**, and does: `internlm2` at 116% and `SmolLM3` at 113%, where the endpoint is *closer to base* than the SFT rung was. For SmolLM3 the cause is known — the final 0.9/0.1 merge with a long-context checkpoint pulls it back. That is a real reversal, not an artefact, and any framing that assumes stages accumulate hides it.

## Population

Declared here, generated into `population.json` by `run.py`, per `RESULTS.md`.

- **Models** — lineages with BOTH a released `sft` rung and a released preference rung, so the ratio is computable. That is a **subpopulation, and a selected one**: labs that publish intermediate checkpoints are open-science labs. Measured on 2026-08-16, lineages with a released preference stage carry *lower* base→endpoint JS than those without (0.1361 vs 0.1545, n=19 vs 32), so this population is **biased low relative to the roster**. The result is a claim about that subpopulation and must say so.
- **Prompts** — `Prompts.all()`, i.e. admitted AND live (`status` ACTIVE or absent). 2,783 rows, 2,706 unique texts. The 105 struck rows (93 RETIRED, 10 MIXED, 2 DISPUTED) are excluded; `Prompts.struck()` returns them.
- **Domains** — the `domain` field: violence 552, power 253, taboo 240, neutral 210, sexual 157, property 208, betrayal 204, contradiction 199, and 23 smaller. **The original claim's categories were "sex" and "violence"; `sexual` here is n=157 and `taboo` (240) may or may not be the same construct.** Resolving that mapping is part of the work, not an assumption of it.
- **Instrument** — `rule_version 3`, `dict_sha b16011275c42955c`.

## Status

**Not run.** Waiting on the measurement queue so the population is stable at the point of first run: MPT base/instruct/chat, then `olmo-think` resuming from 569/4,393. `olmo-think` matters directly — it gives Olmo-3 a second recipe, and Olmo-3 is the lineage the "~90%" claim was made on.

## Claim

*Nothing yet. This section is written after `run.py` has run, and states what the numbers support — including if that is "no clear division".*
