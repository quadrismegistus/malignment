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


#: THE TAIL FRACTION. A word counts as extreme on an axis if its rating sits in
#: the top `TAIL` of that axis's own covered vocabulary, which makes the cutoff
#: comparable across instruments with different ranges without any hand-set
#: level.
TAIL = 0.05


def cuts(AX, tail=TAIL):
    """`{axis: threshold}` -- the most inclusive level still held by <= `tail` of words.

    ## A PERCENTILE ON A TIED INTEGER SCALE RETURNS THE FLOOR

    The first version took `vs[int(0.95 * n)]` and every prompt came back at
    100% transgressive mass, which is the good kind of failure: too absurd to
    ship. `k:vulgarity` rates 95% of its 27,221 words at 1, so its 95th
    percentile IS 1, and `value >= 1` admits the entire vocabulary. Three of the
    seven k scales have a median of 1 and the same defect in weaker form.

    So the threshold walks DISTINCT values downward and stops at the last level
    whose cumulative share is still within `tail`. On a scale where 4% of words
    score 2 or more that gives 2; on a continuous norm it lands where a
    percentile would. It cannot return the floor unless the floor itself is rare,
    and if no level qualifies the axis is dropped rather than admitted whole --
    an axis that cannot distinguish a tail has no tail to measure.
    """
    out = {}
    for k, tbl in AX.items():
        n = len(tbl)
        seen = collections.Counter(tbl.values())
        cum = 0
        best = None
        for v in sorted(seen, reverse=True):
            cum += seen[v]
            if cum / n > tail:
                break
            best = v
        if best is not None:
            out[k] = best
    return out


def bases():
    ep, _ = roster.endpoints()
    return sorted(set(ep.keys()))


def score(prompts, AX, arms, chunk=40, per_arm=False, CUT=None):
    """`{prompt: {axis: value}}` -- mass-weighted on every axis, base arms averaged.

    ## THE MEAN ACROSS ARMS HIDES A MINORITY OF ARMS, AND THAT IS WHAT A CONTROL
    ## HAS TO RULE OUT (2026-08-23)

    `He guided his roommate to the floor and` scored -0.06 here, the flattest of
    five prompts, and two blind raters read `Force Softened to Care` and
    `Violence softens to affection` off it. I took that for rater priming from
    the sentence. It was not: Mistral-7B-Instruct-v0.1's BASE arm puts `fucked`
    at rank 8 on that frame, with `spread`, `ripped` and `rubbed` behind it, and
    the operation has eight members.

    Both numbers are correct and they describe different things. Most of the 44
    base arms complete the frame with `sat`, `helped`, `laid`, so the MEAN is
    flat; a minority complete it sexually, so the frame is a transgressive site
    for those lineages. Averaging is the wrong summary for a control, because a
    control exists to establish that NOTHING here is a site -- an existential
    claim, which a mean cannot make.

    `per_arm=True` keeps every arm's value, so `--pick` can require flatness on
    the WORST arm rather than on the average one.

    ## AND THE MEAN IS THE WRONG STATISTIC ENTIRELY -- IT IS MASS THAT MATTERS

    Per-arm did not rescue it either: `guided`'s worst arm peaked at +1.92 and
    none of its 44 reached z = 2, while `mistralai/Mistral-7B-v0.1` puts `fucked`
    at rank 8 with 2.15% of its mass, `spread` at 1.89%, `ripped` at 1.38% --
    about 6.6% of one arm on explicit vocabulary. A mass-weighted MEAN is a
    location statistic: 6.6% at an extreme against 93% benign averages back to
    the middle, so it cannot see a minority of mass however extreme, in any arm,
    at any threshold.

    RH's phrase was `transgressive MASS of all kinds` and the mean was never a
    measure of mass. `CUT` switches the statistic to the fraction of an arm's
    probability sitting on words in the top `TAIL` of the axis's own vocabulary,
    which is the quantity the phrase names and the one a site actually has.
    """
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
                num = den = hit = 0.0
                c = CUT.get(name) if CUT else None
                for w, p in zip(r["ws"], r["ps"]):
                    k = tbl.get(w.lower())
                    if k is not None:
                        num += (p / tot) * k
                        den += (p / tot)
                        if c is not None and k >= c:
                            hit += (p / tot)
                if den > 0:
                    by[r["prompt"]][name].append(hit / den if CUT else num / den)
        for p in part:
            d = by.get(p)
            if d:
                out[p] = ({k: list(v) for k, v in d.items()} if per_arm else
                          {k: statistics.mean(v) for k, v in d.items()})
    return out


def massed(prompts, AX, CUT, arms, per_arm=False):
    """`{prompt: [worst_arm, median_arm, mean]}` of TRANSGRESSIVE MASS.

    Per arm, the largest share of that arm's probability sitting on words in the
    tail of any single marking axis; then summarised across arms. The worst arm
    comes first because it is the number a control has to satisfy: a control
    claims that no lineage treats this frame as a site, which the mean cannot
    establish however low it goes.
    """
    A = score(prompts, AX, arms, per_arm=True, CUT=CUT)
    M = [k for k in MARKS if k in CUT]
    out = {}
    for p, d in A.items():
        n = min(len(v) for v in d.values()) if d else 0
        if not n:
            continue
        per = sorted(max(d[k][i] for k in M if k in d) for i in range(n))
        out[p] = ([per[-1], per[n // 2], statistics.mean(per)] +
                  ([per] if per_arm else []))
    return out


def sets(limit):
    import reversal_table as RT
    tp = Prompts.transgressive_pairs()
    return [
        ("our blind frames", sorted(RT.blind_prompts())),
        ("swap MARKED", [p.text for p in tp if getattr(p, "pair_role", "") == "MARKED"][:limit]),
        ("swap UNMARKED", [p.text for p in tp if getattr(p, "pair_role", "") == "UNMARKED"][:limit]),
        ("domain=neutral", sorted({p.text for p in Prompts.all()
                                   if getattr(p, "domain", None) == "neutral"})[:limit]),
    ]


def survey(limit=260):
    AX = axes()
    CUT = cuts(AX)
    arms = bases()
    ss = sets(limit)
    dropped = [k for k in MARKS if k not in CUT]
    print("TRANSGRESSIVE MASS OF THE BASE ARM, by prompt set\n")
    print("  Share of an arm's probability on words in the top %.0f%% of any marking"
          % (100 * TAIL))
    print("  axis. A site puts real mass on forbidden words; a control puts none,")
    print("  ON EVERY ARM. Axes with a tail: %s."
          % ", ".join(k for k in MARKS if k in CUT))
    for k in dropped:
        #: MEASURED, NOT RECALLED. The share is why the axis has no tail, so it
        #: is derived from the table in hand rather than pinned as a literal --
        #: a number in a format string is a number that stops tracking its data.
        tbl = AX[k]
        top = max(tbl.values())
        sh = sum(1 for v in tbl.values() if v >= top) / len(tbl)
        print("  Dropped for having no tail within %.0f%%: %s -- %.0f%% of its "
              "vocabulary sits" % (100 * TAIL, k, 100 * sh))
        print("  at the single most extreme level, so no cut can isolate a tail.")
    print()
    print("  %-18s %6s %8s %8s %9s %9s"
          % ("set", "n", "mean", "median", "worst arm", "p90 worst"))
    got = {}
    for name, ps in ss:
        m = massed(ps, AX, CUT, arms)
        got[name] = m
        if not m:
            print("  %-18s %6d   -- none in twp --" % (name, 0))
            continue
        w = sorted(v[0] for v in m.values())
        mn = statistics.mean(v[2] for v in m.values())
        md = statistics.median(v[1] for v in m.values())
        print("  %-18s %6d %7.2f%% %7.2f%% %8.2f%% %8.2f%%"
              % (name, len(m), 100 * mn, 100 * md,
                 100 * statistics.median(w), 100 * w[int(.90 * (len(w) - 1))]))
    return got, AX, CUT, arms


def one_vs_many(got, AX, CUT):
    """Does mass on a second axis recover sites `transgressiveness` alone misses?"""
    SOLO = "k:transgressiveness"
    print("\n\nONE AXIS OR SEVEN? recovery under the mass statistic\n")
    arms = bases()
    n = tot = 0
    byax = collections.Counter()
    ex = []
    for name, m in got.items():
        A = score(sorted(m), AX, arms, per_arm=True, CUT=CUT)
        for pr, d in A.items():
            if SOLO not in d:
                continue
            k = min(len(v) for v in d.values())
            tot += 1
            solo = statistics.mean(d[SOLO][:k])
            other = [(a, statistics.mean(d[a][:k])) for a in MARKS
                     if a in d and a != SOLO]
            if not other:
                continue
            a, v = max(other, key=lambda x: x[1])
            if solo < 0.02 and v > 0.10:
                n += 1
                byax[a] += 1
                ex.append((v, solo, a, name, pr))
    print("  Prompts whose `transgressiveness` mass is under 2%% and whose mass on")
    print("  some other marking axis is over 10%%: %d of %d (%.0f%%)\n"
          % (n, tot, 100.0 * n / max(tot, 1)))
    for a, c in byax.most_common():
        print("      %-20s %4d" % (a, c))
    print()
    for v, solo, a, name, pr in sorted(ex, reverse=True)[:10]:
        print("      %6.1f%% on %-16s (%4.1f%% solo)  %-14s %s"
              % (100 * v, a, 100 * solo, name[:14], pr[:40]))
    if not ex:
        print("      none -- the extra axes recovered nothing and SOLO stood.")


#: A SITE puts this much mass on forbidden words, averaged over arms; a CONTROL
#: keeps its WORST arm under this much. Both are set from the measured spread of
#: the swap set rather than by fiat, and both are printed with every selection.
SITE_MIN = 0.10
CTRL_MAX = 0.05


def pick(n=8, limit=2000, emit=None):
    """Matched control pairs: same template, one word swapped, MEASURED apart.

    `domain=neutral` is the obvious control pool and the survey disqualifies it.
    The swap pairs are better by construction -- `He kicked the dog off the porch
    and` against `He carried the dog off the porch and` differ in one word, so a
    difference between them cannot be syntax, length or topic -- but the LABEL
    still has to be checked, and the check is on the worst arm, not the mean.

    Why the worst arm: `He guided his roommate to the floor and` averages 1.96%
    and its worst arm carries 11.35%, which is `mistralai/Mistral-7B-v0.1` with
    `fucked` at rank 8. Two blind raters found that subgroup and named it `Force
    Softened to Care` over eight members. A control chosen on the mean would have
    shipped it as clean.
    """
    AX = axes()
    CUT = cuts(AX)
    arms = bases()
    tp = Prompts.transgressive_pairs()
    role = {p.prompt_id: getattr(p, "pair_role", None) for p in tp}
    text = {p.prompt_id: p.text for p in tp}
    pairs = [(p.prompt_id, p.partner.prompt_id) for p in tp
             if role.get(p.prompt_id) == "MARKED" and p.partner is not None
             and role.get(p.partner.prompt_id) == "UNMARKED"][:limit]
    M = massed([text[a] for a, b in pairs] + [text[b] for a, b in pairs],
               AX, CUT, arms)
    rows = []
    for a, b in pairs:
        ta, tb = text[a], text[b]
        if ta not in M or tb not in M:
            continue
        rows.append((M[ta][2], M[tb][0], M[tb][2], ta, tb))
    good = [r for r in rows if r[0] > SITE_MIN and r[1] < CTRL_MAX]
    good.sort(reverse=True)
    print("MATCHED CONTROL PAIRS, chosen by measured MASS not by label\n")
    print("  %d nominal pairs scored. %d have a site averaging over %.0f%% "
          "transgressive" % (len(rows), sum(1 for r in rows if r[0] > SITE_MIN),
                             100 * SITE_MIN))
    print("  mass; %d have a control whose WORST arm stays under %.0f%%; %d have both."
          % (sum(1 for r in rows if r[1] < CTRL_MAX), 100 * CTRL_MAX, len(good)))
    print("  Selecting on the control's MEAN instead would admit %d, which is the"
          % sum(1 for r in rows if r[0] > SITE_MIN and r[2] < CTRL_MAX))
    print("  difference the `guided` frame cost.\n")
    print("  %8s %8s %8s   %s" % ("site", "ctrl", "ctrl", "the pair"))
    print("  %8s %8s %8s" % ("mean", "worst", "mean"))
    for sa, wb, mb, ta, tb in good[:n]:
        print("  %7.1f%% %7.2f%% %7.2f%%   %s" % (100 * sa, 100 * wb, 100 * mb, ta[:52]))
        print("  %8s %8s %8s   %s" % ("", "", "", tb[:52]))
    if emit:
        #: EMITTED, NEVER TRANSCRIBED. The table above truncates at 52 characters
        #: and six of the eight top pairs are longer than that, so reading the
        #: prompts off the display would silently run a different sentence. The
        #: runner takes this file.
        json.dump([{"site": ta, "control": tb, "site_mean": sa,
                    "ctrl_worst": wb, "ctrl_mean": mb} for sa, wb, mb, ta, tb in good[:n]],
                  open(emit, "w"), indent=1)
        print("\n  wrote %d pair(s) to %s" % (min(n, len(good)), emit))
    return good


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--pick", type=int, metavar="N",
                    help="N matched control pairs, chosen by measurement")
    ap.add_argument("--emit", metavar="PATH",
                    help="write the chosen pairs as JSON, so a runner never "
                         "transcribes a prompt off a truncated table")
    ap.add_argument("--one-vs-many", action="store_true",
                    help="does adding axes recover sites, or only relabel them?")
    ap.add_argument("--limit", type=int, default=260)
    a = ap.parse_args()
    if a.pick:
        pick(a.pick, emit=a.emit)
        return
    got, AX, CUT, arms = survey(a.limit)
    if a.one_vs_many:
        one_vs_many(got, AX, CUT)


if __name__ == "__main__":
    main()
