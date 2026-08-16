# removal_rates

**Question.** Which alignment stage *removes* sexual vocabulary, and which removes violent vocabulary — each measured against blind-rated neutral words, and never against each other?

**Status: RUN, 2026-08-16.** Lexicon `d542e7e2bb86bd00`, 18 chains over 16 lineages, 2,189-prompt panel. Registered — with RH, not solo — before any rate was computed.

## Result

**A is SUPPORTED. B is NOT.** They are reported separately and are not summarised into one verdict; that separation is what made this outcome visible at all.

| | n | mean | 95% CI | positive | t | sign p |
|---|---|---|---|---|---|---|
| **A** sexual is an SFT speciality | 16 | **+0.0894** | **[+0.023, +0.161]** | 11/16 | 0.026 | 0.21 |
| **B** violent is a preference-stage speciality | 16 | −0.0014 | [−0.056, +0.051] | 9/16 | 0.96 | 0.80 |

Raw removal rates — the fraction of each set's *inherited* mass that fell, median over lineages:

| word set | SFT | PREF |
|---|---|---|
| **sexual** | **0.3767** | 0.0910 |
| violent | 0.3610 | 0.1042 |
| neutral (all 3,812) | 0.2970 | 0.0937 |
| neutral matched to sexual | 0.2679 | 0.0797 |
| neutral matched to violent | 0.3311 | 0.0960 |

**SFT strips 37.7% of the sexual mass it inherits against 26.8% for frequency-matched neutral vocabulary** — an 11-point gap that closes at the preference stage. That is the original claim's first half, and it survives.

**It is not SFT-thoroughness.** The registration named that as the outcome it would rather not see: A passing because SFT over-removes *everything*. Neutral sits at 29.7% and sexual at 37.7%, so the excess is specific, not a by-product of H1's finding that SFT does ~82% of all displacement.

**The sign test does not clear, and the CI is doing the work — as registered.** A's effect is +0.089 against a sign-test **MDE of 0.10**, so at n=16 that test structurally cannot see it. The registration named the bootstrap CI as primary and printed the MDE before any p-value was read, precisely so this could not be argued afterwards.

**Sensitivity check (registered): per-prompt averaging.** A holds at **+0.0759, CI [+0.016, +0.139]**; B stays null. So the result does not rest on the ~40 prompts carrying 82% of sexual mass.

## B, stated as a bound

*"DPO handles violence"* is **bounded to ±0.05.** Violence is removed at 36.1% by SFT and 10.4% by the preference stage — it is SFT-dominated too, and the preference stage shows no violence speciality once compared to frequency-matched neutral words.

The unmatched reference is informative here: against *unmatched* neutral, B comes out at **−0.0434, CI [−0.082, −0.006]** — significant in the **wrong** direction. Frequency matching removes that. Violent words are frequency-comparable to the reference (median 50 vs 52) and sexual words are not (30), which is why matching was declared for both arms rather than assumed unnecessary.

## Per lineage

11 of 16 positive on A. The top of the ranking is OLMo-heavy — `Olmo-Hybrid` +0.387, `Olmo-3-1125-32B` +0.278, `Olmo-3-1025-7B` +0.260 — **and this cannot be read as confirmation**: 3 lineages were seen while designing the statistic (registration §2), and OLMo was already known to be the strong subgroup from `lexical_domains`.

**`Amber` is the interesting exception**: its *preference* stage does the sexual work (+0.238 vs +0.127 at SFT), the only lineage where that holds clearly. That matches v1's recorded observation that Amber splits labour 50/50 between SFT and DPO rather than being ego-dominant.

`pythia-2.8b`, `pythia-6.9b`, `internlm2-base-7b` and `SmolLM3-3B-Base` are negative on A.

## What this does and does not settle

**It does not reinstate the withdrawn claim.** *"SFT handles sex, DPO handles violence"* was withdrawn as a conjunction and stays withdrawn: its second half is bounded near zero. What is supported is the **first half alone**, under an operationalisation the earlier tests did not use.

**Why this is not a third bite at the same apple.** H3 and L1 measured JS — a *symmetric* divergence, so a sexual word that *rose* counted exactly as much as one that *fell* — normalised by `base→endpoint`, a path length that never touches the preference step. This measures **falls**, against **inherited** mass, at **both real edges**. RH: *"misoperationalisation shows us nothing relating to hypothesis so not a null."*

**Registration §5's stopping rule did not fire**, because it required *both* A and B to fail.

## Method and files

    run.py       measures. Writes results/cells.csv (273,918 rows) + sets.csv + chains.csv
    analyse.py   tests. Reads those; never queries ClickHouse. --per-prompt for the check

    rate_C(stage)   = mass FALLEN from C / C mass the stage INHERITED
    excess_C(stage) = rate_C(stage) − rate_matched_neutral(stage)
    A: excess_sexual(SFT) > excess_sexual(PREF)      B: excess_violent(PREF) > excess_violent(SFT)

`sexual = lexicon sexual ∪ both` and `violent = lexicon violent ∪ both`, so `rape` is in both sets. That is only sound because A and B are never compared — RH's design decision, and the reason it is safe.
