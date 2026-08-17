# path_aggregation — does enumerating every token path close the CJK gap?

**No. NULL RESULT, and it redirects the question rather than answering it.**

`twp.score_words` encodes a named word ONCE and scores that single token path.
`twp.expand` discovers surfaces by walking a beam and accumulates `mass x term`
at EVERY path that lands on one. The docstring for `score_words` records the
consequence as a CJK-specific looseness:

    English (mpt, 'She was so angry...')   103/113 EXACT, max rel 4.5e-08
    CJK     (mpt, '那个自由的人选择了')      78/183 EXACT, max rel 4.9e-01

and attributes it to byte-level tokenizers reaching one CJK surface by several
routes. `twp_v4.score_words_paths` enumerates all of them and sums. This folder
asks whether that closes the gap.

## RUN

    python run.py --model HuggingFaceTB/SmolLM2-360M      # 80 CJK tokens
    python run.py --model Qwen/Qwen2.5-0.5B               # 25,587 CJK tokens
    python run.py --model <id> --limit 12                 # correctness, not cost

Both scorers are compared against `expand` **on the surfaces `expand` itself
found**. Scoring a word list chosen by anything else would compare two
instruments on a population neither produced.

## RESULT

Chinese prompt `那个自由的人选择了`, all surfaces, keys are `(surface, first_token)`:

    model                CJK toks   scorer              exact  under  over
    Qwen2.5-0.5B           25,587   score_words         147     13     0
                                    score_words_paths   147     13     0    <- identical
    SmolLM2-360M               80   score_words          33     57    66
                                    score_words_paths    33     54    69    <- 3 keys

English `She was so angry she wanted to`, SmolLM2-360M: **byte-identical**, 114
exact of 123, max rel 5.0e-08 for both.

**Path aggregation moves three keys on the most extreme byte-speller in the
roster and nothing at all on the others.** Enumeration is faithful -- every
enumerated path round-trips, `capped` is 0 -- so this is not a failure to find
the paths. The paths exist and carry no mass.

## SO WHAT DOES CAUSE THE CJK DISAGREEMENT

Unknown, and now separated from the hypothesis that was blocking it. What the
numbers rule out and rule in:

- **NOT multi-path spelling.** Both scorers disagree with `expand` by the SAME
  amount on SmolLM2 (33 of 162 exact for each), and a single-path scorer that
  cannot see alternate routes has the same error as one that sums all of them.
- **NOT a lower-bound problem, because the sign is wrong.** 66 of SmolLM2's zh
  keys are `score_words` ABOVE `expand`. A single path can only under-count the
  sum of all paths, so over-counting means the two instruments disagree about
  something other than which paths exist -- the boundary term or the beam, not
  the enumeration.
- **Scale is CJK-specific.** English is exact to 5.0e-08 on the same model and
  the same run, so it is not a generic arithmetic difference.

**RUN 2026-08-17, and it is the TERM.** Decomposing `p = mass x term` for every
disagreeing key on SmolLM2-360M, zh:

    surface  ntok   expand      score_words   mass       term_sw    term implied
                                                                    for expand
    他        2     0.0185310   0.0185310     0.037351   0.496135   0.496135
    一个       1     0.0326187   0.0320549     0.124183   0.258126   0.262666
    自己       4     0.0123311   0.0114837     0.019016   0.603897   0.648461
    我        2     0.0057578   0.0050940     0.018533   0.274865   0.310685

**`mass` is IDENTICAL on every row** -- the agreeing rows prove the decomposition,
since `expand / mass` reproduces the computed `term` exactly where they agree. So
the two instruments walk the same path with the same mass and disagree only about
`row[b].sum()`.

### the cache hypothesis is KILLED, and batching is real but too small

`_boundary_for` is one function called from both sites, so a different `b` could
only come from its two caches -- `bcache`/`intra_cache`, which `expand` fills
across a beam walk and `score_words` starts empty. **Tested and dead:** masks
computed with caches warmed by ten other surfaces are IDENTICAL to masks computed
fresh, 0 of 6 differing, same `b.sum()` to the token.

    surface   fresh b.sum   warmed b.sum   identical
    一个        48171         48171          yes      (6 of 6)

So the mask is the same and the term still differs, which leaves the ROW.
`next_dist` DOES depend on batch composition -- the same prefix scored alone and
inside a 251-prefix batch gives:

    一个   term alone 0.2584266   term in batch 0.2581256   rel 1.2e-03

Real, reproducible, and the same class as the prompt-cache non-identity that
keeps `USE_PROMPT_CACHE` off. **But it is an order of magnitude too small.** The
observed gap for `一个` is 0.258126 against expand's implied 0.262666, rel
1.8e-02. Batching contributes and does not explain.

### the live candidate, NOT tested

`expand` accumulates `words[(surf, t1)] += mass * term` at EVERY depth, with
`surf = clean_surface(tok.decode(pref).strip())`. **If a deeper prefix strips
back to the SAME surface** -- `一个 ` -> `一个` -- expand adds a second
contribution under one key. That inflates expand above a single-path scorer for a
ONE-TOKEN surface, which is the sign and the shape observed, and it is not
multi-path spelling of the word. Test it by instrumenting `_account` to record
`(surf, t1, depth)` and looking for a key credited at two depths.

## TWO HYPOTHESES DIED HERE, BOTH ON EVIDENCE

1. **multi-path spelling** -- enumerating every path moves 3 keys of 162
2. **depth-wise theta pruning** -- `_account` gates continuations on
   `mass >= theta` at every depth, which predicted the sign correctly and is
   still WRONG: zero disagreeing keys have an intermediate mass below theta.
   The check that appeared to confirm it was partly vacuous, because for a
   2-token path (the zh median) the only intermediate mass IS `P0[t1]`, which is
   >= theta by construction for any key `expand` emitted.

## WHAT THIS FOLDER DOES ESTABLISH

Enumeration itself is sound and cheap, and it is reusable whatever the CJK answer
turns out to be:

- `twp_v4.byte_table` detects a tokenizer's byte notation by VERIFICATION, not by
  guessing: both candidate notations are built, each must reassemble the probes,
  and exactly one must succeed. Over all 100 roster endpoints exactly one does --
  none passed both, none passed neither.
- `twp_v4.enumerate_paths` segments a target's UTF-8 BYTES, so it represents
  tokens that are half a character, which the character-keyed `_tok_index`
  cannot.
- Pruning is relative to each target's own best path and what it discards is
  SUMMED and returned as `pruned_mass`, an upper bound (mass never grows along a
  path), so the result is an interval rather than a point. Measured at
  3.7e-06 for SmolLM2 zh across 770 dropped paths.

## THE CLAIM THAT MOTIVATED THIS IS STILL UNTESTED ON ITS OWN MODEL

The 78/183 figure was measured on `gl198976/mpt-7b`. **mpt cannot be loaded
locally**: its bundled modelling code does `from transformers.models.bloom...
import _expand_mask`, removed in transformers 5.x, and `runners.py` refuses
remote code for MPT for this reason while `models.py` does not. So this folder
tests the HYPOTHESIS on two other models and finds it null; it does not reproduce
the original measurement. If mpt turns out to behave differently from both a
25,587-CJK-token tokenizer and an 80-CJK-token one, that would be the finding,
and it needs a box or a loader guard rather than another rewrite here.
