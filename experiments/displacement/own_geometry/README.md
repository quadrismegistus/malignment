---
title: Does alignment move the model's own geometry, or only re-weight it?
status: two ladders and the seven-paraphrase replication complete; the blank-state norm is a NEW contrast and is with RH
unit: one lineage ladder with separated stages; one prompt
---

# Own geometry

`displacement/chain_of_connections` asked whether `kill` and `scream` are close in a semantic space and answered no, in three spaces. But all three were **foreign to the model**: bge-m3 is someone else's encoder, GloVe is type-level co-occurrence, and the Llama input embedding was read as a static table. Freud's chain is "determined in a particular way", and what determines it here is the training. So the question has to be asked of the model that underwent the training, in its own spaces, at each stage.

**Commissioned by RH through the paper seat. Contrast, baseline and prediction were stated before anything ran and are recorded below unchanged.**

## The question, in two halves

1. Does the rank of `scream` relative to `kill` **change** from base to SFT to DPO to RLVR, in any of the model's own spaces, beyond what the controls change?
2. And if something moves, does **`kill` move toward the vocal cluster** or the vocal cluster toward `kill`?

## Prediction, recorded in advance

> The geometry barely moves in any space and the probabilities do, which would say alignment re-weights an existing geometry rather than rewiring it; the alternative worth finding is that the unembedding rows move -- they are the cheapest thing for a preference objective to change -- while the input embeddings and residuals do not, which would locate the operation.

## Design

**Ladders.** Four stages each, base / SFT / DPO / RLVR:

    tulu       meta-llama/Llama-3.1-8B -> Tulu-3-8B-SFT -> -DPO -> Llama-3.1-Tulu-3.1-8B
    olmo       Olmo-3-1025-7B -> Olmo-3-7B-Instruct-SFT -> -DPO -> Olmo-3-7B-Instruct
    olmo2-1b   OLMo-2-0425-1B -> -SFT -> -DPO -> -Instruct        (smoke ladder)

**Prompt.** The exhibit, `She was so angry she wanted to`.

**Candidates.** The same 307 that `chain_of_connections` uses after its dictionary and length filters — every word clearing theta on this prompt in either arm, minus non-words, case duplicates and fragments. **30 of the 307 are multi-token**, represented by their first subtoken in the type-level spaces and by their whole span in the contextual ones.

**Four spaces, each the model's own**, all mean-centred over the candidate set per stage because with one frame and one word varying the shared component otherwise dominates (`chain_of_connections` §7):

    1 input      embedding rows of the candidate tokens
    2 residual   hidden state at the candidate's own position in
                 "She was so angry she wanted to {word}", at 2/3 depth and
                 as the mean over all layers
    3 unembed    the rows the candidates compete with at the logit
    4 decision   the residual at the BLANK, dotted with each candidate's
                 unembed row -- the logit decomposed

**Space 2 is not the representation that chose the word**, and the caveat travels with it: the state at the word's position is downstream of having the word. Space 4 exists for that reason and is the only one of the four that is the decision itself.

**Measure.** Cosine of each candidate to `kill`, and its rank among the 307, at every stage. Reported for `scream` and each lineage-grain destination (`cry`, `hurt`, `hit`, `punch`, `destroy`, `fight`), with `eat`, `dance`, `sit`, `write` carried unchanged as controls, and each candidate's probability at the blank beside them.

**Baseline for "moved".** The distribution of |rank change| across all 307 candidates between consecutive stages. A shift for `scream` is reported as a **percentile of that distribution**, so a move is judged against how much everything moves.

**Direction.** Cosine is symmetric and cannot say who moved. The stages are continuous fine-tunes with no rotation between them, so the same row at two stages is comparable in absolute terms: `||v_next - v_prev||` per candidate, with `kill` and the vocal cluster reported as multiples of the median candidate's movement.

## The gate that could have faked the entire result

The stages do not share a tokenizer file — every `tokenizer.json` differs by md5 — and **the Tulu base has vocab 128256 against its children's 128264.** If a candidate's token id shifted between stages, every "the geometry moved" reading would be an index shift wearing a finding's clothes.

Checked before anything was built, and re-asserted at run time by `check_ids`, which **refuses rather than warns**: the 307 candidates tokenise identically at all four stages of both ladders, **0 differences**.

## Caveats carried

- One prompt family. The six other anger paraphrases are the replication and are not yet run.
- **A rank in a geometry is not a route.** The standing warning from `chain_of_connections` §§4, 5, 9 applies here unchanged.
- `p` is the probability of the candidate's **first token** at the blank. For the 277 single-token candidates that is the word's probability; for the 30 multi-token ones it is an upper bound, and no beam is run here.

## Producers

    python run.py --ladder tulu       # loads four models, writes results/geometry_tulu.{json,npz}
    python tables.py --ladder tulu    # renders every table from the saved geometry, no models

`run.py` saves the raw matrices because the direction question needs displacement and a cosine is symmetric; `tables.py` never loads a model, so the analysis can be redone without four checkpoint loads.

---

# Result: the geometry does not move and the probabilities do

**Tulu / Llama-3.1-8B, base → SFT → DPO → RLVR.** The displacement happens on this ladder, in full view:

    p(first token) at the blank      base      sft      dpo     rlvr
    kill                          0.13825  0.10507  0.08524  0.09132
    scream                        0.04559  0.10184  0.17491  0.13924

`scream` rises 3.8x and **overtakes `kill` between SFT and DPO**. That is the operation this project is named for, occurring in one lineage across four checkpoints.

Now the same four stages, in the model's own spaces. `scream`'s rank among the 307 candidates by cosine to `kill`:

    space        base   sft   dpo  rlvr    total drift
    input         176   162   162   163      13 of 307
    unembed       157   156   156   156       1 of 307
    resid (2/3)   162    95    90    95      72 of 307
    decision       21    19    28    26       7 of 307

**While its probability quadruples, its position relative to `kill` moves by 1 rank in the unembedding and 13 in the input embedding.**

## And "it moved" has to be read against how much everything moves

    |rank change| over all 307        median   p90   max  |  scream    percentile
    input        base -> sft              2     7    15  |     14       99th
    input        sft  -> dpo              0     1     2  |      0       88th
    unembed      base -> sft              1     5    10  |      1       52nd
    decision     base -> sft              5    15    29  |      2       27th
    decision     sft  -> dpo             10    29    54  |      9       48th

`scream` IS the 99th-percentile mover in the input space at base→SFT — and that means 14 ranks in a space whose median move is 2. It is the top of a distribution that barely exists. In the decision space, the one that actually chooses, `scream` moves **less** than the median candidate at every transition (27th, 48th, 42nd percentile). **Nothing is done to `scream`'s geometry that is not done to everything.**

## The correlation the design asked for by eye, computed

Spearman between |change in log p| and |change in rank|, over all 307 candidates. If alignment rewired the geometry to make room for the words it promotes, this would be positive:

    space         bas>sft   sft>dpo   dpo>rlv
    input          +0.002    -0.071    -0.103
    resid_23       -0.025    +0.186    -0.030
    resid_mean     +0.033    +0.164    +0.024
    unembed        -0.068    +0.001    -0.089
    decision       +0.018    +0.029    +0.039

**Zero, everywhere.** The words whose probability changes most are not the words whose geometry changes most. The two are unrelated.

## Who moved: nobody in particular

`||v_next − v_prev||` as a multiple of the median candidate's movement:

    space      transition      kill   vocal cluster   scream    eat
    input      base -> sft    0.98x       0.97x        1.09x   1.04x
    unembed    base -> sft    1.11x       0.99x        0.96x   0.95x
    unembed    sft  -> dpo    1.17x       1.25x        1.08x   0.95x
    decision   sft  -> dpo    0.93x       0.98x        0.94x   0.84x

Every quantity sits within about ±25% of the median candidate. **`kill` does not move toward the vocal cluster and the vocal cluster does not move toward `kill`.** The second half of the question has a null answer, and the null is tight rather than underpowered: the estimator would have shown a 2x displacement easily and nothing reaches 1.3x.

## The prediction was right and its named alternative is refuted

Recorded in advance: *"the geometry barely moves in any space and the probabilities do... the alternative worth finding is that the unembedding rows move -- they are the cheapest thing for a preference objective to change -- while the input embeddings and residuals do not."*

The first half holds. The alternative is **false, and backwards**: the unembedding is the most STATIC space of the four. Median row movement:

    transition     input    unembed    resid_23   decision
    base -> sft   0.0239    0.0215      3.6359     0.3403
    sft  -> dpo   0.0008    0.0006      1.1791     0.3592
    dpo  -> rlvr  0.0017    0.0016      0.7356     0.1486

**Both weight matrices are frozen to three decimal places after SFT, while the residual stream and the decision keep moving.** Between SFT and DPO — the transition where `scream` overtakes `kill` — the unembedding rows move by 0.0006 and the decision by 0.36, six hundred times more.

So the operation is **not in what the words mean to the model and not in the rows they compete with. It is in what the model computes at the blank.** DPO changes the state that does the choosing while leaving the vocabulary's geometry alone.

## What this licenses, and what it does not

- **Licensed:** on this ladder and this prompt, alignment re-weights an existing geometry rather than rewiring it, and the re-weighting is located in the layers rather than in either embedding table.
- **Licensed:** `kill → scream` is not a movement of `kill` toward `scream` in any of the model's own spaces. Whatever relates them, the training does not build it by moving them together.
- **NOT licensed:** that the geometry is unchanged *everywhere* — `resid_23` moves `scream` 72 ranks, the one place something does happen, and that space is the one whose caveat is that it is not the representation that chose the word.
- **NOT licensed:** anything about other prompts. One prompt family; the six anger paraphrases are the declared replication and are not yet run.
- A rank in a geometry is still not a route.

---

# The second ladder replicates it on a family that does something else entirely

**Olmo-3-7B, base → SFT → DPO → Instruct.** This lineage does not displace. It evacuates:

    p(first token)   base      sft      dpo     rlvr      fall
    kill          0.09910  0.00787  0.00063  0.00040     250x
    scream        0.03320  0.01308  0.00199  0.00142      23x
    cry           0.03217  0.01948  0.00272  0.00210      15x
    eat           0.00432  0.00011  0.00002  0.00002     200x

Every candidate falls, the innocuous ones included. This is the genre-collapse behaviour already on record for OLMo — the frame is vacated rather than the word substituted — and it makes the family a good second test, because at the probability level it is doing the **opposite** of Tulu.

`scream`'s rank to `kill` across the two ladders:

    space        tulu: base -> rlvr   drift      olmo: base -> rlvr   drift
    input             176 ->  163       13            181 ->  181        0
    unembed           157 ->  156        1            234 ->  241        7
    resid (2/3)       162 ->   95       67            139 ->  117       22
    decision           21 ->   26        5            161 ->  250       89
    p(scream)       0.046 -> 0.139    3.0x up      0.033 -> 0.001     23x down

**The two families move probability in opposite directions by factors of 3 and 23, and in both the type-level geometry is static** — `scream`'s input-space rank moves 13 places in one and 0 in the other.

The geometry-versus-probability correlation is null on this ladder too:

    space         bas>sft   sft>dpo   dpo>rlv
    input          +0.014    -0.106    +0.034
    resid_23       -0.025    +0.026    -0.081
    unembed        -0.021    -0.039    +0.075
    decision       +0.073    +0.034    -0.001

And nothing is singled out by displacement: in the unembedding at base→SFT, `scream` moves 1.55x the median candidate, the vocal cluster 1.25x, `kill` 1.19x, `eat` 1.13x — the largest separation anywhere in either ladder, and it is a factor of 1.4 between `scream` and a control.

**Where OLMo differs is the decision space**, and it differs in the direction the collapse predicts: `scream` falls 161 → 250 of 307, moving 58 ranks at base→SFT (92nd percentile) and 28 more at SFT→DPO (94th). In Tulu, the ladder that promotes `scream`, the decision-space rank is flat at 21 → 26. So the decision space registers this family's operation — evacuation — while registering nothing for the other family's substitution.

## Two ladders, one answer

    Licensed by both: alignment re-weights an existing geometry rather than
    rewiring it, and the type-level spaces (input, unembed) are static to
    three decimal places after SFT in both families.

    Licensed by both: the geometry does not move where the probability moves.
    Ten correlations across two ladders and five spaces, range -0.11 to +0.19.

    Licensed by both: `kill` does not move toward the vocal cluster, nor the
    cluster toward `kill`. Nothing exceeds 1.6x the median candidate.

    NOT settled: what DOES change. The residual stream and the decision move
    in both ladders, but they move for everything, and in Tulu the decision
    space is flat for `scream` precisely where its probability triples. The
    locating claim this folder can make is negative -- not the embeddings,
    not the unembeddings -- and the positive half is open.

The obvious next question, and it is not answered here: if the decision-space rank of `scream` is flat while `p(scream)` triples, the promotion is happening in the **magnitude** of the blank-position state rather than in its direction, which a cosine cannot see. That is one norm calculation away and is the natural continuation.

---

# Replication: the seven anger paraphrases, Tulu ladder

Named in the commissioned design. The set is the one declared in `substitution_shape/README.md` — the seven prompts where `kill` is the crossed biggest faller and the riser is `scream` — and that README's verdict travels with it: the direction holds on all seven and **the magnitude varies fourfold**, with base `kill` running 16 to 42 of 50 before alignment touches anything.

**The displacement reproduces on all seven.** `p(scream)` rises base→DPO on every one; `p(kill)` falls on six, and **rises slightly on one** (`I was so angry I wanted to`, 0.0950 → 0.1003):

    prompt                              p(scream) base -> dpo     p(kill) base -> rlvr
    She was so angry she wanted to        0.0456 -> 0.1749         0.1382 -> 0.0913
    My rage is growing and I want to      0.0360 -> 0.0705         0.0289 -> 0.0154
    My rage grew until I wanted to        0.1057 -> 0.1706         0.0682 -> 0.0488
    I was so angry I wanted to            0.0653 -> 0.1435         0.0950 -> 0.1003   <- kill rises
    Her rage grew until she wanted to     0.1864 -> 0.2900         0.0675 -> 0.0351
    She is so angry she wants to          0.0234 -> 0.0710         0.1217 -> 0.0891
    She was so furious she wanted to      0.0233 -> 0.1138         0.1396 -> 0.1084

**And the geometric null reproduces on all seven.** `scream`'s rank to `kill`, base → last stage, with the drift as a percentile of that prompt's own |rank change| distribution:

    space        drift across the seven      percentile range
    input            13 - 16                   97th - 100th
    unembed           1 -  8                   42nd -  98th
    decision          0 -  8                    5th -  50th
    resid (2/3)      29 - 84                   80th -  99th

In the **decision** space — the one that chooses — `scream` moves 0 to 8 ranks and sits at or below the median candidate on every single prompt (5th to 50th percentile), while its probability roughly triples. The only space with real movement is `resid_23`, the space whose standing caveat is that it is not the representation that chose the word.

The geometry-versus-probability correlation, 28 of them (7 prompts × 4 spaces), base → last stage: **range −0.184 to +0.175, every one null.**

## BUT THIS IS A REPLICATION FOR ONLY TWO OF THE FOUR SPACES

`input` and `unembed` are **properties of the model, not of the prompt**. The seven runs read the same two weight matrices; all that changes is the candidate set they are ranked against. So for those two spaces these are not seven observations, they are one measurement against seven overlapping reference sets — and the sets overlap heavily:

    642 distinct candidates over the seven; the seven sets sum to 2,495
    mean multiplicity 3.9; pairwise Jaccard 0.46 / 0.61 / 0.78 (min/median/max)
    190 candidates -- 30% of the union -- appear in ALL seven

That is exactly the hazard `substitution_shape` already named for this prompt family: *neither seven independent observations nor one observation repeated*. It applies here with a sharper edge, because for the type-level spaces the underlying quantity is literally identical across rows, and the near-constant input drift (13, 15, 13, 15, 15, 14, 16) is the signature of that rather than seven agreeing measurements.

**The genuine replication is `resid_23` and `decision`**, which are computed from a forward pass on each prompt and so do differ across the seven. Those are the two that carry the claim, and they hold: decision-space drift 0–8 at the 5th–50th percentile on all seven.

## What the replication adds, and what it does not

- **Adds:** the decision-space null is a property of the frame, not of the one prompt looked at first, across a family whose lineage-grain magnitudes vary fourfold.
- **Adds:** a case where `p(kill)` *rises* while `p(scream)` rises too, and the geometry is static there as well — so the null is not conditional on `kill` falling.
- **Does not add:** independent evidence about the input and unembedding matrices. One measurement, seven reference sets.
- **Does not address:** whether the promotion lives in the magnitude of the blank-position state rather than its direction. That is a new contrast, it is with RH, and it is not run.
