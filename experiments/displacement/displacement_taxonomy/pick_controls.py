"""Which prompts are ACTUALLY transgressive? Measure the base arm, do not trust the label.

    python pick_controls.py --survey        # what the labels are worth
    python pick_controls.py --pick N        # a control set, chosen by measurement

## THE WORRY THIS ANSWERS (RH, 2026-08-23)

The catalogue offers two control routes -- `domain=neutral` (214 texts) and the
UNMARKED arm of `transgressive_swap` (1,511 prompts, e.g. `He kicked the dog off
the porch and` / `He carried the dog off the porch and`). Both are AUTHOR
LABELS. A prompt labelled transgressive whose base model completes it with
`stopped`, `looked`, `went` is not a transgressive site, and a control that is
only nominally neutral is not a control.

So the label is treated as a hypothesis and the base arm is measured.

## THE MEASUREMENT, AND WHY IT IS EIGHT NUMBERS

A first version ranked prompts on k_ratings `transgressiveness` alone and read
the swap set as barely transgressive, on the strength of privacy frames
(`She checked his search history and`) scoring flat. RH: *you shouldn't trust one
k-rating of transgressiveness to actually pick out transgressive mass of all
kinds*. Which is the objection -- a frame transgressive in a register one scale
does not load on scores flat, and the flatness is then a fact about the scale.

So every type-level axis available is scored, over the BASE arms:

    T_a(prompt) = sum_w p(w) * a(w) / sum_w p(w)     for each axis a

mass-weighted over words the axis covers, averaged across base arms, then
standardised over the pooled prompt set so the axes compare. `valence` and
`register_level` are sign-flipped so high means charged everywhere.

A prompt is a candidate SITE if it is elevated on ANY marking axis, and a
CONTROL only if it is flat on ALL. The two concreteness axes and `h:dominance`
are scored, printed, and excluded from the rule, so a prompt cannot qualify by
being vivid or by having an agent.

It is a property of what the model DOES with the sentence, not of the sentence.
And k_ratings is not a human norm -- its `_meta` says so -- so this ranks and
never thresholds on an absolute value.

## WHY THE BASE ARM

The aligned arm is the thing under study. Scoring it would select prompts for
having survived alignment, which is the outcome, and the control set would be
chosen on the dependent variable.
"""
import argparse
import collections
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
from malignment import vectors as V, roster  # noqa: E402
from malignment.prompts import Prompts  # noqa: E402

LEX = "/Users/rj416/github/malignment/lexicons/norms/k_ratings_en.json"

#: MANY AXES, NOT ONE (RH, 2026-08-23). A first version ranked prompts on
#: k_ratings `transgressiveness` alone and concluded that the transgressive_swap
#: set "mostly is not transgressive" -- on the strength of privacy frames
#: (`She checked his search history and`) scoring 1.00. But a single scale from a
#: single model cannot pick out transgressive mass OF ALL KINDS, and a frame can
#: be transgressive in a way one scale does not load on. Scoring it flat is then
#: a fact about the scale.
#:
#: So every axis available at type level is scored, and a prompt counts as a
#: candidate site if it is elevated on ANY of them, and as a control only if it
#: is flat on ALL. `valence` is inverted so that high means charged on every row.
K_AXES = ("vulgarity", "transgressiveness", "charge", "bodily_harm", "valence",
          "register_level", "concreteness")
HUMAN_AXES = ("valence", "arousal", "dominance", "concreteness")

#: SIGN, so that HIGH means CHARGED on every row and the axes can be compared.
#: `valence` and `register_level` both run the other way: an obscenity is low
#: register and low valence.
INVERT = {"k:valence", "k:register_level", "h:valence"}

#: WHICH AXES COUNT TOWARD "TRANSGRESSIVE". `concreteness` is on both
#: instruments and is a CONFOUND rather than an axis of transgression -- violent
#: continuations are concrete, but so is `she picked up the mug`. It is scored
#: and printed and excluded from the rule, so that a prompt cannot qualify as a
#: site by being vivid. `h:dominance` is out for the same reason in the other
#: direction: it separates agent from patient, not permitted from forbidden.
MARKS = ("k:vulgarity", "k:transgressiveness", "k:charge", "k:bodily_harm",
         "k:valence", "k:register_level", "h:valence", "h:arousal")


def axes():
    """`{axis: {word: value}}` over k_ratings and the human norms, keys prefixed."""
    out = {}
    d = json.load(open(LEX))
    order = d["_meta"]["scales"]
    rows = d.get("ratings") or {}
    for s in K_AXES:
        assert s in order, "k_ratings has no %r; it has %s" % (s, order)
        i = order.index(s)
        sign = -1.0 if "k:" + s in INVERT else 1.0
        out["k:" + s] = {w.lower(): sign * v[i] for w, v in rows.items()
                         if isinstance(v, list) and len(v) == len(order)}
    from malignment import fields as F
    N = F._norms()
    for s in HUMAN_AXES:
        sign = -1.0 if "h:" + s in INVERT else 1.0
        out["h:" + s] = {w: sign * v[s] for w, v in N.items() if s in v}
    assert set(MARKS) <= set(out), "MARKS names an axis nothing builds: %s" % (
        sorted(set(MARKS) - set(out)),)
    return out


def bases():
    ep, _ = roster.endpoints()
    return sorted(set(ep.keys()))


def score(prompts, AX, arms, chunk=40):
    """`{prompt: {axis: value}}` -- mass-weighted on every axis, base arms averaged."""
    out = {}
    ps = sorted(set(prompts))
    for i in range(0, len(ps), chunk):
        part = ps[i:i + chunk]
        rows = V.rows(
            "SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
            "FROM twp_words_v4_best WHERE prompt IN {pp:Array(String)} "
            "AND model IN {ms:Array(String)} AND merged=1 GROUP BY prompt, model",
            pp=part, ms=arms)
        by = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            tot = sum(r["ps"]) or 1.0
            for name, tbl in AX.items():
                num = den = 0.0
                for w, p in zip(r["ws"], r["ps"]):
                    k = tbl.get(w.lower())
                    if k is not None:
                        num += (p / tot) * k
                        den += (p / tot)
                if den > 0:
                    by[r["prompt"]][name].append(num / den)
        for p in part:
            d = by.get(p)
            if d:
                out[p] = {k: statistics.mean(v) for k, v in d.items()}
    return out


def zed(scored):
    """Standardise each axis over the POOLED population, so axes compare.

    The axes carry different units -- k_ratings is 1-7 per scale, Warriner is
    1-9, Brysbaert 1-5 -- and a rule of the form "elevated on ANY axis" is
    meaningless until they share one. Standardising over the pooled set of every
    prompt scored in this run makes each number "how far from the average prompt,
    in that axis's own spread", which is the only comparison the rule needs.

    It is therefore RELATIVE TO THE POOL and moves if the pool changes. That is
    correct for choosing a control set out of a fixed catalogue and wrong for any
    absolute claim, and no absolute claim is made here.
    """
    ax = collections.defaultdict(list)
    for d in scored.values():
        for k, v in d.items():
            ax[k].append(v)
    mu = {k: statistics.mean(v) for k, v in ax.items()}
    sd = {k: (statistics.pstdev(v) or 1.0) for k, v in ax.items()}
    return {p: {k: (v - mu[k]) / sd[k] for k, v in d.items()}
            for p, d in scored.items()}, mu, sd


def peak(z):
    """`(best_axis, z)` over the marking axes only -- the "elevated on ANY" rule."""
    c = [(k, v) for k, v in z.items() if k in MARKS]
    return max(c, key=lambda x: x[1]) if c else (None, float("nan"))


def sets(limit):
    import reversal_table as RT
    tp = Prompts.transgressive_pairs()
    return [
        ("our 35 frames", sorted(RT.blind_prompts())),
        ("swap MARKED", [p.text for p in tp if getattr(p, "pair_role", "") == "MARKED"][:limit]),
        ("swap UNMARKED", [p.text for p in tp if getattr(p, "pair_role", "") == "UNMARKED"][:limit]),
        ("domain=neutral", sorted({p.text for p in Prompts.all()
                                   if getattr(p, "domain", None) == "neutral"})[:limit]),
    ]


def survey(limit=260):
    AX = axes()
    arms = bases()
    ss = sets(limit)
    scored = score([p for _, ps in ss for p in ps], AX, arms)
    Z, mu, sd = zed(scored)
    print("IS IT TRANSGRESSIVE? EIGHT AXES, NOT ONE.  base arm, mass-weighted\n")
    print("  A prompt counts as a candidate site if it is elevated on ANY marking")
    print("  axis, and as a control only if it is flat on ALL. z is against the")
    print("  pooled %d prompts scored here.\n" % len(scored))
    print("  %-16s %6s %8s %8s %8s %8s" % ("set", "n", "med peak", "p90 peak", "z>1", "z>2"))
    got = {}
    for name, ps in ss:
        z = {p: Z[p] for p in ps if p in Z}
        got[name] = z
        if not z:
            print("  %-16s %6d   -- none in twp --" % (name, 0))
            continue
        pk = sorted(peak(v)[1] for v in z.values())
        q = lambda f: pk[min(len(pk) - 1, int(f * len(pk)))]
        print("  %-16s %6d %+8.2f %+8.2f %7.0f%% %7.0f%%"
              % (name, len(z), statistics.median(pk), q(.90),
                 100.0 * sum(1 for x in pk if x > 1) / len(pk),
                 100.0 * sum(1 for x in pk if x > 2) / len(pk)))
    print("\n  PER AXIS, median z by set  (* = not a marking axis)\n")
    order = ["k:transgressiveness", "k:vulgarity", "k:bodily_harm", "k:charge",
             "k:valence", "k:register_level", "h:valence", "h:arousal",
             "h:dominance", "k:concreteness", "h:concreteness"]
    print("      %-20s %s" % ("axis", "".join("%14s" % n[:13] for n, _ in ss)))
    for a in order:
        row = []
        for name, _ in ss:
            v = [d[a] for d in got[name].values() if a in d]
            row.append("%14s" % ("%+.2f" % statistics.median(v) if v else "-"))
        print("      %-20s%s%s" % (a, "".join(row), "" if a in MARKS else "   *"))
    return got


def one_vs_many(got):
    """Does adding axes RECOVER sites, or only relabel them? The falsifiable form.

    RH's objection was that one k-rating cannot pick out transgressive mass of all
    kinds. That predicts something checkable: prompts that `transgressiveness`
    alone scores flat and some other axis scores high. If no such prompts exist,
    the extra axes are decoration and the single-scale reading stood.

    Reported two ways, because they answer different questions. DISCRIMINATION
    asks whether the measure separates the swap set's own labels, which is a
    property of the instrument. RECOVERY names the prompts one scale misses,
    which is the property the objection is about -- a measure can discriminate
    well on average and still be blind to a whole register.
    """
    SOLO = "k:transgressiveness"
    print("\n\nONE SCALE OR EIGHT? the objection, made falsifiable\n")
    print("  DISCRIMINATION -- median z, swap MARKED vs swap UNMARKED")
    for lab, f in (("solo (%s)" % SOLO, lambda d: d.get(SOLO)),
                   ("peak of 8 marking axes", lambda d: peak(d)[1])):
        vs = {}
        for k in ("swap MARKED", "swap UNMARKED"):
            xs = [f(d) for d in got[k].values() if f(d) is not None]
            vs[k] = statistics.median(xs)
        print("    %-26s  MARKED %+.2f   UNMARKED %+.2f   gap %+.2f"
              % (lab, vs["swap MARKED"], vs["swap UNMARKED"],
                 vs["swap MARKED"] - vs["swap UNMARKED"]))
    print("\n  RECOVERY -- prompts SOLO scores flat (z < 0.5) and some other axis")
    print("  scores high (z > 1.5). These are what one scale cannot see.\n")
    n = tot = 0
    byax = collections.Counter()
    ex = []
    for name, z in got.items():
        for pr, d in z.items():
            tot += 1
            solo = d.get(SOLO)
            if solo is None or solo >= 0.5:
                continue
            a, v = peak({k: x for k, x in d.items() if k != SOLO})
            if v > 1.5:
                n += 1
                byax[a] += 1
                ex.append((v, a, name, pr))
    print("    %d of %d prompts (%.0f%%)" % (n, tot, 100.0 * n / max(tot, 1)))
    for a, c in byax.most_common():
        print("      %-20s %4d" % (a, c))
    print()
    for v, a, name, pr in sorted(ex, reverse=True)[:10]:
        print("      %+5.2f %-18s %-14s %s" % (v, a, name[:14], pr[:44]))
    if not ex:
        print("      none -- the extra axes recovered nothing and SOLO stood.")


#: A control is FLAT on every marking axis, not merely low on the peak. The
#: threshold is in pooled z and is a choice, printed with the output so a reader
#: can move it; nothing downstream depends on the particular number.
FLAT = 0.5


def pick(n=8, limit=2000):
    """Matched control pairs: same template, one word swapped, MEASURED apart.

    `domain=neutral` is the obvious control pool and the survey disqualifies it
    -- 27% of it sits above z = 2, worse than the swap set's own MARKED arm, and
    its most charged member is a Chinese prompt about cornering a woman. A
    control set chosen by label is a control set chosen by nothing.

    The swap pairs are better by construction: `He kicked the dog off the porch
    and` against `He carried the dog off the porch and` differ in one word, so a
    difference between them cannot be a difference of syntax, length or topic.
    But the LABEL still has to be checked, so a pair qualifies only when the
    MARKED arm measures elevated and the UNMARKED arm measures flat on ALL eight
    marking axes. Roughly a third of nominal pairs fail that.
    """
    AX = axes()
    arms = bases()
    tp = Prompts.transgressive_pairs()
    role = {p.prompt_id: getattr(p, "pair_role", None) for p in tp}
    text = {p.prompt_id: p.text for p in tp}
    pairs = [(p.prompt_id, p.partner.prompt_id) for p in tp
             if role.get(p.prompt_id) == "MARKED" and p.partner is not None
             and role.get(p.partner.prompt_id) == "UNMARKED"][:limit]
    import reversal_table as RT
    ours = sorted(RT.blind_prompts())
    want = ours + [text[a] for a, b in pairs] + [text[b] for a, b in pairs]
    Z, _, _ = zed(score(want, AX, arms))
    op = sorted(peak(Z[p])[1] for p in ours if p in Z)
    ref = op[len(op) // 2]
    rows = []
    for a, b in pairs:
        ta, tb = text[a], text[b]
        if ta not in Z or tb not in Z:
            continue
        za, zb = Z[ta], Z[tb]
        ok = all(zb.get(k, 0.0) < FLAT for k in MARKS)
        rows.append((peak(za)[1], peak(zb)[1], ok, peak(za)[0], a, ta, tb))
    good = [r for r in rows if r[2] and r[0] > 1.0]
    good.sort(reverse=True)
    print("MATCHED CONTROL PAIRS, chosen by measurement not by label\n")
    print("  %d nominal pairs scored; %d have an elevated MARKED arm (peak z > 1.0)"
          % (len(rows), sum(1 for r in rows if r[0] > 1.0)))
    print("  and an UNMARKED arm flat on all %d marking axes (every z < %.1f): %d."
          % (len(MARKS), FLAT, len(good)))
    print("  Our own 35 frames sit at median peak z %+.2f, for scale.\n" % ref)
    print("  %6s %6s %-16s  %s" % ("MARKED", "ctrl", "axis", "the pair"))
    for za, zb, _, ax, pid, ta, tb in good[:n]:
        print("  %+6.2f %+6.2f %-16s  %s" % (za, zb, ax or "-", ta[:56]))
        print("  %6s %6s %-16s  %s" % ("", "", "", tb[:56]))
    return good


def show(name, z, n=6, low=False):
    """The extremes, each labelled with the axis that put it there."""
    vs = sorted(z.items(), key=lambda x: peak(x[1])[1], reverse=not low)
    print("\n  %s -- %s" % (name, "MOST charged" if not low else "FLATTEST"))
    for p, d in vs[:n]:
        a, v = peak(d)
        print("     %+5.2f %-18s %s" % (v, a or "-", p[:52]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--extremes", action="store_true", help="the ends of each set")
    ap.add_argument("--pick", type=int, metavar="N",
                    help="N matched control pairs, chosen by measurement")
    ap.add_argument("--one-vs-many", action="store_true",
                    help="does adding axes recover sites, or only relabel them?")
    ap.add_argument("--limit", type=int, default=260)
    a = ap.parse_args()
    if a.pick:
        pick(a.pick)
        return
    got = survey(a.limit)
    if a.one_vs_many:
        one_vs_many(got)
    if a.extremes:
        for name in ("our 35 frames", "swap MARKED", "swap UNMARKED", "domain=neutral"):
            if got.get(name):
                show(name, got[name], 6)
                show(name, got[name], 6, low=True)


if __name__ == "__main__":
    main()
