---
subject: displacement
kind: question
status: "RUN 2026-09-11. Three instruments: existence/norm_change per-lineage lookups (DELTA, and withdrawn as evidence about architecture), a 50-base pairwise similarity sweep on field, type-norm and contextual-norm measures (BASE, 1,225 pairs, 200 v6-rated prompts), and the Olmo-3 / Olmo-Hybrid ladders across stages where AI2's post-training data is attested identical. NOT REGISTERED; no between-group test is run, and n on the attention-free side is one pure SSM and one linear-attention model."
question: Does the displacement operation, or anything else these models do, depend on the attention mechanism?
headline: "ALIGNMENT MOVES MODELS APART: any two of the 50 bases sit 0.407 apart in contextual-norm space, any two of the 50 aligned endpoints 0.669, and all four measures agree (1,225 pairs each). Architecture is NOT detectable at base -- falcon-mamba-7b, which computes no attention of any kind, is the MEDIAN model of the census at rank 25/50 -- which is this folder's answer to Weatherby and a negative. The claim that architecture becomes decisive under alignment is WITHDRAWN 2026-09-11: the Olmo-3/Olmo-Hybrid gap grows 0.28 to 0.62, but that pair starts in the bottom 1% of base-base distances and ends at the 35th percentile of aligned-aligned ones, so it converged toward the crowd while the whole roster spread out."
---

# architecture

**Does the operation need attention?**

Weatherby's *Language Machines* (2025) locates the poetic function in the transformer's attention mechanism: "the transformer architecture gives us quantitative aboutness" (161-62), and computation and language "share form" as "a demonstrable technical fact". The claim is architecture-specific by construction. He hedges it once, and the hedge is the testable part: attention is "probably just one way, we do not yet know of any others, to make this function computationally manipulable" (155), with a note pointing at Google's Griffin, "RNNs with local attention" (227n26).

That Griffin model is in this census. So is a model with no attention at all.


## THE RESULT

> **Alignment moves models apart. Any two base models sit 0.407 apart; any two aligned models sit 0.669 apart.**

1,225 pairs in each population, 200 v6-rated prompts, words above the twp theta of 0.001, distance between mass-weighted centroids in z-scored contextual-norm space. **All four measures agree**, including the two that are not norm-based:

    measure              50 BASE      50 ALIGNED
    contextual norms       0.407           0.669     further apart
    type norms             0.304           0.481     further apart
    Jaccard                0.566           0.411     less overlap
    weighted Jaccard       0.513           0.337     less overlap

Base models are alike. Aligned models are not. Whatever else alignment does, at the level of which words a model will put in a slot it is a DIFFERENTIATING operation, not a homogenising one -- which sits oddly beside this campaign's own finding that aligned models converge in fluency onto 1.135 bits/byte. Converging in how they say it, diverging in what they select.

    ARTIFACT CHECK, PARTIAL. Aligned cells are thinner: 89 words above
    theta against the base's 108, so aligned centroids rest on ~18%
    fewer words and are somewhat noisier. That contributes to the gap
    and is unlikely to account for a 64% rise. Not fully discharged.

## AND THE ANSWER TO WEATHERBY, WHICH IS A NEGATIVE

Across the 50 bases, `falcon-mamba-7b` -- which computes no attention of any kind -- is the **median model of the census**, rank 25 of 50. `rwkv-4-7b-pile` is more central than the average transformer. The most central model on both norm measures is a Mamba hybrid. Whatever separates these fifty base models from one another, **it is not whether they compute attention.**

## WHAT WAS WITHDRAWN, AND WHY IT MATTERS THAT IT WAS

An earlier version of this file led with "the architecture shows up at the cut, not in the language", on the Olmo-3 / Olmo-Hybrid gap growing from 0.28 at base to 0.62 at SFT under attested-identical post-training data. **That is withdrawn.** Calibrated against the two populations above:

    the pair at base   0.28   bottom 1% of the 1,225 base-base distances
    the pair at SFT    0.62   35th percentile of aligned-aligned

The pair begins as one of the most similar in the entire census and ends **still more similar than typical**. It did not diverge from the crowd; the crowd spread out around it and the pair regressed toward the middle, which is what any extreme starting value does under a noisy population-wide transformation. The widening was real and it was not about architecture.

The general form of the sentence had already failed a smaller check: of three base-to-SFT steps measured on this scale -- Llama-3.1-8B to Tulu-3-SFT at 0.223, Olmo-Hybrid at 0.323, Olmo-3 at 0.513 -- **only one exceeds the base-to-base median of 0.407**, so a claim that an alignment step outruns the whole spread of architectures generalised from the largest of three.

**Both failures had the same shape**: a quantity read without the population it belongs to. The surviving claims in this file are the ones stated against 1,225 pairs.

## TWO TURFS, AND EVERY RESULT BELOW BELONGS TO ONE OF THEM


**This folder originally ran one question and reported it as two.** The correction, RH 2026-09-11, and it is the frame for everything here.

    HIS TURF     a claim about the ARCHITECTURE: does the mechanism realize
                 the poetic function? A property of a model, testable on a
                 BASE model, with no reference to post-training at all.

    OURS         a claim about the OPERATION: alignment displaces along a
                 chain of permitted substitutes, and the wave misses it
                 because it reads theory off the aligned surface. A
                 base->aligned DELTA, and the delta is the point.

`existence` and `norm_change` are delta instruments. `existence` regresses (p_aligned - p_base) on scene; `norm_change` regresses (aligned - base) on the base dose. **Neither speaks to a claim about an architecture**, and the sentence this README carried until today -- that the transformer "demonstrates nothing about language that autoregression had not already" -- did not follow from either and is withdrawn.

**The delta is close to the worst place to look for an architecture effect,** which makes the null it produced much weaker than it first reads. Alignment is the most architecture-independent stage in the pipeline: broadly shared SFT mixtures, broadly shared DPO recipes, often the same public corpora. Convergent deltas across architectures are substantially evidence that post-training converged. This folder's own `norm_change` section says so without having been asked: agreement with the roster median tracks how much a model was ALIGNED, and the two dissenters are the two weakest movers. A quantity dominated by post-training cannot be informative about construction.

So the folder now runs both arms, and labels which turf each result stands on. **What survives on our turf** is the original finding, unchanged and now correctly scoped: alignment's operation does not depend on the architecture it runs on. **What is needed on his** is a base-level capacity read, and the honest position is that this folder held none until today.

## HIS TURF, ANSWERED: the attention-free models are not distinctive


All 50 endpoint BASES, pairwise, 1,225 pairs, 200 v6-rated prompts, words above the twp theta of 0.001. If attention realized something distinctive about language, models lacking it should sit APART from the transformer cloud. Each model's median distance to the other 49, and its rank among 50 (rank 1 = most central):

    model                    attn           block     ctxD  rank     typeD  rank
    Falcon-H1-7B-Base        full+ssm       hybrid   0.363   3/50    0.274   4/50
    rwkv-4-7b-pile           linear         dense    0.376  12/50    0.286  16/50
    Olmo-Hybrid-7B           full+linear    hybrid   0.378  14/50    0.287  17/50
    falcon-mamba-7b          none           ssm      0.397  25/50    0.294  23/50
    Falcon-H1-1.5B-Base      full+ssm       hybrid   0.406  30/50    0.295  26/50
    Zamba2-7B                full+ssm       hybrid   0.407  32/50    0.294  22/50
    recurrentgemma-9b        local+linear   hybrid   0.407  33/50    0.326  41/50
    OLMoE-1B-7B-0125         full           moe      0.418  36/50    0.309  32/50
    -- roster median --                              0.398           0.295

**`falcon-mamba-7b`, which computes no attention of any kind, is the median model of the census**: rank 25 of 50 on contextual norms, 23 of 50 on type norms, 29 of 50 on vocabulary overlap. `rwkv-4-7b-pile` is MORE central than the average transformer. The most central model on both norm measures is `Falcon-H1-7B-Base`, a Mamba hybrid, which is more typical of this roster than most of the dense transformers in it.

The ranks also disagree across measures -- `Falcon-H1-7B-Base` is 3rd on contextual norms and 46th on Jaccard -- which is what no signal looks like rather than a weak one.

**This is the folder's answer to Weatherby and it is a negative.** The instrument is the same one that cleanly separates an SFT step from a DPO step and reads +0.930 when two runs really do the same thing. Pointed at base models, it finds that removing attention entirely moves a model to the middle of the distribution. Whatever distinguishes these 50 base models from each other, it is not whether they compute attention.

**The scale that makes this readable.** Base models are all much closer to each other than `Olmo-3` is to its own SFT checkpoint: the median distance between any two of the 50 bases is 0.407, while `olmo3 base->SFT` is 0.513. One alignment step moves a model further than the entire spread of architectures, vendors, scales and corpora at base. (`hybrid base->SFT` at 0.323 does not clear that bar, so this is not uniform, but the comparison holds for the larger of the two.)

**What it does NOT show.** This is not the poetic function. It is the general claim -- does architecture make a detectable difference to how a base model distributes mass over a slot -- and the answer is no, at this grain, on these measures. A model could still lack rhyme pull while sitting at the centre of a norm-profile cloud, which is exactly what `rhyme_pull`'s base arm would test and why that fleet is still the direct test. What this removes is the ground under "computation and language share form as a demonstrable technical fact": the demonstrable difference is not where the architecture is.

**AND IT SITS AGAINST THE CROSS-STAGE RESULT, WHICH IS THE INTERESTING PART.** Architecture is undetectable at base and decisive under alignment: the same SFT data moves two architectures nearly orthogonally (+0.233) where the ceiling is +0.930. **The architecture shows up at the cut, not in the language.** That puts the live fact on the operation's side of the contest rather than on the mechanism's, which is this project's thesis arriving from a direction it did not plan.

## WITHDRAWN: the same post-training data moves the two architectures apart

**THE SECTION BELOW IS SUPERSEDED. Read it as the record of a claim, not as a claim.** Its measurements stand; its interpretation does not. The gap it reports is real and robust to the framed edge, but calibrated against 1,225 aligned-aligned distances the pair turns out to sit at the 35th percentile after starting in the bottom 1%, so the widening is the roster's and not the architecture's. See the withdrawal at the top of this file. What survives from this section is the instrument work: the ceiling control at +0.930, the attested-identical Dolci mixtures, and the framed-edge correction.


RH, 2026-09-11: does the architectural minimal pair sit closer than the ALIGNMENT minimal pair, and what happens to the architecture pair ACROSS STAGES, where the post-training data is the same?

AI2 shipped both ladders, so this is askable: `Olmo-3-1025-7B -> Instruct-SFT -> Instruct-DPO -> Instruct` beside `Olmo-Hybrid-7B -> Instruct-SFT-7B -> Instruct-DPO-7B`. **The post-training data is attested the same, not assumed**: both SFT cards declare `allenai/Dolci-Instruct-SFT`, and the `Dolci-Instruct-DPO` card states it "was used to preference tune Olmo 3 Instruct 7B".

200 v6-rated prompts, words above the twp extraction theta of 0.001, `movement.words_multi` at rule_version 4. `ctxD` is the distance between mass-weighted centroids in z-scored contextual-norm space over all 12 v6 rating scales.

    ARCHITECTURE GAP, olmo3 vs hybrid, BY STAGE
    stage      Jacc    ctxD    ctxD on SHARED SUPPORT    median |A and B|
    base       0.63   0.282                     0.265                  81
    SFT        0.46   0.579                     0.490                  55
    DPO        0.41   0.664                     0.557                  46

    ALIGNMENT MOVES, within one architecture
    olmo3   base->SFT  0.513     hybrid  base->SFT  0.323
            SFT->DPO   0.183             SFT->DPO   0.090
            DPO->RLVR  0.067

**The architecture gap roughly doubles under the same SFT data**, and the shared-support column says that is not an artifact of the two vocabularies drifting apart: restricted to words both models hold above theta, it still goes 0.265 -> 0.490.

**Two architectures given the same post-training data do not converge; they diverge.** `olmo3` travels 0.513 from base to SFT and `hybrid` travels 0.323 -- the dense model moves 1.6x further on identical data -- and they move apart rather than along.

**This is the folder's strongest architecture evidence, and it is strong for the reason the delta was weak.** The objection to `existence` and `norm_change` is that alignment is the most architecture-independent stage, so convergent deltas across the roster mostly record convergent post-training. Here the recipe is not merely similar but the same mixture from one lab, held constant by attestation, and the outcome still depends on what it was applied to.

**The answer to RH's question is that it changes with stage.** At base the architecture pair is CLOSER than one alignment step (0.282 against 0.323 and 0.513). After SFT the architecture gap (0.579) EXCEEDS either model's own journey from base. Alignment is the larger force at the start and the architectures end up further from each other than from where they began.

**The stage near-points reproduce the cut on a new instrument.** `base->SFT` is 0.323 and 0.513; `SFT->DPO` is 0.090 and 0.183; `DPO->RLVR` is 0.067. The first step is three to seven times any later one, which is Findings U's "SFT does the cutting" arrived at from contextual norms rather than from movement rules.

**Limits.** One architecture contrast, so n=1 and nothing here is a rate over architectures. 200 prompts. Aligned models are read on the RAW edge with no chat template, and this roster has aligned models that emit the assistant frame unbidden, which would inflate a base-to-aligned distance. And the DPO row carries a documented card defect: `attestations.json` flags Olmo-3's DPO card as declaring `Dolci-Think-DPO-7B`, templated from its Think sibling, against a `base_model` of Instruct-SFT -- 150k pairs against 260k. **The SFT row is the one where the data is cleanly the same, and it already carries the result.**

### Is the widening just compounding? RH's objection, tested

RH: "bases are not identical, so even the same alignment data/method is shifting probabilities similarly but ending further from where they started." That null is specific enough to test. Compounding requires the two models to move the SAME WAY at different magnitudes, and it predicts the widening happens ALONG the difference that already existed.

    cos(move_olmo3, move_hybrid), base->SFT      +0.233   IQR [-0.480, +0.734]
       prompts with cos > 0.9                       12%
       prompts with cos < 0.5                       58%
    cos(base gap, difference of the two moves)   -0.112
    |difference of moves| 0.551 vs base gap 0.281, larger on 80% of prompts

The moves are not parallel, the widening is not along the pre-existing gap, and the two models' responses to identical data differ by more than they differed to begin with.

**The low cosine is not the instrument's noise floor.** The obvious objection is that per-prompt centroids over 50 to 80 words are too noisy to register any true alignment. But the SMALLER step agrees MORE: `SFT->DPO` moves only 0.195 and 0.092 yet scores +0.511, against `base->SFT`'s 0.524 and 0.338 at +0.233. If noise dominated, the smaller-signal step would score lower.

**And the ceiling is measured, not assumed.** One base (`meta-llama/Llama-3.1-8B`), one architecture, five Tulu-3 SFT arms each missing a different data source (`no-math`, `no-persona`, `no-safety`, `no-wildchat`, and the full mixture), 1,910 pair-prompt comparisons:

    same base, DIFFERENT data      median cos  +0.930   cos>0.9 on 57%, <0.5 on 15%
    same data, DIFFERENT arch      median cos  +0.233   cos>0.9 on 12%, <0.5 on 58%

The percentages are almost exactly swapped. **Dropping an entire data source barely rotates the move; changing what the data is applied to nearly orthogonalizes it.** The direction of an alignment move is set more by what you apply it to than by what you apply.

### CORRECTION, same day: the framed edge, and what it took back

RH pointed out that v4 carries framed cells for these checkpoints, so confound (3) below was closeable rather than merely nameable. Both aligned arms read on the `prefill` edge, 200 prompts drawn from the 763 that are both v6-rated and framed:

    ARCHITECTURE GAP        raw ctxD   framed ctxD
    at SFT                     0.621         0.622
    at DPO                     0.660         0.731

    cos(move_olmo3, move_hybrid), base_raw -> SFT
    raw                       +0.229
    framed                    +0.595

**The GAP survives exactly** -- 0.621 against 0.622 -- and is larger framed at DPO. Read in the frame they were trained for, the two architectures are as far apart as off it. That measure is the cleaner one in any case, since both sides sit on the same edge.

**The MOVE-DIRECTION claim does not survive and is struck.** "Nearly orthogonal" was substantially an artifact of reading aligned models off-template. What replaces it is a bracket, because neither end is clean: the raw number reads both aligned models off the template they were trained for, and the framed number is `base_raw -> SFT_framed`, so both move vectors carry the frame's own contribution -- a large component SHARED by both models, which mechanically inflates the cosine. The true value lies between +0.229 and +0.595, and both ends sit below the +0.930 ceiling, so the moves are not parallel; but the strong version is withdrawn.

The headline sentence is untouched by this: it compares base-to-base distances against a base-to-SFT distance, all on the raw edge, and no framed quantity enters it.

**WHERE THE OBJECTION SURVIVES, and it is not dismissed.** The five Llama arms share the same BASE WEIGHTS, not merely the same architecture. So the ceiling control holds the starting point exactly rather than approximately, and what is established is "same starting point, parallel moves" against "different starting point, divergent moves". Architecture is why these two start apart, so on this pair the architectural claim and the starting-point claim have the same evidence and cannot be separated.

**The control that would separate them is not in the roster**: same architecture, genuinely different pretraining run, same post-training data, same scale. The nearest available is `Llama-3.1-8B` and `OLMo-2-0425-1B` both under Tulu-3 -- two dense transformers, different pretraining, one recipe -- confounded by 8B against 1B, and it needs the OLMo-2 arm's mixture checked in `attestations.json` rather than inferred from the lab. **Until that is filled in, the defensible sentence is the weaker one: models that start apart respond to identical alignment data in different directions.** Not "architecture mediates alignment."

## HIS TURF: what a direct test needs, and one route that is now closed


**An embedding-based read of paradigmatic coherence was proposed on 2026-09-11 and killed the same hour, by RH's objection and then by measurement.** The proposal: embed the high-mass candidates at a base model's slot and ask whether they form a tight equivalence class, which would be selection projected onto combination, directly, on CPU, with no fleet. RH's objection: "kill and scream are not necessarily proximate."

They are not. Measured on the two encoders this repo has already gated (`named_under_dose/embed.py`, whose gate exists because docket [459] once gate-checked bge-m3 on `prompt + " " + word` and the repo's rule is that a gate passed for one use is not evidence about another):

    pair              GloVe    bge-m3
    kill/scream       0.221     0.580
    kill/laugh        0.242     0.568      <- NOT closer than the displacement pair
    kill/help         0.411     0.626      <- CLOSER than the displacement pair
    kill/murder       0.459     0.809
    scream/shout      0.620     0.775

**The canonical displacement pair is not a proximity relation either encoder can see.** In GloVe "scream" is farther from "kill" than "laugh" is.

RH's second question, whether to embed `prompt + word` instead, was tested and makes it worse. The shared prefix dominates: pairwise cosine over eight candidates compresses from [0.535, 0.809] bare to [0.822, 0.987] in context, and the ordering does not improve -- kill/scream 0.894 ties kill/leave 0.894 and kill/help 0.890. Adding the prompt to every candidate makes every candidate similar.

This is consistent with what `existence` already found by a different route: **where the mass goes is not adjacency.** The destination barely depends on the origin. So a semantic-proximity instrument was never going to see this operation, and a null from one would have been a fact about the encoder.

### The lexicon route DOES work, and it is RH's, not the encoder's

RH's counter-proposal, same day: build similarity from **field inclusion + type norm similarity + (possibly) contextual norm similarity**, using `malignment/fields.py`, which already holds USAS, RID, General Inquirer, WordNet supersenses, the `k_` ratings and the psycholinguistic norms. Probed immediately. Distance from `kill` in z-scored norm space over **arousal, valence, dominance, concreteness only -- no charge dimension, so nothing downstream of the transgressive hypothesis is in the metric**:

    word        dist   USAS field                      field vs kill
    attack      0.42   Calm/Violent/Angry [-]          different
    murder      0.72   Life and living things [-]      SHARED
    scream      1.09   Speech acts                     different
    hurt        1.85   Health and disease [-]          different
    shout       2.20   Sensory:- Sound [++]            different
    laugh       3.71   Happy/sad: Happy [+]            different
    help        4.50   Helping/hindering [+]           different

**`scream` ranks third of twelve. `laugh` ranks ninth.** GloVe put `laugh` AHEAD of `scream` and `help` ahead of both. The norms rank the displacement pair correctly, on four ordinary psycholinguistic dimensions, with no encoder in the path.

**The two terms must be reported separately and never summed.** Field inclusion does not track the relation at all: of the near neighbours only `murder` shares `kill`'s USAS field, and `scream` sits in "Speech acts". That is not the composite failing, it is the composite RESOLVING -- what displacement preserves is the norm profile (`kill` arousal 6.81, `scream` 6.74) and what it changes is the field. Summing the two into one similarity score would cancel exactly the structure the instrument exists to show, and it is the same structure `existence` reached independently: the mass LEAVES the faller's own field.

**Two conditions before this is an instrument rather than a probe.** It is twelve hand-picked words and needs the gate `named_under_dose/embed.py` applies to encoders -- near-synonyms closer than unrelated pairs, on held-out pairs chosen first. And **coverage must be a gate, not a default**: `stab` has no norms on any of the four dimensions, and the first version of this probe ranked it as `kill`'s NEAREST neighbour at distance 0.00, because `nansum` over an all-NaN row returns zero. `fields.py`'s own docstring names that hazard and `named_under_dose` refuses it by dropping uncovered words. Complete cases only.

The third term, **contextual norm similarity**, is the part that would make this context-sensitive without the prefix-domination that sank the embedding route, and it is denser than expected. Read through `fields.slot_prompts()` and `fields.contextual_norms(prompt, instrument="v6")` -- the general instrument only, not the institutional or sexual ones, which are separate constructs under their own directories:

    prompts rated                2,188
    (prompt, word) cells       114,524
    words per prompt          median 60, max 113; 86% of prompts carry >= 10
    WITHIN-SLOT PAIRS        3,878,463
    overlap with movement_v4   2,188 of 2,188 -- EVERY rated prompt is in the
                               raw edge, covering 73.3% of its 2,985 prompts

**Twelve of the nineteen keys are ratings; seven are not, and putting them in a similarity metric would be circular.** `aggression, deliberation, directedness, fit, harm, hedged, interiority, makes_better, makes_worse, mundanity, superego, vocalisation` are what raters gave. `fall, rise, net, net_rate, n_eligible, n_present, ratable` are movement outcomes and bookkeeping that travel in the same dict -- they are the dependent variable, and a similarity built from them would predict displacement with displacement.

**Which is also the argument for `rhyme_pull` as the direct test, and it is a positive argument rather than a fallback.** Jakobson's equivalence class does not have to be semantic. A rime class is a FORMAL equivalence relation, computed exactly from IPA rime keys in `rhyme_pull_pilot.py` -- final-stressed-syllable-onward, onsets stripped -- with no encoder in the path and therefore no encoder gate to fail. That is the sense in which it tests selection directly, and it is why `plan_rhyme.md` reached for prosodic rather than embeddings in the first place.

    HIS TURF, available        rhyme_pull BASE arm. Unrun. The half of the
                               delta design that tests Weatherby.
    HIS TURF, closed           embedding paradigmatic coherence. Measured
                               above; the encoders cannot see the relation.
    OUR TURF, held             existence, norm_change, both delta.
    OUR TURF, new              existence --arm base/aligned, a LEVEL.

## Where the metadata comes from


`roster/models/models.yaml` has no architecture field, and it is AUTHORED (hand-edited, no script writes it), so this folder does not add one. What it does have is `env.profile: ssm`, an environment requirement (mamba-ssm and causal-conv1d kernels) carrying its own `why`, which picks out the SSM and hybrid families exactly. The rest comes from `roster/models/attestations.json`, whose `notes` carry sourced architecture prose at `confidence: high`.

`run.py` declares the architecture of every departure from the default and cites the source inline. **The default is a dense transformer with full attention.** Nothing is coded as unknown.

Two axes, because they cross:

    attn    full | full+linear | local+linear | full+ssm | linear | none
    block   dense | moe | ssm | hybrid

`recurrentgemma` is local attention AND linear recurrence; `Olmo-Hybrid` is full attention AND linear attention. A single axis would have to collapse them into the same cell.

## The charge instrument: what it showed, and why it is the weakest of the three


Content-selectivity slope from `existence` (negative means higher-charge words lose more mass, which is the operation). Roster grand median -0.000295, 43 of 50 lineages negative.

    model                    attn           block        slope      sum|d|
    Falcon-H1-1.5B-Base      full+ssm       hybrid    -0.000442        1566
    OLMoE-1B-7B-0125         full           moe       -0.000388        1686
    Olmo-Hybrid-7B           full+linear    hybrid    -0.000257        1303
    Zamba2-7B                full+ssm       hybrid    -0.000152         477
    falcon-mamba-7b          none           ssm       -0.000124         948
    recurrentgemma-9b        local+linear   hybrid    -0.000114        1933
    Falcon-H1-7B-Base        full+ssm       hybrid    -0.000048        1596
    rwkv-4-7b-pile           linear         dense     +0.000107         552
    -- roster median --                               -0.000295        1185

**Every architecture in the roster displaces except one, and the exception is confounded.** `falcon-mamba-7b` computes no token-token attention of any kind and displaces. Weatherby's own cited counter-architecture, Griffin, displaces. The hedge in (155) is the correct sentence; the surrounding claim is not.

`rwkv-4-7b-pile` is the only non-displacer among the eight. RWKV-4's WKV operator is time-decaying channel-wise linear attention with no token-token dot product ([A Survey of RWKV](https://arxiv.org/html/2412.14847v1)), so it would be the clean case for an attention requirement if the reading held. It does not hold: rwkv-raven-7b is one of seven non-displacing lineages whose median `sum|delta|` is 878 against 1,265 for a sample of twelve displacers. The seven barely move at all. A model that was hardly aligned cannot show a content-selective alignment effect, and architecture is not identified against alignment strength here.

## The second instrument agrees


`norm_change` asks a different question of the same roster: does the base arm's transgressive lift predict what alignment moves along word norms? Until 2026-09-11 it wrote only the aggregate, one row per target already collapsed over lineages, so no question could stratify it. `dose.py --per-lineage` now writes the vector beside it (the aggregate files are byte-identical under the same flags, checked).

Taking the top 12 targets by p and asking how often each model's slope has the same sign as the roster median:

    model                    attn           block     agree
    Falcon-H1-1.5B-Base      full+ssm       hybrid    12/12
    OLMoE-1B-7B-0125         full           moe       12/12
    falcon-mamba-7b          none           ssm       12/12
    Olmo-Hybrid-7B           full+linear    hybrid    11/12
    recurrentgemma-9b        local+linear   hybrid    11/12
    Zamba2-7B                full+ssm       hybrid     9/12
    Falcon-H1-7B-Base        full+ssm       hybrid     7/12
    rwkv-4-7b-pile           linear         dense      6/12

The roster itself agrees with its own median on 38 to 40 of 45 lineages per target, so 12/12 is the normal value and 6/12 is chance. **The model with no attention scores the maximum.**

And the two dissenters are the two weakest movers. `rwkv-4-7b-pile` and `Falcon-H1-7B-Base` are also the two lowest `|slope|` in the existence table above. Two instruments, built on different constructs, pick out the same two models, and the property they share is not an architecture, it is how little alignment did to them. That is the confound stated once and then confirmed independently.

## The matched contrasts, and why they disagree


    1  CONTROLLED BY DESIGN (AI2)
       Olmo-3-1025-7B     full          dense    -0.000159    2045
       Olmo-Hybrid-7B     full+linear   hybrid   -0.000257    1303

    2  SAME PRETRAINING CORPUS (Google)
       gemma-2-9b         full          dense    -0.000498    2261
       recurrentgemma-9b  local+linear  hybrid   -0.000114    1933

    3  ONE VENDOR, FOUR CORPORA (TII, all ~7B) -- WEAK, NOT A CONTROL
       falcon-7b          full          dense    -0.000266    1292
       Falcon3-7B-Base    full          dense    -0.000158    1109
       falcon-mamba-7b    none          ssm      -0.000124     948
       Falcon-H1-7B-Base  full+ssm      hybrid   -0.000048    1596

    4  DENSE vs MoE (AI2)
       Olmo-3-1025-7B     full          dense    -0.000159    2045
       OLMoE-1B-7B-0125   full          moe      -0.000388    1686

Contrast 1 is the best control in the roster and it is not ours. AI2 built Olmo Hybrid as a controlled experiment: "we train Olmo Hybrid, a 7B-parameter model largely comparable to Olmo 3 7B but with the sliding window layers replaced by Gated DeltaNet layers", demonstrating the benefit of hybrid models "in a controlled, large-scale setting" (arXiv:2604.03444, Merrill et al., 3 Apr 2026, quoted in `attestations.json`). Same lab, same three-stage pipeline, same data mix, 5.50T against 5.93T tokens. The declared architectural difference is the attention mechanism and nothing else. **Replacing attention layers with linear-attention layers made displacement stronger, not weaker.**

**Contrast 3 is not the vendor control it looks like, and should not be reported as one.** One lab is not one corpus, and the attestations say so: `falcon-7b` is RefinedWeb-English and RefinedWeb-French; `Falcon3-7B-Base` is a single 14T-token run over "web, code, STEM, and curated high-quality and multilingual data"; `falcon-mamba-7b` is 5.8T with "carefully selected data mixtures"; `Falcon-H1` is different again. Four models from one lab, four corpora. It is weaker than contrast 1 and weaker than contrast 2.

Contrast 2 is attested as sharing a corpus ("RecurrentGemma uses the same training data and data processing as used by the Gemma model family"; "The architecture is Griffin, not Gemma's transformer") and goes the other way by a factor of four.

### A reading that makes the two contrasts agree, POST HOC and unregistered

The two swaps are not the same manipulation in opposite directions. They remove different halves of the attention mechanism.

    contrast 1   Olmo-Hybrid KEEPS full attention and loses its SLIDING-WINDOW
                 layers (replaced by Gated DeltaNet).   local removed
                 -0.000159 -> -0.000257                 displacement UP
    contrast 2   recurrentgemma is Griffin: sliding-window attention plus
                 RG-LRU, so it has local attention and NO global attention.
                 -0.000498 -> -0.000114                 global removed
                                                        displacement DOWN

Read on the local/global axis rather than the presence/absence axis, **both contrasts point the same way**: global attention supports displacement, local attention does not, and removing local attention may even free capacity for it. `falcon-mamba-7b`, which has neither, sits low at -0.000124, and `rwkv-4-7b-pile`, which has neither, is the one non-displacer.

**This is post hoc on two contrasts of one model each, generated after seeing the signs, and it is not a finding.** Across vendors it already breaks: `gemma-2-9b` has full global attention and is the strongest displacer here at -0.000498, while `Olmo-3-1025-7B` also has full global attention and sits at -0.000159, so vendor and corpus swamp it the moment the comparison leaves a matched pair. It is recorded because it is cheap to state, it is falsifiable, and `rhyme_pull` across these same models would test it: if global attention is what carries the operation, the same ordering should appear on the paradigmatic instrument. **It has to be written down before that fleet runs or it is worthless.**

**Taken together these do not support an architecture effect in either direction.** Two same-lab, same-data contrasts with opposite signs, over one observation each, is what no effect plus lineage-level noise looks like. The defensible claim is the negative one: the operation is not confined to full attention, and the sign of the architecture difference is not stable across the two cases where the confounds are actually controlled.

## WHY WOULD ARCHITECTURE SHOW UP AT THE CUT AND NOT IN THE LANGUAGE?

RH's question, 2026-09-11. **Nothing below is measured.** These are candidate explanations, in the order this seat would spend money testing them, with the deflationary rivals named first because they are cheaper and would dissolve the finding.

**1. The two stages are not measured at the same point in their optimization.** Base models are read at a converged optimum reached over trillions of tokens. Post-trained checkpoints are read after roughly two million examples, a far shorter run that need not have converged at all. Two models stopped early in an unconverged optimization will differ idiosyncratically without any architecture mediating anything. This is the rival to beat, and it predicts something checkable: the divergence should SHRINK with further post-training. `SFT->DPO` at +0.511 against `base->SFT` at +0.233 is weakly consistent with exactly that.

**2. "Same data" may not be "same optimization."** A lab that changes the attention mechanism commonly retunes the learning rate, the schedule, or the epoch count. `attestations.json` establishes the same Dolci mixtures; it does not establish the same hyperparameters, and nothing in this folder checked. If AI2 tuned the hybrid's SFT differently, the divergence is the tuning.

**3. The raw-edge confound, specific to the aligned arm. TESTED, and it splits.** Post-trained models were read with NO chat template, and this roster contains aligned models that emit the assistant frame unbidden (E-ASSIST-AMBIENT). Re-run on the `prefill` edge: the architecture GAP is unchanged (0.621 raw, 0.622 framed at SFT) so it is not a format-compliance artifact, but the move-DIRECTION cosine goes +0.229 to +0.595 and the "nearly orthogonal" claim was struck. See the correction above. **This rival is dead for the gap and was correct for the directions.**

**4. Data volume overdetermines the base and underdetermines the cut.** Six orders of magnitude separate 5.9T pretraining tokens from ~2.15M SFT examples. If the pretraining objective on that much natural text admits essentially one good solution, every architecture is pushed into it and the architecture becomes a means rather than a difference -- which is what rank 25/50 for an attention-free model looks like. Post-training constrains far less, so the same gradient signal applied to different parameterizations is free to land in different places. On this account architecture was always present and only becomes VISIBLE when the data stops dictating the answer.

**5. A small perturbation is governed by local geometry; a large optimization by the objective.** The same point differently: pretraining selects a basin, and which basin is a question about the data. Alignment is a nudge WITHIN a basin, and where a nudge goes is a question about the local curvature, which is the architecture. Big optimization, data wins. Small perturbation, geometry wins.

**6. The head is shared and the tail is not.** All these models agree on high-frequency structure because the corpus fixes it. Alignment operates on the rare and the marked -- refusals, hedges, register -- where the corpus constrains least and models were always freest to differ. Our own instrument reads words above p = 0.001, so it is already looking below the head. This predicts the divergence should concentrate in low-probability words, which is directly checkable on data we hold.

**4 through 6 are one family and are not really rivals to each other**: the architecture is a degree of freedom that the pretraining data consumes and that post-training gives back. **1 through 3 would make the finding go away.** They should be run first, and (3) is nearly free.

The result is worth stating carefully for the project because of where it lands rather than because of its size. This seat's campaign holds that the cut is where the interesting thing happens, and this is a case of the material substrate becoming legible exactly there and nowhere else -- but "the architecture is visible at the cut" is a claim about a measurement, and it stays that until (1) through (3) are closed.

## PRE-COMMITMENT, recorded 2026-09-11, before any rhyme_pull cell was measured


Written now because it costs nothing now and cannot be recovered later. If the `rhyme_pull` fleet runs and contrast 1 and contrast 2 disagree in sign again, two readings are available and **they are not distinguishable after the fact**: that the charge instrument was too blunt, and that there is no architecture effect to find. `norm_change` has already produced the first pattern on a second construct, so the ambiguity is not hypothetical.

The commitment, in advance:

1. **A second sign disagreement is not instrument failure.** It is not grounds for a third instrument.
2. **It is a BOUND, not a null.** It says any architecture effect is smaller than lineage-level variation at n=2 per contrast. It does not say architecture does not matter, and it must not be written up as if it did.
3. **The local/global reading above is the prediction under test**, in the form stated there: if global attention carries the operation, `rhyme_pull` should order these models the same way charge-selectivity did. It was recorded before the fleet, and a version of it arrived at after seeing rhyme results is a different claim with no standing. **AMENDED the same day, before any cell: this prediction requires BOTH ARMS and is not testable on bases alone.** Every number in this folder is a base->aligned delta -- `existence` regresses (p_aligned - p_base) on scene, `norm_change` regresses (aligned - base) on the base dose -- so they measure what alignment DOES. A base-only `rhyme_pull` measures a base CAPACITY. Ordering a capacity against a delta compares two constructs, which is this seat's most repeated defect and would have been undetectable once the numbers existed. All 12 lineages have aligned counterparts in the roster, so the delta design is available: `falcon-mamba-7b-instruct`, `recurrentgemma-9b-it`, `Olmo-Hybrid-Instruct-DPO-7B`, `rwkv-raven-7b`, and so on.

   The two questions are both real and they are not the same, which is why the amendment is an addition rather than a replacement. **Weatherby's claim is about the architecture**, so a base-only capacity read is the right test OF HIM. **The comparison with the charge instrument needs the delta.** The delta design answers both, because it contains the base arm.
4. **What would raise n** is the only route out, and it is models, not cells per model: more matched pairs where a lab swapped one attention mechanism and held the corpus. 178 poems per model does not make two models into more than two.

Subject to RH; the spend and the route are his call, and this is recorded rather than decided.

## Limits, stated


- **n on the side that matters is one and one.** One pure SSM, one linear-attention-only model. `run.py` runs no between-group test and this README makes no distributional claim about architecture classes. These are positions in a distribution of 50.
- **Everywhere except contrasts 1 and 2, architecture is confounded with vendor, scale, vintage, and corpus.** That is why those two lead.
- **Alignment strength varies across the roster by a factor of four** and is not controlled here. The `sum|delta|` column is reported beside every slope for exactly this reason.
- **`norm_change` runs on 45 pairs, not existence's 50.** Its README (line 995) makes `--match-framed` non-optional, because raw at n=50 beside framed at n=45 differs partly by which labs ship a chat template. All 12 architecture models are in the 45, so nothing here is lost to it, but the two instruments are not quite the same population.
- **`rate_and_magnitude` writes no results file**, so `sum|delta|` is recomputed directly from `movement_v4` here rather than looked up.
- `rhyme_pull` would be the sharpest test of the Jakobson claim specifically, since it measures the paradigmatic axis directly rather than charge-selectivity. It is a pilot, not a producer, and was not run here.

## Running it


    python run.py > results.txt

Pure lookup and one query. No model loading, no GPU.
