#!/usr/bin/env python
"""PER-WORD transfer: does a word's PKU preference score predict its mass change?

    python word_transfer.py --score-only    fit and inspect the per-word scores
    python word_transfer.py

## WHY THIS AND NOT THE PROJECTION IN run.py

`run.py` learned beta over SEVEN norm dimensions and projected each rung's
norm-profile movement onto it. Two things were wrong with that channel and both
are measured, not suspected:

    1  IT IS NARROW. On PKU itself the 7 norm dims reach AUC 0.5811 where a
       unigram model reaches 0.7135 (`ablation.py`). Most of what the
       annotators respond to is lexical and never entered the transfer.
    2  IT AGGREGATED ON BOTH SIDES, AND NOT THE SAME WAY. The PKU profile is a
       mean over the tokens of a REALISED multi-sentence response; the model
       profile is a mass-weighted mean over a SINGLE-SLOT next-word
       distribution. run.py called these "the same functional form", which is
       true of the arithmetic and false about the objects.

This file removes both. A word's corpus score against that same word's mass
change: one grain, no profile averaging on either side, and the stronger signal.

## THE SCORE

Smoothed log-odds of appearing in the SAFER response vs the other one, per word,
over all 73,907 pairs. Reported beside the fitted logistic coefficients so the
two can be checked against each other -- a hand-computable statistic and a
cross-validated one should agree, and if they do not, that is worth knowing
before either is used.

## THE CONTROL THAT MATTERS

Word frequency. Common words have both large PKU counts and distinctive
movement, so a raw correlation could be reading frequency twice. Every
correlation is therefore reported ALSO on the residual after regressing out
`log p_base`, and the two are printed together.
"""
import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIB = os.path.join(os.path.dirname(HERE), "pku-safe-rlhf")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
sys.path.insert(0, SIB)

OUT = os.path.join(HERE, "results")
SEED = 20260907
LLAMA = "huggyllama/llama-7b"
ALPACA = "PKU-Alignment/alpaca-7b-reproduced"
BEAVER = "PKU-Alignment/beaver-7b-v1.0"
RUNGS = (("PLACEBO", LLAMA, ALPACA), ("TREATED", ALPACA, BEAVER),
         ("SPAN", LLAMA, BEAVER))
MIN_COUNT = 20
MIN_WORDS = 8


def scores(mode="mixed"):
    """{word: z-scored log-odds}. THE TARGET IS A CHOICE AND IT MATTERS.

    RH, 2026-09-07: *"Why are we predicting labelled UNSAFE?"* The first run
    used `pooled`, and **44.2% of PKU pairs have BOTH responses labelled
    unsafe**, so on nearly half the data `safer_response_id` picks the LESS BAD
    harmful response, which is still harmful. Another 41.2% are both-safe,
    where the preference is style rather than safety. **Only 14.6% of pairs are
    the regime where "safer" separates safe from unsafe.**

        pooled    safer_response_id over all 73,907 pairs. What Safe RLHF
                  actually optimises, so defensible as the training signal --
                  but 85% of it is within-safety-class comparison.
        mixed     THE CLEAN TARGET, and the default. The 10,813 pairs where
                  exactly one response is labelled safe. Both answer the SAME
                  PROMPT, so topic is controlled by construction.
        absolute  is_response_N_safe over all 147,814 responses. **TRIED AND
                  REJECTED**: safe and unsafe responses answer DIFFERENT
                  prompts, so it learns topic. Its top "safe" words are
                  `waste, animal, food, energy, pet, environmental` -- the
                  subject matter of benign questions, not a stance. Kept
                  selectable so the defect can be reproduced, never as default.

    pooled and mixed correlate +0.739 and share their top words; absolute
    correlates only +0.565 with pooled. The transfer result is the same under
    pooled and mixed and BIGGER under mixed.
    """
    import numpy as np
    import run as PKU
    assert hasattr(PKU, "k_ranks"), "imported the wrong run.py -- see did.py"
    d = PKU.load("train")
    n = len(d["prompt"])
    good, bad = collections.Counter(), collections.Counter()
    for i in range(n):
        s0, s1 = d["is_response_0_safe"][i], d["is_response_1_safe"][i]
        if mode == "absolute":
            for c, ok in ((0, s0), (1, s1)):
                (good if ok else bad).update(
                    PKU.TOKEN.findall(d["response_%d" % c][i].lower()))
            continue
        if mode == "mixed":
            if s0 == s1:
                continue
            g, b = (0, 1) if s0 else (1, 0)
        else:
            g = d["safer_response_id"][i]; b = 1 - g
        good.update(PKU.TOKEN.findall(d["response_%d" % g][i].lower()))
        bad.update(PKU.TOKEN.findall(d["response_%d" % b][i].lower()))
    vocab = [w for w in set(good) | set(bad)
             if good[w] + bad[w] >= MIN_COUNT]
    tg, tb = sum(good[w] for w in vocab), sum(bad[w] for w in vocab)
    #: Z-SCORED, NOT RAW LOG-ODDS. The unweighted version was tried first and
    #: its extremes were all rare technical nouns -- `sumac`, `digitalis`,
    #: `hellebore` one way, `eyedropper`, `dichromate` the other -- because a
    #: log-odds at count 20 is mostly sampling noise. Dividing by the standard
    #: error of the log-odds (Monroe et al.'s form) is what makes the extremes
    #: words with evidence behind them rather than words with none.
    lo = {}
    a0 = 0.5
    for w in vocab:
        g, b = good[w] + a0, bad[w] + a0
        pg = g / (tg + a0 * len(vocab))
        pb = b / (tb + a0 * len(vocab))
        se = math.sqrt(1.0 / g + 1.0 / b)
        lo[w] = math.log(pg / pb) / se
    return lo, good, bad


def deltas(base, aligned, prompts):
    """{prompt: {word: delta}} from movement_v4, plus p_base for the control."""
    from malignment import vectors as V
    out, pb = collections.defaultdict(dict), collections.defaultdict(dict)
    CH = 120
    for i in range(0, len(prompts), CH):
        blk = prompts[i:i + CH]
        for r in V.rows(
                "SELECT prompt, word, delta, p_base FROM movement_v4 "
                "WHERE base={b:String} AND aligned={a:String} "
                "AND prompt IN {ps:Array(String)} AND rule='canonical' "
                "AND frame_base='' AND frame_aligned=''",
                b=base, a=aligned, ps=blk):
            out[r["prompt"]][r["word"]] = r["delta"]
            pb[r["prompt"]][r["word"]] = r["p_base"]
    return out, pb


def per_prompt_rho(D, PB, lo):
    """[(prompt, rho, rho_resid, n)] -- Spearman per prompt, raw and residualised."""
    import numpy as np
    from scipy import stats
    out = []
    for p, wd in D.items():
        ws = [w for w in wd if w.strip().lower() in lo]
        if len(ws) < MIN_WORDS:
            continue
        x = np.asarray([lo[w.strip().lower()] for w in ws])
        y = np.asarray([wd[w] for w in ws])
        if np.std(x) == 0 or np.std(y) == 0:
            continue
        rho = stats.spearmanr(x, y).statistic
        f = np.log(np.asarray([max(PB[p][w], 1e-9) for w in ws]))
        if np.std(f) > 0:
            xr = x - np.polyval(np.polyfit(f, x, 1), f)
            yr = y - np.polyval(np.polyfit(f, y, 1), f)
            rr = stats.spearmanr(xr, yr).statistic if np.std(xr) and np.std(yr) else float("nan")
        else:
            rr = float("nan")
        out.append((p, float(rho), float(rr), len(ws)))
    return out


def sign_test(vals):
    up = sum(1 for v in vals if v > 0); dn = sum(1 for v in vals if v < 0)
    n = up + dn
    if n == 0:
        return up, dn, 1.0
    k = min(up, dn)
    return up, dn, min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--score", default="mixed", choices=("mixed", "pooled", "absolute"),
                    help="see scores(). mixed is the clean target and the default; "
                         "absolute is topic-confounded and kept only to reproduce it")
    ap.add_argument("--prompts", type=int, default=900)
    a = ap.parse_args(argv)
    import numpy as np
    lo, good, bad = scores(a.score)
    print("per-word PKU log-odds, target=%s, %d words (min count %d)"
          % (a.score, len(lo), MIN_COUNT))
    top = sorted(lo, key=lambda w: -lo[w])[:14]
    bot = sorted(lo, key=lambda w: lo[w])[:14]
    print("  SAFER side  : %s" % ", ".join(top))
    print("  OTHER side  : %s" % ", ".join(bot))
    if a.score_only:
        return 0

    from malignment import roster, vectors as V
    prompts = [r["prompt"] for r in V.rows(
        "SELECT prompt FROM twp_words_v4_best WHERE model={m:String} "
        "GROUP BY prompt ORDER BY prompt LIMIT {n:UInt32}", m=BEAVER, n=a.prompts)]
    print("\n%s\nPER-WORD TRANSFER, %d prompts\n%s" % ("=" * 92, len(prompts), "=" * 92))
    print("%-9s %6s %10s %10s %11s %10s" % ("rung", "n", "med rho", "up/dn", "p", "med resid"))
    res = {}
    for name, b_, a_ in RUNGS:
        D, PB = deltas(b_, a_, prompts)
        rows = per_prompt_rho(D, PB, lo)
        r = [x[1] for x in rows]
        rr = [x[2] for x in rows if x[2] == x[2]]
        up, dn, p = sign_test(r)
        res[name] = dict(n=len(r), med=float(np.median(r)), up=up, dn=dn, p=p,
                         med_resid=float(np.median(rr)) if rr else None)
        print("%-9s %6d %+10.4f %5d/%-4d %11.2g %+10.4f"
              % (name, len(r), np.median(r), up, dn, p,
                 np.median(rr) if rr else float("nan")))

    print("\n%s\nCONTROL: endpoint pairs PKU never touched\n%s" % ("=" * 92, "=" * 92))
    ep, _ = roster.endpoints()
    meds = []
    for b_, a_ in sorted(ep.items()):
        if b_ == LLAMA:
            continue
        D, PB = deltas(b_, a_, prompts)
        rows = per_prompt_rho(D, PB, lo)
        if len(rows) < 50:
            continue
        meds.append((float(np.median([x[1] for x in rows])), b_, a_))
    meds.sort()
    cm = [m for m, _, _ in meds]
    up, dn, p = sign_test(cm)
    print("  %d lineages, median-of-medians %+.4f, %d up / %d dn, p=%.2g"
          % (len(cm), np.median(cm), up, dn, p))
    t = res["TREATED"]["med"]
    below = sum(1 for m in cm if m < t)
    print("  TREATED %+.4f is above %d of %d controls (percentile %.0f)"
          % (t, below, len(cm), 100.0 * below / max(len(cm), 1)))
    print("  PLACEBO %+.4f" % res["PLACEBO"]["med"])
    os.makedirs(OUT, exist_ok=True)
    fn = "word_transfer_%s.json" % a.score
    json.dump(dict(score=a.score, rungs=res,
                   control=[(m, b_, a_) for m, b_, a_ in meds],
                   n_words=len(lo), n_prompts=len(prompts)),
              open(os.path.join(OUT, fn), "w"), indent=1)
    print("\n-> results/%s" % fn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
