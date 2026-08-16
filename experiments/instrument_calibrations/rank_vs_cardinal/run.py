#!/usr/bin/env python
"""Is `dN = sum dP(w)s(w)` too sensitive to the axis, and does a rank version help?

`dN` consumes the axis's CARDINAL values. Two facts make that worth testing
rather than assuming:

    the axis is not stable    resampling one author's own tags into halves and
                              building two axes from the same item gives
                              scorings correlating at r = 0.828 -- measured over
                              all 86 round-3 items in the sibling calibration
                              `../generic_axis/results/summary.json`
    dP is heavy-tailed        one candidate at p = 0.4 halving swamps fifty
                              candidates moving 0.001, so `dN` can rest on the
                              cardinal position of a single word

So this measures three statistics side by side over a real declared pair, and
then PERTURBS THE AXIS and watches which of them moves.

    dN       sum dP(w) s(w)              as booked; cardinal
    dN_rank  s replaced by normal scores rank-based, decomposition preserved
    delta    2*P(post more naughty) - 1  Cliff's delta; fully non-parametric

All three are implemented in `malignment.slot_axis` and their invariances are
asserted in `python -m malignment.slot_axis`, not claimed here.

## THE PAIR, AND WHY THIS ONE

`gl198976/mpt-7b -> gl198976/mpt-7b-instruct` is a DECLARED ENDPOINT PAIR in the
roster and both arms carry `CDH0050` twp records, which no other pair in the
local store does. Asserted below rather than assumed: the endpoint mapping is
re-read from `roster.endpoints()` at run time, so a roster correction breaks this
run instead of silently re-pointing it.

## THE AXIS, WITH NO AUTHOR TAGS ANYWHERE

These are corpus prompts. Nobody tagged poles for them and nobody will, so the
axis is the POOLED 12-PAIR LEXICAL one -- `naughty/nice`, `vulgar/polite` and ten
more, each normalised, then averaged, every pole word embedded in the prompt's
own frame. The sibling calibration is what licenses using it: pooled, it
reproduces the declared axis's scoring at r = 0.740 against that instrument's own
split-half ceiling of 0.828, i.e. **about 89% of the reliability tagging buys**,
and it beat every single pair on every measure.

**That is a licence to use it here and not a claim that it is the declared
axis.** The absolute level of `N` under a lexical axis is not comparable to `N`
under author tags -- the origins are different points -- which is precisely why
this run reports only DIFFERENCES, where the origin cancels exactly.

## THE PERTURBATION, WHICH IS THE ACTUAL EXPERIMENT -- AND IT NEEDS TWO SIZES

Every statistic is recomputed on every prompt under every perturbed axis. A
statistic robust to the axis keeps its ORDERING OF PROMPTS when the axis is
rebuilt from a different pole set; one that is not, reorders.

    LOO      12 axes, each pooling 11 of the 12 pairs      MILD
    SINGLE   12 axes, each built from ONE pair             STRONG

**The first run of this experiment used LOO alone and reported all three
statistics between 0.974 and 0.992, which is a result about the perturbation
rather than about the statistics.** Dropping one pair from a twelve-pair pool
barely moves the pooled direction, so nothing could have separated. Same defect
as judging a guard vacuous on a subsample too small to discriminate: the
population has to be able to tell the two versions apart before its verdict means
anything. SINGLE axes genuinely differ -- the sibling calibration puts their
agreement with a declared axis anywhere from 0.21 to 0.74.

Both are reported, and the comparison that carries weight is BETWEEN STATISTICS
UNDER THE SAME FAMILY, never a raw number read on its own.

## THE RESIDUAL IS BOUNDED RATHER THAN IMPUTED

`ps` renormalises over the scored words, which asserts the ~25% below theta is
distributed like the mass above it. It is not -- lexicon words vanish below theta
at 27.1% against 16.9% for controls -- so that assertion discards naughty-side
mass preferentially. Because `ps` depends only on rank, the assertion can be
replaced by a bound: `slot_axis.superiority_bounds` puts one arm's residual at
the extreme nice end and the other's at the extreme naughty end, and the true
value is inside whatever the residual actually contains. `dN` admits no such
bound, because it needs the cardinal positions theta destroyed. **The WIDTH of
that interval reports how much of the answer theta is deciding**, and where it
straddles 0.5 the direction of movement is not established at this theta,
whatever the point estimate says.

## CONCENTRATION

`top1_share` is the share of the total absolute contribution carried by the
single largest word. It answers the second half of the question -- how much of
`dN` is one word -- and is reported for the cardinal and rank forms so the
comparison is like for like. `delta` has no per-word decomposition and is
reported as `nan`, which is a property of the statistic and not a gap here.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from malignment import roster, slot_axis                      # noqa: E402
from malignment.checkpoint import Checkpoint                  # noqa: E402
from malignment.slot_axis import Axis, _normal_scores         # noqa: E402

sys.path.insert(0, os.path.join(REPO, "experiments", "instrument_calibrations",
                                "generic_axis"))
from run import LEXICAL_PAIRS  # noqa: E402,E501  the SAME twelve, imported not retyped

BASE = "gl198976/mpt-7b"
SEED = 20260817
PRODUCER = "CDH0050"
#: A PROMPT WITH ONE CANDIDATE HAS NO ORDERING, so it is not evidence about an
#: instrument that orders. `The mayor promised law and` resolves to `order` and
#: nothing else clears theta: its rank score is Phi^-1(1/2) = 0, every
#: contribution is 0, and `top1_share` comes out 0/0. Dropped and COUNTED rather
#: than averaged in as a zero -- and the cardinal form does not announce the
#: problem, it just reports `top1_share` 1.000, which reads as a finding.
MIN_VOCAB = 5


def probs_by_prompt(model_id):
    """{prompt: ({word: p}, residual_total)}, duplicate words SUMMED.

    A word can appear on more than one row -- different token paths reaching the
    same surface, `re` at t1 250 and t1 294 in the very first record -- and
    taking either row alone silently discards mass that belongs to the word.
    """
    ck = Checkpoint(model_id)
    out = {}
    for prod, st in ck.stashes():
        if prod != PRODUCER:
            continue
        for k in st.keys():
            if not isinstance(k, dict) or k.get("model") != model_id:
                continue
            r = st.get(k)
            if not r:
                continue
            d = {}
            for row in r["rows"]:
                d[row["word"]] = d.get(row["word"], 0.0) + row["p"]
            res = r.get("residual", {}).get("total", 0.0)
            #: The conservation identity is the record's own invariant. If it
            #: does not hold the record is not a distribution and nothing below
            #: means anything.
            tot = sum(d.values()) + res
            assert abs(tot - 1.0) < 1e-6, \
                "%s: sum(words) + residual = %.9f, not 1" % (model_id, tot)
            out[r["prompt"]] = (d, res)
    return out


def pooled_axis(prompt, pairs, words):
    """A pooled lexical axis over `pairs`, plus scores for `words`.

    Returns (scores, direction). Every pair is unit-normalised BEFORE averaging,
    so a pair whose two poles happen to sit far apart in the frame does not
    dominate the pool by magnitude alone.
    """
    lex = sorted({w for p in pairs for w in p})
    LF = dict(zip(lex, slot_axis.embed_cached(prompt, lex)))
    u = np.zeros_like(LF[lex[0]])
    o = np.zeros_like(LF[lex[0]])
    for g, n in pairs:
        d = LF[g] - LF[n]
        nn = np.linalg.norm(d)
        if nn > 1e-8:
            u += d / nn
        o += (LF[g] + LF[n]) / 2.0
    o /= len(pairs)
    nu = np.linalg.norm(u)
    u = u / nu if nu > 1e-8 else u
    V = slot_axis.embed_cached(prompt, words)
    return dict(zip(words, (float(x) for x in (V - o) @ u))), u


def stats_for(ax, base, post, S, b_res=None, p_res=None):
    """The three statistics plus the concentration measures, from one scoring."""
    car = ax.split(base, post, S=S)
    rnk = ax.split_rank(base, post, S=S)
    sup = ax.superiority(base, post, S=S)
    vocab = sorted(set(base) | set(post))
    dP = {w: post.get(w, 0.0) - base.get(w, 0.0) for w in vocab}
    Z = _normal_scores(S)

    def top1(sc):
        c = [abs(dP[w] * sc.get(w, 0.0)) for w in vocab]
        t = sum(c)
        return (max(c) / t) if t > 0 else float("nan")

    out = {}
    if b_res is not None:
        #: The residual carried as an INTERVAL rather than renormalised away.
        #: Only computed on the unperturbed axis: it is a statement about theta,
        #: not about the pole set.
        bnd = ax.superiority_bounds(base, post, b_res, p_res, S=S)
        out = {"ps_min": bnd["ps_min"], "ps_max": bnd["ps_max"],
               "ps_width": bnd["width"], "straddles_null": bnd["straddles_null"]}
    out.update({"dN": car["dN"], "suppression": car["suppression"],
                "substitution": car["substitution"],
                "dN_rank": rnk["dN"], "suppression_rank": rnk["suppression"],
                "substitution_rank": rnk["substitution"],
                "delta": sup["delta"], "ps": sup["ps"],
                "top1_share": top1(S), "top1_share_rank": top1(Z),
                "n_vocab": len(vocab)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=0,
                    help="first N shared prompts, for a smoke run")
    ap.add_argument("--sample", type=int, default=200,
                    help="random sample of shared prompts; 0 uses all of them")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    ep, unresolved = roster.endpoints()
    assert BASE in ep, "%s is not a declared base in endpoints()" % BASE
    POST = ep[BASE]
    print("pair       %s -> %s" % (BASE, POST))
    print("unresolved %d lineages in endpoints()" % len(unresolved))

    b_all, p_all = probs_by_prompt(BASE), probs_by_prompt(POST)
    prompts = sorted(set(b_all) & set(p_all))
    assert prompts, "no shared %s prompts between the two arms" % PRODUCER
    n_shared = len(prompts)
    #: A SAMPLE, DECLARED. Every prompt needs its whole candidate vocabulary
    #: embedded in its own frame -- ~250 strings each, on CPU by ruling -- so the
    #: full 2,881 is hours. The comparison here is BETWEEN statistics on
    #: identical prompts, so it needs enough prompts to correlate over, not the
    #: population. Seeded, and the drawn prompts are written out with the rows.
    if args.sample and args.sample < len(prompts):
        idx = np.random.default_rng(args.seed).choice(
            len(prompts), size=args.sample, replace=False)
        prompts = [prompts[i] for i in sorted(idx)]
    if args.limit:
        prompts = prompts[:args.limit]
    print("prompts    %d shared (%d base, %d post); using %d"
          % (n_shared, len(b_all), len(p_all), len(prompts)))

    ax = Axis.__new__(Axis)          # scores are supplied; no poles are declared
    ax._use_store = False

    #: TWO PERTURBATION FAMILIES, BECAUSE ONE OF THEM CANNOT DISCRIMINATE.
    #: Leave-one-out of a twelve-pair pool barely moves the pooled direction, and
    #: the first run of this experiment duly reported all three statistics at
    #: 0.97-0.99 -- a result about the perturbation, not about the statistics.
    #: SINGLE-pair axes are the strong version: the sibling calibration measures
    #: their agreement with a declared axis at anywhere from 0.21 to 0.74, so
    #: they are genuinely different instruments pointed at the same question.
    #: Both are reported. If the mild family separates nothing and the strong one
    #: does, that IS the finding, and reporting only the strong one would hide
    #: how much of the spread is the perturbation's size.
    perturb = ([("LOO:-%s" % g, [q for q in LEXICAL_PAIRS if q[0] != g])
                for g, _ in LEXICAL_PAIRS]
               + [("SINGLE:%s-%s" % p, [p]) for p in LEXICAL_PAIRS])
    rows, per_axis, dropped = [], {name: [] for name, _ in perturb}, []
    for i, pr in enumerate(prompts, 1):
        base, b_res = b_all[pr]
        post, p_res = p_all[pr]
        vocab = sorted(set(base) | set(post))
        if len(vocab) < MIN_VOCAB:
            dropped.append((pr, len(vocab)))
            continue
        S, _u = pooled_axis(pr, LEXICAL_PAIRS, vocab)
        r = {"prompt": pr, "residual_base": b_res, "residual_post": p_res}
        r.update(stats_for(ax, base, post, S, b_res, p_res))
        rows.append(r)
        for name, pairs in perturb:
            Sl, _ = pooled_axis(pr, pairs, vocab)
            per_axis[name].append(stats_for(ax, base, post, Sl))
        if i % 5 == 0 or i == len(prompts):
            print("  %3d/%d" % (i, len(prompts)))

    if dropped:
        print("dropped    %d prompts under MIN_VOCAB=%d (%s)"
              % (len(dropped), MIN_VOCAB,
                 ", ".join("%d word%s" % (n, "" if n == 1 else "s")
                           for _, n in dropped[:5])))
    write(args.out, BASE, POST, prompts, rows, per_axis, len(unresolved),
          n_shared, dropped)


def write(out, base_id, post_id, prompts, rows, per_axis, n_unresolved,
          n_shared, dropped):
    import csv
    from scipy.stats import pearsonr, spearmanr
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "per_prompt.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    col = lambda k, src=rows: np.array([r[k] for r in src], dtype=float)
    dN, dR, dl = col("dN"), col("dN_rank"), col("delta")

    agree = {
        "dN_vs_dN_rank_pearson": float(pearsonr(dN, dR).statistic),
        "dN_vs_dN_rank_spearman": float(spearmanr(dN, dR).statistic),
        "dN_vs_delta_pearson": float(pearsonr(dN, dl).statistic),
        "dN_vs_delta_spearman": float(spearmanr(dN, dl).statistic),
        "dN_rank_vs_delta_spearman": float(spearmanr(dR, dl).statistic),
        "sign_agree_dN_dN_rank": float(np.mean(np.sign(dN) == np.sign(dR))),
        "sign_agree_dN_delta": float(np.mean(np.sign(dN) == np.sign(dl))),
    }

    #: THE PERTURBATION RESULT. For each statistic, how well does the
    #: leave-one-out axis reproduce the full-pool ORDERING over prompts.
    stab = {}
    for fam in ("LOO", "SINGLE"):
        src_names = [n for n in per_axis if n.startswith(fam)]
        stab[fam] = {}
        for stat, full in (("dN", dN), ("dN_rank", dR), ("delta", dl)):
            rs = [float(spearmanr(full, col(stat, per_axis[n])).statistic)
                  for n in src_names]
            pe = [float(pearsonr(full, col(stat, per_axis[n])).statistic)
                  for n in src_names]
            sg = [float(np.mean(np.sign(full) == np.sign(col(stat, per_axis[n]))))
                  for n in src_names]
            stab[fam][stat] = {"spearman_mean": float(np.mean(rs)),
                               "spearman_min": float(np.min(rs)),
                               "pearson_mean": float(np.mean(pe)),
                               "sign_agree_mean": float(np.mean(sg)),
                               "n_axes": len(src_names)}

    summary = {
        "base": base_id, "post": post_id, "producer": PRODUCER,
        "n_prompts": len(rows), "n_prompts_drawn": len(prompts),
        "n_shared_prompts": n_shared, "min_vocab": MIN_VOCAB,
        "dropped_min_vocab": [{"prompt": p, "n_vocab": n} for p, n in dropped],
        "seed": SEED, "n_unresolved_lineages": n_unresolved,
        "n_leave_one_out_axes": len(per_axis),
        "lexical_pairs": ["%s-%s" % p for p in LEXICAL_PAIRS],
        "embedder": slot_axis.EMBEDDER,
        "residual_mean_base": float(col("residual_base").mean()),
        "residual_mean_post": float(col("residual_post").mean()),
        "top1_share_mean": float(col("top1_share").mean()),
        "ps_width_mean": float(col("ps_width").mean()),
        "n_straddling_null": int(sum(1 for r in rows if r["straddles_null"])),
        "top1_share_rank_mean": float(col("top1_share_rank").mean()),
        "agreement": agree,
        "axis_stability": stab,
    }
    with open(os.path.join(out, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print("\nRESIDUAL   base %.3f  post %.3f  (mass with no position on the axis)"
          % (summary["residual_mean_base"], summary["residual_mean_post"]))
    print("THETA BOUND  ps interval with the residual placed adversarially")
    print("    mean width %.3f   %d of %d prompts straddle 0.5"
          % (summary["ps_width_mean"], summary["n_straddling_null"], len(rows)))
    print("CONCENTRATION  share of the total contribution carried by ONE word")
    print("    cardinal %.3f      rank %.3f"
          % (summary["top1_share_mean"], summary["top1_share_rank_mean"]))
    #: `rows`, NOT `prompts`. The drawn sample and the measured population
    #: differ by the MIN_VOCAB drops, and a label taken from the wrong one
    #: describes a run that did not happen.
    print("\nAGREEMENT between the three statistics, over %d prompts" % len(rows))
    for k, v in agree.items():
        print("    %-28s %+.3f" % (k, v))
    for fam, what in (("LOO", "pooling 11 of 12 pairs -- a MILD perturbation"),
                      ("SINGLE", "one pair only -- a STRONG perturbation")):
        print("\nAXIS STABILITY: %d %s axes, %s" % (stab[fam]["dN"]["n_axes"],
                                                    fam, what))
        print("    %-9s %10s %10s %10s %10s" % ("statistic", "rho mean",
                                                "rho min", "r mean", "sign agree"))
        for stat in ("dN", "dN_rank", "delta"):
            d = stab[fam][stat]
            print("    %-9s %10.3f %10.3f %10.3f %10.3f"
                  % (stat, d["spearman_mean"], d["spearman_min"],
                     d["pearson_mean"], d["sign_agree_mean"]))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
