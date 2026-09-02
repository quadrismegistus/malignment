---
id: DOL.sft_share
question: Which alignment stage carries the displacement, and does the answer depend on content domain?
status: RUN 2026-08-16 — H1 supported, H2 split, H3 NOT supported
opened: 2026-08-16
kind: question
headline: SFT carries most of the displacement, and the content-dependent division of labour does not survive its own test.
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

**Run 2026-08-16.** 18 chains on 16 distinct bases; every arm measured, none waiting. See amendment A1 — the stopping rule's premise was false, because none of the pending checkpoints arrives by a preference op and so none forms or joins a chain.

## Claim

**SFT carries most of the displacement, and the content-dependent division of labour does not survive its own test.**

**H1 — SUPPORTED.** Median share **0.819**, 16/18 chains above 0.50, sign p = 0.0013. At the SFT checkpoint a model is already ~82% of the way to where its preference-tuned endpoint sits.

**H2 — SPLIT, and the split is the finding.** The recorded "~90%" is not wrong, it is **branch-specific**:

| chain | share |
|---|---|
| Olmo-3-7B-**Instruct**-DPO | **0.773** |
| Olmo-3-7B-**Think**-DPO | **0.950** |

Same base, same lab, two products, 18 points apart. Any single number for "OLMo's SFT share" is picking a branch without saying so.

**H3 — NOT SUPPORTED.** *"SFT handles sex, DPO handles violence"* does not survive:

    chain level  n=18  mean +0.0110  14/18 positive  p=0.0309
    base  level  n=16  mean +0.0086  12/16 positive  p=0.0768   <- the registered test

Amendment A2 fixed, before computing it, that the base-level check decides. It gives **+0.0086, 12/16 positive, p = 0.0768**, so **H3 is reported NOT SUPPORTED** rather than supported-with-caveat. (A4: `run.py` did not compute this until 2026-08-16 — the number was right but was produced by hand. It is now emitted by the producer, labelled as deciding.)

Two things worth keeping from the null. The **direction is consistent** — positive at both levels, 12 of 16 bases — so this is a failure to demonstrate, not a demonstration of absence. And the **magnitude was never large enough to carry the original wording**: +0.011 on a share, inside a system where SFT does ~82% of everything. A dichotomy ("SFT handles X, DPO handles Y") and a 1-point tilt are different claims, and only the second was ever in the data.

**Bases pull both ways**, which is what a null of this shape looks like: Amber +0.0707, Mistral +0.0492 against pythia-6.9b −0.0306, llama-7b −0.0210, OLMo-2 −0.0199.

**One reversal, kept as registered:** `internlm2-chat-7b` at share 1.16 — its preference stage moved the model *back* toward base. Its card says "Online RLHF", the one non-DPO method in the set.

## What this does not license

- Any claim about the roster as a whole. 18 chains require a **separately released preference checkpoint**, which is an open-science habit: lineages that have one carry lower base→endpoint JS than those that do not (0.1361 vs 0.1545). **Biased low, by construction.**
- Re-running H3 with `taboo` merged into `sexual`. The mapping was fixed in the registration precisely so that a null could not be converted by widening a category afterwards. If someone wants that test it is a NEW experiment with its own registration, and it must say that it was run after seeing this one.
