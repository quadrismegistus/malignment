"""Which step carries the move? One sign per lineage, then a sign test.

    ~/github/lltk/.venv/bin/python .../ladder_signs.py
    ... --min-n 25 --col usas_x

**Run in the LLTK venv** -- the scorer needs `lltk.tools.constants`.

## THE LINEAGE IS THE UNIT, WHICH IS WHY n=50 ON ONE STEM IS ENOUGH

Per-lineage magnitudes do not resolve at this n and are not asked to. The 1B
OLMo ladder resolved its SFT step (+0.0275, CI [+0.0110, +0.0446]); smol3
resolved nothing, which its size predicts. Both are usable observations of a
SIGN. The test is over lineages, and needs each to be unbiased, not significant.

## THE POPULATION COMES FROM THE STASH, NOT FROM THE SWEEP PLAN

They are different stores and they disagree. `OLMo-2-0425-1B` has 150 passages
per rung generated this morning and its SFT/DPO weights are no longer in the
HF cache, so the sweep skips it while the analysis can still use it. Reading the
plan instead of the stash would silently drop the lineage where the effect is
largest and the only one whose SFT step resolved with intervals.

## WHAT A SIGN IS HERE

For each lineage with a base, an SFT rung and a later rung, two deltas:

    sft_step   = median(SFT)  - median(base)
    pref_step  = median(last) - median(SFT)

and the sign asks which is larger in absolute terms -- SFT_CARRIES if
|sft_step| > |pref_step|. That is the question Findings U answered for
displacement ("SFT does the cutting"), asked of abstraction and interiority.

**The second step is NOT one operation.** Across these lineages it is dpo,
rlhf, rlvr, apo, distill_align, or a second sft. They are reported by op as
well as pooled, because pooling them as "the preference stage" is an undeclared
choice about which operations are the same kind of thing.

Sign convention: `rh_absconc_median` is HIGH = CONCRETE, so alignment's
direction is NEGATIVE. `usas_x` is higher = more interior.
"""

import argparse, collections, math, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")

STEM = "He was beautiful and disgusting and she wanted to"
PAT = re.compile(r"<think>|</think>|How can I assist|the user (said|provided|might)"
                 r"|I need to respond|let me (try|start)", re.I)


def ascii_share(t):
    return sum(1 for c in t if ord(c) < 128) / max(len(t), 1)


def sign_test(diffs):
    v = [x for x in diffs if x != 0]
    n = len(v)
    if not n:
        return 0, 0, float("nan"), 1.0
    up = sum(1 for x in v if x > 0)
    p = min(1.0, sum(math.comb(n, k)
                     for k in range(0, min(up, n - up) + 1)) * 2 / 2 ** n)
    return n, up, st.median(v), p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", default=STEM)
    ap.add_argument("--min-n", type=int, default=25)
    ap.add_argument("--min-words", type=int, default=60)
    ap.add_argument("--cols", nargs="*",
                    default=["rh_absconc_median", "usas_x"])
    a = ap.parse_args(argv)
    from malignment import Checkpoint
    from ladder_sweep import plan
    from measure_lltk import Scorer

    S = Scorer()
    rows = plan(2)
    bylin = collections.defaultdict(list)
    for m, prof, base, role in rows:
        bylin[base].append((m, role))

    scored, skipped = {}, []
    for base, nodes in sorted(bylin.items()):
        got = {}
        for m, role in nodes:
            ts = [getattr(p, "text", "") or ""
                  for p in Checkpoint(m).generations(prompt=a.stem, frame="raw")]
            ts = [t for t in ts if len(t.split()) >= a.min_words
                  and ascii_share(t) >= 0.995]
            if len(ts) < a.min_n:
                continue
            vals = collections.defaultdict(list)
            think = 0
            for t in ts:
                think += bool(PAT.search(t))
                r = S.score(t)
                if r:
                    for c in a.cols:
                        if r.get(c) is not None:
                            vals[c].append(r[c])
            got[role] = dict(n=len(ts), think=think / len(ts), model=m,
                             **{c: st.median(v) for c, v in vals.items() if v})
        #: a lineage needs base, an sft rung and a LATER rung to decompose.
        #: Named when it does not, because a quietly shorter population is the
        #: thing this whole sweep exists to prevent.
        later = [r for r in got if r not in ("base", "sft", "sft_ablation")]
        if "base" in got and "sft" in got and later:
            scored[base] = (got, later)
        else:
            skipped.append((base, sorted(got)))

    print("%d lineages scored, %d incomplete in the stash" % (len(scored), len(skipped)))
    for b, have in skipped:
        print("    %-32s has %s" % (b.split("/")[-1][:32], ", ".join(have) or "nothing"))

    for col in a.cols:
        print("\n=== %s ===" % col)
        print("  %-26s %-9s %9s %9s   %s"
              % ("lineage", "pref op", "sft step", "pref step", "carried by"))
        diffs = []
        byop = collections.defaultdict(list)
        for b, (got, later) in sorted(scored.items()):
            op = sorted(later, key=lambda r: ("rlvr" in r, r))[-1]
            if col not in got["base"] or col not in got["sft"] or col not in got[op]:
                continue
            sftd = got["sft"][col] - got["base"][col]
            prefd = got[op][col] - got["sft"][col]
            who = "SFT" if abs(sftd) > abs(prefd) else "pref"
            diffs.append(abs(sftd) - abs(prefd))
            byop[op].append(abs(sftd) - abs(prefd))
            print("  %-26s %-9s %+9.4f %+9.4f   %s"
                  % (b.split("/")[-1][:26], op, sftd, prefd, who))
        if diffs:
            n, up, med, p = sign_test(diffs)
            print("  SIGN TEST |sft| > |pref| : %d of %d lineages, p=%.4g" % (up, n, p))
            for op, d in sorted(byop.items()):
                nn, uu, _, _ = sign_test(d)
                print("      %-12s %d of %d" % (op, uu, nn))


if __name__ == "__main__":
    main()
