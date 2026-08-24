"""Why the half-split scoring was wrong, as a number anyone can regenerate.

    python experiments/displacement_axis/protocol_check.py

`variance_decomp.py` and `variance_repeated.py` scored every model by fitting on
half A's net movement and evaluating on half B, and scored the CEILING with
`np.polyfit(ya, yb, 1)` -- a slope fitted USING yb, the target. Two different
rules under one label. For two noisy halves with correlation rho the first gives
1-2(1-rho) and the second gives rho^2; at the observed rho=0.51 that is 0.000
against 0.261.

The consequence is not subtle and it ran for a full day: every model in that
analysis landed between -0.09 and +0.08, was compared against 0.261, and was
reported as explaining nothing. "Sexual is unexplained", "every model explains
something in identity and nothing anywhere else", and a purpose-built sexual
instrument declared indistinguishable from the wrong one at p=0.97 all come from
this and from nothing else.

This file regenerates the two facts that establish it, and writes them long so
they can be plotted rather than quoted:

  A  a PERFECT predictor -- half A itself -- scored by the models' own rule
  B  held-out R2 as the fitting half GROWS, with the test block held at a fixed
     size so the target's own noise never changes. This is what says leave-one-
     out is the right design rather than merely a bigger one.

Both are on the same frames the decomposition used. No ratings are involved: the
point is about the scoring, so nothing that could be blamed on an instrument is
allowed into it.
"""

import argparse, collections, csv, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
#: `--run` selects the run directory; pilot3 stays the default so every
#: command already written against this file keeps meaning what it meant.
RUN = "pilot3"
RES = os.path.join(HERE, "results", RUN)
LONG = os.path.join(RES, "long")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=RUN, help="run directory under results/")
    ap.add_argument("--splits", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    global RES
    RES = os.path.join(HERE, "results", a.run)
    global LONG
    LONG = os.path.join(RES, "long")
    if not os.path.isdir(RES):
        ap.error("no such run: %s" % RES)
    print("run: %s" % a.run)
    import numpy as np
    os.makedirs(LONG, exist_ok=True)

    lins = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        lins[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    dom = {c["item_id"]: c.get("domain")
           for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}

    rng = random.Random(a.seed)
    #: The sweep must REACH the data. Fixed at [1,2,4,8,12,16] it answered
    #: "still climbing at 16" on pilot3's 20 fitting lineages, which was the
    #: honest reading there; run unchanged on pilot4's 49 it prints the same
    #: sentence while saying nothing about lineages 17-49. Extended to the
    #: roster, with the test block held out.
    #: The per-frame loop below already skips any k that does not leave room for
    #: the 4-lineage test block, so this list only has to REACH the data.
    KS = [1, 2, 4, 8, 12, 16, 24, 32, 40, 45]
    import dedupe
    prompt_of = {c["item_id"]: c["prompt"]
                 for c in (json.loads(l) for l in open(os.path.join(RES, "cells.jsonl")))}
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))
    rows_a, rows_b = [], []
    for item, L_ in lins.items():
        if item not in KEEP:
            continue
        L = sorted(L_)
        ok = sorted({w for l in L for w in L_[l]})
        if len(L) < 8 or len(ok) < 40:
            continue
        ix = {w: i for i, w in enumerate(ok)}
        V = np.zeros((len(L), len(ok)))
        for r_, l in enumerate(L):
            for w, d_ in L_[l].items():
                V[r_, ix[w]] = 1 if d_ > 0 else (-1 if d_ < 0 else 0)

        rep, perf, rho = [], [], []
        for _ in range(a.splits):
            p = list(range(len(L))); rng.shuffle(p); h = len(p) // 2
            ya, yb = V[p[:h]].sum(0), V[p[h:]].sum(0)
            if ya.std() == 0 or yb.std() == 0:
                continue
            tot = ((yb - yb.mean()) ** 2).sum()
            b = np.polyfit(ya, yb, 1)
            rep.append(1 - ((yb - np.polyval(b, ya)) ** 2).sum() / tot)
            perf.append(1 - ((yb - ya) ** 2).sum() / tot)
            rho.append(float(np.corrcoef(ya, yb)[0, 1]))
        if rep:
            rows_a.append(dict(item=item, domain=dom.get(item), n_words=len(ok),
                               n_lineages=len(L),
                               ceiling_as_reported=float(np.mean(rep)),
                               perfect_predictor_same_rule=float(np.mean(perf)),
                               corr_half_half=float(np.mean(rho))))
        #: B needs a fixed-size test block, so it only runs where there is room
        if len(L) < 20:
            continue
        per = collections.defaultdict(list)
        for _ in range(60):
            p = list(range(len(L))); rng.shuffle(p)
            yb = V[p[:4]].mean(0)
            if yb.std() == 0:
                continue
            tot = ((yb - yb.mean()) ** 2).sum()
            for k in KS:
                if k > len(p) - 4:
                    continue
                ya = V[p[4:4 + k]].mean(0)          # MEAN both sides: scale matches
                if ya.std() == 0:
                    continue
                per[k].append(1 - ((yb - ya) ** 2).sum() / tot)
        for k, v in per.items():
            if v:
                rows_b.append(dict(item=item, domain=dom.get(item),
                                   n_lineages=len(L), fit_lineages=k,
                                   r2=float(np.mean(v)), n_draws=len(v)))

    for name, rows in (("protocol_ceiling.csv", rows_a),
                       ("protocol_growth.csv", rows_b)):
        with open(os.path.join(LONG, name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)

    med = lambda k, R: float(np.median([r[k] for r in R]))
    print("A  THE TWO RULES, on %d frames, %d splits each\n" % (len(rows_a), a.splits))
    print("   ceiling AS REPORTED (slope fitted on the target) : %+.3f"
          % med("ceiling_as_reported", rows_a))
    print("   a PERFECT predictor, scored by the models' rule  : %+.3f"
          % med("perfect_predictor_same_rule", rows_a))
    print("   median corr(half A net, half B net)              : %+.3f"
          % med("corr_half_half", rows_a))
    print("   frames where the perfect predictor beats 0 : %d/%d"
          % (sum(1 for r in rows_a if r["perfect_predictor_same_rule"] > 0), len(rows_a)))
    print("\nB  R2 AS THE FITTING HALF GROWS (test block fixed at 4 lineages)\n")
    print("   %-20s %9s %10s" % ("lineages used to fit", "median R2", "frames>0"))
    for k in KS:
        v = [r["r2"] for r in rows_b if r["fit_lineages"] == k]
        if v:
            print("   %-20d %+9.3f %7d/%-4d"
                  % (k, float(np.median(v)), sum(1 for x in v if x > 0), len(v)))
    #: State what the curve DID, rather than a sentence written when it stopped
    #: at 16. A rise over the last two points is not convergence.
    grew = {k: float(np.median([r["r2"] for r in rows_b if r["fit_lineages"] == k]))
            for k in KS if any(r["fit_lineages"] == k for r in rows_b)}
    got = sorted(grew)
    if len(got) >= 2:
        d = grew[got[-1]] - grew[got[-2]]
        print("\n   last step %d -> %d lineages: R2 %+0.4f -> %+0.4f (%+0.4f). %s"
              % (got[-2], got[-1], grew[got[-2]], grew[got[-1]], d,
                 "STILL CLIMBING -- leave-one-out, and the magnitude numbers are "
                 "still bounded by lineage count." if d > 0.005 else
                 "FLATTENING -- the fitting half is no longer the binding constraint."))
    print("\n-> results/%s/long/protocol_ceiling.csv, protocol_growth.csv" % a.run)


if __name__ == "__main__":
    main()
