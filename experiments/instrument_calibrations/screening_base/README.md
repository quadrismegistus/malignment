# screening_base

**Question.** Which released checkpoint is representative of the roster's transgressive-vocabulary behaviour, and should therefore screen slot frames?

**Status: REGISTERED, NOT RUN — 2026-08-16.** `registration.md` is frozen; `run.py` does not exist yet. This file will carry the result when it does.

**id.** `screening_base`

## Why this exists

`SlotExplorer` screens candidate frames by showing what one model wants to say at the blank. That model is a choice, and it is a consequential one in both directions: a **quiet** screener rejects frames that are alive in the models actually measured, and a **loud** one admits frames that are dead in them. The second is the original M01 failure — *"the prompt and slots were just badly chosen … accidentally lame"* — arriving by a different route.

The screening base is **not** the diagnostic pair and takes a different answer. Screening reads one distribution and no contrast, so contamination is not its hazard: selection on `P_base` is a pre-treatment covariate and cannot bias a base→aligned contrast measured after it. Representativeness is its hazard. The diagnostic pair (`slots.DIAGNOSTIC_PAIR`, Falcon3-3B) has the opposite requirement and is declared separately.

## What is registered

A **selection rule**, a population and a set of refusals. No hypothesis — this question makes no claim about what alignment does, which is why it lives in `instrument_calibrations/` and must not appear in the hypothesis register.

The rule, in one line: among models with ≥2,000 of the 2,189 panel prompts, the screener is the one minimising `max(|percentile − 50|)` across **mean**, **breadth** and **intensity** of labelled mass. No tunable parameter.

## Read the registration first, for one reason

**An exploratory pass was run before the registration existed**, answering RH's question about defaulting to Llama. `registration.md` opens with that selection event, what it licenses and what it does not. In short: this can freeze a rule and give the choice a receipt; it cannot claim Falcon3-10B-Base won a pre-registered contest, because the specification was written knowing the exploratory ranking.

## Inputs

| | |
|---|---|
| prompts | `{db}.wf_panel`, 2,189 crossed panel prompts |
| models | ≥2,000 of those prompts measured — 156 of 403 on the snapshot date |
| instrument | `{db}.wf_sexviolence`, sha `d542e7e2bb86bd00`, 1,063 words |

**The instrument is English-only and blind on CJK**, and its own registration requires the unlabelled share to be reported downstream. `run.py` must use `\p{Han}` for that check: the exploratory pass used `[\x{4e00}-\x{9fff}]`, which ClickHouse matched against 2,188 of 2,189 prompts where the true count is **1**.
