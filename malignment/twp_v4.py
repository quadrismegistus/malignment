#!/usr/bin/env python
"""twp_v4.py — the word-boundary rule, proposed changes, each one switchable.

    from malignment import twp_v4 as V4

    V4.expand4(model, tok, prompt, dev, bmask, cjk=cjk)          # all rules off == v3
    V4.expand4(..., rules=V4.Rules(term_floor=0.001))            # one rule on
    V4.compare(model, tok, prompt, dev, bmask, cjk, rules)       # what moved, and by how much

## WHY A SEPARATE MODULE AND NOT A BRANCH IN `expand`

`twp.expand` is `RULE_VERSION 3`, `dict_sha b16011275c42955c`, and 984,857 stored
cells were written by it with conservation exactly 1.000000. **v3 must stay
byte-identical while v4 is unstable**, and the cheapest way to guarantee that is
to not touch it: this module IMPORTS `_account`'s pieces rather than forking
them, so a v3 fix reaches v4 automatically and a v4 experiment cannot reach v3.

Tagged `pre-rule-v4` before any of this existed.

## EVERY RULE IS OFF BY DEFAULT AND EVERY RULE IS SEPARATE

`Rules()` with no arguments must reproduce v3 exactly — asserted by
`compare()` returning zero movement, which is the first thing to run after any
edit here. **A bundle of four changes that collectively shift every number is
unattributable**; the point of this file is that each can be switched on alone
and its effect measured against the same cell.

## THE FOUR CANDIDATES, AND WHAT IS ACTUALLY KNOWN ABOUT EACH

**1. `term_floor` — the one the measurement was for.**
`p = mass x term`, `term = row[b].sum()` over ~30k-48k boundary tokens. Measured
on `gl198976/mpt-7b`, 25 prompts, 2,375 words:

    median term                                   0.9993
    mass-weighted share of p from sub-theta        8.8%
    median tail fraction of term                   6.7%   (top-20 by p: 11.7%)
    boundary tokens per word 30,533, sub-floor    30,489

**`term` is NEAR-SATURATED for real words and therefore carries almost no
information about them** — after "night", essentially anything is a boundary. It
is fractional only where a surface genuinely wants to continue, i.e. fragments
(`murm` 0.534, wanting `ured`). So the honest v4 question is not "correct a
bias" but "should a factor that is 0.999 for every real word be in the product".
A floor discards the diffuse remainder; the ~8.8% it removes is near-uniform, so
it should largely cancel in `dP` and entirely in signs — **which is a prediction
this module exists to test, not an assurance.**

**2. `enumerate_paths` — the CJK gap.**
`expand` accumulates at every depth reaching a surface; `twp.score_words` scores
one path and so is a LOWER BOUND: English matches to 4.5e-08, CJK to only ~0.5,
because byte-level tokenizers reach one CJK surface many ways (`什么` ->
['?','?','么']). Affects `score_words`, not `expand` — listed here so the union
top-up and the rule change stay one conversation.

**3. `count_paths` — `n_paths` is misnamed.**
It counts distinct FIRST TOKENS, because ingest folds jsonl rows by `word` and a
row is already one `(word, t1)`. I misread it twice while diagnosing (2), and
dario confirmed nothing of theirs reads it ([6388]) — so it can be renamed now
at zero cost to consumers, which will not be true later.

**4. `fragment_gate` — NOT RECOMMENDED, kept so it can be refuted with numbers.**
Suppressing `murm`/`spapers` needs a lexicon, which would also drop legitimate
rare words, names and neologisms from a full-vocabulary instrument. And after (1)
it may be moot: fragments are where `term` is fractional, so a floor may remove
them without a wordlist. **Try (1) before anyone builds a gate.**
"""
import dataclasses
import os
import sys

import numpy as np
import torch

from . import twp as T

RULE_VERSION = 4


@dataclasses.dataclass(frozen=True)
class Rules:
    """One switch per proposed change. All-default MUST reproduce v3.

    `frozen` so a rule set cannot be mutated after a run has been labelled with
    it -- the stamp-declares-not-applies failure, where a record says which rule
    made it and the rule changed underneath.
    """
    #: Discard boundary tokens below this from `term`. 0.0 == v3 (keep all).
    term_floor: float = 0.0
    #: Renormalise `term` over the kept boundary mass. Only meaningful with a
    #: floor; asserts the discarded tail was noise rather than absent mass.
    term_renorm: bool = False
    #: Sum over ALL token paths reaching a surface, not the canonical one.
    enumerate_paths: bool = False
    #: Treat a hyphen FOLLOWED BY AN ALPHANUMERIC as intra-word, so
    #: `self` + `-motivated` is one word. v3 unmasks 7 hand-listed English
    #: contractions (`'s 't 'm 're 'll 've 'd`) and nothing else, so a hyphen is
    #: terminal like `!` -- see the module docstring for why that is not merely
    #: wrong but wrong DIFFERENTIALLY.
    hyphen_intra: bool = False
    #: Divide by the boundary mass at depth 0 -- Pimentel & Meister Thm 2's
    #: DENOMINATOR, which v3 omits. See `expand4`.
    apply_z: bool = False

    def is_v3(self):
        return (self.term_floor == 0.0 and not self.term_renorm
                and not self.enumerate_paths and not self.hyphen_intra
                and not self.apply_z)

    def label(self):
        if self.is_v3():
            return "v3"
        bits = []
        if self.term_floor:
            bits.append("floor=%g%s" % (self.term_floor, "+renorm" if self.term_renorm else ""))
        if self.enumerate_paths:
            bits.append("paths")
        if self.hyphen_intra:
            bits.append("hyphen")
        if self.apply_z:
            bits.append("Z")
        return "v4[" + ",".join(bits) + "]"


_HYPH = {}


def hyphen_intra_ids(tok):
    """Vocab ids that CONTINUE a word across a hyphen: `-motivated`, `-based`.

    **DERIVED FROM THE VOCABULARY, NOT HAND-LISTED**, which is the point. v3's
    intra-word set is 7 English contractions typed out by a person, so it covers
    `don't` and nothing else -- not `self-motivated`, not French `l'`, not any
    language nobody thought of. This is a predicate over the actual vocabulary,
    so it is correct for whatever tokenizer it is handed.

    **NO LEADING SPACE.** ` -motivated` starts a new word; `-motivated` continues
    one. And the character after the hyphen must be alphanumeric, so `--` and a
    bare `-` stay terminal: `listen--I` still cuts at the dashes, which is right.

    Counted across the roster's tokenizers, and the spread is the defect:

        mpt-7b, pythia-6.9b       50,254 vocab        0 such ids
        Llama-3.1-8B, SmolLM3    128,000 vocab    ~1,747
        Qwen2.5-7B               151,643 vocab     1,746

    **So v3 measures the same English word differently depending on vocabulary
    size** -- and vocabulary size tracks model recency, which tracks alignment
    sophistication. A per-tokenizer inconsistency aligned with the treatment axis
    is the `T`-as-mediator hazard again, one level down.
    """
    key = id(tok)
    if key not in _HYPH:
        import re
        pat = re.compile(r"^-[A-Za-z0-9]")
        ids = [i for i in range(tok.vocab_size)
               if pat.match(tok.decode([i]) or "")]
        _HYPH[key] = np.array(ids, dtype=np.int64)
    return _HYPH[key]


@torch.no_grad()
def expand4(model, tok, prompt, dev, bmask, cjk=None, theta=T.THETA,
            bos_policy="inherited", rules=None):
    """`twp.expand`'s beam with the v4 switches. Returns (words, residual, meta).

    Mirrors v3's loop deliberately rather than calling it, because the changes
    are INSIDE the loop -- but every helper (`_prompt_ids`, `next_dist`,
    `clean_surface`, `_boundary_for`, `is_mojibake`) is v3's, so the rule this
    diverges from is the rule the store was written with.
    """
    rules = rules or Rules()
    pids, _rs, _rid = T._prompt_ids(tok, prompt, bos_policy)
    lg = model(torch.tensor([pids], device=dev)).logits[0, -1, :].float()
    P0 = torch.softmax(lg, -1).cpu().numpy()
    del lg
    sel = np.flatnonzero(P0 >= theta)
    live = [((int(t),), float(P0[t]), int(t)) for t in sel]
    words, res = {}, dict(tail=float(1.0 - P0[sel].sum()), drop=0.0, mojibake=0.0)
    #: v4 accounts the mass a floor discards to its OWN channel. Folding it into
    #: `drop` would make it indistinguishable from sub-theta continuation loss,
    #: and conservation would still read 1.0 while meaning something different.
    res["term_floored"] = 0.0
    paths, bcache, intra = {}, {}, {}
    for _ in range(T.MAX_DEPTH):
        if not live:
            break
        dist = T.next_dist(model, tok, pids, [p for p, _, _ in live], dev)
        nxt = []
        for (pref, mass, t1), row in zip(live, dist):
            surf = T.clean_surface(tok.decode(list(pref)).strip())
            b = T._boundary_for(surf, bmask, cjk, bcache, intra)
            #: Applied AFTER v3's rule and only where v3 itself unmasks the
            #: contractions -- an alphanumeric-final surface. `100` + `-5` and
            #: `self` + `-motivated` continue; `listen` + `--` does not.
            if rules.hyphen_intra and surf and surf[-1].isalnum():
                hy = hyphen_intra_ids(tok)
                if len(hy):
                    b = b.copy()
                    b[hy] = False
            bm = row[b]
            if rules.term_floor > 0.0:
                keep = bm >= rules.term_floor
                term = float(bm[keep].sum())
                floored = float(bm[~keep].sum())
                if rules.term_renorm and term > 0:
                    term = term / (term + floored) * float(bm.sum())
                    floored = float(bm.sum()) - term
            else:
                term, floored = float(bm.sum()), 0.0
            if surf and not T.is_mojibake(surf):
                key = (surf, t1)
                words[key] = words.get(key, 0.0) + mass * term
                paths[key] = paths.get(key, 0) + 1
                res["term_floored"] += mass * floored
            elif surf:
                res["mojibake"] += mass * (term + floored)
            else:
                res["drop"] += mass * (term + floored)
            cont = np.flatnonzero(~b)
            m2 = mass * row[cont]
            k2 = m2 >= theta
            for t, mm in zip(cont[k2], m2[k2]):
                nxt.append(((*pref, int(t)), float(mm), t1))
            res["drop"] += float(m2[~k2].sum())
        live = nxt
    res["open"] = float(sum(m for _, m, _ in live))
    #: **Z: PIMENTEL & MEISTER THM 2's DENOMINATOR, WHICH v3 OMITS.**
    #: arXiv:2406.14561, and independently Oh & Schuler arXiv:2406.10851 as
    #: "whitespace-trailing decoding". For a bow-marking tokenizer the word
    #: probability is
    #:
    #:     p(w | c) = PROD p(tokens)  x  SUM_bow p(s | c o w)
    #:                                   -------------------
    #:                                   SUM_bow p(s | c)
    #:
    #: v3 computes `mass x term`, which is the NUMERATOR exactly. `Z` is the
    #: same boundary sum evaluated at depth 0 -- before the word -- and it is
    #: what makes the quantity `p(w | c, a word starts here)` rather than
    #: `p(w AND a boundary follows | c)`.
    #:
    #: **EOS is in the bow set** on P&M's definition (`S_bow u {EOS}`): a word
    #: may end by the sequence ending. v3's static mask does not include it.
    #:
    #: Measured on our prompt shapes: Z = 0.99788..0.99948, so -log Z is
    #: 0.0005..0.0021 nats and the correction is ~0.1%. **It is applied because
    #: it is free and correct, NOT because it changes anything** -- our prompts
    #: end at clean word boundaries, which is exactly the case where Z -> 1. A
    #: prompt ending mid-word or with a trailing space is the case where Z
    #: departs from 1, and that is also the prompt-boundary problem
    #: (Hayase et al. arXiv:2506.14123), which this does not fix.
    zb = bmask.copy()
    eos = getattr(tok, "eos_token_id", None)
    if eos is not None and 0 <= int(eos) < len(zb):
        zb[int(eos)] = True
    Z = float(P0[zb].sum())
    #: **REFUSED FOR CJK, AND THE MEASUREMENT IS WHY.** P&M scope Theorem 2 to
    #: BOW-MARKING tokenizers -- a new word signalled by a leading space. CJK is
    #: not bow-marking, so the depth-0 boundary set captures almost none of the
    #: mass and `Z` measures "how likely is a space next", which after Chinese
    #: text is correctly ~2%. Dividing by it inflates everything ~50x:
    #:
    #:     'She was so angry she wanted to'   Z=0.997966   sum +0.204%
    #:     'The mob dragged him into...'      Z=0.999481   sum +0.052%
    #:     '那个自由的人选择了'                  Z=0.019630   sum 0.355 -> 18.101
    #:
    #: **18.1 is Oh & Schuler Thm 1's violation caused BY the correction** --
    #: word probabilities summing far past one. So this is undefined for CJK
    #: rather than inaccurate, and it refuses instead of guessing a CJK bow set.
    #: 457 of the roster's prompts are `language='zh'`.
    if rules.apply_z:
        if T.is_cjk(prompt):
            raise ValueError(
                "apply_z is undefined for a CJK prompt: Pimentel & Meister Thm 2 "
                "assumes a bow-marking tokenizer, and Z=%.4f here measures the "
                "probability of a SPACE, not of a word boundary. Dividing by it "
                "would inflate this cell ~%.0fx." % (Z, 1.0 / max(Z, 1e-9)))
        if Z > 0:
            words = {k: v / Z for k, v in words.items()}
    meta = {"rule_version": RULE_VERSION, "rules": dataclasses.asdict(rules),
            "Z": Z,
            "label": rules.label(),
            #: THE HONEST FIELD NAME. v3's `n_paths` counts distinct first
            #: tokens; this counts what the name says.
            "n_paths_true": dict(paths)}
    return words, res, meta


@torch.no_grad()
def score_words_paths(model, tok, prompt, targets, dev, bmask, cjk=None,
                      bos_policy="inherited", theta=T.THETA):
    """Score named words over ALL token paths, not the canonical one. -> same shape as `twp.score_words`

    **`twp.score_words` IS A LOWER BOUND AND CJK IS WHERE THE BOUND IS LOOSE.**
    It encodes each target once and scores that path. Measured against `expand`
    on the same device:

        English (mpt, 'She was so angry...')   103/113 EXACT, max rel 4.5e-08
        CJK     (mpt, '那个自由的人选择了')      78/183 EXACT, max rel 4.9e-01

    Byte-level tokenizers reach one CJK surface many ways -- mpt encodes `什么`
    as `['?','?','么']` -- and `expand` accumulates every path that lands on a
    surface while a single encode captures one. Hence ~0.5.

    **AND `n_paths` COULD NOT HAVE TOLD ME.** It counts distinct FIRST TOKENS
    (ingest folds jsonl rows by `word`, and a row is already one `(word, t1)`),
    so `你` is a single token with `n_paths = 1` and still diverges 2.3x. I read
    that field as a path count twice while diagnosing this.

    ## HOW: A BEAM CONSTRAINED TO THE TARGETS

    Enumerating every tokenization of a string is combinatorial, so this does not
    enumerate -- it runs `expand`'s own beam and prunes to paths whose decoded
    surface is still a viable PREFIX of some target. Cost is bounded by the beam,
    not by the number of tokenizations, and every path `expand` would have taken
    to a target is taken here.

    Accumulates on `(surface, first_token)`, which is `expand`'s key, so the
    result is comparable to a stored row rather than merely similar to one.

    ## FAILURE -- DO NOT USE. THREE ATTEMPTS, THREE DEFECTS, KEPT AS A RECORD

        CJK      score_words 183 matched,  94 exact, max_rel 6.6e-01
                 paths_v4    106 matched,  55 exact, max_rel 9.0e+00
        English  score_words 113 matched, 103 exact, max_rel 4.5e-08
                 paths_v4      0 matched                       <- finds NOTHING

    **1. Quadratic.** Viability tested by decoding every continuation token for
    every live prefix at every depth: O(live x vocab) decodes. Never returned.

    **2. Unbounded.** Dropping theta was deliberate -- the words this exists to
    find are sub-theta -- but `mm > 0.0` prunes nothing, so the frontier
    multiplied by the branching factor at every depth. Also never returned.
    Fixed with `PATH_FLOOR`/`PATH_WIDTH`, which are sound and stay.

    **3. The leading space.** Candidates are looked up as `rest[:k]` taken from
    the target, so `kill` searches for `k`, `ki`, `kil`, `kill` -- and the token
    is `" kill"`. **The bow convention, which `twp.score_words` handles
    explicitly with `cands = ["", " "]` twenty lines away and which I had got
    right two hours earlier.** CJK partly works only because CJK has no leading
    space, which is why the English zero is the informative half and the CJK
    9x is a symptom of the same miss.

    **Stopped here rather than attempting a fourth fix in the same sitting.**
    Three failures on one function, the last of them a concept already solved in
    the neighbouring function, is a signal about the author's state rather than
    the problem's difficulty. `twp.score_words` remains correct-and-bounded:
    exact in English, a documented ~0.5 lower bound in CJK.

    A rewrite should start from `score_words`'s verified separator handling and
    add path aggregation to THAT, rather than rebuild the walk from scratch.
    """
    raise NotImplementedError(
        "score_words_paths is BROKEN -- see the docstring's FAILURE section. It "
        "finds 0 of 113 English targets because candidate lookup ignores the "
        "leading-space (bow) convention. Use twp.score_words, which is a "
        "documented lower bound, until this is rewritten.")

    #: **CANDIDATES COME FROM THE TARGETS, NOT FROM THE VOCABULARY.** The first
    #: version tested viability by decoding EVERY continuation token for every
    #: live prefix at every depth -- O(live x vocab) decodes, millions per
    #: depth, and it never returned. The needed continuations are exactly the
    #: strings `target[len(surf):][:k]`, so they are looked up in a
    #: string->ids index instead. O(live x targets x maxlen).
    pids, _rs, _rid = T._prompt_ids(tok, prompt, bos_policy)
    want = set(targets)
    idx = _tok_index(tok)
    lg = model(torch.tensor([pids], device=dev)).logits[0, -1, :].float()
    P0 = torch.softmax(lg, -1).cpu().numpy()
    del lg

    def extensions(done):
        """(token id, its string) for every token that advances `done` toward a target."""
        out = []
        for w in want:
            if not w.startswith(done) or w == done:
                continue
            rest = w[len(done):]
            for k in range(1, min(len(rest), _MAXTOK) + 1):
                for tid in idx.get(rest[:k], ()):
                    out.append((tid, rest[:k]))
        return out

    #: Seed on the targets' own first pieces, at FULL vocabulary rather than
    #: theta -- the words this exists to find are precisely the sub-theta ones.
    live = []
    for tid, s in extensions(""):
        live.append(((tid,), float(P0[tid]), tid, s))
    got, bcache, intra = {}, {}, {}
    for _ in range(T.MAX_DEPTH):
        if not live:
            break
        dist = T.next_dist(model, tok, pids, [p for p, _, _, _ in live], dev)
        nxt = []
        for (pref, mass, t1, done), row in zip(live, dist):
            surf = T.clean_surface(done.strip())
            if surf in want and not T.is_mojibake(surf):
                b = T._boundary_for(surf, bmask, cjk, bcache, intra)
                k = (surf, int(t1))
                got[k] = got.get(k, 0.0) + mass * float(row[b].sum())
            for tid, s in extensions(done):
                mm = mass * float(row[tid])
                if mm >= PATH_FLOOR:
                    nxt.append(((*pref, tid), mm, t1, done + s))
        #: **THE BEAM MUST BE BOUNDED OR IT GROWS MULTIPLICATIVELY.** Dropping
        #: theta was deliberate -- the words this exists to find are sub-theta --
        #: but replacing it with `mm > 0` prunes nothing, so `live` multiplies by
        #: the branching factor at every depth and never returns. That was the
        #: second performance bug in this function; the first was decoding the
        #: whole vocabulary per prefix.
        #:
        #: `PATH_FLOOR` is 1e-10, far below any word probability we report, and
        #: `PATH_WIDTH` caps the frontier by mass. Both are ORDERS below theta,
        #: so neither can drop a path that carries reportable mass -- and if the
        #: cap ever binds it is recorded, not silent.
        nxt.sort(key=lambda x: -x[1])
        if len(nxt) > PATH_WIDTH:
            dropped = sum(x[1] for x in nxt[PATH_WIDTH:])
            got.setdefault("__CAPPED__", 0.0)
            got["__CAPPED__"] += dropped
            nxt = nxt[:PATH_WIDTH]
        live = nxt
    return got


_MAXTOK = 24
#: Orders of magnitude below theta (1e-3), so neither can drop a path carrying
#: mass anyone would report. `__CAPPED__` in the result records what the width
#: cap dropped, so a bound that binds says so rather than silently truncating.
PATH_FLOOR = 1e-10
PATH_WIDTH = 4096
_TOKIDX = {}


def _tok_index(tok):
    """string -> [token ids that decode to it]. Built once per tokenizer."""
    key = id(tok)
    if key not in _TOKIDX:
        d = {}
        for i in range(tok.vocab_size):
            d.setdefault(tok.decode([i]), []).append(i)
        _TOKIDX[key] = d
    return _TOKIDX[key]


def leak_bound(pre, post, S, residual_pre, residual_post):
    """What the UNRESOLVED mass could be doing to an axis statistic. -> dict

    **A STANDING OBLIGATION THIS REPO DOES NOT MEET.** Finding N's registration:
    *"The per-cell worst-case leak bound is a COMPANION COLUMN beside the
    primary, reported for every cell — not a caveat sentence. It is the same
    order as plausible effects."* The archive reports it per cell; `movement.py`
    was ported without it (grep: no `leak`, no `dR_i`), so every `dN` in this
    store is currently quoted with no aperture attached.

    Theta gates FIRST TOKENS, so a cell resolves ~74-94% of its mass and the rest
    is words we never saw. Those words have axis scores too. Two numbers, and
    **they answer different questions, so both are returned and neither is "the"
    bound**:

        worst    RIGOROUS and adversarial: every unit of unresolved mass sits at
                 the extreme pole AND moves entirely between arms.
                 (residual_pre + residual_post) * max|s|.
                 Nothing can exceed it. Measured median +/-0.0851 against
                 measured |dN| of 0.0003..0.0945 -- i.e. WIDER THAN MOST
                 EFFECTS, exactly as the registration warned.

        matched  The tail is distributed like the HEAD: unresolved mass carries
                 the same mean axis score as the mass we did resolve. A point
                 correction, not an interval:
                 residual_post * E_post[s] - residual_pre * E_pre[s].

    **`matched` IS OPTIMISTIC IN A KNOWN DIRECTION AND MUST NOT BE QUOTED
    ALONE.** dario measured the residual is NOT matched -- lexicon words vanish
    below theta at 27.1% against 16.9% for controls, so it is ENRICHED in
    exactly what an axis weighs. The truth sits between `matched` and `worst`,
    nearer `matched`, and nobody has measured where.

    The per-cell worst case swamps the per-cell effect. That does NOT sink the
    aggregates -- `41/50 lineages`, `91% negative` are sign counts over
    thousands of cells, and they survive if leak contributions are not
    adversarially CORRELATED across cells. **That is an assumption, it is
    testable, and it has not been tested.**
    """
    smax = max((abs(v) for v in S.values()), default=0.0)
    tp, tq = sum(pre.values()), sum(post.values())
    e_pre = sum(p * S.get(w, 0.0) for w, p in pre.items()) / tp if tp else 0.0
    e_post = sum(p * S.get(w, 0.0) for w, p in post.items()) / tq if tq else 0.0
    return {"worst": (residual_pre + residual_post) * smax,
            "matched": residual_post * e_post - residual_pre * e_pre,
            "residual_pre": residual_pre, "residual_post": residual_post,
            "s_max": smax, "e_pre": e_pre, "e_post": e_post}


def compare(model, tok, prompt, dev, bmask, cjk=None, rules=None, top=6):
    """v3 against v4 on ONE cell. Prints what moved; returns the deltas.

    **RUN THIS WITH `Rules()` FIRST.** All-default must show zero movement; if it
    does not, this module has drifted from v3 and every v4 number after it is
    measuring the drift as well as the rule.
    """
    rules = rules or Rules()
    v3 = T.expand(model, tok, prompt, dev, bmask, cjk=cjk)
    w3 = v3[0] if isinstance(v3, tuple) else v3
    w4, res4, meta = expand4(model, tok, prompt, dev, bmask, cjk=cjk, rules=rules)
    keys = set(w3) | set(w4)
    d = [(w4.get(k, 0.0) - w3.get(k, 0.0), k) for k in keys]
    moved = [x for x in d if x[0] != 0.0]
    p3, p4 = sum(w3.values()), sum(w4.values())
    print("  %s vs v3   %r" % (meta["label"], prompt[:44]))
    print("    words: v3 %d | v4 %d | only-v3 %d | only-v4 %d"
          % (len(w3), len(w4), len(set(w3) - set(w4)), len(set(w4) - set(w3))))
    print("    summed p: %.6f -> %.6f  (%+.2f%%)"
          % (p3, p4, 100 * (p4 - p3) / p3 if p3 else 0.0))
    print("    moved: %d of %d words | floored mass %.6f"
          % (len(moved), len(keys), res4.get("term_floored", 0.0)))
    if rules.is_v3() and moved:
        print("    *** Rules() IS NOT v3 -- %d words moved, max %.3e ***"
              % (len(moved), max(abs(x) for x, _ in moved)))
    for x, k in sorted(moved, key=lambda z: -abs(z[0]))[:top]:
        print("       %-18s %.6f -> %.6f  (%+.1f%%)"
              % (str(k[0])[:18], w3.get(k, 0.0), w4.get(k, 0.0),
                 100 * x / w3[k] if w3.get(k) else float("inf")))
    return {"v3": w3, "v4": w4, "res": res4, "meta": meta, "moved": moved}
