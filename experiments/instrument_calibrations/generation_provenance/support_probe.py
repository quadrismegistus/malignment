"""Can counting distinct outputs detect nucleus truncation? Validate before spending.

    python .../support_probe.py --model Qwen/Qwen2.5-7B-Instruct

litmod's instrument for the vendor probe: truncation's signature is not that
outputs SHIFT, it is that outputs become IMPOSSIBLE -- a token past the nucleus
boundary has probability exactly zero, not merely low. So sample a high-entropy
continuation n times and count DISTINCT outputs. Wide support means top_p is 1.0;
narrow support means it truncates.

That replaces an acceptance-of-the-null ("the distributions do not differ, so the
default is 1.0"), which has decent power against a default of 0.7 and almost none
against 0.95 -- and 0.95 is exactly where a vendor default lands.

## THIS FILE SPENDS NOTHING AND ASKS WHETHER THE INSTRUMENT WORKS AT ALL

The vendor probe is metered and its whole value rests on the test being able to
separate `top_p=1.0` from `top_p=0.95`. That is checkable for free on a local
checkpoint, where top_p is OURS to set and the answer is known.

**And locally we can do better than check it -- we can compute the ground truth.**
`next_token` returns the full next-token distribution, so the EXACT nucleus size
at any top_p is a sort and a cumulative sum. Running both gives:

    exact      how many tokens the nucleus actually contains at each top_p
    sampled    how many distinct ones n draws actually reveal

The gap between them IS the instrument's sensitivity. If the exact nucleus
collapses from 1.0 to 0.95 but n=100 sampling cannot see the collapse, the test
cannot answer the vendor question and the metered run should not happen.

## WHY THE PROMPT MATTERS AND WHICH ONE IS USED

A low-entropy prompt saturates: if the model is nearly certain of the next token,
support is 1 at every top_p and the test reads "total truncation everywhere".
The prompt below is chosen for a wide, near-flat continuation set, and its
entropy is REPORTED -- a support number without the entropy beside it cannot be
told apart from a ceiling effect.

Temperature is held at 1.0 throughout. At temperature 0 every arm returns one
type and the test reads as total truncation for a reason that has nothing to do
with top_p.
"""

import argparse, collections, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

TOP_PS = (1.0, 0.95, 0.9, 0.7)
#: a wide, near-flat continuation set. Reported entropy says whether it is.
PROMPT = "She wanted to"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--prompt", default=PROMPT)
    ap.add_argument("--seed", type=int, default=20260821)
    a = ap.parse_args(argv)
    import torch
    from malignment import Checkpoint
    from malignment.generate import encode, render

    ck = Checkpoint(a.model)
    ld = ck.load()
    print("%s | prompt %r | n=%d, temperature 1.0" % (a.model, a.prompt, a.n))

    # ---- EXACT: the model's own next-token distribution
    text_in, _ = render(ld, a.prompt, template=None)
    enc = encode(ld, text_in, False)
    with torch.no_grad():
        logits = ld.model(**enc).logits[0, -1].float()
    p = torch.softmax(logits, dim=-1)
    srt, _ = torch.sort(p, descending=True)
    cum = torch.cumsum(srt, dim=0)
    ent = float(-(p * torch.log2(p.clamp_min(1e-12))).sum())
    print("  next-token entropy %.2f bits over a vocab of %d"
          % (ent, p.shape[0]))
    print("  (a low-entropy prompt saturates the test; this is the check on that)")

    exact = {}
    for tp in TOP_PS:
        #: nucleus = smallest set whose cumulative mass reaches top_p
        exact[tp] = int((cum < tp).sum().item()) + 1

    # ---- SAMPLED: what n draws of one token actually reveal
    print("\n  %-7s %10s %10s %9s   %s" % ("top_p", "exact", "sampled", "of n",
                                           "vs top_p=1.0"))
    sampled = {}
    for tp in TOP_PS:
        seen = collections.Counter()
        for i in range(a.n):
            torch.manual_seed(a.seed + i)
            with torch.no_grad():
                g = ld.model.generate(**enc, do_sample=True, temperature=1.0,
                                      top_p=tp, max_new_tokens=1,
                                      pad_token_id=ld.tok.eos_token_id)
            seen[int(g[0][-1])] += 1
        sampled[tp] = len(seen)
        d_ex = exact[tp] / exact[1.0]
        d_sa = sampled[tp] / sampled[1.0]
        print("  %-7s %10d %10d %9d   exact %.0f%% of baseline, sampled %.0f%%"
              % (tp, exact[tp], sampled[tp], a.n, 100 * d_ex, 100 * d_sa))

    # ---- THE VERDICT THE VENDOR PROBE DEPENDS ON
    print("\n  CAN n=%d SAMPLING SEE THE 1.0 -> 0.95 STEP?" % a.n)
    e1, e95 = exact[1.0], exact[0.95]
    s1, s95 = sampled[1.0], sampled[0.95]
    print("    exact nucleus   %d -> %d  (%.0f%% of the tokens removed)"
          % (e1, e95, 100 * (1 - e95 / e1)))
    print("    sampled support %d -> %d  (%+d types)" % (s1, s95, s95 - s1))
    #: the honest verdict, stated either way. A test that cannot separate the
    #: values that matter must not be bought, and the reason it fails is the
    #: same either way: n draws reveal only the head of a wide distribution.
    if s95 < s1 * 0.8:
        print("    -> the step IS visible at this n. The instrument can carry")
        print("       the vendor question at 0.95.")
    else:
        print("    -> NOT visible at this n. %d draws of a %d-token nucleus"
              % (a.n, e1))
        print("       reveal mostly the head, and the sliver 0.95 removes lives")
        print("       in the tail those draws never reach. A null from this test")
        print("       on a vendor would mean 'n was too small', not 'default is")
        print("       1.0' -- do not buy it in this form.")


if __name__ == "__main__":
    main()
