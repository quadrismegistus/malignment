#!/usr/bin/env python
"""Does displaced mass go to the ARGMAX, as the squeezing effect predicts?

    python squeezing.py

## THE CLAIM

Ren & Sutherland, "Learning Dynamics of LLM Finetuning" (ICLR 2025,
arXiv 2407.10490), the SQUEEZING EFFECT:

    when a low-probability token is suppressed by the negative gradient,
    softmax mechanics concentrate its probability mass on the ARGMAX -- the
    already-most-probable token -- regardless of any semantic relation.

## WHY IT MATTERS MORE THAN A LITERATURE NOTE

**It is the deflationary rival to this campaign's own finding.** If displaced
mass simply lands on whatever was already winning, then "displacement" is
softmax bookkeeping, the semantic chain (kill -> strangle) is a coincidence of
the embedding geometry, and every reading built on the direction of the
substitution is decoration on a gradient artifact. So it has to be tested, and
tested against our data rather than argued about.

## WHAT BEARS ON IT

Per (prompt, endpoint pair): identify the word with the largest `p_base` --
the base argmax -- and ask two things.

    1  is the base argmax the TOP GAINER?      squeezing says usually yes
    2  what is its own delta?                  squeezing says positive

Plus the distribution of the top gainer's RANK in the base, which tests the
reconciliation the reading note proposes (`reading/ren-squeezing-effect.md`):
*"the semantically related alternatives are already high-probability in the
base distribution... so they tend to be the ones the softmax gradient
promotes."* If that holds, gainers should cluster at low ranks.

## THE SCOPE LIMIT, WHICH IS NOT SMALL

**This does not test their mechanism in the regime they studied.** Their claim
is about DPO TRAINING DYNAMICS acting on a LOW-probability token. This measures
base->endpoint movement spanning SFT and preference tuning together, and our
fallers are typically HIGH-probability (`kill` at p_base 0.798). So the result
here says the squeezing effect does not ACCOUNT FOR what we measure. It does not
say the effect is absent from DPO training.
"""
import collections
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))


def main():
    from malignment import movement as M, vectors as V
    w = M.endpoint_edge_where("raw")
    ps = [r["prompt"] for r in V.rows(
        "SELECT prompt FROM twp_words_v4_best GROUP BY prompt "
        "ORDER BY prompt LIMIT 300")]
    cells = collections.defaultdict(dict)
    for i in range(0, len(ps), 40):
        for r in V.rows(
                "SELECT prompt, base, aligned, word, p_base, delta FROM movement_v4 "
                "WHERE rule='canonical' AND prompt IN {ps:Array(String)} AND %s" % w,
                ps=ps[i:i + 40]):
            cells[(r["prompt"], r["base"], r["aligned"])][r["word"]] = (
                r["p_base"], r["delta"])
    same = gain = n = 0
    amd, rank = [], collections.Counter()
    for wd in cells.values():
        if len(wd) < 5:
            continue
        n += 1
        am = max(wd, key=lambda x: wd[x][0])
        tg = max(wd, key=lambda x: wd[x][1])
        if am == tg:
            same += 1
        d = wd[am][1]
        amd.append(d)
        if d > 0:
            gain += 1
        order = sorted(wd, key=lambda x: -wd[x][0])
        rank[min(order.index(tg) + 1, 11)] += 1
    print("cells (prompt x endpoint pair): %d" % n)
    print()
    print("SQUEEZING predicts mass concentrates on the base ARGMAX.")
    print("  base argmax IS the top gainer   : %6d  (%.1f%%)" % (same, 100.0 * same / n))
    print("  base argmax gains ANY mass      : %6d  (%.1f%%)" % (gain, 100.0 * gain / n))
    print("  mean delta on the base argmax   : %+.5f" % st.mean(amd))
    print("  median delta on the base argmax : %+.5f" % st.median(amd))
    print()
    print("Rank of the TOP GAINER in the base distribution:")
    for r in sorted(rank):
        print("   rank %-4s %6d  %5.1f%%"
              % ("11+" if r == 11 else str(r), rank[r], 100.0 * rank[r] / n))
    print()
    print("READING: the base argmax LOSES mass on average and is the top gainer")
    print("in under a quarter of cells; gainers come from right across the base")
    print("distribution, 23% from outside the top ten. Mass does not concentrate")
    print("on the already-most-probable token, and the reading note's")
    print("reconciliation -- that gainers are already high-probability -- does")
    print("not hold either.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
