"""Is the axis shift alignment REORDERING its preferences or SHARPENING them?

    python experiments/displacement_axis/mechanism.py --run pilot2

Writes `<run>/mechanism.jsonl`, one row per cell. Report with
`mechanism_report.py`.

## THE QUESTION, AND HOW IT REPLACED A WORSE ONE (RH, 2026-08-18)

This started as "would ranks instead of mass change anything?" -- a fair worry
about `dN_position`, which is a MASS-WEIGHTED centroid and so lets a word holding
half the distribution speak for the distribution.

Two corrections killed that framing and produced this one.

**First: the aperture is already out.** `dN_position` is `N_aligned - N_base`
where `N = sum p(w)s(w) / sum p(w)` (`slot_axis.stats`, line 409), renormalised
PER ARM by that arm's own available mass. Differences in how much mass each
checkpoint puts above `theta` divide out by construction. "Mass is confounded
with concentration" was never the objection, and an earlier draft of this file
said it was.

**Second, and this is the one that matters: if alignment's signature move IS to
become more decisive about words it already preferred, a rank statistic is blind
to precisely the effect under study.** A model that already ranked `accept`
first and sharpens it from 0.011 to 0.521 shows ZERO rank change and a total
change in what it emits. Ranks would report that as nothing happened. So ranks
are not a more conservative instrument here; on that hypothesis they are a
systematically deaf one, and "the rank version is smaller" would then be the
EXPECTED CONSEQUENCE of the effect being real rather than evidence against it.

So the useful decomposition is not mass-against-rank. It is:

    REORDERING   does the model change WHICH words it prefers
    SHARPENING   does it redistribute magnitude among preferences it already had

## THE COUNTERFACTUAL

Both are recoverable by swapping one arm's magnitude profile into the other's
ordering. Writing `v = sorted(p, descending)` for the multiset of probabilities
with the words forgotten, and `r(w)` for a word's ordinal position:

    sharpen-only   q(w)  = v_a[r_b(w)]    base preferences, ALIGNED decisiveness
    reorder-only   q'(w) = v_b[r_a(w)]    aligned preferences, BASE decisiveness

    dN_sharpen  = N(q)  - N(p_b)
    dN_reorder  = N(q') - N(p_b)
    interaction = dN_total - dN_sharpen - dN_reorder

Each counterfactual is a PERMUTATION of a real probability vector, so it is a
valid distribution summing to that arm's own total, and `N` renormalises anyway.
No normalisation choice needs defending.

The interaction is reported and never folded into either term. It is not an
error term: the two mechanisms genuinely interact, because sharpening onto a word
matters more when that word has also moved, and a decomposition that hid it would
attribute a joint effect to whichever term happened to be listed first.

## TIES, WHICH ARE THE ONE PLACE THIS COULD CHEAT

Ranks here are ORDINAL, not averaged: the counterfactual pours exactly one value
into each slot, and averaged ranks are fractional. But these distributions have
long ties at zero -- words below `theta` are unrecorded -- so which tied word
receives which tail value is arbitrary.

Two guards, and the second is the one that would catch a real problem:

  - the sort key is `(-p, word)`, so the arbitrariness is at least deterministic
    and a re-run reproduces it;
  - `--flip-ties` reverses the secondary key. **If the decomposition moves under
    that, it is an artifact of tie-breaking and not a measurement.**

**RUN ON PILOT2, AND THE EXPECTATION WAS WRONG IN THE INTERESTING DIRECTION.**
This paragraph previously said the tail carries little mass so the decomposition
would not move. It moves. `dN_reorder` differs in 80% of cells, `interaction` in
95%, and the largest single perturbation (8.5e-03) EXCEEDS the median effect
being measured (-3.2e-03). What does not move is the conclusion: medians shift in
the fourth decimal (-0.00318 to -0.00327), the sharpen-dominant share goes 37.4%
to 37.2%, and 32 cells of 3,758 (0.9%) change which mechanism dominates.

    So the aggregate is robust and a PER-CELL dN_reorder is not quotable.
    Do not build a cell exhibit on this column the way the plea-deal exhibit
    was built on the word contributions.

The asymmetry has a cause and it is the same effect under study. `q_reorder`
pours into the ALIGNED ordering, and the aligned arm is the concentrated one --
entropy falls in 82% of cells -- so more of its words sit at the `theta` floor,
tied, with arbitrary relative order. Verified rather than reasoned: per-cell
perturbation against entropy change gives r = -0.458, the sharpest quartile has
median perturbation 3.7e-04, and the quartile where entropy ROSE has median
perturbation exactly zero. `dN_sharpen`, which pours into the base ordering,
moves in 15% of cells. `dN_total` uses no ordinals and is invariant to machine
precision (max difference 0.00e+00 over 3,758 cells).

Rank statistics (`d_rho`, `d_auc`) are computed alongside, because the original
question deserves its answer even though it is no longer the primary: if
reordering dominates, the rank version should track the mass version, and if
sharpening dominates it should not.
"""

import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
TABLE = "twp_words_v4"


def _ordinal(vals, words, flip=False):
    """Ordinal positions, 0-based, deterministic under ties.

    `pos[i]` is item i's place in descending order of value. Every item gets a
    DISTINCT position by construction, which is what the counterfactual needs and
    what averaged ranks cannot supply.
    """
    key = (lambda i: (-vals[i], words[i][::-1])) if flip else (lambda i: (-vals[i], words[i]))
    order = sorted(range(len(vals)), key=key)
    pos = [0] * len(vals)
    for place, i in enumerate(order):
        pos[i] = place
    return pos


def _N(p, s):
    """Mass-weighted centroid renormalised by available mass. Mirrors stats()."""
    tot = sum(p)
    if tot <= 0:
        return None
    return sum(a * b for a, b in zip(p, s)) / tot


def _ranks_avg(vals):
    """Average ranks, ties shared, highest value rank 1. For the correlations."""
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    out = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def _pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def _spearman(p, s):
    #: `-rank` so "probable words sit nice" is NEGATIVE in both the rank and the
    #: mass family. Flipping it would make every agreement read as a clash.
    return _pearson([-v for v in _ranks_avg(p)], s)


def _auc(p, tag):
    """P(nice word outranks naughty word). Ties count a half; chance is 0.5.

    Enumerated rather than taken from the rank-sum identity: the pole sets are
    single digits so the loop costs nothing, and the identity needs a tie
    correction that is easy to get wrong and invisible in the output.
    """
    nice = [p[i] for i in range(len(p)) if tag[i] == "nice"]
    naughty = [p[i] for i in range(len(p)) if tag[i] == "naughty"]
    if not nice or not naughty:
        return None
    return sum((1.0 if a > b else 0.5 if a == b else 0.0)
               for a in nice for b in naughty) / (len(nice) * len(naughty))


def _entropy(p):
    tot = sum(p)
    if tot <= 0:
        return None
    return -sum((q / tot) * math.log(q / tot) for q in p if q > 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="pilot2", help="run directory under results/")
    ap.add_argument("--flip-ties", action="store_true",
                    help="reverse the tie-break; the decomposition must not move")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    rundir = os.path.join(RESULTS, a.run)
    cells = [json.loads(l) for l in open(os.path.join(rundir, "cells.jsonl"))]
    man = json.load(open(os.path.join(rundir, "manifest.json")))
    print("run %s | %d cells | %d pairs%s"
          % (a.run, len(cells), len(man["pairs_run"]),
             " | TIE-BREAK FLIPPED" if a.flip_ties else ""), flush=True)

    from malignment import vectors as V
    from malignment.slots import read_items, corpora
    from malignment.slot_axis import Axis

    items = {d["item_id"]: d for _, p in corpora() for d in read_items(p)}
    prompts = sorted({c["prompt"] for c in cells})
    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    by_item = collections.defaultdict(list)
    for c in cells:
        by_item[c["item_id"]].append(c)

    out, done = [], 0
    for item_id, group in by_item.items():
        d = items.get(item_id)
        if not d:
            continue
        #: Axis once per item, as run.py does: it depends on the prompt and the
        #: poles and on nothing either checkpoint supplies.
        ax = Axis(d["prompt"], list(d["naughty"]), list(d["nice"]))
        if not ax.ok:
            continue
        per = store.get(d["prompt"]) or {}
        for c in group:
            pbm, pam = per.get(c["base"]), per.get(c["endpoint"])
            if pbm is None or pam is None:
                continue
            words = sorted(set(pbm) | set(pam))
            sc = ax.score(words)
            S = [sc[w] for w in words]
            pb = [pbm.get(w, 0.0) for w in words]
            pa = [pam.get(w, 0.0) for w in words]
            Nb, Na = _N(pb, S), _N(pa, S)
            if Nb is None or Na is None:
                continue

            rb = _ordinal(pb, words, a.flip_ties)
            ra = _ordinal(pa, words, a.flip_ties)
            vb = sorted(pb, reverse=True)
            va = sorted(pa, reverse=True)
            #: base ORDER carrying aligned MAGNITUDES, and the mirror image.
            n_sh = _N([va[rb[i]] for i in range(len(words))], S)
            n_re = _N([vb[ra[i]] for i in range(len(words))], S)

            tag = [("naughty" if w in d["naughty"]
                    else "nice" if w in d["nice"] else None) for w in words]
            rho_b, rho_a = _spearman(pb, S), _spearman(pa, S)
            auc_b, auc_a = _auc(pb, tag), _auc(pa, tag)
            eb, ea = _entropy(pb), _entropy(pa)

            total = Na - Nb
            sh = (n_sh - Nb) if n_sh is not None else None
            re = (n_re - Nb) if n_re is not None else None
            out.append({
                "item_id": item_id, "base": c["base"], "endpoint": c["endpoint"],
                "domain": c.get("domain"), "signature": c["signature"],
                "n_words": len(words),
                "N_base": Nb, "N_aligned": Na,
                "dN_total": total, "dN_sharpen": sh, "dN_reorder": re,
                "interaction": (total - sh - re) if (sh is not None and re is not None) else None,
                "dT": c.get("dT"),
                "d_entropy": (ea - eb) if (eb is not None and ea is not None) else None,
                "d_rho": (rho_a - rho_b) if (rho_b is not None and rho_a is not None) else None,
                "d_auc": (auc_a - auc_b) if (auc_b is not None and auc_a is not None) else None,
                #: Carried so the report can CHECK the recomputation against the
                #: run rather than assume two scripts agree. dN_total here and
                #: dN_position there are the same quantity by two code paths.
                "dN_position_from_run": c.get("dN_position"),
            })
            done += 1
            if done % 400 == 0:
                print("  %d cells" % done, flush=True)

    path = a.out or os.path.join(
        rundir, "mechanism_flipties.jsonl" if a.flip_ties else "mechanism.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print("\nwrote %s (%d rows)" % (path, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
