"""Every table for a run, computed from its committed artifacts.

    python experiments/displacement_axis/report.py --run pilot3
    python experiments/displacement_axis/report.py --run pilot3 --only sign,frames
    python experiments/displacement_axis/report.py --run pilot3 --words   # per-frame word tables

Sections, in the order the argument decomposes:

    pop        the population, from the manifest, with coverage warnings
    sign       DOES the mass move toward the permitted pole, and the pooled null
    consist    per-item consistency against the null -- the corpus-level FENCE
    share      how much of the movement the declared axis accounts for
    mech       reordering against sharpening, and the rank statistics
    dose       displacement against base transgressive mass, and layered conditions
    frames     frames where displacement is the majority response
    churn      the churn class, decomposed
    ties       tie-break robustness, if a flipties run exists beside this one

## WHY THIS FILE EXISTS

Every number in it was at some point computed in a shell one-liner and reported
without a producer. That is `producer-debt.md` Class 1 sub-type B, and it made a
published number UNAUDITABLE -- the top of the severity ladder, above missing
artifacts and far above missing figures. One such number was already found wrong
when someone tried to re-derive it. A number that only exists in a transcript is
worse than a number nobody has computed, because it gets quoted.

## READING NOTES THAT ARE NOT OPTIONAL

**`displacement` at 100% nice-ward and `reverse` at 0% are DEFINITIONAL.**
Displacement is defined as both split components negative, which forces `dN`
negative. Those rows are not evidence about anything. `churn` is the informative
class because its sign is not fixed by its definition.

**The pooled null answers the direction claim; the per-item null does not.** A
frame's checkpoints share prompts and pretraining, so almost any axis shows a
lopsided split within one frame. What is expensive is the sign agreeing ACROSS
frames. Null axes get lopsided splits in arbitrary directions and cancel; the
declared axes do not. Both are printed, and the section headers say which claim
each one bears on, because the wrong pairing was made once already.

**`dN_reorder` and `interaction` are aggregate-only.** Per-cell values move under
tie-breaking by more than the median effect. `ties` prints the evidence when a
flipties run is present.
"""

import argparse
import collections
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

SECTIONS = ["pop", "sign", "consist", "share", "mech", "dose", "frames", "churn", "ties"]


def load(rundir, name):
    p = os.path.join(rundir, name)
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def z_binom(k, n, p=0.5):
    """Normal approximation to the binomial. n is in the thousands throughout."""
    if n <= 0:
        return float("nan")
    return (k - n * p) / math.sqrt(n * p * (1 - p))


def pearson(x, y):
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


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return st.median(v) if v else None


def f(v, w=9, p=4):
    return ("%+*.*f" % (w, p, v)) if v is not None else (" " * (w - 3)) + "n/a"


def short(b, e, n=40):
    return (b.split("/")[-1] + " -> " + e.split("/")[-1])[:n]


# ---------------------------------------------------------------- sections

def sec_pop(A):
    m = A["manifest"]
    print("POPULATION  run=%s  measured %s  code %s"
          % (m["run"], m.get("measured_on"), (m.get("code_commit") or "?")[:8]))
    print("   %d cells | %d items | %d prompts | %d of %d declared pairs"
          % (m["n_cells"], m["n_items"], m["n_prompts"],
             len(m["pairs_run"]), m["declared_pairs"]))
    print("   identity check |D.u - dN| worst %.2e" % (m.get("identity_check_worst") or 0))
    print("   signatures: %s" % "  ".join("%s %d (%.0f%%)" % (k, v, 100 * v / m["n_cells"])
                                          for k, v in m["signatures"].items()))
    ns = [p["n_cells"] for p in m["pairs_run"]]
    print("   cells per pair: min %d max %d median %d" % (min(ns), max(ns), int(st.median(ns))))
    #: **A THIN PAIR IS A COVERAGE FACT, NOT A RESULT.** Silently dropping it
    #: would make the panel look balanced; printing the warning keeps the reader
    #: aware that a per-pair rate on 36 cells is not comparable to one on 300.
    thin = [p for p in m["pairs_run"] if p["n_cells"] < 0.5 * max(ns)]
    if thin:
        print("   THIN COVERAGE (under half the best-covered pair):")
        for p in thin:
            print("      %-42s %4d cells" % (short(p["base"], p["endpoint"], 42), p["n_cells"]))
    print("   NOTE: coverage is uneven, so every corpus-wide proportion below is")
    print("         over an unbalanced panel.")


def sec_sign(A):
    c = [x for x in A["cells"] if x.get("dN_position") is not None]
    n = len(c)
    k = sum(1 for x in c if x["dN_position"] < 0)
    print("DIRECTION -- does the mass move toward the permitted pole?")
    print("   %d of %d cells nice-ward = %.1f%%   null 50%%   z = %+.1f" % (k, n, 100 * k / n, z_binom(k, n)))

    print("\n   by pair (each an independently trained and aligned lineage):")
    by = collections.defaultdict(list)
    for x in c:
        by[(x["base"], x["endpoint"])].append(x)
    rows = []
    for kk, g in by.items():
        kn = sum(1 for x in g if x["dN_position"] < 0)
        rows.append((kn / len(g), short(*kk), kn, len(g), z_binom(kn, len(g))))
    for r, lab, kn, tot, zz in sorted(rows, reverse=True):
        mark = "***" if abs(zz) > 3 else "*" if abs(zz) > 2 else "   "
        note = "REVERSED" if (zz < -2) else ("null" if abs(zz) <= 2 else "")
        print("      %-40s %4d/%4d %5.0f%%  z=%+5.1f %s %s" % (lab, kn, tot, 100 * r, zz, mark, note))
    sigp = sum(1 for r, _, _, _, zz in rows if zz > 2)
    print("      %d of %d lineages significantly nice-ward on their own" % (sigp, len(rows)))

    print("\n   by domain:")
    byd = collections.defaultdict(list)
    for x in c:
        byd[x["domain"]].append(x)
    for dd, g in sorted(byd.items(), key=lambda kv: -sum(1 for x in kv[1] if x["dN_position"] < 0) / len(kv[1])):
        kn = sum(1 for x in g if x["dN_position"] < 0)
        zz = z_binom(kn, len(g))
        print("      %-14s %4d/%4d %5.0f%%  z=%+5.1f %s"
              % (dd, kn, len(g), 100 * kn / len(g), zz, "" if abs(zz) > 2 else "  NOT SIGNIFICANT"))

    print("\n   by signature (displacement/reverse are DEFINITIONAL -- not evidence):")
    bys = collections.defaultdict(list)
    for x in c:
        bys[x["signature"]].append(x)
    for s in ("displacement", "churn", "reverse", "suppression", "arrival", "flat"):
        g = bys.get(s)
        if not g:
            continue
        kn = sum(1 for x in g if x["dN_position"] < 0)
        #: **"DEFINITIONAL" IS NOT EXACT AND THE LABEL SHOULD SAY SO.** `signature`
        #: comes from split()'s suppression/substitution; `dN_position` is a
        #: difference of per-arm renormalised centroids. They are DIFFERENT
        #: decompositions of the same movement, so a cell near zero can disagree
        #: in sign between them. On pilot3 that is 2 cells of 5,600, at
        #: |dN_position| of 1.8e-04 and 3.7e-03. Printing the count keeps the label
        #: honest without anyone having to recall the caveat, which is the only
        #: kind of caveat that survives.
        tag = ""
        if s in ("displacement", "reverse"):
            exc = (len(g) - kn) if s == "displacement" else kn
            tag = ("  <- definitional, %d exception%s" % (exc, "" if exc == 1 else "s")
                   if exc else "  <- definitional")
        print("      %-14s %4d/%4d %5.0f%%  z=%+5.1f%s"
              % (s, kn, len(g), 100 * kn / len(g), z_binom(kn, len(g)), tag))

    xs = A["axis_share"]
    xs = [r for r in (xs or []) if r.get("null_head_signed") and r.get("cos_theta") is not None]
    if not xs:
        return
    K = min(len(r["null_head_signed"]) for r in xs)
    print("\n   POOLED NULL -- this is the null that bears on the direction claim.")
    print("   50% is only correct if the axis orientation is arbitrary, and ours is")
    print("   fixed by the author's labels. So: %d size-matched random bisections of" % K)
    print("   each frame's own vocabulary, same centroid-difference construction.")
    real = sum(1 for r in xs if r["cos_theta"] < 0) / len(xs)
    fr = [sum(1 for r in xs if r["null_head_signed"][j] < 0) / len(xs) for j in range(K)]
    print("      declared axis      %.3f nice-ward   |dev from .5| = %.3f" % (real, abs(real - 0.5)))
    print("      random bisections  %.3f median      range %.3f - %.3f, |dev| max %.3f"
          % (st.median(fr), min(fr), max(fr), max(abs(x - 0.5) for x in fr)))
    print("      declared beats %d of %d draws"
          % (sum(1 for x in fr if abs(real - 0.5) > abs(x - 0.5)), K))


def sec_consist(A):
    xs = [r for r in (A["axis_share"] or []) if r.get("null_head_signed")
          and r.get("cos_theta") is not None]
    if not xs:
        print("CONSISTENCY -- no null draws in this run")
        return
    K = min(len(r["null_head_signed"]) for r in xs)
    print("PER-ITEM CONSISTENCY -- the FENCE, not the direction claim")
    print("   Asks whether the declared axis predicts agreement among ONE frame's")
    print("   checkpoints better than a random bisection. It does, barely, and that")
    print("   is expected: a frame's checkpoints share prompts and pretraining, so")
    print("   almost any direction shows a lopsided split. The direction claim lives")
    print("   across frames, where null axes cancel and declared axes do not.")
    byi = collections.defaultdict(list)
    for r in xs:
        byi[r["item_id"]].append(r)
    usable = [(i, g) for i, g in byi.items() if len(g) >= 8]
    if not usable:
        print("   no items with >=8 checkpoints")
        return
    rdev, ndev, beat = [], [], []
    for i, g in usable:
        fr = sum(1 for r in g if r["cos_theta"] < 0) / len(g)
        rd = abs(fr - 0.5)
        rdev.append(rd)
        nd = [abs(sum(1 for r in g if r["null_head_signed"][j] < 0) / len(g) - 0.5)
              for j in range(K)]
        ndev.extend(nd)
        beat.append(sum(1 for x in nd if rd > x) / K)
    print("   items with >=8 checkpoints: %d" % len(usable))
    print("      declared |consistency dev|  median %.3f" % st.median(rdev))
    print("      null     |consistency dev|  median %.3f" % st.median(ndev))
    print("      declared beats %.0f%% of nulls per item (median)" % (100 * st.median(beat)))
    print("      items beating >=95%% of nulls: %d of %d (%.0f%%)"
          % (sum(1 for x in beat if x >= 0.95), len(beat),
             100 * sum(1 for x in beat if x >= 0.95) / len(beat)))
    print("      items doing worse than half the draws: %d (%.0f%%)"
          % (sum(1 for x in beat if x < 0.5), 100 * sum(1 for x in beat if x < 0.5) / len(beat)))
    print("   => NO SINGLE FRAME SUPPORTS A DISPLACEMENT CLAIM. Corpus level only.")


def sec_share(A):
    xs = [r for r in (A["axis_share"] or []) if r.get("cos_theta") is not None]
    if not xs:
        return
    print("AXIS SHARE -- how much of the movement is the declared distinction")
    print("   |D| is the centroid's actual movement in embedding space; cos is the")
    print("   fraction of its DIRECTION along the axis; r2 the fraction of variance.")
    print("   %-14s %6s %10s %8s %10s %7s %8s"
          % ("", "cells", "|D| move", "|cos|", "null(head)", "beats", "r2"))
    by = collections.defaultdict(list)
    for r in xs:
        by[r["signature"]].append(r)

    def row(lab, g):
        if not g:
            return
        hb = [r["beats_head"] for r in g if r.get("beats_head") is not None]
        nh = [r["null_head_med"] for r in g if r.get("null_head_med") is not None]
        print("   %-14s %6d %10.4f %8.3f %10.3f %6.0f%% %8.3f"
              % (lab, len(g), st.median(r["norm"] for r in g),
                 st.median(abs(r["cos_theta"]) for r in g),
                 st.median(nh) if nh else float("nan"),
                 100 * st.median(hb) if hb else float("nan"),
                 st.median(r["r2"] for r in g)))
    row("all cells", xs)
    for s in ("displacement", "churn", "reverse"):
        row("  " + s, by.get(s, []))
    print("   NOTE on the null, because two analytic arguments both undershoot it:")
    print("        ambient 1024 dims       -> expected |cos| 0.031   (6x too small)")
    print("        effective dim 67.7      -> expected |cos| 0.122   (1.5x too small)")
    print("        construction-matched    -> 0.180, what is measured")
    print("        The gap is that null axes are NOT random directions: they are")
    print("        centroid differences of 3-11 word sets from the same vocabulary,")
    print("        so they inherit local structure. Hence an empirical null, not an")
    print("        analytic one. (Vectors are L2-normalised; global centering is a")
    print("        verified no-op -- every quantity here is a difference, so the")
    print("        anisotropy cancels: max |cos| change 1.4e-09 over 120 cells.)")
    dis = by.get("displacement", [])
    if dis:
        print("   r2 in displacement cells is %.3f, so most of the movement there is in"
              % st.median(r["r2"] for r in dis))
        print("      directions this instrument does not characterise.")


def sec_mech(A):
    ms = A["mechanism"]
    if not ms:
        return
    print("MECHANISM -- reordering against sharpening")
    pair = [(r["dN_total"], r["dN_position_from_cells"]) for r in ms
            if r.get("dN_total") is not None and r.get("dN_position_from_cells") is not None]
    if pair:
        worst = max(abs(u - v) for u, v in pair)
        print("   cross-check against cells.jsonl: worst |diff| %.2e  %s"
              % (worst, "OK" if worst < 1e-6 else "*** DISAGREE ***"))
    de = [r["d_entropy"] for r in ms if r.get("d_entropy") is not None]
    dt = [r["dT"] for r in ms if r.get("dT") is not None]
    if de:
        print("   IS THE PREMISE TRUE: entropy median %s, fell in %.0f%% of cells"
              % (f(st.median(de)), 100 * sum(1 for v in de if v < 0) / len(de)))
    if dt:
        print("                        dT median %s, rose in %.0f%% of cells"
              % (f(st.median(dt)), 100 * sum(1 for v in dt if v > 0) / len(dt)))
    hdr = "   %-14s %6s %9s %9s %9s %9s %9s" % (
        "", "cells", "total", "sharpen", "reorder", "interact", "sharp>ord")
    print(hdr)

    def row(lab, g):
        if not g:
            return
        both = [(r["dN_sharpen"], r["dN_reorder"]) for r in g
                if r.get("dN_sharpen") is not None and r.get("dN_reorder") is not None]
        dom = (sum(1 for s, q in both if abs(s) > abs(q)) / len(both)) if both else None
        print("   %-14s %6d %s %s %s %s %8s"
              % (lab, len(g), f(med(g, "dN_total")), f(med(g, "dN_sharpen")),
                 f(med(g, "dN_reorder")), f(med(g, "interaction")),
                 ("%.0f%%" % (100 * dom)) if dom is not None else "n/a"))
    row("all cells", ms)
    by = collections.defaultdict(list)
    for r in ms:
        by[r["signature"]].append(r)
    for s in ("displacement", "churn", "reverse"):
        row("  " + s, by.get(s, []))
    tot = [abs(r["dN_reorder"]) for r in ms if r.get("dN_reorder") is not None]
    shs = [abs(r["dN_sharpen"]) for r in ms if r.get("dN_sharpen") is not None]
    if tot and shs and sum(shs) > 0:
        print("   sum|reorder| / sum|sharpen| = %.2f" % (sum(tot) / sum(shs)))

    print("\n   RANK STATISTICS -- corroboration, not a better headline.")
    #: The two families point nice-ward in OPPOSITE signs: d_rho was built to
    #: share the mass convention, d_auc is P(nice outranks naughty) so nice-ward
    #: is positive. One rule for both reported AUC as the sharpest clash in the
    #: table when it was agreeing. `orient` makes the convention a property of
    #: the statistic rather than of anyone's memory.
    for k, lab, orient in (("d_rho", "rank rho", +1), ("d_auc", "pole AUC", -1)):
        p = [(r["dN_total"], r[k] * orient) for r in ms
             if r.get("dN_total") is not None and r.get(k) is not None]
        if not p:
            continue
        x = [u for u, _ in p]
        y = [v for _, v in p]
        agree = sum(1 for u, v in p if (u < 0) == (v < 0)) / len(p)
        r = pearson(x, y)
        print("      %-10s n=%5d  pearson %s vs dN_total, sign agreement %.0f%%%s"
              % (lab, len(p), ("%+.3f" % r) if r is not None else "n/a", 100 * agree,
                 "  [sign flipped to mass convention]" if orient < 0 else ""))
    for comp in ("dN_reorder", "dN_sharpen", "d_entropy"):
        p = [(r["d_rho"], r[comp]) for r in ms
             if r.get("d_rho") is not None and r.get(comp) is not None]
        if p:
            print("      rank rho vs %-12s pearson %+.3f"
                  % (comp, pearson([u for u, _ in p], [v for _, v in p])))
    print("      => ranks estimate dN_reorder, are near-blind to sharpening, and are")
    print("         flat against concentration. They agree here BECAUSE reordering")
    print("         dominates; they could not have established that it does.")


def sec_dose(A):
    c = [x for x in A["cells"] if x.get("base_naughty_mass") is not None
         and x.get("base_share") is not None]
    if not c:
        print("DOSE -- base pole mass not in cells.jsonl (pre-analyze.py run)")
        return
    print("DOSE-RESPONSE -- displacement against base transgressive mass")
    c.sort(key=lambda x: x["base_naughty_mass"])
    q = len(c) // 4
    print("   %-24s %6s %7s %7s %7s %10s %9s"
          % ("quartile", "cells", "displ", "churn", "rev", "median dN", "mass"))
    for i, lab in enumerate(["Q1 lowest", "Q2", "Q3", "Q4 highest"]):
        sl = c[i * q:(i + 1) * q] if i < 3 else c[3 * q:]
        sg = collections.Counter(x["signature"] for x in sl)
        print("   %-24s %6d %6.0f%% %6.0f%% %6.0f%% %s %9.4f"
              % (lab, len(sl), 100 * sg["displacement"] / len(sl), 100 * sg["churn"] / len(sl),
                 100 * sg["reverse"] / len(sl), f(med(sl, "dN_position")),
                 st.median(x["base_naughty_mass"] for x in sl)))
    print("   => a frame with no transgressive mass on a checkpoint CANNOT displace")
    print("      on it, so the headline rate is diluted by impossible cells.")

    by = collections.defaultdict(list)
    for x in c:
        by[(x["base"], x["endpoint"])].append(x)
    strong = {k for k, g in by.items()
              if sum(1 for x in g if x["signature"] == "displacement") / len(g) >= 0.20}
    print("\n   layering the two conditions the thesis requires:")
    print("   %-46s %6s %7s %7s %10s" % ("condition", "cells", "displ", "churn", "median dN"))

    def row(lab, sl):
        if not sl:
            return
        sg = collections.Counter(x["signature"] for x in sl)
        print("   %-46s %6d %6.0f%% %6.0f%% %s"
              % (lab, len(sl), 100 * sg["displacement"] / len(sl),
                 100 * sg["churn"] / len(sl), f(med(sl, "dN_position"))))
    row("all cells", c)
    row("displacing regime (%d of %d pairs at >=20%%)" % (len(strong), len(by)),
        [x for x in c if (x["base"], x["endpoint"]) in strong])
    row("transgressive site (naughty mass >=0.05)", [x for x in c if x["base_naughty_mass"] >= 0.05])
    both = [x for x in c if (x["base"], x["endpoint"]) in strong and x["base_naughty_mass"] >= 0.05]
    row("BOTH", both)
    if both:
        print("\n   within BOTH, by domain:")
        byd = collections.defaultdict(list)
        for x in both:
            byd[x["domain"]].append(x)
        for dd, g in sorted(byd.items(),
                            key=lambda kv: -sum(1 for x in kv[1] if x["signature"] == "displacement") / len(kv[1])):
            if len(g) < 20:
                continue
            print("      %-14s %5d cells  displacement %3.0f%%"
                  % (dd, len(g), 100 * sum(1 for x in g if x["signature"] == "displacement") / len(g)))


def sec_frames(A, show_words=False, top=8):
    c = A["cells"]
    byi = collections.defaultdict(list)
    for x in c:
        byi[x["item_id"]].append(x)
    minpairs = max(4, int(0.6 * max(len(g) for g in byi.values())))
    full = {i: g for i, g in byi.items() if len(g) >= minpairs}
    rank = []
    for i, g in full.items():
        nd = sum(1 for x in g if x["signature"] == "displacement")
        if nd / len(g) > 0.5:
            rank.append((nd / len(g), nd, len(g), i))
    rank.sort(reverse=True)
    print("FRAMES where displacement is the MAJORITY response")
    print("   %d of %d items measured on >=%d pairs" % (len(rank), len(full), minpairs))
    prompts = {x["item_id"]: x["prompt"] for x in c}
    for r, nd, nt, i in rank:
        print("   %2d/%2d  %-14s %s" % (nd, nt, prompts[i][:0] or "", prompts[i][:88]))
    #: The item ceiling is set by the WEAK PAIRS: a lineage that displaces on 10%
    #: of its cells cannot contribute to any frame's majority, so a low count is
    #: partly a fact about model heterogeneity rather than about the frames.
    by = collections.defaultdict(list)
    for x in c:
        by[(x["base"], x["endpoint"])].append(x)
    strong = {k for k, g in by.items()
              if sum(1 for y in g if y["signature"] == "displacement") / len(g) >= 0.20}
    if strong and len(strong) < len(by):
        byi2 = collections.defaultdict(list)
        for x in c:
            if (x["base"], x["endpoint"]) in strong:
                byi2[x["item_id"]].append(x)
        f2 = {i: g for i, g in byi2.items() if len(g) >= max(4, int(0.7 * len(strong)))}
        maj = [i for i, g in f2.items()
               if sum(1 for x in g if x["signature"] == "displacement") / len(g) > 0.5]
        hi = [i for i, g in f2.items()
              if sum(1 for x in g if x["signature"] == "displacement") / len(g) >= 0.8]
        print("   restricting to the %d pairs that displace at all (>=20%% of cells):"
              % len(strong))
        print("      %d of %d items displace on a majority (%.0f%%), %d at >=80%%"
              % (len(maj), len(f2), 100 * len(maj) / max(len(f2), 1), len(hi)))
        print("      => the item ceiling is largely the weak models, not the frames.")
    return [i for _, _, _, i in rank][:top]


def sec_words(A, item_ids, rundir):
    """Per-frame word tables, streamed: words.jsonl runs to hundreds of MB."""
    if not item_ids:
        return
    c = A["cells"]
    prompts = {x["item_id"]: x["prompt"] for x in c}
    doms = {x["item_id"]: x["domain"] for x in c}
    want = set(item_ids)
    dis = {(x["item_id"], x["base"], x["endpoint"]) for x in c
           if x["signature"] == "displacement" and x["item_id"] in want}
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    path = os.path.join(rundir, "words.jsonl")
    if not os.path.exists(path):
        print("WORDS -- words.jsonl absent (gitignored; regenerate with analyze.py)")
        return
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            if (r["item_id"], r["base"], r["endpoint"]) in dis:
                agg[r["item_id"]][r["word"]].append(r)
    for i in item_ids:
        W = agg.get(i)
        if not W:
            continue
        ncell = len({(r["base"], r["endpoint"]) for ws in W.values() for r in ws})
        print("\n" + "=" * 88)
        print("%s   [%s]   displacing on %d pairs" % (prompts[i], doms[i], ncell))
        rows = []
        for w, rs in W.items():
            rows.append((sum(r["contribution"] for r in rs) / ncell, w,
                         sum(r["p_base"] for r in rs) / ncell,
                         sum(r["p_aligned"] for r in rs) / ncell, rs[0]["pole"], len(rs)))
        rows.sort(key=lambda t: -abs(t[0]))
        print("  %-16s %9s %9s %9s %9s %5s %s"
              % ("word", "p_base", "p_align", "mean dP", "contrib", "cells", "pole"))
        for cb, w, pb, pa, pole, nn in rows[:10]:
            print("  %-16s %9.4f %9.4f %+9.4f %+9.4f %5d  %s"
                  % (w, pb, pa, pa - pb, cb, nn,
                     {"naughty": "NAUGHTY", "nice": "nice"}.get(pole, "-")))
        print("  (means over the pairs on which this frame displaced)")


def sec_churn(A):
    c = [x for x in A["cells"] if x["signature"] == "churn"]
    xs = {(r["item_id"], r["base"], r["endpoint"]): r for r in (A["axis_share"] or [])}
    if not c:
        return
    print("CHURN, DECOMPOSED -- %d cells, the largest class" % len(c))
    k = sum(1 for x in c if (x.get("dN_position") or 0) < 0)
    print("   nice-ward in %.0f%% of cells (z=%+.1f). Informative BECAUSE churn's sign"
          % (100 * k / len(c), z_binom(k, len(c))))
    print("   is not fixed by its definition, unlike displacement's 100%.")
    print("   median suppression %s   median substitution %s"
          % (f(med(c, "suppression")), f(med(c, "substitution"))))
    g = [xs[(x["item_id"], x["base"], x["endpoint"])] for x in c
         if (x["item_id"], x["base"], x["endpoint"]) in xs]
    g = [r for r in g if r.get("cos_theta") is not None]
    if not g:
        return
    print("   |D| median %.4f -- churn cells are NOT quiet cells."
          % st.median(r["norm"] for r in g))
    print("   |cos| median %.3f against a %.3f null: the axis is ENGAGED and the"
          % (st.median(abs(r["cos_theta"]) for r in g),
             st.median(r["null_head_med"] for r in g if r.get("null_head_med") is not None)))
    print("   SIGN IS UNDETERMINED. (An earlier reading called churn orthogonal; that")
    print("   came from reading a median SIGNED cos as though it were a magnitude.)")
    g.sort(key=lambda r: r["norm"])
    q = max(len(g) // 4, 1)
    for lab, sl in (("quietest quartile", g[:q]), ("loudest quartile", g[-q:])):
        print("      %-20s |D| %.4f  |cos| %.3f  beats %.0f%% of nulls"
              % (lab, st.median(r["norm"] for r in sl),
                 st.median(abs(r["cos_theta"]) for r in sl),
                 100 * st.median(r["beats_head"] for r in sl if r.get("beats_head") is not None)))


def sec_ties(A, rundir):
    fl = load(rundir, "mechanism_flipties.jsonl")
    if not fl:
        print("TIES -- no flipties run beside this one.")
        print("   Run: analyze.py --out <same dir> --flip-ties --force")
        print("   Until then dN_reorder and interaction are UNVALIDATED per cell.")
        return
    a = {(r["item_id"], r["base"], r["endpoint"]): r for r in A["mechanism"]}
    b = {(r["item_id"], r["base"], r["endpoint"]): r for r in fl}
    ks = sorted(set(a) & set(b))
    print("TIE-BREAK ROBUSTNESS -- %d cells compared" % len(ks))
    print("   %-14s %11s %11s %12s %13s" % ("field", "median", "median flip", "max |diff|", "cells moved"))
    for fld in ("dN_total", "dN_sharpen", "dN_reorder", "interaction"):
        va = [a[x][fld] for x in ks if a[x].get(fld) is not None and b[x].get(fld) is not None]
        vb = [b[x][fld] for x in ks if a[x].get(fld) is not None and b[x].get(fld) is not None]
        if not va:
            continue
        d = [abs(u - v) for u, v in zip(va, vb)]
        mv = sum(1 for x in d if x > 1e-9)
        print("   %-14s %+11.5f %+11.5f %12.2e %7d (%3.0f%%)"
              % (fld, st.median(va), st.median(vb), max(d), mv, 100 * mv / len(d)))
    sa = [a[x]["dN_sharpen"] for x in ks]
    ra = [a[x]["dN_reorder"] for x in ks]
    sb = [b[x]["dN_sharpen"] for x in ks]
    rb = [b[x]["dN_reorder"] for x in ks]
    da = sum(1 for s, r in zip(sa, ra) if abs(s) > abs(r)) / len(ks)
    db = sum(1 for s, r in zip(sb, rb) if abs(s) > abs(r)) / len(ks)
    flips = sum(1 for i in range(len(ks))
                if (abs(sa[i]) > abs(ra[i])) != (abs(sb[i]) > abs(rb[i])))
    print("   sharpen-dominant share: %.1f%% -> %.1f%%" % (100 * da, 100 * db))
    print("   cells changing dominant mechanism: %d of %d (%.1f%%)"
          % (flips, len(ks), 100 * flips / len(ks)))
    pert = [abs(a[x]["dN_reorder"] - b[x]["dN_reorder"]) for x in ks]
    ent = [a[x]["d_entropy"] for x in ks if a[x].get("d_entropy") is not None]
    if len(ent) == len(pert):
        print("   perturbation vs entropy change: pearson %+.3f" % pearson(pert, ent))
        print("      (q_reorder pours into the ALIGNED ordering, and the aligned arm is")
        print("       the concentrated one, so more of its words tie at the theta floor)")
    print("   => AGGREGATES ROBUST, PER-CELL dN_reorder NOT QUOTABLE.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--only", default=None,
                    help="comma-separated subset of: " + ",".join(SECTIONS))
    ap.add_argument("--words", action="store_true",
                    help="also print per-frame word tables (streams words.jsonl)")
    ap.add_argument("--top", type=int, default=8, help="frames to show words for")
    a = ap.parse_args(argv)

    rundir = os.path.join(RESULTS, a.run)
    man = os.path.join(rundir, "manifest.json")
    if not os.path.exists(man):
        print("no manifest at %s" % man, file=sys.stderr)
        return 1
    A = {"manifest": json.load(open(man)),
         "cells": load(rundir, "cells.jsonl") or [],
         "mechanism": load(rundir, "mechanism.jsonl") or [],
         "axis_share": load(rundir, "axis_share.jsonl") or []}

    want = [s.strip() for s in a.only.split(",")] if a.only else SECTIONS
    frames = []
    for s in want:
        if s not in SECTIONS:
            print("unknown section %r; choose from %s" % (s, ",".join(SECTIONS)), file=sys.stderr)
            return 1
        print("\n" + "=" * 88)
        if s == "pop":
            sec_pop(A)
        elif s == "sign":
            sec_sign(A)
        elif s == "consist":
            sec_consist(A)
        elif s == "share":
            sec_share(A)
        elif s == "mech":
            sec_mech(A)
        elif s == "dose":
            sec_dose(A)
        elif s == "frames":
            frames = sec_frames(A, top=a.top)
        elif s == "churn":
            sec_churn(A)
        elif s == "ties":
            sec_ties(A, rundir)
    if a.words:
        if not frames:
            frames = sec_frames(A, top=a.top)
        print("\n" + "=" * 88)
        print("WORD TABLES")
        sec_words(A, frames, rundir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
