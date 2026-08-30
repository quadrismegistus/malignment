"""MPS returns out-of-range token indices when sampling. CPU does not.

    .venv/bin/python -u run.py                 reproduce on SmolLM2-360M
    .venv/bin/python -u run.py --model M       any cached checkpoint
    .venv/bin/python -u run.py --draws 2000    tighter rate estimate

## THE DEFECT

Sampling one token from `HuggingFaceTB/SmolLM2-360M-Instruct` after the prompt
`"It was a"`, with `top_k=50` so the permitted set has exactly fifty members:

    seed 159, mps:  ' nodded'     token 20341, RANK 29516, p = 1.17e-08
    seed 159, cpu:  ' beautiful'  a top-50 token

Five repeats each way, fully deterministic. **The filter is not the problem** --
the permitted set is fifty tokens and MPS returns index 29,516. It is the
sampling step returning an out-of-range index for particular RNG states.

Every filtering method leaks, at the same rate, the same token:

    top_p=0.95                 allowed 1521    1/400
    top_k=50                   allowed   50    1/400
    top_k=436                  allowed  436    1/400
    min_p=0.05                 allowed   51    1/400
    top_p=0.95 + top_k=1520    allowed 1521    1/400

**So the published workarounds do not work.** `top_k` and `min_p` are widely
recommended as MPS-safe alternatives to `top_p`; measured here they are not.

## THE MECHANISM: IT REQUIRES EXACT ZEROS

Model-free, 2,000 draws, a 49,152-long vector with fifty entries at 0.02:

    tail exactly 0.0      cpu 0/2000    mps 2/2000   (seeds 159, 622)
    tail at 1e-12         cpu 0/2000    mps 0/2000

**A nonzero floor fixes it.** The defect needs zero-probability entries in the
vector, and MPS then samples them.

That is why every filter leaks identically: `top_k`, `top_p` and `min_p` all set
filtered logits to `-inf`, which softmaxes to EXACTLY zero. And it is why
`top_p=1.0, top_k=0` is SAFE -- no filtering, no zeros, no defect. The earlier
claim in this file that all MPS sampling is affected was wrong; only filtered
sampling is.

## WHY IT MATTERS AT LENGTH

At ~1/400 per draw, a generation of N tokens contains at least one impossible
token with probability `1 - (1-0.0025)^N`:

    N =  256    47%
    N =  600    78%
    N = 1900    99%

Next-token work is essentially unaffected -- one draw, 0.25%. **Long-form
FILTERED generation is essentially always affected.** Unfiltered generation is
not affected at all.

## THE FIX

Either sample on CPU -- one draw per step, negligible against the forward pass --
or floor the distribution before sampling rather than zeroing it. `top_p=1.0,
top_k=0` is also safe but is unusable for long-form for a different reason: it
samples the true tail, 4 draws in 300 beyond rank 5000.

## PRIOR ART, AND HOW THIS DIFFERS

    pytorch#92752   torch.multinomial on MPS returns [-9223372036854775808].
                    Same op, same backend, CLOSED -- and this reproduces on
                    torch 2.13.0. Theirs returns INT64_MIN and faults on
                    indexing; this returns a VALID vocabulary index that
                    decodes to a real word, so it is silent.
    nanoGPT#458     MPS on torch 2.2.x generates only token 0, fine on 2.1.x,
                    root cause never found. Same symptom family.
    transformers#44247  NOT this. SDPA producing inf/nan so multinomial raises,
                    under non-float32 + non-causal + query seq <= 8 + key seq
                    >= 1024. Measured here in float32, causal, 4-token prompt,
                    with a finite vector summing to 1.000033.

## A CORRECTION WORTH KEEPING

An earlier version of this file claimed ALL MPS sampling is affected, on the
grounds that validating `generate()` against `torch.multinomial` on the SAME
device could not detect the defect. The first half was wrong -- the exact-zero
requirement means unfiltered sampling is genuinely clean, so that agreement was
real and not an artifact of shared machinery.

The second half stands as a rule anyway: a backend cannot be its own referee,
and the comparison has to be CPU against MPS at matched seeds. It was the right
principle applied to a case that did not need it, used to overturn a correct
result.

## WHAT IS AND IS NOT AFFECTED IN THIS CAMPAIGN

    AFFECTED      anything calling generate() with do_sample=True on mps:
                  malignment.generate, experiments/national_story, and any
                  local generation for slot or passage work.
    NOT AFFECTED  forward-pass work -- twp next-word probabilities, the logit
                  lens (readout_share), charge's stored masses, movement. No
                  sampling, no RNG, no multinomial.

## WHAT THIS DOES NOT EXPLAIN

Long aligned generations degenerate into token salad far more often than base
ones (17 of 24 against 0 of 20 at top_p=1.0). **That asymmetry is probably NOT
this bug.** The corruption hits both arms -- `resurrectionists` intrusions are
visible in base and aligned text alike -- and both recover from a single bad
token. The likelier cause is that an aligned model completes a story and then
overruns its own ending, while a base model never has an ending to overrun: the
only clean aligned samples are the ones that hit EOS early, at 445 and 747
words. Separating the two needs a correct sampler, which is why it is named here
rather than answered.
"""

import argparse
import sys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM2-360M-Instruct")
    ap.add_argument("--prompt", default="It was a")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--top-k", type=int, default=50)
    a = ap.parse_args(argv)

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    tok = AutoTokenizer.from_pretrained(a.model)
    out = {}
    for dev in ("cpu", "mps"):
        if dev == "mps" and not torch.backends.mps.is_available():
            continue
        m = AutoModelForCausalLM.from_pretrained(
            a.model, dtype=torch.float32).to(dev).eval()
        enc = tok(a.prompt, return_tensors="pt").to(dev)
        with torch.no_grad():
            lg = m(**enc).logits[0, -1, :].float()
        p = torch.softmax(lg, -1)
        sp, si = torch.sort(p, descending=True)
        #: the permitted set is EXACT under top_k -- fifty ids, no cumulative
        #: threshold to argue about. Any draw outside it is unambiguous.
        allowed = set(si[:a.top_k].tolist())
        rank = {int(t): r for r, t in enumerate(si.tolist())}
        bad = []
        for i in range(a.draws):
            torch.manual_seed(i)
            o = m.generate(**enc, do_sample=True, temperature=1.0,
                           top_k=a.top_k, max_new_tokens=1,
                           pad_token_id=tok.eos_token_id)
            t = int(o[0, -1])
            if t not in allowed:
                bad.append((i, t, rank[t], float(p[t])))
        out[dev] = bad
        print("%-4s  %d draws, top_k=%d  ->  %d outside the permitted set"
              % (dev, a.draws, a.top_k, len(bad)))
        for i, t, r, pv in bad[:5]:
            print("        seed %-5d %-14r rank %-7d p=%.2e"
                  % (i, tok.decode([t]), r, pv))
        del m
    if "cpu" in out and "mps" in out:
        print()
        print("VERDICT: cpu %d / %d, mps %d / %d"
              % (len(out["cpu"]), a.draws, len(out["mps"]), a.draws))
        if out["mps"] and not out["cpu"]:
            r = len(out["mps"]) / a.draws
            print("  mps rate %.4f per draw -> P(at least one) at N tokens:" % r)
            for n in (256, 600, 1900):
                print("     N=%-5d %.0f%%" % (n, 100 * (1 - (1 - r) ** n)))


if __name__ == "__main__":
    main()
