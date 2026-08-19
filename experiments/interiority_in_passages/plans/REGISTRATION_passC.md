# Pre-registration: the confirmatory arm of Pass C

    registered      2026-08-19
    scope           the TEN uncoded lineage pairs, L16-L25
    status          FROZEN. Written before any of those ten was launched.
    verified        results/passC/codings/ holds 18 files. SIXTEEN are the
                    lineage shards analysed here, shard-100 to shard-115, and
                    every analysis globs `shard-1*.json` to select exactly those.
                    The other two, shard-00 and shard-99, are from the earlier
                    SAMPLE draw -- a different population -- and appear in no
                    number in this document. No shard 116 or above exists.

This is a confirmatory test of three claims that were formed on sixteen pairs
already coded. **Those sixteen are exploratory and stay exploratory.** Nothing
below re-analyses them; they supply the predictions and nothing else.

---

# 0. FULL DISCLOSURE OF WHAT CAME BEFORE

A registration written after fifteen exploratory runs is worth only as much as
its account of them.

- The design changed six times. `plans/RUBRICS.md` is the ledger: eleven coding
  runs before production, with fields, n, agreement and defects.
- Fields were cut after seeing data: `charge`, `why`, `presence`. `presence` was
  the DECLARED PRIMARY estimand and was demoted after it arrived at a 94%
  ceiling and proved 92.6% reproducible by a mental-state-verb regex.
- `mode` was declared primary over `degree` on a kappa comparison. **That was
  wrong** and the current claim rests on `degree`. Recorded, not hidden.
- The hypothesis direction was known to the designer throughout.
- The numbers were looked at at 10, 12, 13 and 15 pairs. That is optional
  stopping.
- Two headline claims from the first three pairs were overturned by later pairs:
  a null on degree (+0.03, p=1.000) and a prompt-kind interaction. See
  HANDOFF.md section 6a.
- The run paused at sixteen pairs because a session usage limit was nearly full,
  which is external to the data.

**The ten remaining pairs have never been coded, scored for these fields, or
inspected.** Their model names are known (section 3) because the roster was fixed
in advance. Nothing else about them is.

# 1. THE INSTRUMENT, FROZEN

    rubric        plans/passC_rubric.md
                  sha256[:16] = 2740a81f9535212e   6665 bytes
    coder         Opus, effort 'high', ONE coder per passage, no model: key
    fields        narrative, span, mode, drift, degree
    blinding      coders never see arm, model, or another coder's judgement;
                  every batch mixes arms; metadata fields are prefixed _

Any edit to the rubric file invalidates this registration for pairs coded after
the edit. If the rubric must change, the affected pairs are exploratory.

Reliability, measured on this population by double-coding L01:

    narrative 0.847   mode 0.843   drift 0.819   degree 0.866

**`drift` is the least reliable of the four and H3 depends on it.** See 6.3.

# 2. POPULATION AND UNIT

    corpus      f11_l2, English only
    draw        triage.parquet -- top 200 per cell by classifier score.
                NOT a random sample. The population is "passages a classifier
                ranks as confidently narrative", which is narrower than
                "narrative passages" and is stated in every result.
    unit        THE LINEAGE PAIR. Never the passage. n = 10.
    test        Wilcoxon signed-rank on per-pair differences, two-sided,
                alpha = 0.05. Sign test reported beside it, never instead.

The passage-level pooled statistic is not the estimand and will not be reported
as one. Pooling once gave the opposite sign to the paired test.

# 3. THE TEN PAIRS, NAMED IN ADVANCE

    L16  m-a-p/CT-LLM-Base                          | CT-LLM-SFT-DPO
    L17  meta-llama/Llama-3.1-8B                    | Llama-3.1-8B-Instruct
    L18  mistralai/Mistral-7B-v0.1                  | HuggingFaceH4/zephyr-7b-beta
    L19  openbmb/MiniCPM5-1B-Base                   | MiniCPM5-1B
    L20  tiiuae/Falcon3-10B-Base                    | Falcon3-10B-Instruct
    L21  tiiuae/Falcon3-1B-Base                     | Falcon3-1B-Instruct
    L22  tiiuae/Falcon3-3B-Base                     | Falcon3-3B-Instruct
    L23  tiiuae/Falcon3-7B-Base                     | Falcon3-7B-Instruct
    L24  togethercomputer/RedPajama-INCITE-Base-7B-v0.1 | RedPajama-INCITE-7B-Chat
    L25  zai-org/glm-4-9b-hf                        | glm-4-9b-chat-hf

All ten are run. **No pair is dropped for its result.** The only exclusions are
the two mechanical rules in section 4, both applied before any delta is read.

Note four of ten are one family (Falcon3, 1B/3B/7B/10B). They are not independent
observations of "alignment"; they are one alignment recipe at four scales. This
inflates the effective n and is a declared weakness, reported as a sensitivity
analysis collapsing Falcon3 to a single mean (giving n=7).

# 4. EXCLUSION RULES, MECHANICAL AND PRE-SPECIFIED

Applied before any hypothesis test, in this order, and reported with counts.

**E1. Cell too small.** A pair is excluded if either arm yields fewer than 20
narrative passages of its 200. Rationale: Qwen2.5-0.5B produced 7, and a mean on
7 is not an estimate.

**E2. Arms not length-comparable.** A pair is excluded if the ratio of the two
arms' median completion word counts falls outside [0.5, 2.0]. Rationale: two of
fifteen pairs failed this, they were the two largest effects in the run in
opposite directions, and a three-word completion can neither contain interiority
nor drift. Threshold set now, on the thirteen surviving pairs' observed range,
which is 0.96 to 1.05 -- every one within 5% of parity, and the two excluded at
0.02 and 20.10. The gap between the surviving cluster and the threshold is two
orders of magnitude, so the rule cannot be doing subtle work and was not tuned to
any incoming result.

Both rules use only arm-level properties, never an outcome. If more than three of
the ten are excluded, the confirmatory test is reported as underpowered and the
result is not called confirmed.

# 5. THE THREE HYPOTHESES

Predictions are the observed values on the thirteen surviving exploratory pairs.
MDE is two-sided alpha=.05, 80% power, Wilcoxon, n=10, using the exploratory
across-pair SD.

## H1. Alignment increases interiority in narrative passages, regardless of
##     whether the prompt supplies any.

    estimand    per pair: mean `degree` (0-3) over narrative passages,
                aligned minus base
    predicted   +0.237      (sd across pairs 0.199)
    MDE at n=10  0.184      POWERED
    confirms    Wilcoxon p < 0.05 AND the sign positive AND at least 8 of 10
                pairs positive

The second clause is tested three ways, and **only the first is confirmatory**:

    H1a  main effect, as above                          POWERED     confirmatory
    H1b  EXTERIOR prompts alone   predicted +0.240   MDE 0.244   underpowered
         INTERIOR prompts alone   predicted +0.246   MDE 0.205   borderline
    H1c  interaction, EXTERIOR delta minus INTERIOR delta
         predicted -0.006   MDE 0.304

**H1c cannot establish "regardless of prompt".** Absence of a detected
interaction at n=10 bounds it only at about +/-0.30, which is LARGER than the
main effect itself. The honest statement available is: *the effect appears in
both prompt strata separately, and any interaction is smaller than 0.30.* It will
be written that way and not as "the effect is independent of the prompt". NEITHER
prompts are not testable (only 4 of 13 pairs reach n>=10 per cell).

## H2. Alignment produces more narrative overall.

    estimand    per pair: % of the 200 coded passages with narrative=true,
                aligned minus base
    predicted   +10.3pp     (sd across pairs 18.7)
    MDE at n=10  17.4pp     NOT POWERED
    confirms    NOTHING at n=10. See below.

**H2 is registered as a directional prediction that this study cannot decide,
and it is registered anyway so that the failure is on the record rather than
discovered later.** Two independent problems:

1. **Power.** The predicted effect is 10.3pp and the detectable one is 17.4pp.
   The across-pair spread is enormous (-33.5 to +47.5). A null result is
   uninformative; only a very large effect would register.
2. **The estimand is not the quantity in the claim.** These are the top 200 per
   cell by classifier score, not a random sample. Yield-within-top-200 rises
   monotonically with a cell's underlying narrative rate but is a compressed,
   biased estimate of it, and the classifier's arm gap was measured at +0.4pp in
   the relevant score band. **So "alignment produces more narrative" is not what
   is being measured.**

Pre-specified reporting: direction and per-pair values, with the sentence "this
study is not powered for H2 and the draw is not a random sample, so this is
directional evidence only". **The proper test is a separate measurement** -- a
fresh uniformly random sample per cell, coded on `narrative` alone, which is
cheap because it needs one field. Registered here as the required follow-up so
that it is not quietly replaced by the biased version.

There is also a substantive reason to want it: the passages excluded by the
narrative filter are excluded for alignment-related reasons (Qwen2.5-0.5B's
aligned arm answers fiction prompts as instructions), so the yield is a result
about alignment and not merely a nuisance.

## H3. The narrative alignment produces is more stable, with less drift.

    estimand    per pair: % of narrative passages with drift=HOLDS,
                aligned minus base
    predicted   +5.3pp      (sd across pairs 6.0)
    MDE at n=10  5.6pp      MARGINAL -- predicted effect sits just BELOW the MDE
    confirms    Wilcoxon p < 0.05 AND sign positive AND at least 8 of 10 up
    secondary   SHIFTS predicted -4.8pp; UNMOORED predicted -0.5pp, not powered

Reported alongside: `drift` has the lowest double-coded agreement of the four
fields (0.819), and SHIFTS runs at roughly 5-10% of narrative passages, so a
per-pair rate rests on order 10 passages. **H3 is the weakest of the three both
statistically and instrumentally**, and a failure to confirm should be read as
"this study could not detect it", not as a refutation.

# 6. WHAT WOULD FALSIFY, STATED PLAINLY

- **H1 fails** if the Wilcoxon is non-significant, or if fewer than 8 of 10 pairs
  are positive, or if the sign reverses. Given +0.237 predicted against a 0.184
  MDE, a failure here is a real problem for the claim and will be reported as
  one.
- **A confirmed H1 with a large detected interaction (H1c)** falsifies the
  "regardless of prompt" clause while leaving the main claim standing. These are
  reported separately.
- **H3 fails** if non-significant. Because it is marginal by design, a null is
  weak evidence and will be labelled as such.
- **H2 cannot fail informatively.** That is why it is written down.

# 7. ANALYSES THAT ARE NOT CONFIRMATORY

Everything else is exploratory and will be labelled exploratory in any write-up,
including: told/shown (`mode`) in all forms; degree conditional on interiority
being present; the alignment-stage stratum (Instruct vs DPO vs zephyr); the
convergence pattern in aligned base rates; drift-by-degree; quintuplet role;
per-family effects; and any analysis suggested by the ten pairs after seeing
them.

Two exploratory results from the sixteen are stated here so that a later
"prediction" cannot be constructed from them: SHOWN-given-interior was +0.1pp
(p=0.893) and degree-given-interiority-present was +0.181 (13/13).

# 8. THE DESCRIPTIVE ANALYSIS, ALSO REPORTED (RH, 2026-08-19)

**Every result above is confirmatory and covers ten pairs. A second analysis is
reported alongside it, covering EVERY coded pair, and it is the primary
description of the phenomenon.** RH's ruling: the full roster is the true
population, and a confirmatory subset chosen for registration hygiene is not a
better description of what alignment does than all the evidence there is.

    scope       all coded lineage pairs -- the 16 exploratory plus the 10
                confirmatory, 26 in total when the run completes
    status      DESCRIPTIVE. Not confirmatory, never reported as a test of H1-H3,
                and its p-values carry the whole exploratory history above.
    estimands   the same three, computed identically

## One exclusion applies, and it is E1

**Pairs underpowered by having too few narrative passages are excluded**
(RH, 2026-08-19). That is E1 from section 4 unchanged: either arm under 20
narrative passages of its 200. It removes Qwen2.5-0.5B, whose aligned arm holds
7. A mean over 7 passages is not an estimate and its inclusion would be a
precision claim the data cannot support.

## E2 is reported both ways, because it changes nothing

On the 16 coded pairs:

    everything, no rules at all             n=16  mean +0.201  15/16 up  p=0.00516
    E1 only                                 n=15  mean +0.200  14/15 up  p=0.00836
    E1 + E2 (length ratio in [0.5, 2.0])    n=13  mean +0.237  13/13 up  p=0.00024

The direction, the near-unanimity and the significance survive including the two
length-degenerate pairs. **The primary descriptive figure is E1-only**, per RH's
ruling; the E1+E2 figure is reported beside it as a sensitivity analysis.

The rule is not doing subtle work: surviving pairs have length ratios between
0.96 and 1.05, and the two E2 removes are 0.02 and 20.10. There is no borderline
case, and no pair sits anywhere near the threshold.

## One row needs a gloss, not an exclusion

bloom-7b1 -> bloomz-7b1 contributes -1.357, the only negative. It must NOT be
described as "alignment reduced interiority for this pair". bloomz's median
completion is 3 words against bloom's 187; it emits fragments (`protect her.`)
and all 158 of its aligned narrative passages were coded drift=HOLDS, which a
three-word span cannot do. The description is **"this model stopped producing
text"**, and the interiority reading of its number is unavailable. Length-matched
in the one comparable band the delta is -0.586.

Lucie-7B is the mirror (+1.266, ratio 20.10) and carries the same footnote in the
other direction.

Both rows appear in the descriptive table with that footnote attached.

## What the descriptive analysis is not

It is not a second chance at H1-H3. If a hypothesis fails its confirmatory test
on the ten and succeeds descriptively on the twenty-six, **the confirmatory
result is the one that stands as a test**, and the descriptive figure is reported
as what the full evidence looks like, with the discrepancy stated rather than
resolved in favour of whichever is nicer. Registering that in advance is the
whole point of writing this section before the ten are coded.

# 9. DEVIATIONS

Any departure from this document is recorded in this file, dated, with the reason
and the pre-deviation number where one exists. A deviation is not a defect; an
unrecorded one is.
