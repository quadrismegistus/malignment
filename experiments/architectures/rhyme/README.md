---
subject: architectures
kind: question
status: "RUN 2026-09-12. @malign's fleet: 94 models, 5,325,818 distinct closure keys over 1,786 prompts, all three matched contrasts complete on BOTH arms, ~$19.70. 48 of 50 endpoint lineages covered -- the 32B and 70B arms are uncovered BY CHOICE (24 GB cards; big80/twogpu exist) and all five missing checkpoints are DENSE, so no claim here needs them. Analysis producer `run.py` written here; `called` slot, 177 of 180 cells usable, 47 lineages with both arms present. THE REGISTERED PREDICTION FAILED AS WRITTEN and the ranking it asked for was confounded -- that is a defect in the pre-commitment, not a result."
question: Does rhyme pull -- probability mass on the scheme partner's rime class -- depend on the attention mechanism?
headline: "ON THE ONE INSTRUMENT THAT READS A FORMAL EQUIVALENCE CLASS, MODELS WITHOUT ATTENTION ARE NOT DEFICIENT. Base-arm rhyme pull: granite-3.0-8b 0.086, Mistral-7B 0.071, Zamba2-7B (hybrid) 0.067, gemma-2-9b 0.066, falcon-mamba-7b (NO ATTENTION) 0.031 -- which exceeds Olmo-Hybrid 0.026 and Olmo-3 0.015, both of which have attention. And under alignment falcon-mamba shows the LARGEST relative GAIN of any lineage clearing the floor (+1.448), against a fleet where most models lose rhyme pull. The registered prediction -- that the Olmo-3/Olmo-Hybrid pair would show the smallest |delta| because it holds global attention constant -- FAILS literally (ranks 35 and 39 of 47), and the |delta| ranking it asked for is confounded by baseline, since a model with no rhyme pull has nothing to lose. Scale-free, the pair sits at -0.500 and -0.520, adjacent; that is the prediction's substance but it is a POST HOC repair of a statistic chosen before the data existed."
---

# rhyme

## THE RESULT, AND WHAT THE PRE-COMMITMENT ACTUALLY DID

**Base-arm rhyme pull** -- target-class mass minus a matched non-partner class, `called` slot, 177 cells:

    granite-3.0-8b-base      full/dense          0.08612
    Mistral-7B-v0.1          full/dense          0.07070
    Zamba2-7B                full+ssm/hybrid     0.06733
    gemma-2-9b               full/dense          0.06630
    Qwen3-8B-Base            full/dense          0.03791
    OLMoE-1B-7B-0125         full/moe            0.03287
    falcon-mamba-7b          none/ssm            0.03098   <- NO ATTENTION
    Olmo-Hybrid-7B           full+linear/hybrid  0.02586
    Olmo-3-1025-7B           full+local/dense    0.01549
    Falcon-H1-7B-Base        full+ssm/hybrid     0.00803

**`falcon-mamba-7b`, which computes no attention of any kind, has MORE rhyme pull than `Olmo-3-1025-7B` and `Olmo-Hybrid-7B`, both of which have it.** A Mamba-attention hybrid sits third of the whole fleet. This is the instrument built to read Jakobson's axis of selection in the one form the poetic function names, on IPA rime keys with no encoder in the path, and it does not separate the architectures.

**Why the rime keys could be revised without re-renting anything, and whose call that was.** The classes are applied OFFLINE, on the Mac, with the paper-pinned `prosodic`; nothing phonological ran on a box. That split is **RH's** -- "don't run prosodic on the cloud" -- and it has already paid once: a v1 rime key fell back to syllable SPELLING and shattered /ei/ into ay/ey/eigh, and fixing it cost an afternoon rather than a re-rent. The fleet stores the PRIMITIVE (`p_close`, `k_rider`, `n_scored`) and not a ratio, which is @malign's, and is why `line_closure`, `rhyme_given_closure` and `close_given_class` are all derivable here without touching a GPU.

### The population, stated precisely, because three numbers are in play

    94 models        in the closure table
    48 of 50         endpoint lineages covered by the fleet
    47 lineages      enter the delta table here: both arms present.
                     --min-cells does NOT bind: all 94 models carry 176-177
                     cells, so the flag is a guard that has never fired

**The two uncovered lineages are @malign's choice and not a limit**: `Olmo-3-1125-32B` and `Llama-3.1-70B` need 64.5 and 141.1 GB and he ran 24 GB cards; `big80`/`twogpu` profiles exist and it is a few dollars. `internlm2` failed at load on a destroyed box and its reason is unrecorded.

**No claim here needs them.** All five missing checkpoints are DENSE -- `Olmo-3-1125-32B` and `Olmo-3.1-32B-Instruct` are `full+local/dense`, both Llama-3.1-70B arms are `full/dense`, `internlm2-base-7b` is `full/dense`. They would extend the dense range and add nothing to the architecture contrast, which turns on whether attention-free and hybrid models are deficient. If a LATER claim wants the full 50 for a different reason -- a scale effect, say -- the dollars are available and the finding here does not wait on them.

### CORRECTION 2026-09-12: I published fabricated ranks

The first version of this file, its commit message and two messages to @malign
said the pair ranked **30 and 35 of 41**. The producer prints **35 and 39 of
47**. I wrote those three numbers from inference before the rank line existed --
I had seen a six-row "smallest |delta|" list that did not contain the pair, and
supplied specific ranks for it rather than reading them.

The conclusion is unchanged, which is not a defence: 35th and 39th of 47 fails
the prediction exactly as 30th and 35th of 41 would have. **A number that is
right about the direction and invented about the value is still invented**, and
it went into a README, the generated index and two peer messages before anyone
asked to reproduce it. It was caught only because @malign asked for the rule so
he could re-derive the count from his side.

`--min-cells` is also recorded here as a guard that has never fired: all 94
models carry 176-177 of the 177 usable cells, so no threshold between 1 and 50
changes the population.

### The registered prediction failed, and the failure is partly mine

It said: `Olmo-3` and `Olmo-Hybrid` share a 32-layer schedule with `full_attention` at identical positions and differ only in what fills the other 24 slots, so **if global attention carries the operation that pair should move LEAST on rhyme pull of any contrast in the fleet.**

Literally, it fails: their |delta| ranks 35th and 39th of 47 lineages.

**And the ranking it asked for is confounded.** |delta| tracks BASELINE -- `Tanuki-8B` has base pull 0.003 and `CT-LLM` 0.002, so their deltas are near zero for want of anything to lose, and they top the smallest-|delta| list. **Ranking by raw |delta| rewards having no rhyme pull at all.** That is a defect in how I wrote the pre-commitment, visible only once the data existed, and it is recorded here rather than quietly replaced.

### The post-hoc repair, labelled as one

Relative delta, for lineages whose base pull clears 0.01 so the ratio has a denominator:

    falcon-mamba-7b      none/ssm            +1.448   <- largest GAIN in the fleet
    gemma-2-9b           full/dense          +1.281
    Zamba2-7B            full+ssm/hybrid     -0.120
    OLMoE-1B-7B-0125     full/moe            -0.175
    Olmo-3-1025-7B       full+local/dense    -0.500
    Olmo-Hybrid-7B       full+linear/hybrid  -0.520
    Mistral-7B-v0.1      full/dense          -0.736
    glm-4-9b-hf          full/dense          -0.999

`Olmo-3` and `Olmo-Hybrid` sit adjacent at -0.500 and -0.520, which IS the prediction's substance -- hold global attention constant and the pair behaves alike. **But adjacency in a sorted list of 18 is weak evidence, and this statistic was chosen after seeing that the registered one was confounded.** It does not carry the weight the pre-commitment was meant to carry.

**The finding that does not depend on any of that**: most of the fleet LOSES rhyme pull under alignment, which reproduces the known erosion; the two largest relative GAINS are `falcon-mamba` and `gemma-2-9b`, an attention-free model and a dense transformer. Whatever alignment does to rhyme pull, it is not sorted by architecture.


**Does rhyme pull depend on attention?** The direct test, and the only instrument in this subject that does not read the output distribution's semantic profile.

The measurement code lives in `emergence/capacities/verse_capacity.py` and is reused rather than rewritten; what is NOT reused is that folder's ladder framing, which asks WHEN a capacity arrives and needs progress checkpoints nobody publishes for these architectures.

`SPEC_rhyme_pull.md` is the costing. `rhyme_smoke.py` and `tests/` are @malign's producer-shape gates and they pass.

## PRE-COMMITMENT, recorded 2026-09-11, before any rhyme_pull cell was measured



Written now because it costs nothing now and cannot be recovered later. If the `rhyme_pull` fleet runs and contrast 1 and contrast 2 disagree in sign again, two readings are available and **they are not distinguishable after the fact**: that the charge instrument was too blunt, and that there is no architecture effect to find. `norm_change` has already produced the first pattern on a second construct, so the ambiguity is not hypothetical.

The commitment, in advance:

1. **A second sign disagreement is not instrument failure.** It is not grounds for a third instrument.
2. **It is a BOUND, not a null.** It says any architecture effect is smaller than lineage-level variation at n=2 per contrast. It does not say architecture does not matter, and it must not be written up as if it did.
3. **The local/global reading above is the prediction under test**, in the form stated there: if global attention carries the operation, `rhyme_pull` should order these models the same way charge-selectivity did. It was recorded before the fleet, and a version of it arrived at after seeing rhyme results is a different claim with no standing. **AMENDED the same day, before any cell: this prediction requires BOTH ARMS and is not testable on bases alone.** Every number in this folder is a base->aligned delta -- `existence` regresses (p_aligned - p_base) on scene, `norm_change` regresses (aligned - base) on the base dose -- so they measure what alignment DOES. A base-only `rhyme_pull` measures a base CAPACITY. Ordering a capacity against a delta compares two constructs, which is this seat's most repeated defect and would have been undetectable once the numbers existed. All 12 lineages have aligned counterparts in the roster, so the delta design is available: `falcon-mamba-7b-instruct`, `recurrentgemma-9b-it`, `Olmo-Hybrid-Instruct-DPO-7B`, `rwkv-raven-7b`, and so on.

   **SHARPENED 2026-09-11, before any cell, by the config probe.** The prediction is about whether GLOBAL attention carries the operation, and contrast 1 holds global attention CONSTANT while varying only what fills the other 24 slots: `Olmo-3-1025-7B` and `Olmo-Hybrid-7B` share a 32-layer schedule with `full_attention` at exactly [3, 7, 11, 15, 19, 23, 27, 31] in both, and all 24 remaining layers go `sliding_attention -> linear_attention`. That is the cleanest available test of the hedge Weatherby makes at (155), because the mechanism his claim names is not varied at all while the local one is replaced wholesale. **If global attention is what carries the operation, this pair should move LEAST on rhyme pull of any contrast in the fleet** -- a prediction about the pair this campaign has been treating as its most sensitive control, and one that would be worthless recorded afterwards.

   The two questions are both real and they are not the same, which is why the amendment is an addition rather than a replacement. **Weatherby's claim is about the architecture**, so a base-only capacity read is the right test OF HIM. **The comparison with the charge instrument needs the delta.** The delta design answers both, because it contains the base arm.
4. **What would raise n** is the only route out, and it is models, not cells per model: more matched pairs where a lab swapped one attention mechanism and held the corpus. 178 poems per model does not make two models into more than two.

Subject to RH; the spend and the route are his call, and this is recorded rather than decided.
