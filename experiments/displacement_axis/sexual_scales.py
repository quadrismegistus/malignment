"""Does the sexual instrument explain sexual frames that v6 cannot?

    python experiments/displacement_axis/sexual_scales.py --splits 40

WHY THIS EXISTS. `variance_repeated.py` reported the sexual domain at -0.007
median held-out R2 -- nothing explained by anything, including the embedding --
and I wrote that up as "sexual is unexplained". RH asked how that could be true
of `She slowly took off her`, which is X_metonymy's own scene, where an in-context
intimacy instrument reaches rho -0.53 to -0.66.

Two things were wrong with the claim, and only the second is interesting:

  a THAT FRAME IS UNMEASURABLE THERE, NOT UNEXPLAINED. It carries 8 lineages in
    twp_words_v4_best against 50 in `movement`, and its split-half CEILING is
    0.029. Half A of four lineages does not predict half B of four. No model can
    explain an outcome that does not replicate, so the frame contributes a near-
    zero to every row including the ceiling.

  b v6 HAS NO SCALE FOR WHAT MOVES IN A SEXUAL FRAME. Its twelve are harm,
    aggression, directedness, makes_better/worse, interiority, deliberation,
    superego, vocalisation, hedged, fit, mundanity. X's result used intimacy,
    exposure-on-removal, sexual charge and body zone. So the sexual row measured
    v6's blind spot and I reported it as a property of the frames.

THE TEST. `sexual_slot_en_v2` has the missing dimensions and was already run on
16 gender-paired frames; 14 of them are in pilot3 at 20 lineages each. On exactly
those frames, with exactly the same words, splits, seed and ridge, put the two
scale sets head to head against each other, against the embedding, and against
the ceiling.

IDENTICAL WORD SETS ARE THE WHOLE POINT. A word enters only if v6 rated it, v2
rated it, it is embeddable and it appears in words.jsonl. Comparing 9 scales over
their words against 12 over theirs is the error this file exists to avoid making
a fourth time.
"""

import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
RES = os.path.join(HERE, "results", "pilot3")
SEX = os.path.join(REPO, "experiments", "slot_ratings", "sexual", "results")

#: The nine numeric scales of sexual_slot_en_v2. zone_kind and referent_kind are
#: categorical and left out rather than one-hot encoded: they would add ~8 free
#: parameters to a 9-column design over ~130 words and win on flexibility alone.
S2 = ["orality", "tactility", "genitality", "incorporation", "body_distance",
      "exposure", "charge", "euphemism", "explicitness"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--rho", action="store_true",
                    help="score the same frames with the X_metonymy estimator instead")
    a = ap.parse_args(argv)
    if a.rho:
        return rho()
    import numpy as np, random, yaml
    from malignment import slot_axis as SA
    from axis_variants import ratings

    v6, _ = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})

    sx = collections.defaultdict(dict)
    for r in json.load(open(os.path.join(SEX, "rated_gender_pairs_v2.json")))["rows"]:
        if r.get("ratable") is False:
            continue
        if all(isinstance(r.get(s), (int, float)) for s in S2):
            sx[r["prompt"]][r["word"]] = {s: float(r[s]) for s in S2}

    poles = {}
    for f in glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml")):
        for it in (yaml.safe_load(open(f, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("naughty"):
                poles[it["prompt"]] = (list(it["naughty"]), list(it["nice"]))

    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    _cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    item_of = {c["prompt"]: c["item_id"] for c in _cl}

    def r2(X, ya, yb):
        Xd = np.c_[np.ones(len(X)), X]
        lam = 1e-3 * np.trace(Xd.T @ Xd) / Xd.shape[1]
        b = np.linalg.solve(Xd.T @ Xd + lam * np.eye(Xd.shape[1]), Xd.T @ ya)
        pr = Xd @ b
        tot = ((yb - yb.mean()) ** 2).sum()
        return 1 - ((yb - pr) ** 2).sum() / tot if tot > 0 else np.nan

    rng = random.Random(a.seed)
    MODELS = ["ceiling", "sex9", "v6_12", "both21", "sex_best1", "v6_best1",
              "bge_pcs", "bge_axis"]
    rows = []
    for p in sorted(sx):
        item = item_of.get(p)
        if not item or item not in cells or p not in v6:
            continue
        L = sorted(cells[item])
        if len(L) < 8:
            continue
        allw = sorted({w for l in L for w in cells[item][l]})
        #: the identical-set rule, enforced once, here
        ok = [w for w in allw
              if w in sx[p] and w in v6[p] and all(s in v6[p][w] for s in S6)]
        if len(ok) < 40:
            continue
        try:
            E = SA.embed_cached(p, ok)
        except Exception:
            continue
        Ec = E - E.mean(0)
        PC = Ec @ np.linalg.svd(Ec, full_matrices=False)[2][:10].T
        ax = None
        if p in poles:
            idx = {w: i for i, w in enumerate(ok)}
            P1 = [E[idx[w]] for w in poles[p][0] if w in idx]
            P2 = [E[idx[w]] for w in poles[p][1] if w in idx]
            if len(P1) >= 2 and len(P2) >= 2:
                u = np.mean(P1, 0) - np.mean(P2, 0)
                ax = (E @ (u / (np.linalg.norm(u) or 1))).reshape(-1, 1)
        R2m = np.array([[sx[p][w][s] for s in S2] for w in ok], float)
        R6 = np.array([[v6[p][w][s] for s in S6] for w in ok], float)

        per = collections.defaultdict(list)
        nm = {"sex": [], "v6": []}
        for _ in range(a.splits):
            sh = list(L); rng.shuffle(sh)
            h = len(sh) // 2
            def net(sub):
                n = collections.Counter()
                for l in sub:
                    for w, dp in cells[item][l].items():
                        n[w] += 1 if dp > 0 else (-1 if dp < 0 else 0)
                return n
            na, nb = net(sh[:h]), net(sh[h:])
            ya = np.array([na[w] for w in ok], float)
            yb = np.array([nb[w] for w in ok], float)
            if ya.std() == 0 or yb.std() == 0:
                continue
            per["sex9"].append(r2(R2m, ya, yb))
            per["v6_12"].append(r2(R6, ya, yb))
            per["both21"].append(r2(np.c_[R2m, R6], ya, yb))
            per["bge_pcs"].append(r2(PC, ya, yb))
            if ax is not None:
                per["bge_axis"].append(r2(ax, ya, yb))
            s2 = [r2(R2m[:, [i]], ya, yb) for i in range(len(S2))]
            s6 = [r2(R6[:, [i]], ya, yb) for i in range(len(S6))]
            per["sex_best1"].append(np.nanmax(s2)); nm["sex"].append(S2[int(np.nanargmax(s2))])
            per["v6_best1"].append(np.nanmax(s6)); nm["v6"].append(S6[int(np.nanargmax(s6))])
            b = np.polyfit(ya, yb, 1)
            per["ceiling"].append(1 - ((yb - np.polyval(b, ya)) ** 2).sum()
                                  / ((yb - yb.mean()) ** 2).sum())
        if len(per["ceiling"]) < a.splits // 2:
            continue
        r = dict(prompt=p, item=item, n_words=len(ok), n_lineages=len(L),
                 n_splits=len(per["ceiling"]))
        for k, v in nm.items():
            c = collections.Counter(v)
            r[k + "_name"] = c.most_common(1)[0][0] if c else None
            r[k + "_name_share"] = c.most_common(1)[0][1] / len(v) if v else None
        for m in MODELS:
            v = [x for x in per[m] if x == x]
            if v:
                r["mean_" + m] = float(np.mean(v)); r["sd_" + m] = float(np.std(v))
        rows.append(r)

    if not rows:
        print("no frames qualified"); return
    print("SEXUAL FRAMES, SEXUAL INSTRUMENT vs v6 vs bge")
    print("%d frames | %d random lineage splits each | identical word set per frame\n"
          % (len(rows), a.splits))
    print("  %-52s %4s %4s %7s %7s %7s %7s"
          % ("frame", "lin", "wds", "ceil", "sex9", "v6_12", "bge_pc"))
    for r in sorted(rows, key=lambda r: -r.get("mean_sex9", -9)):
        print("  %-52s %4d %4d %+7.3f %+7.3f %+7.3f %+7.3f"
              % (r["prompt"][:52], r["n_lineages"], r["n_words"],
                 r.get("mean_ceiling", float("nan")), r.get("mean_sex9", float("nan")),
                 r.get("mean_v6_12", float("nan")), r.get("mean_bge_pcs", float("nan"))))
    ceil = float(np.median([r["mean_ceiling"] for r in rows]))
    print("\n  ceiling (half A predicts half B): %.3f\n" % ceil)
    print("  %-14s %9s %9s %10s   %s"
          % ("model", "median R2", "sd/split", "% ceiling", "wins/frames"))
    for m in MODELS[1:]:
        v = [r["mean_" + m] for r in rows if "mean_" + m in r]
        if not v:
            continue
        sd = [r["sd_" + m] for r in rows if "sd_" + m in r]
        print("  %-14s %9.3f %9.3f %9.0f%%   %d/%d > 0"
              % (m, float(np.median(v)), float(np.median(sd)),
                 100 * float(np.median(v)) / ceil, sum(1 for x in v if x > 0), len(v)))
    from scipy import stats
    print("\nHEAD TO HEAD (paired over frames, same words both sides)")
    for x, y in (("sex9", "v6_12"), ("sex9", "bge_pcs"), ("both21", "sex9"),
                 ("sex_best1", "v6_best1")):
        d = [r["mean_" + x] - r["mean_" + y] for r in rows
             if "mean_" + x in r and "mean_" + y in r]
        if len(d) < 3:
            continue
        print("   %-10s - %-10s  %+.3f   %s wins %d/%d   p=%.3g"
              % (x, y, float(np.median(d)), x, sum(1 for z in d if z > 0), len(d),
                 stats.wilcoxon(d).pvalue))
    print("\nWHICH SCALE WINS, per frame (share of splits)")
    for r in sorted(rows, key=lambda r: -r.get("mean_sex9", -9)):
        print("   %-52s sex:%-14s %.0f%%   v6:%-13s %.0f%%"
              % (r["prompt"][:52], r["sex_name"], 100 * (r["sex_name_share"] or 0),
                 r["v6_name"], 100 * (r["v6_name_share"] or 0)))
    for k, lab in (("sex", "sexual v2"), ("v6", "v6")):
        c = collections.Counter(r[k + "_name"] for r in rows)
        print("  %-10s overall: %s" % (lab, ", ".join("%s %d" % t for t in c.most_common())))
    json.dump(dict(_what="held-out R2 over %d random lineage splits, sexual v2 "
                         "scales vs v6 vs bge on 14 sexual frames, identical word "
                         "set per frame" % a.splits, rows=rows),
              open(os.path.join(RES, "sexual_scales.json"), "w"), indent=1)
    print("\n-> results/pilot3/sexual_scales.json")




def rho(argv=None):
    """The SAME frames and words, scored the way X_metonymy scored them.

    Held-out R2 and per-pair rho are different questions and the file above
    answers only the first. rho asks whether a scale ORDERS the movers inside a
    lineage; R2 asks whether a linear fit on half the lineages predicts the other
    half's net movement in squared error. A scale can order every pair correctly
    and still lose to the mean as a predictor, because ordering does not fix a
    slope and net movement over ten lineages is a noisy target.

    This is what reconciles the -0.087 above with X's -0.53: run both on one set
    of numbers and report the gap rather than picking whichever supports a story.
    """
    import numpy as np, json, os, collections
    from scipy import stats
    from axis_variants import ratings
    rows = json.load(open(os.path.join(RES, "sexual_scales.json")))["rows"]
    keep = {r["prompt"] for r in rows}
    v6, _ = ratings()
    S6 = sorted({s for p in v6.values() for w in p.values() for s in w})
    sx = collections.defaultdict(dict)
    for r in json.load(open(os.path.join(SEX, "rated_gender_pairs_v2.json")))["rows"]:
        if r.get("ratable") is not False and all(
                isinstance(r.get(s), (int, float)) for s in S2):
            sx[r["prompt"]][r["word"]] = {s: float(r[s]) for s in S2}
    cells = collections.defaultdict(lambda: collections.defaultdict(dict))
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        cells[d["item_id"]][d["base"] + " -> " + d["endpoint"]][d["word"]] = d["dP"]
    item_of = {json.loads(l)["prompt"]: json.loads(l)["item_id"]
               for l in open(os.path.join(RES, "cells.jsonl"))}

    print("PER-PAIR RHO, the X_metonymy estimator, on the same 12 frames\n")
    print("  rho is scale vs mover verdict (+1 riser / -1 faller / 0) WITHIN one")
    print("  lineage, then Wilcoxon over that frame's 20 lineages.\n")
    agg = collections.defaultdict(list)
    for r in sorted(rows, key=lambda r: -r["mean_sex9"]):
        p = r["prompt"]; item = item_of[p]
        ok = [w for w in sorted({w for l in cells[item].values() for w in l})
              if w in sx[p] and w in v6[p] and all(s in v6[p][w] for s in S6)]
        best = None
        for s in S2 + S6:
            src = sx[p] if s in S2 else v6[p]
            per = []
            for l in sorted(cells[item]):
                d = cells[item][l]
                ww = [w for w in ok if w in d]
                if len(ww) < 8:
                    continue
                y = [1 if d[w] > 0 else (-1 if d[w] < 0 else 0) for w in ww]
                x = [src[w][s] for w in ww]
                if len(set(y)) < 2 or len(set(x)) < 2:
                    continue
                per.append(stats.spearmanr(x, y).statistic)
            if len(per) >= 8:
                med = float(np.median(per))
                pv = stats.wilcoxon(per).pvalue
                agg[s].append(med)
                if best is None or abs(med) > abs(best[1]):
                    best = (s, med, pv, len(per))
        if best:
            print("  %-52s %-15s %+.3f  p=%.2g  (%d pairs)  [R2 %+.3f]"
                  % (p[:52], best[0], best[1], best[2], best[3], r["mean_sex9"]))
    print("\n  SCALE, pooled over frames (median of per-frame medians)")
    out = sorted(agg.items(), key=lambda kv: -abs(np.median(kv[1])))
    for s, v in out[:12]:
        w = stats.wilcoxon(v).pvalue if len(v) >= 6 else float("nan")
        print("   %-16s %-8s %+.3f   %2d/%-2d frames signed same way   p=%.3g"
              % (s, "[sex]" if s in S2 else "[v6]", float(np.median(v)),
                 max(sum(1 for x in v if x > 0), sum(1 for x in v if x < 0)), len(v), w))


if __name__ == "__main__":
    main()
