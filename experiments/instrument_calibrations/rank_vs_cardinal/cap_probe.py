#!/usr/bin/env python
"""What a top-N rank cap does, measured on records theta already produced.

RH's proposal: take the top 50 words from each arm, and refuse the comparison
where an arm does not have 50 candidates. This measures it.

**WHAT THIS CAN AND CANNOT TEST.** A real v4 rank rule would EXPAND by rank, so
it would reach words theta never entered. Nothing here can produce those -- they
were never measured and no downstream analysis can invent them. What a cap
applied to existing records DOES test is the other half of the proposal, and it
is the half that carries the confound: whether making the aperture the same on
both arms changes the answer. `run.py` measured the asymmetry it is meant to fix
-- base residual 0.257 against post 0.222 on this pair, an aperture difference
correlated with the treatment itself, because alignment sharpens distributions
and a fixed probability floor therefore sees more of the aligned arm.

## THREE REGIMES, AND THE MIDDLE ONE IS THE PROPOSAL AS STATED

    UNION       every recorded word, a missing arm counted as 0     what run.py does
    CAP_UNION   union of each arm's top-N, a missing arm as 0       the proposal
    CAP_INTER   top-N among words RECORDED IN BOTH arms             fully symmetric

**`CAP_UNION` does not fully remove the asymmetry, and the reason is worth
stating.** A word in post's top 50 may be absent from base's record entirely --
not because base gives it zero, but because it fell below theta there. Counting
that as 0 is an imputation, the same one `UNION` makes, and no rank cap applied
after the fact can repair it: the number was never measured. Only a re-scoring
pass at production time can, which is the `union rescoring` recommendation and is
a change to twp rather than to analysis.

`CAP_INTER` removes it by exclusion instead, and pays for that honestly: it drops
exactly the words that appear in one arm only, which is where a word `arriving
from nothing` under alignment would show up. Both are reported because neither is
free, and the SIZE of the gap between them is the measurement of what the
one-arm-only words are worth. `run.py`'s earlier probe put them at ~30% of rows
but only ~3.7% of mass.

## THE ELIGIBILITY RULE IS A SELECTION AND IS REPORTED AS ONE

Refusing prompts where either arm has fewer than N candidates is RH's rule and it
is implemented, but it is not neutral: a prompt with few candidates above theta
is a PEAKED prompt, so the rule preferentially discards the confident,
low-entropy cases. The count and the residual profile of what it removes are
printed, because a filter whose bias runs along the same axis as the phenomenon
cannot be applied silently.
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

from malignment import roster, slot_axis          # noqa: E402
from malignment.slot_axis import Axis             # noqa: E402

#: BY PATH, UNDER AN EXPLICIT NAME. A bare `import run` from this directory
#: resolves to whichever `run.py` won the path race -- see `run._load`.
R = __import__("importlib").import_module("importlib.util")
_spec = R.spec_from_file_location("rvc_run", os.path.join(HERE, "run.py"))
_rvc = R.module_from_spec(_spec)
sys.modules["rvc_run"] = _rvc
_spec.loader.exec_module(_rvc)

LEXICAL_PAIRS = _rvc.LEXICAL_PAIRS
BASE, PRODUCER, SEED = _rvc.BASE, _rvc.PRODUCER, _rvc.SEED


def regimes(base, post, cap):
    """{regime: (word set, base probs, post probs)} for the three apertures."""
    def topn(d):
        return [w for w, _ in sorted(d.items(), key=lambda kv: -kv[1])[:cap]]

    both = set(base) & set(post)
    inter_ranked = sorted(both, key=lambda w: -(base[w] + post[w]))[:cap]
    sets = {
        "UNION": sorted(set(base) | set(post)),
        "CAP_UNION": sorted(set(topn(base)) | set(topn(post))),
        "CAP_INTER": sorted(inter_ranked),
    }
    out = {}
    for k, ws in sets.items():
        out[k] = (ws,
                  {w: base.get(w, 0.0) for w in ws},
                  {w: post.get(w, 0.0) for w in ws})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cap", type=int, default=50)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    ep, _un = roster.endpoints()
    assert BASE in ep, "%s is not a declared base in endpoints()" % BASE
    POST = ep[BASE]
    b_all, p_all = _rvc.probs_by_prompt(BASE), _rvc.probs_by_prompt(POST)
    prompts = sorted(set(b_all) & set(p_all))
    n_shared = len(prompts)
    if args.sample and args.sample < len(prompts):
        idx = np.random.default_rng(args.seed).choice(
            len(prompts), size=args.sample, replace=False)
        prompts = [prompts[i] for i in sorted(idx)]
    print("pair       %s -> %s" % (BASE, POST))
    print("prompts    %d shared; drawn %d; cap N=%d"
          % (n_shared, len(prompts), args.cap))

    ax = Axis.__new__(Axis)
    ax._use_store = False
    rows, refused = [], []
    for i, pr in enumerate(prompts, 1):
        base, b_res = b_all[pr]
        post, p_res = p_all[pr]
        #: RH'S ELIGIBILITY RULE, applied to each arm independently.
        if len(base) < args.cap or len(post) < args.cap:
            refused.append({"prompt": pr, "n_base": len(base), "n_post": len(post),
                            "residual_base": b_res, "residual_post": p_res})
            continue
        reg = regimes(base, post, args.cap)
        vocab = sorted({w for ws, _, _ in reg.values() for w in ws})
        S, _u = _rvc.pooled_axis(pr, LEXICAL_PAIRS, vocab)
        r = {"prompt": pr, "n_base": len(base), "n_post": len(post),
             "residual_base": b_res, "residual_post": p_res}
        for name, (ws, b, p) in reg.items():
            st = _rvc.stats_for(ax, b, p, {w: S[w] for w in ws})
            for k in ("dN", "dN_rank", "delta", "ps", "top1_share"):
                r["%s_%s" % (name, k)] = st[k]
            r["%s_n" % name] = len(ws)
            r["%s_mass_base" % name] = sum(b.values())
            r["%s_mass_post" % name] = sum(p.values())
            #: THE QUANTITY THE WHOLE PROPOSAL IS ABOUT: how differently the two
            #: arms are seen. Signed, so a systematic direction is visible.
            r["%s_aperture_gap" % name] = sum(p.values()) - sum(b.values())
            r["%s_one_arm_only" % name] = sum(
                1 for w in ws if (b[w] == 0.0) != (p[w] == 0.0))
        rows.append(r)
        if i % 25 == 0 or i == len(prompts):
            print("  %3d/%d" % (i, len(prompts)))

    write(args.out, BASE, POST, args.cap, rows, refused, n_shared, len(prompts))


def write(out, base_id, post_id, cap, rows, refused, n_shared, n_drawn):
    import csv
    from scipy.stats import pearsonr, spearmanr
    os.makedirs(out, exist_ok=True)
    #: **THE FILENAME IS THE GRAIN, AND IT NAMES THE QUESTION** (lacan, [6399]).
    #: These were `cap_per_prompt.csv` and `cap_summary.json` -- a prefix on
    #: `run.py`'s `per_prompt.csv`, which is the `by_chain_v2.csv` shape
    #: `experiments/README.md` warns about: a variant disambiguated by a prefix
    #: rather than a grain named for itself.
    #:
    #: And it was worse than a naming smell. **Both files are one row per prompt
    #: over DIFFERENT POPULATIONS** -- `run.py` measures 197 and this measures
    #: the 159 that clear `MIN_VOCAB`-plus-eligibility -- so two same-grain files
    #: sat beside each other with no way to tell from the names which row set
    #: either held. That is exactly the ambiguity the rule exists to prevent.
    tag = "cap%d" % cap
    with open(os.path.join(out, "aperture_by_prompt.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    col = lambda k: np.array([r[k] for r in rows], dtype=float)
    REG = ("UNION", "CAP_UNION", "CAP_INTER")
    aperture, agree = {}, {}
    for g in REG:
        aperture[g] = {
            "n_words_mean": float(col("%s_n" % g).mean()),
            "mass_base_mean": float(col("%s_mass_base" % g).mean()),
            "mass_post_mean": float(col("%s_mass_post" % g).mean()),
            "aperture_gap_mean": float(col("%s_aperture_gap" % g).mean()),
            "aperture_gap_abs_mean": float(np.abs(col("%s_aperture_gap" % g)).mean()),
            "one_arm_only_mean": float(col("%s_one_arm_only" % g).mean()),
            "top1_share_mean": float(col("%s_top1_share" % g).mean()),
        }
    for g in ("CAP_UNION", "CAP_INTER"):
        for stat in ("dN", "dN_rank", "delta"):
            a, b = col("UNION_%s" % stat), col("%s_%s" % (g, stat))
            agree["%s/%s" % (g, stat)] = {
                "pearson": float(pearsonr(a, b).statistic),
                "spearman": float(spearmanr(a, b).statistic),
                "sign_agree": float(np.mean(np.sign(a) == np.sign(b))),
            }

    ref_res = ([r["residual_base"] for r in refused] or [float("nan")])
    summary = {
        "base": base_id, "post": post_id, "cap": cap, "seed": SEED,
        "n_shared_prompts": n_shared, "n_drawn": n_drawn,
        "n_eligible": len(rows), "n_refused": len(refused),
        "refused_residual_base_mean": float(np.mean(ref_res)),
        "eligible_residual_base_mean": float(col("residual_base").mean()),
        "aperture": aperture, "agreement_vs_UNION": agree,
    }
    with open(os.path.join(out, "aperture_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print("\nELIGIBILITY  '%d candidates on both arms or no comparison'" % cap)
    print("    eligible %d of %d drawn; refused %d"
          % (len(rows), n_drawn, len(refused)))
    print("    mean base residual: eligible %.3f   REFUSED %.3f"
          % (summary["eligible_residual_base_mean"],
             summary["refused_residual_base_mean"]))
    print("\nAPERTURE  what each regime actually looks at")
    print("    %-10s %7s %8s %8s %9s %9s %8s"
          % ("regime", "words", "mass_b", "mass_p", "gap", "|gap|", "1-arm"))
    for g in REG:
        d = aperture[g]
        print("    %-10s %7.1f %8.3f %8.3f %+9.4f %9.4f %8.1f"
              % (g, d["n_words_mean"], d["mass_base_mean"], d["mass_post_mean"],
                 d["aperture_gap_mean"], d["aperture_gap_abs_mean"],
                 d["one_arm_only_mean"]))
    print("\nAGREEMENT with the uncapped UNION regime")
    print("    %-22s %8s %9s %10s" % ("", "pearson", "spearman", "sign agree"))
    for k, v in agree.items():
        print("    %-22s %8.3f %9.3f %10.3f"
              % (k, v["pearson"], v["spearman"], v["sign_agree"]))
    print("\nwrote %s" % os.path.join(out, "aperture_summary.json"))


if __name__ == "__main__":
    main()
