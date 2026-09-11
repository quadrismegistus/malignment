#!/usr/bin/env python
"""Is removal order the reverse of acquisition order? Jakobson's regression test.

    python run.py --dry        the join and the rung clock, nothing computed
    python run.py

See README.md for the design, the three hazards and the recorded predictions.

## THE TWO CLOCKS

    ACQUISITION  allenai/Olmo-3-1025-7B@stage{1,2,3}-stepN   pretraining
    REMOVAL      allenai/Olmo-3-7B-Think-SFT@stepN           SFT

**THE STAGES RESTART THEIR STEP NUMBERING and a raw step number inverts the
clock**: `stage2-step1000` comes AFTER `stage1-step1413814`. So rungs are placed
on a CUMULATIVE clock -- stage1 as-is, stage2 offset by stage1's last step,
stage3 by both -- and that clock is what `t_move` integrates against. Getting
this wrong would put most of pretraining after its own end.

## THE STATISTIC IS `t_move`, NOT AN ONSET

Copied in behaviour from `../tuning_order/timing.py`:

    t_move(w) = SUM_n  step_n * |d_n|  /  SUM_n |d_n|

the mass-weighted average step at which a word actually moved, over the
INCREMENT edges (rung n -> n+1).

**NOT a threshold crossing.** `tuning_order`'s cross-seat audit (docket [6648])
found a persistent-sign onset fires at the FIRST RUNG for 55% of sites, making a
paired lag 0 by construction -- *"the statistic times when the sign settles, not
when the mass moves."* An acquisition-order measure built that way reproduces
the artifact exactly, so this file never computes one.

## THE UNIT IS THE PROMPT

Words inside a prompt compete for the same mass and are not independent. The
correlation is computed WITHIN each prompt and the prompt is the replicate,
following `tuning_order`'s own correction.

## THE FREQUENCY CONTROL IS NOT OPTIONAL

Frequent words are acquired early and are unmarked; rare words late and marked.
So a raw negative correlation may be Zipf's law wearing Jakobson's clothes.
Every correlation is reported ALSO after partialling out `log p` at the
pretrained endpoint, and **the README records in advance that a result which
does not survive the control is a NULL, not a weakened positive.**
"""
import argparse
import collections
import math
import os
import statistics as S
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

PRE = "allenai/Olmo-3-1025-7B@%s"
SFT = "allenai/Olmo-3-7B-Think-SFT@step%d"
MIN_MOVE = 0.003          #: CANONICAL's delta, as tuning_order uses
MIN_WORDS = 8             #: per-prompt floor for a correlation
OUT = os.path.join(HERE, "results")


def rungs():
    """[(cumulative_step, model)] for the pretraining ladder, in TRAINING ORDER."""
    import re
    from malignment import vectors as V
    by = collections.defaultdict(list)
    for r in V.rows("SELECT DISTINCT model FROM twp_words "
                    "WHERE model LIKE 'allenai/Olmo-3-1025-7B@%'"):
        m = re.match(r"(stage\d)-step(\d+)", r["model"].split("@")[1])
        if m:
            by[m.group(1)].append((int(m.group(2)), r["model"]))
    out, offset = [], 0
    for st in ("stage1", "stage2", "stage3"):
        v = sorted(by.get(st, []))
        for step, model in v:
            out.append((offset + step, model))
        if v:
            offset += v[-1][0]
    return out


def acquisition(prompts):
    """{(prompt, word): t_move} on the pretraining ladder, cumulative clock."""
    from malignment import vectors as V
    rg = rungs()
    num = collections.defaultdict(float)
    den = collections.defaultdict(float)
    prev = None
    for cum, model in rg:
        cur = collections.defaultdict(dict)
        for i in range(0, len(prompts), 50):
            for r in V.rows("SELECT prompt, word, p FROM twp_words "
                            "WHERE model={m:String} AND prompt IN {ps:Array(String)}",
                            m=model, ps=prompts[i:i + 50]):
                cur[r["prompt"]][r["word"]] = r["p"]
        if prev is not None:
            for p, wd in cur.items():
                a = prev.get(p, {})
                for w in set(wd) | set(a):
                    d = abs(wd.get(w, 0.0) - a.get(w, 0.0))
                    if d > 0:
                        num[(p, w)] += cum * d
                        den[(p, w)] += d
        prev = cur
    return ({k: num[k] / den[k] for k in den if den[k] >= MIN_MOVE},
            prev, len(rg))


def removal(prompts):
    """{(prompt, word): t_move} on the SFT ladder, from movement_rungs."""
    from malignment import ch
    from malignment.ch import _lit
    ps = ",".join(_lit(p) for p in prompts)
    q = ("SELECT prompt, word, "
         "sum(step_aligned * abs(delta)) / sum(abs(delta)) AS t_move, "
         "sum(abs(delta)) AS tv "
         "FROM {db}.movement_rungs WHERE kind='increment' "
         "AND prompt IN (%s) GROUP BY prompt, word HAVING tv >= %f"
         % (ps, MIN_MOVE))
    return {(r["prompt"], r["word"]): float(r["t_move"]) for r in ch.query(q)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--prompts", type=int, default=400)
    a = ap.parse_args(argv)
    import numpy as np
    from scipy import stats
    from malignment import vectors as V

    rg = rungs()
    print("pretraining ladder: %d rungs, cumulative clock %d .. %d"
          % (len(rg), rg[0][0], rg[-1][0]))
    for st in ("stage1", "stage2", "stage3"):
        v = [c for c, m in rg if st in m]
        if v:
            print("   %-8s %2d rungs, cumulative %d .. %d" % (st, len(v), min(v), max(v)))
    #: the prompts every rung of BOTH ladders carries
    sets = []
    for _, m in [rg[0], rg[len(rg) // 2], rg[-1]] + [(0, SFT % 1000), (0, SFT % 43000)]:
        sets.append({r["prompt"] for r in V.rows(
            "SELECT prompt FROM twp_words WHERE model={m:String} GROUP BY prompt", m=m)})
    shared = sorted(set.intersection(*sets))
    print("prompts shared across both ladders: %d" % len(shared))
    if len(shared) > a.prompts:
        shared = shared[:a.prompts]
        print("   using the first %d" % a.prompts)
    if a.dry:
        return 0

    acq, last, nr = acquisition(shared)
    rem = removal(shared)
    print("\nwords with t_move on BOTH ladders: %d" % len(set(acq) & set(rem)))

    #: per-prompt Spearman, raw and with log p partialled out
    byp = collections.defaultdict(list)
    for k in set(acq) & set(rem):
        p, w = k
        f = last.get(p, {}).get(w)
        if f and f > 0:
            byp[p].append((acq[k], rem[k], math.log(f)))
    raw, part = [], []
    for p, v in byp.items():
        if len(v) < MIN_WORDS:
            continue
        x = np.asarray([t[0] for t in v]); y = np.asarray([t[1] for t in v])
        f = np.asarray([t[2] for t in v])
        if np.std(x) == 0 or np.std(y) == 0:
            continue
        raw.append(stats.spearmanr(x, y).statistic)
        if np.std(f) > 0:
            xr = x - np.polyval(np.polyfit(f, x, 1), f)
            yr = y - np.polyval(np.polyfit(f, y, 1), f)
            if np.std(xr) > 0 and np.std(yr) > 0:
                part.append(stats.spearmanr(xr, yr).statistic)
    def report(name, v):
        if not v:
            print("%-28s no usable prompts" % name); return
        up = sum(1 for x in v if x > 0); dn = sum(1 for x in v if x < 0)
        n = up + dn
        k = min(up, dn)
        pv = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
        print("%-28s n=%4d  median rho %+.4f  %4d up / %-4d dn  p=%.3g"
              % (name, len(v), S.median(v), up, dn, pv))
    print()
    print("PREDICTION: regression HOLDS if rho is NEGATIVE -- late-acquired words")
    print("leave early -- AND the sign survives the frequency control.")
    print()
    report("raw", raw)
    report("log-p partialled out", part)
    os.makedirs(OUT, exist_ok=True)
    import json
    json.dump(dict(n_rungs=nr, n_prompts=len(shared),
                   n_words=len(set(acq) & set(rem)),
                   raw_median=S.median(raw) if raw else None,
                   partial_median=S.median(part) if part else None,
                   raw_n=len(raw), partial_n=len(part)),
              open(os.path.join(OUT, "run.json"), "w"), indent=1)
    print("\n-> results/run.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
