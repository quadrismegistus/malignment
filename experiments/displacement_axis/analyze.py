"""One pass over a run: cells, words, mechanism, axis share, and their nulls.

    python experiments/displacement_axis/analyze.py --out .../results/pilot3
    python experiments/displacement_axis/report.py  --run pilot3

Supersedes `run.py`, `mechanism.py` and `axis_share.py`, which each rebuilt the
per-item Axis independently. Three passes over 300 items is three sets of
embedding lookups for one question, and worse, it let the three files disagree
about which cells were in scope.

## WHY ONE FILE (RH, 2026-08-18)

Two reasons, and the second is the one that matters.

**Cost.** The Axis is a function of the prompt and the poles and of nothing a
checkpoint supplies, so it is built once per item. Doing that in three scripts
does it three times.

**Auditability.** Several results reported during the pilot2 session existed only
in shell history: the sign test, the transgressive-mass quartiles, the layered
conditional rates, the per-frame displacement consistency, and the word tables.
Numbers that live in a session and not in code are `producer-debt.md` Class 1
sub-type B -- a published number with no producer is UNAUDITABLE, which outranks
every figure in the ladder. One of them was already found wrong on re-derivation
(a churn statistic quoted from a pass that wrote no artifact and could not be
reproduced). Everything printed by `report.py` is now computed from a committed
artifact by committed code.

## WHAT IS COMPUTED, AND THE IDENTITY THAT TIES IT TOGETHER

    cells.jsonl        dN, dT, dN_position, the split components, signature,
                       per-arm N/leverage/purity, leak bounds, base pole mass
    words.jsonl        per-word p_base, p_aligned, dP, s, contribution
    mechanism.jsonl    reorder / sharpen / interaction, rank rho, pole AUC, entropy
    axis_share.jsonl   |D|, cos_theta, r2, and 24 null bisections per item
    manifest.json      the population BY ENUMERATION, plus every run parameter

`D . u` from the full 1024-dim vectors must equal `dN_position` from the scores.
The origin cancels because D is a difference of two centroids affine in one
origin. Checked per cell; the run refuses on the first failure and names it. An
assert tying a new quantity to an old one through an identity cannot pass by
being approximately right, which is worth more than a range check on either.

Tolerance is 1e-6, not 1e-9: the embeddings are float32 (eps 1.19e-07), so
order-1e-2 quantities carry ~1e-9 error by construction and 1e-9 refused a
correct run on 2026-08-18. 1e-6 is still three orders tighter than any
disagreement that would mean anything.

## THE POPULATION IS DISCOVERED AND THAT IS A HAZARD

Pairs come from `roster.endpoints()` intersected with the models present in the
source table, never from the model names alone. So the same command against the
same code returns a DIFFERENT population after every ingest, and the files open
with mode "w". Hence: one directory per run, and a refusal if the target already
holds a `manifest.json`. Compare runs by `pairs_run`, never by name or count.

`base_naughty_mass` and `base_share` are written into `cells.jsonl` because every
conditional result in the report keys on them, and recovering them later means
another full store read.
"""

import argparse
import collections
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
#: v4 because the slot corpus lives there and nowhere else. The v3 table answers
#: a query for these prompts with 2 rows of 279 -- a well-formed answer from the
#: wrong corpus, which is how this was nearly run against the wrong instrument.
TABLE = "twp_words_v4"
CELL_TABLE = "twp_cells_v4"


def signature(supp, subs, eps=1e-6):
    """Name the pattern the two components make. -> str

    Displacement puts both negative; churn within one pole puts them opposite.
    Each case verified on synthetic distributions with known mass moved.
    """
    if abs(supp) < eps and abs(subs) < eps:
        return "flat"
    if supp < 0 and subs < 0:
        return "displacement"
    if supp < 0 and abs(subs) < eps:
        return "suppression"
    if abs(supp) < eps and subs < 0:
        return "arrival"
    if (supp > 0) != (subs > 0):
        return "churn"
    return "reverse"


def _ordinal(vals, words, flip=False):
    """0-based ordinal positions, distinct for every item, deterministic on ties.

    The counterfactual pours exactly one value into each slot, so averaged ranks
    are unusable here even though they are correct for the correlations. Ties at
    the theta floor are therefore broken arbitrarily; `--flip-ties` reverses the
    secondary key so that arbitrariness is measurable rather than assumed away.
    """
    key = (lambda i: (-vals[i], words[i][::-1])) if flip else (lambda i: (-vals[i], words[i]))
    pos = [0] * len(vals)
    for place, i in enumerate(sorted(range(len(vals)), key=key)):
        pos[i] = place
    return pos


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
    #: mass family. Without it every agreement reads as a clash -- which is
    #: exactly what happened to the pole AUC on first reporting.
    return _pearson([-v for v in _ranks_avg(p)], s)


def _auc(p, tag):
    """P(nice word outranks naughty word) by probability. Ties half; chance 0.5.

    NOTE THE SIGN: nice-ward is POSITIVE here and NEGATIVE for dN_position. The
    report flips it explicitly rather than relying on anyone remembering.

    Enumerated rather than via the rank-sum identity: the pole sets are single
    digits, and the identity needs a tie correction that is easy to get wrong and
    invisible in the output.
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
    ap.add_argument("--out", required=True,
                    help="run directory; each run needs its OWN")
    ap.add_argument("--domain", default=None, help="restrict to one domain")
    ap.add_argument("--limit", type=int, default=None, help="first N items")
    ap.add_argument("--force", action="store_true",
                    help="overwrite a run directory that already holds a manifest")
    ap.add_argument("--flip-ties", action="store_true",
                    help="reverse the tie-break; aggregates must not move")
    ap.add_argument("--null-draws", type=int, default=24,
                    help="random size-matched axes per item (0 disables)")
    ap.add_argument("--head-mass", type=float, default=0.90,
                    help="mass fraction defining the 'words the model uses' pool")
    ap.add_argument("--seed", type=int, default=20260818)
    ap.add_argument("--tol", type=float, default=1e-6,
                    help="max |D.u - dN_position| tolerated before refusing")
    a = ap.parse_args(argv)

    suffix = "_flipties" if a.flip_ties else ""
    if os.path.exists(os.path.join(a.out, "manifest.json")) and not a.force:
        print("refusing: %s already holds a manifest.json. Give this run its own\n"
              "          --out, or pass --force to replace it." % a.out, file=sys.stderr)
        return 2

    import numpy as np
    from malignment import roster, vectors as V
    from malignment.slots import read_items, corpora
    from malignment.slot_axis import Axis, embed_cached, separates

    ep, unresolved = roster.endpoints()
    items = [d for _, p in corpora() for d in read_items(p) if not d.get("quarantined")]
    if a.domain:
        items = [d for d in items if (d.get("domain") or "") == a.domain]
    if a.limit:
        items = items[:a.limit]
    prompts = sorted({d["prompt"] for d in items})

    rows = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM %s WHERE prompt IN {ps:Array(String)} GROUP BY prompt, model"
                  % TABLE, ps=prompts)
    store = collections.defaultdict(dict)
    for r in rows:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))

    #: `twp_cells.total` IS the residual, verified rather than assumed: cells.total
    #: 0.24342 + summed word mass 0.75658 = 1.000000 exactly, on three checkpoints.
    #: The name reads like "total mass" and means its complement.
    cell_rows = V.rows("SELECT prompt, model, total FROM %s "
                       "WHERE prompt IN {ps:Array(String)}" % CELL_TABLE, ps=prompts)
    residual = collections.defaultdict(dict)
    for r in cell_rows:
        residual[r["prompt"]][r["model"]] = r["total"]

    have = {m for per in store.values() for m in per}
    pairs = [(b, e) for b, e in sorted(ep.items()) if b in have and e in have]
    skipped_pairs = [(b, e, "base absent" if b not in have else "endpoint absent")
                     for b, e in sorted(ep.items()) if not (b in have and e in have)]
    print("items %d | prompts %d | declared pairs %d | measurable pairs %d%s"
          % (len(items), len(prompts), len(ep), len(pairs),
             " | TIE-BREAK FLIPPED" if a.flip_ties else ""), flush=True)

    os.makedirs(a.out, exist_ok=True)
    fc = open(os.path.join(a.out, "cells%s.jsonl" % suffix), "w", encoding="utf-8")
    fw = open(os.path.join(a.out, "words%s.jsonl" % suffix), "w", encoding="utf-8")
    fm = open(os.path.join(a.out, "mechanism%s.jsonl" % suffix), "w", encoding="utf-8")
    fx = open(os.path.join(a.out, "axis_share%s.jsonl" % suffix), "w", encoding="utf-8")
    fs = open(os.path.join(a.out, "skipped%s.jsonl" % suffix), "w", encoding="utf-8")
    for b, e, why in skipped_pairs:
        fs.write(json.dumps({"kind": "pair", "base": b, "endpoint": e, "reason": why}) + "\n")

    rng = np.random.default_rng(a.seed)
    n_cells, worst = 0, 0.0
    sig = collections.Counter()
    per_pair, per_domain, cells_skipped = collections.Counter(), collections.Counter(), collections.Counter()
    items_seen, prompts_seen = set(), set()

    for d in items:
        per = store.get(d["prompt"]) or {}
        if not per:
            fs.write(json.dumps({"kind": "item", "item_id": d["item_id"],
                                 "reason": "prompt not in store"}) + "\n")
            continue
        #: **THE AXIS IS BUILT ONCE PER ITEM.** It depends on the prompt and the
        #: poles and on nothing the checkpoints supply.
        ax = Axis(d["prompt"], list(d["naughty"]), list(d["nice"]))
        if not ax.ok:
            fs.write(json.dumps({"kind": "item", "item_id": d["item_id"],
                                 "reason": "degenerate axis"}) + "\n")
            continue

        #: One embedding matrix per item over the union of EVERY arm's vocabulary,
        #: so per-cell work is arithmetic on rows already resident.
        vocab = sorted({w for m in per for w in per[m]})
        if not vocab:
            continue
        E = embed_cached(d["prompt"], vocab, True)
        idx = {w: i for i, w in enumerate(vocab)}
        u = ax.axis
        Sarr = (E - ax.origin) @ u
        S = {w: float(Sarr[i]) for i, w in enumerate(vocab)}
        #: **PYTHON FLOATS, NOT float32.** The embeddings are float32, so anything
        #: derived from `Sarr` by pure-python arithmetic (the correlations) returns
        #: numpy scalars, and `json.dumps` refuses those with a TypeError at the
        #: first write. Converting once here is cheaper than casting at each of
        #: seven call sites and cannot be forgotten at one of them.
        Slist = [float(x) for x in Sarr]
        tags = [("naughty" if w in d["naughty"]
                 else "nice" if w in d["nice"] else None) for w in vocab]

        #: NULL AXES, once per item and shared by its cells, so real and null are
        #: scored against the SAME D and each null carries one fixed orientation
        #: across the item -- which is what makes a per-item consistency figure
        #: meaningful. Two pools because they answer different objections: uniform
        #: asks whether the axis is special at all, `head` asks whether it is
        #: special beyond being built from words the model actually emits.
        n_g, n_n = len(d["naughty"]), len(d["nice"])
        pooled = collections.Counter()
        for m in per:
            for w, q in per[m].items():
                pooled[w] += q
        tot_pool = sum(pooled.values()) or 1.0
        run_mass, head_pool = 0.0, []
        for w, q in pooled.most_common():
            head_pool.append(idx[w])
            run_mass += q
            if run_mass / tot_pool >= a.head_mass:
                break
        nulls = {"uniform": [], "head": []}
        if a.null_draws and n_g + n_n <= len(vocab):
            for _ in range(a.null_draws):
                for kind, pool in (("uniform", list(range(len(vocab)))), ("head", head_pool)):
                    if len(pool) < n_g + n_n:
                        continue
                    pick = rng.choice(len(pool), n_g + n_n, replace=False)
                    A = E[[pool[i] for i in pick[:n_g]]].mean(0)
                    B = E[[pool[i] for i in pick[n_g:]]].mean(0)
                    v = A - B
                    nv = float(np.linalg.norm(v))
                    if nv > 1e-8:
                        nulls[kind].append(v / nv)

        sep_ok, gap, correct, total = separates(S, list(d["naughty"]), list(d["nice"]))
        rp = residual.get(d["prompt"]) or {}

        for b, e in pairs:
            if b not in per or e not in per:
                fs.write(json.dumps({"kind": "cell", "item_id": d["item_id"], "base": b,
                                     "endpoint": e,
                                     "reason": "prompt not measured on this arm"}) + "\n")
                cells_skipped["prompt not measured on this arm"] += 1
                continue
            pbm, pam = per[b], per[e]
            words = sorted(set(pbm) | set(pam))
            #: **PER-ARM, NOT POOLED.** An earlier draft called stats() on the mean
            #: of the two distributions, which belongs to neither checkpoint.
            stb = ax.stats(pbm, S)
            sta = ax.stats(pam, S)
            sp = ax.split(pbm, pam, S,
                          residual_pre=rp.get(b), residual_post=rp.get(e))
            supp = sp.get("suppression") or 0.0
            subs = sp.get("substitution") or 0.0
            g = signature(supp, subs)
            sig[g] += 1

            #: Base pole mass, written here because every conditional in the
            #: report keys on it and recovering it later costs a store read.
            gm = sum(pbm.get(w, 0.0) for w in d["naughty"])
            nm = sum(pbm.get(w, 0.0) for w in d["nice"])
            share = (gm / (gm + nm)) if (gm + nm) > 0 else None
            #: **THE ALIGNED POLE MASSES, WHICH THIS FILE DID NOT RECORD UNTIL
            #: 2026-08-18 AND SHOULD HAVE.** The effect size of the whole project
            #: is how much probability leaves the transgressive pole, and it was
            #: not derivable from cells.jsonl -- only dN_position was, which is a
            #: POSITION statistic and makes a large phenomenon read as -0.006.
            #: Recording both arms costs two sums and makes report.py's `mass`
            #: section computable from the artifact instead of from a store read.
            gma = sum(pam.get(w, 0.0) for w in d["naughty"])
            nma = sum(pam.get(w, 0.0) for w in d["nice"])

            dN_pos = ((sta.get("N") - stb.get("N"))
                      if (sta.get("N") is not None and stb.get("N") is not None) else None)
            fc.write(json.dumps({
                "item_id": d["item_id"], "prompt": d["prompt"],
                "domain": d.get("domain"), "matched_set": d.get("matched_set"),
                "base": b, "endpoint": e,
                "dN": sp.get("dN"), "dN_renorm": sp.get("dN_renorm"),
                "suppression": supp, "substitution": subs,
                "sign_disagree": sp.get("sign_disagree"), "signature": g,
                "base_scored_mass": sp.get("base_scored_mass"),
                "post_scored_mass": sp.get("post_scored_mass"),
                #: The aperture travels with the number: the per-cell bound is a
                #: COMPANION COLUMN beside the primary, not a footnote.
                "leak_worst": sp.get("leak_worst"),
                "leak_matched_floor": sp.get("leak_matched_floor"),
                "residual_base": rp.get(b), "residual_endpoint": rp.get(e),
                "movers": sp.get("movers"),
                "N_base": stb.get("N"), "N_aligned": sta.get("N"),
                "dN_position": dN_pos,
                "T_base": sp.get("base_scored_mass"), "T_aligned": sp.get("post_scored_mass"),
                "dT": ((sp.get("post_scored_mass") or 0) - (sp.get("base_scored_mass") or 0)),
                "leverage_base": stb.get("leverage"), "leverage_aligned": sta.get("leverage"),
                "separates": bool(sep_ok), "gap": gap,
                "purity": stb.get("purity"), "flags": stb.get("flags"),
                "n_words": len(words),
                "base_naughty_mass": gm, "base_nice_mass": nm, "base_share": share,
                "naughty_aligned": gma, "nice_aligned": nma,
            }) + "\n")

            contrib = {c["word"]: c for c in (sp.get("contributions") or [])}
            for w, c in contrib.items():
                fw.write(json.dumps({
                    "item_id": d["item_id"], "base": b, "endpoint": e, "word": w,
                    "p_base": pbm.get(w, 0.0), "p_aligned": pam.get(w, 0.0),
                    "dP": c["dP"], "s": c["s"], "contribution": c["c"],
                    "pole": ("naughty" if w in d["naughty"]
                             else "nice" if w in d["nice"] else None),
                }) + "\n")

            # ---- mechanism: reordering against sharpening -------------------
            pb = np.zeros(len(vocab))
            pa = np.zeros(len(vocab))
            for w, q in pbm.items():
                pb[idx[w]] = q
            for w, q in pam.items():
                pa[idx[w]] = q
            tb, ta = float(pb.sum()), float(pa.sum())
            if tb <= 0 or ta <= 0:
                n_cells += 1
                continue
            pbl, pal = pb.tolist(), pa.tolist()
            Nb = float(pb @ Sarr) / tb
            Na = float(pa @ Sarr) / ta
            rb = _ordinal(pbl, vocab, a.flip_ties)
            ra = _ordinal(pal, vocab, a.flip_ties)
            vb = sorted(pbl, reverse=True)
            va = sorted(pal, reverse=True)
            q_sh = np.array([va[rb[i]] for i in range(len(vocab))])
            q_re = np.array([vb[ra[i]] for i in range(len(vocab))])
            n_sh = float(q_sh @ Sarr) / float(q_sh.sum()) if q_sh.sum() > 0 else None
            n_re = float(q_re @ Sarr) / float(q_re.sum()) if q_re.sum() > 0 else None
            rho_b, rho_a = _spearman(pbl, Slist), _spearman(pal, Slist)
            auc_b, auc_a = _auc(pbl, tags), _auc(pal, tags)
            eb, ea = _entropy(pbl), _entropy(pal)
            tot_d = Na - Nb
            sh = (n_sh - Nb) if n_sh is not None else None
            re = (n_re - Nb) if n_re is not None else None
            fm.write(json.dumps({
                "item_id": d["item_id"], "base": b, "endpoint": e,
                "domain": d.get("domain"), "signature": g,
                "n_words": len(vocab),
                "N_base": Nb, "N_aligned": Na, "dN_total": tot_d,
                "dN_sharpen": sh, "dN_reorder": re,
                "interaction": (tot_d - sh - re) if (sh is not None and re is not None) else None,
                "dT": ((sp.get("post_scored_mass") or 0) - (sp.get("base_scored_mass") or 0)),
                "d_entropy": (ea - eb) if (eb is not None and ea is not None) else None,
                "d_rho": (rho_a - rho_b) if (rho_b is not None and rho_a is not None) else None,
                "d_auc": (auc_a - auc_b) if (auc_b is not None and auc_a is not None) else None,
                "dN_position_from_cells": dN_pos,
            }) + "\n")

            # ---- axis share: how much of the movement is this axis -----------
            cb = (pb @ E) / tb
            ca = (pa @ E) / ta
            D = ca - cb
            nrm = float(np.linalg.norm(D))
            proj = float(D @ u)
            err = abs(proj - tot_d)
            worst = max(worst, err)
            if err > a.tol:
                print("REFUSING: %s %s -> %s  |D.u - dN| = %.3e exceeds %.1e"
                      % (d["item_id"], b, e, err, a.tol), file=sys.stderr)
                for f in (fc, fw, fm, fx, fs):
                    f.close()
                return 1
            cos = (proj / nrm) if nrm > 0 else None
            xrow = {"item_id": d["item_id"], "base": b, "endpoint": e,
                    "domain": d.get("domain"), "signature": g,
                    "dN_position": dN_pos, "proj": proj, "norm": nrm,
                    "cos_theta": cos,
                    "r2": (cos * cos) if cos is not None else None,
                    "dT": ((sp.get("post_scored_mass") or 0) - (sp.get("base_scored_mass") or 0))}
            if cos is not None and nrm > 0:
                for kind, axes in nulls.items():
                    if not axes:
                        continue
                    signed = [float(D @ v) / nrm for v in axes]
                    cs = sorted(abs(x) for x in signed)
                    xrow["null_%s_med" % kind] = cs[len(cs) // 2]
                    xrow["null_%s_p95" % kind] = cs[int(0.95 * (len(cs) - 1))]
                    xrow["beats_%s" % kind] = sum(1 for x in cs if abs(cos) > x) / len(cs)
                    #: **SIGNS KEPT.** Summaries of |cos| answer the magnitude
                    #: question and cannot answer the direction one. "63% of cells
                    #: move nice-ward" has null 50% only if the axis orientation is
                    #: arbitrary, and ours is fixed by the author's labels.
                    if kind == "head":
                        xrow["null_head_signed"] = [round(x, 6) for x in signed]
            fx.write(json.dumps(xrow) + "\n")

            n_cells += 1
            per_pair[(b, e)] += 1
            per_domain[d.get("domain")] += 1
            items_seen.add(d["item_id"])
            prompts_seen.add(d["prompt"])
            if n_cells % 250 == 0:
                print("  %d cells" % n_cells, flush=True)

    for f in (fc, fw, fm, fx, fs):
        f.close()

    import datetime
    import subprocess
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, cwd=HERE).stdout.strip() or None
    except Exception:
        head = None
    manifest = {
        "run": os.path.basename(os.path.normpath(a.out)),
        "measured_on": datetime.date.today().isoformat(),
        "note": ("The population is FROZEN here by enumeration. Pairs are discovered by "
                 "intersecting roster.endpoints() with the models present in the source "
                 "table, so a later run against a larger store is a different population "
                 "under the same code. Compare pairs_run, not run names."),
        "source_table": TABLE, "residual_table": CELL_TABLE,
        "code_commit": head,
        "params": {"domain": a.domain, "limit": a.limit, "flip_ties": a.flip_ties,
                   "null_draws": a.null_draws, "head_mass": a.head_mass,
                   "seed": a.seed, "tol": a.tol},
        "identity_check_worst": worst,
        "declared_pairs": len(ep),
        "pairs_run": [{"base": b, "endpoint": e, "n_cells": n}
                      for (b, e), n in sorted(per_pair.items())],
        "pairs_not_run": [{"base": b, "endpoint": e, "reason": why}
                          for b, e, why in skipped_pairs],
        "n_cells": n_cells, "n_items": len(items_seen), "n_prompts": len(prompts_seen),
        "signatures": dict(sig.most_common()),
        "domains": dict(per_domain.most_common()),
        "cells_skipped": dict(cells_skipped.most_common()),
    }
    with open(os.path.join(a.out, "manifest%s.json" % suffix), "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=2) + "\n")

    print("\nidentity check: largest |D.u - dN_position| = %.2e over %d cells" % (worst, n_cells))
    print("cells %d" % n_cells)
    for k, v in sig.most_common():
        print("  %-14s %5d  %4.0f%%" % (k, v, 100.0 * v / max(n_cells, 1)))
    print("\npairs run %d of %d declared:" % (len(per_pair), len(ep)))
    for (b, e), n in sorted(per_pair.items()):
        print("  %-44s -> %-44s %4d" % (b, e, n))
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
