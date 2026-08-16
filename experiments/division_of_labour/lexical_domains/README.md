# lexical_domains

**Question.** Is the division of labour content-dependent — does SFT do relatively more of the work on *sexual* words and the preference stage more on *violent* words — measured on the words themselves rather than on prompt-domain labels?

**Status: RUN, 2026-08-16. L1 NOT SUPPORTED AS TESTED — and the operationalisation is now known to be wrong.** See "What this test could not ask". Lexicon `d542e7e2bb86bd00`, 18 chains over 16 lineages, 2,189-prompt panel.

## Result

All figures below are printed by `analyse.py`. Unit is the **lineage** (18 chains are 16 bases). The sign test is the registered one; t and Wilcoxon are unregistered and decide nothing.

| test | n | mean | 95% CI | positive | sign p | t | W |
|---|---|---|---|---|---|---|---|
| **L1 corrected** (both categories, same prompts) | 16 | **+0.0024** | [−0.047, +0.047] | 9/16 | 0.80 | 0.92 | 0.63 |
| L1 original (defective — each category on its own prompts) | 16 | +0.0052 | [−0.058, +0.060] | 10/16 | 0.45 | 0.87 | 0.60 |
| addendum: explicit prompts only | 10 | −0.0625 | [−0.169, +0.046] | 4/10 | 1.00 | 0.31 | 0.32 |

**A null is quotable only as a bound.** The registered sign test has an **MDE of 0.10** at n=16 — it cannot see an effect smaller than that, so its p-value alone says nothing. The interval does the work: the sexual−violent difference is **within ±0.05**, and all three tests agree.

The first run differenced two quantities computed on 195–487 vs 963–1111 prompts. Correcting that made the effect *smaller* and the bound *tighter*. `--variant original` remains runnable, because a correction whose predecessor cannot be re-run is a claim about a number nobody can see.

## L2 — within prompt domain

Nine domains tested, so ~0.5 expected to clear p<.05 by chance.

| prompt domain | mean | positive | 95% CI | p |
|---|---|---|---|---|
| taboo | +0.1872 | 11/16 | [+0.020, +0.408] | 0.21 |
| other | +0.1075 | 10/16 | [−0.066, +0.271] | 0.45 |
| neutral | +0.0611 | 9/15 | [−0.050, +0.163] | 0.61 |
| violence | +0.0288 | 10/16 | [−0.018, +0.077] | 0.45 |
| **sexual** | **−0.0433** | **5/16** | [−0.098, +0.008] | 1.00 |
| betrayal | −0.0987 | 6/10 | [−0.382, +0.168] | 0.75 |

**Restricting to sexual context makes it more negative, not less.** This is the answer to the obvious objection that averaging over neutral prompts dilutes a real effect: concentrating the context should recover the signal and instead reverses it. `taboo` is the one positive-leaning cell and the one worth a designed test.

(`animal` shows +4.3 at 7/16 — a ratio blow-up on tiny denominators, not an effect. Sign counts are the robust reading.)

## L3 — where the mass goes

| category | arm | departed | arrived | net |
|---|---|---|---|---|
| sexual | SFT | 0.005357 | 0.002771 | **−0.002586** |
| sexual | pref | 0.005792 | 0.002823 | **−0.002969** |
| violent | SFT | 0.009159 | 0.005678 | **−0.003480** |
| violent | pref | 0.010340 | 0.006427 | **−0.003913** |

**Both categories lose net mass at both stages; departure runs ~2× arrival.** Mass leaves this vocabulary rather than migrating into it. At category granularity that is suppression, not displacement — the direction `register_shift`'s R1a-without-R1b would take, which that registration names as the outcome it would rather not see.

## Descriptive probes

Registration constrains inference; it does not produce understanding. These are descriptive and none is a test.

**Per lineage** the spread is wide — −0.24 (internlm2) to +0.18 (Olmo-3-1025-7B), sd ≈ 0.10. Lineages disagree in direction, which is why a sign test was hopeless and why the mean sits near zero without being uniform.

**Family split (POST HOC — a subgroup found by looking):**

| group | n | mean | 95% CI | positive | sign p |
|---|---|---|---|---|---|
| OLMo | 5 | +0.0535 | [+0.004, +0.103] | 4/5 | 0.375 |
| everything else | 11 | −0.0208 | [−0.082, +0.035] | 5/11 | 1.00 |

The v1 claim was made **on OLMo 3**, so this is the subgroup that was always going to be inspected — which makes it a hypothesis for *other* OLMo checkpoints (Think, the step ladders, 32B), not a result on these. It is 5 lineages, chosen after seeing the ranking, with a sign p of 0.375.

**Word probe.** 275 words poolable (≥8 lineages), scored against their own chain's lexicon-wide baseline. **36 clear p<0.05 against 13.8 expected by chance** — 2.6× enrichment, so something is there, but individual words are candidates only. Violent words dominate the list; the sexual ones clearing are `sodomized`, `masturbated`, `fucked`, `tits`, `nipples`, `cleavage`, `orgasmed`, `sexual`. **The `mean_excess_share` magnitudes are unusable** (`slaughtered` +611, `tits` +168) — small denominators inflate the ratio, so rank by `sign_p` and ignore the size.

## Method and files

`run.py` **measures** and writes the finest grain; `analyse.py` **tests** and may not query ClickHouse. If an analysis needs a column, the measurement must be re-run and that shows as a diff.

    results/cells.csv       67,601   base, aligned, prompt_key, domain, explicit, category, js, departed, arrived
    results/word_cells.csv  14,601   base, aligned, word, category, register, js, n_prompts
    results/prompts.csv      2,706   prompt_key -> prompt_id, domain, subdomain, language, text
    results/chains.csv          18   + family and vendor, so nobody string-matches a model id
    results/by_*.csv, summary.json   everything analyse.py prints

Conservation against `movement_cells.js_total − js_tail`, booked by a different producer: **worst |diff| ~1e-17**.

---

## What this test could not ask

Three faults surfaced in an adversarial pass **after** the run, all in *what was measured* rather than in whether it was honestly pre-declared. Registration binds a design; it cannot tell you the design answers the question.

**1. `share` is not a share.** JS is **not additive along a path**, so `js_C(base→sft) / js_C(base→endpoint)` is a ratio of two path lengths sharing an endpoint, not a decomposition of work. It exceeds 1 whenever the endpoint sits closer to base than the SFT rung — observed (internlm2, 1.237). A quantity that can exceed 1 was being read as a proportion.

**2. Violence is the wrong baseline for sex.** Normalising one content type by the other means the test only fires if they *differ* — it is structurally blind to "SFT handles both" — and it imports violence's noise into sexual's estimate. The neutral baseline is the chain's own displacement across all vocabulary.

**3. The denominator never touches the preference step.** `sft→pref` does not appear in the statistic. "SFT or DPO?" was asked without measuring one of them.

**A finding the difference test structurally could not report:** `share_violent` runs 0.44–1.24, mostly 0.7–1.0, with almost no chain below 0.5. **Violence is SFT-dominated too, nearly everywhere.** If that survives a proper baseline, *"DPO handles violence"* is false on its own terms — cleaner than any null. Two SFT-dominated categories cancel in a difference.

**Status of the withdrawal.** The stopping rule fired on a pre-committed test and is not being quietly reversed. The claim is recorded as **not supported as tested**. The correct test is a new question, to be registered with the contrast and baseline agreed *before* freezing.
