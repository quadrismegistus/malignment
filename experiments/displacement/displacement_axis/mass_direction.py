"""Direction of travel and magnitude of travel, on the MASS quantity, per scale.

    python experiments/displacement_axis/mass_direction.py

WHY THIS EXISTS. `loo.py`, `rho_domains.py` and everything else committed on
2026-08-20 predict a word's UNWEIGHTED movement -- the +1/-1 mover verdict, where
a word at p=0.0001 counts exactly as much as a word at p=0.18. That is Findings
P's outcome family, not this directory's. This directory's quantity is

    N = sum p(w) r(w) / sum p(w)   per arm,   dN = N_aligned - N_base

the mass-weighted position shift, identical to `dN_position` except in what r(w)
is. `compare_scorers.py` says so in its own header -- "a scale can order which
words move without shifting the centroid, and vice versa. Both are reported
because the campaign has confused them before" -- and then the campaign confused
them again for a day.

WHY MASS IS THE ONE THE ARGUMENT NEEDS. Displacement is a claim about where the
probability mass goes, i.e. about what the model would actually say. An unweighted
per-word outcome is dominated by the low-probability tail, which is also the
noisiest part of it; that is the likeliest reason the unweighted benchmark sits at
0.024 and why removing 48 duplicate rows flipped the named-vs-embedding
comparison. The tail carries no mass, so it cannot do either to `dN`.

TWO QUESTIONS, KEPT APART, because in the mass frame they are different objects
rather than two summaries of one:

  DEGENERACY GATE, and it applies to BOTH tables. Where a scale is near-constant
over a frame's vocabulary its dN is ~0 and so is every permutation of it, which
makes the ratio 1.00x and drives `beats` to 0 -- reading as a confident result
pointing the wrong way. `harm` is constant on 76% of sexual frames.
spearman(beats, rating sd) = +0.487, p=0.00045 over 48 (domain, scale) cells.
`rho` never had this problem because a constant predictor has no rank variance
and the frame is skipped; dN has no such reflex, so the gate is explicit.

  DIRECTION   the sign of dN. Consistent across a frame's lineages? Across a
              domain's frames? Sign tests throughout, so the table is directly
              comparable to the rho table in the README.
  MAGNITUDE   |dN|, against the permutation that shuffles ratings across the
              frame's own vocabulary -- marginals preserved exactly, only the
              word-to-rating link destroyed. A scale whose |dN| does not beat its
              own shuffle has measured nothing, however consistent its sign.

THE FALSIFIABLE PART. The unweighted work says the domain signature is
`vocalisation` for identity, `harm` for violence, `mundanity` for sexual. If those
are tail artifacts, mass weighting removes them. If they are the centroid moving,
mass weighting sharpens them. Written down before running.

POPULATION. `words.jsonl`, so the cells are exactly the ones `dN_position` is
computed over -- the axis-scored subset, not the full returned vocabulary. That
makes the comparison with `dN_position` like-for-like, and it differs on purpose
from `rated_contextual.py`, which reads the store and covers the wider vocabulary.
Coverage of base mass by RATED words is reported per cell and pooled; a scale is
not quotable on a cell where the ratings cover a small share of the mass.
"""

import argparse, collections, csv, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
sys.path.insert(0, REPO); sys.path.insert(0, HERE)
#: `--run` selects the run directory; pilot3 stays the default so every command
#: already written against this file keeps meaning what it meant. A different
#: run is a different DIRECTORY, so it cannot clobber the canonical artifact and
#: the suffix guard below is about parameters only.
RUN = "pilot3"
RES = os.path.join(HERE, "results", RUN)
LONG = os.path.join(RES, "long")
SLOT = os.path.join(REPO, "experiments", "slot_ratings")
DROP = {"n_eligible", "n_present", "rise", "fall", "net", "ratable"}


def contextual():
    R = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(SLOT, "results", "v6", "rated_v6_*.json")):
        for x in json.load(open(f)):
            if x.get("ratable"):
                R[(x["prompt"], x["word"])].update(
                    {k: v for k, v in x.items()
                     if isinstance(v, int) and not isinstance(v, bool) and k not in DROP})
    return R


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=RUN, help="run directory under results/")
    ap.add_argument("--null-draws", type=int, default=40)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--min-coverage", type=float, default=0.30,
                    help="a cell needs this share of BASE mass on rated words")
    ap.add_argument("--min-sd", type=float, default=0.5,
                    help="a (frame, scale) needs this much rating spread to enter "
                         "either table; below it dN is a number about nothing")
    a = ap.parse_args(argv)
    global RES, LONG
    RES = os.path.join(HERE, "results", a.run)
    LONG = os.path.join(RES, "long")
    if not os.path.isdir(RES):
        ap.error("no such run: %s" % RES)
    print("run: %s" % a.run)
    import numpy as np
    from scipy import stats
    import dedupe

    R = contextual()
    S = sorted({k for v in R.values() for k in v})
    print("contextual ratings: %d (prompt, word) pairs, %d prompts, %d scales\n"
          % (len(R), len({p for p, _ in R}), len(S)))

    cl = [json.loads(l) for l in open(os.path.join(RES, "cells.jsonl"))]
    prompt_of = {c["item_id"]: c["prompt"] for c in cl}
    domain_of = {c["item_id"]: c.get("domain") for c in cl}
    pos = {(c["item_id"], c["base"], c["endpoint"]): c.get("dN_position") for c in cl}
    KEEP = dedupe.report(prompt_of, dedupe.keep(prompt_of))

    cells = collections.defaultdict(dict)
    for line in open(os.path.join(RES, "words.jsonl")):
        d = json.loads(line)
        if d["item_id"] in KEEP:
            cells[(d["item_id"], d["base"], d["endpoint"])][d["word"]] = (
                d["p_base"], d["p_aligned"])

    rng = np.random.default_rng(a.seed)
    rows, dropped = [], collections.Counter()
    for (item, base, end), ws in cells.items():
        p = prompt_of[item]
        rated = [w for w in sorted(ws) if (p, w) in R and all(s in R[(p, w)] for s in S)]
        if len(rated) < 8:
            dropped["under 8 rated words"] += 1
            continue
        pb = np.array([ws[w][0] for w in rated], float)
        pa = np.array([ws[w][1] for w in rated], float)
        allb = sum(v[0] for v in ws.values())
        cov = pb.sum() / allb if allb > 0 else 0.0
        if pb.sum() <= 0 or pa.sum() <= 0:
            dropped["zero mass"] += 1
            continue
        if cov < a.min_coverage:
            dropped["coverage under %.2f" % a.min_coverage] += 1
            continue
        M = np.array([[R[(p, w)][s] for s in S] for w in rated], float)
        wb, wa = pb / pb.sum(), pa / pa.sum()
        dN = wa @ M - wb @ M
        #: the permutation: shuffle the word->rating link, marginals untouched
        null = np.empty((a.null_draws, len(S)))
        for j in range(a.null_draws):
            Mp = M[rng.permutation(len(rated))]
            null[j] = wa @ Mp - wb @ Mp
        beats = (np.abs(dN) > np.abs(null)).mean(0)
        rec = dict(item=item, prompt=p, domain=domain_of.get(item), base=base,
                   endpoint=end, n_rated=len(rated), coverage_mass=float(cov),
                   dN_position=pos.get((item, base, end)))
        sd = M.std(0)
        for i, s in enumerate(S):
            #: DEGENERACY GATE. Where a scale is near-constant over a frame's
            #: vocabulary, dN and every permutation of it are both ~0: the ratio
            #: goes to 1.00x and `beats` collapses to 0, which reads as a real
            #: result pointing the wrong way. Measured: spearman(beats, rating
            #: sd) = +0.487, p=0.00045 over 48 (domain, scale) cells; `harm` is
            #: constant on 76% of sexual frames. rho self-gates because a
            #: constant predictor has no rank variance. dN does not, so it is
            #: gated here, in BOTH tables, not just the magnitude one.
            rec["sd_" + s] = float(sd[i])
            if sd[i] < a.min_sd:
                continue
            rec["dN_" + s] = float(dN[i])
            rec["beats_" + s] = float(beats[i])
            rec["nullabs_" + s] = float(np.median(np.abs(null[:, i])))
        rows.append(rec)

    ngate = sum(1 for r in rows for s in S if "dN_" + s not in r)
    print("degeneracy gate (rating sd < %.2f): %d of %d (cell, scale) pairs dropped"
          % (a.min_sd, ngate, len(rows) * len(S)))
    print("cells scored: %d over %d frames, %d lineages"
          % (len(rows), len({r["item"] for r in rows}),
             len({(r["base"], r["endpoint"]) for r in rows})))
    for k, v in dropped.most_common():
        print("   dropped %5d cells: %s" % (v, k))
    print("   median coverage of base mass by rated words: %.3f\n"
          % float(np.median([r["coverage_mass"] for r in rows])))

    #: FRAME is the unit: collapse a frame's lineages to its median, then test
    #: across frames. Lineages within a frame are not independent observations of
    #: a domain, and pooling them would be the correlated-subunits defect again.
    byframe = collections.defaultdict(list)
    for r in rows:
        byframe[r["item"]].append(r)

    def frame_stats(F, key):
        v = [f[key] for f in F if f.get(key) is not None]
        return (float(np.median(v)) if v else None,
                sum(1 for x in v if x > 0), len(v))

    fr = []
    for item, F in byframe.items():
        d = dict(item=item, prompt=F[0]["prompt"], domain=F[0]["domain"],
                 n_lineages=len(F),
                 coverage_mass=float(np.median([f["coverage_mass"] for f in F])))
        m, up, n = frame_stats(F, "dN_position")
        d["dN_position"] = m
        d["pos_up"], d["pos_n"] = up, n
        for s in S:
            #: only the cells that PASSED the gate for this scale; a frame can
            #: pass on one scale and fail on another, so the sub-population is
            #: per-scale and must be rebuilt rather than inherited from F
            G = [f for f in F if ("dN_" + s) in f]
            if len(G) < max(3, len(F) // 3):
                continue
            m, up, n = frame_stats(G, "dN_" + s)
            if m is None:
                continue
            d["dN_" + s] = m
            d["up_" + s], d["n_" + s] = up, n
            d["ngate_" + s] = len(G)
            d["beats_" + s] = float(np.median([f["beats_" + s] for f in G]))
            #: LIKE FOR LIKE. An earlier version divided |median dN| by
            #: median |dN_null|: a SIGNED median over an ABSOLUTE one, so sign
            #: cancellation shrank the numerator alone and every ratio came back
            #: under 1.0, reading as "smaller than chance". Both sides are now
            #: medians of |dN| over the frame's lineages.
            realabs = float(np.median([abs(f["dN_" + s]) for f in G]))
            nullabs = float(np.median([f["nullabs_" + s] for f in G]))
            d["absdN_" + s] = realabs
            d["ratio_" + s] = realabs / nullabs if nullabs > 0 else None
        fr.append(d)

    doms = collections.defaultdict(list)
    for d in fr:
        doms[d["domain"] or "?"].append(d)
    order = [k for k in sorted(doms, key=lambda k: -len(doms[k])) if len(doms[k]) >= 5]

    def sign(v):
        k = max(sum(1 for x in v if x > 0), sum(1 for x in v if x < 0))
        return k, len(v), stats.binomtest(k, len(v), 0.5).pvalue

    print("DIRECTION OF TRAVEL: sign of dN, frames as the unit")
    print("  'agree' = frames sharing the majority sign; * = p < 0.05/12\n")
    for dm in order:
        F = doms[dm]
        print("  %s (n=%d frames)" % (dm.upper(), len(F)))
        r_ = []
        for s in S:
            v = [f["dN_" + s] for f in F if "dN_" + s in f]
            if len(v) < 5:
                continue
            k, n, pv = sign(v)
            r_.append((abs(float(np.median(v))), s, float(np.median(v)), k, n, pv))
        for _, s, m, k, n, pv in sorted(r_, reverse=True)[:6]:
            print("     %-14s %+8.4f   agree %3d/%-3d  p=%-9.2g %s"
                  % (s, m, k, n, pv, "*" if pv < 0.05 / len(S) else ""))
        v = [f["dN_position"] for f in F if f.get("dN_position") is not None]
        if v:
            k, n, pv = sign(v)
            print("     %-14s %+8.4f   agree %3d/%-3d  p=%-9.2g   [the bge axis]"
                  % ("dN_position", float(np.median(v)), k, n, pv))
        print()

    print("MAGNITUDE OF TRAVEL: |dN| against its own permutation")
    print("  ratio = median |dN| / median |dN| under the shuffle, BOTH absolute;")
    print("  beats = share of draws the real |dN| exceeds. Sorted by ratio.")
    print("  beats = share of")
    print("  draws the real |dN| exceeds. ratio ~1 and beats ~0.5 is nothing.\n")
    print("  %-14s" % "scale" + "".join("%20s" % d[:18] for d in order))
    for s in S:
        cells_ = []
        for dm in order:
            F = [f for f in doms[dm] if "ratio_" + s in f and f["ratio_" + s]]
            if len(F) < 5:
                cells_.append("%20s" % "--"); continue
            cells_.append("%12.2fx %6.2f" % (
                float(np.median([f["ratio_" + s] for f in F])),
                float(np.median([f["beats_" + s] for f in F]))))
        print("  %-14s" % s + "".join(cells_))

    #: A NON-DEFAULT RUN MUST NOT CLOBBER THE CANONICAL ARTIFACT. The threshold
    #: sweep ran this file four times ending at --min-sd 1.00, overwrote
    #: mass_direction.json and both CSVs, and the sd=1.00 data was committed
    #: under a message quoting the sd=0.50 numbers. Caught by counting frames in
    #: the committed JSON, not by anything in the run. Parameters now go in the
    #: filename when they differ from the defaults, and into the JSON always.
    params = dict(min_sd=a.min_sd, null_draws=a.null_draws,
                  min_coverage=a.min_coverage, seed=a.seed)
    dflt = dict(min_sd=0.5, null_draws=40, min_coverage=0.30, seed=20260820)
    tag = "" if params == dflt else "_sd%g_n%d" % (a.min_sd, a.null_draws)
    if tag:
        print("\nNON-DEFAULT RUN: writing with suffix '%s', canonical files untouched"
              % tag)
    os.makedirs(LONG, exist_ok=True)
    with open(os.path.join(LONG, "mass_cells%s.csv" % tag), "w", newline="") as fh:
        keys = sorted({k for r in rows for k in r})
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    with open(os.path.join(LONG, "mass_frames%s.csv" % tag), "w", newline="") as fh:
        keys = sorted({k for r in fr for k in r})
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(fr)
    json.dump(dict(_what="mass-weighted dN per (cell, scale) with its permutation "
                         "null, and the frame-level collapse", _params=params,
                   cells=rows, frames=fr),
              open(os.path.join(RES, "mass_direction%s.json" % tag), "w"))
    print("\n-> results/%s/mass_direction%s.json,"
          " long/mass_cells%s.csv, long/mass_frames%s.csv" % (a.run, tag, tag, tag))


if __name__ == "__main__":
    main()
