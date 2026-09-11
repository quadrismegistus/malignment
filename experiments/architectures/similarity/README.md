---
subject: architectures
kind: question
status: "RUN 2026-09-11. 50 endpoint BASES and 50 ALIGNED endpoints, pairwise, 1,225 pairs each, 200 v6-rated prompts, words above the twp theta of 0.001. Four measures: Jaccard, probability-weighted Jaccard, type-norm centroid distance, contextual-norm centroid distance. NOT REGISTERED, no between-group test; n on the attention-free side is one pure SSM and one RNN."
question: Do models of different architectures differ in what they put in a slot, at base and after alignment?
headline: "CORPUS DOMINATES AND ARCHITECTURE DOES NOT REGISTER. The most similar pair of 1,225 bases is pythia-6.9b and rwkv-4-7b-pile, a transformer and an RNN that share the Pile, and all three attested same-corpus/different-architecture pairs sit in the top 7. falcon-mamba-7b, which computes no attention of any kind, is the MEDIAN model of the census at rank 25/50. Separately: alignment moves models APART, base-base median 0.407 against aligned-aligned 0.669, on all four measures."
---

# similarity

**Do these models differ by architecture at all?** The question underneath the other three: before asking whether alignment's operation depends on the attention mechanism, ask whether anything does.

Producer: `run.py --arm base|aligned`. Reads `fields.contextual_norms(instrument='v6')` and `movement.words_multi` at rule_version 4.

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

## THE SAME ANSWER AT A SECOND GRAIN: what the models actually WROTE

    python run.py --grain page

RH's point, 2026-09-11: **the base arm of a delta instrument is a level, and a level is architecture-comparable.** `passage_analysis/selection_and_combination` computes aligned-minus-base, so it holds per-lineage BASE measurements, and `f_b` is each base model's word-frequency distribution over its own passages. That is what a model actually wrote, against this folder's slot grain of what it would assign probability to. Five architecture lineages are in it -- two pure SSMs, a Mamba hybrid, Griffin and the MoE -- better coverage than any other passage artifact.

    drop top-1000 function words, 35 lineages, 2,918 word types
    same vendor, SAME block    n=  6  median 0.4995
    same vendor, DIFF block    n=  9  median 0.6163
    different vendor           n=580  median 0.4210

**Same vendor with DIFFERENT architectures is more alike than same vendor with the SAME one.** The two pure SSMs score 0.5331 to each other, BELOW the same-vendor-different-block median, because `Falcon3-Mamba` shares a training generation with the dense `Falcon3` family while `falcon-mamba` is the earlier run:

    Falcon3-10B-Base   Falcon3-7B-Base         0.7625   dense / dense
    Falcon3-10B-Base   Falcon3-Mamba-7B-Base   0.7013   dense / ssm
    Falcon3-7B-Base    Falcon3-Mamba-7B-Base   0.6305   dense / ssm
    falcon-mamba-7b    Falcon3-Mamba-7B-Base   0.5331   ssm   / ssm

Training generation and corpus dominate; architecture does not register. Same answer as the slot grain, reached from what the models write rather than from what they would choose.

**TWO TRAPS, BOTH NEARLY REPORTED.** On raw frequencies every pair scores ~0.99, because a word-frequency vector is function words -- the first version read that as models being alike, and `--drop-head` exists because of it. And after dropping them the SSM-to-SSM cosine rose above the dense baseline (0.5331 against 0.4337), which looked like architecture clustering until the vendor control was run. `recurrentgemma-9b` is excluded rather than rescued: 98.3% of its passages are degenerate repetition loops, so its vocabulary vector is "she".

## CORPUS DOMINATES, AND THAT IS A POSITIVE RESULT RATHER THAN A NULL


The twelve most similar base pairs of 1,225:

     1  0.273  pythia-6.9b            rwkv-4-7b-pile
     2  0.282  Olmo-3-1025-7B         Olmo-Hybrid-7B          same vendor
     3  0.282  granite-3.0-8b-base    Falcon-H1-7B-Base
     4  0.282  rwkv-4-7b-pile         jais-family-6p7b
     5  0.286  Olmo-Hybrid-7B         Falcon-H1-7B-Base
     7  0.288  gemma-2-9b             recurrentgemma-9b       same vendor
        0.407  roster median
        1.017  roster max

**The most similar pair in the census is a transformer and an RNN.** They share no architecture and no weights. They share the Pile.

`malignment/similarity.py` reached that same pair by a different route and uses it as its measured ceiling for "similar because of data" -- *"a transformer and an RNN, no shared weights, both trained on the Pile. Anything at or below that is corpus, not lineage"* -- established on argmax agreement and JS over full distributions. This instrument is contextual-norm centroids over rated slots, and it returns the same pair at rank 1 of 1,225. Two unrelated measurements, one answer.

**All three attested same-corpus/different-architecture pairs are in the top 7**: pythia/rwkv at 1, AI2's controlled attention swap at 2, gemma-2/recurrentgemma at 7. Hold the corpus and change the architecture -- including changing it to no attention at all -- and the result is among the most similar pairs there are.

So the folder's finding is not "we failed to detect architecture". It is that **corpus determines what a base model will put in a slot and architecture does not register**, with three controls and a second instrument agreeing.

**WHERE THIS IS STILL THIN.** Everything in this file reads one window: which words a model puts in a slot, profiled by charge, norms and overlap. Four instruments that share a window are weaker than four independent ones. `rhyme_pull` is unrun and is the one test designed to catch what these cannot -- a formal equivalence class rather than a semantic profile. And n on the attention-free side is one pure SSM and one RNN.

## WHAT WAS WITHDRAWN, AND WHY IT MATTERS THAT IT WAS


An earlier version of this file led with "the architecture shows up at the cut, not in the language", on the Olmo-3 / Olmo-Hybrid gap growing from 0.28 at base to 0.62 at SFT under attested-identical post-training data. **That is withdrawn.** Calibrated against the two populations above:

    the pair at base   0.28   bottom 1% of the 1,225 base-base distances
    the pair at SFT    0.62   35th percentile of aligned-aligned

The pair begins as one of the most similar in the entire census and ends **still more similar than typical**. It did not diverge from the crowd; the crowd spread out around it and the pair regressed toward the middle, which is what any extreme starting value does under a noisy population-wide transformation. The widening was real and it was not about architecture.

The general form of the sentence had already failed a smaller check: of three base-to-SFT steps measured on this scale -- Llama-3.1-8B to Tulu-3-SFT at 0.223, Olmo-Hybrid at 0.323, Olmo-3 at 0.513 -- **only one exceeds the base-to-base median of 0.407**, so a claim that an alignment step outruns the whole spread of architectures generalised from the largest of three.

**Both failures had the same shape**: a quantity read without the population it belongs to. The surviving claims in this file are the ones stated against 1,225 pairs.

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
