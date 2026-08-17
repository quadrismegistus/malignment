# term_noise — how much of a word's `term` is diffuse boundary noise?

`p(word) = mass x term`, with `term = row[b].sum()` over every boundary token.
**This measurement decided v4's scope**, because `term` multiplies into every
stored `p` and therefore sits inside every `dP` any consumer weights by.

    python run.py --models gl198976/mpt-7b --n 25 --write

## RESULT — 25 prompts, sub-theta floor 0.001

    model                          words   tail share   median term
    HuggingFaceTB/SmolLM3-3B-Base    2384      9.5%   0.9936
    Qwen/Qwen2.5-7B                  2389      9.0%   0.9954

**`term` IS NEAR-SATURATED FOR REAL WORDS and therefore carries almost no
information about them.** After a complete word essentially anything is a
boundary, so the median sits at ~0.99 and the ~9% that comes from the diffuse
sub-theta tail is near-uniform across words.

It is fractional only where a surface genuinely wants to continue — fragments.
`murm` scores 0.534 on SmolLM3 because the model wants `murmured`. **Fragments
are where it is VISIBLE, not where it happens.**

## WHAT IT RULED OUT

`term_floor` — discarding the diffuse remainder — was the v4 candidate this
measured for, and it is DEAD. The two arms of one pair lose different shares
(7.7% vs 3.6%), so it does not cancel in `dP`; `dN` moves 15.4%; and the loss is
TREATMENT-CORRELATED, the peakier aligned arm losing less. A correction that
tracks the treatment is not a correction.

## A WITHDRAWN NUMBER THAT USED TO BE IN THIS FILE

`run.py`'s docstring said `term` sums over **48,197** boundary tokens for a Latin
surface. That figure was measured on a CJK surface and is withdrawn ([6390]). For
a LATIN surface mpt marks 28,823 space-initial, 1,247 punct, 155 empty and 2 CJK.
The saturation result does not depend on it.
