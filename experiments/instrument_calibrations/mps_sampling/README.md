---
id: mps_sampling
kind: calibration
question: "Does MPS sample tokens the filter forbade, and under what conditions?"
status: "RUN. It does, at ~1/400 per draw, and ONLY when the distribution contains exact zeros -- which every filter creates. Unfiltered sampling is clean."
headline: "MPS returns out-of-range token indices when sampling. CPU does not. The defect needs EXACT ZEROS, so it is a property of FILTERED sampling and not of MPS sampling as such."
grain: apparatus
---

# mps_sampling

**MPS returns out-of-range token indices when sampling. CPU does not. The defect needs EXACT ZEROS, so it is a property of FILTERED sampling and not of MPS sampling as such.**

This folder had no README until 2026-09-02 and the whole finding lived in `run.py`'s docstring, which is where the campaign's rule says a finding must not live. Nothing here is new; it is the docstring given a file a reader can find.

    seed 159, mps:  ' nodded'     token 20341, RANK 29516, p = 1.17e-08
    seed 159, cpu:  ' beautiful'  a top-50 token

`HuggingFaceTB/SmolLM2-360M-Instruct`, prompt `"It was a"`, `top_k=50` so the permitted set has exactly fifty members. Five repeats each way, fully deterministic.

## Why it is a calibration and not a question about alignment

It says nothing about what alignment does. It measures the apparatus every generation experiment runs on, and it sets a hard constraint they all inherit -- which is the same kind as `displacement_reference`, and the reason it sits here rather than at top level.

## THE MECHANISM, WHICH IS WHAT MAKES THE RULE PRECISE

Model-free, 2,000 draws, a 49,152-long vector with fifty entries at 0.02:

    tail exactly 0.0      cpu 0/2000    mps 2/2000   (seeds 159, 622)
    tail at 1e-12         cpu 0/2000    mps 0/2000

**A nonzero floor fixes it.** So every filter leaks identically -- `top_k`, `top_p` and `min_p` all set filtered logits to `-inf`, which softmaxes to exactly zero:

    top_p=0.95                 allowed 1521    1/400
    top_k=50                   allowed   50    1/400
    top_k=436                  allowed  436    1/400
    min_p=0.05                 allowed   51    1/400
    top_p=0.95 + top_k=1520    allowed 1521    1/400

**The published workarounds do not work.** `top_k` and `min_p` are widely recommended as MPS-safe alternatives to `top_p`; measured here they are not, at the same rate and on the same token.

## WHY IT MATTERS AT LENGTH AND NOT AT ONE TOKEN

`1 - (1-0.0025)^N`:

    N =  256    47%
    N =  600    78%
    N = 1900    99%

Next-token work is essentially unaffected. **Long-form filtered generation is essentially always affected.**

    AFFECTED      anything calling generate() with do_sample=True on mps:
                  malignment.generate, experiments/national_story, and any
                  local generation for slot or passage work
    NOT AFFECTED  forward-pass work -- twp next-word probabilities, the logit
                  lens (readout_share), charge's stored masses, movement.
                  No sampling, no RNG, no multinomial.

## The fix

Sample on CPU -- one draw per step, negligible against the forward pass -- or floor the distribution before sampling rather than zeroing it. `top_p=1.0, top_k=0` is also safe and is unusable for long-form for a different reason: it samples the true tail, 4 draws in 300 beyond rank 5000. That is why `../story_decoder` could not be run locally.

## Prior art, and how this differs

    pytorch#92752   torch.multinomial on MPS returns [-9223372036854775808].
                    Same op, same backend, CLOSED -- and this reproduces on
                    torch 2.13.0. Theirs returns INT64_MIN and faults on
                    indexing; this returns a VALID vocabulary index that
                    decodes to a real word, so IT IS SILENT.
    nanoGPT#458     MPS on torch 2.2.x generates only token 0, fine on 2.1.x,
                    root cause never found. Same symptom family.
    transformers#44247  NOT this. SDPA producing inf/nan so multinomial raises.
                    Measured here in float32, causal, 4-token prompt, with a
                    finite vector summing to 1.000033.

## A correction worth keeping

An earlier version claimed ALL MPS sampling is affected, on the grounds that validating `generate()` against `torch.multinomial` on the SAME device cannot detect the defect. **The first half was wrong** -- the exact-zero requirement means unfiltered sampling is genuinely clean, so that agreement was real and not an artifact of shared machinery.

The second half stands as a rule anyway: a backend cannot be its own referee, and the comparison has to be CPU against MPS at matched seeds. It was the right principle applied to a case that did not need it, and used to overturn a correct result.

## What this does NOT explain, and the temptation to let it

Long aligned generations degenerate into token salad far more often than base ones (17 of 24 against 0 of 20 at `top_p=1.0`). **That asymmetry is probably not this bug.** The corruption hits both arms -- `resurrectionists` intrusions are visible in base and aligned text alike -- and both recover from a single bad token. The likelier cause is that an aligned model completes a story and then overruns its own ending, while a base model never has an ending to overrun: the only clean aligned samples are the ones that hit EOS early, at 445 and 747 words.

Separating the two needs a correct sampler. Named here rather than answered, because a known defect in the neighbourhood of an unexplained asymmetry is exactly the thing that gets credited with it.

## The second MPS defect

There is another, and neither folder cross-referenced the other until now: **MPS corrupts embeddings of short Chinese strings**, recorded in `../frame_prefill/README.md` and `../../displacement/readout_share/README.md`. Same backend, different op, same rule -- CPU is the referee.
