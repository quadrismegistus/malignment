"""The sexual-versus-neutral gradient on MATCHED lineages and a MATCHED pass. -> results/body_matched.md

    python -u body_matched.py

The paper seat, 2026-09-24, at RH's word: the draft claims the outward ordering
is about five times stronger in sexual scenes (`body.py`, median rho +0.36 on
16 prompts, 50 lineages) than in neutral ones (`body_neutral.py`, +0.07 on 10
prompts). The obvious objection is that the comparison is not like for like.
It differs in TWO ways, and this removes both:

    lineages   body.py uses all 50 endpoint pairs; the neutral battery has the
               ones that ran on this Mac. HERE: only lineages with BOTH groups.
    pass       body.py reads `movement_v4`, whose cells are the pass-1 cell
               MERGED with pass 2 (topup: sub-theta words filled in for the
               lineage union); the neutral cells have pass 1 only. HERE: both
               groups are read from the jsonl STASH, PASS 1 ONLY (topup absent),
               with `body_neutral.py`'s record choice and fold.

Same tests as `body.py` / `body_paired.py`: word-level Spearman of body_distance
against the median per-lineage delta (>= 10 carriers, >= 10 admitted words), and
the paired largest-valid-faller against largest-valid-riser count. Ruler: the
sexual_slot_en_v2 task (ratable, not a modifier, body_distance > 0). No new
rating: a word this matched read admits that no source has rated is COUNTED
and reported, not rated.

Also reported, per group: the SPREAD of body_distance among admitted words
(range, IQR, SD), because neutral candidates rarely include the genitals and a
narrower ruler range can shrink rho mechanically. And the Mann-Whitney U of the
per-prompt rhos, sexual against neutral, over prompts.

POST HOC: every per-prompt number on both groups had been seen.
"""
import collections, glob, json, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import body_neutral as BN  # noqa: E402
import body_paired as BP  # noqa: E402

MIN_CARRIERS, MIN_WORDS = 10, 10


def stash(model, prompts):
    """{prompt: {word: p}}, PASS 1 ONLY (no topup), raw frame, rule_version 4."""
    best = {}
    for f in glob.glob(os.path.join(BN.STASH, model.replace("/", "__"), "*", "jsonl.hashstash.raw", "data.jsonl")):
        for line in open(f, encoding="utf-8"):
            if '"rule_version": 4' not in line or '"topup": true' in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            p = r.get("prompt")
            if p not in prompts or r.get("topup") or not r.get("rows") or r.get("frame") not in (None, ""):
                continue
            k = (int(bool(r.get("prompt_cache"))), r.get("__written_at__", 0))
            if p not in best or k > best[p][0]:
                best[p] = (k, r)
    out = {}
    for p, (_k, r) in best.items():
        fold = collections.defaultdict(float)
        for w in r["rows"]:
            fold[w["word"]] += float(w["p"])
        out[p] = dict(fold)
    return out


def main():
    from scipy.stats import binomtest, mannwhitneyu, spearmanr
    from malignment import roster
    R = BN.ratings()
    sexual = BP.sexual_prompts(R)
    neutral = list(BN.PROMPTS)
    groups = {"SEXUAL": sexual, "NEUTRAL": neutral}
    allp = set(sexual) | set(neutral)
    eps, _ = roster.endpoints()
    S = {m: stash(m, allp) for pair in eps.items() for m in pair}
    #: a lineage enters if BOTH arms hold pass-1 cells for EVERY prompt in BOTH groups
    lin = [(b, a) for b, a in eps.items() if all(p in S[b] and p in S[a] for p in allp)]
    L = ["# Sexual against neutral on matched lineages and a matched pass", "",
         "Producer `body_matched.py` (post hoc). %d lineages hold pass-1 cells for all %d sexual and %d neutral "
         "prompts on both arms; every number below is on exactly those lineages, pass 1 only, read from the "
         "stash." % (len(lin), len(sexual), len(neutral)), ""]
    res = {}
    unrated = collections.Counter()
    for g, ps in groups.items():
        L += ["## %s" % g, "", "| prompt | word-level n | rho | p | paired hits | misses | ties | body_distance range | IQR | SD |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        res[g] = []
        for p in ps:
            d = collections.defaultdict(list)
            h = m = t = 0
            for b, a in lin:
                wb, wa = S[b][p], S[a][p]
                ws = [(w, wa.get(w, 0.0) - wb.get(w, 0.0)) for w in set(wb) | set(wa)]
                for w, x in ws:
                    d[w].append(100.0 * x)
                fl, rs = BN.sorted_sides(ws)
                f, nf = BP.walk(fl, R, p)
                r, nr = BP.walk(rs, R, p)
                unrated[g] += len(nf) + len(nr)
                if f and r:
                    x, y = R[(p, r)]["body_distance"], R[(p, f)]["body_distance"]
                    h += x > y; m += x < y; t += x == y
            car = {w: v for w, v in d.items() if len(v) >= MIN_CARRIERS}
            unrated[g] += sum(1 for w in car if (p, w) not in R)
            med = {w: st.median(v) for w, v in car.items() if BP.valid(R.get((p, w)))}
            bd = sorted(R[(p, w)]["body_distance"] for w in med)
            if len(med) >= MIN_WORDS and len(set(bd)) > 1:
                rho, pv = spearmanr([R[(p, w)]["body_distance"] for w in med], list(med.values()))
                res[g].append(rho)
                wl = "%d | %+.3f | %.2g" % (len(med), rho, pv)
            else:
                wl = "%d | -- | --" % len(med)
            q = lambda f: bd[int(f * (len(bd) - 1))] if bd else float("nan")
            L.append("| %s | %s | %d | %d | %d | %s | %s | %s |" % (
                p, wl, h, m, t, ("%d-%d" % (bd[0], bd[-1])) if bd else "--",
                ("%d-%d" % (q(0.25), q(0.75))) if bd else "--", ("%.2f" % st.pstdev(bd)) if len(bd) > 1 else "--"))
        v = res[g]
        pos = sum(x > 0 for x in v)
        L += ["", "%s: %d of %d prompts positive (sign p %.2g), median rho %+.3f. Unrated words met: %d (not rated here)."
              % (g, pos, len(v), binomtest(pos, len(v)).pvalue if v else float("nan"),
                 st.median(v) if v else float("nan"), unrated[g]), ""]
    #: RANGE RESTRICTION. Neutral candidates rarely reach the genitals, so the
    #: sexual ruler is WIDER (SD ~1.5-2.1 against ~1.1-1.4) and rho can differ
    #: mechanically. Recompute the sexual word-level rho with the low end cut
    #: off, so both groups span comparable ranges.
    for floor in (2, 3):
        rr = []
        for p in sexual:
            d = collections.defaultdict(list)
            for b, a in lin:
                wb, wa = S[b][p], S[a][p]
                for w in set(wb) | set(wa):
                    d[w].append(100.0 * (wa.get(w, 0.0) - wb.get(w, 0.0)))
            med = {w: st.median(v) for w, v in d.items() if len(v) >= MIN_CARRIERS
                   and BP.valid(R.get((p, w))) and R[(p, w)]["body_distance"] >= floor}
            bd = [R[(p, w)]["body_distance"] for w in med]
            if len(med) >= MIN_WORDS and len(set(bd)) > 1:
                rr.append(spearmanr(bd, list(med.values()))[0])
        uu = mannwhitneyu(rr, res["NEUTRAL"], alternative="two-sided")
        L.append("RANGE CHECK, sexual words with body_distance >= %d only: %d prompts testable, %d positive, "
                 "median rho %+.3f; Mann-Whitney against neutral U=%.0f, p=%.3g."
                 % (floor, len(rr), sum(x > 0 for x in rr), st.median(rr), uu.statistic, uu.pvalue))
    L.append("")
    u = mannwhitneyu(res["SEXUAL"], res["NEUTRAL"], alternative="two-sided")
    L += ["## The gradient on matched lineages", "",
          "Mann-Whitney over prompts, sexual (n=%d, median %+.3f) against neutral (n=%d, median %+.3f): U=%.0f, p=%.3g."
          % (len(res["SEXUAL"]), st.median(res["SEXUAL"]), len(res["NEUTRAL"]), st.median(res["NEUTRAL"]), u.statistic, u.pvalue)]
    open(os.path.join(HERE, "results", "body_matched.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
