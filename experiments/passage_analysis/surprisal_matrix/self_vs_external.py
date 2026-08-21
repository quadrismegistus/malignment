"""Does alignment lower entropy from the model's OWN view, or only an outsider's?

    python .../self_vs_external.py

RH, 2026-08-21: *"everyone talks about how alignment reduces entropy, but do they
generally mean entropy from its own POV... it seems stranger that it would also
reduce entropy for an external observer."*

Two different quantities, routinely run together:

    SELF        the generator's surprisal at its OWN output. Close to the
                model's entropy rate: how few options it was choosing among.
                What "RLHF reduces entropy / diversity collapse" usually means.
    EXTERNAL    a THIRD PARTY's surprisal at that output. A claim about the
                TEXT, in which the generating model does not appear. What this
                folder measures with deepseek, and what machine-text detection
                measures with a proxy model.

They are coupled but not identical, and `ogden_axes.py` already shows them
coming apart in the other direction: Basic English restricts options to 850
words -- maximal narrowing -- and RAISES external surprisal on 47 of 47 pairs.
Narrowing your own options does not entail becoming predictable to someone else.

## THE 2x2 THAT SEPARATES THEM

`malign_logits.gen_scores` scores every passage under TWO models: the generator
itself and its lineage partner. So for each lineage:

                        scored by BASE      scored by ALIGNED
    base output          self(base)          cross(base->aligned)
    aligned output       cross(aligned->base) self(aligned)

    self(aligned) - self(base)   does alignment narrow its OWN view?
    external (deepseek)          does the text get more predictable to an outsider?

**And the off-diagonal is the sharper test, but only in EXCESS form.** If
alignment narrows the distribution, base output should be costly to the aligned
model (the base explores regions alignment suppressed) while aligned output is
cheap to the base (it lies inside the broader distribution).

The raw comparison `cross(b->a) - cross(a->b)` does NOT isolate that, and it is
reported here marked as confounded: base output is higher-entropy text in the
first place, so it costs more to read whoever reads it. The statistic that
separates the two is each scorer's EXCESS over the text's own generator --
`cross - self` on the same text, which is a one-sided KL-like quantity -- and
then the difference of those two excesses. That asks how much extra each model
pays for the OTHER's text, having already priced the text's own entropy out.

A symmetric excess would mean the arms differ in WHERE they put mass, not in
HOW MUCH they concentrate it.

## UNITS, AND WHY BITS PER TOKEN IS LEGITIMATE HERE

Across scorers with different tokenizers, bits/token is not comparable and
bits/byte would be required. Within a lineage it IS comparable, and that was
checked rather than assumed: **219,170 of 220,258 f11_l2 passages (99.51%) get
an identical token count from both scorers.** The roster's rule that an arm pair
shares a tokenizer holds.

The 1,088 that disagree are dropped and counted. They are not tokenizer noise --
mean gap 72 to 92 tokens on 256-token passages, confined to four models
(Qwen2.5-0.5B and Olmo-3 lineages), so a truncation or text-version mismatch
rather than a boundary effect. Averaging them in would mix two different
passages under one key.

Deepseek's bits/token is on a THIRD tokenizer and so is comparable in DIRECTION
only, never in level, against the self and cross columns. It is reported in its
own column for that reason and no difference is taken across the two.
"""

import argparse, collections, csv, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
LN2 = math.log(2)


def sign_test(d):
    v = [x for x in d if x != 0]
    n, up = len(v), sum(1 for x in v if x > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    return n, up, n - up, statistics.median(v), min(
        1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="f11_l2")
    ap.add_argument("--min-passages", type=int, default=20)
    a = ap.parse_args(argv)
    os.environ["MALIGNMENT_CH_DB"] = "malign_logits"
    from malignment import ch, roster

    #: one row per (model, scorer): median bits/token over that model's
    #: passages, restricted to passages where BOTH scorers agree on n.
    rows = ch.query("""
        SELECT model, scorer, count() n_pass,
               round(median(bpt), 6) AS bpt
        FROM (
          SELECT g.model AS model, g.scorer AS scorer,
                 -arraySum(g.logprobs) / g.n / %f AS bpt
          FROM {db}.gen_scores g
          INNER JOIN (
            SELECT model, prompt, sample_idx FROM {db}.gen_scores
            WHERE corpus = '%s' AND scorable = 1
            GROUP BY model, prompt, sample_idx
            HAVING count() = 2 AND min(n) = max(n)
          ) k ON g.model = k.model AND g.prompt = k.prompt
                 AND g.sample_idx = k.sample_idx
          WHERE g.corpus = '%s' AND g.scorable = 1 AND g.n > 0
        )
        GROUP BY model, scorer
    """ % (LN2, a.corpus, a.corpus))
    by = collections.defaultdict(dict)
    npass = {}
    for r in rows:
        by[r["model"]][r["scorer"]] = r["bpt"]
        npass[(r["model"], r["scorer"])] = r["n_pass"]
    print("corpus %s | %d (model, scorer) cells" % (a.corpus, len(rows)))

    lin = roster.lineages()
    out = []
    for base, members in sorted(lin.items()):
        for al in [m for m in members if m != base]:
            b, A = by.get(base, {}), by.get(al, {})
            need = (b.get(base), b.get(al), A.get(al), A.get(base))
            if any(x is None for x in need):
                continue
            if min(npass.get((base, base), 0), npass.get((al, al), 0)) < a.min_passages:
                continue
            out.append(dict(base=base, aligned=al,
                            self_b=b[base], cross_b_to_a=b[al],
                            self_a=A[al], cross_a_to_b=A[base]))
    print("lineage pairs with the full 2x2: %d\n" % len(out))
    if not out:
        return

    print("MEDIAN OF THE 2x2 OVER %d PAIRS   (bits/token, within-lineage "
          "tokenizer)" % len(out))
    print("%-22s %14s %14s" % ("", "scored by BASE", "scored by ALIGNED"))
    print("%-22s %14.4f %14.4f" % ("base output",
          statistics.median(x["self_b"] for x in out),
          statistics.median(x["cross_b_to_a"] for x in out)))
    print("%-22s %14.4f %14.4f" % ("aligned output",
          statistics.median(x["cross_a_to_b"] for x in out),
          statistics.median(x["self_a"] for x in out)))

    print("\nTHE TESTS, paired within lineage, sign test")
    print("%-46s %9s %5s %5s %10s" % ("", "median", "up", "dn", "p"))
    tests = [
        ("SELF: aligned at its own output - base at its own",
         lambda x: x["self_a"] - x["self_b"]),
        ("EXCESS on base output: cross(b->a) - self(b)",
         lambda x: x["cross_b_to_a"] - x["self_b"]),
        ("EXCESS on aligned output: cross(a->b) - self(a)",
         lambda x: x["cross_a_to_b"] - x["self_a"]),
        ("ASYMMETRY of those two excesses",
         lambda x: (x["cross_b_to_a"] - x["self_b"])
                   - (x["cross_a_to_b"] - x["self_a"])),
        ("raw off-diagonal cross(b->a) - cross(a->b)  <- CONFOUNDED",
         lambda x: x["cross_b_to_a"] - x["cross_a_to_b"]),
    ]
    for lab, f in tests:
        if f is None:
            print("%-46s" % lab); continue
        n, up, dn, med, p = sign_test([f(x) for x in out])
        print("%-46s %+9.4f %5d %5d %10.3g" % (lab, med, up, dn, p))

    #: THE COMPARISON RH ASKED FOR. External is on a different tokenizer, so
    #: only its SIGN is put beside these -- never a difference between them.
    print("\nAGAINST THE EXTERNAL OBSERVER (deepseek, arm_paired.py, 22 lineages)")
    print("  external surprisal, aligned - base:  -0.8435 bits/token  (22/22 down)")
    print("  deepseek is a THIRD tokenizer, so that number is comparable to the")
    print("  rows above in DIRECTION only. No difference is taken across them.")
    print("\nIf SELF falls and EXTERNAL falls, the two claims coincide here and")
    print("the literature's conflation is harmless on this corpus. If SELF is")
    print("flat or rises while EXTERNAL falls, they are different claims and only")
    print("the external one is ours -- which is what ogden_axes.py already showed")
    print("in the opposite direction, where maximal narrowing RAISED external")
    print("surprisal on 47 of 47 pairs.")


if __name__ == "__main__":
    main()
