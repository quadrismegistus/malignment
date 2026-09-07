#!/usr/bin/env python
"""Does the direction PKU rewards predict the direction alignment moved beaver?

    python run.py --beta      phase 1 only: fit beta on PKU, characterise the null
    python run.py             all three phases

See README.md for the design. Three phases:

    1  BETA   logistic regression on PKU's kA - kB (mean K-rank profile
              difference between the two responses of a pair), label
              `safer_response_id`. The coefficient vector is the direction in
              norm-space this annotation regime rewards. Null from `randomise`.
    2  LADDER project each rung's norm-profile movement onto beta:
                 PLACEBO  llama-7b -> alpaca-7b-reproduced   (Alpaca SFT, not PKU)
                 TREATED  alpaca-7b-reproduced -> beaver-7b  (Safe RLHF on PKU)
                 SPAN     llama-7b -> beaver-7b              (both)
    3  CONTROL the other endpoint pairs, which PKU never touched.

## THE CORRESPONDENCE THAT MAKES THE TRANSFER LEGITIMATE

PKU's `kvec` is the mean K-rank over the lexicon-covered TOKENS of a response,
so it is occurrence-weighted. The model-side analogue is the same mean weighted
by PROBABILITY MASS over the lexicon-covered words of the slot distribution --
`norm_change`'s "level". Token frequency and probability mass are the two
weightings of the same quantity, and both sides are then DIFFERENCED between two
arms. Without that the projection would compare a text statistic to a
distribution statistic and mean nothing.

## FENCES INHERITED FROM ../pku-safe-rlhf/

`register_level` (IAA 0.597, NOT ESTABLISHED) and `vulgarity` (variance on 463
of 27,242 words) are COMPUTED AND REPORTED, NEVER EVIDENCE. That is that
folder's rule and it binds here: this file's README predicted beta would load on
`k_register_level`, and if it does, that is a reported observation and not a
result. `transgressiveness` and `bodily_harm` are the primary dimensions.

Ranks, never levels: charge and concreteness shift in LEVEL between instrument
versions while holding ORDER at r=0.88.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIB = os.path.join(os.path.dirname(HERE), "pku-safe-rlhf")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
sys.path.insert(0, SIB)

OUT = os.path.join(HERE, "results")
SEED = 20260907
NULLS = 200

LLAMA = "huggyllama/llama-7b"
ALPACA = "PKU-Alignment/alpaca-7b-reproduced"
BEAVER = "PKU-Alignment/beaver-7b-v1.0"
LADDER = (("PLACEBO", LLAMA, ALPACA), ("TREATED", ALPACA, BEAVER),
          ("SPAN", LLAMA, BEAVER))


def beta(label="safer_response_id"):
    """(dims, beta, auc_real, auc_null_mean, n) -- the direction PKU rewards."""
    import numpy as np
    import run as PKU
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    d = PKU.load("train")
    dims, ranks = PKU.k_ranks()
    idx = list(range(len(d["prompt"])))
    F = PKU.features(d, idx, dims, ranks)
    X = F["k"]
    #: y = 1 when response_0 is the preferred one, so a POSITIVE projection on
    #: beta means "moved toward what the annotators preferred".
    y = np.asarray([1 if d[label][i] == 0 else 0 for i in idx])
    keep = np.isfinite(X).all(axis=1)
    X, y = X[keep], y[keep]
    n = len(y)
    rng = np.random.default_rng(SEED)
    tr = rng.random(n) < 0.7
    m = LogisticRegression(max_iter=3000, solver="liblinear")
    m.fit(X[tr], y[tr])
    real = roc_auc_score(y[~tr], m.decision_function(X[~tr]))
    #: THE NULL IS CHARACTERISED, NOT ASSUMED. p_on_passages' I2 was wrong in
    #: two successive versions for want of exactly this.
    nulls = []
    for s in range(NULLS):
        r2 = np.random.default_rng(SEED + s + 1)
        yp = r2.permutation(y)
        mm = LogisticRegression(max_iter=3000, solver="liblinear")
        mm.fit(X[tr], yp[tr])
        nulls.append(roc_auc_score(yp[~tr], mm.decision_function(X[~tr])))
    return dims, m.coef_[0], real, float(np.mean(nulls)), float(np.std(nulls)), n


def profiles(models, prompts, dims, ranks):
    """{(model, prompt): K-rank profile}, mass-weighted. The model-side kvec."""
    import numpy as np
    from malignment import movement as M
    out = {}
    CH = 60
    for i in range(0, len(prompts), CH):
        blk = prompts[i:i + CH]
        #: `words_multi` returns {prompt: {model: {word: p}}} -- NOT keyed by
        #: (model, prompt). The first version of this loop unpacked it as a
        #: pair key, matched nothing, and would have reported n=0 on every
        #: stage as though the data were absent.
        W = M.words_multi(models, blk)
        for p, bym in W.items():
          for mdl, probs in bym.items():
            num = np.zeros(len(dims)); den = 0.0
            for w, pr in probs.items():
                r = ranks.get(w.strip().lower())
                if r is None:
                    continue
                num += pr * r; den += pr
            if den > 0:
                out[(mdl, p)] = num / den
    return out


def project(prof, base, aligned, prompts, b):
    """[(prompt, projection)] -- the movement's component along beta."""
    import numpy as np
    out = []
    for p in prompts:
        a, z = prof.get((base, p)), prof.get((aligned, p))
        if a is None or z is None:
            continue
        out.append((p, float(np.dot(z - a, b))))
    return out


def sign_test(vals):
    import math
    up = sum(1 for v in vals if v > 0); dn = sum(1 for v in vals if v < 0)
    n = up + dn
    if n == 0:
        return up, dn, 1.0
    k = min(up, dn)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return up, dn, p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--beta", action="store_true", help="phase 1 only")
    ap.add_argument("--prompts", type=int, default=700)
    a = ap.parse_args(argv)
    import numpy as np
    import run as PKU

    print("=" * 88)
    print("PHASE 1 -- BETA: the direction PKU's annotators reward")
    print("=" * 88)
    res = {}
    for label in ("safer_response_id", "better_response_id"):
        dims, b, real, nm, ns, n = beta(label)
        print("\n%s   n=%d pairs" % (label, n))
        print("  AUC real %.4f | null mean %.4f sd %.4f | REAL-MINUS-NULL %+.4f"
              % (real, nm, ns, real - nm))
        order = np.argsort(-np.abs(b))
        print("  beta, largest |coef| first:")
        for j in order[:10]:
            fence = "  [REPORTED ONLY]" if dims[j] in ("register_level", "vulgarity") else ""
            print("     %-26s %+.3f%s" % (dims[j], b[j], fence))
        res[label] = dict(dims=list(dims), beta=[float(x) for x in b],
                          auc=real, null_mean=nm, null_sd=ns, n=n)
    if a.beta:
        os.makedirs(OUT, exist_ok=True)
        json.dump(res, open(os.path.join(OUT, "beta.json"), "w"), indent=1)
        print("\n-> results/beta.json")
        return 0

    dims, ranks = PKU.k_ranks()
    b = np.asarray(res["safer_response_id"]["beta"])

    from malignment import movement as M, roster, vectors as V
    q = ("SELECT prompt FROM twp_words_v4_best WHERE model={m:String} "
         "GROUP BY prompt ORDER BY prompt LIMIT {n:UInt32}")
    prompts = [r["prompt"] for r in V.rows(q, m=BEAVER, n=a.prompts)]
    print("\n%s\nPHASE 2 -- THE LADDER, %d prompts\n%s" % ("=" * 88, len(prompts), "=" * 88))
    prof = profiles([LLAMA, ALPACA, BEAVER], prompts, dims, ranks)
    print("%-10s %-46s %7s %8s %10s %9s" % ("stage", "edge", "n", "median", "up/dn", "p"))
    lad = {}
    for name, bs, al in LADDER:
        v = project(prof, bs, al, prompts, b)
        vals = [x for _, x in v]
        up, dn, p = sign_test(vals)
        lad[name] = dict(median=float(np.median(vals)), n=len(vals), up=up, dn=dn, p=p)
        print("%-10s %-46s %7d %+8.4f %5d/%-4d %9.2g"
              % (name, "%s -> %s" % (bs.split("/")[-1][:20], al.split("/")[-1][:20]),
                 len(vals), np.median(vals), up, dn, p))

    print("\n%s\nPHASE 3 -- CONTROL: endpoint pairs PKU never touched\n%s" % ("=" * 88, "=" * 88))
    ep, _ = roster.endpoints()
    pairs = [(bs, al) for bs, al in sorted(ep.items()) if bs != LLAMA]
    meds = []
    ms = sorted({x for pr in pairs for x in pr})
    cprof = profiles(ms, prompts, dims, ranks)
    for bs, al in pairs:
        v = [x for _, x in project(cprof, bs, al, prompts, b)]
        if len(v) < 50:
            continue
        meds.append((float(np.median(v)), bs, al))
    meds.sort()
    cm = [m for m, _, _ in meds]
    up, dn, p = sign_test(cm)
    print("  %d control lineages, median-of-medians %+.4f, %d up / %d dn, p=%.2g"
          % (len(cm), np.median(cm), up, dn, p))
    tre = lad["TREATED"]["median"]
    above = sum(1 for m in cm if m < tre)
    print("  TREATED median %+.4f sits above %d of %d controls (percentile %.0f)"
          % (tre, above, len(cm), 100.0 * above / max(len(cm), 1)))
    print("  PLACEBO median %+.4f" % lad["PLACEBO"]["median"])
    print("\n  most positive controls:")
    for m, bs, al in meds[-4:][::-1]:
        print("     %+.4f  %s -> %s" % (m, bs.split("/")[-1][:26], al.split("/")[-1][:26]))
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(beta=res, ladder=lad, n_prompts=len(prompts),
                   control=[(m, b_, a_) for m, b_, a_ in meds]),
              open(os.path.join(OUT, "run.json"), "w"), indent=1)
    print("\n-> results/run.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
